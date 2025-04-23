# -*- coding: utf-8 -*-
"""
ascii_colors: A Python library for rich terminal output with advanced logging features.
Includes a logging compatibility layer.

Provides:
- ANSI color and style constants.
- Direct printing methods with colors/styles (e.g., `ASCIIColors.red()`, `ASCIIColors.bold()`).
- A flexible logging system with Handlers and Formatters (Console, File, RotatingFile, JSON).
- Compatibility functions (`getLogger`, `basicConfig`) mimicking the standard `logging` module.
- Utility functions like `execute_with_animation`, `highlight`, `trace_exception`.

Author: Saifeddine ALOUI (ParisNeo)
License: Apache License 2.0
"""

import inspect
import json
import logging as std_logging # Alias to avoid name conflicts
import os
import shutil
import string
import sys
import threading
import time
import traceback
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from threading import Lock
from typing import (Any, Callable, Dict, List, Optional, TextIO, Tuple, Type,
                    Union, cast, Text, TypeVar, ContextManager, IO)

# --- Log Level Enum & Constants ---

class LogLevel(IntEnum):
    """Internal log levels for filtering messages, matching standard logging values."""
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0

# Provide standard logging level constants mapped to our enum values.
CRITICAL: int = LogLevel.CRITICAL.value
ERROR: int = LogLevel.ERROR.value
WARNING: int = LogLevel.WARNING.value
INFO: int = LogLevel.INFO.value
DEBUG: int = LogLevel.DEBUG.value
NOTSET: int = LogLevel.NOTSET.value

# --- Type Aliases ---

ExcInfoType = Optional[Union[bool, BaseException, Tuple[Optional[Type[BaseException]], Optional[BaseException], Any]]]
LevelType = Union[LogLevel, int]
StreamType = Union[TextIO, IO[str]] # Type hint for streams

# --- Utility Functions ---

def get_trace_exception(ex: BaseException) -> str:
    """Formats an exception and its traceback into a string."""
    traceback_lines: List[str] = traceback.format_exception(type(ex), ex, ex.__traceback__)
    return "".join(traceback_lines)

# --- Formatter Classes ---

class Formatter:
    """
    Base class for formatting log records into strings.
    Supports standard logging format styles ('%' and '{').
    """
    # Mapping for standard logging format specifiers
    _style_mapping: Dict[str, Dict[str, Callable[[Dict[str, Any]], Any]]] = {
        # '%' style mappings (executed during string formatting)
        '%': {
            'asctime': lambda r: r['timestamp'].strftime(r.get('datefmt', "%Y-%m-%d %H:%M:%S,%f")[:-3]),
            'created': lambda r: r['timestamp'].timestamp(),
            'filename': lambda r: r['filename'], # Use calculated filename
            'funcName': lambda r: r['funcName'],
            'levelname': lambda r: r['levelname'],
            'levelno': lambda r: r['levelno'],
            'lineno': lambda r: r['lineno'],
            'message': lambda r: r['message'],
            'module': lambda r: Path(r['pathname']).stem if r['pathname'] != 'N/A' else 'N/A',
            'msecs': lambda r: int(r['timestamp'].microsecond / 1000),
            'name': lambda r: r.get('name', 'root'),
            'pathname': lambda r: r['pathname'],
            'process': lambda r: os.getpid(),
            'processName': lambda r: threading.current_thread().name,
            'relativeCreated': lambda r: (r['timestamp'] - r.get('_initial_timestamp', r['timestamp'])).total_seconds() * 1000,
            'thread': lambda r: threading.get_ident(),
            'threadName': lambda r: threading.current_thread().name,
        },
        # '{' style mappings (can be used to pre-populate record for str.format)
        '{': {
            # Note: These are less critical for { style as str.format accesses dict keys directly.
            # Provided for potential consistency or complex format needs.
            'asctime': lambda r: r['timestamp'].strftime(r.get('datefmt', "%Y-%m-%d %H:%M:%S,%f")[:-3]),
            # ... other fields can be added similarly if needed ...
        }
    }
    _initial_timestamp: datetime = datetime.now() # For relativeCreated

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = '%',
        include_source: bool = False,
        **kwargs: Any # Allow extra kwargs for compatibility
    ):
        """
        Initializes the formatter.

        Args:
            fmt: Format string. If None, uses a default based on style.
            datefmt: Date format string. Defaults to logging standard including ms.
            style: '%' or '{'. Determines format string syntax.
            include_source: If True, attempts to include file/line/func context (adds overhead).
        """
        self.style: str = style if style in ('%', '{') else '%'
        self.fmt: Optional[str] = fmt # Store None if passed
        self.datefmt: str = datefmt if datefmt is not None else "%Y-%m-%d %H:%M:%S,%f"
        self.include_source: bool = include_source
        self._kwargs: Dict[str, Any] = kwargs

    def format(
        self,
        level: LogLevel,
        message: str,
        timestamp: datetime,
        exc_info: Optional[Tuple[Optional[Type[BaseException]], Optional[BaseException], Any]],
        logger_name: str = 'root',
        **kwargs: Any,
    ) -> str:
        """Formats the log record data into a final string."""
        level_name: str = level.name
        level_no: int = level.value
        filename: str = "N/A"; lineno: int = 0; funcName: str = "N/A"; pathname: str = "N/A"

        if self.include_source:
            try:
                frame = inspect.currentframe(); depth = 0
                while frame and depth < 20: # Limit stack walk depth
                    fname = frame.f_code.co_filename; func = frame.f_code.co_name
                    is_internal_file = Path(fname).parent.name == "ascii_colors" or Path(fname).name == "__init__.py"
                    is_internal_func = func in ('_log','format','handle','emit','debug','info','warning','error','critical','exception','log','trace_exception','basicConfig')
                    if not (is_internal_file and is_internal_func):
                        pathname = str(Path(fname).resolve()); lineno = frame.f_lineno; funcName = func; filename = Path(pathname).name
                        break
                    frame = frame.f_back; depth += 1
                del frame
            except Exception: pass # Ignore inspection errors

        # Prepare the record dictionary with all standard logging names
        log_record: Dict[str, Any] = {
            **ASCIIColors.get_thread_context(), **kwargs, # Context first, then explicit kwargs
            "levelno": level_no, "levelname": level_name,
            "message": message, # The actual message string
            "timestamp": timestamp, # datetime object for calculations
            "name": logger_name,
            "datefmt": self.datefmt, # Pass along date format
            "filename": filename, "pathname": pathname, "lineno": lineno, "funcName": funcName,
            "_initial_timestamp": self._initial_timestamp,
            # Add calculated fields useful for formatting
            "asctime": timestamp.strftime(self.datefmt[:-3] if self.datefmt.endswith(',%f') else self.datefmt),
            "msecs": int(timestamp.microsecond / 1000),
            "process": os.getpid(), "thread": threading.get_ident(),
            "threadName": threading.current_thread().name,
        }
        # Aliases for original ascii_colors names if needed (less common now)
        log_record['level_name'] = level_name; log_record['level'] = level_no
        log_record['file_name'] = filename; log_record['line_no'] = lineno; log_record['func_name'] = funcName

        # Determine format string and style to use
        current_fmt = self.fmt
        current_style = self.style
        if current_fmt is None: # Use default format if none provided
            current_fmt = "%(levelname)s:%(name)s:%(message)s"
            current_style = '%'

        formatted_message: str = ""
        try:
            if current_style == '%':
                formatted_message = self._format_percent_style(log_record, current_fmt)
            elif current_style == '{':
                # For {} style, just pass the comprehensive log_record
                formatted_message = current_fmt.format(**log_record)
            else:
                formatted_message = f"[UNSUPPORTED_STYLE:{current_style}] {current_fmt}"
        except KeyError as e:
             formatted_message = f"[FORMAT_ERROR: Missing key {e} for '{current_style}' style. Fmt: '{current_fmt}'. Keys: {list(log_record.keys())}]"
        except Exception as e:
             formatted_message = f"[FORMAT_ERROR: {type(e).__name__} '{e}' using style '{current_style}' with fmt '{current_fmt}'. Keys: {list(log_record.keys())}]"

        if exc_info: formatted_message += "\n" + self.format_exception(exc_info)
        return formatted_message

    def _format_percent_style(self, record: Dict[str, Any], fmt: str) -> str:
        """Internal helper for %-style formatting."""
        class RecordAccessor:
            def __init__(self, rec: Dict[str, Any]): self._rec = rec
            def __getitem__(self, key: str) -> Any:
                # Prioritize standard % mapping calculation
                if key in Formatter._style_mapping['%']:
                    try: return Formatter._style_mapping['%'][key](self._rec)
                    except Exception as e_lambda: return f"<FmtErr:{key}:{e_lambda}>"
                # Fallback to direct access in the record
                try: return self._rec[key]
                except KeyError: raise KeyError(f"Format key '{key}' not found")
        try:
            return fmt % RecordAccessor(record)
        except (TypeError, KeyError, ValueError) as e:
            return f"[FORMAT_SUBSTITUTION_ERROR: {type(e).__name__} '{e}' for key '{getattr(e, 'args', ['N/A'])[0]}'. Fmt:'{fmt}'. Record Keys: {list(record.keys())}]"
        except Exception as e:
             return f"[FORMAT_UNKNOWN_ERROR: {e}] Fmt:'{fmt}'"

    def format_exception(self, exc_info: Tuple[Optional[Type[BaseException]], Optional[BaseException], Any]) -> str:
        """Formats exception information."""
        if exc_info and exc_info[1]: return get_trace_exception(exc_info[1])
        return ""

