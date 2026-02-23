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


class Table(Renderable):
    """A table with rows and columns."""
    
    def __init__(
        self,
        *headers: str,
        title: Optional[str] = None,
        caption: Optional[str] = None,
        width: Optional[int] = None,
        min_width: Optional[int] = None,
        box: Union[BoxStyle, str] = BoxStyle.SQUARE,
        padding: Tuple[int, int] = (0, 1),
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
        self.headers = list(headers)
        self.title = title
        self.caption = caption
        self.width = width
        self.min_width = min_width
        self.box = box if isinstance(box, BoxStyle) else BoxStyle.SQUARE
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
        self.border_style = border_style
        self.rows: List[List[str]] = []
    
    def add_row(self, *cells: str, style: Optional[Union[str, Style]] = None) -> None:
        """Add a row to the table."""
        self.rows.append(list(cells))
    
    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[Union[str, Renderable]]:
        chars = self.box.get_chars()
        max_width = self.width or options.max_width
        
        col_count = len(self.headers)
        if col_count == 0:
            return
        
        pad_x, pad_y = self.padding
        col_widths = [0] * col_count
        
        # Process headers with markup and calculate widths
        processed_headers = []
        for i, h in enumerate(self.headers):
            processed = console._apply_markup(h) if console.markup else h
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
        total_width = sum(col_widths) + (col_count + 1)  # +1 for each vertical border
        
        # Expand or shrink to fit
        if self.expand and total_width < max_width:
            extra = max_width - total_width
            per_col = extra // col_count
            for i in range(col_count):
                col_widths[i] += per_col
            total_width = sum(col_widths) + (col_count + 1)
        
        if total_width > max_width:
            # Shrink proportionally
            available = max_width - (col_count + 1)
            if available > 0:
                total_content = sum(w - pad_x * 2 for w in col_widths)
                if total_content > 0:
                    for i in range(col_count):
                        content_width = col_widths[i] - pad_x * 2
                        new_content = max(3, (available * content_width) // total_content)
                        col_widths[i] = new_content + pad_x * 2
            total_width = sum(col_widths) + (col_count + 1)
        
        border_ansi = str(Style.parse(self.border_style)) if self.border_style else ""
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
        if self.show_edge:
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
            parts = [chars["vertical"]]
            for i, (h, w) in enumerate(zip(processed_headers, col_widths)):
                plain_h = re.sub(r"\x1b\[[0-9;]*m", "", h)
                content_width = w - pad_x * 2
                text_width = wcswidth(plain_h)
                left_pad = (content_width - text_width) // 2
                right_pad = content_width - text_width - left_pad
                cell_content = f"{' ' * pad_x}{' ' * left_pad}{h}{' ' * right_pad}{' ' * pad_x}"
                parts.append(f"{header_ansi}{cell_content}{reset}{border_ansi}")
                parts.append(chars["vertical"])
            yield f"{border_ansi}{''.join(parts)}{reset}"
            
            # Header separator
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
            
            parts = [chars["vertical"]]
            for i in range(col_count):
                w = col_widths[i]
                cell = row[i] if i < len(row) else ""
                plain_cell = re.sub(r"\x1b\[[0-9;]*m", "", cell)
                content_width = w - pad_x * 2
                text_width = wcswidth(plain_cell)
                left_pad = (content_width - text_width) // 2
                right_pad = content_width - text_width - left_pad
                
                if row_ansi:
                    cell_content = f"{' ' * pad_x}{' ' * left_pad}{cell}{reset}{' ' * right_pad}{' ' * pad_x}"
                    parts.append(f"{row_ansi}{cell_content}{border_ansi}")
                else:
                    cell_content = f"{' ' * pad_x}{' ' * left_pad}{cell}{' ' * right_pad}{' ' * pad_x}"
                    parts.append(f"{cell_content}{border_ansi}")
                parts.append(chars["vertical"])
            
            yield f"{border_ansi}{''.join(parts)}{reset}"
            
            # Row separator
            if self.show_lines and row_idx < len(processed_rows) - 1:
                parts = [chars["left_t"]]
                for i, w in enumerate(col_widths):
                    parts.append(chars["horizontal"] * w)
                    if i < col_count - 1:
                        parts.append(chars["cross"])
                    else:
                        parts.append(chars["right_t"])
                yield f"{border_ansi}{''.join(parts)}{reset}"
        
        # Bottom border
        if self.show_edge:
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
        min_width = len(self.headers) * 3 + len(self.headers) + 1
        return Measurement(min_width, options.max_width)