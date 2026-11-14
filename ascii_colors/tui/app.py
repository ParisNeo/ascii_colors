# -*- coding: utf-8 -*-
"""
Application event loop for the ascii_colors TUI framework.

The ``App`` class:
  * enters the terminal's alternate screen buffer,
  * spawns a background render thread (so animations stay smooth even while
    the main thread blocks on keyboard input),
  * dispatches key events to the focused widget,
  * restores the terminal cleanly on exit (including on exceptions).
"""

import os
import shutil
import sys
import threading
from typing import Iterator, List, Optional

from ascii_colors.tui.screen import ScreenBuffer, ScreenRenderer
from ascii_colors.tui.widgets import Container, Widget


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


def _read_key() -> str:
    """Read a single key using the library's cross-platform helper."""
    from ascii_colors.utils import _get_key

    return _get_key(intercept_control=True)


class App:
    """A minimal curses-style application loop."""

    def __init__(
        self,
        *,
        fps: float = 20.0,
        stream=None,
        alt_screen: bool = True,
        hide_cursor: bool = True,
        quit_keys: Optional[List[str]] = None,
        force_terminal: Optional[bool] = None,
    ):
        self.fps = max(1.0, fps)
        self.stream = stream or sys.stdout
        self.alt_screen = alt_screen
        self.hide_cursor = hide_cursor
        self.quit_keys = list(quit_keys) if quit_keys is not None else ["ESCAPE"]
        self.force_terminal = force_terminal

        self.root: Optional[Widget] = None
        self.width = 0
        self.height = 0
        self.buffer = ScreenBuffer(1, 1)
        self.renderer = ScreenRenderer(self.stream)

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._render_thread: Optional[threading.Thread] = None
        self._started = False
        self._focus_targets: List[Widget] = []
        self._focus_idx = 0
        self._modals: List[Widget] = []

    # ------------------------------------------------------------ public API
    def set_root(self, root: Widget) -> None:
        self.root = root
        self._attach_app(root)

    def exit(self) -> None:
        self._stop_event.set()

    def push_modal(self, widget: Widget) -> None:
        """Push a centered modal overlay; keyboard focus is restricted to it."""
        with self._lock:
            widget.parent = None
            self._attach_app(widget)
            self._modals.append(widget)
            self._refresh_focus()

    def pop_modal(self) -> Optional[Widget]:
        """Pop the topmost modal overlay and return it."""
        with self._lock:
            if not self._modals:
                return None
            popped = self._modals.pop()
            self._refresh_focus()
            return popped

    def refresh_focus(self) -> None:
        """Recompute the focusable widgets after structural changes."""
        with self._lock:
            self._refresh_focus()

    def _attach_app(self, widget: Widget) -> None:
        widget._attach_app(self)

    def _refresh_focus(self) -> None:
        for target in self._focus_targets:
            target._focused = False
        self._focus_targets = []
        if self._modals:
            self._focus_targets = list(self._collect_focusables(self._modals[-1]))
        if not self._focus_targets and self.root is not None:
            self._focus_targets = list(self._collect_focusables(self.root))
        if self._focus_targets:
            self._focus_idx = 0
            self._focus_targets[0]._focused = True

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
            self._render_thread = threading.Thread(
                target=self._render_loop, name="ascii-tui-render", daemon=True
            )
            self._stop_event.clear()
            self._render_thread.start()

            while not self._stop_event.is_set():
                if not self._started:
                    continue
                try:
                    key = _read_key()
                except (KeyboardInterrupt, EOFError, OSError):
                    break

                if not key:
                    continue
                key = _KEY_ALIASES.get(key, key)
                with self._lock:
                    self._dispatch_key(key)
        finally:
            self._stop_event.set()
            if self._render_thread and self._render_thread.is_alive():
                self._render_thread.join(timeout=1.5)
            self._disable_tui()

    # ------------------------------------------------------------ TUI plumbing
    def _is_tty(self) -> bool:
        try:
            return bool(self.stream.isatty())
        except Exception:
            return False

    def _enable_tui(self) -> None:
        from ascii_colors.utils import set_windows_ctrl_c_ignored

        set_windows_ctrl_c_ignored(True)
        sequence = []
        if self.alt_screen:
            sequence.append("\033[?1049h")
        if self.hide_cursor:
            sequence.append("\033[?25l")
        sequence.append("\033[2J\033[H")
        self.stream.write("".join(sequence))
        self.stream.flush()

    def _disable_tui(self) -> None:
        from ascii_colors.utils import set_windows_ctrl_c_ignored

        set_windows_ctrl_c_ignored(False)
        sequence = []
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
        self._started = True

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

    def _render_loop(self) -> None:
        interval = 1.0 / self.fps
        while not self._stop_event.is_set():
            with self._lock:
                try:
                    self._resize_if_needed()
                    self.root.layout(0, 0, self.width, self.height)
                    self.buffer.clear()
                    self.root.draw(self.buffer)
                    for modal in self._modals:
                        self._layout_modal(modal)
                        modal.draw(self.buffer)
                    self.renderer.draw(self.buffer)
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
        if key in self.quit_keys:
            self._stop_event.set()
            return

        focused = self._focused_widget()

        if key in ("CTRL_C", "CTRL_Q"):
            # Give the focused widget (and any open modal) first refusal so a
            # text editor can use Ctrl+C for copy. Fall back to quitting when
            # nothing consumes the key and no modal is trapping focus.
            if not self._modals and (focused is None or not focused.handle_key(key)):
                self._stop_event.set()
            return

        if key in ("TAB", "BACKTAB"):
            # Widgets that genuinely want Tab (text editors insert an indent)
            # get it first; everything else keeps the focus-cycling behaviour.
            if focused is not None and focused.handle_key(key):
                return
            self._cycle_focus(1 if key == "TAB" else -1)
            return

        if focused is not None:
            focused.handle_key(key)