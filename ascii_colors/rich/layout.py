# -*- coding: utf-8 -*-
"""
Layout components: Panel, Padding, and Columns.
"""

import re
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ascii_colors.rich.console import Console, ConsoleOptions

from ascii_colors.constants import ANSI
from ascii_colors.rich.style import Style, BoxStyle
from ascii_colors.rich.text import Text, Renderable, wcswidth


class Padding:
    """Padding around content."""
    
    def __init__(
        self,
        renderable: Renderable,
        pad: Optional[Union[int, Tuple[int, ...]]] = None,
        style: Optional[Union[str, Style]] = None,
    ):
        self.renderable = renderable
        self.pad = self._normalize_padding(pad or (0, 1))
        self.style = style
    
    def _normalize_padding(
        self,
        pad: Union[int, Tuple[int, ...]]
    ) -> Tuple[int, int, int, int]:
        """Normalize padding to (top, right, bottom, left)."""
        if isinstance(pad, int):
            return (pad, pad, pad, pad)
        elif len(pad) == 2:
            return (pad[0], pad[1], pad[0], pad[1])
        elif len(pad) == 4:
            return pad
        else:
            return (0, 1, 0, 1)
    
    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[Renderable]:
        from ascii_colors.rich.console import ConsoleOptions
        
        top, right, bottom, left = self.pad
        
        for _ in range(top):
            yield Text(" " * options.max_width)
        
        for line in console.render(
            self.renderable,
            options.update_width(options.max_width - left - right)
        ):
            yield Text(" " * left + line + " " * right)
        
        for _ in range(bottom):
            yield Text(" " * options.max_width)


