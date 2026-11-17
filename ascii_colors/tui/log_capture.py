# -*- coding: utf-8 -*-
"""Bounded, non-printing capture of ASCIIColors log records."""

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ascii_colors.constants import DEBUG, LogLevel
from ascii_colors.core import ASCIIColors
from ascii_colors.handlers import Handler
from ascii_colors.utils import strip_ansi


@dataclass(frozen=True)
class CapturedLog:
    """One plain-text log entry retained for the terminal log viewer."""

    timestamp: datetime
    level: str
    logger: str
    message: str

    def format(self) -> str:
        return (
            f"{self.timestamp:%H:%M:%S}  {self.level:<8} "
            f"{self.logger}: {self.message}"
        )


class TerminalLogBuffer:
    """Thread-safe bounded storage shared by logging and the TUI."""

    def __init__(self, max_entries: int = 4000):
        if max_entries < 1:
            raise ValueError("max_entries must be positive")
        self._entries = deque(maxlen=max_entries)
        self._lock = threading.RLock()

    def append(
        self,
        message: str,
        level: str = "INFO",
        logger: str = "ASCIIColors",
        timestamp: Optional[datetime] = None,
    ) -> None:
        plain = strip_ansi(str(message)).replace("\r\n", "\n").replace("\r", "\n")
        stamp = timestamp or datetime.now()
        with self._lock:
            for line in plain.split("\n"):
                self._entries.append(CapturedLog(stamp, level.upper(), logger, line))

    def entries(
        self,
        query: str = "",
        *,
        level: str = "",
        limit: Optional[int] = None,
    ) -> List[CapturedLog]:
        needle = query.casefold()
        wanted_level = level.upper()
        with self._lock:
            result = list(self._entries)
        if wanted_level:
            result = [entry for entry in result if entry.level == wanted_level]
        if needle:
            result = [
                entry
                for entry in result
                if needle in entry.message.casefold()
                or needle in entry.logger.casefold()
            ]
        if limit is not None:
            result = result[-max(0, limit):]
        return result

    def lines(self, query: str = "", *, level: str = "") -> List[str]:
        return [entry.format() for entry in self.entries(query, level=level)]

    def text(self, query: str = "", *, level: str = "") -> str:
        return "\n".join(self.lines(query, level=level))

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


class MemoryLogHandler(Handler):
    """Capture formatted ASCIIColors records without touching the terminal."""

    def __init__(self, buffer: TerminalLogBuffer, level=DEBUG):
        super().__init__(level=level)
        self.buffer = buffer

    def emit(self, level: LogLevel, formatted_message: str) -> None:
        self.buffer.append(formatted_message, level.name)


def attach_log_capture(
    buffer: Optional[TerminalLogBuffer] = None,
    *,
    max_entries: int = 4000,
) -> TerminalLogBuffer:
    """Install one process-local capture handler and return its buffer."""
    with ASCIIColors._handler_lock:
        for handler in ASCIIColors._handlers:
            if isinstance(handler, MemoryLogHandler) and not handler.closed:
                return handler.buffer
    result = buffer or TerminalLogBuffer(max_entries=max_entries)
    ASCIIColors.add_handler(MemoryLogHandler(result))
    return result