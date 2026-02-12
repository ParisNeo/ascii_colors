# -*- coding: utf-8 -*-
"""
Text renderable and base renderable class for rich compatibility.
"""

from abc import ABC, abstractmethod
from typing import Iterator, List, Optional, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ascii_colors.rich.console import Console, ConsoleOptions
    from ascii_colors.rich.style import Style

from ascii_colors.constants import ANSI
from ascii_colors.rich.style import Style as StyleClass, Color

# Try to import wcwidth for better Unicode handling
try:
    from wcwidth import wcswidth, wcwidth as wcwidth_func
    _HAS_WCWIDTH = True
except ImportError:
    _HAS_WCWIDTH = False
    def wcswidth(s: str) -> int:
        """Fallback wcswidth that approximates width."""
        return sum(2 if ord(c) > 127 else 1 for c in s)
    def wcwidth_func(c: str) -> int:
        """Fallback wcwidth."""
        return 2 if ord(c) > 127 else 1


class Renderable(ABC):
    """Abstract base class for renderable objects."""
    
    @abstractmethod
    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[Union[str, "Renderable"]]:
        """Render to console."""
        pass
    
    def __rich_measure__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> "Measurement":
        """Measure the renderable."""
        from ascii_colors.rich.console import Measurement
        return Measurement(1, options.max_width)


class Text(Renderable):
    """A renderable text object with styling."""
    
    def __init__(
        self,
        text: Optional[Union[str, "Text"]] = None,
        style: Optional[Union[str, "Style"]] = None,
        justify: Optional[str] = None,
        overflow: str = "fold",
        no_wrap: bool = False,
        end: str = "",
    ):
        self._spans: List[Tuple[int, int, "Style"]] = []
        self.justify = justify
        self.overflow = overflow
        self.no_wrap = no_wrap
        self.end = end
        
        # Handle Text objects - recursively extract plain text
        if isinstance(text, Text):
            self.plain = text.plain if isinstance(text.plain, str) else str(text.plain)
            for start, end_pos, text_style in text._spans:
                self._spans.append((start, end_pos, text_style))
        else:
            self.plain = text if isinstance(text, str) else (str(text) if text is not None else "")
        
        self.style = style if isinstance(style, StyleClass) else (StyleClass.parse(style) if style else None)
    
    def __str__(self) -> str:
        if isinstance(self.plain, str):
            return self.plain
        return str(self.plain)
    
    def __len__(self) -> int:
        return len(self.plain)
    
    def append(
        self,
        text: Union[str, "Text"],
        style: Optional[Union[str, "Style"]] = None,
    ) -> "Text":
        """Append text to this Text object."""
        if isinstance(text, Text):
            offset = len(self.plain)
            text_str = text.plain if isinstance(text.plain, str) else str(text.plain)
            self.plain += text_str
            for start, end, text_style in text._spans:
                self._spans.append((start + offset, end + offset, text_style))
            return self
        
        offset = len(self.plain)
        self.plain += text
        if style:
            style_obj = style if isinstance(style, StyleClass) else StyleClass.parse(style)
            self._spans.append((offset, offset + len(text), style_obj))
        return self
    
    def truncate(self, max_width: int, overflow: Optional[str] = None) -> "Text":
        """Truncate text to max_width."""
        overflow = overflow or self.overflow
        width = wcswidth(self.plain)
        
        if width <= max_width:
            return self
        
        if overflow == "ellipsis":
            truncated = self.plain[:max(0, max_width - 3)] + "..."
        else:
            truncated = self.plain[:max_width]
        
        new_text = Text(truncated, style=self.style)
        for start, end, style in self._spans:
            if start < len(truncated):
                new_text._spans.append((start, min(end, len(truncated)), style))
        
        return new_text
    
    def pad(self, width: int, align: str = "left", char: str = " ") -> "Text":
        """Pad text to width with alignment."""
        text_width = wcswidth(self.plain)
        if text_width >= width:
            return self
        
        pad_len = width - text_width
        if align == "left":
            new_plain = self.plain + char * pad_len
        elif align == "right":
            new_plain = char * pad_len + self.plain
        elif align == "center":
            left = pad_len // 2
            right = pad_len - left
            new_plain = char * left + self.plain + char * right
        else:
            new_plain = self.plain + char * pad_len
        
        new_text = Text(new_plain, style=self.style)
        offset = len(new_plain) - len(self.plain)
        for start, end, style in self._spans:
            if align == "right":
                new_start = start + pad_len
                new_end = end + pad_len
            elif align == "center":
                new_start = start + (pad_len // 2)
                new_end = end + (pad_len // 2)
            else:
                new_start = start
                new_end = end
            new_text._spans.append((new_start, new_end, style))
        
        return new_text
    
    def wrap(self, width: int) -> List["Text"]:
        """Wrap text into multiple lines."""
        if self.no_wrap or width <= 0:
            return [self]
        
        lines = []
        current_line = ""
        current_width = 0
        
        for char in self.plain:
            char_width = wcwidth_func(char)
            
            if current_width + char_width > width and current_line:
                lines.append(Text(current_line))
                current_line = char
                current_width = char_width
            else:
                current_line += char
                current_width += char_width
        
        if current_line:
            lines.append(Text(current_line))
        
        if not lines:
            lines = [Text("")]
        
        return lines
    
    def render(self, width: Optional[int] = None) -> str:
        """Render text with ANSI codes."""
        if not self._spans and not self.style:
            return self.plain
        
        result_parts = []
        prev_end = 0
        
        sorted_spans = sorted(self._spans, key=lambda x: x[0])
        
        for start, end_pos, span_style in sorted_spans:
            if start > prev_end:
                result_parts.append(self.plain[prev_end:start])
            
            if span_style:
                result_parts.append(str(span_style))
                result_parts.append(self.plain[start:end_pos])
                result_parts.append(ANSI.color_reset)
            else:
                result_parts.append(self.plain[start:end_pos])
            
            prev_end = end_pos
        
        if prev_end < len(self.plain):
            result_parts.append(self.plain[prev_end:])
        
        if self.style and not self._spans:
            result_parts.insert(0, str(self.style))
            result_parts.append(ANSI.color_reset)
        
        result = "".join(result_parts)
        
        if width and self.justify:
            text_width = wcswidth(self.plain)
            if text_width < width:
                if self.justify == "center":
                    pad = (width - text_width) // 2
                    result = " " * pad + result + " " * (width - text_width - pad)
                elif self.justify == "right":
                    result = " " * (width - text_width) + result
        
        return result
    
    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[Union[str, Renderable]]:
        """Render to console."""
        lines = self.wrap(options.max_width)
        for i, line in enumerate(lines):
            if i > 0:
                yield "\n"
            yield line.render(options.max_width)
    
    def __rich_measure__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> "Measurement":
        """Measure the renderable."""
        from ascii_colors.rich.console import Measurement
        width = wcswidth(self.plain)
        return Measurement(min(width, 1), min(width, options.max_width))
