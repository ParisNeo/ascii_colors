# -*- coding: utf-8 -*-
"""
Widget toolkit for the ascii_colors TUI framework.

Every widget knows how to:
  * layout itself inside a rectangular region (``layout``),
  * draw onto a ``ScreenBuffer`` (``draw``),
  * optionally handle keyboard events when focused (``handle_key``).
"""

import time
from typing import Any, Callable, Iterable, Iterator, List, Optional, Sequence, Tuple, Sequence, Tuple

from ascii_colors.constants import ANSI
from ascii_colors.rich.style import RICH_COLOR_MAP
from ascii_colors.rich.text import wcswidth
from ascii_colors.rich.layout import wrap_line_preserving_ansi
from ascii_colors.tui.borders import BORDERS, get_border
from ascii_colors.tui.screen import ScreenBuffer, _ANSI_TERM


# --------------------------------------------------------------------- helpers
_MARKUP_CONSOLE = None


def _markup(text: str) -> str:
    """Apply rich markup lazily without pulling in heavy imports at module load."""
    if "[" not in text:
        return text
    global _MARKUP_CONSOLE
    try:
        if _MARKUP_CONSOLE is None:
            from ascii_colors.rich.console import Console

            _MARKUP_CONSOLE = Console(force_terminal=True)
        return _MARKUP_CONSOLE._apply_markup(text)
    except Exception:
        return text


def _visible_width(text: str) -> int:
    return wcswidth(_ANSI_TERM.sub("", text))


def _resolve_style(style: str) -> str:
    """Normalize a style spec to an ANSI SGR sequence.

    Accepts:
      * empty → ``""``
      * ANSI escapes (kept verbatim)
      * rich-markup fragments like ``"[bold cyan]"`` (converted via ``_markup``)
      * plain color names like ``"cyan"`` (looked up in ``RICH_COLOR_MAP``)

    Unknown values resolve to ``""`` so the renderer can never emit them as
    literal text on screen.
    """
    if not style:
        return ""
    if style.startswith("\x1b"):
        return style
    if "[" in style:
        return _markup(style)
    return RICH_COLOR_MAP.get(style, "")


_FOCUS_BG = RICH_COLOR_MAP.get("bg_bright_black", "\033[100m")
_FOCUS_FG = RICH_COLOR_MAP.get("bright_yellow", "\033[93m")
_DIM = ANSI.style_dim
_GREEN = RICH_COLOR_MAP.get("bright_green", "\033[92m")
_BLUE = RICH_COLOR_MAP.get("bright_blue", "\033[94m")
_CYAN = RICH_COLOR_MAP.get("bright_cyan", "\033[96m")
_BLACK = RICH_COLOR_MAP.get("black", "\033[30m")


