# -*- coding: utf-8 -*-
"""
Table component for rich compatibility.
"""

import re
from typing import List, Optional, Tuple, Union, TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from ascii_colors.rich.console import Console, ConsoleOptions

from ascii_colors.constants import ANSI
from ascii_colors.rich.style import Style, BoxStyle
from ascii_colors.rich.text import Text, Renderable, wcswidth

_ANSI_TERM = 'ABCDEFGHJKSTfmnsulh'
_ANSI_STRIP = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _truncate_ansi(text: str, max_width: int) -> str:
    """Truncate text to max_width visual cells, preserving ANSI sequences."""
    if max_width <= 0:
        return ""
    plain = _ANSI_STRIP.sub("", text)
    if wcswidth(plain) <= max_width:
        return text
    parts = []
    visual = 0
    i = 0
    n = len(text)
    while i < n and visual < max_width:
        if text[i:i+2] in ('\x1b[', '\033['):
            j = i + 2
            while j < n and text[j] not in _ANSI_TERM:
                j += 1
            if j < n:
                j += 1
            parts.append(text[i:j])
            i = j
        else:
            ch = text[i]
            cw = wcswidth(ch)
            if cw <= 0:
                cw = 1
            if visual + cw > max_width:
                break
            parts.append(ch)
            visual += cw
            i += 1
    parts.append(ANSI.color_reset)
    return "".join(parts)


class Column:
    """Configuration for a table column."""
    def __init__(
        self,
        header: str = "",
        style: Optional[Union[str, Style]] = None,
        no_wrap: bool = False,
        width: Optional[int] = None,
        justify: str = "left",
    ):
        self.header = header
        self.style = style if isinstance(style, Style) else (Style.parse(style) if style else None)
        self.no_wrap = no_wrap
        self.width = width
        self.justify = justify