class JSONFormatter(Formatter):
    """Formats log records as JSON strings."""
    def __init__(
        self,
        fmt: Optional[Dict[str, str]] = None,
        datefmt: Optional[str] = None,
        style: str = '%',
        json_ensure_ascii: bool = False,
        json_indent: Optional[int] = None,
        json_separators: Optional[Tuple[str, str]] = None,
        json_sort_keys: bool = False,
        include_fields: Optional[List[str]] = None,
        include_source: bool = False,
        **kwargs: Any
    ):
        """Initializes the JSON formatter."""
        super().__init__(style=style, include_source=include_source) # Pass style, include_source
        self.fmt_dict: Optional[Dict[str, str]] = fmt
        self.include_fields: Optional[List[str]] = include_fields
        self.datefmt_str: Optional[str] = datefmt

        if datefmt is None or datefmt.lower() == "iso":
            self._format_date = lambda dt: dt.isoformat()
        else:
            self._format_date = lambda dt: dt.strftime(self.datefmt_str) # type: ignore

        self.json_ensure_ascii = json_ensure_ascii; self.json_indent = json_indent
        self.json_separators = json_separators; self.json_sort_keys = json_sort_keys

    def format(
        self,
        level: LogLevel, message: str, timestamp: datetime,
        exc_info: Optional[Tuple[Optional[Type[BaseException]], Optional[BaseException], Any]],
        logger_name: str = 'root', **kwargs: Any
    ) -> str:
        """Formats the log record into a JSON string."""
        level_name: str = level.name; level_no: int = level.value
        dt_str: str = self._format_date(timestamp)
        filename: str = "N/A"; lineno: int = 0; funcName: str = "N/A"; pathname: str = "N/A"

        if self.include_source:
             try: # Simplified source detection
                 frame = inspect.currentframe(); depth = 0
                 while frame and depth < 20:
                     fname = frame.f_code.co_filename; func = frame.f_code.co_name
                     is_internal_file = Path(fname).parent.name == "ascii_colors" or Path(fname).name == "__init__.py"
                     is_internal_func = func in ('_log','format','handle','emit','debug','info','warning','error','critical','exception','log','trace_exception','basicConfig')
                     if not (is_internal_file and is_internal_func):
                         pathname = str(Path(fname).resolve()); lineno = frame.f_lineno; funcName = func; filename = Path(pathname).name
                         break
                     frame = frame.f_back; depth += 1
                 del frame
             except Exception: pass

        # Build the full record dictionary first
        log_record: Dict[str, Any] = {
            "levelno": level_no, "levelname": level_name,
            "asctime": dt_str, # Use pre-formatted date string
            "timestamp": timestamp.timestamp(), # Raw timestamp
            "message": message, "name": logger_name,
            "filename": filename, "pathname": pathname, "lineno": lineno, "funcName": funcName,
            "process": os.getpid(), "processName": threading.current_thread().name,
            "thread": threading.get_ident(), "threadName": threading.current_thread().name,
            **ASCIIColors.get_thread_context(), **kwargs
        }

        if exc_info:
            try:
                log_record["exc_info"] = self.format_exception(exc_info)
                log_record["exc_type"] = exc_info[0].__name__ if exc_info[0] else None
                log_record["exc_value"] = str(exc_info[1]) if exc_info[1] else None
            except Exception as e: log_record["exception_formatting_error"] = str(e)

        # Select and format fields for the final JSON object
        final_json_object: Dict[str, Any] = {}
        if self.include_fields is not None:
            final_json_object = {k: v for k, v in log_record.items() if k in self.include_fields}
        elif self.fmt_dict is not None:
            # Use a temporary formatter to evaluate fmt_dict values
            # This seems overly complex and potentially slow, consider simplifying if possible
            temp_formatter = Formatter(style=self.style, datefmt=self.datefmt_str, include_source=self.include_source)
            temp_formatter._initial_timestamp = self._initial_timestamp
            for key, fmt_string in self.fmt_dict.items():
                temp_formatter.fmt = fmt_string
                try:
                     # Pass the full record, let the temp formatter handle it
                     formatted_value = temp_formatter.format(level, message, timestamp, None, logger_name=logger_name, **log_record)
                     final_json_object[key] = formatted_value
                except Exception as e: final_json_object[key] = f"<FmtErr:{key}:{e}>"
        else: # Default fields
            default_fields = ["timestamp", "levelname", "name", "message", "filename", "lineno", "funcName"]
            final_json_object = {k: v for k, v in log_record.items() if k in default_fields}
            final_json_object.update(ASCIIColors.get_thread_context()) # Add context/kwargs back
            final_json_object.update(kwargs)
            if "exc_info" in log_record: final_json_object["exc_info"] = log_record["exc_info"]

        try: # Serialize the final object
            return json.dumps(final_json_object, default=str, ensure_ascii=self.json_ensure_ascii, indent=self.json_indent, separators=self.json_separators, sort_keys=self.json_sort_keys)
        except Exception as e: return json.dumps({"json_format_error": str(e), "record_keys": list(final_json_object.keys())})