def _draw_scrollbar(
    buffer: ScreenBuffer,
    x: int,
    y: int,
    h: int,
    total: int,
    view: int,
    offset: int,
    thumb_style: str = "",
) -> None:
    """Draw a vertical scrollbar at column ``x`` covering ``h`` rows."""
    if h <= 0 or total <= view:
        return
    thumb = max(1, (view * h) // total)
    thumb = min(h, thumb)
    max_offset = max(1, total - view)
    scroll_range = max(0, h - thumb)
    pos = int((scroll_range * max(0, offset)) / max_offset)
    pos = max(0, min(h - thumb, pos))
    bar_style = thumb_style or _DIM
    for i in range(h):
        if pos <= i < pos + thumb:
            buffer.set_cell(x, y + i, "█", bar_style)
        else:
            buffer.set_cell(x, y + i, "│", _DIM)


# ----------------------------------------------------------------------- Widget
class Widget:
    """Base class for all TUI widgets."""

    def __init__(self, style: str = "", pad: int = 0):
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
        self.style = style
        self.pad = pad
        self.parent: Optional["Widget"] = None
        self.focusable = False
        self.visible = True
        self._focused = False
        self.hovered = False
        self.min_height = 0
        self.min_width = 0
        self.flex = 1
        self._app = None

    def _attach_app(self, app) -> None:
        self._app = app
        if isinstance(self, Container):
            for c in self.children:
                c._attach_app(app)

    def layout(self, x: int, y: int, w: int, h: int) -> None:
        self.x, self.y = x, y
        self.w, self.h = max(0, w), max(0, h)

    def draw(self, buffer: ScreenBuffer) -> None:  # noqa: D401 - abstract
        pass

    def measure(self, available_width: int, available_height: int) -> tuple:
        """Return the widget's intrinsic ``(width, height)`` requirements."""
        return self.min_width, self.min_height

    def handle_key(self, key: str) -> bool:
        return False

    def on_mouse_enter(self) -> None:
        """Called when the pointer enters this widget."""

    def on_mouse_leave(self) -> None:
        """Called when the pointer leaves this widget."""

    def contains(self, x: int, y: int) -> bool:
        """Return ``True`` when ``(x, y)`` falls inside this widget's rect."""
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h

    def handle_mouse(self, event) -> bool:
        """Handle a mouse event; return ``True`` when consumed.

        The base widget ignores mouse input. Override in interactive widgets
        (``ListBox``, ``Table``, ``Button``, ``TextInput``, scroll views, …)
        to react to clicks and wheel events.
        """
        return False

    def inner_rect(self):
        return (
            self.x + self.pad,
            self.y + self.pad,
            max(0, self.w - 2 * self.pad),
            max(0, self.h - 2 * self.pad),
        )


class Container(Widget):
    """A widget that contains children."""

    def __init__(self, style: str = "", pad: int = 0):
        super().__init__(style, pad)
        self.children: List[Widget] = []

    def add(self, child: Widget) -> Widget:
        child.parent = self
        self.children.append(child)
        child._attach_app(self._app)
        return child

    def draw(self, buffer: ScreenBuffer) -> None:
        for child in self.children:
            if child.visible:
                child.draw(buffer)

    def layout_children(self) -> None:
        """Override in subclasses to position children."""


class VBox(Container):
    """Stacks children vertically."""

    def __init__(self, gap: int = 0, style: str = "", pad: int = 0):
        super().__init__(style, pad)
        self.gap = gap

    def layout(self, x, y, w, h):
        super().layout(x, y, w, h)
        self.layout_children()

    def layout_children(self) -> None:
            ix, iy, iw, ih = self.inner_rect()
            visible = [child for child in self.children if child.visible]
            for child in self.children:
                if not child.visible:
                    child.layout(ix, iy, 0, 0)
            if not visible or iw <= 0 or ih <= 0:
                return

            gap_total = self.gap * max(0, len(visible) - 1)
            available = max(0, ih - gap_total)
            bases = [max(0, child.measure(iw, available)[1]) for child in visible]
            heights = self._allocate(available, bases, [child.flex for child in visible])

            cur_y = iy
            for child, height in zip(visible, heights):
                child.layout(ix, cur_y, iw, height)
                cur_y += height + self.gap

    @staticmethod
    def _allocate(available: int, bases: List[int], flexes: List[float]) -> List[int]:
        """Allocate an exact total without overflow, rounding gaps, or overlap."""
        if not bases:
            return []
        available = max(0, available)
        total = sum(bases)
        if total <= 0:
            sizes = [0] * len(bases)
            weights = [max(0.0, flex) for flex in flexes]
            # Zero-sized children (notably plain Labels in an HBox) still
            # need to share the available space when none declares flex.
            if sum(weights) <= 0:
                weights = [1.0] * len(bases)
        elif total > available:
            # Proportionally shrink every child when the terminal is too small.
            sizes = []
            cumulative_base = 0
            previous_target = 0
            for base in bases:
                cumulative_base += base
                target = (available * cumulative_base) // total
                sizes.append(max(0, target - previous_target))
                previous_target = target
            return sizes
        else:
            sizes = list(bases)
            weights = [max(0.0, flex) for flex in flexes]

        remaining = available - sum(sizes)
        weight_sum = sum(weights)
        if remaining <= 0 or weight_sum <= 0:
            return sizes

        cumulative_weight = 0.0
        previous_extra = 0
        for index, weight in enumerate(weights):
            cumulative_weight += weight
            target_extra = int(remaining * cumulative_weight / weight_sum)
            sizes[index] += max(0, target_extra - previous_extra)
            previous_extra = target_extra
        return sizes


class HBox(Container):
    """Arranges children horizontally."""

    def __init__(self, gap: int = 0, style: str = "", pad: int = 0):
        super().__init__(style, pad)
        self.gap = gap

    def layout(self, x, y, w, h):
        super().layout(x, y, w, h)
        self.layout_children()

    def layout_children(self) -> None:
            ix, iy, iw, ih = self.inner_rect()
            visible = [child for child in self.children if child.visible]
            for child in self.children:
                if not child.visible:
                    child.layout(ix, iy, 0, 0)
            if not visible or iw <= 0 or ih <= 0:
                return

            gap_total = self.gap * max(0, len(visible) - 1)
            available = max(0, iw - gap_total)
            bases = [max(0, child.measure(available, ih)[0]) for child in visible]
            widths = VBox._allocate(available, bases, [child.flex for child in visible])

            cur_x = ix
            for child, width in zip(visible, widths):
                child.layout(cur_x, iy, width, ih)
                cur_x += width + self.gap


class Box(VBox):
    """A vertical stack surrounded by a border and optional padding."""

    def __init__(
        self,
        *,
        title: Optional[str] = None,
        border: str = "simple",
        border_style: str = "",
        inner_style: str = "",
        chars: Optional[dict] = None,
        padding: int = 1,
        gap: int = 0,
        style: str = "",
        opaque: bool = True,
    ):
        super().__init__(gap=gap, style=style)
        self.title = title
        self.border_style = _resolve_style(border_style) or _DIM
        self.inner_style = _resolve_style(inner_style)
        self.chars = chars if chars is not None else get_border(border)
        self.bordered = bool(self.chars and self.chars.get("h"))
        self.padding = padding
        self.opaque = opaque
        self.min_height = 3 if self.bordered else 1
        self.min_width = 4 if self.bordered else 1

    def inner_rect(self):
        if self.bordered:
            ix = self.x + 1 + self.padding
            iy = self.y + 1 + self.padding
            iw = max(0, self.w - 2 - 2 * self.padding)
            ih = max(0, self.h - 2 - 2 * self.padding)
        else:
            ix = self.x + self.padding
            iy = self.y + self.padding
            iw = max(0, self.w - 2 * self.padding)
            ih = max(0, self.h - 2 * self.padding)
        return ix, iy, iw, ih

    def draw(self, buffer: ScreenBuffer) -> None:
        # Paint the complete surface before drawing children. In particular,
        # modal boxes must obscure the application beneath them rather than
        # behaving like a transparent border floating over the transcript.
        if self.opaque:
            buffer.fill(self.x, self.y, self.w, self.h, " ", self.inner_style)
        if self.bordered:
            buffer.box(self.x, self.y, self.w, self.h, self.chars, self.border_style)
        if self.title and self.w > 4 and self.bordered:
            t = _markup(self.title)
            tw = _visible_width(t) + 2
            tx = self.x + 2
            buffer.fill(tx, self.y, tw, 1, " ", self.border_style)
            buffer.draw_text(tx, self.y, f" {t} ", self.border_style, max_width=self.w - 4)
        super().draw(buffer)


# ------------------------------------------------------------------- leaf widgets
class Label(Widget):
    """A text label. Single-line by default; set ``wrap=True`` for multi-line."""

    def __init__(
        self,
        text: str = "",
        *,
        style: str = "",
        align: str = "left",
        wrap: bool = False,
    ):
        super().__init__(style)
        self.text = text
        self.align = align
        self.wrap = wrap
        self.min_height = 1
        self.flex = 0

    def measure(self, available_width: int, available_height: int) -> tuple:
        if not self.wrap or available_width <= 0:
            return self.min_width, self.min_height
        plain = _ANSI_TERM.sub("", _markup(self.text))
        rows = 0
        for paragraph in plain.split("\n"):
            width = max(0, wcswidth(paragraph))
            rows += max(1, (width + available_width - 1) // available_width)
        return self.min_width, max(self.min_height, rows)

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        rendered = _markup(self.text)
        if self.wrap:
            buffer.draw_wrapped(
                self.x, self.y, self.w, self.h, rendered, self.style, align=self.align
            )
            return
        width = _visible_width(rendered)
        if self.align == "center":
            x = self.x + max(0, (self.w - width) // 2)
        elif self.align == "right":
            x = self.x + max(0, self.w - width)
        else:
            x = self.x
        buffer.draw_text(x, self.y, rendered, self.style, max_width=self.w)


class AsciiArt(Widget):
    """Render multi-line block/Unicode art with alignment and transparency.

    Unlike ``Label``, every line is drawn independently: embedded newlines
    never collapse into one row, spaces can remain transparent, and oversized
    art is clipped instead of forcing the surrounding layout to overflow.
    ``char_styles`` optionally assigns ANSI or rich-markup styles to selected
    characters, enabling shaded block-art without preprocessing the source.
    """

    def __init__(
        self,
        art: Any,
        *,
        style: str = "",
        char_styles: Optional[dict] = None,
        align: str = "center",
        valign: str = "top",
        transparent: bool = True,
    ):
        super().__init__(style)
        self.lines = art.split("\n") if isinstance(art, str) else [str(v) for v in art]
        self.char_styles = char_styles or {}
        self.align = align
        self.valign = valign
        self.transparent = transparent
        self.min_height = len(self.lines)
        self.min_width = 0
        self.flex = 0

    def measure(self, available_width: int, available_height: int) -> tuple:
        width = max((wcswidth(line) for line in self.lines), default=0)
        return width, len(self.lines)

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        visible = self.lines[: self.h]
        y = self.y
        if self.valign == "bottom":
            y += max(0, self.h - len(visible))
        elif self.valign == "center":
            y += max(0, (self.h - len(visible)) // 2)

        base_style = _resolve_style(self.style) or self.style
        for row, line in enumerate(visible):
            line_width = wcswidth(line)
            if line_width <= self.w and self.align == "center":
                x = self.x + (self.w - line_width) // 2
            elif line_width <= self.w and self.align == "right":
                x = self.x + self.w - line_width
            else:
                x = self.x
            cursor = x
            for char in line:
                if cursor >= self.x + self.w:
                    break
                if self.transparent and char == " ":
                    cursor += 1
                    continue
                style = _resolve_style(self.char_styles.get(char, "")) or base_style
                cursor += buffer.draw_text(
                    cursor, y + row, char, style,
                    max_width=max(0, self.x + self.w - cursor),
                )


class Divider(Widget):
    """A horizontal dividing line with an optional centered title."""

    def __init__(self, *, char: str = "─", style: str = "", title: str = ""):
        super().__init__(style or _DIM)
        self.char = char
        self.title = title
        self.min_height = 1
        self.flex = 0

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        buffer.hline(self.x, self.y, self.w, self.char, self.style)
        if self.title:
            t = f" {_markup(self.title)} "
            tw = _visible_width(t)
            x = self.x + max(0, (self.w - tw) // 2)
            buffer.fill(x, self.y, tw, 1, " ", self.style)
            buffer.draw_text(x, self.y, t, self.style, max_width=tw)


class ProgressBar(Widget):
    """A horizontal progress bar (value in 0..100)."""

    def __init__(
        self,
        value: float = 0.0,
        *,
        style: str = "",
        fill_style: str = "",
        empty_style: str = "",
        show_percent: bool = True,
        bar_char: str = "█",
        empty_char: str = "░",
    ):
        super().__init__(style)
        self.value = max(0.0, min(100.0, float(value)))
        self.fill_style = fill_style or _GREEN
        self.empty_style = empty_style or _DIM
        self.show_percent = show_percent
        self.bar_char = bar_char
        self.empty_char = empty_char
        self.min_height = 1
        self.flex = 0

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        pct_text = f" {int(round(self.value)):3d}%" if self.show_percent else ""
        bar_w = max(1, self.w - len(pct_text))
        filled = min(bar_w, int(round((self.value / 100.0) * bar_w)))
        empty = bar_w - filled
        buffer.put(self.x, self.y, self.bar_char * filled, self.fill_style)
        buffer.put(self.x + filled, self.y, self.empty_char * empty, self.empty_style)
        if pct_text:
            buffer.put(self.x + bar_w, self.y, pct_text, self.style)


class Button(Widget):
    """A button activated via ENTER or SPACE."""

    def __init__(
        self,
        label: str,
        *,
        on_press: Optional[Callable[[], None]] = None,
        style: str = "",
        focus_style: str = "",
    ):
        super().__init__(style)
        self.label = label
        self.on_press = on_press
        self.focus_style = focus_style or (ANSI.style_bold + _FOCUS_BG + _FOCUS_FG)
        self.focusable = True
        self.min_height = 1
        self.min_width = len(label) + 2
        self.flex = 0

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        text = f" {self.label} "
        style = self.focus_style if self._focused else self.style
        used = buffer.put(self.x, self.y, text[: self.w], style)
        if used < self.w:
            buffer.put(self.x + used, self.y, " " * (self.w - used), style)

    def handle_key(self, key: str) -> bool:
        if key in ("ENTER", " ") and self.on_press:
            self.on_press()
            return True
        return False

    def handle_mouse(self, event) -> bool:
        if event.action == "press" and event.button == "left":
            if self.contains(event.x, event.y):
                if self.on_press:
                    self.on_press()
                return True
        return False


class ListBox(Widget):
    """A vertically scrollable list with selection and scrollbar."""

    def __init__(
        self,
        items: Iterable[str],
        *,
        style: str = "",
        selected_style: str = "",
        on_select: Optional[Callable[[str, int], None]] = None,
    ):
        super().__init__(style)
        self.items: List[str] = list(items)
        self.selected = 0
        self.scroll = 0
        self.on_select = on_select
        self.selected_style = selected_style or (ANSI.style_bold + _FOCUS_FG)
        self.focusable = True
        self.min_height = 3
        self.min_width = 10
        self.flex = 1

    def _sync_scroll(self) -> None:
        if not self.items:
            self.selected = 0
            self.scroll = 0
            return
        self.selected = max(0, min(len(self.items) - 1, self.selected))
        visible = max(1, self.h)
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + visible:
            self.scroll = self.selected - visible + 1

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        self._sync_scroll()
        visible = self.h
        has_sb = len(self.items) > visible
        text_w = max(1, self.w - (1 if has_sb else 0))
        for row in range(visible):
            idx = self.scroll + row
            y = self.y + row
            if idx >= len(self.items):
                buffer.put(self.x, y, " " * text_w, self.style)
                continue
            item = self.items[idx]
            is_sel = idx == self.selected
            if is_sel and self._focused:
                row_style = ANSI.style_bold + _FOCUS_BG + _FOCUS_FG
            elif is_sel:
                row_style = self.selected_style
            else:
                row_style = self.style
            prefix = "▸ " if is_sel else "  "
            buffer.put(self.x, y, prefix, row_style)
            line = _markup(item)
            used = 2 + buffer.draw_text(
                self.x + 2, y, line, row_style, max_width=max(0, text_w - 2)
            )
            if used < text_w:
                buffer.put(self.x + used, y, " " * (text_w - used), row_style)
        if has_sb:
            _draw_scrollbar(
                buffer, self.x + self.w - 1, self.y, visible,
                len(self.items), visible, self.scroll, _CYAN,
            )

    def handle_key(self, key: str) -> bool:
        if not self.items:
            return False
        if key in ("UP", "k"):
            self.selected = max(0, self.selected - 1)
            return True
        if key in ("DOWN", "j"):
            self.selected = min(len(self.items) - 1, self.selected + 1)
            return True
        if key == "HOME":
            self.selected = 0
            return True
        if key == "END":
            self.selected = len(self.items) - 1
            return True
        if key in ("ENTER", " "):
            if self.on_select:
                self.on_select(self.items[self.selected], self.selected)
            return True
        return False

    def handle_mouse(self, event) -> bool:
        if event.action == "wheel":
            if event.button == "wheel_up":
                self.selected = max(0, self.selected - 1)
                return True
            if event.button == "wheel_down":
                self.selected = min(len(self.items) - 1, self.selected + 1)
                return True
            return False
        if event.action == "press" and event.button == "left":
            if not self.contains(event.x, event.y):
                return False
            idx = self.scroll + (event.y - self.y)
            if 0 <= idx < len(self.items):
                self.selected = idx
                if self.on_select:
                    self.on_select(self.items[idx], idx)
                return True
        return False


class TextInput(Widget):
    """A single-line text editor with cursor and optional submit callback."""

    def __init__(
        self,
        value: str = "",
        *,
        placeholder: str = "",
        style: str = "",
        focus_style: str = "",
        placeholder_style: str = "",
        on_submit: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(style)
        self.value = value
        self.cursor = len(value)
        self.placeholder = placeholder
        self.focus_style = focus_style or (ANSI.style_reverse + _FOCUS_FG)
        self.placeholder_style = placeholder_style or _DIM
        self.on_submit = on_submit
        self.focusable = True
        self.min_height = 1
        self.min_width = 10
        self.flex = 1
        self._scroll = 0

    def _sync_scroll(self) -> None:
        if self.cursor < self._scroll:
            self._scroll = self.cursor
        elif self.cursor >= self._scroll + self.w:
            self._scroll = self.cursor - self.w + 1

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        y = self.y
        if not self.value:
            if self._focused:
                buffer.put(self.x, y, self.placeholder[: max(0, self.w - 1)], self.placeholder_style)
                buffer.set_cell(self.x, y, " ", self.focus_style)
            else:
                buffer.put(self.x, y, self.placeholder[: self.w], self.placeholder_style)
            return
        self.w = max(1, self.w)
        self._sync_scroll()
        visible = self.value[self._scroll : self._scroll + self.w]
        buffer.put(self.x, y, visible, self.style)
        if self._focused:
            cur_x = self.x + (self.cursor - self._scroll)
            if 0 <= cur_x < self.x + self.w:
                if self.cursor < len(self.value):
                    ch = self.value[self.cursor]
                else:
                    ch = " "
                buffer.set_cell(cur_x, y, ch, self.focus_style)

    def handle_key(self, key: str) -> bool:
        if key == "BACKSPACE":
            if self.cursor > 0:
                self.value = self.value[: self.cursor - 1] + self.value[self.cursor :]
                self.cursor -= 1
            return True
        if key == "DELETE":
            if self.cursor < len(self.value):
                self.value = self.value[: self.cursor] + self.value[self.cursor + 1 :]
            return True
        if key == "LEFT":
            self.cursor = max(0, self.cursor - 1)
            return True
        if key == "RIGHT":
            self.cursor = min(len(self.value), self.cursor + 1)
            return True
        if key == "HOME":
            self.cursor = 0
            return True
        if key == "END":
            self.cursor = len(self.value)
            return True
        if key == "ENTER":
            if self.on_submit:
                self.on_submit(self.value)
            return True
        if len(key) == 1 and key.isprintable() and key not in ("\t", "\n", "\r"):
            self.value = self.value[: self.cursor] + key + self.value[self.cursor :]
            self.cursor += 1
            return True
        return False

    def handle_mouse(self, event) -> bool:
        if event.action == "press" and event.button == "left":
            if not self.contains(event.x, event.y):
                return False
            rel = event.x - self.x + self._scroll
            self.cursor = max(0, min(len(self.value), rel))
            return True
        return False


class MultiLineInput(Widget):
    """Multi-line editor with history and interactive text completions.

    Completion providers return ``(typed_prefix, replacement, description)``
    tuples. Suggestions support Up/Down, Tab/Right acceptance, Enter execution,
    Escape dismissal, mouse clicks and wheel navigation.
    """

    def __init__(
        self,
        value: str = "",
        *,
        placeholder: str = "",
        style: str = "",
        focus_style: str = "",
        placeholder_style: str = "",
        on_submit: Optional[Callable[[str], None]] = None,
        max_height: Optional[int] = None,
        completions: Optional[
            Callable[[str, int], Sequence[Tuple[str, str, str]]]
        ] = None,
    ):
        super().__init__(style)
        self.value = value
        self.cursor = len(value)
        self.placeholder = placeholder
        self.focus_style = focus_style or (ANSI.style_reverse + _FOCUS_FG)
        self.placeholder_style = placeholder_style or _DIM
        self.on_submit = on_submit
        self.max_height = max_height
        self.completions = completions
        self.history: List[str] = []
        self._history_idx = -1
        self._history_stash = ""
        self.focusable = True
        self.min_height = 1
        self.min_width = 10
        self.flex = 1
        self._scroll = 0
        self.completion_items: List[Tuple[str, str, str]] = []
        self.completion_selected = 0
        self.completion_start = 0

    @property
    def completion_active(self) -> bool:
        return bool(self.completion_items)

    def _refresh_completions(self) -> None:
        self.completion_items = []
        self.completion_selected = 0
        self.completion_start = self.cursor
        if self.completions is None or self._history_idx != -1:
            return
        try:
            candidates = list(self.completions(self.value, self.cursor))
        except Exception:
            return
        if candidates:
            self.completion_items = candidates
            self.completion_start = max(0, self.cursor - len(candidates[0][0]))

    def _replace_text(self, start: int, end: int, text: str) -> None:
        self.value = self.value[:start] + text + self.value[end:]
        self.cursor = start + len(text)
        self._history_idx = -1
        self._refresh_completions()

    def _accept_completion(self, index: Optional[int] = None) -> bool:
        if not self.completion_items:
            return False
        if index is not None:
            self.completion_selected = max(
                0, min(len(self.completion_items) - 1, index)
            )
        replacement = self.completion_items[self.completion_selected][1]
        self.value = (
            self.value[:self.completion_start]
            + replacement
            + self.value[self.cursor:]
        )
        self.cursor = self.completion_start + len(replacement)
        self.completion_items = []
        return True

    def _layout_lines(self) -> List[tuple]:
        """Map visual lines to slices of the underlying editor value."""
        lines: List[tuple] = []
        width = max(1, self.w)
        start = 0
        length = len(self.value)
        while start <= length:
            end = start
            while end < length and self.value[end] != "\n" and end - start < width:
                end += 1
            lines.append((self.value[start:end], start, end))
            if end >= length:
                break
            start = end + 1 if self.value[end] == "\n" else end
        return lines or [("", 0, 0)]

    def _cursor_row_col(self, lines: List[tuple]) -> tuple:
        for index, (_text, start, end) in enumerate(lines):
            if start <= self.cursor <= end:
                return index, self.cursor - start
        return len(lines) - 1, len(lines[-1][0])

    def _sync_scroll(self, lines: Optional[List[tuple]] = None) -> None:
        lines = lines if lines is not None else self._layout_lines()
        row, _column = self._cursor_row_col(lines)
        if self.h <= 0:
            self._scroll = 0
            return
        if row < self._scroll:
            self._scroll = row
        elif row >= self._scroll + self.h:
            self._scroll = row - self.h + 1
        self._scroll = max(0, min(self._scroll, max(0, len(lines) - self.h)))

    def _line_start(self) -> int:
        return self.value.rfind("\n", 0, self.cursor) + 1

    def _line_end(self) -> int:
        end = self.value.find("\n", self.cursor)
        return len(self.value) if end == -1 else end

    def _on_submit(self) -> None:
        text = self.value
        if text:
            self.history.append(text)
        self._history_idx = -1
        self._history_stash = ""
        self.completion_items = []
        if self.on_submit is not None:
            self.on_submit(text)

    def _completion_window(self) -> tuple:
        count = min(6, len(self.completion_items))
        first = (self.completion_selected // count) * count if count else 0
        top = max(0, self.y - count)
        return first, count, top

    def _handle_completion_key(self, key: str) -> bool:
        if not self.completion_active:
            return False
        if key == "UP":
            self.completion_selected = max(0, self.completion_selected - 1)
        elif key == "DOWN":
            self.completion_selected = min(
                len(self.completion_items) - 1, self.completion_selected + 1
            )
        elif key in ("TAB", "RIGHT"):
            return self._accept_completion()
        elif key == "ENTER":
            self._accept_completion()
            self._on_submit()
        elif key == "ESCAPE":
            self.completion_items = []
        else:
            return False
        return True

    def _draw_completions(self, buffer: ScreenBuffer) -> None:
        if not self.completion_active:
            return
        first, count, top = self._completion_window()
        candidates = self.completion_items[first:first + count]
        width = min(
            self.w,
            max(
                20,
                max(wcswidth(item[1]) + wcswidth(item[2]) + 6 for item in candidates),
            ),
        )
        for row, item in enumerate(candidates):
            selected = first + row == self.completion_selected
            row_style = (
                ANSI.style_bold + _FOCUS_BG + _FOCUS_FG
                if selected
                else ANSI.style_bold + _BLACK + _FOCUS_BG
            )
            buffer.fill(self.x, top + row, width, 1, " ", row_style)
            command = f" {item[1]} "
            buffer.draw_text(
                self.x, top + row, command, row_style, max_width=width
            )
            description = f" {item[2]}"
            description_x = self.x + max(
                len(command), width - wcswidth(description)
            )
            buffer.draw_text(
                description_x,
                top + row,
                description,
                _DIM + _BLACK + _FOCUS_BG,
                max_width=max(0, self.x + width - description_x),
            )

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        if not self.value:
            if self._focused:
                buffer.draw_text(
                    self.x,
                    self.y,
                    self.placeholder,
                    self.placeholder_style,
                    max_width=max(0, self.w - 1),
                )
                buffer.set_cell(self.x, self.y, " ", self.focus_style)
            else:
                buffer.draw_text(
                    self.x, self.y, self.placeholder, self.placeholder_style,
                    max_width=self.w,
                )
        else:
            lines = self._layout_lines()
            self._sync_scroll(lines)
            cursor_row, cursor_column = self._cursor_row_col(lines)
            for row in range(self.h):
                line_index = self._scroll + row
                y = self.y + row
                buffer.put(self.x, y, " " * self.w, self.style)
                if line_index < len(lines):
                    buffer.draw_text(
                        self.x, y, lines[line_index][0], self.style,
                        max_width=self.w,
                    )
            if self._focused:
                screen_row = cursor_row - self._scroll
                cursor_x = self.x + cursor_column
                if 0 <= screen_row < self.h and cursor_x < self.x + self.w:
                    line_text = lines[cursor_row][0]
                    character = (
                        line_text[cursor_column]
                        if cursor_column < len(line_text)
                        else " "
                    )
                    buffer.set_cell(
                        cursor_x, self.y + screen_row, character, self.focus_style
                    )
        if self._focused:
            self._draw_completions(buffer)

    def _navigate_history(self, direction: int) -> bool:
        if direction < 0 and not self.value and self.history:
            if self._history_idx == -1:
                self._history_stash = self.value
                self._history_idx = len(self.history) - 1
            else:
                self._history_idx = max(0, self._history_idx - 1)
            self.value = self.history[self._history_idx]
        elif direction > 0 and self._history_idx != -1:
            if self._history_idx < len(self.history) - 1:
                self._history_idx += 1
                self.value = self.history[self._history_idx]
            else:
                self._history_idx = -1
                self.value = self._history_stash
        else:
            return False
        self.cursor = len(self.value)
        self.completion_items = []
        return True

    def handle_key(self, key: str) -> bool:
        if self._handle_completion_key(key):
            return True
        if key == "ENTER":
            self._on_submit()
            return True
        if key in ("CTRL_J", "ALT_ENTER"):
            self._replace_text(self.cursor, self.cursor, "\n")
            return True
        if key == "BACKSPACE":
            if self.cursor > 0:
                self._replace_text(self.cursor - 1, self.cursor, "")
            return True
        if key == "DELETE":
            if self.cursor < len(self.value):
                self._replace_text(self.cursor, self.cursor + 1, "")
            return True
        if key == "LEFT":
            self.cursor = max(0, self.cursor - 1)
            self._refresh_completions()
            return True
        if key == "RIGHT":
            self.cursor = min(len(self.value), self.cursor + 1)
            self._refresh_completions()
            return True
        if key in ("HOME", "CTRL_A"):
            self.cursor = self._line_start()
            self._refresh_completions()
            return True
        if key in ("END", "CTRL_E"):
            self.cursor = self._line_end()
            self._refresh_completions()
            return True
        if key == "CTRL_U":
            self._replace_text(0, len(self.value), "")
            return True
        if key == "CTRL_W":
            start = self.cursor
            while start > 0 and self.value[start - 1].isspace():
                start -= 1
            while start > 0 and not self.value[start - 1].isspace():
                start -= 1
            self._replace_text(start, self.cursor, "")
            return True
        if key in ("UP", "DOWN"):
            if self._navigate_history(-1 if key == "UP" else 1):
                return True
            lines = self._layout_lines()
            row, column = self._cursor_row_col(lines)
            target = row + (-1 if key == "UP" else 1)
            if 0 <= target < len(lines):
                _text, start, end = lines[target]
                self.cursor = start + min(column, end - start)
                self._refresh_completions()
            return True
        if len(key) == 1 and key.isprintable() and key != "\t":
            self._replace_text(self.cursor, self.cursor, key)
            return True
        return False

    def handle_mouse(self, event) -> bool:
        if self.completion_active:
            first, count, top = self._completion_window()
            inside_popup = (
                top <= event.y < top + count
                and self.x <= event.x < self.x + self.w
            )
            if event.action == "wheel":
                return self._handle_completion_key(
                    "UP" if event.button == "wheel_up" else "DOWN"
                )
            if (
                event.action == "press"
                and event.button == "left"
                and inside_popup
            ):
                index = first + event.y - top
                if index < len(self.completion_items):
                    return self._accept_completion(index)
        if event.action != "press" or event.button != "left":
            return False
        if not self.contains(event.x, event.y):
            return False
        lines = self._layout_lines()
        row = self._scroll + event.y - self.y
        if 0 <= row < len(lines):
            text, start, _end = lines[row]
            column = max(0, min(len(text), event.x - self.x))
            self.cursor = start + column
            self._refresh_completions()
        return True


class ChatView(Widget):

    def _handle_completion_key(self, key: str) -> bool:
        if not self.completion_active:
            return False
        if key == "UP":
            self.completion_selected = max(0, self.completion_selected - 1)
            return True
        if key == "DOWN":
            self.completion_selected = min(
                len(self.completion_items) - 1, self.completion_selected + 1
            )
            return True
        if key in ("TAB", "RIGHT"):
            return self._accept_completion()
        if key == "ENTER":
            self._accept_completion()
            self._on_submit()
            return True
        if key == "ESCAPE":
            self.completion_items = []
            return True
        return False

    def handle_key(self, key: str) -> bool:
        if self._handle_completion_key(key):
            return True
        if key in ("ENTER",):
            self._on_submit()
            return True
        if key in ("CTRL_J", "ALT_ENTER"):
            self._replace_text(self.cursor, self.cursor, "\n")
            return True
        if key == "BACKSPACE":
            if self.cursor > 0:
                self._replace_text(self.cursor - 1, self.cursor, "")
            return True
        if key == "DELETE":
            if self.cursor < len(self.value):
                self._replace_text(self.cursor, self.cursor + 1, "")
            return True
        if key == "LEFT":
            self.cursor = max(0, self.cursor - 1)
            self._refresh_completions()
            return True
        if key == "RIGHT":
            self.cursor = min(len(self.value), self.cursor + 1)
            self._refresh_completions()
            return True
        if key == "HOME" or key == "CTRL_A":
            self.cursor = self._line_start()
            self._refresh_completions()
            return True
        if key == "END" or key == "CTRL_E":
            self.cursor = self._line_end()
            self._refresh_completions()
            return True
        if key == "CTRL_U":
            self._replace_text(0, len(self.value), "")
            return True
        if key == "CTRL_W":
            start = self.cursor
            while start > 0 and self.value[start - 1].isspace():
                start -= 1
            while start > 0 and not self.value[start - 1].isspace():
                start -= 1
            self._replace_text(start, self.cursor, "")
            return True
        if key == "UP":
            if not self.value and self.history:
                if self._history_idx == -1:
                    self._history_stash = self.value
                    self._history_idx = len(self.history) - 1
                elif self._history_idx > 0:
                    self._history_idx -= 1
                self.value = self.history[self._history_idx]
                self.cursor = len(self.value)
                return True
            lines = self._layout_lines()
            row, col = self._cursor_row_col(lines)
            if row > 0:
                _text, start, end = lines[row - 1]
                self.cursor = start + min(col, end - start)
            return True
        if key == "DOWN":
            if self._history_idx != -1:
                if self._history_idx < len(self.history) - 1:
                    self._history_idx += 1
                    self.value = self.history[self._history_idx]
                else:
                    self._history_idx = -1
                    self.value = self._history_stash
                self.cursor = len(self.value)
                return True
            lines = self._layout_lines()
            row, col = self._cursor_row_col(lines)
            if row < len(lines) - 1:
                _text, start, end = lines[row + 1]
                self.cursor = start + min(col, end - start)
            return True
        if len(key) == 1 and key.isprintable() and key not in ("\t",):
            self._replace_text(self.cursor, self.cursor, key)
            return True
        return False

    def handle_mouse(self, event) -> bool:
        if self.completion_active:
            rows = min(6, len(self.completion_items))
            top = self.completion_selected // rows
            popup_y = max(0, self.y - rows)
            if event.action == "press" and event.button == "left":
                if popup_y <= event.y < popup_y + rows and self.x <= event.x < self.x + self.w:
                    index = top * rows + event.y - popup_y
                    if index < len(self.completion_items):
                        return self._accept_completion(index)
            if event.action == "wheel":
                return self._handle_completion_key(
                    "UP" if event.button == "wheel_up" else "DOWN"
                )
        if event.action != "press" or event.button != "left":
            return False
        if not self.contains(event.x, event.y):
            return False
        lines = self._layout_lines()
        row_idx = self._scroll + (event.y - self.y)
        if 0 <= row_idx < len(lines):
            text, start, _end = lines[row_idx]
            col = max(0, min(len(text), event.x - self.x))
            self.cursor = start + col
            self._refresh_completions()
            return True
        return False


class ChatView(Widget):
    """A scrollable, streaming-friendly chat transcript.

    Renders a list of ``{"role", "content"}`` messages, each prefixed by a
    role-coloured label header and wrapped to the available width. Designed
    for streaming: use :meth:`append_to_last` / :meth:`update_last` to feed
    incremental model output while keeping the view pinned to the bottom
    unless the user has scrolled up.
    """

    def __init__(
        self,
        messages: Optional[Iterable[dict]] = None,
        *,
        user_style: str = "",
        assistant_style: str = "",
        system_style: str = "",
        tool_style: str = "",
        error_style: str = "",
        user_label: str = "You",
        assistant_label: str = "AI",
        system_label: str = "system",
        tool_label: str = "tool",
        error_label: str = "error",
        show_labels: bool = True,
    ):
        super().__init__()
        self.messages: List[dict] = []
        if messages:
            for message in messages:
                self.messages.append(
                    {
                        "role": message.get("role", "user"),
                        "content": message.get("content", ""),
                    }
                )
        self.user_style = user_style
        self.assistant_style = assistant_style
        self.system_style = system_style
        self.tool_style = tool_style
        self.error_style = error_style
        if not self.user_style:
            self.user_style = ANSI.style_bold + _CYAN
        if not self.assistant_style:
            self.assistant_style = _GREEN
        if not self.system_style:
            self.system_style = _DIM
        if not self.tool_style:
            self.tool_style = RICH_COLOR_MAP.get("bright_yellow", "\033[93m")
        if not self.error_style:
            self.error_style = RICH_COLOR_MAP.get("bright_red", "\033[91m")
        self.user_label = user_label
        self.assistant_label = assistant_label
        self.system_label = system_label
        self.tool_label = tool_label
        self.error_label = error_label
        self.show_labels = show_labels
        self.focusable = True
        self.min_height = 5
        self.min_width = 20
        self.flex = 1
        self.scroll = 0
        self._dirty = True
        self._lines: List[tuple] = []
        self._last_width = -1
        self._auto_scroll = True

    def add_message(self, role: str, content: str) -> int:
        self.messages.append({"role": role, "content": content or ""})
        self._dirty = True
        self._auto_scroll = True
        return len(self.messages) - 1

    def update_last(self, content: str) -> None:
        if not self.messages:
            self.add_message("assistant", content or "")
            return
        self.messages[-1]["content"] = content or ""
        self._dirty = True
        self._auto_scroll = True

    def append_to_last(self, chunk: str) -> None:
        if not self.messages:
            self.add_message("assistant", "")
        self.messages[-1]["content"] = (
            self.messages[-1].get("content") or ""
        ) + (chunk or "")
        self._dirty = True
        self._auto_scroll = True

    def clear(self) -> None:
        self.messages = []
        self._dirty = True
        self._auto_scroll = True

    def scroll_to_end(self) -> None:
        self._rebuild_lines_if_needed()
        self.scroll = max(0, len(self._lines) - self.h)
        self._auto_scroll = True

    def scroll_up(self, n: int = 1) -> None:
        self.scroll = max(0, self.scroll - n)
        self._auto_scroll = False

    def scroll_down(self, n: int = 1) -> None:
        max_scroll = max(0, len(self._lines) - self.h)
        self.scroll = min(max_scroll, self.scroll + n)
        if self.scroll >= max_scroll:
            self._auto_scroll = True

    def handle_key(self, key: str) -> bool:
        self._rebuild_lines_if_needed()
        if key in ("UP", "k"):
            self.scroll_up(1)
            return True
        if key in ("DOWN", "j"):
            self.scroll_down(1)
            return True
        if key == "PAGE_UP":
            self.scroll_up(max(1, self.h - 1))
            return True
        if key == "PAGE_DOWN":
            self.scroll_down(max(1, self.h - 1))
            return True
        if key == "HOME":
            self.scroll = 0
            self._auto_scroll = False
            return True
        if key == "END":
            self.scroll_to_end()
            return True
        if key == "CTRL_L":
            self.clear()
            return True
        return False

    def handle_mouse(self, event) -> bool:
        if event.action != "wheel":
            return False
        if event.button == "wheel_up":
            self.scroll_up(3)
            return True
        if event.button == "wheel_down":
            self.scroll_down(3)
            return True
        return False

    def _rebuild_lines_if_needed(self) -> None:
        available_width = max(1, self.w - 3)
        if not self._dirty and self._last_width == available_width:
            return
        self._last_width = available_width
        self._dirty = False
        self._lines = []
        label_of = {
            "user": self.user_label,
            "assistant": self.assistant_label,
            "system": self.system_label,
            "tool": self.tool_label,
            "error": self.error_label,
        }
        style_of = {
            "user": self.user_style,
            "assistant": self.assistant_style,
            "system": self.system_style,
            "tool": self.tool_style,
            "error": self.error_style,
        }
        for i, message in enumerate(self.messages):
            role = message.get("role", "user")
            role = role if role in style_of else "assistant"
            line_style = style_of[role] or _DIM
            if i > 0:
                self._lines.append((role, "", ""))
            if self.show_labels:
                label = label_of.get(role, role)
                self._lines.append((role, f"┤ {label} ├", line_style))
            content = _markup(message.get("content", "") or "")
            for raw_line in content.split("\n"):
                for wrapped in wrap_line_preserving_ansi(raw_line, available_width):
                    self._lines.append((role, wrapped, line_style))

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        self._rebuild_lines_if_needed()
        total = len(self._lines)
        view_h = self.h
        max_scroll = max(0, total - view_h)
        if self._auto_scroll:
            self.scroll = max_scroll
        else:
            self.scroll = max(0, min(self.scroll, max_scroll))
        has_sb = total > view_h
        content_w = max(1, self.w - (1 if has_sb else 0))
        for row in range(view_h):
            y = self.y + row
            buffer.put(self.x, y, " " * self.w, self.style)
            idx = self.scroll + row
            if idx >= total:
                continue
            _role, text, line_style = self._lines[idx]
            if not text:
                continue
            if self.w > 2:
                buffer.draw_text(
                    self.x + 2,
                    y,
                    text,
                    line_style or self.style,
                    max_width=max(0, content_w - 2),
                )
        if has_sb:
            _draw_scrollbar(
                buffer,
                self.x + self.w - 1,
                self.y,
                view_h,
                total,
                view_h,
                self.scroll,
                _CYAN,
            )


# ---------------------------------------------------------------- data widgets
class Table(Widget):
    """A scrollable, selectable data grid with headers, alignment and scrollbar."""

    def __init__(
        self,
        headers: List[str],
        rows: Iterable[List[str]],
        *,
        style: str = "",
        header_style: str = "",
        selected_style: str = "",
        on_select: Optional[Callable[[List[str], int], None]] = None,
        column_widths: Optional[List[int]] = None,
        column_aligns: Optional[List[str]] = None,
    ):
        super().__init__(style)
        self.headers = list(headers)
        self.rows = [list(r) for r in rows]
        self.selected = 0
        self.scroll = 0
        self.header_style = header_style or (ANSI.style_bold + _CYAN)
        self.selected_style = selected_style or (ANSI.style_bold + _FOCUS_BG + _FOCUS_FG)
        self.on_select = on_select
        self.column_widths = column_widths
        self.column_aligns = column_aligns or ["left"] * len(self.headers)
        self.focusable = True
        self.min_height = 3
        self.min_width = 20
        self.flex = 1

    def _widths(self) -> List[int]:
        n = len(self.headers)
        if self.column_widths is not None:
            return list(self.column_widths)
        widths = [max(1, wcswidth(h)) for h in self.headers]
        for row in self.rows:
            for i in range(min(n, len(row))):
                w = wcswidth(_ANSI_TERM.sub("", str(row[i])))
                if w > widths[i]:
                    widths[i] = w
        return widths

    def _sync_scroll(self) -> None:
        if not self.rows:
            self.selected = 0
            self.scroll = 0
            return
        self.selected = max(0, min(len(self.rows) - 1, self.selected))
        visible = max(1, self.h - 2)
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + visible:
            self.scroll = self.selected - visible + 1

    def _draw_cells(
        self, buffer: ScreenBuffer, y: int, cells: List[str], widths: List[int], style: str, total_w: int
    ) -> None:
        cx = self.x
        n = len(self.headers)
        for i in range(n):
            remaining = total_w - (cx - self.x)
            if remaining <= 0:
                break
            avail = min(max(1, widths[i]), remaining) if i < n - 1 else remaining
            text = _markup(str(cells[i])) if i < len(cells) else ""
            content_w = wcswidth(_ANSI_TERM.sub("", text))
            align = self.column_aligns[i] if i < len(self.column_aligns) else "left"
            if align == "right":
                pad = max(0, avail - content_w)
                buffer.put(cx, y, " " * pad, style)
                buffer.draw_text(cx + pad, y, text, style, max_width=max(0, avail - pad))
            elif align == "center":
                pad = max(0, (avail - content_w) // 2)
                buffer.put(cx, y, " " * pad, style)
                buffer.draw_text(cx + pad, y, text, style, max_width=max(0, avail - pad))
            else:
                buffer.draw_text(cx, y, text, style, max_width=avail)
                if content_w < avail:
                    buffer.put(cx + content_w, y, " " * (avail - content_w), style)
            cx += avail + 1

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        widths = self._widths()
        visible = max(0, self.h - 2)
        has_sb = len(self.rows) > visible and visible > 0
        text_w = max(1, self.w - (1 if has_sb else 0))
        self._draw_cells(buffer, self.y, self.headers, widths, self.header_style, text_w)
        if self.h >= 2:
            sep_w = min(text_w, sum(widths) + max(0, len(widths) - 1))
            buffer.put(self.x, self.y + 1, "─" * sep_w, _DIM)
        if visible <= 0:
            return
        self._sync_scroll()
        for row_i in range(visible):
            idx = self.scroll + row_i
            y = self.y + 2 + row_i
            if idx >= len(self.rows):
                buffer.put(self.x, y, " " * text_w, self.style)
                continue
            is_sel = idx == self.selected
            if is_sel and self._focused:
                row_style = ANSI.style_bold + _FOCUS_BG + _FOCUS_FG
            elif is_sel:
                row_style = self.selected_style
            else:
                row_style = self.style
            if is_sel:
                buffer.put(self.x, y, " " * text_w, row_style)
            self._draw_cells(buffer, y, self.rows[idx], widths, row_style, text_w)
        if has_sb:
            _draw_scrollbar(
                buffer, self.x + self.w - 1, self.y + 2, visible,
                len(self.rows), visible, self.scroll, _CYAN,
            )

    def handle_key(self, key: str) -> bool:
        if not self.rows:
            return False
        if key in ("UP", "k"):
            self.selected = max(0, self.selected - 1)
            return True
        if key in ("DOWN", "j"):
            self.selected = min(len(self.rows) - 1, self.selected + 1)
            return True
        if key == "HOME":
            self.selected = 0
            return True
        if key == "END":
            self.selected = len(self.rows) - 1
            return True
        if key in ("ENTER", " "):
            if self.on_select:
                self.on_select(self.rows[self.selected], self.selected)
            return True
        return False

    def handle_mouse(self, event) -> bool:
        if event.action == "wheel":
            if event.button == "wheel_up":
                self.selected = max(0, self.selected - 1)
                return True
            if event.button == "wheel_down":
                self.selected = min(len(self.rows) - 1, self.selected + 1)
                return True
            return False
        if event.action == "press" and event.button == "left":
            if not self.contains(event.x, event.y):
                return False
            visible = max(0, self.h - 2)
            row_in_view = event.y - (self.y + 2)
            if 0 <= row_in_view < min(visible, len(self.rows) - self.scroll):
                idx = self.scroll + row_in_view
                self.selected = idx
                if self.on_select:
                    self.on_select(self.rows[idx], idx)
                return True
        return False


class Spinner(Widget):
    """An animated single-line spinner (advances each frame via wall clock)."""

    FRAMES_DOTS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    FRAMES_LINE = "|/-\\"
    FRAMES_ARROW = "←↖↑↗→↘↓↙"
    FRAMES_BLOCK = "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁"

    def __init__(
        self,
        *,
        label: str = "",
        frames: Optional[str] = None,
        interval: float = 0.1,
        style: str = "",
        spinner_style: str = "",
    ):
        super().__init__(style)
        self.label = label
        self.frames = frames or self.FRAMES_DOTS
        self.interval = max(0.01, interval)
        self.spinner_style = spinner_style or _FOCUS_FG
        self.min_height = 1
        self.flex = 0
        self._start = time.time()

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        idx = int((time.time() - self._start) / self.interval) % len(self.frames)
        buffer.put(self.x, self.y, self.frames[idx], self.spinner_style)
        if self.label:
            buffer.draw_text(
                self.x + 2, self.y, _markup(self.label), self.style,
                max_width=max(0, self.w - 2),
            )


class Checkbox(Widget):
    """A toggleable boolean control."""

    def __init__(
        self,
        label: str,
        *,
        checked: bool = False,
        on_change: Optional[Callable[[bool], None]] = None,
        style: str = "",
        focus_style: str = "",
    ):
        super().__init__(style)
        self.label = label
        self.checked = checked
        self.on_change = on_change
        self.focus_style = focus_style or (ANSI.style_bold + _FOCUS_BG + _FOCUS_FG)
        self.focusable = True
        self.min_height = 1
        self.min_width = len(label) + 4
        self.flex = 0

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        style = self.focus_style if self._focused else self.style
        box = "[x]" if self.checked else "[ ]"
        buffer.put(self.x, self.y, f"{box} ", style)
        buffer.draw_text(
            self.x + 4, self.y, _markup(self.label), style,
            max_width=max(0, self.w - 4),
        )

    def handle_key(self, key: str) -> bool:
        if key == " ":
            self.checked = not self.checked
            if self.on_change:
                self.on_change(self.checked)
            return True
        return False

    def handle_mouse(self, event) -> bool:
        if event.action == "press" and event.button == "left":
            if self.contains(event.x, event.y):
                self.checked = not self.checked
                if self.on_change:
                    self.on_change(self.checked)
                return True
        return False


class StatusBar(Widget):
    """A chrome bar with left and right aligned segments."""

    def __init__(
        self,
        *,
        left: str = "",
        right: str = "",
        style: str = "",
        pad: int = 1,
    ):
        super().__init__(style)
        self.left = left
        self.right = right
        self.pad = pad
        self.min_height = 1
        self.flex = 0

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        buffer.put(self.x, self.y, " " * self.w, self.style)
        inner_w = max(0, self.w - 2 * self.pad)
        if self.left:
            buffer.draw_text(
                self.x + self.pad, self.y, _markup(self.left), self.style,
                max_width=inner_w,
            )
        if self.right:
            rendered = _markup(self.right)
            rw = _visible_width(rendered)
            x = self.x + self.w - self.pad - rw
            if x > self.x + self.pad:
                buffer.draw_text(x, self.y, rendered, self.style, max_width=rw)


# ------------------------------------------------------------ scroll container
class ScrollView(VBox):
    """A vertically scrollable container with scrollbar and clipping."""

    def __init__(self, *, style: str = "", gap: int = 0, pad: int = 0):
        super().__init__(gap=gap, style=style, pad=pad)
        self.scroll = 0
        self.focusable = True
        self.min_height = 3
        self.flex = 1

    def _content_height(self) -> int:
        if not self.children:
            return 0
        visible = [c for c in self.children if c.visible]
        heights = [max(0, c.min_height) for c in visible]
        return sum(heights) + self.gap * max(0, len(visible) - 1)

    def _max_scroll(self) -> int:
        _, _, _, ih = self.inner_rect()
        return max(0, self._content_height() - ih)

    def _has_sb(self) -> bool:
        _, _, _, ih = self.inner_rect()
        return self._content_height() > ih and ih > 0

    def layout_children(self) -> None:
            ix, iy, iw, ih = self.inner_rect()
            visible = [child for child in self.children if child.visible]
            for child in self.children:
                if not child.visible:
                    child.layout(ix, iy, 0, 0)
            if self._has_sb():
                iw = max(0, iw - 1)
            cur_y = iy - self.scroll
            for child in visible:
                height = max(0, child.measure(iw, ih)[1])
                child.layout(ix, cur_y, iw, height)
                cur_y += height + self.gap

    def draw(self, buffer: ScreenBuffer) -> None:
        super().draw(buffer)
        ix, iy, iw, ih = self.inner_rect()
        for yy in range(self.y, iy):
            buffer.put(self.x, yy, " " * self.w, self.style)
        for yy in range(iy + ih, self.y + self.h):
            buffer.put(self.x, yy, " " * self.w, self.style)
        if self.pad > 0:
            for yy in range(iy, iy + ih):
                buffer.put(self.x, yy, " " * self.pad, self.style)
                buffer.put(ix + iw, yy, " " * self.pad, self.style)
        if self._has_sb():
            _draw_scrollbar(
                buffer, self.x + self.w - 1, iy, ih,
                self._content_height(), ih, self.scroll, _CYAN,
            )

    def handle_key(self, key: str) -> bool:
        _, _, _, ih = self.inner_rect()
        max_scroll = self._max_scroll()
        if key in ("UP", "k"):
            self.scroll = max(0, self.scroll - 1)
            return True
        if key in ("DOWN", "j"):
            self.scroll = min(max_scroll, self.scroll + 1)
            return True
        if key == "PAGE_UP":
            self.scroll = max(0, self.scroll - max(1, ih))
            return True
        if key == "PAGE_DOWN":
            self.scroll = min(max_scroll, self.scroll + max(1, ih))
            return True
        if key == "HOME":
            self.scroll = 0
            return True
        if key == "END":
            self.scroll = max_scroll
            return True
        return False

    def handle_mouse(self, event) -> bool:
        if event.action != "wheel":
            return False
        if event.button == "wheel_up":
            self.scroll = max(0, self.scroll - 3)
            return True
        if event.button == "wheel_down":
            self.scroll = min(self._max_scroll(), self.scroll + 3)
            return True
        return False


# --------------------------------------------------------------------- tabbed
class Tabs(Container):
    """A header row plus swap-in content panels (one visible at a time)."""

    def __init__(
        self,
        *,
        header_style: str = "",
        active_style: str = "",
        style: str = "",
        gap: int = 1,
    ):
        super().__init__(style=style)
        self._labels: List[str] = []
        self.active = 0
        self.header_style = header_style or _DIM
        self.active_style = active_style or (
            ANSI.style_bold + ANSI.style_underline + _CYAN
        )
        self.gap = gap
        self.focusable = True
        self.min_height = 3
        self.min_width = 10
        self.flex = 1

    def add_tab(self, label: str, content: Widget) -> Widget:
        content.visible = not self.children
        self._labels.append(label)
        self.add(content)
        return content

    def _sync_visibility(self) -> None:
        for i, c in enumerate(self.children):
            c.visible = i == self.active

    def layout(self, x, y, w, h):
        super().layout(x, y, w, h)
        self._sync_visibility()
        if 0 <= self.active < len(self.children):
            self.children[self.active].layout(
                self.x, self.y + 1, self.w, max(0, self.h - 1)
            )

    def draw(self, buffer: ScreenBuffer) -> None:
        if not self.children or self.w <= 0 or self.h <= 0:
            return
        cx = self.x
        for i, label in enumerate(self._labels[: len(self.children)]):
            style = self.active_style if i == self.active else self.header_style
            text = f" {label} "
            tw = wcswidth(text)
            if cx + tw > self.x + self.w:
                break
            buffer.put(cx, self.y, text, style)
            cx += tw + self.gap
        if 0 <= self.active < len(self.children):
            self.children[self.active].draw(buffer)

    def handle_key(self, key: str) -> bool:
        if not self.children:
            return False
        if key in ("LEFT", "h"):
            self.active = (self.active - 1) % len(self.children)
        elif key in ("RIGHT", "l"):
            self.active = (self.active + 1) % len(self.children)
        else:
            return False
        self._sync_visibility()
        if self._app is not None:
            self._app.refresh_focus()
        return True

    def handle_mouse(self, event) -> bool:
        if event.action != "press" or event.button != "left":
            return False
        if event.y != self.y or not self.contains(event.x, event.y):
            return False
        cx = self.x
        for i, label in enumerate(self._labels[: len(self.children)]):
            text = f" {label} "
            tw = wcswidth(text)
            if cx <= event.x < cx + tw:
                self.active = i
                self._sync_visibility()
                if self._app is not None:
                    self._app.refresh_focus()
                return True
            cx += tw + self.gap
        return False


# --------------------------------------------------------------------- charts
class Sparkline(Widget):
    """A single-row mini-chart built from horizontal block characters."""

    _CHARS = "▁▂▃▄▅▆▇█"

    def __init__(
        self,
        values: Iterable[float],
        *,
        style: str = "",
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ):
        super().__init__(style or _GREEN)
        self.values = [float(v) for v in values]
        self.min_value = min_value
        self.max_value = max_value
        self.min_height = 1
        self.flex = 0

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0 or not self.values:
            return
        n = len(self.values)
        if n > self.w:
            vals = [self.values[int(i * n / self.w)] for i in range(self.w)]
        else:
            vals = self.values[: self.w]
        lo = self.min_value if self.min_value is not None else min(vals)
        hi = self.max_value if self.max_value is not None else max(vals)
        span = hi - lo
        for i, v in enumerate(vals):
            if span <= 0:
                idx = 0
            else:
                norm = max(0.0, min(1.0, (v - lo) / span))
                idx = int(norm * (len(self._CHARS) - 1))
            buffer.put(self.x + i, self.y, self._CHARS[idx], self.style)


class BarChart(Widget):
    """A vertical bar chart with optional X labels."""

    def __init__(
        self,
        values: Iterable[float],
        *,
        labels: Optional[Iterable[str]] = None,
        style: str = "",
        fill_style: str = "",
        bar_char: str = "█",
        max_value: Optional[float] = None,
        gap: int = 1,
    ):
        super().__init__(style)
        self.values = [float(v) for v in values]
        self.labels = list(labels) if labels else None
        self.fill_style = fill_style or _BLUE
        self.bar_char = bar_char
        self.max_value = max_value
        self.gap = gap
        self.min_height = 4
        self.flex = 1

    def draw(self, buffer: ScreenBuffer) -> None:
        if not self.values or self.w <= 0 or self.h <= 0:
            return
        n = len(self.values)
        label_rows = 1 if (self.labels and self.h >= 2) else 0
        chart_h = self.h - label_rows
        if chart_h <= 0:
            return
        total_gap = self.gap * max(0, n - 1)
        col_w = max(1, (self.w - total_gap) // n)
        mx = self.max_value if self.max_value is not None else max(self.values + [1.0])
        mx = max(mx, 1e-9)
        for i, v in enumerate(self.values):
            x = self.x + i * (col_w + self.gap)
            if x >= self.x + self.w:
                break
            norm = max(0.0, min(1.0, v / mx))
            bar_h = int(round(norm * chart_h))
            top = self.y + chart_h - bar_h
            width = min(col_w, self.w - (x - self.x))
            for row in range(bar_h):
                buffer.put(x, top + row, self.bar_char * width, self.fill_style)
            if label_rows and self.labels and i < len(self.labels):
                lbl = str(self.labels[i])[: max(1, col_w)]
                lw = min(wcswidth(lbl), width)
                pad = max(0, (width - lw) // 2)
                buffer.put(x + pad, self.y + chart_h, lbl[:width], _DIM)


_BIG_DIGITS = {
    "0": ["███", "█ █", "█ █", "█ █", "███"],
    "1": [" █ ", "██ ", " █ ", " █ ", "███"],
    "2": ["███", "  █", "███", "█  ", "███"],
    "3": ["███", "  █", "███", "  █", "███"],
    "4": ["█ █", "█ █", "███", "  █", "  █"],
    "5": ["███", "█  ", "███", "  █", "███"],
    "6": ["███", "█  ", "███", "█ █", "███"],
    "7": ["███", "  █", "  █", "  █", "  █"],
    "8": ["███", "█ █", "███", "█ █", "███"],
    "9": ["███", "█ █", "███", "  █", "███"],
    ".": ["   ", "   ", "   ", "   ", " █ "],
    "%": ["█ █", "  █", " █ ", "█  ", "█ █"],
    "-": ["   ", "   ", "███", "   ", "   "],
}


class BigValue(Widget):
    """A dashboard-style KPI tile: big block digits with an optional label."""

    def __init__(
        self,
        value: Any,
        *,
        label: str = "",
        style: str = "",
        big_style: str = "",
        label_style: str = "",
    ):
        super().__init__(style)
        self.value = str(value)
        self.label = label
        self.big_style = big_style or (ANSI.style_bold + _CYAN)
        self.label_style = label_style or _DIM
        self.min_height = 6 if label else 5
        self.flex = 1

    def _render_rows(self) -> List[str]:
        rows = ["", "", "", "", ""]
        for ch in self.value:
            block = _BIG_DIGITS.get(ch)
            if block is None:
                block = ["   "] * 5
            for i in range(5):
                rows[i] += block[i] + " "
        return rows

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        rows = self._render_rows()
        width = wcswidth(rows[0])
        start_x = self.x + max(0, (self.w - width) // 2)
        for i, row in enumerate(rows[: self.h]):
            buffer.draw_text(start_x, self.y + i, row, self.big_style, max_width=self.w)
        if self.label and self.h > 5:
            lbl = _markup(self.label)
            lw = _visible_width(lbl)
            lx = self.x + max(0, (self.w - lw) // 2)
            buffer.draw_text(lx, self.y + 5, lbl, self.label_style, max_width=self.w)


# 5-row block font used by :class:`BigText`. Each glyph is 5 cells wide.
# Lowercase letters are mapped to uppercase; unknown characters fall back
# to a blank glyph so mixing text with spaces never crashes.
_BIG_FONT = {
    " ": ("     ", "     ", "     ", "     ", "     "),
    "A": (" ███ ", "█   █", "█████", "█   █", "█   █"),
    "B": ("████ ", "█   █", "████ ", "█   █", "████ "),
    "C": (" ████", "█    ", "█    ", "█    ", " ████"),
    "D": ("████ ", "█   █", "█   █", "█   █", "████ "),
    "E": ("█████", "█    ", "████ ", "█    ", "█████"),
    "F": ("█████", "█    ", "████ ", "█    ", "█    "),
    "G": (" ████", "█    ", "█  ██", "█   █", " ████"),
    "H": ("█   █", "█   █", "█████", "█   █", "█   █"),
    "I": ("█████", "  █  ", "  █  ", "  █  ", "█████"),
    "J": ("█████", "    █", "    █", "█   █", " ███ "),
    "K": ("█   █", "█  █ ", "███  ", "█  █ ", "█   █"),
    "L": ("█    ", "█    ", "█    ", "█    ", "█████"),
    "M": ("█   █", "██ ██", "█ █ █", "█   █", "█   █"),
    "N": ("█   █", "██  █", "█ █ █", "█  ██", "█   █"),
    "O": (" ███ ", "█   █", "█   █", "█   █", " ███ "),
    "P": ("████ ", "█   █", "████ ", "█    ", "█    "),
    "Q": (" ███ ", "█   █", "█   █", "█  █ ", " ██ █"),
    "R": ("████ ", "█   █", "████ ", "█  █ ", "█   █"),
    "S": (" ████", "█    ", " ███ ", "    █", "████ "),
    "T": ("█████", "  █  ", "  █  ", "  █  ", "  █  "),
    "U": ("█   █", "█   █", "█   █", "█   █", " ███ "),
    "V": ("█   █", "█   █", "█   █", " █ █ ", "  █  "),
    "W": ("█   █", "█   █", "█ █ █", "██ ██", "█   █"),
    "X": ("█   █", " █ █ ", "  █  ", " █ █ ", "█   █"),
    "Y": ("█   █", " █ █ ", "  █  ", "  █  ", "  █  "),
    "Z": ("█████", "   █ ", "  █  ", " █   ", "█████"),
    "0": (" ███ ", "█  ██", "█ █ █", "██  █", " ███ "),
    "1": ("  █  ", " ██  ", "  █  ", "  █  ", " ███ "),
    "2": (" ███ ", "█   █", "  ██ ", " █   ", "█████"),
    "3": ("████ ", "    █", " ███ ", "    █", "████ "),
    "4": ("█   █", "█   █", "█████", "    █", "    █"),
    "5": ("█████", "█    ", "████ ", "    █", "████ "),
    "6": (" ███ ", "█    ", "████ ", "█   █", " ███ "),
    "7": ("█████", "    █", "   █ ", "  █  ", " █   "),
    "8": (" ███ ", "█   █", " ███ ", "█   █", " ███ "),
    "9": (" ███ ", "█   █", " ████", "    █", " ███ "),
    "-": ("     ", "     ", "█████", "     ", "     "),
    ".": ("     ", "     ", "     ", "     ", "  █  "),
    ",": ("     ", "     ", "     ", "  █  ", " █   "),
    ":": ("     ", "  █  ", "     ", "  █  ", "     "),
    ";": ("     ", "  █  ", "     ", "  █  ", " █   "),
    "!": ("  █  ", "  █  ", "  █  ", "     ", "  █  "),
    "?": (" ███ ", "█   █", "  ██ ", "     ", "  █  "),
    "'": ("  █  ", "  █  ", "     ", "     ", "     "),
    "/": ("    █", "   █ ", "  █  ", " █   ", "█    "),
    "\\": ("█    ", " █   ", "  █  ", "   █ ", "    █"),
    "+": ("     ", "  █  ", "█████", "  █  ", "     "),
    "*": ("     ", "█ █ █", " ███ ", "█ █ █", "     "),
    "=": ("     ", "█████", "     ", "█████", "     "),
    "<": ("   █ ", "  █  ", " █   ", "  █  ", "   █ "),
    ">": (" █   ", "  █  ", "   █ ", "  █  ", " █   "),
    "(": ("   █ ", "  █  ", "  █  ", "  █  ", "   █ "),
    ")": (" █   ", "  █  ", "  █  ", "  █  ", " █   "),
    "[": ("  ██ ", "  █  ", "  █  ", "  █  ", "  ██ "),
    "]": (" ██  ", "  █  ", "  █  ", "  █  ", " ██  "),
    "_": ("     ", "     ", "     ", "     ", "█████"),
    "|": ("  █  ", "  █  ", "  █  ", "  █  ", "  █  "),
    "#": ("█ █ █", "█████", "█ █ █", "█████", "█ █ █"),
    "@": (" ███ ", "█   █", "█ ██ ", "█    ", " ███ "),
    "$": ("  █  ", " ███ ", "█ █  ", " ██  ", "  █  "),
    "%": ("█   █", "   █ ", "  █  ", " █   ", "█   █"),
    "&": (" ██  ", "█  █ ", " ███ ", "█  █ ", " ██ █"),
    "^": ("  █  ", " █ █ ", "     ", "     ", "     "),
    "~": ("     ", " █ █ ", "█ █ █", "     ", "     "),
    "`": (" █   ", "  █  ", "     ", "     ", "     "),
}


class BigText(Widget):
    """A banner rendered from a 5-row block-letter font.

    Supports an optional drop-shadow (offset ``+1`` row / ``+1`` column,
    drawn with ``shadow_style`` underneath the main glyphs) which is what
    produces the classic "HERMES-AGENT" style banner look.

    Parameters
    ----------
    text:
        Source string. Lowercase letters map to their uppercase glyphs;
        unknown characters are rendered as blanks.
    style:
        ANSI / rich-markup style for the main glyphs (default: bold yellow).
    shadow:
        When ``True``, a drop-shadow is rendered behind the glyphs.
    shadow_style:
        Style for the shadow (default: ``bright_black``).
    gap:
        Blank columns between letters (default: ``1``).
    scale:
        Duplicate each glyph cell into a ``scale × scale`` block. ``2`` gives
        a chunky, extra-large banner. Default: ``1``.
    """

    def __init__(
        self,
        text: str,
        *,
        style: str = "",
        shadow: bool = False,
        shadow_style: str = "",
        gap: int = 1,
        scale: int = 1,
        align: str = "center",
        responsive: bool = True,
    ):
        super().__init__(style)
        self.text = str(text)
        self.align = align
        self.responsive = responsive
        self.shadow = shadow
        self.shadow_style = shadow_style or RICH_COLOR_MAP.get("bright_black", "\033[90m")
        self.gap = max(0, gap)
        self.scale = max(1, scale)
        if not self.style:
            self.style = ANSI.style_bold + RICH_COLOR_MAP.get("bright_yellow", "\033[93m")
        self.min_height = 5 * self.scale + (self.scale if shadow else 0)
        self.flex = 0

    def _layout_glyphs(self):
        """Return a 2-D grid whose cells are ``"main"``, ``"shadow"``, or ``None``."""
        chars = [c.upper() for c in self.text]
        glyphs = [_BIG_FONT.get(c, _BIG_FONT[" "]) for c in chars]
        if not glyphs:
            return [[None]]
        glyph_w = len(glyphs[0][0])
        glyph_h = len(glyphs[0])
        stride = glyph_w + self.gap
        total_w = len(glyphs) * stride - (self.gap if glyphs else 0)
        scale = self.scale
        grid_h = glyph_h * scale + (scale if self.shadow else 0)
        grid_w = total_w * scale + (scale if self.shadow else 0)
        grid = [[None] * grid_w for _ in range(grid_h)]

        def stamp(glyphs_iter, row_off, col_off, kind):
            cx = 0
            for glyph in glyphs_iter:
                for ry, row in enumerate(glyph):
                    for rx, ch in enumerate(row):
                        if ch != "█":
                            continue
                        for sy in range(scale):
                            for sx in range(scale):
                                gy = (ry * scale) + sy + row_off
                                gx = (cx + rx) * scale + sx + col_off
                                if 0 <= gy < grid_h and 0 <= gx < grid_w:
                                    grid[gy][gx] = kind
                cx += stride

        if self.shadow:
            stamp(glyphs, scale, scale, "shadow")
        stamp(glyphs, 0, 0, "main")
        return grid

    def draw(self, buffer: ScreenBuffer) -> None:
            if self.w <= 0 or self.h <= 0:
                return
            grid = self._layout_glyphs()
            if not grid or not grid[0]:
                return
            grid_w = len(grid[0])
            grid_h = len(grid)
            main_style = _resolve_style(self.style) or self.style

            # A narrow terminal gets a readable one-line title, not half a glyph.
            if self.responsive and (grid_w > self.w or grid_h > self.h):
                x = self.x + max(0, (self.w - wcswidth(self.text)) // 2)
                y = self.y + max(0, (self.h - 1) // 2)
                buffer.draw_text(x, y, self.text, main_style, max_width=self.w)
                return

            if self.align == "left":
                start_x = self.x
            elif self.align == "right":
                start_x = self.x + max(0, self.w - grid_w)
            else:
                start_x = self.x + max(0, (self.w - grid_w) // 2)

            shadow_style = _resolve_style(self.shadow_style) or self.shadow_style
            for ry, row in enumerate(grid):
                if ry >= self.h:
                    break
                y = self.y + ry
                cx = start_x
                for cell in row:
                    if cx >= self.x + self.w:
                        break
                    if cell == "main":
                        buffer.set_cell(cx, y, "█", main_style)
                    elif cell == "shadow":
                        buffer.set_cell(cx, y, "█", shadow_style)
                    cx += 1