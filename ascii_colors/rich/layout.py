# -*- coding: utf-8 -*-
"""
Layout components: Panel, Padding, and Columns.
"""

import re
import textwrap
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from ascii_colors.rich.console import Console, ConsoleOptions

from ascii_colors.constants import ANSI
from ascii_colors.rich.style import Style, BoxStyle, box
from ascii_colors.rich.text import Text, Renderable, wcswidth

# Import Measurement at module level for type annotations
from ascii_colors.rich.console import Measurement

# ANSI escape sequence regex - compile once for efficiency
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

_UNSET = object()


def visual_width(text: str) -> int:
    """Calculate the visual width of text, ignoring ANSI escape codes."""
    plain = ANSI_ESCAPE.sub("", text)
    return wcswidth(plain)


def wrap_line_preserving_ansi(line: str, max_width: int) -> List[str]:
    """Wrap a line that may contain ANSI codes and wide characters."""
    if not line:
        return [""]
    
    if visual_width(line) <= max_width:
        return [line]
    
    result_lines = []
    current_line = ""
    current_visual_width = 0
    i = 0
    line_len = len(line)
    
    while i < line_len:
        if line[i:i+2] in ('\033[', '\x1b['):
            j = i + 2
            while j < line_len and line[j] not in 'ABCDEFGHJKSTfmnsulh':
                j += 1
            if j < line_len:
                j += 1
            current_line += line[i:j]
            i = j
        else:
            char = line[i]
            char_width = wcswidth(char)
            
            if current_visual_width + char_width > max_width and current_line:
                result_lines.append(current_line)
                current_line = ""
                current_visual_width = 0
            
            current_line += char
            current_visual_width += char_width
            i += 1
    
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
        
        pad_tuple = cast(Tuple[int, ...], pad)
        
        if len(pad_tuple) == 2:
            return (pad_tuple[0], pad_tuple[1], pad_tuple[0], pad_tuple[1])
        elif len(pad_tuple) == 4:
            return (pad_tuple[0], pad_tuple[1], pad_tuple[2], pad_tuple[3])
        else:
            first = pad_tuple[0] if len(pad_tuple) > 0 else 0
            return (first, first, first, first)
    
    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[Renderable]:
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


