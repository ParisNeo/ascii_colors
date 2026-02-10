# -*- coding: utf-8 -*-
"""
Rich library compatibility layer for ascii_colors.
Provides a pure-Python implementation of Rich's core features
for terminal rendering without external dependencies.
"""

from __future__ import annotations

import os
import sys
import re
import math
import shutil
import time
import threading
from abc import ABC, abstractmethod
from enum import Enum, auto
from contextlib import contextmanager
from typing import (
    Any, Callable, Dict, List, Optional, Tuple, Union, Iterator, 
    Iterable, TextIO, overload, Literal
)
from ascii_colors.constants import ANSI

# Get builtin print to avoid conflicts with rich.print
import builtins
_builtin_print = builtins.print

# Try to import wcwidth for better Unicode handling
try:
    from wcwidth import wcswidth, wcwidth
    _HAS_WCWIDTH = True
except ImportError:
    _HAS_WCWIDTH = False
    def wcswidth(s: str) -> int:
        """Fallback wcswidth that approximates width."""
        return sum(2 if ord(c) > 127 else 1 for c in s)
    def wcwidth(c: str) -> int:
        """Fallback wcwidth."""
        return 2 if ord(c) > 127 else 1


# ============== Measurement and Sizing ==============

class ConsoleOptions:
    """Options for rendering to console."""
    
    def __init__(
        self,
        max_width: int = 80,
        min_width: int = 1,
        max_height: Optional[int] = None,
        legacy_windows: Optional[bool] = None,
        ascii_only: bool = False,
        size: Optional[Tuple[int, int]] = None,
    ):
        self.max_width = max_width
        self.min_width = min_width
        self.max_height = max_height
        self.legacy_windows = legacy_windows
        self.ascii_only = ascii_only
        self.size = size or (max_width, max_height or 25)
    
    def update_width(self, width: int) -> ConsoleOptions:
        """Return new options with updated width."""
        new_options = ConsoleOptions(
            max_width=width,
            min_width=self.min_width,
            max_height=self.max_height,
            legacy_windows=self.legacy_windows,
            ascii_only=self.ascii_only,
            size=(width, self.size[1] if self.size else 25),
        )
        return new_options


class Measurement:
    """Measurement of renderable dimensions."""
    
    def __init__(self, minimum: int, maximum: int):
        self.minimum = minimum
        self.maximum = maximum
    
    @classmethod
    def get(
        cls,
        console: Console,
        options: ConsoleOptions,
        renderable: Renderable,
    ) -> Measurement:
        """Get measurement of a renderable."""
        # Default measurement - try to get actual width
        if hasattr(renderable, '__len__'):
            try:
                length = len(renderable)
                return cls(length, length)
            except:
                pass
        
        # Default to console width
        return cls(1, options.max_width)
    
    def normalize(self) -> Measurement:
        """Ensure minimum <= maximum."""
        return Measurement(min(self.minimum, self.maximum), max(self.minimum, self.maximum))


# ============== Base Renderable ==============

class Renderable(ABC):
    """Abstract base class for renderable objects."""
    
    @abstractmethod
    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> Iterator[Union[str, Renderable]]:
        """Render to console."""
        pass
    
    def __rich_measure__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> Measurement:
        """Measure the renderable."""
        return Measurement(1, options.max_width)


# ============== Style and Color System ==============

class Color:
    """Represents a color for terminal output."""
    
    def __init__(self, name: Optional[str] = None, rgb: Optional[Tuple[int, int, int]] = None):
        self.name = name
        self.rgb = rgb
    
    @classmethod
    def parse(cls, color_str: str) -> Color:
        """Parse a color string into a Color object."""
        # Handle hex colors
        if color_str.startswith('#'):
            hex_val = color_str[1:]
            if len(hex_val) == 3:
                rgb = tuple(int(c * 2, 16) for c in hex_val)
            elif len(hex_val) == 6:
                rgb = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
            else:
                rgb = (255, 255, 255)
            return cls(rgb=rgb)
        
        # Handle named colors
        color_map = {
            'black': (0, 0, 0),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'yellow': (255, 255, 0),
            'blue': (0, 0, 255),
            'magenta': (255, 0, 255),
            'cyan': (0, 255, 255),
            'white': (255, 255, 255),
            'bright_black': (85, 85, 85),
            'bright_red': (255, 85, 85),
            'bright_green': (85, 255, 85),
            'bright_yellow': (255, 255, 85),
            'bright_blue': (85, 85, 255),
            'bright_magenta': (255, 85, 255),
            'bright_cyan': (85, 255, 255),
            'bright_white': (255, 255, 255),
        }
        
        rgb = color_map.get(color_str.lower(), (255, 255, 255))
        return cls(name=color_str, rgb=rgb)
    
    def __str__(self) -> str:
        if self.name:
            return self.name
        if self.rgb:
            r, g, b = self.rgb
            return f"#{r:02x}{g:02x}{b:02x}"
        return "default"


