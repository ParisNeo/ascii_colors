# -*- coding: utf-8 -*-
"""
Console class for rich text output with markup support.
"""

import os
import re
import sys
import time
import shutil
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TextIO, Iterator

from ascii_colors.constants import ANSI

# Import style-related functions
from ascii_colors.rich.style import (
    Style, Color, BoxStyle,
    RICH_COLOR_MAP, RICH_STYLE_MAP, SEMANTIC_TAG_MAP,
)

# Import text
from ascii_colors.rich.text import Text, Renderable, wcswidth

# Get builtin print to avoid conflicts
import builtins
_builtin_print = builtins.print


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
    
    def update_width(self, width: int) -> "ConsoleOptions":
        """Return new options with updated width."""
        return ConsoleOptions(
            max_width=width,
            min_width=self.min_width,
            max_height=self.max_height,
            legacy_windows=self.legacy_windows,
            ascii_only=self.ascii_only,
            size=(width, self.size[1] if self.size else 25),
        )


class Measurement:
    """Measurement of renderable dimensions."""
    
    def __init__(self, minimum: int, maximum: int):
        self.minimum = minimum
        self.maximum = maximum
    
    @classmethod
    def get(
        cls,
        console: "Console",
        options: ConsoleOptions,
        renderable: Renderable,
    ) -> "Measurement":
        """Get measurement of a renderable."""
        if hasattr(renderable, "__len__"):
            try:
                length = len(renderable)
                return cls(length, length)
            except:
                pass
        
        return cls(1, options.max_width)
    
    def normalize(self) -> "Measurement":
        """Ensure minimum <= maximum."""
        return Measurement(min(self.minimum, self.maximum), max(self.minimum, self.maximum))


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
        self._width = force_width if force_width is not None else width
        self._height = force_height if force_height is not None else height
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
        self.highlighter = highlighter
        self.safe_box = safe_box
        self.legacy_windows = legacy_windows
        self.get_environ = get_environ
        self.get_time = get_time or time.time
        self.get_terminal_size = get_terminal_size or self._default_get_terminal_size
        
        self._is_terminal = self._detect_terminal()
        self._is_jupyter = self._detect_jupyter()
        self._color_system: Optional[str] = self._detect_color_system()
    
    def _default_get_terminal_size(self) -> Tuple[int, int]:
        """Default terminal size getter."""
        try:
            size = shutil.get_terminal_size()
            return (size.columns, size.lines)
        except:
            return (80, 25)
    
    def _detect_jupyter(self) -> bool:
        """Detect if we're running in Jupyter."""
        if self.force_jupyter is not None:
            return self.force_jupyter
        try:
            get_ipython = self.get_environ("get_ipython")
            if get_ipython and callable(get_ipython):
                ipython = get_ipython()
                return ipython.__class__.__name__ == "ZMQInteractiveShell"
        except:
            pass
        return False
    
    def _detect_color_system(self) -> Optional[str]:
        """Detect the color system to use."""
        if self.no_color:
            return None
        
        if not self._is_terminal and not self._is_jupyter:
            return None
        
        colorterm = self.get_environ("COLORTERM")
        if colorterm in ("truecolor", "24bit"):
            return "truecolor"
        
        term = self.get_environ("TERM")
        if term:
            term = str(term).lower()
            if "256color" in term:
                return "256"
            if term in ("xterm", "vt100", "screen", "ansi"):
                return "standard"
        
        if self._is_terminal:
            return "standard"
        
        return None
    
    def _detect_terminal(self) -> bool:
        """Detect if we're running in a terminal."""
        if self.force_terminal is not None:
            return self.force_terminal
        if self.force_jupyter:
            return False
        try:
            return self.file.isatty()
        except:
            return False
    
    @property
    def is_terminal(self) -> bool:
        return self._is_terminal
    
    @property
    def is_jupyter(self) -> bool:
        return self._is_jupyter
    
    @property
    def color_system(self) -> Optional[str]:
        return self._color_system
    
    @property
    def width(self) -> int:
        if self._width is not None:
            return self._width
        if self.file is sys.stdout or self.file is sys.stderr:
            width, _ = self.get_terminal_size()
            return width
        return 80
    
    @property
    def height(self) -> int:
        if self._height is not None:
            return self._height
        _, height = self.get_terminal_size()
        return height
    
    @property
    def size(self) -> Tuple[int, int]:
        return (self.width, self.height)
    
    def _process_emoji(self, text: str) -> str:
        if not self.emoji:
            return re.sub(r":[\w_]+:", "", text)
        return text
    
    def _expand_tabs(self, text: str) -> str:
        return text.expandtabs(self.tab_size)
    
    def _parse_rich_markup_tag(self, tag_content: str) -> str:
        """Parse a rich markup tag and return ANSI codes."""
        if tag_content.startswith("/"):
            return ANSI.color_reset
        
        content = tag_content.lower().strip()
        parts = content.split()
        codes = []
        
        i = 0
        while i < len(parts):
            part = parts[i]
            
            if part == "on" and i + 1 < len(parts):
                bg_color = parts[i + 1]
                bg_key = f"bg_{bg_color}"
                if bg_key in RICH_COLOR_MAP:
                    codes.append(RICH_COLOR_MAP[bg_key])
                elif bg_color in RICH_COLOR_MAP and RICH_COLOR_MAP[bg_color].startswith("\u001b[38"):
                    fg_code = RICH_COLOR_MAP[bg_color]
                    bg_code = fg_code.replace("[38", "[48")
                    codes.append(bg_code)
                i += 2
                continue
            
            if part in SEMANTIC_TAG_MAP:
                codes.append(SEMANTIC_TAG_MAP[part])
            elif part in RICH_COLOR_MAP:
                codes.append(RICH_COLOR_MAP[part])
            elif part in RICH_STYLE_MAP:
                codes.append(RICH_STYLE_MAP[part])
            elif part.startswith("#") and len(part) in (4, 7):
                try:
                    hex_val = part[1:]
                    if len(hex_val) == 3:
                        r = int(hex_val[0] * 2, 16)
                        g = int(hex_val[1] * 2, 16)
                        b = int(hex_val[2] * 2, 16)
                    else:
                        r = int(hex_val[0:2], 16)
                        g = int(hex_val[2:4], 16)
                        b = int(hex_val[4:6], 16)
                    codes.append(f"\033[38;2;{r};{g};{b}m")
                except ValueError:
                    pass
            
            i += 1
        
        return "".join(codes) if codes else ""
    
    def _apply_markup(self, text: str) -> str:
        """Apply rich markup like [bold]text[/bold] or [magenta]text[/magenta]."""
        if self.no_color:
            return re.sub(r"\[/?[^\]]+\]", "", text)
        
        if not text or "[" not in text:
            return text
        
        # Process emoji first
        text = self._process_emoji(text)
        
        # Simple case: no closing tags, return as-is
        if "[/" not in text:
            # Check if there are any opening tags
            if not re.search(r'\[[\w\s#]+\]', text):
                return text
        
        result = []
        i = 0
        style_stack = []
        
        while i < len(text):
            if text[i] == '[':
                # Look for closing bracket
                end = i + 1
                while end < len(text) and text[end] != ']':
                    end += 1
                
                if end < len(text) and text[end] == ']':
                    tag_content = text[i+1:end]
                    
                    if tag_content.startswith('/'):
                        # Closing tag - use full normalized content for matching
                        full_closing_tag = tag_content[1:].lower().strip()
                        # Normalize: collapse multiple spaces, strip
                        normalized_close = ' '.join(full_closing_tag.split())
                        
                        # Find matching opening tag in stack
                        new_stack = []
                        found = False
                        for j, (stack_tag, ansi) in enumerate(style_stack):
                            # Compare normalized versions
                            if not found and stack_tag == normalized_close:
                                found = True
                            else:
                                new_stack.append((stack_tag, ansi))
                        
                        if found:
                            style_stack = new_stack
                            result.append(ANSI.color_reset)
                            # Re-apply remaining styles
                            for _, ansi in style_stack:
                                result.append(ansi)
                        
                        i = end + 1
                        continue
                    else:
                        # Opening tag - store full normalized tag for matching
                        full_opening_tag = tag_content.lower().strip()
                        # Normalize: collapse multiple spaces, strip
                        normalized_open = ' '.join(full_opening_tag.split())
                        
                        ansi_codes = self._parse_rich_markup_tag(tag_content)
                        if ansi_codes:
                            style_stack.append((normalized_open, ansi_codes))
                            result.append(ansi_codes)
                        
                        i = end + 1
                        continue
            
            result.append(text[i])
            i += 1
        
        # Ensure we reset at the end if we opened any styles
        if style_stack:
            result.append(ANSI.color_reset)
        
        return ''.join(result)
    
    def render(
        self,
        renderable: Union[Renderable, str],
        options: Optional[ConsoleOptions] = None,
    ) -> List[str]:
        """Render a renderable to lines."""
        if options is None:
            options = ConsoleOptions(max_width=self.width)
        
        if isinstance(renderable, str):
            markup_rendered = self._apply_markup(renderable)
            return markup_rendered.split("\n")
        
        if isinstance(renderable, Text):
            wrapped = renderable.wrap(options.max_width)
            return [line.render(options.max_width) for line in wrapped]
        
        if hasattr(renderable, "__rich_console__"):
            lines = []
            try:
                for segment in renderable.__rich_console__(self, options):
                    if isinstance(segment, str):
                        lines.append(segment)
                    elif isinstance(segment, Text):
                        sub_lines = segment.wrap(options.max_width)
                        lines.extend([line.render(options.max_width) for line in sub_lines])
                    elif hasattr(segment, "__rich_console__"):
                        sub_lines = self.render(segment, options)
                        lines.extend(sub_lines)
                    else:
                        lines.append(str(segment))
            except Exception as e:
                lines.append(f"[Rendering error: {e}]")
            
            return lines
        
        return str(renderable).split("\n")
    
    def print(
        self,
        *objects,
        sep=" ",
        end="\n",
        style=None,
        justify=None,
        overflow=None,
        no_wrap=None,
        emoji=None,
        markup=None,
        highlight=None,
        width=None,
        crop=True,
        soft_wrap=False,
    ):
        """Print objects to the console."""
        use_emoji = emoji if emoji is not None else self.emoji
        use_markup = markup if markup is not None else self.markup
        use_highlight = highlight if highlight is not None else self.highlight
        
        for i, obj in enumerate(objects):
            if i > 0:
                _builtin_print(sep, end="", file=self.file)
            
            obj_type = type(obj).__name__
            
            if obj_type in ("Panel", "Table", "Columns", "Tree", "Syntax", "Markdown"):
                max_width = width if width is not None else self.width
                options = ConsoleOptions(max_width=max_width)
                try:
                    lines = self.render(obj, options)
                    for line in lines:
                        _builtin_print(line, file=self.file)
                        if self.record:
                            self._record_buffer.append(line + "\n")
                except Exception as e:
                    _builtin_print(f"[Error rendering {obj_type}: {e}]", file=self.file)
                    
            elif isinstance(obj, str):
                output = obj
                
                if use_emoji:
                    output = self._process_emoji(output)
                if use_markup:
                    output = self._apply_markup(output)
                if use_highlight and self.highlighter:
                    output = self.highlighter.highlight(output)
                
                output = self._expand_tabs(output)
                
                max_width = width if width is not None else self.width
                if not no_wrap and max_width:
                    output = self._wrap_text(output, max_width, overflow, soft_wrap, crop)
                if justify and max_width:
                    output = self._justify_text(output, max_width, justify)
                if style:
                    style_obj = style if isinstance(style, Style) else Style.parse(style)
                    output = f"{style_obj}{output}{ANSI.color_reset}"
                
                _builtin_print(output, end="", file=self.file)
                if self.record:
                    self._record_buffer.append(output)
                    
            elif isinstance(obj, Text):
                output = obj.plain if isinstance(obj.plain, str) else str(obj.plain)
                
                if use_emoji:
                    output = self._process_emoji(output)
                if use_markup:
                    output = self._apply_markup(output)
                if use_highlight and self.highlighter:
                    output = self.highlighter.highlight(output)
                
                output = self._expand_tabs(output)
                
                max_width = width if width is not None else self.width
                if not no_wrap and max_width:
                    output = self._wrap_text(output, max_width, overflow, soft_wrap, crop)
                if justify and max_width:
                    output = self._justify_text(output, max_width, justify)
                if style:
                    style_obj = style if isinstance(style, Style) else Style.parse(style)
                    output = f"{style_obj}{output}{ANSI.color_reset}"
                
                _builtin_print(output, end="", file=self.file)
                if self.record:
                    self._record_buffer.append(output)
                    
            elif hasattr(obj, "__rich_console__"):
                max_width = width if width is not None else self.width
                options = ConsoleOptions(max_width=max_width)
                try:
                    lines = self.render(obj, options)
                    for line in lines:
                        _builtin_print(line, file=self.file)
                        if self.record:
                            self._record_buffer.append(line + "\n")
                except Exception as e:
                    _builtin_print(f"[Error: {e}] {str(obj)}", file=self.file)
                    
            else:
                output = str(obj)
                _builtin_print(output, end="", file=self.file)
                if self.record:
                    self._record_buffer.append(output)
        
        _builtin_print(end, end="", file=self.file)
        if self.record:
            self._record_buffer.append(end)
    
    def log(
        self,
        *objects,
        sep=" ",
        end="\n",
        style=None,
        justify=None,
        emoji=None,
        markup=None,
        highlight=None,
    ):
        """Log to console with timestamp."""
        import datetime
        
        use_emoji = emoji if emoji is not None else self.emoji
        use_markup = markup if markup is not None else self.markup
        use_highlight = highlight if highlight is not None else self.highlight
        
        output_parts = []
        
        if self.log_time:
            current_time = datetime.datetime.now()
            time_str = current_time.strftime(self.log_time_format.strip("[]"))
            time_style = Style(dim=True)
            output_parts.append(f"{time_style}[{time_str}]{ANSI.color_reset}")
        
        if self.log_path:
            import inspect
            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller = frame.f_back
                filename = caller.f_code.co_filename
                lineno = caller.f_lineno
                # Get just the filename, not full path
                display_file = os.path.basename(filename)
                path_style = Style(dim=True, color="cyan")
                output_parts.append(f"{path_style}{display_file}:{lineno}{ANSI.color_reset}")
        
        for obj in objects:
            if isinstance(obj, str):
                output_parts.append(obj)
            else:
                output_parts.append(str(obj))
        
        log_line = " ".join(output_parts)
        
        if use_emoji:
            log_line = self._process_emoji(log_line)
        if use_markup:
            log_line = self._apply_markup(log_line)
        if use_highlight and self.highlighter:
            log_line = self.highlighter.highlight(log_line)
        if justify:
            log_line = self._justify_text(log_line, self.width, justify)
        if style:
            style_obj = style if isinstance(style, Style) else Style.parse(style)
            log_line = f"{style_obj}{log_line}{ANSI.color_reset}"
        
        _builtin_print(log_line, end=end, file=self.file)
        
        if self.record:
            self._record_buffer.append(log_line + end)
    
    def _wrap_text(self, text, max_width, overflow=None, soft_wrap=False, crop=True):
        """Wrap text to fit within max_width."""
        lines = text.split("\n")
        wrapped_lines = []
        
        for line in lines:
            if len(line) <= max_width:
                wrapped_lines.append(line)
                continue
            
            if overflow == "ellipsis" and crop:
                wrapped_lines.append(line[:max_width-1] + "…")
            elif overflow == "ignore":
                wrapped_lines.append(line)
            else:
                if soft_wrap:
                    for i in range(0, len(line), max_width):
                        wrapped_lines.append(line[i:i+max_width])
                else:
                    import textwrap
                    wrapped_lines.extend(textwrap.wrap(line, width=max_width))
        
        return "\n".join(wrapped_lines)
    
    def _justify_text(self, text, width, justify):
        """Justify text within the given width."""
        lines = text.split("\n")
        justified_lines = []
        
        for line in lines:
            plain_line = re.sub(r"\033\[[0-9;]+m", "", line)
            line_width = wcswidth(plain_line)
            
            if line_width >= width:
                justified_lines.append(line)
                continue
            
            padding = width - line_width
            
            if justify == "left":
                justified_lines.append(line)
            elif justify == "right":
                justified_lines.append(" " * padding + line)
            elif justify == "center":
                left_pad = padding // 2
                right_pad = padding - left_pad
                justified_lines.append(" " * left_pad + line + " " * right_pad)
            elif justify == "full":
                words = line.split()
                if len(words) <= 1:
                    justified_lines.append(line)
                else:
                    gaps = len(words) - 1
                    space_per_gap = padding // gaps
                    extra_spaces = padding % gaps
                    
                    result = []
                    for i, word in enumerate(words[:-1]):
                        result.append(word)
                        result.append(" " * (1 + space_per_gap + (1 if i < extra_spaces else 0)))
                    result.append(words[-1])
                    justified_lines.append("".join(result))
            else:
                justified_lines.append(line)
        
        return "\n".join(justified_lines)
    
    def rule(
        self,
        title="",
        characters="─",
        style=None,
        align="center",
    ):
        """Print a horizontal rule."""
        width = self.width
        
        # Parse the line style if provided
        style_ansi = ""
        if style:
            style_obj = style if isinstance(style, Style) else Style.parse(style)
            style_ansi = str(style_obj)
        
        if title:
            # Process title markup first
            title_clean = self._apply_markup(title)
            # Strip ANSI for width calculation
            import re
            title_plain = re.sub(r"\033\[[0-9;]+m", "", title_clean)
            title_width = wcswidth(title_plain)
            char_width = width - title_width - 2
            
            if align == "left":
                left = 0
                right = char_width
            elif align == "right":
                left = char_width
                right = 0
            else:
                left = char_width // 2
                right = char_width - left
            
            # Build the line: apply style to rule characters, but re-apply after title
            left_part = characters * left
            right_part = characters * right
            
            # Apply style to the rule parts if specified
            if style_ansi:
                left_part = f"{style_ansi}{left_part}{ANSI.color_reset}"
                # The title already has its own styling from _apply_markup
                # After title's closing tag resets, we need to re-apply the line style
                right_part = f"{style_ansi}{right_part}{ANSI.color_reset}"
                line = f"{left_part} {title_clean} {right_part}"
            else:
                line = f"{left_part} {title_clean} {right_part}"
        else:
            line = characters * width
            if style_ansi:
                line = f"{style_ansi}{line}{ANSI.color_reset}"
        
        _builtin_print(line, file=self.file)
    
    def input(
        self,
        prompt="",
        *,
        markup=True,
        emoji=True,
        password=False,
        stream=None,
    ):
        """Get input from user with styled prompt."""
        if markup:
            prompt = self._apply_markup(prompt)
        
        if stream is None:
            stream = self.file
        
        _builtin_print(prompt, end="", file=stream)
        
        if password:
            import getpass
            return getpass.getpass("")
        else:
            return input()
    
    def export_text(self, clear=True, styles=False) -> str:
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
    
    def clear(self, home=False):
        """Clear the console."""
        if home:
            _builtin_print("\033[H", end="", file=self.file)
        else:
            _builtin_print("\033[2J\033[H", end="", file=self.file)
    
    def save_screen(self):
        """Save current screen."""
        _builtin_print("\033[?47h", end="", file=self.file)
    
    def restore_screen(self):
        """Restore saved screen."""
        _builtin_print("\033[?47l", end="", file=self.file)
