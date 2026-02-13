# -*- coding: utf-8 -*-
"""
Live display components: Live and Status for rich compatibility.
"""

import time
import threading
from typing import Callable, Iterator, List, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ascii_colors.rich.console import Console, ConsoleOptions

from ascii_colors.constants import ANSI
from ascii_colors.rich.style import Style
from ascii_colors.rich.text import Text, Renderable
from ascii_colors.rich.console import Console

import builtins
_builtin_print = builtins.print


class Live:
    """Live updating display."""
    
    def __init__(
        self,
        renderable: Optional[Renderable] = None,
        console: Optional["Console"] = None,
        screen: bool = False,
        auto_refresh: bool = True,
        refresh_per_second: float = 4,
        vertical_overflow: str = "ellipsis",
        get_renderable: Optional[Callable[[], Renderable]] = None,
    ):
        from ascii_colors.rich.console import Console
        
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
        self._cursor_hidden: bool = False
    
    def __enter__(self) -> "Live":
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()

    def start(self) -> None:
        """Start the live display."""
        if self.screen:
            self.console.save_screen()
        
        # Hide cursor once at start to prevent flicker
        self._hide_cursor()
        
        # Do initial render
        self._render()
        
        # Start auto-refresh thread if enabled
        if self.auto_refresh:
            self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
            self._refresh_thread.start()
    
    def _hide_cursor(self) -> None:
        """Hide terminal cursor."""
        if not self._cursor_hidden:
            _builtin_print("\033[?25l", end="", flush=True, file=self.console.file)
            self._cursor_hidden = True
    
    def _show_cursor(self) -> None:
        """Show terminal cursor."""
        if self._cursor_hidden:
            _builtin_print("\033[?25h", end="", flush=True, file=self.console.file)
            self._cursor_hidden = False
    
    def stop(self) -> None:
        """Stop the live display."""
        self._stop_event.set()
        
        if self._refresh_thread:
            self._refresh_thread.join(timeout=1)
        
        # Show cursor again
        self._show_cursor()
        
        if self.screen:
            self.console.restore_screen()
        
        # Move to new line after stopping
        _builtin_print("", file=self.console.file)
    
    def _refresh_loop(self) -> None:
        """Background refresh loop."""
        while not self._stop_event.is_set():
            time.sleep(1.0 / self.refresh_per_second)
            if not self._stop_event.is_set():
                self.refresh()
    
    def _render(self, clear: bool = True) -> None:
        """Render current content with minimal flicker."""
        with self._lock:
            renderable = self.renderable
            if self.get_renderable:
                renderable = self.get_renderable()
            
            if renderable is None:
                return
            
            # Process string renderables through markup
            if isinstance(renderable, str):
                renderable = Text(renderable)
            
            # Ensure Text objects get markup processed
            if isinstance(renderable, Text):
                # Apply markup to the text content if it contains tags
                if '[' in str(renderable.plain) and ']' in str(renderable.plain):
                    processed = self.console._apply_markup(str(renderable.plain))
                    # Create new Text with processed content, preserving styles
                    renderable = Text(processed, style=renderable.style, justify=renderable.justify)
            
            # Render to lines
            lines = self.console.render(renderable)
            
            # Clear previous content by moving up and clearing lines (not full screen)
            if clear and self._rendered_content:
                lines_to_clear = len(self._rendered_content)
                # Move cursor up to the first line of previous content
                if lines_to_clear > 1:
                    _builtin_print(f"\033[{lines_to_clear - 1}A", end="", file=self.console.file)
                # Move to beginning of line and clear each line
                for _ in range(lines_to_clear):
                    _builtin_print("\r\033[K", end="", file=self.console.file)
                    if _ < lines_to_clear - 1:
                        _builtin_print("\033[B", end="", file=self.console.file)
                # Move back up to the first line position
                if lines_to_clear > 1:
                    _builtin_print(f"\033[{lines_to_clear - 1}A", end="", file=self.console.file)
            
            # Store current content length for next clear
            self._rendered_content = lines
            
            # Print new content
            for i, line in enumerate(lines):
                if i > 0:
                    _builtin_print("\n", end="", file=self.console.file)
                _builtin_print(line, end="", file=self.console.file)
            
            _builtin_print("", end="", flush=True, file=self.console.file)
    
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
        self._frame = 0
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._last_line_length = 0
        self._cursor_hidden = False
    
    def __enter__(self) -> "Status":
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
    
    def _render_frame(self) -> None:
        """Render a single spinner frame with in-place update."""
        with self._lock:
            char = self.spinner_chars[self._frame % len(self.spinner_chars)]
            self._frame += 1
            
            style = self.spinner_style
            style_str = str(style) if style else ""
            
            # Build status line (spinner char + status text)
            line = f"{style_str}{char}{ANSI.color_reset} {self.status}"
            
            # Calculate visible length (strip ANSI for width calculation)
            import re
            plain_line = re.sub(r"\033\[[0-9;]+m", "", line)
            
            # Move to start of line, clear to end, print new content
            # Use carriage return for smooth in-place update
            if self._last_line_length > len(plain_line):
                # Previous line was longer, need extra clearing
                padding = " " * (self._last_line_length - len(plain_line))
                _builtin_print(f"\r{line}{padding}\r{line}", end="", flush=True, file=self.console.file)
            else:
                _builtin_print(f"\r{line}", end="", flush=True, file=self.console.file)
            
            self._last_line_length = len(plain_line)
    
    def _animate(self) -> None:
        """Animation loop."""
        # Hide cursor at start
        if not self._cursor_hidden:
            _builtin_print("\033[?25l", end="", file=self.console.file)
            self._cursor_hidden = True
        
        try:
            while not self._stop_event.is_set():
                self._render_frame()
                time.sleep(1.0 / (self.speed * 10))
        finally:
            # Cursor will be shown in stop()
            pass
    
    def start(self) -> None:
        """Start the status display."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        # Small delay to let first frame render
        time.sleep(0.01)
    
    def stop(self) -> None:
        """Stop the status display."""
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=2)
        
        # Show cursor and clean up line
        if self._cursor_hidden:
            _builtin_print("\033[?25h", end="", file=self.console.file)
            self._cursor_hidden = False
        
        # Clear the line and move to new line
        _builtin_print(f"\r{' ' * (self._last_line_length + 10)}\r", end="", file=self.console.file)
        _builtin_print("", file=self.console.file)
    
    def update(self, status: str, *, spinner: Optional[str] = None, speed: Optional[float] = None) -> None:
        """Update status text."""
        with self._lock:
            self.status = status
            if spinner:
                self.spinner_chars = self.SPINNERS.get(spinner, self.spinner_chars)
            if speed:
                self.speed = speed