class Style:
    """Represents text styling (color, bold, italic, etc.)."""
    
    def __init__(
        self,
        color: Optional[Union[str, Color]] = None,
        background: Optional[Union[str, Color]] = None,
        bold: Optional[bool] = None,
        dim: Optional[bool] = None,
        italic: Optional[bool] = None,
        underline: Optional[bool] = None,
        blink: Optional[bool] = None,
        reverse: Optional[bool] = None,
        strike: Optional[bool] = None,
    ):
        self.color = Color.parse(color) if isinstance(color, str) else color
        self.background = Color.parse(background) if isinstance(background, str) else background
        self.bold = bold
        self.dim = dim
        self.italic = italic
        self.underline = underline
        self.blink = blink
        self.reverse = reverse
        self.strike = strike
    
    @classmethod
    def parse(cls, style_str: str) -> Style:
        """Parse a style string like 'bold red on blue'."""
        style = cls()
        
        parts = style_str.lower().split()
        i = 0
        while i < len(parts):
            part = parts[i]
            
            if part == 'bold':
                style.bold = True
            elif part == 'dim':
                style.dim = True
            elif part == 'italic':
                style.italic = True
            elif part == 'underline':
                style.underline = True
            elif part == 'blink':
                style.blink = True
            elif part == 'reverse':
                style.reverse = True
            elif part == 'strike' or part == 'strikethrough':
                style.strike = True
            elif part == 'on' and i + 1 < len(parts):
                i += 1
                style.background = Color.parse(parts[i])
            else:
                # Assume it's a color
                style.color = Color.parse(part)
            
            i += 1
        
        return style
    
    def __str__(self) -> str:
        """Convert style to ANSI escape codes."""
        codes = []
        
        if self.bold:
            codes.append(ANSI.style_bold)
        if self.dim:
            codes.append(ANSI.style_dim)
        if self.italic:
            codes.append(ANSI.style_italic)
        if self.underline:
            codes.append(ANSI.style_underline)
        if self.blink:
            codes.append(ANSI.style_blink)
        if self.reverse:
            codes.append(ANSI.style_reverse)
        if self.strike:
            codes.append(ANSI.style_strikethrough)
        
        # Foreground color
        if self.color:
            if self.color.rgb:
                r, g, b = self.color.rgb
                codes.append(f"\033[38;2;{r};{g};{b}m")
            elif self.color.name:
                # Map color name to ANSI
                name = self.color.name.lower()
                color_map = {
                    'black': ANSI.color_black, 'red': ANSI.color_red,
                    'green': ANSI.color_green, 'yellow': ANSI.color_yellow,
                    'blue': ANSI.color_blue, 'magenta': ANSI.color_magenta,
                    'cyan': ANSI.color_cyan, 'white': ANSI.color_white,
                    'bright_black': ANSI.color_bright_black,
                    'bright_red': ANSI.color_bright_red,
                    'bright_green': ANSI.color_bright_green,
                    'bright_yellow': ANSI.color_bright_yellow,
                    'bright_blue': ANSI.color_bright_blue,
                    'bright_magenta': ANSI.color_bright_magenta,
                    'bright_cyan': ANSI.color_bright_cyan,
                    'bright_white': ANSI.color_bright_white,
                }
                if name in color_map:
                    codes.append(color_map[name])
        
        # Background color
        if self.background:
            if self.background.rgb:
                r, g, b = self.background.rgb
                codes.append(f"\033[48;2;{r};{g};{b}m")
            elif self.background.name:
                name = self.background.name.lower()
                bg_map = {
                    'black': ANSI.color_bg_black, 'red': ANSI.color_bg_red,
                    'green': ANSI.color_bg_green, 'yellow': ANSI.color_bg_yellow,
                    'blue': ANSI.color_bg_blue, 'magenta': ANSI.color_bg_magenta,
                    'cyan': ANSI.color_bg_cyan, 'white': ANSI.color_bg_white,
                    'bright_black': ANSI.color_bg_bright_black,
                    'bright_red': ANSI.color_bg_bright_red,
                    'bright_green': ANSI.color_bg_bright_green,
                    'bright_yellow': ANSI.color_bg_bright_yellow,
                    'bright_blue': ANSI.color_bg_bright_blue,
                    'bright_magenta': ANSI.color_bg_bright_magenta,
                    'bright_cyan': ANSI.color_bg_bright_cyan,
                    'bright_white': ANSI.color_bg_bright_white,
                }
                if name in bg_map:
                    codes.append(bg_map[name])
        
        return "".join(codes)
    
    def __add__(self, other: Style) -> Style:
        """Combine two styles."""
        return Style(
            color=other.color or self.color,
            background=other.background or self.background,
            bold=other.bold if other.bold is not None else self.bold,
            dim=other.dim if other.dim is not None else self.dim,
            italic=other.italic if other.italic is not None else self.italic,
            underline=other.underline if other.underline is not None else self.underline,
            blink=other.blink if other.blink is not None else self.blink,
            reverse=other.reverse if other.reverse is not None else self.reverse,
            strike=other.strike if other.strike is not None else self.strike,
        )


# ============== Text and Content ==============

class Text(Renderable):
    """A renderable text object with styling."""
    
    def __init__(
        self,
        text: Optional[Union[str, Text]] = None,
        style: Optional[Union[str, Style]] = None,
        justify: Optional[Literal["left", "center", "right", "full"]] = None,
        overflow: Literal["fold", "crop", "ellipsis"] = "fold",
        no_wrap: bool = False,
        end: str = "",
    ):
        self._spans: List[Tuple[int, int, Style]] = []
        self.justify = justify
        self.overflow = overflow
        self.no_wrap = no_wrap
        self.end = end
        
        # Handle Text objects - recursively extract plain text
        if isinstance(text, Text):
            # Get the plain string representation, not the object itself
            self.plain = text.plain if isinstance(text.plain, str) else str(text.plain)
            # Merge spans from the other text object with offset 0
            for start, end_pos, text_style in text._spans:
                self._spans.append((start, end_pos, text_style))
        else:
            self.plain = text if isinstance(text, str) else (str(text) if text is not None else "")
        
        self.style = style if isinstance(style, Style) else (Style.parse(style) if style else None)
    
    def __str__(self) -> str:
        # Always return a string, never a Text object
        if isinstance(self.plain, str):
            return self.plain
        return str(self.plain)
    
    def __len__(self) -> int:
        return len(self.plain)
    
    def append(self, text: Union[str, Text], style: Optional[Union[str, Style]] = None) -> Text:
        """Append text to this Text object."""
        if isinstance(text, Text):
            # Append with its own styles converted to our offsets
            offset = len(self.plain)
            # Ensure we're appending a string, not a Text object
            text_str = text.plain if isinstance(text.plain, str) else str(text.plain)
            self.plain += text_str
            for start, end, text_style in text._spans:
                self._spans.append((start + offset, end + offset, text_style))
            return self
        
        # Append plain string with optional style
        offset = len(self.plain)
        self.plain += text
        if style:
            style_obj = style if isinstance(style, Style) else Style.parse(style)
            self._spans.append((offset, offset + len(text), style_obj))
        return self
    
    def truncate(self, max_width: int, overflow: Optional[str] = None) -> Text:
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
        # Adjust spans
        for start, end, style in self._spans:
            if start < len(truncated):
                new_text._spans.append((start, min(end, len(truncated)), style))
        
        return new_text
    
    def pad(self, width: int, align: str = "left", char: str = " ") -> Text:
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
        
        # Adjust spans for padding
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
    
    def wrap(self, width: int) -> List[Text]:
        """Wrap text into multiple lines."""
        if self.no_wrap or width <= 0:
            return [self]
        
        lines = []
        current_line = ""
        current_width = 0
        
        for char in self.plain:
            char_width = wcwidth(char)
            
            if current_width + char_width > width and current_line:
                lines.append(Text(current_line))
                current_line = char
                current_width = char_width
            else:
                current_line += char
                current_width += char_width
        
        if current_line:
            lines.append(Text(current_line))
        
        # Handle empty string
        if not lines:
            lines = [Text("")]
        
        return lines
    
    def render(self, width: Optional[int] = None) -> str:
        """Render text with ANSI codes."""
        if not self._spans and not self.style:
            return self.plain
        
        # Build styled output
        result_parts = []
        prev_end = 0
        
        # Sort spans by start position
        sorted_spans = sorted(self._spans, key=lambda x: x[0])
        
        for start, end_pos, span_style in sorted_spans:
            # Add unstyled text before span
            if start > prev_end:
                result_parts.append(self.plain[prev_end:start])
            
            # Add styled text
            if span_style:
                result_parts.append(str(span_style))
                result_parts.append(self.plain[start:end_pos])
                result_parts.append(ANSI.color_reset)
            else:
                result_parts.append(self.plain[start:end_pos])
            
            prev_end = end_pos
        
        # Add remaining unstyled text
        if prev_end < len(self.plain):
            result_parts.append(self.plain[prev_end:])
        
        # Apply base style if no spans
        if self.style and not self._spans:
            result_parts.insert(0, str(self.style))
            result_parts.append(ANSI.color_reset)
        
        result = "".join(result_parts)
        
        # Apply justification if width provided
        if width and self.justify:
            text_width = wcswidth(self.plain)
            if text_width < width:
                if self.justify == "center":
                    pad = (width - text_width) // 2
                    result = " " * pad + result + " " * (width - text_width - pad)
                elif self.justify == "right":
                    result = " " * (width - text_width) + result
        
        return result
    
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> Iterator[Union[str, Renderable]]:
        """Render to console."""
        lines = self.wrap(options.max_width)
        for i, line in enumerate(lines):
            if i > 0:
                yield "\n"
            yield line.render(options.max_width)
    
    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        """Measure the renderable."""
        width = wcswidth(self.plain)
        return Measurement(min(width, 1), min(width, options.max_width))