# --- Handler Classes ---

class Handler(ABC):
    """Abstract base class for log handlers."""
    level: LogLevel
    formatter: Optional[Formatter]
    _lock: Lock
    closed: bool

    def __init__(
        self,
        level: LevelType = DEBUG,
        formatter: Optional[Formatter] = None,
    ):
        """Initializes the handler."""
        self.level = LogLevel(level)
        self.formatter = formatter # Store None if passed
        self._lock = Lock()
        self.closed = False

    def setLevel(self, level: LevelType) -> None:
        """Sets the minimum level for this handler."""
        with self._lock: self.level = LogLevel(level)

    def getLevel(self) -> int:
        """Gets the minimum level for this handler."""
        return self.level.value

    def setFormatter(self, formatter: Formatter) -> None:
        """Sets the formatter for this handler."""
        with self._lock: self.formatter = formatter

    def getFormatter(self) -> Optional[Formatter]:
        """Gets the formatter for this handler."""
        return self.formatter

    def set_formatter(self, formatter: Formatter) -> None:
        """Sets the formatter (ascii_colors original name)."""
        self.setFormatter(formatter)

    def handle(
        self,
        level: LogLevel, message: str, timestamp: datetime,
        exc_info: Optional[Tuple[Optional[Type[BaseException]], Optional[BaseException], Any]],
        logger_name: str = 'root', **kwargs: Any
    ) -> None:
        """Filters record by level, formats it, and emits it."""
        if self.closed: return
        if level >= self.level:
            fmt_to_use = self.formatter # Use assigned formatter if available
            if fmt_to_use is None:
                 # Create temporary default formatter if none assigned
                 fmt_to_use = Formatter() # Uses internal defaults (fmt=None -> % style)
            formatted_message = fmt_to_use.format(level, message, timestamp, exc_info, logger_name=logger_name, **kwargs)
            self.emit(level, formatted_message)

    @abstractmethod
    def emit(self, level: LogLevel, formatted_message: str) -> None:
        """Sends the formatted log record to the destination."""
        raise NotImplementedError

    def close(self) -> None:
        """Tidy up resources."""
        self.closed = True

class ConsoleHandler(Handler):
    """Handles logging to console streams (stderr/stdout)."""
    stream: StreamType

    def __init__(
        self,
        level: LevelType = DEBUG,
        formatter: Optional[Formatter] = None,
        stream: Optional[StreamType] = None,
    ):
        """Initializes the console handler."""
        super().__init__(level, formatter)
        self.stream = stream if stream is not None else sys.stderr

    def emit(self, level: LogLevel, formatted_message: str) -> None:
        """Prints the formatted message to the stream with colors."""
        if self.closed: return
        color = ASCIIColors._level_colors.get(level, ASCIIColors.color_white)
        output = f"{color}{formatted_message}{ASCIIColors.color_reset}\n"
        # Check stream validity before writing
        if self.stream and hasattr(self.stream, 'write') and not getattr(self.stream, 'closed', False):
            with self._lock:
                try:
                    self.stream.write(output)
                    self.stream.flush()
                except Exception as e:
                     print(f"{ASCIIColors.color_bright_red}PANIC: ConsoleHandler failed: {e}{ASCIIColors.color_reset}", file=sys.stderr, flush=True)

    def close(self) -> None:
        """Closes the stream if it's not sys.stdout or sys.stderr."""
        if self.closed: return
        with self._lock:
            try:
                if self.stream and self.stream not in (sys.stdout, sys.stderr):
                    if hasattr(self.stream, 'flush'): self.stream.flush()
                    if hasattr(self.stream, 'close'): self.stream.close()
            except Exception as e:
                 print(f"{ASCIIColors.color_bright_red}PANIC: Error closing console stream: {e}{ASCIIColors.color_reset}", file=sys.stderr, flush=True)
        super().close()

StreamHandler = ConsoleHandler # Alias

class FileHandler(Handler):
    """Handles logging to a file."""
    filename: Path
    mode: str
    encoding: Optional[str]
    delay: bool
    _stream: Optional[IO[str]]

    def __init__(
        self,
        filename: Union[str, Path],
        mode: str = 'a',
        encoding: Optional[str] = "utf-8",
        delay: bool = False,
        level: LevelType = DEBUG,
        formatter: Optional[Formatter] = None,
    ):
        """Initializes the file handler."""
        super().__init__(level, formatter) # Formatter can be None
        self.filename = Path(filename).resolve()
        self.mode = mode; self.encoding = encoding; self.delay = delay
        self._stream = None
        if not self.delay: self._open_file()

    def _open_file(self) -> None:
        """Opens the file stream if not already open."""
        if self.closed: return
        if self._stream is None or getattr(self._stream, 'closed', True):
            try:
                self.filename.parent.mkdir(parents=True, exist_ok=True)
                self._stream = open(self.filename, self.mode, encoding=self.encoding)
            except Exception as e:
                print(f"{ASCIIColors.color_bright_red}PANIC: FileHandler failed open {self.filename}: {e}{ASCIIColors.color_reset}", file=sys.stderr, flush=True)
                self._stream = None

    def emit(self, level: LogLevel, formatted_message: str) -> None:
        """Writes the formatted message to the log file."""
        if self.closed: return
        with self._lock:
            if self.delay and (self._stream is None or getattr(self._stream, 'closed', True)):
                self._open_file()
            if self._stream and not getattr(self._stream, 'closed', True):
                try:
                    self._stream.write(formatted_message + "\n")
                    self._stream.flush()
                except Exception as e:
                    print(f"{ASCIIColors.color_bright_red}PANIC: Write failed for {self.filename}: {e}{ASCIIColors.color_reset}", file=sys.stderr, flush=True)
                    self.close()

    def close(self) -> None:
        """Closes the stream used by the handler."""
        if self.closed: return
        with self._lock:
            if self._stream and not getattr(self._stream, 'closed', True):
                try:
                    self._stream.flush(); self._stream.close()
                except Exception as e:
                     print(f"{ASCIIColors.color_bright_red}PANIC: Error closing {self.filename}: {e}{ASCIIColors.color_reset}", file=sys.stderr, flush=True)
            self._stream = None
        super().close()

    def flush(self) -> None:
        """Flushes the stream buffer."""
        if self.closed: return
        with self._lock:
            if self._stream and not getattr(self._stream, 'closed', True) and hasattr(self._stream, 'flush'):
                try: self._stream.flush()
                except Exception as e: print(f"{ASCIIColors.color_bright_red}PANIC: Flush failed for {self.filename}: {e}{ASCIIColors.color_reset}", file=sys.stderr, flush=True)

