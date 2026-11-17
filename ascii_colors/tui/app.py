# -*- coding: utf-8 -*-
"""Application runtime for the ascii_colors TUI framework.

The runtime uses three cooperating execution paths:

* an input thread translates platform input into key/mouse events,
* the main thread consumes one serialized event queue,
* a render thread paints the latest state at the configured frame rate.

Terminal callbacks therefore never race each other, and worker threads can use
:meth:`App.post` to update widgets without mutating them during a draw.
"""

import os
import queue
import shutil
import sys
import threading
from functools import partial
from typing import Callable, Iterator, List, Optional, Union

from ascii_colors.tui.screen import ScreenBuffer, ScreenRenderer
from ascii_colors.tui.widgets import Container, Widget
from ascii_colors.utils import MouseEvent


_KEY_ALIASES = {
    "RETURN": "ENTER",
    "\r": "ENTER",
    "\n": "ENTER",
    "SPACE": " ",
    "TAB_BACK": "BACKTAB",
    "SHIFT_TAB": "BACKTAB",
    "\t": "TAB",
    "ESC": "ESCAPE",
    "\x1b": "ESCAPE",
    "\x7f": "BACKSPACE",
}


def _read_key() -> Union[str, MouseEvent]:
    """Read a single key using the library's cross-platform helper."""
    from ascii_colors.utils import _get_key

    return _get_key(intercept_control=True)