# ============== Console ==============

class Console:
    """Console for rich text output."""
    
    def __init__(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        file: Optional[TextIO] = None,
        force_terminal: Optional[bool] = None,
        force_jupyter: Optional[bool] = None,
        force_width: Optional[int] = None,
        force_height: Optional[int] = None,
        no_color: bool = False,
        tab_size: int = 4,
        record: bool = False,
        markup: bool = True,
        emoji: bool = True,
        emoji_variant: Optional[str] = None,
        highlight: bool = True,
        log_time: bool = True,
        log_path: bool = True,
        log_time_format: str = "[%X]",
        highlighter: Optional[Any] = None,
        legacy_windows: Optional[bool] = None,
        safe_box: bool = True,
        get_environ: Callable[[str], Any] = lambda x: None,
        get_time: Optional[Callable[[], float]] = None,
        get_terminal_size: Optional[Callable[[], Tuple[int, int]]] = None,
    ):
        self.file = file or sys.stdout
        self._width = width
        self._height = height
        self.force_terminal = force_terminal
        self.force_jupyter = force_jupyter
        self.no_color = no_color
        self.tab_size = tab_size
        self.record = record
        self._record_buffer: List[str] = []
        self.markup = markup
        self.emoji = emoji
        self.emoji_variant = emoji_variant
        self.highlight = highlight
        self.log_time = log_time
        self.log_path = log_path
        self.log_time_format = log_time_format
        self.safe_box = safe_box
        self.legacy_windows = legacy_windows
        
        # Detect environment
        self._is_terminal = self._detect_terminal()
        self._color_system: Optional[str] = "standard" if not no_color else None
    
    def _detect_terminal(self) -> bool:
        """Detect if we're running in a terminal."""
        if self.force_terminal is not None:
            return self.force_terminal
        
        try:
            return self.file.isatty()
        except:
            return False
    
    @property
    def width(self) -> int:
        """Get console width."""
        if self._width is not None:
            return self._width
        
        if self.file is sys.stdout or self.file is sys.stderr:
            try:
                return shutil.get_terminal_size().columns
            except:
                return 80
        
        return 80
    
    @property
    def height(self) -> int:
        """Get console height."""
        if self._height is not None:
            return self._height
        
        try:
            return shutil.get_terminal_size().lines
        except:
            return 25
    
    @property
    def size(self) -> Tuple[int, int]:
        """Get console size as (width, height)."""
        return (self.width, self.height)
    
    def _apply_markup(self, text: str) -> str:
        """Apply rich markup like [bold]text[/bold]."""
        if not self.markup or self.no_color:
            # Strip markup tags
            return re.sub(r'\[/?[^\]]+\]', '', text)
        
        # Simple markup parser
        style_pattern = r'\[([^\]]+)\](.*?)\[/\1\]'
        
        def replace_style(match):
            style_str = match.group(1)
            content = match.group(2)
            
            # Parse style
            style = Style.parse(style_str)
            ansi_codes = str(style)
            
            return f"{ansi_codes}{content}{ANSI.color_reset}"
        
        # Keep applying until no more matches (for nested styles)
        result = text
        for _ in range(5):  # Max nesting depth
            new_result = re.sub(style_pattern, replace_style, result, flags=re.DOTALL)
            if new_result == result:
                break
            result = new_result
        
        # Clean up any remaining tags
        result = re.sub(r'\[/?[^\]]+\]', '', result)
        
        return result
    
    def render(self, renderable: Union[Renderable, str], options: Optional[ConsoleOptions] = None) -> List[str]:
        """Render a renderable to lines."""
        if options is None:
            options = ConsoleOptions(max_width=self.width)
        
        # Handle strings
        if isinstance(renderable, str):
            markup_rendered = self._apply_markup(renderable)
            return markup_rendered.split("\n")
        
        # Handle Text objects
        if isinstance(renderable, Text):
            wrapped = renderable.wrap(options.max_width)
            return [line.render(options.max_width) for line in wrapped]
        
        # Handle Renderable objects
        if hasattr(renderable, '__rich_console__'):
            lines = []
            for segment in renderable.__rich_console__(self, options):
                if isinstance(segment, str):
                    lines.extend(segment.split("\n"))
                elif hasattr(segment, '__rich_console__'):
                    # Recursively render
                    sub_lines = self.render(segment, options)
                    lines.extend(sub_lines)
                elif isinstance(segment, Text):
                    sub_lines = segment.wrap(options.max_width)
                    lines.extend([line.render(options.max_width) for line in sub_lines])
            return lines
        
        # Fallback
        return str(renderable).split("\n")
    
    def print(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[Union[str, Style]] = None,
        justify: Optional[str] = None,
        overflow: Optional[str] = None,
        no_wrap: Optional[bool] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        width: Optional[int] = None,
        crop: bool = True,
        soft_wrap: bool = False,
    ) -> None:
        """Print objects to the console."""
        # Combine objects
        output_parts = []
        for i, obj in enumerate(objects):
            if i > 0:
                output_parts.append(sep)
            
            if isinstance(obj, str):
                output_parts.append(obj)
            elif isinstance(obj, Text):
                # Use the plain string, not the Text object itself
                output_parts.append(obj.plain if isinstance(obj.plain, str) else str(obj.plain))
            elif hasattr(obj, '__rich_console__'):
                # Render rich object
                lines = self.render(obj)
                output_parts.append("\n".join(lines))
            else:
                output_parts.append(str(obj))
        
        output = "".join(output_parts)
        
        # Apply markup if enabled
        if markup if markup is not None else self.markup:
            output = self._apply_markup(output)
        
        # Apply style if provided
        if style:
            style_obj = style if isinstance(style, Style) else Style.parse(style)
            output = f"{style_obj}{output}{ANSI.color_reset}"
        
        # Ensure newline
        if not output.endswith(end):
            output += end
        
        # Output using builtin print to avoid recursion
        _builtin_print(output, end="", file=self.file or None)
        
        # Record if enabled
        if self.record:
            self._record_buffer.append(output)
    
    def log(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[Union[str, Style]] = None,
        justify: Optional[str] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
    ) -> None:
        """Log to console with timestamp."""
        import datetime
        time_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        time_style = Style(dim=True)
        
        # Build log line with timestamp
        output_parts = [f"{time_style}[{time_str}]{ANSI.color_reset}"]
        
        for obj in objects:
            if isinstance(obj, str):
                output_parts.append(obj)
            else:
                output_parts.append(str(obj))
        
        log_line = " ".join(output_parts)
        
        # Apply style
        if style:
            style_obj = style if isinstance(style, Style) else Style.parse(style)
            log_line = f"{style_obj}{log_line}{ANSI.color_reset}"
        
        _builtin_print(log_line, end=end, file=self.file or None)
        
        if self.record:
            self._record_buffer.append(log_line + end)
    
    def rule(
        self,
        title: str = "",
        characters: str = "─",
        style: Optional[Union[str, Style]] = None,
        align: Literal["left", "center", "right"] = "center",
    ) -> None:
        """Print a horizontal rule."""
        width = self.width
        
        if title:
            title_clean = self._apply_markup(title)
            title_width = wcswidth(title_clean)
            char_width = width - title_width - 2  # Spaces around title
            
            if align == "left":
                left = 0
                right = char_width
            elif align == "right":
                left = char_width
                right = 0
            else:  # center
                left = char_width // 2
                right = char_width - left
            
            line = characters * left + " " + title + " " + characters * right
        else:
            line = characters * width
        
        # Apply style
        if style:
            style_obj = style if isinstance(style, Style) else Style.parse(style)
            line = f"{style_obj}{line}{ANSI.color_reset}"
        
        _builtin_print(line, file=self.file or None)
    
    def input(
        self,
        prompt: str = "",
        *,
        markup: bool = True,
        emoji: bool = True,
        password: bool = False,
        stream: Optional[TextIO] = None,
    ) -> str:
        """Get input from user with styled prompt."""
        if markup:
            prompt = self._apply_markup(prompt)
        
        if stream is None:
            stream = self.file
        
        # Print prompt
        _builtin_print(prompt, end="", file=stream)
        
        # Get input
        if password:
            import getpass
            return getpass.getpass("")
        else:
            return input()
    
    def export_text(self, clear: bool = True, styles: bool = False) -> str:
        """Export recorded output as text."""
        result = "".join(self._record_buffer)
        if clear:
            self._record_buffer.clear()
        return result
    
    @contextmanager
    def capture(self):
        """Capture console output."""
        old_record = self.record
        old_buffer = self._record_buffer[:]
        
        self.record = True
        self._record_buffer = []
        
        class CaptureResult:
            def __init__(self, buffer: List[str]):
                self._buffer = buffer
            
            def get(self) -> str:
                return "".join(self._buffer)
        
        try:
            yield CaptureResult(self._record_buffer)
        finally:
            self.record = old_record
            self._record_buffer = old_buffer
    
    def clear(self, home: bool = False) -> None:
        """Clear the console."""
        if home:
            _builtin_print("\033[H", end="", file=self.file or None)
        else:
            _builtin_print("\033[2J\033[H", end="", file=self.file or None)
    
    def save_screen(self) -> None:
        """Save current screen."""
        _builtin_print("\033[?47h", end="", file=self.file or None)
    
    def restore_screen(self) -> None:
        """Restore saved screen."""
        _builtin_print("\033[?47l", end="", file=self.file or None)


