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
        col_widths = [0] * col_count
        
        # Process headers with markup
        processed_headers = []
        for i, h in enumerate(self.headers):
            if console.markup:
                processed = console._apply_markup(h)
            else:
                processed = h
            processed_headers.append(processed)
            plain = re.sub(r"\033\[[0-9;]+m", "", processed)
            col_widths[i] = max(col_widths[i], wcswidth(plain))
        
        for row in self.rows:
            for i, cell in enumerate(row):
                if i < col_count:
                    cell_str = str(cell)
                    if console.markup:
                        cell_str = console._apply_markup(cell_str)
                    plain = re.sub(r"\033\[[0-9;]+m", "", cell_str)
                    col_widths[i] = max(col_widths[i], wcswidth(plain))
        
        pad_x, pad_y = self.padding
        for i in range(col_count):
            col_widths[i] += pad_x * 2
        
        total_width = sum(col_widths) + (col_count + 1)
        
        if self.expand and total_width < max_width:
            extra = max_width - total_width
            per_col = extra // col_count
            for i in range(col_count):
                col_widths[i] += per_col
        
        if total_width > max_width:
            available = max_width - (col_count + 1)
            for i in range(col_count):
                col_widths[i] = max(3, (available * col_widths[i]) // sum(col_widths))
        
        border_ansi = str(Style.parse(self.border_style)) if self.border_style else ""
        header_ansi = str(self.header_style) if self.header_style else ""
        reset = ANSI.color_reset
        
        if self.title:
            title_clean = console._apply_markup(self.title) if console.markup else self.title
            title_width = wcswidth(title_clean)
            left = (total_width - title_width) // 2
            yield f"{border_ansi}{' ' * left}{self.title}{' ' * (total_width - title_width - left)}{reset}"
            yield ""
        
        if self.show_edge:
            parts = [chars["top_left"]]
            for i, w in enumerate(col_widths):
                parts.append(chars["horizontal"] * w)
                if i < len(col_widths) - 1:
                    parts.append(chars["top_t"])
                else:
                    parts.append(chars["top_right"])
            yield f"{border_ansi}{''.join(parts)}{reset}"
        
        if self.show_header:
            parts = [chars["vertical"]]
            for i, (h, w) in enumerate(zip(processed_headers, col_widths)):
                # Strip ANSI for width calculation but keep for display
                plain_h = re.sub(r"\033\[[0-9;]+m", "", h)
                cell = plain_h.center(w - pad_x * 2)
                # Re-apply markup if it was stripped
                display_cell = h if h != plain_h else cell
                # Center manually with padding
                pad_total = w - pad_x * 2 - wcswidth(plain_h)
                left_pad = pad_total // 2
                right_pad = pad_total - left_pad
                parts.append(" " * pad_x + f"{header_ansi}{' ' * left_pad}{plain_h}{' ' * right_pad}{reset}{border_ansi}" + " " * pad_x)
                parts.append(chars["vertical"])
            yield f"{border_ansi}{''.join(parts)}{reset}"
            
            parts = [chars["left_t"]]
            for i, w in enumerate(col_widths):
                parts.append(chars["horizontal"] * w)
                if i < len(col_widths) - 1:
                    parts.append(chars["cross"])
                else:
                    parts.append(chars["right_t"])
            yield f"{border_ansi}{''.join(parts)}{reset}"
        
        for row_idx, row in enumerate(self.rows):
            parts = [chars["vertical"]]
            row_style = None
            if self.row_styles:
                style_idx = row_idx % len(self.row_styles)
                row_style = self.row_styles[style_idx]
                if isinstance(row_style, str):
                    row_style = Style.parse(row_style)
            
            row_ansi = str(row_style) if row_style else ""
            
            for i, (cell, w) in enumerate(zip(row, col_widths)):
                cell_str = str(cell)
                if console.markup:
                    cell_str = console._apply_markup(cell_str)
                
                plain_cell = re.sub(r"\033\[[0-9;]+m", "", cell_str)
                cell_width = wcswidth(plain_cell)
                pad = w - pad_x * 2 - cell_width
                
                left_pad = pad // 2
                right_pad = pad - left_pad
                
                if row_ansi:
                    styled_content = f"{row_ansi}{' ' * pad_x}{cell_str}{' ' * right_pad}{' ' * left_pad}{reset}"
                else:
                    styled_content = f"{' ' * pad_x}{cell_str}{' ' * right_pad}{' ' * left_pad}"
                
                parts.append(styled_content + f"{border_ansi}" + " " * pad_x)
                parts.append(chars["vertical"])
            
            yield f"{border_ansi}{''.join(parts)}{reset}"
            
            if self.show_lines and row_idx < len(self.rows) - 1:
                parts = [chars["left_t"]]
                for i, w in enumerate(col_widths):
                    parts.append(chars["horizontal"] * w)
                    if i < len(col_widths) - 1:
                        parts.append(chars["cross"])
                    else:
                        parts.append(chars["right_t"])
                yield f"{border_ansi}{''.join(parts)}{reset}"
        
        if self.show_edge:
            parts = [chars["bottom_left"]]
            for i, w in enumerate(col_widths):
                parts.append(chars["horizontal"] * w)
                if i < len(col_widths) - 1:
                    parts.append(chars["bottom_t"])
                else:
                    parts.append(chars["bottom_right"])
            yield f"{border_ansi}{''.join(parts)}{reset}"
        
        if self.caption:
            yield ""
            yield self.caption
    
    def __rich_measure__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> "Measurement":
        from ascii_colors.rich.console import Measurement
        min_width = len(self.headers) * 3 + len(self.headers) + 1
        return Measurement(min_width, options.max_width)