class RotatingFileHandler(FileHandler):
    """Handles logging to a file, rotating it when it reaches a certain size."""
    maxBytes: int
    backupCount: int

    def __init__(
        self, filename: Union[str, Path], mode: str = 'a', maxBytes: int = 0, backupCount: int = 0,
        encoding: Optional[str] = "utf-8", delay: bool = False, level: LevelType = DEBUG, formatter: Optional[Formatter] = None
    ):
        """Initializes the rotating file handler."""
        super().__init__(filename, mode=mode, encoding=encoding, delay=delay, level=level, formatter=formatter)
        self.maxBytes = maxBytes; self.backupCount = backupCount

    def emit(self, level: LogLevel, formatted_message: str) -> None:
        """Writes to the file THEN potentially rotates it."""
        if self.closed: return
        super().emit(level, formatted_message) # Write first
        try: # Check rotation after writing
            if self.should_rotate(): self.do_rollover()
        except Exception as e:
             print(f"{ASCIIColors.color_bright_red}PANIC: Rotation check/rollover failed for {self.filename}: {e}{ASCIIColors.color_reset}", file=sys.stderr, flush=True)

    def should_rotate(self) -> bool:
        """Checks if the log file needs rotation based on size."""
        if self.closed or self.maxBytes <= 0: return False
        # Stream might be closed by do_rollover, check file on disk
        try:
            if self.filename.exists(): return self.filename.stat().st_size >= self.maxBytes
        except OSError: return False
        return False

    def do_rollover(self) -> None:
        """Performs the log file rotation."""
        if self.closed: return
        with self._lock:
            # --- Close stream BEFORE stat/FS ops ---
            stream_closed_by_us = False
            if self._stream and not getattr(self._stream, 'closed', True):
                try: self._stream.flush(); self._stream.close(); stream_closed_by_us = True
                except Exception: pass
            self._stream = None

            try: # --- Check condition AFTER closing ---
                needs_rotation = False
                if self.maxBytes > 0 and self.filename.exists() and self.filename.stat().st_size >= self.maxBytes:
                    needs_rotation = True
                if not needs_rotation:
                    if stream_closed_by_us: self._open_file() # Reopen if we closed it unnecessarily
                    return

                # --- Perform FS Operations ---
                if self.backupCount > 0:
                    for i in range(self.backupCount - 1, -1, -1): # Iterate down from N-1 to 0
                        sfn = self.filename if i == 0 else self.filename.with_name(f"{self.filename.name}.{i}")
                        dfn = self.filename.with_name(f"{self.filename.name}.{i + 1}")
                        if sfn.exists():
                            if dfn.exists(): dfn.unlink() # Remove existing destination
                            sfn.rename(dfn)
                else: # No backups, just delete current log
                    if self.filename.exists(): self.filename.unlink()

            except Exception as e:
                 print(f"{ASCIIColors.color_bright_red}PANIC: Error during FS ops in rollover for {self.filename}: {e}{ASCIIColors.color_reset}", file=sys.stderr, flush=True)

            # --- Re-open primary log file ---
            self._open_file() # Creates if needed

class handlers:
    """Provides access to handler classes like `logging.handlers`."""
    RotatingFileHandler = RotatingFileHandler
    FileHandler = FileHandler
    StreamHandler = StreamHandler