# ============== BoxStyle Enum ==============

class BoxStyle(Enum):
    """Box drawing styles."""
    SQUARE = "square"
    ROUND = "round"
    MINIMAL = "minimal"
    MINIMAL_HEAVY_HEAD = "minimal_heavy_head"
    SIMPLE = "simple"
    SIMPLE_HEAD = "simple_head"
    DOUBLE = "double"
    
    def get_chars(self) -> Dict[str, str]:
        """Get characters for this box style."""
        chars = {
            'top_left': '┌', 'top_right': '┐',
            'bottom_left': '└', 'bottom_right': '┘',
            'horizontal': '─', 'vertical': '│',
            'left_t': '├', 'right_t': '┤',
            'top_t': '┬', 'bottom_t': '┴',
            'cross': '┼',
        }
        
        if self == BoxStyle.ROUND:
            chars['top_left'] = '╭'
            chars['top_right'] = '╮'
            chars['bottom_left'] = '╰'
            chars['bottom_right'] = '╯'
        elif self == BoxStyle.DOUBLE:
            chars['top_left'] = '╔'
            chars['top_right'] = '╗'
            chars['bottom_left'] = '╚'
            chars['bottom_right'] = '╝'
            chars['horizontal'] = '═'
            chars['vertical'] = '║'
            chars['left_t'] = '╠'
            chars['right_t'] = '╣'
            chars['top_t'] = '╦'
            chars['bottom_t'] = '╩'
            chars['cross'] = '╬'
        elif self == BoxStyle.MINIMAL:
            chars = {
                'top_left': ' ', 'top_right': ' ',
                'bottom_left': ' ', 'bottom_right': ' ',
                'horizontal': '─', 'vertical': ' ',
                'left_t': ' ', 'right_t': ' ',
                'top_t': '─', 'bottom_t': '─',
                'cross': '─',
            }
        
        return chars


# ============== Layout Components ==============

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
    
    def _normalize_padding(self, pad: Union[int, Tuple[int, ...]]) -> Tuple[int, int, int, int]:
        """Normalize padding to (top, right, bottom, left)."""
        if isinstance(pad, int):
            return (pad, pad, pad, pad)
        elif len(pad) == 2:
            return (pad[0], pad[1], pad[0], pad[1])
        elif len(pad) == 4:
            return pad
        else:
            return (0, 1, 0, 1)
    
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> Iterator[Renderable]:
        top, right, bottom, left = self.pad
        
        # Yield top padding
        for _ in range(top):
            yield Text(" " * options.max_width)
        
        # Yield content with side padding
        for line in console.render(self.renderable, options.update_width(options.max_width - left - right)):
            yield Text(" " * left + line + " " * right)
        
        # Yield bottom padding
        for _ in range(bottom):
            yield Text(" " * options.max_width)