class App:
    """A curses-style application with queued events and mouse routing."""

    def __init__(
        self,
        *,
        fps: float = 20.0,
        stream=None,
        alt_screen: bool = True,
        hide_cursor: bool = True,
        quit_keys: Optional[List[str]] = None,
        force_terminal: Optional[bool] = None,
        mouse: bool = False,
        synchronized_output: bool = True,
    ):
        self.fps = max(1.0, fps)
        self.stream = stream or sys.stdout
        self.alt_screen = alt_screen
        self.hide_cursor = hide_cursor
        self.quit_keys = list(quit_keys) if quit_keys is not None else ["ESCAPE"]
        self.force_terminal = force_terminal
        self.mouse = mouse
        self.on_mouse: Optional[Callable[[MouseEvent], None]] = None
        self._key_bindings: dict = {}

        self.root: Optional[Widget] = None
        self.width = 0
        self.height = 0
        self.buffer = ScreenBuffer(1, 1)
        self.renderer = ScreenRenderer(
            self.stream, synchronized_output=synchronized_output
        )

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._events: queue.Queue = queue.Queue()
        self._render_thread: Optional[threading.Thread] = None
        self._input_thread: Optional[threading.Thread] = None
        self._focus_targets: List[Widget] = []
        self._focus_idx = 0
        self._modals: List[Widget] = []
        self._hovered: Optional[Widget] = None
        self._mouse_capture: Optional[Widget] = None

    # ------------------------------------------------------------ public API
    def set_root(self, root: Widget) -> None:
        self.root = root
        root._attach_app(self)

    def exit(self) -> None:
        self._stop_event.set()

    def post(self, callback: Callable, *args, **kwargs) -> None:
        """Schedule ``callback`` on the UI thread.

        This is the supported way for model/network worker threads to update
        widget state. The callable is serialized with keyboard and mouse input.
        """
        if not callable(callback):
            raise TypeError("App.post() expects a callable")
        self._events.put(partial(callback, *args, **kwargs))

    call_soon = post

    def bind(self, key: str, callback: Callable[[], None]) -> None:
        """Bind a named key to an application-level callback.

        Bindings are intended for commands such as ``CTRL_N`` and ``F1``.
        They run before focused-widget dispatch; unbound printable keys keep
        flowing to text editors normally.
        """
        if not callable(callback):
            raise TypeError("App.bind() expects a callable")
        self._key_bindings[key] = callback

    def unbind(self, key: str) -> None:
        self._key_bindings.pop(key, None)

    def push_modal(self, widget: Widget) -> None:
        """Push a centered modal overlay; input focus is restricted to it."""
        with self._lock:
            widget.parent = None
            widget._attach_app(self)
            self._modals.append(widget)
            self._refresh_focus()

    def pop_modal(self) -> Optional[Widget]:
        """Pop the topmost modal overlay and return it."""
        with self._lock:
            if not self._modals:
                return None
            popped = self._modals.pop()
            self._mouse_capture = None
            self._set_hovered(None)
            self._refresh_focus()
            return popped

    def refresh_focus(self) -> None:
        """Recompute focusable widgets while preserving the current focus."""
        with self._lock:
            self._refresh_focus()

    def focus(self, widget: Widget) -> bool:
        """Focus ``widget`` and return whether it is currently focusable.

        Applications use this to choose an intentional initial focus target,
        such as a chat composer, instead of accepting the first widget found
        during tree traversal.
        """
        with self._lock:
            if widget not in self._focus_targets:
                self._refresh_focus()
            if widget not in self._focus_targets:
                return False
            self._focus_on(widget)
            return True

    def _refresh_focus(self) -> None:
        previous = self._focused_widget()
        for target in self._focus_targets:
            target._focused = False
        self._focus_targets = []
        if self._modals:
            self._focus_targets = list(self._collect_focusables(self._modals[-1]))
        if not self._focus_targets and self.root is not None:
            self._focus_targets = list(self._collect_focusables(self.root))
        if not self._focus_targets:
            self._focus_idx = 0
            return
        if previous in self._focus_targets:
            self._focus_idx = self._focus_targets.index(previous)
        else:
            self._focus_idx = min(self._focus_idx, len(self._focus_targets) - 1)
        self._focus_targets[self._focus_idx]._focused = True

    def run(self) -> None:
        if self.root is None:
            raise RuntimeError("App.set_root() must be called before run()")
        if self.force_terminal is False or not self._is_tty():
            raise RuntimeError(
                "App.run() requires an interactive terminal "
                "(set force_terminal=True to bypass this check)."
            )

        self._enable_tui()
        try:
            self._initial_layout()
            self._stop_event.clear()
            self._render_thread = threading.Thread(
                target=self._render_loop, name="ascii-tui-render", daemon=True
            )
            self._input_thread = threading.Thread(
                target=self._input_loop, name="ascii-tui-input", daemon=True
            )
            self._render_thread.start()
            self._input_thread.start()
            self._event_loop()
        finally:
            self._stop_event.set()
            if self._render_thread and self._render_thread.is_alive():
                self._render_thread.join(timeout=1.5)
            # Input can remain blocked in the OS console API. It is a daemon;
            # never hang application shutdown waiting for another keypress.
            self._disable_tui()

    def _input_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                key = _read_key()
            except (KeyboardInterrupt, EOFError, OSError):
                self._stop_event.set()
                return
            if key:
                self._events.put(key)

    def _event_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                event = self._events.get(timeout=0.1)
            except queue.Empty:
                continue
            with self._lock:
                if callable(event) and not isinstance(event, MouseEvent):
                    event()
                elif isinstance(event, MouseEvent):
                    self._dispatch_mouse(event)
                else:
                    key = _KEY_ALIASES.get(event, event)
                    self._dispatch_key(key)

    # ------------------------------------------------------------ TUI plumbing
    def _is_tty(self) -> bool:
        try:
            return bool(self.stream.isatty())
        except Exception:
            return False

    def _enable_tui(self) -> None:
        from ascii_colors.utils import (
            enable_windows_vt_input,
            set_windows_ctrl_c_ignored,
        )

        set_windows_ctrl_c_ignored(True)
        enable_windows_vt_input(self.mouse)
        sequence = []
        if self.alt_screen:
            sequence.append("\033[?1049h")
        if self.hide_cursor:
            sequence.append("\033[?25l")
        if self.mouse:
            sequence.append("\033[?1000h\033[?1002h\033[?1006h")
        sequence.append("\033[2J\033[H")
        self.stream.write("".join(sequence))
        self.stream.flush()

    def _disable_tui(self) -> None:
        from ascii_colors.utils import (
            enable_windows_vt_input,
            set_windows_ctrl_c_ignored,
        )

        set_windows_ctrl_c_ignored(False)
        enable_windows_vt_input(False)
        sequence = []
        if self.mouse:
            sequence.append("\033[?1006l\033[?1002l\033[?1000l")
        if self.hide_cursor:
            sequence.append("\033[?25h")
        if self.alt_screen:
            sequence.append("\033[?1049l")
        try:
            self.stream.write("".join(sequence))
            self.stream.flush()
        except Exception:
            pass

    def _initial_layout(self) -> None:
        width, height = self._get_terminal_size()
        self.width, self.height = width, height
        self.buffer = ScreenBuffer(width, height)
        self.root.layout(0, 0, width, height)
        self._refresh_focus()

    def _get_terminal_size(self):
        try:
            columns, lines = os.get_terminal_size(self.stream.fileno())
            return max(10, columns), max(3, lines)
        except Exception:
            size = shutil.get_terminal_size(fallback=(80, 24))
            return max(10, size.columns), max(3, size.lines)

    def _layout_modal(self, modal: Widget) -> None:
        modal_width = modal.w or modal.min_width or max(20, self.width // 2)
        modal_height = modal.h or modal.min_height or max(5, self.height // 3)
        modal_width = min(modal_width, self.width)
        modal_height = min(modal_height, self.height)
        x = modal.x if modal.x > 0 else max(0, (self.width - modal_width) // 2)
        y = modal.y if modal.y > 0 else max(0, (self.height - modal_height) // 2)
        modal.layout(x, y, modal_width, modal_height)

    def _collect_focusables(self, widget: Widget) -> Iterator[Widget]:
        if not widget.visible:
            return
        if isinstance(widget, Container):
            for child in widget.children:
                yield from self._collect_focusables(child)
        if widget.focusable:
            yield widget

    def refresh(self, *, clear: bool = False) -> None:
        """Relayout and repaint the application immediately.

        Use this after changing several pieces of application state at once,
        such as applying settings or replacing a generator. Rendering remains
        synchronized with the background renderer through the app lock.

        ``clear=True`` also clears the physical terminal before repainting;
        this is useful after overlays close or stale cells are visible.
        """
        with self._lock:
            if self.root is None or self.width <= 0 or self.height <= 0:
                return
            if clear:
                self.renderer.clear_screen()
            self._draw_frame(force=True)

    def _draw_frame(self, *, force: bool = False) -> None:
        self._resize_if_needed()
        self.root.layout(0, 0, self.width, self.height)
        self.buffer.clear()
        self.root.draw(self.buffer)
        for modal in self._modals:
            self._layout_modal(modal)
            modal.draw(self.buffer)
        self.renderer.draw(self.buffer, force=force)

    def _render_loop(self) -> None:
        interval = 1.0 / self.fps
        while not self._stop_event.is_set():
            with self._lock:
                try:
                    self._draw_frame()
                except Exception as exc:
                    try:
                        message = (
                            f"\033[1;1H[RENDER ERROR: "
                            f"{type(exc).__name__}: {str(exc)[:80]}]\033[K"
                        )
                        self.stream.write(message)
                        self.stream.flush()
                    except Exception:
                        pass
            self._stop_event.wait(interval)

    def _resize_if_needed(self) -> None:
        width, height = self._get_terminal_size()
        if width == self.width and height == self.height:
            return
        self.width, self.height = width, height
        self.buffer.resize(width, height)
        self.renderer.clear_screen()

    # ------------------------------------------------------------ mouse dispatch
    @staticmethod
    def _point_in_widget(widget: Widget, x: int, y: int) -> bool:
        return widget.visible and widget.contains(x, y)

    def _deepest_at(self, widget: Widget, x: int, y: int) -> Optional[Widget]:
            if not widget.visible:
                return None
            if getattr(widget, "completion_active", False):
                count = min(6, len(widget.completion_items))
                top = max(0, widget.y - count)
                if widget.x <= x < widget.x + widget.w and top <= y < top + count:
                    return widget
            if not self._point_in_widget(widget, x, y):
                return None
            if isinstance(widget, Container):
                for child in reversed(widget.children):
                    found = self._deepest_at(child, x, y)
                    if found is not None:
                        return found
            return widget
    def _widget_at(self, x: int, y: int) -> Optional[Widget]:
        if self._modals:
            for modal in reversed(self._modals):
                found = self._deepest_at(modal, x, y)
                if found is not None:
                    return found
            return None
        return self._deepest_at(self.root, x, y) if self.root else None

    def _set_hovered(self, widget: Optional[Widget]) -> None:
        if widget is self._hovered:
            return
        if self._hovered is not None:
            self._hovered.hovered = False
            self._hovered.on_mouse_leave()
        self._hovered = widget
        if widget is not None:
            widget.hovered = True
            widget.on_mouse_enter()

    def _focus_on(self, widget: Widget) -> None:
        if widget not in self._focus_targets:
            return
        current = self._focused_widget()
        if current is not None:
            current._focused = False
        self._focus_idx = self._focus_targets.index(widget)
        widget._focused = True

    def _dispatch_mouse(self, mouse: MouseEvent) -> None:
        if self.on_mouse is not None:
            self.on_mouse(mouse)

        target = self._mouse_capture or self._widget_at(mouse.x, mouse.y)
        self._set_hovered(target)
        if target is None:
            return

        if mouse.action == "press" and mouse.button in ("left", "middle", "right"):
            self._mouse_capture = target
            if target.focusable:
                self._focus_on(target)

        node: Optional[Widget] = target
        while node is not None:
            if node.handle_mouse(mouse):
                break
            if mouse.action == "wheel":
                node = node.parent
            else:
                break

        if mouse.action == "release":
            self._mouse_capture = None

    # ------------------------------------------------------------ key dispatch
    def _focused_widget(self) -> Optional[Widget]:
        if not self._focus_targets:
            return None
        return self._focus_targets[self._focus_idx % len(self._focus_targets)]

    def _cycle_focus(self, delta: int) -> None:
        if not self._focus_targets:
            return
        current = self._focused_widget()
        if current:
            current._focused = False
        self._focus_idx = (self._focus_idx + delta) % len(self._focus_targets)
        focused = self._focused_widget()
        if focused:
            focused._focused = True

    def _dispatch_key(self, key: str) -> None:
        # A modal owns Escape while it is open. Global quit keys must not
        # terminate the application before the dialog can cancel itself.
        if key in self.quit_keys and not self._modals:
            focused = self._focused_widget()
            if focused is not None and focused.handle_key(key):
                return
            self._stop_event.set()
            return

        binding = self._key_bindings.get(key)
        if binding is not None:
            binding()
            return

        focused = self._focused_widget()
        if key in ("CTRL_C", "CTRL_Q"):
            if not self._modals and (focused is None or not focused.handle_key(key)):
                self._stop_event.set()
            return

        if key in ("TAB", "BACKTAB"):
            if focused is not None and focused.handle_key(key):
                return
            self._cycle_focus(1 if key == "TAB" else -1)
            return

        if focused is not None and focused.handle_key(key):
            return
        if self._modals and key == "ESCAPE":
            # Let custom modal chrome cancel first; ordinary dialogs such as
            # Help still get conventional Escape-to-close behavior.
            if not self._modals[-1].handle_key(key):
                self.pop_modal()