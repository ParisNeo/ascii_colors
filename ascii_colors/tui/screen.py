# -*- coding: utf-8 -*-
"""
Screen buffer and diff-based renderer for TUI applications.

The ``ScreenBuffer`` holds a 2D grid of styled cells. ``ScreenRenderer``
compares the current buffer to the previously-drawn one and emits only the
rows that changed, using ANSI cursor addressing so we never have to clear
the whole screen between frames.
"""

import re
import sys
from typing import List, Optional, Tuple

from ascii_colors.constants import ANSI
from ascii_colors.rich.text import wcswidth

_ANSI_SGR = re.compile(r"\x1b\[([0-9;]*)m")
_ANSI_TERM = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
_ANSI_TERM_CHARS = "ABCDEFGHJKSTfmnsulh"


class Cell:
    """A single character cell with an attached SGR style prefix."""

    __slots__ = ("char", "style")

    def __init__(self, char: str = " ", style: str = ""):
        self.char = char
        self.style = style

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Cell)
            and self.char == other.char
            and self.style == other.style
        )


class ScreenBuffer:
    """A 2D grid of styled characters."""

    def __init__(self, width: int, height: int):
        self.width = max(1, width)
        self.height = max(1, height)
        self.cells: List[List[Cell]] = [
            [Cell() for _ in range(self.width)] for _ in range(self.height)
        ]

    # ------------------------------------------------------------------ shapes
    def resize(self, width: int, height: int) -> None:
        width = max(1, width)
        height = max(1, height)
        new_cells = [[Cell() for _ in range(width)] for _ in range(height)]
        for y in range(min(height, self.height)):
            for x in range(min(width, self.width)):
                new_cells[y][x] = self.cells[y][x]
        self.width = width
        self.height = height
        self.cells = new_cells

    def clear(self) -> None:
        for row in self.cells:
            for cell in row:
                cell.char = " "
                cell.style = ""

    # --------------------------------------------------------------- primitives
    def _erase_wide_conflict(self, x: int, y: int) -> None:
        """Avoid leaving orphan wide-char halves behind when we overwrite a cell."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        cell = self.cells[y][x]
        if cell.char == "" and x - 1 >= 0:
            self.cells[y][x - 1].char = " "
            self.cells[y][x - 1].style = ""
        if cell.char and wcswidth(cell.char) >= 2 and x + 1 < self.width:
            if self.cells[y][x + 1].char == "":
                self.cells[y][x + 1].char = " "
                self.cells[y][x + 1].style = ""

    def set_cell(self, x: int, y: int, char: str, style: str = "") -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        self._erase_wide_conflict(x, y)
        self.cells[y][x].char = char
        self.cells[y][x].style = style

    def put(self, x: int, y: int, text: str, style: str = "") -> int:
        """Draw plain text (no embedded ANSI). Returns cells consumed."""
        if not text or not (0 <= y < self.height):
            return 0
        cx = x
        consumed = 0
        for ch in text:
            cw = wcswidth(ch)
            if cw <= 0:
                continue
            if cx < 0:
                cx += cw
                continue
            if cx + cw > self.width:
                break
            self.set_cell(cx, y, ch, style)
            if cw >= 2 and cx + 1 < self.width:
                self.cells[y][cx + 1].char = ""
                self.cells[y][cx + 1].style = style
            cx += cw
            consumed += cw
        return consumed

    def fill(self, x: int, y: int, w: int, h: int, char: str = " ", style: str = "") -> None:
        """Fill a rectangle with a single character."""
        if not char or w <= 0 or h <= 0:
            return
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.width, x + w), min(self.height, y + h)
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                self.set_cell(xx, yy, char, style)

    def hline(self, x: int, y: int, w: int, char: str = "─", style: str = "") -> None:
        """Draw a horizontal line of ``char`` starting at (x, y)."""
        if w > 0 and char:
            self.put(x, y, char * w, style)

    def vline(self, x: int, y: int, h: int, char: str = "│", style: str = "") -> None:
        """Draw a vertical line of ``char`` starting at (x, y)."""
        if not (0 <= x < self.width) or not char or h <= 0:
            return
        y0 = max(0, y)
        y1 = min(self.height, y + h)
        for yy in range(y0, y1):
            self.set_cell(x, yy, char, style)

    def box(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        chars: dict,
        style: str = "",
    ) -> None:
        """Draw a border using a border-charset dict (see ``tui.borders``)."""
        if w < 2 or h < 2 or not chars or not chars.get("h"):
            return
        tl = chars.get("tl", "┌")
        tr = chars.get("tr", "┐")
        bl = chars.get("bl", "└")
        br = chars.get("br", "┘")
        hz = chars.get("h", "─")
        vt = chars.get("v", "│")
        right, bottom = x + w - 1, y + h - 1
        self.set_cell(x, y, tl, style)
        self.set_cell(right, y, tr, style)
        self.set_cell(x, bottom, bl, style)
        self.set_cell(right, bottom, br, style)
        for i in range(1, w - 1):
            self.set_cell(x + i, y, hz, style)
            self.set_cell(x + i, bottom, hz, style)
        for j in range(1, h - 1):
            self.set_cell(x, y + j, vt, style)
            self.set_cell(right, y + j, vt, style)

    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        style: str = "",
        max_width: Optional[int] = None,
    ) -> int:
        """Draw text with optional embedded ANSI SGR sequences."""
        if not text or not (0 <= y < self.height):
            return 0
        limit = self.width if max_width is None else min(self.width, max(0, x) + max_width)
        cx = x
        consumed = 0
        i = 0
        n = len(text)
        current_style = style

        while i < n and cx < limit:
            if text[i : i + 2] in ("\x1b[", "\033["):
                m = _ANSI_SGR.match(text, i)
                if m:
                    params = m.group(1)
                    if params in ("", "0"):
                        current_style = style
                    else:
                        current_style = current_style + m.group(0)
                    i = m.end()
                    continue
                j = i + 2
                while j < n and text[j] not in _ANSI_TERM_CHARS:
                    j += 1
                if j < n:
                    j += 1
                i = j
                continue

            ch = text[i]
            j = i + 1
            while j < n:
                nxt = text[j]
                cp = ord(nxt)
                if cp in (0xFE0E, 0xFE0F, 0x200B, 0x200C, 0x200D) or (0x0300 <= cp <= 0x036F):
                    ch += nxt
                    j += 1
                else:
                    break

            cw = wcswidth(ch)
            if cw <= 0:
                i = j
                continue
            if cx < 0:
                i = j
                cx += cw
                continue
            if cx + cw > limit:
                break
            self.set_cell(cx, y, ch, current_style)
            if cw >= 2 and cx + 1 < self.width:
                self.cells[y][cx + 1].char = ""
                self.cells[y][cx + 1].style = current_style
            cx += cw
            consumed += cw
            i = j

        return consumed

    # -------------------------------------------------------- wrapped drawing
    @staticmethod
    def width_of(text: str) -> int:
        """Return visible width of ``text`` (ANSI codes stripped)."""
        return wcswidth(_ANSI_TERM.sub("", text))

    def _styled_cells(self, text: str, base_style: str = ""):
        """Tokenize styled text into ``(char, width, style)`` triples."""
        result: List[Tuple[str, int, str]] = []
        current_style = base_style
        i = 0
        n = len(text)
        while i < n:
            if text[i : i + 2] in ("\x1b[", "\033["):
                m = _ANSI_SGR.match(text, i)
                if m:
                    params = m.group(1)
                    if params in ("", "0"):
                        current_style = base_style
                    else:
                        current_style = current_style + m.group(0)
                    i = m.end()
                    continue
                j = i + 2
                while j < n and text[j] not in _ANSI_TERM_CHARS:
                    j += 1
                if j < n:
                    j += 1
                i = j
                continue
            ch = text[i]
            j = i + 1
            while j < n:
                nxt = text[j]
                cp = ord(nxt)
                if cp in (0xFE0E, 0xFE0F, 0x200B, 0x200C, 0x200D) or (0x0300 <= cp <= 0x036F):
                    ch += nxt
                    j += 1
                else:
                    break
            cw = wcswidth(ch)
            if cw > 0:
                result.append((ch, cw, current_style))
            i = j
        return result

    def draw_wrapped(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        text: str,
        style: str = "",
        align: str = "left",
    ) -> int:
        """Word-wrap styled text inside the rectangle (x, y, w, h)."""
        if w <= 0 or h <= 0 or not text:
            return 0
        cells = self._styled_cells(text, style)
        if not cells:
            return 0

        lines: List[List[Tuple[str, int, str]]] = []
        current: List[Tuple[str, int, str]] = []
        current_w = 0

        def newline():
            nonlocal current, current_w
            lines.append(current)
            current = []
            current_w = 0

        i = 0
        n_cells = len(cells)
        while i < n_cells:
            ch, cw, st = cells[i]
            if ch == "\n":
                newline()
                i += 1
                continue
            if ch in (" ", "\t"):
                if current:
                    current.append((" ", 1, st))
                    current_w += 1
                i += 1
                continue
            word: List[Tuple[str, int, str]] = []
            word_w = 0
            while i < n_cells and cells[i][0] not in (" ", "\t", "\n"):
                word.append(cells[i])
                word_w += cells[i][1]
                i += 1
            if current and current_w + word_w > w:
                newline()
            for c, cw_, st_ in word:
                if current_w + cw_ > w and current:
                    newline()
                current.append((c, cw_, st_))
                current_w += cw_

        if current:
            lines.append(current)

        drawn = 0
        for row_idx, line in enumerate(lines[:h]):
            line_w = sum(cw for _, cw, _ in line)
            if align == "center":
                start_x = x + max(0, (w - line_w) // 2)
            elif align == "right":
                start_x = x + max(0, w - line_w)
            else:
                start_x = x
            cx = start_x
            for ch, cw, st in line:
                if cx + cw > x + w:
                    break
                self.set_cell(cx, y + row_idx, ch, st)
                if cw >= 2 and cx + 1 < x + w:
                    self.cells[y + row_idx][cx + 1].char = ""
                    self.cells[y + row_idx][cx + 1].style = st
                cx += cw
            drawn += 1
        return drawn

    # -------------------------------------------------------------------- rows
    def render_rows(self) -> List[str]:
        """Produce one ANSI-encoded string per row (self-contained).

        Only cells whose style is a valid ANSI SGR sequence are emitted with
        that style. Anything else (a color *name* like ``"cyan"``, a stray
        markup fragment, a typo) is treated as "no style" so raw text like
        ``cyan`` can never leak onto the screen via the row serializer.
        """
        rows: List[str] = []
        for row in self.cells:
            parts: List[str] = []
            current_style = ""
            for cell in row:
                if cell.char == "":
                    continue
                cell_style = cell.style
                if cell_style and not cell_style.startswith("\x1b"):
                    cell_style = ""
                if cell_style != current_style:
                    if current_style:
                        parts.append(ANSI.color_reset)
                    if cell_style:
                        parts.append(cell_style)
                    current_style = cell_style
                parts.append(cell.char)
            if current_style:
                parts.append(ANSI.color_reset)
            rows.append("".join(parts))
        return rows


class ScreenRenderer:
    """Writes screen diffs to a text stream."""

    def __init__(self, stream=None):
        self.stream = stream or sys.stdout
        self._prev_rows: List[str] = []

    def set_stream(self, stream) -> None:
        self.stream = stream

    def draw(self, buffer: ScreenBuffer, force: bool = False) -> None:
        rows = buffer.render_rows()
        out: List[str] = []
        for y, row in enumerate(rows):
            if not force and y < len(self._prev_rows) and self._prev_rows[y] == row:
                continue
            out.append(f"\033[{y + 1};1H{row}\033[K")
        self._prev_rows = rows
        if out:
            self.stream.write("".join(out))
            self.stream.flush()

    def clear_screen(self) -> None:
        self.stream.write("\033[2J\033[H")
        self.stream.flush()
        self._prev_rows = []

    def move_to(self, x: int, y: int) -> None:
        self.stream.write(f"\033[{y + 1};{x + 1}H")
        self.stream.flush()

    def hide_cursor(self) -> None:
        self.stream.write("\033[?25l")
        self.stream.flush()

    def show_cursor(self) -> None:
        self.stream.write("\033[?25h")
        self.stream.flush()