class Panel:
    """A bordered panel around content."""
    
    def __init__(
        self,
        renderable: Union[Renderable, str],
        title: Optional[str] = None,
        title_align: Literal["left", "center", "right"] = "center",
        border_style: Optional[Union[str, Style]] = None,
        box: Union[BoxStyle, str] = BoxStyle.SQUARE,
        padding: Union[int, Tuple[int, ...]] = (0, 1),
        width: Optional[int] = None,
        height: Optional[int] = None,
    ):
        self.renderable = renderable if isinstance(renderable, Renderable) else Text(renderable)
        self.title = title
        self.title_align = title_align
        self.border_style = border_style if isinstance(border_style, Style) else (Style.parse(border_style) if border_style else None)
        self.box = box if isinstance(box, BoxStyle) else BoxStyle.SQUARE
        self.padding = padding if isinstance(padding, tuple) else (padding, padding)
        self.width = width
        self.height = height
    
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> Iterator[Union[str, Renderable]]:
        chars = self.box.get_chars()
        max_width = self.width or options.max_width
        
        # Ensure we don't exceed console width
        max_width = min(max_width, options.max_width)
        
        # Calculate inner width (accounting for borders)
        inner_width = max_width - 2  # Left and right borders
        
        # Normalize padding
        if isinstance(self.padding, int):
            pad_y, pad_x = self.padding, self.padding
        elif len(self.padding) == 2:
            pad_y, pad_x = self.padding
        else:
            pad_y, pad_x = self.padding[0], self.padding[1]
        
        # Available width for content after padding
        content_width = inner_width - pad_x * 2
        content_width = max(content_width, 1)
        
        # Get content lines
        content_lines = []
        if isinstance(self.renderable, Text):
            wrapped = self.renderable.wrap(content_width)
            content_lines = [line.plain for line in wrapped]
        else:
            rendered = console.render(self.renderable, options.update_width(content_width))
            content_lines = rendered
        
        # Build title
        title_text = ""
        if self.title:
            title_clean = console._apply_markup(self.title)
            title_width = wcswidth(title_clean)
            
            # Ensure title fits within panel
            title_width = min(title_width, inner_width - 4)
            
            if self.title_align == "center":
                left = (inner_width - title_width) // 2
                right = inner_width - title_width - left
            elif self.title_align == "right":
                left = inner_width - title_width - 1
                right = 1
            else:  # left
                left = 1
                right = inner_width - title_width - 1
            
            title_text = chars['horizontal'] * left + " " + self.title + " " + chars['horizontal'] * right
        else:
            title_text = chars['horizontal'] * inner_width
        
        # Get styles
        border_ansi = str(self.border_style) if self.border_style else ""
        reset = ANSI.color_reset
        
        # Top border
        yield f"{border_ansi}{chars['top_left']}{title_text}{chars['top_right']}{reset}"
        
        # Empty padding lines (top)
        for _ in range(pad_y):
            yield f"{border_ansi}{chars['vertical']}{reset}{' ' * inner_width}{border_ansi}{chars['vertical']}{reset}"
        
        # Content lines with side padding
        for line in content_lines:
            line_width = wcswidth(line)
            padded = line + " " * (content_width - line_width)
            yield f"{border_ansi}{chars['vertical']}{reset}{' ' * pad_x}{padded}{' ' * pad_x}{border_ansi}{chars['vertical']}{reset}"
        
        # Empty padding lines (bottom)
        for _ in range(pad_y):
            yield f"{border_ansi}{chars['vertical']}{reset}{' ' * inner_width}{border_ansi}{chars['vertical']}{reset}"
        
        # Bottom border
        yield f"{border_ansi}{chars['bottom_left']}{chars['horizontal'] * inner_width}{chars['bottom_right']}{reset}"
    
    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
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
    
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> Iterator[Renderable]:
        if not self.renderables:
            return
        
        width = self.width or options.max_width
        
        # Calculate columns - use a helper to get width safely
        def get_renderable_width(r):
            if isinstance(r, Text):
                return wcswidth(r.plain)
            elif isinstance(r, str):
                return wcswidth(r)
            else:
                # For other renderables, try to get a reasonable estimate
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
        
        # Arrange items
        rows = []
        current_row = []
        for i, item in enumerate(self.renderables):
            if len(current_row) >= num_cols:
                rows.append(current_row)
                current_row = []
            current_row.append(item)
        
        if current_row:
            rows.append(current_row)
        
        # Yield rows
        for row in rows:
            # Render each item in row
            row_lines = []
            max_lines = 0
            
            for item in row:
                if isinstance(item, Text):
                    lines = [line.plain for line in item.wrap(col_width - self.padding)]
                else:
                    lines = console.render(item, options.update_width(col_width - self.padding))
                row_lines.append(lines)
                max_lines = max(max_lines, len(lines))
            
            # Yield each line
            for line_idx in range(max_lines):
                parts = []
                for col_idx, lines in enumerate(row_lines):
                    if line_idx < len(lines):
                        line_str = str(lines[line_idx])
                        parts.append(line_str.ljust(col_width - self.padding))
                    else:
                        parts.append(" " * (col_width - self.padding))
                
                # Join parts with padding
                result = (" " * self.padding).join(parts)
                yield Text(result)
    
    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        return Measurement(10, options.max_width)


# ============== Data Display ==============

