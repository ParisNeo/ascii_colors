# -*- coding: utf-8 -*-
"""
Widget toolkit for the ascii_colors TUI framework.

Every widget knows how to:
  * layout itself inside a rectangular region (``layout``),
  * draw onto a ``ScreenBuffer`` (``draw``),
  * optionally handle keyboard events when focused (``handle_key``).
"""

import time
from typing import Any, Callable, Iterable, Iterator, List, Optional

from ascii_colors.constants import ANSI
from ascii_colors.rich.style import RICH_COLOR_MAP
from ascii_colors.rich.text import wcswidth
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

    def handle_key(self, key: str) -> bool:
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
        if not self.children or ih <= 0:
            return
        gap_total = self.gap * max(0, len(self.children) - 1)
        avail = max(0, ih - gap_total)
        min_sum = sum(max(0, c.min_height) for c in self.children)
        flex_sum = sum(max(0, c.flex) for c in self.children if c.flex > 0)
        extra = max(0, avail - min_sum)
        cur_y = iy
        for c in self.children:
            base = max(0, c.min_height)
            share = (extra * max(0, c.flex)) // flex_sum if flex_sum > 0 and c.flex > 0 else 0
            ch = base + share
            c.layout(ix, cur_y, iw, ch)
            cur_y += ch + self.gap


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
        if not self.children or iw <= 0:
            return
        gap_total = self.gap * max(0, len(self.children) - 1)
        avail = max(0, iw - gap_total)
        min_sum = sum(max(0, c.min_width) for c in self.children)
        flex_sum = sum(max(0, c.flex) for c in self.children if c.flex > 0)
        extra = max(0, avail - min_sum)
        cur_x = ix
        for c in self.children:
            base = max(0, c.min_width)
            share = (extra * max(0, c.flex)) // flex_sum if flex_sum > 0 and c.flex > 0 else 0
            cw = base + share
            c.layout(cur_x, iy, cw, ih)
            cur_x += cw + self.gap


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
    ):
        super().__init__(gap=gap, style=style)
        self.title = title
        self.border_style = _resolve_style(border_style) or _DIM
        self.inner_style = _resolve_style(inner_style)
        self.chars = chars if chars is not None else get_border(border)
        self.bordered = bool(self.chars and self.chars.get("h"))
        self.padding = padding
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
        if self.bordered:
            buffer.box(self.x, self.y, self.w, self.h, self.chars, self.border_style)
        if self.inner_style and self.w > 2 and self.h > 2:
            ix, iy, iw, ih = self.inner_rect()
            buffer.fill(ix, iy, iw, ih, " ", self.inner_style)
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
        heights = [max(0, c.min_height) for c in self.children]
        return sum(heights) + self.gap * max(0, len(self.children) - 1)

    def _max_scroll(self) -> int:
        _, _, _, ih = self.inner_rect()
        return max(0, self._content_height() - ih)

    def _has_sb(self) -> bool:
        _, _, _, ih = self.inner_rect()
        return self._content_height() > ih and ih > 0

    def layout_children(self) -> None:
        ix, iy, iw, ih = self.inner_rect()
        if self._has_sb():
            iw = max(0, iw - 1)
        cur_y = iy - self.scroll
        for c in self.children:
            ch = max(0, c.min_height)
            c.layout(ix, cur_y, iw, ch)
            cur_y += ch + self.gap

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