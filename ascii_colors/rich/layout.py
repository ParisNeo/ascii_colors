# -*- coding: utf-8 -*-
"""
Layout components: Panel, Padding, and Columns.
"""

import re
import textwrap
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, Union, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from ascii_colors.rich.console import Console, ConsoleOptions

from ascii_colors.constants import ANSI
from ascii_colors.rich.style import Style, BoxStyle
from ascii_colors.rich.text import Text, Renderable, wcswidth

# Import Measurement at module level for type annotations
from ascii_colors.rich.console import Measurement

# ANSI escape sequence regex - compile once for efficiency
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]+m")


def visual_width(text: str) -> int:
    """Calculate the visual width of text, ignoring ANSI escape codes.
    
    This properly handles emojis and wide characters (CJK, etc.) which
    typically take 2 terminal columns instead of 1.
    
    Args:
        text: String that may contain ANSI escape codes
    
    Returns:
        Visual width in terminal columns
    """
    plain = ANSI_ESCAPE.sub("", text)
    return wcswidth(plain)


def wrap_line_preserving_ansi(line: str, max_width: int) -> List[str]:
    """Wrap a line that may contain ANSI codes and emojis.
    
    Handles:
    - ANSI escape codes (preserved but don't count towards width)
    - Emojis and wide characters (properly counted as 2 columns)
    - Existing ANSI reset codes are stripped from wrapped lines to avoid
      color bleed, then re-applied if needed
    
    Args:
        line: The line to wrap (may contain ANSI codes)
        max_width: Maximum visual width per line
    
    Returns:
        List of wrapped lines
    """
    if not line:
        return [""]
    
    # Check if line fits without wrapping
    if visual_width(line) <= max_width:
        return [line]
    
    # Need to wrap - handle ANSI codes and wide characters carefully
    result_lines = []
    current_line = ""
    current_visual_width = 0
    i = 0
    line_len = len(line)
    
    while i < line_len:
        # Check for ANSI escape sequence
        if line[i:i+2] == '\033[':
            # Find end of ANSI sequence
            j = i + 2
            while j < line_len and line[j] not in 'ABCDEFGHJKSTfmnsulh':
                j += 1
            if j < line_len:
                j += 1  # Include the final character
            # Add ANSI code without counting towards visual width
            current_line += line[i:j]
            i = j
        else:
            # Regular character - check visual width
            char = line[i]
            char_width = wcswidth(char)
            
            # Handle potential multi-byte characters
            if char_width > 1 and i + 1 < line_len:
                # Check if this might be part of a multi-byte sequence
                # For emojis specifically, they're usually single Unicode chars
                pass
            
            # Check if adding this char would exceed width
            if current_visual_width + char_width > max_width and current_line:
                # Start a new line
                result_lines.append(current_line)
                current_line = ""
                current_visual_width = 0
            
            current_line += char
            current_visual_width += char_width
            i += 1
    
    # Add remaining content
    if current_line:
        result_lines.append(current_line)
    
    return result_lines if result_lines else [""]


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
    """A bordered panel around content.
    
    This class properly handles:
    - Emoji and wide characters (counted as 2 terminal columns)
    - Rich markup tags like [bold], [red], etc.
    - ANSI escape codes for colors and styles
    - Multi-line content with proper wrapping
    """
    
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
        
        # Cap panel width to terminal width with safety margin
        max_safe_width = min(options.max_width, console.width - 2) if hasattr(console, 'width') else options.max_width - 2
        max_safe_width = max(max_safe_width, 20)  # Minimum width
        
        if self.width:
            panel_width = min(self.width, max_safe_width)
        elif self.expand:
            panel_width = max_safe_width
        else:
            panel_width = max_safe_width
        
        inner_width = panel_width - 2
        
        # Parse padding to get horizontal padding value
        # Normalize to (top, right, bottom, left)
        padding_tuple = self._normalize_padding(self.padding)
        pad_y, pad_x = padding_tuple[0], padding_tuple[1]
        
        content_width = inner_width - (pad_x * 2)
        content_width = max(content_width, 1)

        # Ensure content_width is at least 1
        content_width = max(content_width, 20)

        # Render content to list of strings first to properly handle multi-line
        content_lines: List[str] = []

        def wrap_line_with_ansi(line: str, max_width: int) -> List[str]:
            """Wrap a line that may contain ANSI codes, preserving them correctly.

            This handles emojis and wide characters properly by using visual width.
            """
            if not line:
                return [""]

            # Check if line fits without wrapping
            plain = ansi_escape.sub("", line)
            if wcswidth(plain) <= max_width:
                return [line]

            # Need to wrap - must handle ANSI codes and wide characters carefully
            result_lines = []
            current_line = ""
            current_visual_width = 0
            i = 0

            while i < len(line):
                # Check for ANSI escape sequence
                if line[i:i+2] == '\033[':
                    # Find end of ANSI sequence (ends with letter A-Z or m)
                    j = i + 2
                    while j < len(line) and line[j] not in 'ABCDEFGHJKSTfmnsulh':
                        j += 1
                    if j < len(line):
                        j += 1  # Include the final character
                    # Add ANSI code without counting towards visual width
                    current_line += line[i:j]
                    i = j
                else:
                    # Regular character - check visual width
                    # Handle multi-byte characters (emojis, CJK, etc.)
                    char = line[i]

                    # Try to get multi-byte character if this is start of one
                    if ord(char) > 127 or char == '\ufffd':
                        # Could be start of multi-byte, try to get full character
                        # Emojis can be 1-4 bytes in UTF-8
                        char_width = wcswidth(char)
                    else:
                        char_width = wcswidth(char)

                    # Check if adding this char would exceed width
                    if current_visual_width + char_width > max_width and current_line:
                        # Start a new line
                        # Strip trailing ANSI reset to avoid color bleed issues
                        result_lines.append(current_line)
                        current_line = ""
                        current_visual_width = 0

                    current_line += char
                    current_visual_width += char_width
                    i += 1

            # Add remaining content
            if current_line:
                result_lines.append(current_line)

            return result_lines if result_lines else [""]

        if isinstance(self.renderable, str):
            # For strings, apply markup processing first
            processed = console._apply_markup(self.renderable) if console.markup else self.renderable

            # Split by explicit newlines first, then wrap each line if needed
            explicit_lines = processed.split('\n')

            for line in explicit_lines:
                # Use the new wrapper that handles ANSI + emojis
                wrapped = wrap_line_with_ansi(line, content_width)
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
            """Calculate visual width of text, stripping ANSI codes.
            
            This properly handles emojis and wide characters which take
            2 terminal columns instead of 1.
            """
            plain = ansi_escape.sub("", text)
            return wcswidth(plain)
        
        def pad_line(line: str, width: int) -> str:
            """Pad a line to the specified visual width.
            
            This properly handles:
            - ANSI escape codes (don't count towards width)
            - Emojis and wide characters (count as 2 columns each)
            
            Args:
                line: The line to pad (may contain ANSI codes)
                width: Target visual width (number of terminal columns)
            
            Returns:
                The line padded with spaces to reach the target visual width
            """
            # Calculate visual width: strip ANSI codes first, then measure
            plain = ansi_escape.sub("", line)
            visual_width = wcswidth(plain)
            
            if visual_width < width:
                # Need padding - add spaces to reach target visual width
                return line + " " * (width - visual_width)
            # If line is at or exceeds target width, return as-is
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
            
            # Calculate the visual width of this line (including emojis)
            # and ensure it fits within content_width
            visual_len = wcswidth(ansi_escape.sub("", line))
            
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
