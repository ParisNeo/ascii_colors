import sys
import time
import math
import shutil
from threading import Lock
from typing import Any, Dict, Iterable, Optional, TypeVar, Sized, cast
from ascii_colors.constants import ANSI
from ascii_colors.core import ASCIIColors
from ascii_colors.utils import strip_ansi

try: from wcwidth import wcswidth, wcwidth
except ImportError:
    def wcswidth(s): return len(s)
    def wcwidth(c): return 1

_T = TypeVar('_T')

class ProgressBar:
    """Customizable progress bar similar to tqdm."""
    def __init__(self, iterable=None, total=None, desc="", unit="it", ncols=None, bar_format=None, leave=True, 
                 mininterval=0.15, color=ANSI.color_green, style="", background="", bar_style="fill", **kwargs):
        self.iterable, self.desc, self.unit, self.ncols, self.leave, self.mininterval = iterable, desc, unit, ncols, leave, mininterval
        self.color, self.style, self.background, self.bar_style = color, style, background, bar_style.lower()
        self.total = total or (len(cast(Sized, iterable)) if hasattr(iterable, '__len__') else None)
        self.bar_format = bar_format or ("{l_bar} {bar} | {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{unit}]" if self.total else "{l_bar} {bar} [{elapsed}, {n_fmt} {unit}]")
        self.n, self.start_t, self.last_print_t, self._closed, self._lock = 0, time.time(), 0, False, Lock()
        self.progress_char = kwargs.get('progress_char', "─" if self.bar_style == 'line' else "█")
        self.empty_char = kwargs.get('empty_char', " " if self.bar_style == 'line' else "░")
        self._last_rendered = ""  # Store last rendered text for testing
        self._last_line_length = 0  # Track for proper clearing
        self._cursor_hidden = False
        self.file = kwargs.get('file', sys.stdout)

    def __iter__(self):
        self._iterator = iter(self.iterable)
        self.start_t = self.last_print_t = time.time()
        self._hide_cursor()
        # Small settle time for terminal state
        time.sleep(0.001)
        self._render(force=True)
        return self

    def __next__(self):
        try: 
            val = next(self._iterator)
            self.update(1)
            return val
        except StopIteration: 
            self.close()
            raise

    def __enter__(self): 
        self.start_t = self.last_print_t = time.time()
        self._hide_cursor()
        # Small settle time for terminal state
        time.sleep(0.001)
        self._render(force=True)
        return self
        
    def __exit__(self, *args): 
        self.close()

    def _hide_cursor(self):
        """Hide terminal cursor to prevent flicker."""
        if not self._cursor_hidden:
            # Enable synchronized updates (ITerm2, modern terminals)
            self.file.write("\033[?2026h")
            self.file.write("\033[?25l")
            self.file.flush()
            self._cursor_hidden = True
    
    def _show_cursor(self):
        """Show terminal cursor again."""
        if self._cursor_hidden:
            self.file.write("\033[?25h")
            # Disable synchronized updates
            self.file.write("\033[?2026l")
            self.file.flush()
            self._cursor_hidden = False

    def update(self, n=1):
        if self._closed: 
            return
        with self._lock:
            self.n += n
            current_time = time.time()
            if (current_time - self.last_print_t >= self.mininterval) or (self.total and self.n >= self.total):
                self._render()
                self.last_print_t = current_time

    def close(self):
        if self._closed: 
            return
        with self._lock:
            self._closed = True
            self._show_cursor()
            if self.leave: 
                self._render(final=True)
                # Move to new line after final render
                self.file.write("\n")
                self.file.flush()
            else: 
                # Clear the line and move to start
                clear_line = "\r" + " " * (self._last_line_length + 10) + "\r"
                self.file.write(clear_line)
                self.file.flush()

    def _render(self, final=False, force=False):
        """Render progress bar with minimal flicker."""
        elapsed = time.time() - self.start_t
        rate = self.n / elapsed if elapsed > 0 else 0
        eta = (self.total - self.n) / rate if self.total and rate > 0 else 0
        
        l_bar = f"{self.desc}: " if self.desc else ""
        bar_width = (shutil.get_terminal_size().columns or 80) - len(strip_ansi(l_bar)) - 30
        
        if self.total:
            pct = min(1.0, self.n / self.total)
            filled = int(pct * bar_width)
            bar = self.progress_char * filled + self.empty_char * (bar_width - filled)
            msg_content = f"{l_bar}{self.color}{bar}{ANSI.color_reset} {pct*100:3.0f}% | {self.n}/{self.total}"
        else:
            anim = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
            bar = anim[int(time.time() * 10) % len(anim)]
            msg_content = f"{l_bar}{self.color}{bar}{ANSI.color_reset} {self.n} {self.unit}"
        
        # Build complete output in one string: carriage return + content + padding
        plain_content = strip_ansi(msg_content)
        content_len = len(plain_content)
        
        # Calculate padding to clear previous longer lines
        padding = ""
        if content_len < self._last_line_length:
            padding = " " * (self._last_line_length - content_len)
        
        # Single atomic write: \r moves to start, content, padding clears old chars
        output = f"\r{msg_content}{padding}"
        
        self._last_rendered = msg_content
        self._last_line_length = content_len
        
        # Use print for testability, or direct write for performance
        # Write everything at once and flush once
        self.file.write(output)
        self.file.flush()