class Panel(Renderable):
    """A bordered panel around content with in-place update support.
    
    This class supports:
    - Rich markup tags and ANSI codes
    - In-place updates via update() and property assignment
    - Title on top border and Subtitle on bottom border with left/center/right alignment
    - Auto-sizing with Panel.fit() and expand=False
    - Custom BoxStyles (SQUARE, ROUND, DOUBLE, HEAVY, ASCII, etc.)
    """
    
    def __init__(
        self,
        renderable: Union[Renderable, str],
        title: Optional[str] = None,
        title_align: str = "center",
        subtitle: Optional[str] = None,
        subtitle_align: str = "center",
        style: Optional[Union[str, Style]] = None,
        border_style: Optional[Union[str, Style]] = None,
        box: Union[BoxStyle, str] = BoxStyle.SQUARE,
        padding: Union[int, Tuple[int, ...]] = (0, 1),
        width: Optional[int] = None,
        height: Optional[int] = None,
        expand: bool = True,
        highlight: bool = False,
    ):
        self._renderable = renderable if isinstance(renderable, Renderable) else Text(renderable)
        self.title = title
        self.title_align = title_align
        self.subtitle = subtitle
        self.subtitle_align = subtitle_align
        self.style = style if isinstance(style, Style) else (Style.parse(style) if style else None)
        self.border_style = border_style if isinstance(border_style, Style) else (Style.parse(border_style) if border_style else None)
        self.box = box if isinstance(box, BoxStyle) else (BoxStyle(box) if isinstance(box, str) and box in [b.value for b in BoxStyle] else BoxStyle.SQUARE)
        self.padding = padding if isinstance(padding, tuple) else (padding, padding)
        self.width = width
        self.height = height
        self.expand = expand
        self.highlight = highlight

    @property
    def renderable(self) -> Union[Renderable, str]:
        """Get the panel renderable content."""
        return self._renderable

    @renderable.setter
    def renderable(self, value: Union[Renderable, str]) -> None:
        """Set the panel renderable content."""
        self._renderable = value if isinstance(value, Renderable) else Text(value)

    def update(
        self,
        renderable: Optional[Union[Renderable, str]] = None,
        *,
        title: Any = _UNSET,
        title_align: Any = _UNSET,
        subtitle: Any = _UNSET,
        subtitle_align: Any = _UNSET,
        style: Any = _UNSET,
        border_style: Any = _UNSET,
        box: Any = _UNSET,
        padding: Any = _UNSET,
        width: Any = _UNSET,
        height: Any = _UNSET,
        expand: Any = _UNSET,
    ) -> "Panel":
        """Update panel content and attributes in-place.
        
        Args:
            renderable: New content to display in the panel.
            title: New title on top border.
            title_align: Alignment of title ('left', 'center', 'right').
            subtitle: New subtitle on bottom border.
            subtitle_align: Alignment of subtitle ('left', 'center', 'right').
            style: Inner styling.
            border_style: Border color / styling.
            box: Box drawing style.
            padding: Inner padding tuple or int.
            width: Explicit width override.
            height: Explicit height override.
            expand: Whether panel expands to full available width.
            
        Returns:
            self for convenient method chaining.
        """
        if renderable is not None:
            self.renderable = renderable
        if title is not _UNSET:
            self.title = title
        if title_align is not _UNSET:
            self.title_align = title_align
        if subtitle is not _UNSET:
            self.subtitle = subtitle
        if subtitle_align is not _UNSET:
            self.subtitle_align = subtitle_align
        if style is not _UNSET:
            self.style = style if isinstance(style, Style) else (Style.parse(style) if style else None)
        if border_style is not _UNSET:
            self.border_style = border_style if isinstance(border_style, Style) else (Style.parse(border_style) if border_style else None)
        if box is not _UNSET:
            self.box = box if isinstance(box, BoxStyle) else (BoxStyle(box) if isinstance(box, str) and box in [b.value for b in BoxStyle] else BoxStyle.SQUARE)
        if padding is not _UNSET:
            self.padding = padding if isinstance(padding, tuple) else (padding, padding)
        if width is not _UNSET:
            self.width = width
        if height is not _UNSET:
            self.height = height
        if expand is not _UNSET:
            self.expand = expand
        return self

    @classmethod
    def fit(
        cls,
        renderable: Union[Renderable, str],
        title: Optional[str] = None,
        title_align: str = "center",
        subtitle: Optional[str] = None,
        subtitle_align: str = "center",
        style: Optional[Union[str, Style]] = None,
        border_style: Optional[Union[str, Style]] = None,
        box: Union[BoxStyle, str] = BoxStyle.SQUARE,
        padding: Union[int, Tuple[int, ...]] = (0, 1),
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> "Panel":
        """Create a panel that is just wide enough to fit its content."""
        return cls(
            renderable,
            title=title,
            title_align=title_align,
            subtitle=subtitle,
            subtitle_align=subtitle_align,
            style=style,
            border_style=border_style,
            box=box,
            padding=padding,
            width=width,
            height=height,
            expand=False,
        )

    def _normalize_padding(
        self,
        pad: Union[int, Tuple[int, ...]]
    ) -> Tuple[int, int, int, int]:
        """Normalize padding to (top, right, bottom, left)."""
        if isinstance(pad, int):
            return (pad, pad, pad, pad)
        
        pad_tuple = cast(Tuple[int, ...], pad)
        
        if len(pad_tuple) == 2:
            return (pad_tuple[0], pad_tuple[1], pad_tuple[0], pad_tuple[1])
        elif len(pad_tuple) == 4:
            return (pad_tuple[0], pad_tuple[1], pad_tuple[2], pad_tuple[3])
        else:
            first = pad_tuple[0] if len(pad_tuple) > 0 else 0
            return (first, first, first, first)

    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[Union[str, Renderable]]:
        chars = self.box.get_chars()
        
        max_safe_width = min(options.max_width, console.width - 2) if hasattr(console, 'width') else options.max_width - 2
        max_safe_width = max(max_safe_width, 10)
        
        padding_tuple = self._normalize_padding(self.padding)
        pad_y, pad_x = padding_tuple[0], padding_tuple[1]
        
        ansi_escape = re.compile(r"\033\[[0-9;]*[a-zA-Z]")
        
        if self.width:
            panel_width = min(self.width, max_safe_width)
        elif not self.expand:
            title_w = 0
            if self.title:
                t_clean = console._apply_markup(self.title) if console.markup else self.title
                title_w = wcswidth(ansi_escape.sub("", t_clean)) + 4
            
            sub_w = 0
            if self.subtitle:
                s_clean = console._apply_markup(self.subtitle) if console.markup else self.subtitle
                sub_w = wcswidth(ansi_escape.sub("", s_clean)) + 4
            
            content_w = 0
            if isinstance(self._renderable, str):
                lines = self._renderable.split('\n')
                content_w = max((wcswidth(ansi_escape.sub("", l)) for l in lines), default=0)
            elif isinstance(self._renderable, Text):
                lines = str(self._renderable.plain).split('\n')
                content_w = max((wcswidth(ansi_escape.sub("", l)) for l in lines), default=0)
            elif hasattr(self._renderable, '__rich_measure__'):
                meas = self._renderable.__rich_measure__(console, options)
                content_w = meas.maximum
            else:
                try:
                    meas = Measurement.get(console, options, self._renderable)
                    content_w = meas.maximum
                except Exception:
                    content_w = 20
            
            fitted = max(content_w + pad_x * 2 + 2, title_w, sub_w, 10)
            panel_width = min(fitted, max_safe_width)
        else:
            panel_width = max_safe_width
        
        inner_width = max(panel_width - 2, 1)
        content_width = max(inner_width - (pad_x * 2), 1)

        content_lines: List[str] = []

        if isinstance(self._renderable, str):
            processed = console._apply_markup(self._renderable) if console.markup else self._renderable
            explicit_lines = processed.split('\n')
            for line in explicit_lines:
                wrapped = wrap_line_preserving_ansi(line, content_width)
                content_lines.extend(wrapped)
        elif isinstance(self._renderable, Text):
            plain_content = str(self._renderable.plain)
            if '[' in plain_content and console.markup:
                processed = console._apply_markup(plain_content)
            else:
                processed = plain_content
            
            explicit_lines = processed.split('\n')
            for line in explicit_lines:
                wrapped = wrap_line_preserving_ansi(line, content_width)
                content_lines.extend(wrapped)
        else:
            try:
                rendered = console.render(self._renderable, options.update_width(content_width))
                for item in rendered:
                    line_str = str(item.plain) if isinstance(item, Text) else str(item)
                    sub_lines = line_str.split('\n')
                    for sub_line in sub_lines:
                        wrapped = wrap_line_preserving_ansi(sub_line, content_width)
                        content_lines.extend(wrapped)
            except Exception:
                content_lines = [str(self._renderable)]
        
        border_ansi = str(self.border_style) if self.border_style else ""
        style_ansi = str(self.style) if self.style else ""
        reset = ANSI.color_reset
        
        def pad_line(line: str, width: int) -> str:
            plain = ansi_escape.sub("", line)
            vis_w = wcswidth(plain)
            if vis_w < width:
                return line + " " * (width - vis_w)
            return line
        
        # Build top border with title if present
        if self.title:
            title_clean = console._apply_markup(self.title) if console.markup else self.title
            title_clean = re.sub(r'\x1b\[0m$', '', title_clean)
            title_clean = re.sub(r'\x1b\[0m(?=\s*$)', '', title_clean)
            
            title_plain = ansi_escape.sub("", title_clean)
            title_width = wcswidth(title_plain)
            available_for_lines = inner_width - title_width - 2
            
            if available_for_lines < 0:
                max_title_len = max(1, inner_width - 4)
                title_plain_truncated = title_plain[:max_title_len]
                title_width = wcswidth(title_plain_truncated)
                title_clean = title_plain_truncated
                available_for_lines = inner_width - title_width - 2
            
            if self.title_align == "center":
                left_line_len = max(0, available_for_lines // 2)
                right_line_len = max(0, available_for_lines - left_line_len)
            elif self.title_align == "right":
                left_line_len = max(0, available_for_lines - 1)
                right_line_len = 1
            else:
                left_line_len = 1
                right_line_len = max(0, available_for_lines - 1)
            
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
        
        # Content rows
        rendered_content_count = 0
        for line in content_lines:
            line = line.rstrip('\n\r')
            padded_content = pad_line(line, content_width)
            
            if self.style:
                styled_content = f"{style_ansi}{' ' * pad_x}{padded_content}{' ' * pad_x}{reset}"
            else:
                styled_content = f"{' ' * pad_x}{padded_content}{' ' * pad_x}"
            
            yield (
                f"{border_ansi}{chars['vertical']}{reset}"
                f"{styled_content}"
                f"{border_ansi}{chars['vertical']}{reset}"
            )
            rendered_content_count += 1
            
        # Empty padding rows at bottom
        for _ in range(pad_y):
            fill = f"{style_ansi}{' ' * inner_width}{reset}" if self.style else " " * inner_width
            yield f"{border_ansi}{chars['vertical']}{reset}{fill}{border_ansi}{chars['vertical']}{reset}"

        # Height filler rows if explicit height is larger than content
        if self.height:
            current_total_lines = 2 + pad_y * 2 + rendered_content_count
            extra_lines_needed = max(0, self.height - current_total_lines)
            for _ in range(extra_lines_needed):
                fill = f"{style_ansi}{' ' * inner_width}{reset}" if self.style else " " * inner_width
                yield f"{border_ansi}{chars['vertical']}{reset}{fill}{border_ansi}{chars['vertical']}{reset}"
        
        # Bottom border (with subtitle if present)
        if self.subtitle:
            sub_clean = console._apply_markup(self.subtitle) if console.markup else self.subtitle
            sub_clean = re.sub(r'\x1b\[0m$', '', sub_clean)
            sub_clean = re.sub(r'\x1b\[0m(?=\s*$)', '', sub_clean)
            
            sub_plain = ansi_escape.sub("", sub_clean)
            sub_width = wcswidth(sub_plain)
            available_for_lines = inner_width - sub_width - 2
            
            if available_for_lines < 0:
                max_sub_len = max(1, inner_width - 4)
                sub_plain_truncated = sub_plain[:max_sub_len]
                sub_width = wcswidth(sub_plain_truncated)
                sub_clean = sub_plain_truncated
                available_for_lines = inner_width - sub_width - 2
            
            if self.subtitle_align == "center":
                left_line_len = max(0, available_for_lines // 2)
                right_line_len = max(0, available_for_lines - left_line_len)
            elif self.subtitle_align == "right":
                left_line_len = max(0, available_for_lines - 1)
                right_line_len = 1
            else:
                left_line_len = 1
                right_line_len = max(0, available_for_lines - 1)
            
            left_part = f"{border_ansi}{chars['bottom_left']}{chars['horizontal'] * left_line_len}{reset}"
            sub_part = f" {sub_clean} "
            right_part = f"{border_ansi}{chars['horizontal'] * right_line_len}{chars['bottom_right']}{reset}"
            bottom_border = left_part + sub_part + right_part
        else:
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


class Rule(Renderable):
    """A horizontal rule with optional title."""

    def __init__(
        self,
        title: str = "",
        characters: str = "─",
        style: Optional[Union[str, Style]] = None,
        align: str = "center",
    ):
        self.title = title
        self.characters = characters
        self.style = style if isinstance(style, Style) else (Style.parse(style) if style else None)
        self.align = align

    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[str]:
        width = options.max_width
        style_ansi = str(self.style) if self.style else ""
        reset = ANSI.color_reset

        if self.title:
            title_clean = console._apply_markup(self.title) if console.markup else self.title
            title_plain = re.sub(r"\033\[[0-9;]*[a-zA-Z]", "", title_clean)
            title_width = wcswidth(title_plain)
            char_width = width - title_width - 2

            if self.align == "left":
                left, right = 0, max(0, char_width)
            elif self.align == "right":
                left, right = max(0, char_width), 0
            else:
                left = max(0, char_width // 2)
                right = max(0, char_width - left)

            left_part = self.characters * left
            right_part = self.characters * right

            if style_ansi:
                yield f"{style_ansi}{left_part}{reset} {title_clean} {style_ansi}{right_part}{reset}"
            else:
                yield f"{left_part} {title_clean} {right_part}"
        else:
            line = self.characters * width
            yield f"{style_ansi}{line}{reset}" if style_ansi else line

    def __rich_measure__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> "Measurement":
        return Measurement(1, options.max_width)


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
                if isinstance(item, Text):
                    lines = [str(line.plain) if isinstance(line.plain, str) else str(line) for line in item.wrap(col_width - self.padding)]
                elif isinstance(item, str):
                    text = Text(item)
                    lines = [str(line.plain) if isinstance(line.plain, str) else str(line) for line in text.wrap(col_width - self.padding)]
                else:
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