class Table(Renderable):
    """A table with rows and columns."""

    def __init__(
        self,
        *headers: str,
        title: Optional[str] = None,
        caption: Optional[str] = None,
        width: Optional[int] = None,
        min_width: Optional[int] = None,
        box: Optional[Union[BoxStyle, str]] = BoxStyle.ROUND,
        padding: Union[int, Tuple[int, ...]] = (0, 1),
        collapse_padding: bool = False,
        pad_edge: bool = True,
        expand: bool = False,
        show_header: bool = True,
        show_edge: bool = True,
        show_lines: bool = False,
        safe_box: Optional[bool] = None,
        padding_style: Optional[Union[str, Style]] = None,
        header_style: Optional[Union[str, Style]] = None,
        row_styles: Optional[List[Union[str, Style]]] = None,
        border_style: Optional[Union[str, Style]] = None,
    ):
        self.columns: List[Column] = [Column(header=h) for h in headers]
        self.title = title
        self.caption = caption
        self.width = width
        self.min_width = min_width

        if isinstance(box, str):
            try:
                self.box: Optional[BoxStyle] = BoxStyle(box.lower())
            except ValueError:
                self.box = BoxStyle.ROUND
        elif isinstance(box, BoxStyle) or box is None:
            self.box = box
        else:
            self.box = BoxStyle.ROUND

        self.padding = padding
        self.collapse_padding = collapse_padding
        self.pad_edge = pad_edge
        self.expand = expand
        self.show_header = show_header
        self.show_edge = show_edge
        self.show_lines = show_lines
        self.safe_box = safe_box
        self.padding_style = padding_style
        self.header_style = header_style if isinstance(header_style, Style) else (Style.parse(header_style) if header_style else Style(bold=True))
        self.row_styles = row_styles or []
        self.border_style = border_style if isinstance(border_style, Style) else (Style.parse(border_style) if border_style else None)
        self.rows: List[List[str]] = []

    def _normalize_padding(self, pad: Union[int, Tuple[int, ...]]) -> Tuple[int, int]:
        """Normalize padding to (pad_y, pad_x)."""
        if isinstance(pad, int):
            return (pad, pad)
        if len(pad) == 0:
            return (0, 1)
        if len(pad) == 1:
            return (pad[0], pad[0])
        return (pad[0], pad[1])

    def add_column(
        self,
        header: str = "",
        style: Optional[Union[str, Style]] = None,
        no_wrap: bool = False,
        width: Optional[int] = None,
        justify: str = "left",
    ) -> None:
        """Add a column to the table."""
        self.columns.append(Column(header=header, style=style, no_wrap=no_wrap, width=width, justify=justify))

    def add_row(self, *cells: str, style: Optional[Union[str, Style]] = None) -> None:
        """Add a row to the table."""
        self.rows.append(list(cells))

    def clear(self) -> None:
        """Clear all data rows from the table."""
        self.rows.clear()

    def update(
        self,
        *,
        title: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> "Table":
        """Update table metadata in-place."""
        if title is not None:
            self.title = title
        if caption is not None:
            self.caption = caption
        return self

    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[Union[str, Renderable]]:
        chars = self.box.get_chars() if self.box else None
        max_width = self.width or options.max_width

        col_count = len(self.columns)
        if col_count == 0:
            return

        pad_y, pad_x = self._normalize_padding(self.padding)
        # Clamp pad_x so that per-column padding cannot force the table past max_width
        if max_width > 0 and col_count > 0:
            if chars:
                per_col_budget = max(1, (max_width - (col_count + 1)) // col_count)
            else:
                per_col_budget = max(1, max_width // col_count)
            pad_x = min(pad_x, max(0, (per_col_budget - 1) // 2))
        col_widths = [0] * col_count

        # Check explicit column widths first
        for i, col in enumerate(self.columns):
            if col.width is not None:
                col_widths[i] = max(col_widths[i], col.width)

        # Process headers with markup and calculate widths
        processed_headers = []
        for i, col in enumerate(self.columns):
            processed = console._apply_markup(col.header) if console.markup else col.header
            processed_headers.append(processed)
            plain = re.sub(r"\x1b\[[0-9;]*m", "", processed)
            col_widths[i] = max(col_widths[i], wcswidth(plain))

        # Process rows and update widths
        processed_rows = []
        for row in self.rows:
            processed_row = []
            for i, cell in enumerate(row):
                cell_str = str(cell)
                processed_cell = console._apply_markup(cell_str) if console.markup else cell_str
                processed_row.append(processed_cell)
                if i < col_count:
                    plain = re.sub(r"\x1b\[[0-9;]*m", "", processed_cell)
                    col_widths[i] = max(col_widths[i], wcswidth(plain))
            processed_rows.append(processed_row)

        # Add padding to column widths
        for i in range(col_count):
            col_widths[i] += pad_x * 2

        # Calculate total table width
        # With a box: col_count+1 vertical separators.
        # Without a box: cells are joined by pad_x spaces each.
        if chars:
            border_count = col_count + 1
        else:
            border_count = pad_x * (col_count - 1) if col_count > 1 else 0
        total_width = sum(col_widths) + border_count

        # Expand or shrink to fit
        if self.expand and total_width < max_width:
            extra = max_width - total_width
            per_col = extra // col_count
            for i in range(col_count):
                col_widths[i] += per_col
            total_width = sum(col_widths) + border_count

        if total_width > max_width:
            available = max_width - border_count
            if available > 0:
                total_content = sum(max(0, w - pad_x * 2) for w in col_widths)
                if total_content > 0:
                    for i in range(col_count):
                        content_width = max(0, col_widths[i] - pad_x * 2)
                        new_content = max(1, (available * content_width) // total_content)
                        col_widths[i] = new_content + pad_x * 2
            total_width = sum(col_widths) + border_count

        # Final hard-fit guarantee: never exceed max_width, even with awkward padding
        if total_width > max_width:
            excess = total_width - max_width
            for i in range(col_count - 1, -1, -1):
                if excess <= 0:
                    break
                min_col = 1 + pad_x * 2
                reducible = max(0, col_widths[i] - min_col)
                take = min(excess, reducible)
                col_widths[i] -= take
                excess -= take
            total_width = sum(col_widths) + border_count

        border_ansi = str(self.border_style) if self.border_style else ""
        header_ansi = str(self.header_style) if self.header_style else ""
        reset = ANSI.color_reset

        # Render title first (above the table)
        if self.title:
            title_clean = console._apply_markup(self.title) if console.markup else self.title
            title_plain = re.sub(r"\x1b\[[0-9;]*m", "", title_clean)
            title_width = wcswidth(title_plain)
            left_pad = (total_width - title_width) // 2
            yield f"{' ' * max(0, left_pad)}{title_clean}"
            yield ""

        # Top border
        if self.show_edge and chars:
            parts = [chars["top_left"]]
            for i, w in enumerate(col_widths):
                parts.append(chars["horizontal"] * w)
                if i < col_count - 1:
                    parts.append(chars["top_t"])
                else:
                    parts.append(chars["top_right"])
            yield f"{border_ansi}{''.join(parts)}{reset}"

        # Header row
        if self.show_header:
            parts = [chars["vertical"]] if chars else []
            for i, (h, w) in enumerate(zip(processed_headers, col_widths)):
                col_def = self.columns[i]
                plain_h = re.sub(r"\x1b\[[0-9;]*m", "", h)
                content_width = w - pad_x * 2
                text_width = wcswidth(plain_h)
                if text_width > content_width:
                    h = _truncate_ansi(h, content_width)
                    plain_h = re.sub(r"\x1b\[[0-9;]*m", "", h)
                    text_width = wcswidth(plain_h)

                if col_def.justify == "right":
                    left_pad = max(0, content_width - text_width)
                    right_pad = 0
                elif col_def.justify == "center":
                    left_pad = max(0, (content_width - text_width) // 2)
                    right_pad = max(0, content_width - text_width - left_pad)
                else:  # left
                    left_pad = 0
                    right_pad = max(0, content_width - text_width)

                cell_content = f"{' ' * pad_x}{' ' * left_pad}{h}{' ' * right_pad}{' ' * pad_x}"
                parts.append(f"{reset}{header_ansi}{cell_content}{reset}{border_ansi if chars else ''}")
                if chars:
                    parts.append(chars["vertical"])
                elif i < col_count - 1:
                    parts.append(" " * pad_x)
            yield f"{border_ansi if chars else ''}{''.join(parts)}{reset}"

            # Header separator
            if chars:
                parts = [chars["left_t"]]
                for i, w in enumerate(col_widths):
                    parts.append(chars["horizontal"] * w)
                    if i < col_count - 1:
                        parts.append(chars["cross"])
                    else:
                        parts.append(chars["right_t"])
                yield f"{border_ansi}{''.join(parts)}{reset}"

        # Data rows
        for row_idx, row in enumerate(processed_rows):
            row_style = None
            if self.row_styles:
                style_idx = row_idx % len(self.row_styles)
                row_style = self.row_styles[style_idx]
                if isinstance(row_style, str):
                    row_style = Style.parse(row_style)
            row_ansi = str(row_style) if row_style else ""

            parts = [chars["vertical"]] if chars else []
            for i in range(col_count):
                w = col_widths[i]
                col_def = self.columns[i]
                col_ansi = str(col_def.style) if col_def.style else ""

                cell = row[i] if i < len(row) else ""
                plain_cell = re.sub(r"\x1b\[[0-9;]*m", "", cell)
                content_width = w - pad_x * 2
                text_width = wcswidth(plain_cell)
                if text_width > content_width:
                    cell = _truncate_ansi(cell, content_width)
                    plain_cell = re.sub(r"\x1b\[[0-9;]*m", "", cell)
                    text_width = wcswidth(plain_cell)

                if col_def.justify == "right":
                    left_pad = max(0, content_width - text_width)
                    right_pad = 0
                elif col_def.justify == "center":
                    left_pad = max(0, (content_width - text_width) // 2)
                    right_pad = max(0, content_width - text_width - left_pad)
                else:  # left
                    left_pad = 0
                    right_pad = max(0, content_width - text_width)

                combined_style = f"{row_ansi}{col_ansi}"

                if combined_style:
                    cell_content = f"{' ' * pad_x}{' ' * left_pad}{cell}{reset}{' ' * right_pad}{' ' * pad_x}"
                    parts.append(f"{reset}{combined_style}{cell_content}{border_ansi if chars else ''}")
                else:
                    cell_content = f"{' ' * pad_x}{' ' * left_pad}{cell}{' ' * right_pad}{' ' * pad_x}"
                    parts.append(f"{reset}{cell_content}{border_ansi if chars else ''}")

                if chars:
                    parts.append(chars["vertical"])
                elif i < col_count - 1:
                    parts.append(" " * pad_x)

            yield f"{border_ansi if chars else ''}{''.join(parts)}{reset}"

            # Row separator
            if self.show_lines and row_idx < len(processed_rows) - 1 and chars:
                parts = [chars["left_t"]]
                for i, w in enumerate(col_widths):
                    parts.append(chars["horizontal"] * w)
                    if i < col_count - 1:
                        parts.append(chars["cross"])
                    else:
                        parts.append(chars["right_t"])
                yield f"{border_ansi}{''.join(parts)}{reset}"

        # Bottom border
        if self.show_edge and chars:
            parts = [chars["bottom_left"]]
            for i, w in enumerate(col_widths):
                parts.append(chars["horizontal"] * w)
                if i < col_count - 1:
                    parts.append(chars["bottom_t"])
                else:
                    parts.append(chars["bottom_right"])
            yield f"{border_ansi}{''.join(parts)}{reset}"

        # Caption (below the table)
        if self.caption:
            yield ""
            caption_clean = console._apply_markup(self.caption) if console.markup else self.caption
            caption_plain = re.sub(r"\x1b\[[0-9;]*m", "", caption_clean)
            caption_width = wcswidth(caption_plain)
            left_pad = (total_width - caption_width) // 2
            yield f"{' ' * max(0, left_pad)}{caption_clean}"

    def __rich_measure__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> "Measurement":
        from ascii_colors.rich.console import Measurement
        col_count = len(self.columns)
        min_width = col_count * 3 + col_count + 1
        return Measurement(min_width, options.max_width)