class Table:
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
    
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> Iterator[Union[str, Renderable]]:
        chars = self.box.get_chars()
        max_width = self.width or options.max_width
        
        # Calculate column widths
        col_count = len(self.headers)
        col_widths = [0] * col_count
        
        # Header widths
        for i, h in enumerate(self.headers):
            col_widths[i] = max(col_widths[i], wcswidth(h))
        
        # Row widths
        for row in self.rows:
            for i, cell in enumerate(row):
                if i < col_count:
                    col_widths[i] = max(col_widths[i], wcswidth(str(cell)))
        
        # Add padding
        pad_x, pad_y = self.padding
        for i in range(col_count):
            col_widths[i] += pad_x * 2
        
        # Total width
        total_width = sum(col_widths) + (col_count + 1)  # Borders
        
        # Scale if needed
        if self.expand and total_width < max_width:
            extra = max_width - total_width
            per_col = extra // col_count
            for i in range(col_count):
                col_widths[i] += per_col
        
        # Truncate if needed
        if total_width > max_width:
            available = max_width - (col_count + 1)
            for i in range(col_count):
                col_widths[i] = max(3, (available * col_widths[i]) // sum(col_widths))
        
        # Get styles
        border_ansi = str(Style.parse(self.border_style)) if self.border_style else ""
        header_ansi = str(self.header_style) if self.header_style else ""
        reset = ANSI.color_reset
        
        # Title
        if self.title:
            title_clean = console._apply_markup(self.title)
            title_width = wcswidth(title_clean)
            left = (total_width - title_width) // 2
            yield f"{border_ansi}{' ' * left}{self.title}{' ' * (total_width - title_width - left)}{reset}"
            yield ""
        
        # Top border
        if self.show_edge:
            parts = [chars['top_left']]
            for i, w in enumerate(col_widths):
                parts.append(chars['horizontal'] * w)
                if i < len(col_widths) - 1:
                    parts.append(chars['top_t'])
                else:
                    parts.append(chars['top_right'])
            yield f"{border_ansi}{''.join(parts)}{reset}"
        
        # Header
        if self.show_header:
            parts = [chars['vertical']]
            for i, (h, w) in enumerate(zip(self.headers, col_widths)):
                cell = str(h).center(w - pad_x * 2)
                parts.append(" " * pad_x + f"{header_ansi}{cell}{reset}{border_ansi}" + " " * pad_x)
                parts.append(chars['vertical'])
            yield f"{border_ansi}{''.join(parts)}{reset}"
            
            # Separator
            parts = [chars['left_t']]
            for i, w in enumerate(col_widths):
                parts.append(chars['horizontal'] * w)
                if i < len(col_widths) - 1:
                    parts.append(chars['cross'])
                else:
                    parts.append(chars['right_t'])
            yield f"{border_ansi}{''.join(parts)}{reset}"
        
        # Rows
        for row_idx, row in enumerate(self.rows):
            # Row content
            parts = [chars['vertical']]
            row_style = None
            if self.row_styles:
                style_idx = row_idx % len(self.row_styles)
                row_style = self.row_styles[style_idx]
                if isinstance(row_style, str):
                    row_style = Style.parse(row_style)
            
            row_ansi = str(row_style) if row_style else ""
            
            for i, (cell, w) in enumerate(zip(row, col_widths)):
                cell_str = str(cell)
                cell_width = wcswidth(cell_str)
                pad = w - pad_x * 2 - cell_width
                left_pad = pad // 2
                right_pad = pad - left_pad
                parts.append(" " * pad_x + f"{row_ansi}{' ' * left_pad}{cell_str}{' ' * right_pad}{reset}{border_ansi}" + " " * pad_x)
                parts.append(chars['vertical'])
            
            yield f"{border_ansi}{''.join(parts)}{reset}"
            
            # Row separator
            if self.show_lines and row_idx < len(self.rows) - 1:
                parts = [chars['left_t']]
                for i, w in enumerate(col_widths):
                    parts.append(chars['horizontal'] * w)
                    if i < len(col_widths) - 1:
                        parts.append(chars['cross'])
                    else:
                        parts.append(chars['right_t'])
                yield f"{border_ansi}{''.join(parts)}{reset}"
        
        # Bottom border
        if self.show_edge:
            parts = [chars['bottom_left']]
            for i, w in enumerate(col_widths):
                parts.append(chars['horizontal'] * w)
                if i < len(col_widths) - 1:
                    parts.append(chars['bottom_t'])
                else:
                    parts.append(chars['bottom_right'])
            yield f"{border_ansi}{''.join(parts)}{reset}"
        
        # Caption
        if self.caption:
            yield ""
            yield self.caption
    
    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        min_width = len(self.headers) * 3 + len(self.headers) + 1
        return Measurement(min_width, options.max_width)


class Tree:
    """A tree structure for display."""
    
    def __init__(
        self,
        label: Union[str, Text, Renderable],
        *,
        style: Optional[Union[str, Style]] = None,
        guide_style: Optional[Union[str, Style]] = None,
        expanded: bool = True,
        highlight: bool = False,
    ):
        self.label = label if isinstance(label, (Text, Renderable)) else Text(label)
        self.style = style if isinstance(style, Style) else (Style.parse(style) if style else None)
        self.guide_style = guide_style if isinstance(guide_style, Style) else (Style.parse(guide_style) if guide_style else Style(dim=True))
        self.expanded = expanded
        self.highlight = highlight
        self.children: List[Tree] = []
    
    def add(self, label: Union[str, Text, Tree], *, style: Optional[Union[str, Style]] = None) -> Tree:
        """Add a child node."""
        if isinstance(label, Tree):
            child = label
        else:
            # Ensure label is converted to proper type
            if isinstance(label, Text):
                child = Tree(label, style=style or self.style)
            else:
                child = Tree(str(label), style=style or self.style)
        self.children.append(child)
        return child
    
    def add_node(self, label: Union[str, Text]) -> Tree:
        """Add a child node and return it for chaining."""
        # Ensure label is properly converted
        if isinstance(label, Text):
            child = Tree(label, style=self.style)
        else:
            child = Tree(str(label), style=self.style)
        self.children.append(child)
        return child
    
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> Iterator[Union[str, Renderable]]:
        style_ansi = str(self.style) if self.style else ""
        guide_ansi = str(self.guide_style) if self.guide_style else ""
        reset = ANSI.color_reset
        
        # Render label
        if isinstance(self.label, str):
            label_str = self.label
        elif isinstance(self.label, Text):
            label_str = self.label.plain if isinstance(self.label.plain, str) else str(self.label.plain)
        else:
            # Try to render other types
            try:
                rendered = list(console.render(self.label, options))
                label_str = rendered[0] if rendered else str(self.label)
            except:
                label_str = str(self.label)
        
        yield f"{style_ansi}{label_str}{reset}"
        
        # Render children
        for i, child in enumerate(self.children):
            is_last = i == len(self.children) - 1
            
            # Choose guide characters
            if is_last:
                branch = "└── "
                guide = "    "
            else:
                branch = "├── "
                guide = "│   "
            
            # Render child lines with guides
            child_lines = list(console.render(child, options))
            
            for j, line in enumerate(child_lines):
                if j == 0:
                    yield f"{guide_ansi}{branch}{reset}{line}"
                else:
                    yield f"{guide_ansi}{guide}{reset}{line}"
    
    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        return Measurement(10, options.max_width)


# ============== Content Types ==============

class Syntax:
    """Syntax highlighted code."""
    
    def __init__(
        self,
        code: str,
        lexer: str = "python",
        line_numbers: bool = False,
        line_number_start: int = 1,
        highlight_lines: Optional[List[int]] = None,
        code_width: Optional[int] = None,
        tab_size: int = 4,
        theme: Optional[Dict[str, str]] = None,
        word_wrap: bool = False,
        indent_guides: bool = False,
        padding: int = 0,
    ):
        self.code = code
        self.lexer = lexer
        self.line_numbers = line_numbers
        self.line_number_start = line_number_start
        self.highlight_lines = highlight_lines or []
        self.code_width = code_width
        self.tab_size = tab_size
        self.theme = theme or self._default_theme()
        self.word_wrap = word_wrap
        self.indent_guides = indent_guides
        self.padding = padding
    
    def _default_theme(self) -> Dict[str, str]:
        """Default color theme for syntax highlighting."""
        return {
            'keyword': ANSI.color_magenta,
            'string': ANSI.color_green,
            'number': ANSI.color_cyan,
            'comment': ANSI.color_bright_black,
            'function': ANSI.color_blue,
            'class': ANSI.color_yellow,
            'operator': ANSI.color_red,
            'default': ANSI.color_white,
        }
    
    def _tokenize(self, code: str) -> List[Tuple[str, str]]:
        """Simple tokenizer for syntax highlighting."""
        lines = code.split('\n')
        tokens = []
        
        for line in lines:
            # Very simple tokenization based on patterns
            i = 0
            while i < len(line):
                char = line[i]
                
                # Skip leading whitespace
                if char.isspace():
                    j = i
                    while j < len(line) and line[j].isspace():
                        j += 1
                    tokens.append(('whitespace', line[i:j]))
                    i = j
                    continue
                
                # Comments
                if char == '#':
                    tokens.append(('comment', line[i:]))
                    break
                
                # Strings
                if char in '"\'':
                    quote = char
                    j = i + 1
                    while j < len(line):
                        if line[j] == quote and (j == i + 1 or line[j-1] != '\\'):
                            j += 1
                            break
                        j += 1
                    tokens.append(('string', line[i:j]))
                    i = j
                    continue
                
                # Numbers
                if char.isdigit():
                    j = i
                    while j < len(line) and (line[j].isdigit() or line[j] == '.'):
                        j += 1
                    tokens.append(('number', line[i:j]))
                    i = j
                    continue
                
                # Keywords and identifiers
                if char.isalpha() or char == '_':
                    j = i
                    while j < len(line) and (line[j].isalnum() or line[j] == '_'):
                        j += 1
                    word = line[i:j]
                    keywords = {
                        'def', 'class', 'if', 'elif', 'else', 'for', 'while', 
                        'try', 'except', 'finally', 'with', 'import', 'from',
                        'return', 'yield', 'async', 'await', 'lambda', 'pass',
                        'break', 'continue', 'raise', 'assert', 'del', 'global',
                        'nonlocal', 'in', 'is', 'not', 'and', 'or', 'True',
                        'False', 'None',
                    }
                    if word in keywords:
                        tokens.append(('keyword', word))
                    elif word[0].isupper():
                        tokens.append(('class', word))
                    else:
                        tokens.append(('default', word))
                    i = j
                    continue
                
                # Operators
                if char in '+-*/=<>!&|^%~:':
                    j = i
                    while j < len(line) and line[j] in '+-*/=<>!&|^%~:':
                        j += 1
                    tokens.append(('operator', line[i:j]))
                    i = j
                    continue
                
                # Default
                tokens.append(('default', char))
                i += 1
            
            tokens.append(('newline', '\n'))
        
        return tokens
    
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> Iterator[str]:
        tokens = self._tokenize(self.code)
        
        # Build lines
        lines = []
        current_line = []
        
        for token_type, text in tokens:
            if token_type == 'newline':
                lines.append(current_line)
                current_line = []
            else:
                color = self.theme.get(token_type, self.theme['default'])
                current_line.append(f"{color}{text}{ANSI.color_reset}")
        
        if current_line:
            lines.append(current_line)
        
        # Render with line numbers
        line_num = self.line_number_start
        max_line_num = self.line_number_start + len(lines) - 1
        line_num_width = len(str(max_line_num))
        
        for line in lines:
            if self.line_numbers:
                is_highlighted = line_num in self.highlight_lines
                line_style = ANSI.style_bold if is_highlighted else ANSI.style_dim
                prefix = f"{line_style}{line_num:>{line_num_width}} │ {ANSI.color_reset}"
                yield prefix + "".join(line)
            else:
                yield "".join(line)
            
            line_num += 1
    
    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        lines = self.code.split('\n')
        max_len = max(len(line) for line in lines) if lines else 0
        return Measurement(min(20, max_len), options.max_width)


class Markdown:
    """Markdown rendering for terminal."""
    
    def __init__(
        self,
        markup: str,
        code_theme: Optional[str] = None,
        justify: Optional[Literal["left", "center", "right", "full"]] = None,
        style: Optional[Union[str, Style]] = None,
        hyperlinks: bool = True,
    ):
        self.markup = markup
        self.code_theme = code_theme
        self.justify = justify
        self.style = style
        self.hyperlinks = hyperlinks
    
    def _parse_markdown(self) -> List[Tuple[str, str, int]]:
        """Parse markdown into (type, content, level) tuples."""
        lines = self.markup.split('\n')
        result = []
        
        in_code = False
        code_lang = ""
        code_content = []
        
        for line in lines:
            # Code blocks
            if line.strip().startswith('```'):
                if in_code:
                    # End code block
                    result.append(('code', '\n'.join(code_content), code_lang))
                    code_content = []
                    in_code = False
                else:
                    # Start code block
                    code_lang = line.strip()[3:].strip()
                    in_code = True
                continue
            
            if in_code:
                code_content.append(line)
                continue
            
            # Headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                result.append(('header', header_match.group(2), level))
                continue
            
            # Blockquote
            if line.startswith('>'):
                result.append(('quote', line[1:].strip(), 0))
                continue
            
            # List items
            list_match = re.match(r'^([\*\-\+]|\d+\.)\s+(.+)$', line)
            if list_match:
                result.append(('list', list_match.group(2), 0))
                continue
            
            # Empty line
            if not line.strip():
                result.append(('empty', '', 0))
                continue
            
            # Paragraph
            result.append(('para', line, 0))
        
        return result
    
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> Iterator[Union[str, Renderable]]:
        elements = self._parse_markdown()
        
        for elem_type, content, level in elements:
            if elem_type == 'header':
                styles = {
                    1: ANSI.style_bold + ANSI.color_bright_white,
                    2: ANSI.style_bold + ANSI.color_white,
                    3: ANSI.color_bright_white,
                    4: ANSI.color_white + ANSI.style_underline,
                    5: ANSI.color_white,
                    6: ANSI.style_dim,
                }
                style = styles.get(level, ANSI.color_white)
                underline = "═" * min(len(content), options.max_width) if level <= 2 else ""
                
                yield f"{style}{content}{ANSI.color_reset}"
                if underline:
                    yield f"{style}{underline}{ANSI.color_reset}"
                yield ""
            
            elif elem_type == 'para':
                yield content
                yield ""
            
            elif elem_type == 'list':
                yield f"  • {content}"
            
            elif elem_type == 'quote':
                yield f"{ANSI.style_dim}│ {content}{ANSI.color_reset}"
            
            elif elem_type == 'code':
                # Use Syntax for code blocks
                syntax = Syntax(content, lexer=content if content else 'text', line_numbers=False)
                for line in console.render(syntax, options):
                    yield line
                yield ""
            
            elif elem_type == 'empty':
                yield ""
    
    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        return Measurement(20, options.max_width)


# ============== Live Display ==============

class Live:
    """Live updating display."""
    
    def __init__(
        self,
        renderable: Optional[Renderable] = None,
        console: Optional[Console] = None,
        screen: bool = False,
        auto_refresh: bool = True,
        refresh_per_second: float = 4,
        vertical_overflow: Literal["crop", "ellipsis", "visible"] = "ellipsis",
        get_renderable: Optional[Callable[[], Renderable]] = None,
    ):
        self.renderable = renderable
        self.console = console or Console()
        self.screen = screen
        self.auto_refresh = auto_refresh
        self.refresh_per_second = refresh_per_second
        self.vertical_overflow = vertical_overflow
        self.get_renderable = get_renderable
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._rendered_content: List[str] = []
        self._lock = threading.Lock()
    
    def __enter__(self) -> Live:
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
    
    def start(self) -> None:
        """Start live display."""
        if self.screen:
            self.console.save_screen()
        
        # Initial render
        self._render()
        
        # Start auto-refresh thread
        if self.auto_refresh:
            self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
            self._refresh_thread.start()
    
    def stop(self) -> None:
        """Stop live display."""
        self._stop_event.set()
        
        if self._refresh_thread:
            self._refresh_thread.join(timeout=1)
        
        if self.screen:
            self.console.restore_screen()
        
        # Final render
        self._render(clear=False)
    
    def _refresh_loop(self) -> None:
        """Background refresh loop."""
        while not self._stop_event.is_set():
            time.sleep(1.0 / self.refresh_per_second)
            if not self._stop_event.is_set():
                self.refresh()
    
    def _render(self, clear: bool = True) -> None:
        """Render current content."""
        with self._lock:
            renderable = self.renderable
            if self.get_renderable:
                renderable = self.get_renderable()
            
            if renderable is None:
                return
            
            # Clear previous output
            if clear and self._rendered_content:
                lines_to_clear = len(self._rendered_content)
                # Move up and clear lines
                for _ in range(lines_to_clear):
                    _builtin_print("\033[F\033[K", end="", file=self.console.file or None)
            
            # Render new content
            lines = self.console.render(renderable)
            self._rendered_content = lines
            
            for line in lines:
                _builtin_print(line, file=self.console.file or None)
            
            _builtin_print("", end="", flush=True, file=self.console.file or None)
    
    def update(self, renderable: Renderable, *, refresh: bool = False) -> None:
        """Update the renderable."""
        with self._lock:
            self.renderable = renderable
        
        if refresh or not self.auto_refresh:
            self.refresh()
    
    def refresh(self) -> None:
        """Force a refresh."""
        self._render()


class Status:
    """Status spinner display."""
    
    # Spinner animations
    SPINNERS = {
        'dots': '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏',
        'line': '⎺⎻⎼⎽⎼⎻',
        'arrow': '←↖↑↗→↘↓↙',
        'pulse': '◐◓◑◒',
        'star': '✶✸✹✺✹✷',
        'moon': '🌑🌒🌓🌔🌕🌖🌗🌘',
    }
    
    def __init__(
        self,
        status: str,
        *,
        console: Optional[Console] = None,
        spinner: str = 'dots',
        spinner_style: Optional[Union[str, Style]] = None,
        speed: float = 1.0,
    ):
        self.status = status
        self.console = console or Console()
        self.spinner_chars = self.SPINNERS.get(spinner, self.SPINNERS['dots'])
        self.spinner_style = spinner_style if isinstance(spinner_style, Style) else (Style.parse(spinner_style) if spinner_style else Style(color='green'))
        self.speed = speed
        self._live: Optional[Live] = None
        self._frame = 0
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def __enter__(self) -> Status:
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
    
    def _get_renderable(self) -> Text:
        """Get current spinner frame."""
        with self._lock:
            char = self.spinner_chars[self._frame % len(self.spinner_chars)]
            self._frame += 1
            
            style = self.spinner_style
            style_str = str(style) if style else ""
            
            # Build status line
            status_text = f"{style_str}{char}{ANSI.color_reset} {self.status}"
            return Text(status_text)
    
    def start(self) -> None:
        """Start the status display."""
        self._live = Live(
            console=self.console,
            auto_refresh=True,
            refresh_per_second=self.speed * 10,
            get_renderable=self._get_renderable,
        )
        self._live.start()
    
    def stop(self) -> None:
        """Stop the status display."""
        if self._live:
            self._live.stop()
            self._live = None
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=1)
    
    def update(self, status: str, *, spinner: Optional[str] = None, speed: Optional[float] = None) -> None:
        """Update status text."""
        self.status = status
        if spinner:
            self.spinner_chars = self.SPINNERS.get(spinner, self.spinner_chars)
        if speed:
            self.speed = speed


