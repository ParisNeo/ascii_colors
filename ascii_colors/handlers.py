import sys
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Optional, Tuple, Type, Union, IO, TextIO
from ascii_colors.constants import LogLevel, DEBUG
from ascii_colors.formatters import Formatter

class Handler(ABC):
    """Abstract base class for all log handlers."""
    def __init__(self, level: Union[LogLevel, int] = DEBUG, formatter: Optional[Formatter] = None):
        self.level = LogLevel(level)
        self.formatter = formatter
        self._lock, self.closed = Lock(), False

    def setLevel(self, level: Union[LogLevel, int]) -> None:
        with self._lock: self.level = LogLevel(level)

    def getLevel(self) -> int: return self.level.value

    def setFormatter(self, formatter: Formatter) -> None:
        with self._lock: self.formatter = formatter

    def handle(self, level: LogLevel, message: str, timestamp: datetime, exc_info: Optional[Tuple], logger_name: str = 'root', **kwargs: Any) -> None:
        if self.closed or level < self.level: return
        fmt = self.formatter or Formatter()
        formatted = fmt.format(level, message, timestamp, exc_info, logger_name=logger_name, **kwargs)
        with self._lock:
            if not self.closed:
                try: self.emit(level, formatted)
                except Exception: self.handle_error("Error during emit")

    @abstractmethod
    def emit(self, level: LogLevel, formatted_message: str) -> None: pass

    def close(self) -> None:
        with self._lock: self.closed = True

    def handle_error(self, message: str):
        print(f"--- Logging Error in {type(self).__name__} ---\n{message}\nTraceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

class ConsoleHandler(Handler):
    """Handles logging records by writing them to a stream (typically console)."""
    def __init__(self, level: Union[LogLevel, int] = DEBUG, formatter: Optional[Formatter] = None, stream: Optional[IO[str]] = None):
        super().__init__(level, formatter)
        self.stream = stream or sys.stderr

    def emit(self, level: LogLevel, formatted_message: str) -> None:
        from ascii_colors.core import ASCIIColors
        color = ASCIIColors._level_colors.get(level, ASCIIColors.color_white)
        output = f"{color}{formatted_message}{ASCIIColors.color_reset}\n"
        if self.stream and not getattr(self.stream, 'closed', False):
            try:
                self.stream.write(output)
                self.stream.flush()
            except Exception: self.handle_error("Write failed")

    def close(self) -> None:
        if self.closed: return
        with self._lock:
            if self.stream and self.stream not in (sys.stdout, sys.stderr):
                try: self.stream.flush(); self.stream.close()
                except Exception: pass
        super().close()

StreamHandler = ConsoleHandler

class FileHandler(Handler):
    """Handles logging records by writing them to a file."""
    def __init__(self, filename: Union[str, Path], mode: str = 'a', encoding: Optional[str] = "utf-8", delay: bool = False, level: Union[LogLevel, int] = DEBUG, formatter: Optional[Formatter] = None):
        super().__init__(level, formatter)
        if mode not in ('a', 'w'): raise ValueError("Mode must be 'a' or 'w'")
        self.filename, self.mode, self.encoding, self.delay, self._stream = Path(filename).resolve(), mode, encoding, delay, None
        if not self.delay: self._open_file()

    def _open_file(self) -> None:
        if self.closed or (self._stream and not getattr(self._stream, 'closed', True)): return
        try:
            self.filename.parent.mkdir(parents=True, exist_ok=True)
            self._stream = open(self.filename, self.mode, encoding=self.encoding)
        except Exception as e: self.handle_error(f"Open failed: {e}"); self._stream = None

    def emit(self, level: LogLevel, formatted_message: str) -> None:
        if self.closed: return
        if self.delay and (self._stream is None or getattr(self._stream, 'closed', True)): self._open_file()
        if self._stream and not getattr(self._stream, 'closed', True):
            try: self._stream.write(formatted_message + "\n"); self._stream.flush()
            except Exception as e: self.handle_error(f"Write failed: {e}")

    def close(self) -> None:
        if self.closed: return
        with self._lock:
            if self._stream:
                try: self._stream.flush(); self._stream.close()
                except Exception: pass
                self._stream = None
        super().close()

    def flush(self) -> None:
        with self._lock:
            if not self.closed and self._stream: self._stream.flush()

class RotatingFileHandler(FileHandler):
    """Handles logging to a file, rotating it when it reaches a certain size."""
    def __init__(self, filename: Union[str, Path], mode: str = 'a', maxBytes: int = 0, backupCount: int = 0, encoding: Optional[str] = "utf-8", delay: bool = False, level: Union[LogLevel, int] = DEBUG, formatter: Optional[Formatter] = None):
        super().__init__(filename, mode, encoding, delay, level, formatter)
        self.maxBytes, self.backupCount = maxBytes, backupCount

    def emit(self, level: LogLevel, formatted_message: str) -> None:
        if self.closed: return
        try:
            size = len((formatted_message + "\n").encode(self.encoding or 'utf-8'))
            if self.maxBytes > 0 and self.filename.exists() and (self.filename.stat().st_size + size) >= self.maxBytes:
                self.do_rollover()
        except Exception: pass
        super().emit(level, formatted_message)

    def do_rollover(self) -> None:
        if self.closed: return
        if self._stream: self._stream.close(); self._stream = None
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, -1, -1):
                s = self.filename if i == 0 else self.filename.with_name(f"{self.filename.name}.{i}")
                d = self.filename.with_name(f"{self.filename.name}.{i+1}")
                if s.exists():
                    if d.exists(): d.unlink()
                    s.rename(d)
        elif self.filename.exists(): self.filename.unlink()
        self._open_file()

class handlers:
    RotatingFileHandler = RotatingFileHandler
    FileHandler = FileHandler
    StreamHandler = StreamHandler