class Panel:
    """A bordered panel around content."""
    
    def __init__(
        self,
        renderable: Union[Renderable, str],
        title: Optional[str] = None,
        title_align: str = "center",
        style: Optional[Union[str, Style]] = None,
        border_style: Optional[Union[str, Style]] = None,
        box: Union[BoxStyle, str] = BoxStyle.SQUARE,
        padding: Union[int, Tuple[int, ...]] = (0, 1),
        width: Optional[int] = None,
        height: Optional[int] = None,
        expand: bool = True,
    ):
        self.renderable = renderable if isinstance(renderable, Renderable) else Text(renderable)
        self.title = title
        self.title_align = title_align
        self.style = style if isinstance(style, Style) else (Style.parse(style) if style else None)
        self.border_style = border_style if isinstance(border_style, Style) else (Style.parse(border_style) if border_style else None)
        self.box = box if isinstance(box, BoxStyle) else BoxStyle.SQUARE
        self.padding = padding if isinstance(padding, tuple) else (padding, padding)
        self.width = width
        self.height = height
        self.expand = expand
    
    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[Union[str, Renderable]]:
        chars = self.box.get_chars()
        
        if self.width:
            panel_width = min(self.width, options.max_width)
        elif self.expand:
            panel_width = options.max_width
        else:
            panel_width = options.max_width
        
        inner_width = panel_width - 2
        
        if isinstance(self.padding, int):
            pad_y, pad_x = self.padding, self.padding
        elif len(self.padding) == 2:
            pad_y, pad_x = self.padding
        else:
            pad_y, pad_x = self.padding[0], self.padding[1]
        
        content_width = inner_width - (pad_x * 2)
        content_width = max(content_width, 1)
        
        # Render content to list of strings first to properly handle multi-line
        content_lines: List[str] = []
        
        if isinstance(self.renderable, Text):
            # For Text objects, render with the console to get lines
            rendered = console.render(self.renderable, options.update_width(content_width))
            for item in rendered:
                # Convert to string - could be Text or str
                if isinstance(item, Text):
                    line_str = str(item.plain) if isinstance(item.plain, str) else str(item)
                elif isinstance(item, str):
                    line_str = item
                else:
                    line_str = str(item)
                
                # CRITICAL: Handle embedded newlines from Text with no_wrap=True
                # When Text.no_wrap=True, wrap() returns [self] and render() preserves
                # all newlines in a single string. We must split them here.
                if '\n' in line_str:
                    content_lines.extend(line_str.split('\n'))
                else:
                    content_lines.append(line_str)
        elif isinstance(self.renderable, str):
            # For strings, split on newlines and process each
            processed = console._apply_markup(self.renderable) if console.markup else self.renderable
            # Split by newlines and filter out empty trailing lines
            lines = processed.split('\n')
            content_lines = [line for line in lines]  # Keep all lines including empty ones
        else:
            # For other renderables
            rendered = console.render(self.renderable, options.update_width(content_width))
            for item in rendered:
                if isinstance(item, Text):
                    line_str = str(item.plain) if isinstance(item.plain, str) else str(item)
                elif isinstance(item, str):
                    line_str = item
                else:
                    line_str = str(item)
                
                # Handle embedded newlines
                if '\n' in line_str:
                    content_lines.extend(line_str.split('\n'))
                else:
                    content_lines.append(line_str)
        
        border_ansi = str(self.border_style) if self.border_style else ""
        style_ansi = str(self.style) if self.style else ""
        reset = ANSI.color_reset
        
        ansi_escape = re.compile(r"\033\[[0-9;]+m")
        
        def plain_width(text: str) -> int:
            plain = ansi_escape.sub("", text)
            return wcswidth(plain)
        
        def pad_line(line: str, width: int) -> str:
            line_width = plain_width(line)
            if line_width < width:
                return line + " " * (width - line_width)
            elif line_width > width:
                # Truncate if too long, being careful with ANSI codes
                # Simple approach: truncate the raw string
                return line[:width]
            return line
        
        # Build top border with title if present
        if self.title:
            # Process title markup - but ensure we preserve border style context
            title_clean = console._apply_markup(self.title) if console.markup else self.title
            
            # Remove trailing reset codes from title to prevent style leakage
            # The title's internal resets are fine, but trailing reset affects border
            title_clean = re.sub(r'\x1b\[0m$', '', title_clean)  # Remove trailing reset
            title_clean = re.sub(r'\x1b\[0m(?=\s*$)', '', title_clean)  # Remove reset before trailing space
            
            title_plain = ansi_escape.sub("", title_clean)
            title_width = wcswidth(title_plain)
            
            available_for_lines = inner_width - title_width - 2
            
            if available_for_lines < 0:
                max_title_len = inner_width - 4
                # Truncate the plain text, then re-process
                title_plain_truncated = title_plain[:max_title_len]
                title_width = wcswidth(title_plain_truncated)
                # Re-apply markup to truncated plain text if original had markup
                if console.markup:
                    # Try to preserve styling by using truncated plain with original style hint
                    title_clean = title_plain_truncated
                else:
                    title_clean = title_plain_truncated
                available_for_lines = inner_width - title_width - 2
            
            if self.title_align == "center":
                left_line_len = available_for_lines // 2
                right_line_len = available_for_lines - left_line_len
            elif self.title_align == "right":
                left_line_len = available_for_lines - 1
                right_line_len = 1
            else:
                left_line_len = 1
                right_line_len = available_for_lines - 1
            
            left_line_len = max(0, left_line_len)
            right_line_len = max(0, right_line_len)
            
            # Build top border with proper style handling
            # Apply border style, then title (with its own styles), then re-apply border style
            left_part = f"{border_ansi}{chars['top_left']}{chars['horizontal'] * left_line_len}{reset}"
            title_part = f" {title_clean} "  # Title with its own internal styling
            right_part = f"{border_ansi}{chars['horizontal'] * right_line_len}{chars['top_right']}{reset}"
            
            top_border = left_part + title_part + right_part
        else:
            top_border = (
                f"{border_ansi}{chars['top_left']}"
                f"{chars['horizontal'] * inner_width}"
                f"{chars['top_right']}{reset}"
            )
        
        yield top_border
        
        # Empty padding rows at top
        for _ in range(pad_y):
            fill = f"{style_ansi}{' ' * inner_width}{reset}" if self.style else " " * inner_width
            yield f"{border_ansi}{chars['vertical']}{reset}{fill}{border_ansi}{chars['vertical']}{reset}"
        
        # Content rows with proper left padding - each line gets same padding
        for line in content_lines:
            # Strip any trailing newlines or carriage returns
            line = line.rstrip('\n\r')
            
            # Pad/truncate to content width (right padding to fill width)
            padded_content = pad_line(line, content_width)
            
            # Apply left and right padding (pad_x on each side)
            if self.style:
                # Apply style to the padding area as well for consistency
                styled_content = f"{style_ansi}{' ' * pad_x}{padded_content}{' ' * pad_x}{reset}"
            else:
                styled_content = f"{' ' * pad_x}{padded_content}{' ' * pad_x}"
            
            # Build full line: left border + padded content + right border
            yield (
                f"{border_ansi}{chars['vertical']}{reset}"
                f"{styled_content}"
                f"{border_ansi}{chars['vertical']}{reset}"
            )
        
        # Empty padding rows at bottom
        for _ in range(pad_y):
            fill = f"{style_ansi}{' ' * inner_width}{reset}" if self.style else " " * inner_width
            yield f"{border_ansi}{chars['vertical']}{reset}{fill}{border_ansi}{chars['vertical']}{reset}"
        
        # Bottom border
        bottom_border = (
            f"{border_ansi}{chars['bottom_left']}"
            f"{chars['horizontal'] * inner_width}"
            f"{chars['bottom_right']}{reset}"
        )
        yield bottom_border
    
    def __rich_measure__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> "Measurement":
        from ascii_colors.rich.console import Measurement
        if self.width:
            return Measurement(self.width, self.width)
        return Measurement(10, options.max_width)