# ============== Module-level Interface ==============

class RichModule:
    """Module-like interface for rich compatibility."""
    
    def __init__(self):
        self._console = Console()
    
    @property
    def console(self) -> Console:
        """Get the default console."""
        return self._console
    
    def print(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[Union[str, Style]] = None,
        justify: Optional[str] = None,
        overflow: Optional[str] = None,
        no_wrap: Optional[bool] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
    ) -> None:
        """Print to the default console."""
        self._console.print(
            *objects,
            sep=sep,
            end=end,
            style=style,
            justify=justify,
            overflow=overflow,
            no_wrap=no_wrap,
            emoji=emoji,
            markup=markup,
            highlight=highlight,
        )
    
    def log(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[Union[str, Style]] = None,
    ) -> None:
        """Log to the default console."""
        self._console.log(*objects, sep=sep, end=end, style=style)
    
    def rule(
        self,
        title: str = "",
        characters: str = "─",
        style: Optional[Union[str, Style]] = None,
        align: Literal["left", "center", "right"] = "center",
    ) -> None:
        """Print a rule to the default console."""
        self._console.rule(title, characters=characters, style=style, align=align)
    
    def status(
        self,
        status: str,
        *,
        spinner: str = 'dots',
        spinner_style: Optional[Union[str, Style]] = None,
        speed: float = 1.0,
    ) -> Status:
        """Create a status spinner."""
        return Status(
            status,
            console=self._console,
            spinner=spinner,
            spinner_style=spinner_style,
            speed=speed,
        )
    
    def live(
        self,
        renderable: Optional[Renderable] = None,
        *,
        refresh_per_second: float = 4,
        screen: bool = False,
    ) -> Live:
        """Create a live display."""
        return Live(
            renderable,
            console=self._console,
            refresh_per_second=refresh_per_second,
            screen=screen,
        )
    
    # Expose classes
    Console = Console
    Text = Text
    Style = Style
    Panel = Panel
    Padding = Padding
    Columns = Columns
    Table = Table
    Tree = Tree
    Syntax = Syntax
    Markdown = Markdown
    Live = Live
    Status = Status
    BoxStyle = BoxStyle
    Renderable = Renderable
    ConsoleOptions = ConsoleOptions
    Measurement = Measurement


# Create module instance
rich = RichModule()

# Convenience functions
def print(*objects: Any, **kwargs: Any) -> None:
    """Print using the rich module."""
    rich.print(*objects, **kwargs)

def log(*objects: Any, **kwargs: Any) -> None:
    """Log using the rich module."""
    rich.log(*objects, **kwargs)

def rule(title: str = "", **kwargs: Any) -> None:
    """Print a rule using the rich module."""
    rich.rule(title, **kwargs)
