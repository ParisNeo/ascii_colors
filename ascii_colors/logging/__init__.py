# -*- coding: utf-8 -*-
"""
Logging compatibility layer for ascii_colors.
Provides standard logging module compatibility.
"""

import sys
import io
import warnings
from typing import Any, Dict, List, Optional, Union, Callable, Tuple, Iterator

from ascii_colors.constants import LogLevel, DEBUG, INFO, WARNING, ERROR, CRITICAL, NOTSET
from ascii_colors.core import ASCIIColors
from ascii_colors.handlers import Handler, ConsoleHandler, FileHandler, RotatingFileHandler, StreamHandler
from ascii_colors.formatters import Formatter, JSONFormatter


# Cache for logger adapters
_logger_cache: Dict[str, "_AsciiLoggerAdapter"] = {}


class _AsciiLoggerAdapter:
    """Adapter that provides standard logging.Logger interface using ASCIIColors backend."""
    
    def __init__(self, name: str):
        self.name = name
        self.level = NOTSET
        self.handlers: List[Handler] = []
        self.disabled = False
        self.propagate = True
    
    def _get_effective_level(self) -> int:
        """Get the effective level for this logger."""
        if self.level != NOTSET:
            return self.level
        # Return global level from ASCIIColors
        return ASCIIColors._global_level.value
    
    def isEnabledFor(self, level: int) -> bool:
        """
        Check if this logger is enabled for the specified level.
        
        This is a standard logging.Logger method that checks whether
        a message at the given level would actually be logged.
        
        Args:
            level: The log level to check (e.g., DEBUG, INFO, WARNING)
            
        Returns:
            True if the logger is enabled for the given level, False otherwise
        """
        # Check if logger is disabled
        if self.disabled:
            return False
        
        # Get effective level and compare
        effective_level = self._get_effective_level()
        return level >= effective_level
    
    def setLevel(self, level: Union[int, LogLevel]) -> None:
        """Set the logging level."""
        if isinstance(level, LogLevel):
            self.level = level.value
        else:
            self.level = level
    
    def getEffectiveLevel(self) -> int:
        """Get the effective level for this logger."""
        return self._get_effective_level()
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log a debug message."""
        if self.isEnabledFor(DEBUG):
            self._log(LogLevel.DEBUG, msg, args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """Log an info message."""
        if self.isEnabledFor(INFO):
            self._log(LogLevel.INFO, msg, args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log a warning message."""
        if self.isEnabledFor(WARNING):
            self._log(LogLevel.WARNING, msg, args, **kwargs)
    
    def warn(self, msg: str, *args, **kwargs) -> None:
        """Deprecated alias for warning."""
        self.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """Log an error message."""
        if self.isEnabledFor(ERROR):
            self._log(LogLevel.ERROR, msg, args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log a critical message."""
        if self.isEnabledFor(CRITICAL):
            self._log(LogLevel.CRITICAL, msg, args, **kwargs)
    
    def fatal(self, msg: str, *args, **kwargs) -> None:
        """Log a fatal message (alias for critical)."""
        self.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs) -> None:
        """Log an exception message with traceback."""
        kwargs['exc_info'] = True
        self.error(msg, *args, **kwargs)
    
    def log(self, level: int, msg: str, *args, **kwargs) -> None:
        """Log a message at the specified level."""
        if self.isEnabledFor(level):
            log_level = LogLevel(level) if isinstance(level, int) else level
            self._log(log_level, msg, args, **kwargs)
    
    def _log(self, level: LogLevel, msg: str, args: Tuple, **kwargs) -> None:
        """Internal logging method."""
        # Format message with args if provided
        if args:
            try:
                msg = msg % args
            except (TypeError, ValueError):
                pass
        
        # Get exception info if requested
        exc_info = kwargs.get('exc_info', False)
        
        # Call ASCIIColors._log with logger name
        ASCIIColors._log(
            level=level,
            message=msg,
            args=(),
            exc_info=exc_info,
            logger_name=self.name,
            **{k: v for k, v in kwargs.items() if k not in ('exc_info', 'stack_info', 'extra')}
        )
    
    def addHandler(self, hdlr: Handler) -> None:
        """Add a handler to this logger."""
        ASCIIColors.add_handler(hdlr)
        self.handlers.append(hdlr)
    
    def removeHandler(self, hdlr: Handler) -> None:
        """Remove a handler from this logger."""
        ASCIIColors.remove_handler(hdlr)
        if hdlr in self.handlers:
            self.handlers.remove(hdlr)
    
    def hasHandlers(self) -> bool:
        """Check if this logger has any handlers."""
        return len(self.handlers) > 0 or len(ASCIIColors._handlers) > 0
    
    def filter(self, record: Any) -> bool:
        """Filter method (stub for compatibility)."""
        return True
    
    def handle(self, record: Any) -> None:
        """Handle a log record."""
        pass
    
    def findCaller(self, stack_info: bool = False, stacklevel: int = 1) -> Tuple:
        """Find the caller (stub for compatibility)."""
        import inspect
        frame = inspect.currentframe()
        if frame:
            frame = frame.f_back
            if frame and frame.f_back:
                frame = frame.f_back
                co = frame.f_code
                return (co.co_filename, frame.f_lineno, co.co_name, None)
        return ("(unknown file)", 0, "(unknown function)", None)
    
    def getChild(self, suffix: str) -> "_AsciiLoggerAdapter":
        """Get a child logger."""
        if self.root:
            return getLogger(f"{self.name}.{suffix}")
        return getLogger(suffix)
    
    @property
    def root(self) -> bool:
        """Check if this is the root logger."""
        return self.name == "root" or not self.name
    
    def __repr__(self) -> str:
        return f"<_AsciiLoggerAdapter({self.name!r})>"


def getLogger(name: Optional[str] = None) -> _AsciiLoggerAdapter:
    """
    Get a logger with the specified name.
    
    This function mirrors logging.getLogger() for drop-in compatibility.
    """
    name = name or "root"
    
    if name not in _logger_cache:
        _logger_cache[name] = _AsciiLoggerAdapter(name)
    
    return _logger_cache[name]


def basicConfig(
    *,
    filename: Optional[str] = None,
    filemode: str = 'a',
    format: Optional[str] = None,
    datefmt: Optional[str] = None,
    style: str = '%',
    level: Optional[int] = None,
    stream: Optional[io.TextIOWrapper] = None,
    handlers: Optional[List[Handler]] = None,
    force: bool = False,
) -> None:
    """
    Configure basic logging.
    
    Mirrors logging.basicConfig() for drop-in compatibility.
    """
    if ASCIIColors._basicConfig_called and not force:
        return
    
    if force:
        ASCIIColors.clear_handlers()
        _logger_cache.clear()
    
    # Set level if provided
    if level is not None:
        ASCIIColors.set_log_level(level)
    
    # Create formatter
    fmt = format or "%(levelname)s:%(name)s:%(message)s"
    formatter = Formatter(fmt=fmt, datefmt=datefmt, style=style)
    
    # Handle explicit handlers list
    if handlers:
        for hdlr in handlers:
            if hdlr.formatter is None:
                hdlr.setFormatter(formatter)
            ASCIIColors.add_handler(hdlr)
    else:
        # Create default console handler
        if filename:
            hdlr = FileHandler(filename, mode=filemode)
        else:
            hdlr = ConsoleHandler(stream=stream or sys.stderr)
        
        hdlr.setFormatter(formatter)
        ASCIIColors.add_handler(hdlr)
    
    ASCIIColors._basicConfig_called = True


def shutdown() -> None:
    """Shutdown the logging system."""
    for handler in ASCIIColors._handlers[:]:
        try:
            handler.close()
        except Exception:
            pass
    ASCIIColors.clear_handlers()
    _logger_cache.clear()


# Convenience function for exception logging
def trace_exception(ex: Exception, enhanced: bool = True, max_width: Optional[int] = None) -> None:
    """Log an exception with traceback."""
    from ascii_colors.utils import get_trace_exception
    formatted = get_trace_exception(ex, enhanced=enhanced, max_width=max_width)
    ASCIIColors._log(LogLevel.ERROR, formatted, (), exc_info=None, logger_name='trace_exception')