# --- Main ASCIIColors Class ---
_T = TypeVar('_T')
class ASCIIColors:
    """Provides static methods for colored terminal output and manages global logging state."""
    # --- ANSI Reset ---
    color_reset: str = "\u001b[0m"

    # --- Styles ---
    style_bold: str = "\u001b[1m"
    style_dim: str = "\u001b[2m"
    style_italic: str = "\u001b[3m"
    style_underline: str = "\u001b[4m"
    style_blink: str = "\u001b[5m"
    style_blink_fast: str = "\u001b[6m" # Not widely supported
    style_reverse: str = "\u001b[7m"
    style_hidden: str = "\u001b[8m"
    style_strikethrough: str = "\u001b[9m"

    # --- Foreground Colors (Regular) ---
    color_black: str = "\u001b[30m"; color_red: str = "\u001b[31m"
    color_green: str = "\u001b[32m"; color_yellow: str = "\u001b[33m"
    color_blue: str = "\u001b[34m"; color_magenta: str = "\u001b[35m"
    color_cyan: str = "\u001b[36m"; color_white: str = "\u001b[37m"
    # Common alias / 256-color approximation
    color_orange: str = "\u001b[38;5;208m" # Often used orange

    # --- Foreground Colors (Bright) ---
    color_bright_black: str = "\u001b[90m"; color_bright_red: str = "\u001b[91m"
    color_bright_green: str = "\u001b[92m"; color_bright_yellow: str = "\u001b[93m"
    color_bright_blue: str = "\u001b[94m"; color_bright_magenta: str = "\u001b[95m"
    color_bright_cyan: str = "\u001b[96m"; color_bright_white: str = "\u001b[97m"
    # Alternate bright codes sometimes used (often same as bold+regular)
    # color_bright_black_alt: str = "\u001b[30;1m"; # ... etc

    # --- Background Colors (Regular) ---
    bg_black: str = "\u001b[40m"; bg_red: str = "\u001b[41m"
    bg_green: str = "\u001b[42m"; bg_yellow: str = "\u001b[43m"
    bg_blue: str = "\u001b[44m"; bg_magenta: str = "\u001b[45m"
    bg_cyan: str = "\u001b[46m"; bg_white: str = "\u001b[47m"
    bg_orange: str = "\u001b[48;5;208m" # 256-color approx

    # --- Background Colors (Bright) ---
    bg_bright_black: str = "\u001b[100m"; bg_bright_red: str = "\u001b[101m"
    bg_bright_green: str = "\u001b[102m"; bg_bright_yellow: str = "\u001b[103m"
    bg_bright_blue: str = "\u001b[104m"; bg_bright_magenta: str = "\u001b[105m"
    bg_bright_cyan: str = "\u001b[106m"; bg_bright_white: str = "\u001b[107m"

    # --- Global Logging State ---
    _handlers: List[Handler] = []
    _global_level: LogLevel = LogLevel.WARNING
    _handler_lock: Lock = Lock()
    _basicConfig_called: bool = False
    _context: threading.local = threading.local()

    # Default colors for log levels in ConsoleHandler
    _level_colors: Dict[LogLevel, str] = {
        LogLevel.DEBUG: style_dim + color_white, # Dim white for debug
        LogLevel.INFO: color_bright_blue,
        LogLevel.WARNING: color_bright_yellow, # Use bright yellow consistently
        LogLevel.ERROR: color_bright_red,
        LogLevel.CRITICAL: style_bold + color_bright_red,
    }

    # --- Logging Configuration Methods ---
    @classmethod
    def set_log_level(cls, level: LevelType) -> None:
        """Sets the *global* minimum log level."""
        cls._global_level = LogLevel(level)
    @classmethod
    def add_handler(cls, handler: Handler) -> None:
        """Adds a log handler to the global list."""
        with cls._handler_lock:
            if handler not in cls._handlers: cls._handlers.append(handler)
    @classmethod
    def remove_handler(cls, handler: Handler) -> None:
        """Removes a specific handler instance."""
        with cls._handler_lock:
            try: cls._handlers.remove(handler)
            except ValueError: pass
    @classmethod
    def clear_handlers(cls) -> None:
        """Removes all configured handlers."""
        # Does not close handlers, requires explicit close or basicConfig(force=True)
        with cls._handler_lock: cls._handlers.clear()
    @classmethod
    def set_log_file(cls, path: Union[str, Path], level: LevelType = DEBUG, formatter: Optional[Formatter] = None) -> None:
        """[Backward Compatibility] Adds a FileHandler."""
        cls.add_handler(FileHandler(path, level=level, formatter=formatter))
    @classmethod
    def set_template(cls, level: LogLevel, template: str) -> None:
        """DEPRECATED: Use setFormatter on specific handlers."""
        cls.warning("ASCIIColors.set_template is DEPRECATED.")

    # --- Context Management ---
    @classmethod
    def set_context(cls, **kwargs: Any) -> None:
        """Sets key-value pairs in the current thread's logging context."""
        for key, value in kwargs.items(): setattr(cls._context, key, value)
    @classmethod
    def clear_context(cls, *args: str) -> None:
        """Clears keys (or all) from the thread's logging context."""
        context_vars = vars(cls._context)
        keys_to_clear = args if args else [k for k in context_vars if not k.startswith("_")]
        for key in keys_to_clear:
             if hasattr(cls._context, key):
                 try: delattr(cls._context, key)
                 except AttributeError: pass # Might have been deleted by another thread/clear
    @classmethod
    @contextmanager
    def context(cls, **kwargs: Any) -> ContextManager[None]:
        """Context manager to temporarily add thread-local context."""
        previous_values: Dict[str, Any] = {}; added_keys: set[str] = set()
        try:
            for key, value in kwargs.items():
                if hasattr(cls._context, key): previous_values[key] = getattr(cls._context, key)
                else: added_keys.add(key)
                setattr(cls._context, key, value)
            yield
        finally: # Restore previous state carefully
            for key, value in kwargs.items():
                if key in added_keys:
                    if hasattr(cls._context, key): # Check if still present
                         try: delattr(cls._context, key)
                         except AttributeError: pass
                elif key in previous_values:
                     setattr(cls._context, key, previous_values[key])
                # Else: was not present before, wasn't added by us -> do nothing
    @classmethod
    def get_thread_context(cls) -> Dict[str, Any]:
        """Returns a dictionary of the current thread's logging context."""
        return {k: v for k, v in vars(cls._context).items() if not k.startswith("_")}

    # --- Core Logging Method (Internal) ---
    @classmethod
    def _log(
        cls, level: LogLevel, message: str, args: tuple = (),
        exc_info: ExcInfoType = None, logger_name: str = 'ASCIIColors', **kwargs: Any
    ) -> None:
        """Internal method to format, filter, and dispatch a log record."""
        with cls._handler_lock: # Check for handlers only once under lock
            if not cls._handlers and not cls._basicConfig_called:
                 # Auto-add default handler IF NONE EXIST and basicConfig never called
                 default_handler = ConsoleHandler(level=cls._global_level) # Respect global level
                 # No formatter set here, handle() will use default
                 cls._handlers.append(default_handler)

        if level < cls._global_level: return # Global level filter

        timestamp: datetime = datetime.now()
        final_message: str = message
        if args: # Handle % formatting
            try: final_message = message % args
            except TypeError: final_message = f"{message} {args}"

        final_exc_info: Optional[Tuple[Optional[Type[BaseException]], Optional[BaseException], Any]] = None
        processed_exc_info: Optional[Tuple[Type[BaseException], BaseException, Any]] = None
        if exc_info: # Process exception info
            if isinstance(exc_info, BaseException): processed_exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            elif isinstance(exc_info, tuple) and len(exc_info) == 3: processed_exc_info = cast(Tuple[Type[BaseException], BaseException, Any], exc_info)
            elif exc_info is True: processed_exc_info = cast(Tuple[Type[BaseException], BaseException, Any], sys.exc_info())
            if processed_exc_info and processed_exc_info[0] is not None: final_exc_info = processed_exc_info

        # --- Dispatch to Handlers ---
        # Iterate over a copy of the handlers list for thread safety
        current_handlers: List[Handler]
        with cls._handler_lock: current_handlers = cls._handlers[:]

        for handler in current_handlers:
            try: # Protect against handler errors
                handler.handle(level, final_message, timestamp, final_exc_info, logger_name=logger_name, **kwargs)
            except Exception as e:
                cls.print(f"PANIC: Handler {type(handler).__name__} failed: {e}\n{get_trace_exception(e)}", color=cls.color_bright_red, file=sys.stderr, flush=True)

    # --- Semantic Logging Methods ---
    @classmethod
    def debug(cls, message: str, *args: Any, **kwargs: Any) -> None: cls._log(LogLevel.DEBUG, message, args, **kwargs)
    @classmethod
    def info(cls, message: str, *args: Any, **kwargs: Any) -> None: cls._log(LogLevel.INFO, message, args, **kwargs)
    @classmethod
    def warning(cls, message: str, *args: Any, **kwargs: Any) -> None: cls._log(LogLevel.WARNING, message, args, **kwargs)
    @classmethod
    def error(cls, message: str, *args: Any, exc_info: ExcInfoType = None, **kwargs: Any) -> None: cls._log(LogLevel.ERROR, message, args, exc_info=exc_info, **kwargs)
    @classmethod
    def critical(cls, message: str, *args: Any, **kwargs: Any) -> None: cls._log(LogLevel.CRITICAL, message, args, **kwargs)

    # --- Direct Console Print Methods (Bypass Logging) ---
    @staticmethod
    def print(text: str, color: str = color_white, style: str = "", end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Prints directly to console with color/style, bypassing logging."""
        print(f"{style}{color}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    # --- Direct Print - Status ---
    @staticmethod
    def success(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_green, "", end, flush, file)
    @staticmethod
    def fail(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_red, "", end, flush, file)

    # --- Direct Print - Foreground Colors ---
    @staticmethod
    def black(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_black, "", end, flush, file)
    @staticmethod
    def red(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_red, "", end, flush, file)
    @staticmethod
    def green(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_green, "", end, flush, file)
    @staticmethod
    def yellow(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_yellow, "", end, flush, file)
    @staticmethod
    def blue(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_blue, "", end, flush, file)
    @staticmethod
    def magenta(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_magenta, "", end, flush, file)
    @staticmethod
    def cyan(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_cyan, "", end, flush, file)
    @staticmethod
    def white(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_white, "", end, flush, file)
    @staticmethod
    def orange(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_orange, "", end, flush, file)
    @staticmethod
    def bright_black(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_bright_black, "", end, flush, file)
    @staticmethod
    def bright_red(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_bright_red, "", end, flush, file)
    @staticmethod
    def bright_green(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_bright_green, "", end, flush, file)
    @staticmethod
    def bright_yellow(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_bright_yellow, "", end, flush, file)
    @staticmethod
    def bright_blue(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_bright_blue, "", end, flush, file)
    @staticmethod
    def bright_magenta(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_bright_magenta, "", end, flush, file)
    @staticmethod
    def bright_cyan(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_bright_cyan, "", end, flush, file)
    @staticmethod
    def bright_white(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, ASCIIColors.color_bright_white, "", end, flush, file)

    # --- Direct Print - Background Colors ---
    @staticmethod
    def print_with_bg(text: str, color: str = color_white, background: str = "", style: str = "", end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Prints text with specified background color."""
        ASCIIColors.print(text, color, f"{style}{background}", end, flush, file) # Apply background within style arg

    @staticmethod
    def bg_black(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_black, "", end, flush, file)
    @staticmethod
    def bg_red(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_red, "", end, flush, file)
    @staticmethod
    def bg_green(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_green, "", end, flush, file)
    @staticmethod
    def bg_yellow(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_yellow, "", end, flush, file) # Default black text
    @staticmethod
    def bg_blue(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_blue, "", end, flush, file)
    @staticmethod
    def bg_magenta(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_magenta, "", end, flush, file)
    @staticmethod
    def bg_cyan(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_cyan, "", end, flush, file)
    @staticmethod
    def bg_white(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_white, "", end, flush, file) # Default black text
    @staticmethod
    def bg_orange(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_orange, "", end, flush, file)
    @staticmethod
    def bg_bright_black(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_bright_black, "", end, flush, file)
    @staticmethod
    def bg_bright_red(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_bright_red, "", end, flush, file)
    @staticmethod
    def bg_bright_green(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_bright_green, "", end, flush, file)
    @staticmethod
    def bg_bright_yellow(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_bright_yellow, "", end, flush, file)
    @staticmethod
    def bg_bright_blue(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_bright_blue, "", end, flush, file)
    @staticmethod
    def bg_bright_magenta(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_bright_magenta, "", end, flush, file)
    @staticmethod
    def bg_bright_cyan(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_bright_cyan, "", end, flush, file)
    @staticmethod
    def bg_bright_white(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print_with_bg(text, color, ASCIIColors.bg_bright_white, "", end, flush, file)

    # --- Direct Print - Styles ---
    @staticmethod
    def bold(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, color, ASCIIColors.style_bold, end, flush, file)
    @staticmethod
    def dim(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, color, ASCIIColors.style_dim, end, flush, file)
    @staticmethod
    def italic(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, color, ASCIIColors.style_italic, end, flush, file)
    @staticmethod
    def underline(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, color, ASCIIColors.style_underline, end, flush, file)
    @staticmethod
    def blink(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, color, ASCIIColors.style_blink, end, flush, file)
    @staticmethod
    def reverse(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, color, ASCIIColors.style_reverse, end, flush, file)
    @staticmethod
    def hidden(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, color, ASCIIColors.style_hidden, end, flush, file)
    @staticmethod
    def strikethrough(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None: ASCIIColors.print(text, color, ASCIIColors.style_strikethrough, end, flush, file)

    # --- Utility & Direct Console Manipulation Methods ---
    @staticmethod
    def multicolor(texts: List[str], colors: List[str], end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Prints multiple text segments with corresponding colors directly."""
        for text, color in zip(texts, colors): print(f"{color}{text}", end="", flush=True, file=file)
        print(ASCIIColors.color_reset, end=end, flush=flush, file=file)
    @staticmethod
    def highlight(text: str, subtext: Union[str, List[str]], color: str = color_white, highlight_color: str = color_yellow, whole_line: bool = False, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Highlights subtext occurrences within text directly on console."""
        # (Implementation remains same)
        subtexts = [subtext] if isinstance(subtext, str) else subtext
        output: str = ""
        if whole_line:
            lines = text.splitlines();
            for i, line in enumerate(lines):
                line_end = "" if i == len(lines) - 1 else "\n"
                if any(st in line for st in subtexts): output += f"{highlight_color}{line}{ASCIIColors.color_reset}{line_end}"
                else: output += f"{color}{line}{ASCIIColors.color_reset}{line_end}"
        else:
            processed_text = text
            for st in subtexts: processed_text = processed_text.replace(st, f"{highlight_color}{st}{color}")
            output = f"{color}{processed_text}{ASCIIColors.color_reset}"
        print(output, end=end, flush=flush, file=file)
    @staticmethod
    def activate(color_or_style: str, file: StreamType = sys.stdout) -> None:
        """Activates a color or style directly on console."""
        print(f"{color_or_style}", end="", flush=True, file=file)
    @staticmethod
    def reset(file: StreamType = sys.stdout) -> None:
        """Resets all colors and styles directly on console."""
        print(ASCIIColors.color_reset, end="", flush=True, file=file)
    @staticmethod
    def resetAll(file: StreamType = sys.stdout) -> None: # Alias with file arg
        """Resets colors and styles."""
        ASCIIColors.reset(file=file)

    @staticmethod
    def execute_with_animation(pending_text: str, func: Callable[..., _T], *args: Any, color: Optional[str] = None, **kwargs: Any) -> _T:
        """Executes func() with a console spinner, returns func's result or raises."""
        animation = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"; stop_event = threading.Event(); result: List[Optional[_T]] = [None]; exception: List[Optional[BaseException]] = [None]; thread_lock = Lock()
        text_color = color if color else ASCIIColors.color_yellow; success_symbol = "✓"; failure_symbol = "✗"
        def animate() -> None:
            idx = 0
            while not stop_event.is_set():
                ASCIIColors.print(f"\r{text_color}{pending_text} {animation[idx % len(animation)]}", color="", style="", end="", flush=True, file=sys.stdout)
                idx += 1; time.sleep(0.1)
            ASCIIColors.print(f"\r{text_color}{pending_text}  ", color="", style="", end="", flush=True, file=sys.stdout) # Clear animation
        def target() -> None:
            try: res = func(*args, **kwargs)
            except Exception as e_inner:
                with thread_lock: exception[0] = e_inner
            else: 
                with thread_lock: result[0] = res # Store result only on success
            finally: stop_event.set()
        worker = threading.Thread(target=target); animator = threading.Thread(target=animate)
        worker.start(); animator.start(); worker.join(); stop_event.set(); animator.join()
        with thread_lock: final_exception = exception[0]; final_result = result[0]
        final_symbol, final_color = (failure_symbol, ASCIIColors.color_red) if final_exception else (success_symbol, ASCIIColors.color_green)
        status_line = f"\r{text_color}{pending_text} {final_color}{final_symbol}{ASCIIColors.color_reset}          "
        ASCIIColors.print(status_line, color="", style="", flush=True, file=sys.stdout)
        ASCIIColors.print("", color="", style="", file=sys.stdout) # Newline
        if final_exception: raise final_exception
        # Fix: Use the correctly defined TypeVar _T
        return cast(_T, final_result)

# --- Global convenience function ---
def trace_exception(ex: BaseException) -> None:
    """Logs the traceback of an exception using ASCIIColors.error."""
    ASCIIColors.error(f"Exception Traceback ({type(ex).__name__})", exc_info=ex)

# ==============================================================================
# --- Logging Compatibility Layer ---
# ==============================================================================

_logger_cache: Dict[str, '_AsciiLoggerAdapter'] = {}
_logger_cache_lock = Lock()

class _AsciiLoggerAdapter:
    """Mimics standard logging.Logger, delegating to ASCIIColors global state."""
    name: str
    def __init__(self, name: str): self.name = name
    def setLevel(self, level: Union[int, str]) -> None: ASCIIColors.set_log_level(LogLevel(_level_name_to_int(level)))
    def getEffectiveLevel(self) -> int: return ASCIIColors._global_level.value
    def addHandler(self, hdlr: Handler) -> None: ASCIIColors.add_handler(hdlr)
    def removeHandler(self, hdlr: Handler) -> None: ASCIIColors.remove_handler(hdlr)
    def hasHandlers(self) -> bool:
        with ASCIIColors._handler_lock: return bool(ASCIIColors._handlers)
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if ASCIIColors._global_level <= LogLevel.DEBUG: ASCIIColors._log(LogLevel.DEBUG, msg, args, logger_name=self.name, **kwargs)
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if ASCIIColors._global_level <= LogLevel.INFO: ASCIIColors._log(LogLevel.INFO, msg, args, logger_name=self.name, **kwargs)
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if ASCIIColors._global_level <= LogLevel.WARNING: ASCIIColors._log(LogLevel.WARNING, msg, args, logger_name=self.name, **kwargs)
    warn = warning
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if ASCIIColors._global_level <= LogLevel.ERROR: ASCIIColors._log(LogLevel.ERROR, msg, args, logger_name=self.name, **kwargs)
    def exception(self, msg: str, *args: Any, exc_info: ExcInfoType = True, **kwargs: Any) -> None:
        kwargs['exc_info'] = exc_info; self.error(msg, *args, **kwargs)
    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if ASCIIColors._global_level <= LogLevel.CRITICAL: ASCIIColors._log(LogLevel.CRITICAL, msg, args, logger_name=self.name, **kwargs)
    fatal = critical
    def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        try: log_level_enum = LogLevel(level)
        except ValueError:
            if level > LogLevel.CRITICAL: log_level_enum = LogLevel.CRITICAL
            elif level < LogLevel.DEBUG: log_level_enum = LogLevel.DEBUG
            else: log_level_enum = LogLevel.INFO
        if ASCIIColors._global_level <= log_level_enum: ASCIIColors._log(log_level_enum, msg, args, logger_name=self.name, **kwargs)

_level_to_name: Dict[int, str] = {l.value: l.name for l in LogLevel if l.value != 0} # Exclude NOTSET from names
_level_to_name[NOTSET] = "NOTSET"
_name_to_level: Dict[str, int] = {name: level for level, name in _level_to_name.items()}

def getLevelName(level: int) -> str:
    """Return the textual representation of logging level 'level'."""
    return _level_to_name.get(level, f"Level {level}")

def _level_name_to_int(level: Union[int, str]) -> int:
    """Helper to convert level name/int to int."""
    if isinstance(level, int): return level
    if isinstance(level, str): return _name_to_level.get(level.upper(), DEBUG)
    return DEBUG

def getLogger(name: Optional[str] = None) -> _AsciiLoggerAdapter:
    """Returns a logger adapter with the specified name."""
    logger_name = name if name is not None else "root"
    with _logger_cache_lock:
        if logger_name not in _logger_cache:
             _logger_cache[logger_name] = _AsciiLoggerAdapter(logger_name)
        return _logger_cache[logger_name]

def basicConfig(**kwargs: Any) -> None:
    """Does basic configuration for the ASCIIColors logging system."""
    with ASCIIColors._handler_lock:
        already_configured: bool = bool(ASCIIColors._handlers) or ASCIIColors._basicConfig_called
        force: bool = kwargs.get('force', False)
        if already_configured and not force: return

        old_handlers: List[Handler] = ASCIIColors._handlers[:]
        ASCIIColors._handlers.clear()

        if force and old_handlers:
            for h in old_handlers:
                try: h.close()
                except Exception as e: ASCIIColors.print(f"PANIC: Error closing old handler {type(h).__name__}: {e}", color=ASCIIColors.color_bright_red, file=sys.stderr, flush=True)

        # Default level WARNING
        level_arg: Union[int, str] = kwargs.get('level', WARNING)
        level_int = _level_name_to_int(level_arg)
        ASCIIColors.set_log_level(LogLevel(level_int))

        fmt_arg: Optional[str] = kwargs.get('format', kwargs.get('fmt'))
        datefmt_arg: Optional[str] = kwargs.get('datefmt')
        style_arg: str = kwargs.get('style', '%')
        formatter: Formatter = Formatter(fmt=fmt_arg, datefmt=datefmt_arg, style=style_arg)

        handlers_arg: Optional[List[Handler]] = kwargs.get('handlers')
        filename_arg: Optional[Union[str, Path]] = kwargs.get('filename')
        stream_arg: Optional[StreamType] = kwargs.get('stream')
        new_handlers_list: List[Handler] = []
        current_level_enum = LogLevel(level_int)

        if handlers_arg is not None:
            for h in handlers_arg:
                if h.formatter is None: h.setFormatter(formatter)
                new_handlers_list.append(h)
        elif filename_arg is not None:
            mode_arg: str = kwargs.get('filemode', 'a'); encoding_arg: Optional[str] = kwargs.get('encoding'); delay_arg: bool = kwargs.get('delay', False)
            file_kw: Dict[str, Any] = {'mode': mode_arg, 'formatter': formatter, 'delay': delay_arg, 'level': current_level_enum}
            if encoding_arg: file_kw['encoding'] = encoding_arg
            new_handlers_list.append(FileHandler(filename_arg, **file_kw))
        else:
            handler: ConsoleHandler = ConsoleHandler(stream=stream_arg, level=current_level_enum)
            handler.setFormatter(formatter)
            new_handlers_list.append(handler)

        ASCIIColors._handlers = new_handlers_list
        ASCIIColors._basicConfig_called = True

# --- Example Usage ---
if __name__ == "__main__":
    # --- Direct Print Demo ---
    print("--- Direct Print Methods ---")
    ASCIIColors.red("Red Text")
    ASCIIColors.yellow("Yellow Text")
    ASCIIColors.bold("Bold White Text")
    ASCIIColors.italic("Italic Cyan Text", color=ASCIIColors.color_cyan)
    ASCIIColors.underline("Underlined Green", color=ASCIIColors.color_green)
    ASCIIColors.strikethrough("Strikethrough Magenta", color=ASCIIColors.color_magenta)
    ASCIIColors.bg_blue("White text on Blue Background")
    ASCIIColors.print_with_bg("Black text on Yellow BG", color=ASCIIColors.color_black, background=ASCIIColors.bg_yellow)
    ASCIIColors.print_with_bg(" Bold Red on Bright White BG ", color=ASCIIColors.color_red, background=ASCIIColors.bg_bright_white, style=ASCIIColors.style_bold)
    ASCIIColors.multicolor(
        ["Status: ", "OK", " | ", "Value: ", "100"],
        [ASCIIColors.color_white, ASCIIColors.color_green, ASCIIColors.color_white, ASCIIColors.color_cyan, ASCIIColors.color_bright_yellow]
    )
    ASCIIColors.highlight("Highlight the word 'ERROR' in this line.", "ERROR", highlight_color=ASCIIColors.bg_red)

    # --- Logging Demo (Original API) ---
    print("\n--- Logging Demo (ASCIIColors API) ---")
    ASCIIColors.clear_handlers() # Start fresh for demo
    ASCIIColors._basicConfig_called = False # Reset flag
    ASCIIColors.set_log_level(DEBUG)
    # Add console handler with custom format using {} style
    console_fmt = Formatter("[{levelname}] {message} (Thread: {threadName})", style='{')
    ASCIIColors.add_handler(ConsoleHandler(formatter=console_fmt, stream=sys.stdout))
    # Add file handler
    log_file_ascii = Path("temp_ascii_api.log")
    if log_file_ascii.exists(): log_file_ascii.unlink()
    file_fmt = Formatter("%(asctime)s|%(levelname)-8s|%(name)s|%(message)s", style='%', datefmt='%H:%M:%S')
    ASCIIColors.add_handler(FileHandler(log_file_ascii, level=INFO, formatter=file_fmt))

    ASCIIColors.debug("This is a debug message (console only).")
    ASCIIColors.info("Information message %s.", "with arg")
    ASCIIColors.warning("A warning occurred.")
    with ASCIIColors.context(user_id="test"):
        ASCIIColors.error("An error happened in user context.", exc_info=False)
    try:
        x = 1 / 0
    except ZeroDivisionError as e:
        ASCIIColors.critical("Critical failure!", exc_info=e)
        trace_exception(e) # Use utility

    print(f"\nCheck '{log_file_ascii}' for file logs (INFO+)")
    if log_file_ascii.exists():
        print(f"--- {log_file_ascii.name} Content ---")
        print(log_file_ascii.read_text())
        print(f"--- End {log_file_ascii.name} ---")

    # --- Logging Demo (Compatibility Layer) ---
    print("\n--- Logging Demo (Compatibility API) ---")
    log_file_compat = Path("temp_compat_api.log")
    if log_file_compat.exists(): log_file_compat.unlink()

    # Use basicConfig
    basicConfig(
        level=DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename=log_file_compat,
        filemode='w',
        force=True # Override previous config
    )
    # Add another handler (console)
    logger = getLogger("CompatTest")
    console_h = StreamHandler(level=INFO, stream=sys.stdout) # Defaults to stderr if stream=None
    console_h.setFormatter(Formatter("{name}::{levelname} >> {message}", style='{'))
    logger.addHandler(console_h) # Modifies global handlers

    logger.debug("Compat Debug message (file only).")
    logger.info("Compat Info message.")
    logger.warning("Compat Warning message.")
    logger.error("Compat Error message.")
    try:
        y = int("abc")
    except ValueError:
        logger.exception("Compat Exception occurred!") # Includes traceback

    print(f"\nCheck '{log_file_compat}' for file logs (DEBUG+)")
    if log_file_compat.exists():
        print(f"--- {log_file_compat.name} Content ---")
        print(log_file_compat.read_text())
        print(f"--- End {log_file_compat.name} ---")

    # --- Animation ---
    print("\n--- Animation Demo ---")
    def long_task(duration: float = 2):
        ASCIIColors.info(f"Task started, will run for {duration}s...")
        time.sleep(duration)
        #if duration > 1: raise ValueError("Task failed!")
        return f"Task completed after {duration}s"

    try:
        result = ASCIIColors.execute_with_animation("Running task...", long_task, 1.5)
        ASCIIColors.success(f"Animation Success: {result}")
    except Exception as e:
        trace_exception(e)
        ASCIIColors.fail(f"Animation Failed: {e}")

    # Clean up demo files
    # if log_file_ascii.exists(): log_file_ascii.unlink()
    # if log_file_compat.exists(): log_file_compat.unlink()