class Columns:
    """Arrange renderables in columns."""
    
    def __init__(
        self,
        renderables: Iterable[Union[Renderable, str]],
        padding: int = 1,
        width: Optional[int] = None,
        equal: bool = False,
        column_first: bool = False,
    ):
        self.renderables = [r if isinstance(r, Renderable) else Text(r) for r in renderables]
        self.padding = padding
        self.width = width
        self.equal = equal
        self.column_first = column_first
    
    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[Renderable]:
        if not self.renderables:
            return
        
        width = self.width or options.max_width
        
        def get_renderable_width(r):
            if isinstance(r, Text):
                return wcswidth(r.plain)
            elif isinstance(r, str):
                return wcswidth(r)
            else:
                try:
                    return wcswidth(str(r))
                except:
                    return 10
        
        item_widths = [min(get_renderable_width(r), width // 2) for r in self.renderables]
        max_item_width = max(item_widths) if item_widths else 0
        
        if self.equal:
            col_width = max_item_width + self.padding
            num_cols = max(1, width // col_width)
        else:
            num_cols = max(1, width // (max_item_width + self.padding))
        
        col_width = width // num_cols
        
        rows = []
        current_row = []
        for i, item in enumerate(self.renderables):
            if len(current_row) >= num_cols:
                rows.append(current_row)
                current_row = []
            current_row.append(item)
        
        if current_row:
            rows.append(current_row)
        
        for row in rows:
            row_lines = []
            max_lines = 0
            
            for item in row:
                # Handle different types properly
                if isinstance(item, Text):
                    lines = [str(line.plain) if isinstance(line.plain, str) else str(line) for line in item.wrap(col_width - self.padding)]
                elif isinstance(item, str):
                    text = Text(item)
                    lines = [str(line.plain) if isinstance(line.plain, str) else str(line) for line in text.wrap(col_width - self.padding)]
                else:
                    # For other renderables, render to string lines
                    try:
                        rendered = console.render(item, options.update_width(col_width - self.padding))
                        lines = [str(line) for line in rendered]
                    except:
                        lines = [str(item)]
                row_lines.append(lines)
                max_lines = max(max_lines, len(lines))
            
            for line_idx in range(max_lines):
                parts = []
                for col_idx, lines in enumerate(row_lines):
                    if line_idx < len(lines):
                        line_str = str(lines[line_idx])
                        parts.append(line_str.ljust(col_width - self.padding))
                    else:
                        parts.append(" " * (col_width - self.padding))
                
                result = (" " * self.padding).join(parts)
                yield Text(result)
    
    def __rich_measure__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> "Measurement":
        from ascii_colors.rich.console import Measurement
        return Measurement(10, options.max_width)
