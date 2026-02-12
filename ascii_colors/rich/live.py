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
    
    def __enter__(self) -> "Live":
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
    
    def start(self) -> None:
        """Start live display."""
        if self.screen:
            self.console.save_screen()
        
        self._render()
        
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
            
            if clear and self._rendered_content:
                lines_to_clear = len(self._rendered_content)
                for _ in range(lines_to_clear):
                    _builtin_print("\033[F\033[K", end="", file=self.console.file)
            
            lines = self.console.render(renderable)
            self._rendered_content = lines
            
            for line in lines:
                _builtin_print(line, file=self.console.file)
            
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
        self._live: Optional[Live] = None
        self._frame = 0
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def __enter__(self) -> "Status":
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
