# -*- coding: utf-8 -*-
"""
Layout components: Panel, Padding, and Columns.
"""

import re
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, Union, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from ascii_colors.rich.console import Console, ConsoleOptions

from ascii_colors.constants import ANSI
from ascii_colors.rich.style import Style, BoxStyle
from ascii_colors.rich.text import Text, Renderable, wcswidth

# Import Measurement at module level for type annotations
from ascii_colors.rich.console import Measurement


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
        
        # At this point, pad must be a tuple
        pad_tuple = cast(Tuple[int, ...], pad)
        
        if len(pad_tuple) == 2:
            return (pad_tuple[0], pad_tuple[1], pad_tuple[0], pad_tuple[1])
        elif len(pad_tuple) == 4:
            return (pad_tuple[0], pad_tuple[1], pad_tuple[2], pad_tuple[3])
        else:
            # Fallback for unexpected tuple lengths - use first element or defaults
            first = pad_tuple[0] if len(pad_tuple) > 0 else 0
            return (first, first, first, first)
    
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
        
    def _normalize_padding(
        self,
        pad: Union[int, Tuple[int, ...]]
    ) -> Tuple[int, int, int, int]:
        """Normalize padding to (top, right, bottom, left)."""
        if isinstance(pad, int):
            return (pad, pad, pad, pad)
        
        # At this point, pad must be a tuple
        pad_tuple = cast(Tuple[int, ...], pad)
        
        if len(pad_tuple) == 2:
            return (pad_tuple[0], pad_tuple[1], pad_tuple[0], pad_tuple[1])
        elif len(pad_tuple) == 4:
            return (pad_tuple[0], pad_tuple[1], pad_tuple[2], pad_tuple[3])
        else:
            # Fallback for unexpected tuple lengths - use first element or defaults
            first = pad_tuple[0] if len(pad_tuple) > 0 else 0
            return (first, first, first, first)    
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
        
        # Parse padding to get horizontal padding value
        # Normalize to (top, right, bottom, left)
        padding_tuple = self._normalize_padding(self.padding)
        pad_y, pad_x = padding_tuple[0], padding_tuple[1]
        
        content_width = inner_width - (pad_x * 2)
        content_width = max(content_width, 1)
        
        # Render content to list of strings first to properly handle multi-line
        content_lines: List[str] = []
        
        if isinstance(self.renderable, str):
            # For strings, apply markup processing first
            processed = console._apply_markup(self.renderable) if console.markup else self.renderable
            
            # Split by explicit newlines first, then wrap each line if needed
            explicit_lines = processed.split('\n')
            
            for line in explicit_lines:
                # Check if line needs wrapping
                plain_line = re.sub(r"\033\[[0-9;]+m", "", line)
                line_len = wcswidth(plain_line)
                
                if line_len <= content_width:
                    # Line fits, add as-is
                    content_lines.append(line)
                else:
                    # Line too long, need to wrap
                    # But be careful with ANSI codes - wrap by visible width
                    import textwrap
                    # For lines with ANSI codes, we need special handling
                    if '\033[' in line:
                        # Wrap manually preserving ANSI codes
                        current_line = ""
                        current_width = 0
                        i = 0
                        while i < len(line):
                            # Check for ANSI escape sequence
                            if line[i:i+2] == '\033[':
                                # Find end of sequence
                                j = i + 2
                                while j < len(line) and line[j] not in 'ABCDEFGHJKSTfmnsulh':
                                    j += 1
                                if j < len(line):
                                    j += 1  # Include the final character
                                # Add the ANSI code to current line without counting width
                                current_line += line[i:j]
                                i = j
                            else:
                                # Regular character
                                char_width = wcswidth(line[i])
                                if current_width + char_width > content_width and current_width > 0:
                                    # Start new line
                                    content_lines.append(current_line)
                                    current_line = line[i]
                                    current_width = char_width
                                else:
                                    current_line += line[i]
                                    current_width += char_width
                                i += 1
                        # Don't forget the last line
                        if current_line:
                            content_lines.append(current_line)
                    else:
                        # No ANSI codes, safe to use textwrap
                        wrapped = textwrap.wrap(line, width=content_width)
                        content_lines.extend(wrapped)
        elif isinstance(self.renderable, Text):
            # For Text objects, get the plain content and process
            plain_content = str(self.renderable.plain) if isinstance(self.renderable.plain, str) else str(self.renderable.plain)
            
            # Apply markup if the Text contains markup-like content
            if '[' in plain_content and console.markup:
                processed = console._apply_markup(plain_content)
            else:
                processed = plain_content
            
            # Split by explicit newlines
            explicit_lines = processed.split('\n')
            
            for line in explicit_lines:
                plain_line = re.sub(r"\033\[[0-9;]+m", "", line)
                if wcswidth(plain_line) <= content_width:
                    content_lines.append(line)
                else:
                    # Need to wrap
                    import textwrap
                    if '\033[' in line:
                        # Manual wrap with ANSI preservation
                        current_line = ""
                        current_width = 0
                        i = 0
                        while i < len(line):
                            if line[i:i+2] == '\033[':
                                j = i + 2
                                while j < len(line) and line[j] not in 'ABCDEFGHJKSTfmnsulh':
                                    j += 1
                                if j < len(line):
                                    j += 1
                                current_line += line[i:j]
                                i = j
                            else:
                                char_width = wcswidth(line[i])
                                if current_width + char_width > content_width and current_width > 0:
                                    content_lines.append(current_line)
                                    current_line = line[i]
                                    current_width = char_width
                                else:
                                    current_line += line[i]
                                    current_width += char_width
                                i += 1
                        if current_line:
                            content_lines.append(current_line)
                    else:
                        wrapped = textwrap.wrap(line, width=content_width)
                        content_lines.extend(wrapped)
        else:
            # For other renderables, render to string lines
            try:
                rendered = console.render(self.renderable, options.update_width(content_width))
                for item in rendered:
                    if isinstance(item, Text):
                        line_str = str(item.plain) if isinstance(item.plain, str) else str(item)
                    elif isinstance(item, str):
                        line_str = item
                    else:
                        line_str = str(item)
                    
                    # Handle embedded newlines in rendered output
                    if '\n' in line_str:
                        sub_lines = line_str.split('\n')
                        for sub_line in sub_lines:
                            plain_sub = re.sub(r"\033\[[0-9;]+m", "", sub_line)
                            if wcswidth(plain_sub) <= content_width:
                                content_lines.append(sub_line)
                            else:
                                # Wrap if needed
                                import textwrap
                                if '\033[' in sub_line:
                                    # Manual wrap
                                    current_line = ""
                                    current_width = 0
                                    i = 0
                                    while i < len(sub_line):
                                        if sub_line[i:i+2] == '\033[':
                                            j = i + 2
                                            while j < len(sub_line) and sub_line[j] not in 'ABCDEFGHJKSTfmnsulh':
                                                j += 1
                                            if j < len(sub_line):
                                                j += 1
                                            current_line += sub_line[i:j]
                                            i = j
                                        else:
                                            char_width = wcswidth(sub_line[i])
                                            if current_width + char_width > content_width and current_width > 0:
                                                content_lines.append(current_line)
                                                current_line = sub_line[i]
                                                current_width = char_width
                                            else:
                                                current_line += sub_line[i]
                                                current_width += char_width
                                            i += 1
                                    if current_line:
                                        content_lines.append(current_line)
                                else:
                                    wrapped = textwrap.wrap(sub_line, width=content_width)
                                    content_lines.extend(wrapped)
                    else:
                        plain_line = re.sub(r"\033\[[0-9;]+m", "", line_str)
                        if wcswidth(plain_line) <= content_width:
                            content_lines.append(line_str)
                        else:
                            # Wrap if needed
                            import textwrap
                            if '\033[' in line_str:
                                # Manual wrap with ANSI preservation
                                current_line = ""
                                current_width = 0
                                i = 0
                                while i < len(line_str):
                                    if line_str[i:i+2] == '\033[':
                                        j = i + 2
                                        while j < len(line_str) and line_str[j] not in 'ABCDEFGHJKSTfmnsulh':
                                            j += 1
                                        if j < len(line_str):
                                            j += 1
                                        current_line += line_str[i:j]
                                        i = j
                                    else:
                                        char_width = wcswidth(line_str[i])
                                        if current_width + char_width > content_width and current_width > 0:
                                            content_lines.append(current_line)
                                            current_line = line_str[i]
                                            current_width = char_width
                                        else:
                                            current_line += line_str[i]
                                            current_width += char_width
                                        i += 1
                                if current_line:
                                    content_lines.append(current_line)
                            else:
                                wrapped = textwrap.wrap(line_str, width=content_width)
                                content_lines.extend(wrapped)
            except Exception:
                content_lines = [str(self.renderable)]
        
        border_ansi = str(self.border_style) if self.border_style else ""
        style_ansi = str(self.style) if self.style else ""
        reset = ANSI.color_reset
        
        ansi_escape = re.compile(r"\033\[[0-9;]+m")
        
        def plain_width(text: str) -> int:
            plain = ansi_escape.sub("", text)
            return wcswidth(plain)
        
        def pad_line(line: str, width: int) -> str:
            # Calculate width from plain text, but preserve ANSI codes
            line_width = plain_width(line)
            if line_width < width:
                # Add padding spaces - ANSI codes are preserved in line
                return line + " " * (width - line_width)
            # If line is longer than target width, return as-is (don't truncate)
            return line
        
        # Build top border with title if present
        if self.title:
            # Process title markup
            title_clean = console._apply_markup(self.title) if console.markup else self.title
            
            # Remove trailing reset codes from title to prevent style leakage
            title_clean = re.sub(r'\x1b\[0m$', '', title_clean)
            title_clean = re.sub(r'\x1b\[0m(?=\s*$)', '', title_clean)
            
            title_plain = ansi_escape.sub("", title_clean)
            title_width = wcswidth(title_plain)
            
            available_for_lines = inner_width - title_width - 2
            
            if available_for_lines < 0:
                max_title_len = inner_width - 4
                title_plain_truncated = title_plain[:max_title_len]
                title_width = wcswidth(title_plain_truncated)
                if console.markup:
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
            left_part = f"{border_ansi}{chars['top_left']}{chars['horizontal'] * left_line_len}{reset}"
            title_part = f" {title_clean} "
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
            
            padded_content = pad_line(line, content_width)
            
            # Apply left and right padding
            if self.style:
                styled_content = f"{style_ansi}{' ' * pad_x}{padded_content}{' ' * pad_x}{reset}"
            else:
                styled_content = f"{' ' * pad_x}{padded_content}{' ' * pad_x}"
            
            # Build full line
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
        return Measurement(10, options.max_width)
