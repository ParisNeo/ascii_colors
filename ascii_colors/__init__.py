# -*- coding: utf-8 -*-
"""
ascii_colors: A Python library for rich terminal output with advanced logging features.
Includes a logging compatibility layer.

This module provides a comprehensive solution for enhancing command-line application
output. It offers two main functionalities:

1.  **Direct ANSI Styled Printing:** Static methods on the `ASCIIColors` class allow
    for immediate printing of text to the console with specified foreground colors,
    background colors, and text styles (bold, italic, underline, etc.). These methods
    bypass the logging system entirely.

2.  **Structured Logging System:** A flexible and powerful logging system that mirrors
    the interface of Python's standard `logging` module (`getLogger`, `basicConfig`,
    `Handlers`, `Formatters`, level constants). This allows for leveled logging,
    output routing to multiple destinations (console, files), customizable message
    formats (including JSON), log rotation, and thread-local context injection.

The library aims to be easy to use for simple cases while providing robust
configuration options for complex applications.

Key Components:
- ANSI color and style constants (e.g., `ASCIIColors.color_red`, `ASCIIColors.style_bold`).
- Direct printing methods (`ASCIIColors.red()`, `ASCIIColors.print()`, `ASCIIColors.highlight()`).
- Logging compatibility API (`getLogger`, `basicConfig`, `DEBUG`, `INFO`, etc.).
- Handler classes (`ConsoleHandler`/`StreamHandler`, `FileHandler`, `RotatingFileHandler`).
- Formatter classes (`Formatter`, `JSONFormatter`).
- Utility functions (`execute_with_animation`, `trace_exception`).

Author: Saifeddine ALOUI (ParisNeo)
License: Apache License 2.0
"""

import inspect
import json
import logging as std_logging # Alias to avoid name conflicts and access standard levels
import os
import shutil
import platform
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
                    Union, cast, Text, TypeVar, ContextManager, IO, Iterable, Sized)

import math
import re
import textwrap
# Platform specific imports for single key press
import platform
if platform.system() == "Windows":
    import msvcrt
else: # Unix-like (Linux, macOS)
    import termios
    import tty

# --- Helper functions ---

# --- Helper for single key input ---

_KEY_MAP_WINDOWS = {
    b'H': 'UP', b'P': 'DOWN', b'K': 'LEFT', b'M': 'RIGHT', # Arrows
    b'\r': 'ENTER',
    b'\x03': 'QUIT', # Ctrl+C
    b'\x08': 'BACKSPACE',
    # Add other special keys if needed (e.g., Home, End, Del)
}
_KEY_MAP_UNIX_ESCAPE = {
    'A': 'UP', 'B': 'DOWN', 'D': 'LEFT', 'C': 'RIGHT', # Arrows
    # Add Home (H), End (F) etc. if needed: '[1~', '[4~' or 'OH', 'OF'
}

def _get_key() -> str:
    """
    Reads a single keypress from the terminal without waiting for Enter.
    Handles basic arrow keys, Enter, and Ctrl+C across platforms.

    Returns:
        A string representing the key ('UP', 'DOWN', 'LEFT', 'RIGHT', 'ENTER', 'QUIT', 'BACKSPACE')
        or the character pressed.
    """
    if platform.system() == "Windows":
        ch = msvcrt.getch()
        # Check for special keys (starting with \xe0 or \x00)
        if ch in (b'\xe0', b'\x00'):
            ch2 = msvcrt.getch()
            return _KEY_MAP_WINDOWS.get(ch2, '') # Return mapped key or empty string
        # Check for other single-byte special keys
        mapped = _KEY_MAP_WINDOWS.get(ch)
        if mapped:
            return mapped
        # Regular character
        try:
            return ch.decode('utf-8')
        except UnicodeDecodeError:
            return '?' # Or handle decoding errors more robustly

    else: # Unix-like
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd) # Read keys immediately, pass signals (like Ctrl+C)
            # tty.setraw(fd) # More raw, might disable Ctrl+C handling by terminal

            ch = sys.stdin.read(1)

            if ch == '\x1b': # Escape sequence likely
                # Read up to 2 more chars for common sequences (like \x1b[A)
                next_chars = sys.stdin.read(2)
                if next_chars.startswith('['):
                    key = next_chars[1]
                    return _KEY_MAP_UNIX_ESCAPE.get(key, '') # Map arrow keys
                # Could handle other escape sequences here (e.g., Alt+key)
                return 'ESCAPE' # Or return raw escape if needed

            elif ch == '\r' or ch == '\n':
                return 'ENTER'
            elif ch == '\x03': # Ctrl+C
                return 'QUIT'
            elif ch == '\x7f': # Often Backspace
                return 'BACKSPACE'
            else:
                return ch # Regular character

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# Regular expression to match ANSI escape sequences.
# \x1B is the ESC character.
# It matches two main forms:
# 1. ESC followed by a single character from '@' to '_' (used for some simple commands).
# 2. ESC followed by '[' (Control Sequence Introducer - CSI), then optional parameters
#    (digits, ';', '?'), optional intermediate characters (' ' to '/'), and a final
#    command character ('@' to '~'). This covers most color/style/cursor codes like \x1B[31m.
ANSI_ESCAPE_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

def strip_ansi(text: str) -> str:
    """
    Removes ANSI escape sequences (like color codes) from a string.

    Args:
        text: The input string potentially containing ANSI codes.

    Returns:
        The string with ANSI codes removed.
    """
    if not isinstance(text, str):
        # Handle potential non-string input gracefully in tests
        return str(text)
    return ANSI_ESCAPE_REGEX.sub("", text)

# --- Log Level Enum & Constants ---

class LogLevel(IntEnum):
    """
    Enumeration defining standard logging levels.

    These levels correspond directly to the values used in Python's standard
    `logging` module and are used internally for filtering log messages based
    on severity. Lower numerical values indicate lower severity.
    """
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0

# Provide standard logging level constants mapped to our enum values for convenience
# and compatibility with the standard `logging` module interface.
CRITICAL: int = LogLevel.CRITICAL.value
"""Integer value for the CRITICAL log level (50)."""
ERROR: int = LogLevel.ERROR.value
"""Integer value for the ERROR log level (40)."""
WARNING: int = LogLevel.WARNING.value
"""Integer value for the WARNING log level (30)."""
INFO: int = LogLevel.INFO.value
"""Integer value for the INFO log level (20)."""
DEBUG: int = LogLevel.DEBUG.value
"""Integer value for the DEBUG log level (10)."""
NOTSET: int = LogLevel.NOTSET.value
"""Integer value for the NOTSET level (0). Handlers and loggers are often
initialized with this level."""

# --- Type Aliases ---
ActionCallable = Callable[[], Any] # Type alias for menu action functions

ExcInfoType = Optional[Union[bool, BaseException, Tuple[Optional[Type[BaseException]], Optional[BaseException], Any]]]
"""
Type alias for exception information passed to logging methods.
Can be:
- `None`: No exception info.
- `True`: Capture exception info automatically using `sys.exc_info()`.
- An exception instance: The exception object itself.
- A 3-tuple `(type, value, traceback)` as returned by `sys.exc_info()`.
"""

LevelType = Union[LogLevel, int]
"""Type alias for specifying a log level, accepting either a `LogLevel` enum member
or its corresponding integer value."""

StreamType = Union[TextIO, IO[str]]
"""Type alias representing a text stream, typically `sys.stdout`, `sys.stderr`,
or an open file handle in text mode."""

# --- Utility Functions ---

def get_trace_exception(ex: BaseException) -> str:
    """
    Formats a given exception object and its traceback into a single string.

    This utility is useful for consistently formatting exception details,
    often used within formatters or when manually logging exception information.

    Args:
        ex: The exception instance to format.

    Returns:
        A string containing the formatted exception type, message, and traceback.
    """
    traceback_lines: List[str] = traceback.format_exception(type(ex), ex, ex.__traceback__)
    return "".join(traceback_lines)

# --- Formatter Classes ---

class Formatter:
    """
    Base class for formatting log records into textual representations.

    This class converts the internal log record details (level, message, timestamp,
    source info, context, etc.) into a final string suitable for output by a Handler.
    It supports both traditional '%' style and modern '{}' style format strings,
    drawing inspiration and compatibility from Python's standard `logging.Formatter`.

    Attributes:
        style (str): The formatting style ('%' or '{'). Defaults to '%'.
        fmt (Optional[str]): The format string definition. If None, a default
                             format is used based on the style.
        datefmt (str): The format string for timestamps (used with 'asctime').
                       Defaults to "%Y-%m-%d %H:%M:%S,%f" (milliseconds included).
        include_source (bool): If True, attempts to automatically determine and
                               include source code information (filename, lineno,
                               funcName) in the log record. This incurs performance
                               overhead due to stack inspection. Defaults to False.
    """
    # Mapping for standard logging format specifiers for %-style formatting.
    # Lambdas access the prepared `log_record` dictionary.
    _style_mapping: Dict[str, Dict[str, Callable[[Dict[str, Any]], Any]]] = {
        # '%' style mappings (executed during string formatting)
        '%': {
            'asctime': lambda r: r['timestamp'].strftime(r.get('datefmt', "%Y-%m-%d %H:%M:%S,%f")[:-3] if r.get('datefmt', '').endswith(',%f') else r.get('datefmt', "%Y-%m-%d %H:%M:%S")),
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
            'processName': lambda r: threading.current_thread().name, # Note: Python thread names
            'relativeCreated': lambda r: (r['timestamp'] - r.get('_initial_timestamp', r['timestamp'])).total_seconds() * 1000,
            'thread': lambda r: threading.get_ident(),
            'threadName': lambda r: threading.current_thread().name,
        },
        # '{' style mappings (less critical as str.format accesses keys directly,
        # but can be used for pre-calculation or complex needs).
        '{': {
            'asctime': lambda r: r['timestamp'].strftime(r.get('datefmt', "%Y-%m-%d %H:%M:%S,%f")[:-3] if r.get('datefmt', '').endswith(',%f') else r.get('datefmt', "%Y-%m-%d %H:%M:%S")),
            # Other fields are typically accessed directly via {key} in the format string
        }
    }
    _initial_timestamp: datetime = datetime.now() # Class attribute to store initial time for relativeCreated

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = '%',
        include_source: bool = False,
        **kwargs: Any # Allow extra kwargs for compatibility/future use
    ):
        """
        Initializes the Formatter instance.

        Args:
            fmt: The format string. If None, a default format string is used:
                 '%(levelname)s:%(name)s:%(message)s' for style='%', or
                 '{levelname}:{name}:{message}' for style='{'.
            datefmt: The date format string for the 'asctime' field. If None,
                     defaults to "%Y-%m-%d %H:%M:%S,%f", usually displayed with
                     milliseconds truncated (e.g., "%Y-%m-%d %H:%M:%S,fff").
            style: The formatting style to use. Must be '%' or '{'. Defaults to '%'.
            include_source: If True, attempt to find the source file, line number,
                            and function name of the log call site. This involves
                            inspecting the call stack and adds significant overhead.
                            Defaults to False.
            **kwargs: Absorbs any extra keyword arguments for potential future use
                      or compatibility.
        """
        if style not in ('%', '{'):
            raise ValueError(f"Style must be '%' or '{{}}', not '{style}'")
        self.style: str = style
        self.fmt: Optional[str] = fmt # Store None if passed, handle default in format()
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
        """
        Formats the log record data into the final output string.

        This method is called by Handlers to turn the raw log information into
        a formatted string based on the formatter's configuration (`fmt`, `style`,
        `datefmt`, `include_source`).

        Args:
            level: The severity level of the log record (e.g., LogLevel.INFO).
            message: The primary log message string (after any %-style args merge).
            timestamp: The datetime object when the logging call was made.
            exc_info: Exception tuple `(type, value, traceback)` if exception info
                      is present, otherwise None.
            logger_name: The name of the logger that issued the record.
            **kwargs: Any additional context or data passed with the logging call
                      (e.g., using `logger.info("msg", extra={'key': 'val'})` or
                      context variables from `ASCIIColors.context`).

        Returns:
            The fully formatted log record string.
        """
        level_name: str = level.name
        level_no: int = level.value
        filename: str = "N/A"; lineno: int = 0; funcName: str = "N/A"; pathname: str = "N/A"

        # --- Source Information Retrieval (if enabled) ---
        if self.include_source:
            try:
                # Walk up the stack to find the frame outside the logging system
                frame = inspect.currentframe()
                depth = 0
                # Limit depth to prevent excessive stack walking in complex scenarios
                while frame and depth < 20:
                    fname = frame.f_code.co_filename
                    func = frame.f_code.co_name
                    # Heuristic to identify internal logging frames
                    is_internal_file = "ascii_colors" in Path(fname).parts or Path(fname).name == "__init__.py"
                    is_internal_func = func in (
                        '_log','format','handle','emit','debug','info','warning','error','critical','exception',
                        'log','trace_exception','basicConfig','getLogger','_AsciiLoggerAdapter'
                        # Add adapter methods if needed
                    )

                    if not (is_internal_file or is_internal_func): # Found the caller frame
                        pathname = str(Path(fname).resolve()) # Absolute path
                        lineno = frame.f_lineno
                        funcName = func
                        filename = Path(pathname).name # Just the filename part
                        break
                    frame = frame.f_back
                    depth += 1
                del frame # Avoid reference cycles
            except Exception:
                # Ignore errors during inspection, keep defaults N/A
                pass

        # --- Prepare Log Record Dictionary ---
        # Create a dictionary containing all standard logging attributes plus context.
        # This dictionary is used for both %-style and {}-style formatting.
        log_record: Dict[str, Any] = {
            # Merge thread-local context first, then explicit kwargs from the log call
            **ASCIIColors.get_thread_context(),
            **kwargs,
            # Standard logging attributes
            "levelno": level_no,
            "levelname": level_name,
            "pathname": pathname,
            "filename": filename,
            "module": Path(pathname).stem if pathname != 'N/A' else 'N/A',
            "lineno": lineno,
            "funcName": funcName,
            "created": timestamp.timestamp(),
            "msecs": int(timestamp.microsecond / 1000),
            "relativeCreated": (timestamp - self._initial_timestamp).total_seconds() * 1000,
            "thread": threading.get_ident(),
            "threadName": threading.current_thread().name,
            "process": os.getpid(),
            "processName": threading.current_thread().name, # Python threads, not OS processes
            "message": message, # The actual message string
            "name": logger_name,
            # Data needed for formatting calculations
            "timestamp": timestamp, # datetime object
            "datefmt": self.datefmt, # Pass along date format for %-style 'asctime'
            "_initial_timestamp": self._initial_timestamp, # For relativeCreated calculation
            # Pre-calculated fields for convenience/performance (used by %-style or directly in {}-style)
            "asctime": timestamp.strftime(self.datefmt[:-3] if self.datefmt.endswith(',%f') else self.datefmt),
            # Legacy/Alias names (less common now but kept for potential compatibility)
            "level_name": level_name, "level": level_no,
            "file_name": filename, "line_no": lineno, "func_name": funcName,
        }

        # --- Determine Format String and Style ---
        current_fmt = self.fmt
        current_style = self.style
        if current_fmt is None: # Use default format if none provided at init
            if self.style == '%':
                current_fmt = "%(levelname)s:%(name)s:%(message)s"
            else: # self.style == '{'
                current_fmt = "{levelname}:{name}:{message}"
            # Note: Default style remains as initialized ('%') if fmt was None

        # --- Perform Formatting ---
        formatted_message: str = ""
        try:
            if current_style == '%':
                # Use internal helper for %-style substitution
                formatted_message = self._format_percent_style(log_record, current_fmt)
            elif current_style == '{':
                # For {} style, use str.format directly with the comprehensive log_record
                formatted_message = current_fmt.format(**log_record)
            # Should not happen due to __init__ check, but as fallback:
            # else:
            #    formatted_message = f"[UNSUPPORTED_STYLE:{current_style}] {current_fmt}"

        except KeyError as e:
             # Error if a key used in the format string is missing from log_record
             formatted_message = f"[FORMAT_ERROR: Missing key {e} for '{current_style}' style. Fmt: '{current_fmt}'. Avail Keys: {list(log_record.keys())}]"
        except Exception as e:
             # Catch other potential formatting errors (e.g., type mismatches in %)
             formatted_message = f"[FORMAT_ERROR: {type(e).__name__} '{e}' using style '{current_style}' with fmt '{current_fmt}'. Avail Keys: {list(log_record.keys())}]"

        # --- Append Exception Information ---
        if exc_info:
            formatted_message += "\n" + self.format_exception(exc_info)

        return formatted_message

    def _format_percent_style(self, record: Dict[str, Any], fmt: str) -> str:
        """
        Internal helper to perform %-style formatting using calculated values.

        It uses a temporary class (`RecordAccessor`) to intercept key lookups
        during the `%` operation. This allows dynamic calculation of values like
        'asctime' or 'msecs' based on the mappings in `_style_mapping`.

        Args:
            record: The log record dictionary containing all available data.
            fmt: The %-style format string.

        Returns:
            The formatted string.
        """
        class RecordAccessor:
            """Helper class to access record items, calculating %-style specials."""
            def __init__(self, rec: Dict[str, Any]):
                self._rec = rec
            def __getitem__(self, key: str) -> Any:
                # Prioritize dynamic calculation based on standard % mapping
                if key in Formatter._style_mapping['%']:
                    try:
                        return Formatter._style_mapping['%'][key](self._rec)
                    except Exception as e_lambda:
                        # Error during lambda execution for the key
                        return f"<FmtErr:{key}:{e_lambda}>"
                # Fallback to direct access in the record dictionary
                try:
                    return self._rec[key]
                except KeyError:
                    # Key not found in record or calculated mapping
                    raise KeyError(f"Format key '{key}' not found in record or standard mappings.")

        try:
            # Perform the % formatting using the accessor
            return fmt % RecordAccessor(record)
        except (TypeError, KeyError, ValueError) as e:
            # Handle errors during the % substitution itself
            missing_key = getattr(e, 'args', ['N/A'])[0] if isinstance(e, KeyError) else 'N/A'
            return f"[FORMAT_SUBSTITUTION_ERROR: {type(e).__name__} '{e}' for key '{missing_key}'. Fmt:'{fmt}'. Record Keys: {list(record.keys())}]"
        except Exception as e:
             # Catch unexpected errors during formatting
             return f"[FORMAT_UNKNOWN_ERROR: {type(e).__name__} '{e}'] Fmt:'{fmt}'"

    def format_exception(self, exc_info: Tuple[Optional[Type[BaseException]], Optional[BaseException], Any]) -> str:
        """
        Formats the specified exception information as a traceback string.

        Args:
            exc_info: A tuple `(type, value, traceback)` as returned by `sys.exc_info()`.

        Returns:
            A string representing the formatted traceback, or an empty string if
            no valid exception information is provided.
        """
        if exc_info and exc_info[1]: # Check if the exception value exists
            return get_trace_exception(exc_info[1])
        return ""

class JSONFormatter(Formatter):
    """
    Formats log records into JSON strings.

    This formatter serializes the log record dictionary (potentially selecting or
    renaming fields) into a JSON formatted string, making logs easily parsable by
    other systems.

    Attributes:
        fmt_dict (Optional[Dict[str, str]]): A dictionary mapping output JSON keys
            to format strings (using `style`). If set, `include_fields` is ignored.
        include_fields (Optional[List[str]]): A list of standard log record keys
            to include in the JSON output. If None and `fmt_dict` is None, a
            default set of fields is used.
        datefmt_str (Optional[str]): The date format string. If None or "iso",
            uses ISO 8601 format. Otherwise, uses `strftime` with the given format.
        json_ensure_ascii (bool): Passed to `json.dumps`. If True (default),
            non-ASCII characters are escaped.
        json_indent (Optional[int]): Passed to `json.dumps`. If not None, pretty-prints
            JSON with the specified indent level.
        json_separators (Optional[Tuple[str, str]]): Passed to `json.dumps`. Overrides
            default separators (e.g., `(',', ': ')`).
        json_sort_keys (bool): Passed to `json.dumps`. If True, sorts JSON keys
            alphabetically.
        include_source (bool): If True, attempts to include source code info
                               (filename, lineno, funcName). Adds overhead.
    """
    def __init__(
        self,
        fmt: Optional[Dict[str, str]] = None,
        datefmt: Optional[str] = None,
        style: str = '%', # Style applies if using fmt dict with complex values
        json_ensure_ascii: bool = False,
        json_indent: Optional[int] = None,
        json_separators: Optional[Tuple[str, str]] = None,
        json_sort_keys: bool = False,
        include_fields: Optional[List[str]] = None,
        include_source: bool = False,
        **kwargs: Any
    ):
        """
        Initializes the JSONFormatter instance.

        Args:
            fmt: A dictionary mapping desired output JSON keys to format strings
                 (which will be processed using the specified `style`). Example:
                 `{'timestamp': '%(asctime)s', 'level': '%(levelname)s', 'msg': '%(message)s'}`.
                 If provided, `include_fields` is ignored.
            datefmt: Date format string. Special value "iso" (default) uses ISO 8601
                     format (`datetime.isoformat()`). Otherwise, uses `strftime`.
            style: The formatting style ('%' or '{') to use *if* `fmt` (the dict)
                   is provided and contains complex format strings that need evaluation.
                   Defaults to '%'.
            json_ensure_ascii: Corresponds to `ensure_ascii` in `json.dumps`. Defaults to False.
            json_indent: Corresponds to `indent` in `json.dumps`. Defaults to None.
            json_separators: Corresponds to `separators` in `json.dumps`. Defaults to None.
            json_sort_keys: Corresponds to `sort_keys` in `json.dumps`. Defaults to False.
            include_fields: A list of log record attribute names to include in the
                            final JSON object (e.g., ["levelname", "message", "timestamp"]).
                            If `fmt` is None and `include_fields` is None, a default
                            set of fields is used.
            include_source: If True, attempt to find source file/line/func information.
                            Adds overhead. Defaults to False.
            **kwargs: Absorbs extra keyword arguments.
        """
        # Pass style and include_source to parent Formatter for potential use in fmt dict evaluation
        super().__init__(style=style, include_source=include_source)
        self.fmt_dict: Optional[Dict[str, str]] = fmt
        self.include_fields: Optional[List[str]] = include_fields
        self.datefmt_str: Optional[str] = datefmt # Store original date format request

        # Set up the date formatting function based on datefmt
        if datefmt is None or datefmt.lower() == "iso":
            self._format_date: Callable[[datetime], str] = lambda dt: dt.isoformat()
        else:
            # If a specific strftime format is given
            self._format_date = lambda dt: dt.strftime(cast(str, self.datefmt_str))

        # Store JSON serialization options
        self.json_ensure_ascii = json_ensure_ascii
        self.json_indent = json_indent
        self.json_separators = json_separators
        self.json_sort_keys = json_sort_keys

    def format(
        self,
        level: LogLevel, message: str, timestamp: datetime,
        exc_info: Optional[Tuple[Optional[Type[BaseException]], Optional[BaseException], Any]],
        logger_name: str = 'root', **kwargs: Any
    ) -> str:
        """
        Formats the log record into a JSON string.

        Constructs a dictionary representing the log record based on the formatter's
        configuration (`fmt_dict`, `include_fields`, `include_source`) and then
        serializes it to a JSON string using the specified options.

        Args:
            level: The severity level of the log record.
            message: The primary log message string.
            timestamp: The datetime object when the logging call occurred.
            exc_info: Exception tuple `(type, value, traceback)`, or None.
            logger_name: The name of the logger.
            **kwargs: Additional context or data passed with the logging call.

        Returns:
            A string containing the JSON representation of the log record.
            Returns a JSON error object if serialization fails.
        """
        level_name: str = level.name
        level_no: int = level.value
        dt_str: str = self._format_date(timestamp) # Use configured date formatter
        filename: str = "N/A"; lineno: int = 0; funcName: str = "N/A"; pathname: str = "N/A"

        # --- Source Information Retrieval (if enabled) ---
        # (Similar logic to Formatter.format)
        if self.include_source:
             try:
                 frame = inspect.currentframe(); depth = 0
                 while frame and depth < 20:
                     fname = frame.f_code.co_filename; func = frame.f_code.co_name
                     # Check if frame is from this logging module itself
                     is_internal_file = "ascii_colors" in Path(fname).parts or Path(fname).name == "__init__.py"
                     is_internal_func = func in (
                         '_log','format','handle','emit','debug','info','warning','error','critical','exception',
                         'log','trace_exception','basicConfig','getLogger','_AsciiLoggerAdapter', 'format_exception' # Added JSONFormatter methods
                     )
                     if not (is_internal_file or is_internal_func):
                         pathname = str(Path(fname).resolve()); lineno = frame.f_lineno; funcName = func; filename = Path(pathname).name
                         break
                     frame = frame.f_back; depth += 1
                 del frame
             except Exception: pass # Ignore inspection errors

        # --- Build the Full Log Record Dictionary ---
        # This contains all potentially usable information.
        log_record: Dict[str, Any] = {
            "levelno": level_no, "levelname": level_name,
            "asctime": dt_str, # Use pre-formatted date string
            "timestamp": timestamp.timestamp(), # Raw POSIX timestamp
            "message": message, "name": logger_name,
            "pathname": pathname, "filename": filename, "lineno": lineno, "funcName": funcName,
            "module": Path(pathname).stem if pathname != 'N/A' else 'N/A',
            "process": os.getpid(), "processName": threading.current_thread().name,
            "thread": threading.get_ident(), "threadName": threading.current_thread().name,
            # Include context and extra kwargs passed to the logger
            **ASCIIColors.get_thread_context(),
            **kwargs
        }

        # --- Add Exception Information (if present) ---
        if exc_info:
            try:
                log_record["exc_info"] = self.format_exception(exc_info)
                # Optionally include separate fields for exception type/value
                log_record["exc_type"] = exc_info[0].__name__ if exc_info[0] else None
                log_record["exc_value"] = str(exc_info[1]) if exc_info[1] else None
            except Exception as e:
                # Handle errors during exception formatting itself
                log_record["exception_formatting_error"] = str(e)

        # --- Select and Format Fields for Final JSON Object ---
        final_json_object: Dict[str, Any] = {}
        if self.include_fields is not None:
            # Select specific fields from the full log_record
            final_json_object = {k: v for k, v in log_record.items() if k in self.include_fields}
        elif self.fmt_dict is not None:
            # Use the provided dictionary mapping output keys to format strings.
            # Evaluate each format string against the log_record.
            # Create a temporary standard Formatter instance to handle the evaluation.
            temp_formatter = Formatter(style=self.style, datefmt=self.datefmt_str, include_source=False) # Don't re-run source detection
            temp_formatter._initial_timestamp = self._initial_timestamp # Ensure relativeCreated is consistent
            for key, fmt_string in self.fmt_dict.items():
                temp_formatter.fmt = fmt_string # Set the format string for this key
                try:
                     # Format using the temp formatter. Pass the *full* record.
                     # Note: We pass dummy values for level/message/etc. as the formatter should
                     # primarily use the pre-populated `log_record` dictionary passed via kwargs.
                     # This relies on the Formatter._format_percent_style using the provided dict.
                     formatted_value = temp_formatter.format(
                         level, "", timestamp, None, # Dummy values
                         logger_name=logger_name, **log_record # Pass the real data here
                     )
                     # Strip potential exception info added by the temp formatter if fmt had % or {} message
                     # This is a bit heuristic; assumes the main message was the target.
                     # TODO: Revisit this logic. Maybe temp_formatter shouldn't add exc_info.
                     base_message = log_record.get("message", "")
                     if formatted_value.startswith(base_message) and log_record.get("exc_info"):
                         formatted_value = formatted_value.split('\n', 1)[0]

                     final_json_object[key] = formatted_value
                except Exception as e:
                    final_json_object[key] = f"<FmtErr:{key}:{e}>" # Error formatting this specific field
        else:
            # Default behavior: include a standard set of fields if neither fmt_dict nor include_fields specified.
            default_fields = [
                "timestamp", "levelname", "name", "message",
                "filename", "lineno", "funcName", "process", "threadName"
            ]
            final_json_object = {k: v for k, v in log_record.items() if k in default_fields}
            # Add context/kwargs back in case they weren't in default_fields but were provided
            final_json_object.update(ASCIIColors.get_thread_context())
            final_json_object.update(kwargs)
            # Ensure exception info is included if present
            if "exc_info" in log_record:
                final_json_object["exc_info"] = log_record["exc_info"]
            if "exc_type" in log_record:
                final_json_object["exc_type"] = log_record["exc_type"]


        # --- Serialize the Final Dictionary to JSON ---
        try:
            return json.dumps(
                final_json_object,
                default=str, # Convert non-serializable types (like datetime) to strings
                ensure_ascii=self.json_ensure_ascii,
                indent=self.json_indent,
                separators=self.json_separators,
                sort_keys=self.json_sort_keys
            )
        except Exception as e:
            # Fallback if JSON serialization fails
            return json.dumps({
                "json_format_error": f"Failed to serialize log record: {type(e).__name__} - {e}",
                "record_keys_attempted": list(final_json_object.keys())
            })

# --- Handler Classes ---

class Handler(ABC):
    """
    Abstract base class for all log handlers.

    Handlers are responsible for dispatching log records to the appropriate
    destination (e.g., console, file, network socket). Each handler can have
    its own minimum logging level and formatter.

    Subclasses must implement the `emit` method.

    Attributes:
        level (LogLevel): The minimum severity level required for a record to be
                          processed by this handler.
        formatter (Optional[Formatter]): The formatter instance used to convert
                                         log records to strings. If None, a default
                                         formatter may be used during `handle`.
        _lock (Lock): A thread lock to ensure thread-safe operations (like emit).
        closed (bool): Flag indicating if the handler has been closed.
    """
    level: LogLevel
    formatter: Optional[Formatter]
    _lock: Lock
    closed: bool

    def __init__(
        self,
        level: LevelType = DEBUG,
        formatter: Optional[Formatter] = None,
    ):
        """
        Initializes the base Handler.

        Args:
            level: The minimum logging level for this handler. Defaults to DEBUG.
            formatter: The formatter instance to use. Defaults to None.
        """
        self.level = LogLevel(level if isinstance(level, LogLevel) else int(level))
        self.formatter = formatter # Store None if passed, default applied in handle()
        self._lock = Lock()
        self.closed = False

    def setLevel(self, level: LevelType) -> None:
        """
        Sets the minimum logging level for this handler.

        Args:
            level: The new minimum level (LogLevel enum or int).
        """
        with self._lock:
            self.level = LogLevel(level if isinstance(level, LogLevel) else int(level))

    def getLevel(self) -> int:
        """Gets the minimum logging level for this handler."""
        # Returns the integer value for compatibility with standard logging checks
        return self.level.value

    def setFormatter(self, formatter: Formatter) -> None:
        """
        Sets the Formatter for this handler.

        Args:
            formatter: The Formatter instance to use.
        """
        with self._lock:
            self.formatter = formatter

    def getFormatter(self) -> Optional[Formatter]:
        """Gets the Formatter for this handler (may be None)."""
        return self.formatter

    # Original ascii_colors method name, kept for backward compatibility if needed
    def set_formatter(self, formatter: Formatter) -> None:
        """Alias for setFormatter."""
        self.setFormatter(formatter)

    def handle(
        self,
        level: LogLevel, message: str, timestamp: datetime,
        exc_info: Optional[Tuple[Optional[Type[BaseException]], Optional[BaseException], Any]],
        logger_name: str = 'root', **kwargs: Any
    ) -> None:
        """
        Conditionally processes a log record.

        Checks if the record's level meets the handler's threshold. If it does,
        it formats the record using its formatter (or a default one if none is set)
        and then calls the `emit` method to dispatch it.

        Args:
            level: The level of the log record being handled.
            message: The primary message string.
            timestamp: The time the record was created.
            exc_info: Exception information tuple, or None.
            logger_name: The name of the logger originating the record.
            **kwargs: Additional context data.
        """
        if self.closed:
            return
        # Check if the record's level is sufficient for this handler
        if level >= self.level:
            fmt_to_use = self.formatter # Use assigned formatter if available
            if fmt_to_use is None:
                 # Create and use a temporary default Formatter if none was assigned to the handler.
                 # This ensures output occurs even without explicit formatter setup.
                 fmt_to_use = Formatter() # Uses internal defaults (fmt=None -> % style default)

            # Format the record into a string
            formatted_message = fmt_to_use.format(level, message, timestamp, exc_info, logger_name=logger_name, **kwargs)

            # Acquire lock before emitting for thread safety
            with self._lock:
                if not self.closed: # Double check closed status after acquiring lock
                    try:
                        # Dispatch the formatted message
                        self.emit(level, formatted_message)
                    except Exception:
                        # Handle potential errors during emit itself
                        self.handle_error("Error during emit")


    @abstractmethod
    def emit(self, level: LogLevel, formatted_message: str) -> None:
        """
        Sends the formatted log record to the destination.

        This method must be implemented by subclasses. It defines the actual
        output action (e.g., writing to a stream, sending over network).

        Args:
            level: The severity level of the message being emitted (can be used
                   by subclass for level-specific actions, e.g., coloring).
            formatted_message: The final, formatted string to be output.

        Raises:
            NotImplementedError: If called on the base Handler class.
        """
        raise NotImplementedError("emit() must be implemented by Handler subclasses")

    def close(self) -> None:
        """
        Tidies up any resources used by the handler.

        Sets the `closed` flag. Subclasses should override this to close files,
        network connections, etc., calling `super().close()` at the end.
        """
        # Set closed flag immediately to prevent further processing attempts
        # Acquire lock to ensure synchronization with handle/emit
        with self._lock:
            self.closed = True
        # No resources to clean up in the base class itself.

    def handle_error(self, message: str):
        """
        Handles errors which occur during an emit() call.

        This implementation prints a message to sys.stderr.
        This method can be overridden by subclasses.

        Args:
            message (str): A message describing the error.
        """
        # Use direct print to avoid potential recursive logging errors
        print(f"--- Logging Error in {type(self).__name__} ---", file=sys.stderr, flush=True)
        print(message, file=sys.stderr, flush=True)
        print("--- Traceback ---", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        print("--- End Logging Error ---", file=sys.stderr, flush=True)


class ConsoleHandler(Handler):
    """
    Handles logging records by writing them to a stream (typically console).

    Defaults to writing to `sys.stderr`. Applies ANSI color codes based on the
    log level before writing the formatted message. Also available as `StreamHandler`.

    Attributes:
        stream (StreamType): The output stream (e.g., `sys.stderr`, `sys.stdout`).
    """
    stream: StreamType

    def __init__(
        self,
        level: LevelType = DEBUG,
        formatter: Optional[Formatter] = None,
        stream: Optional[StreamType] = None,
    ):
        """
        Initializes the console handler.

        Args:
            level: The minimum logging level for this handler. Defaults to DEBUG.
            formatter: The formatter instance to use. Defaults to None (a default
                       Formatter will be used in `handle`).
            stream: The output stream. Defaults to `sys.stderr`. If None, uses `sys.stderr`.
        """
        super().__init__(level, formatter)
        # Default to sys.stderr if stream is None
        self.stream = stream if stream is not None else sys.stderr

    def emit(self, level: LogLevel, formatted_message: str) -> None:
        """
        Writes the formatted message to the configured stream, adding color codes.

        The color applied is determined by the `level` argument, based on the
        `ASCIIColors._level_colors` mapping. The output is automatically flushed.

        Args:
            level: The severity level of the log record (used for coloring).
            formatted_message: The pre-formatted log message string.
        """
        # Note: Lock is acquired by the calling handle() method.
        if self.closed:
            return

        # Determine the color based on the log level
        color_code = ASCIIColors._level_colors.get(level, ASCIIColors.color_white) # Default to white

        # Construct the final colored output string
        output = f"{color_code}{formatted_message}{ASCIIColors.color_reset}\n"

        # Check stream validity before writing
        stream_valid = self.stream and hasattr(self.stream, 'write') and not getattr(self.stream, 'closed', False)

        if stream_valid:
            try:
                self.stream.write(output)
                self.stream.flush()
            except Exception:
                # Handle errors during write/flush (e.g., broken pipe)
                self.handle_error(f"Failed to write to stream {getattr(self.stream, 'name', self.stream)}")
        # else: # Optionally log if stream becomes invalid?
        #     pass # Or self.handle_error("Stream is invalid or closed")


    def close(self) -> None:
        """
        Closes the handler and the underlying stream if appropriate.

        The stream is flushed and closed only if it's not `sys.stdout` or `sys.stderr`.
        Calls the base class `close` method.
        """
        # Acquire lock before closing stream, synchronized with emit
        if self.closed:
            return
        try:
            with self._lock:
                # Only close the stream if it's managed by this handler
                # and not one of the standard system streams.
                if self.stream and self.stream not in (sys.stdout, sys.stderr):
                    if hasattr(self.stream, 'flush'):
                        try:
                            self.stream.flush()
                        except Exception:
                            self.handle_error("Error flushing stream during close")
                    if hasattr(self.stream, 'close'):
                        try:
                            self.stream.close()
                        except Exception:
                             self.handle_error("Error closing stream during close")
        finally:
            # Ensure base class close is called even if stream closing fails
            super().close()


# Alias StreamHandler to ConsoleHandler for logging compatibility
StreamHandler = ConsoleHandler
"""Alias for :class:`~ascii_colors.ConsoleHandler`, provided for compatibility
with the standard `logging` module terminology."""


class FileHandler(Handler):
    """
    Handles logging records by writing them to a file.

    Attributes:
        filename (Path): The absolute path to the log file.
        mode (str): The file opening mode ('a' for append, 'w' for write).
        encoding (Optional[str]): The file encoding. Defaults to "utf-8".
        delay (bool): If True, file opening is deferred until the first message
                      is emitted. Defaults to False.
        _stream (Optional[IO[str]]): The internal file stream object.
    """
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
        """
        Initializes the file handler.

        Args:
            filename: The path to the log file (string or Path object).
            mode: File opening mode. Defaults to 'a' (append). 'w' overwrites.
            encoding: File encoding. Defaults to "utf-8". If None, system default is used.
            delay: If True, defer opening the file until the first log record is emitted.
                   Defaults to False (open immediately).
            level: The minimum logging level for this handler. Defaults to DEBUG.
            formatter: The formatter instance to use. Defaults to None (a default
                       Formatter will be used in `handle`).

        Raises:
            ValueError: If the mode is invalid.
            OSError: If the file cannot be opened immediately (and delay is False).
        """
        super().__init__(level, formatter) # Formatter can be None
        if mode not in ('a', 'w'):
            raise ValueError(f"Invalid mode: '{mode}'. Must be 'a' or 'w'.")
        # Resolve the path to ensure it's absolute and normalized
        self.filename = Path(filename).resolve()
        self.mode = mode
        self.encoding = encoding
        self.delay = delay
        self._stream = None

        # Open the file immediately if delay is False
        if not self.delay:
            try:
                self._open_file()
            except Exception as e:
                # Raise the error during initialization if immediate open fails
                raise OSError(f"Failed to open log file {self.filename} immediately: {e}") from e


    def _open_file(self) -> None:
        """
        Opens the log file stream.

        Creates parent directories if they don't exist. Sets the internal `_stream`.
        Called by `__init__` (if `delay` is False) or by `emit` (if `delay` is True).
        Handles potential errors during directory creation or file opening.
        """
        # This method should only be called if the stream needs opening.
        # Check closed status first.
        if self.closed:
            return
        # Check if stream already exists and is usable.
        if self._stream and not getattr(self._stream, 'closed', True):
            return

        try:
            # Ensure the directory exists
            self.filename.parent.mkdir(parents=True, exist_ok=True)
            # Open the file with specified mode and encoding
            self._stream = open(self.filename, self.mode, encoding=self.encoding)
        except Exception as e:
            # If opening fails, log an error to stderr and set stream to None
            self.handle_error(f"Failed to open log file {self.filename}: {e}")
            self._stream = None # Ensure stream is None on failure

    def emit(self, level: LogLevel, formatted_message: str) -> None:
        """
        Writes the formatted message to the log file.

        If `delay` was True and the file isn't open yet, it attempts to open it first.
        Handles potential errors during writing or flushing.

        Args:
            level: The severity level (not used directly by FileHandler emit).
            formatted_message: The pre-formatted log message string.
        """
        # Note: Lock is acquired by the calling handle() method.
        if self.closed:
            return

        # Open the file if delay=True and it's not open yet
        if self.delay and (self._stream is None or getattr(self._stream, 'closed', True)):
            self._open_file() # Attempt to open

        # Check if the stream is valid and open before writing
        if self._stream and not getattr(self._stream, 'closed', True):
            try:
                self._stream.write(formatted_message + "\n")
                self._stream.flush() # Ensure message is written to disk
            except Exception as e:
                # Handle write/flush errors, potentially closing the handler
                self.handle_error(f"Write/flush failed for {self.filename}: {e}")
                # Consider if handler should be automatically closed on write error
                # self.close() # Or rely on external management
        # else: # Stream is not available (failed to open or closed elsewhere)
        #     if not self.delay: # Only complain if it was supposed to be open
        #         self.handle_error(f"Stream {self.filename} is not open for writing.")
        #     # If delay is True, _open_file failure was already handled.


    def close(self) -> None:
        """
        Closes the handler and the underlying file stream.

        Flushes the stream before closing. Calls the base class `close` method.
        """
        # Acquire lock before closing stream, synchronized with emit
        if self.closed:
            return
        try:
            if self._stream and not getattr(self._stream, 'closed', True):
                try:
                    # Flush buffer before closing
                    self.flush()
                except Exception:
                    self.handle_error("Error flushing stream during close")
                try:
                    # Close the file stream
                    self._stream.close()
                except Exception:
                        self.handle_error("Error closing stream during close")
        finally:
                # Mark handler as closed and ensure stream reference is cleared
                self._stream = None
                # Call base class close AFTER attempting resource cleanup
                super().close()


    def flush(self) -> None:
        """
        Flushes the stream buffer, ensuring data is written to the file.
        """
        # Acquire lock for thread safety during flush operation
        with self._lock:
            if self.closed:
                return
            if self._stream and not getattr(self._stream, 'closed', True) and hasattr(self._stream, 'flush'):
                try:
                    self._stream.flush()
                except Exception as e:
                    self.handle_error(f"Flush failed for {self.filename}: {e}")


class RotatingFileHandler(FileHandler):
    """
    Handles logging to a file, automatically rotating it when it reaches a certain size.

    Inherits from `FileHandler` and adds rotation logic based on file size
    and a configured number of backup files.

    When the log file reaches `maxBytes`, it is closed, renamed to `filename.1`,
    existing `filename.1` becomes `filename.2`, and so on, up to `backupCount`.
    A new log file is then opened at the original `filename`.

    Attributes:
        maxBytes (int): The maximum size in bytes a log file can reach before
                        rotation occurs. If 0, rotation never happens based on size.
        backupCount (int): The number of backup files to keep (e.g., `filename.1`,
                           `filename.2`, ...). If 0, the current log file is simply
                           truncated or deleted upon rotation.
    """
    maxBytes: int
    backupCount: int

    def __init__(
        self, filename: Union[str, Path], mode: str = 'a', maxBytes: int = 0, backupCount: int = 0,
        encoding: Optional[str] = "utf-8", delay: bool = False, level: LevelType = DEBUG, formatter: Optional[Formatter] = None
    ):
        """
        Initializes the rotating file handler.

        Args:
            filename: Path to the log file.
            mode: File opening mode ('a' or 'w'). Defaults to 'a'.
            maxBytes: Maximum file size in bytes before rotation. 0 means no size-based rotation.
                      Defaults to 0.
            backupCount: Number of backup files to keep. 0 means overwrite/delete current file.
                         Defaults to 0.
            encoding: File encoding. Defaults to "utf-8".
            delay: Defer file opening until first emit. Defaults to False.
            level: Minimum logging level. Defaults to DEBUG.
            formatter: Formatter instance. Defaults to None.
        """
        # Initialize the base FileHandler
        super().__init__(filename, mode=mode, encoding=encoding, delay=delay, level=level, formatter=formatter)
        if maxBytes < 0:
            raise ValueError("maxBytes must be >= 0")
        if backupCount < 0:
            raise ValueError("backupCount must be >= 0")
        self.maxBytes = maxBytes
        self.backupCount = backupCount

    def emit(self, level: LogLevel, formatted_message: str) -> None:
        """
        Writes the log record to the file and then performs rotation if necessary.

        First, it calls the base class `emit` to write the message.
        Then, it checks if rotation conditions are met (`should_rotate`) and,
        if so, calls `do_rollover`.

        Args:
            level: The severity level (passed to base emit, not used directly here).
            formatted_message: The pre-formatted log message string.
        """
        # Acquire lock (done by handle() which calls this) before any action.
        if self.closed:
            return

        try:
            # 1. Write the message using the base class emit
            super().emit(level, formatted_message) # This handles opening if delayed

            # 2. Check if rotation is needed *after* writing
            if self.should_rotate():
                # Rotation check might fail, handle potential errors
                self.do_rollover()

        except Exception as e:
            self.handle_error(f"Error during emit or rotation check/rollover for {self.filename}: {e}")
            # Consider if handler should close on such errors
            # self.close()


    def should_rotate(self) -> bool:
        """
        Checks if the log file needs to be rotated based on its current size.

        Returns:
            True if `maxBytes > 0` and the current log file size is greater than
            or equal to `maxBytes`. False otherwise, or if the file doesn't exist.
        """
        # Note: Lock is acquired by the calling emit() -> handle() methods.
        if self.closed or self.maxBytes <= 0:
            return False

        # We need to check the actual file size on disk, as the internal stream
        # might have been closed by do_rollover or might not reflect the final size yet.
        try:
            if self.filename.exists():
                # Get file size from the filesystem
                file_size = self.filename.stat().st_size
                return file_size >= self.maxBytes
        except OSError as e:
            # Handle potential errors accessing file stats
            self.handle_error(f"Failed to get size of {self.filename} for rotation check: {e}")
            return False # Cannot determine size, so don't rotate

        # File doesn't exist, no need to rotate
        return False


    def do_rollover(self) -> None:
        """
        Performs the actual log file rotation.

        Handles closing the current stream, renaming files according to `backupCount`,
        and reopening the primary log file stream. Ensures thread safety with the handler's lock.
        """
        # Note: Lock is acquired by the calling emit() -> handle() methods.
        if self.closed:
            return

        # --- Critical Section: File Operations ---
        # We have the lock ensuring emit isn't writing while we rotate.

        # 1. Close the current stream BEFORE filesystem operations
        stream_closed_by_us = False
        if self._stream and not getattr(self._stream, 'closed', True):
            try:
                # Flush just in case, then close
                self._stream.flush()
                self._stream.close()
                stream_closed_by_us = True # We closed it for rotation
            except Exception as e:
                self.handle_error(f"Error closing current log stream {self.filename} before rollover: {e}")
                # Attempt to continue rotation even if close failed, but log the error.
        self._stream = None # Ensure stream reference is cleared regardless

        # 2. Perform Backup Renames
        try:
            # Check rotation condition *again* after closing stream, just to be absolutely sure
            # This check uses the file system size.
            if self.maxBytes > 0 and self.filename.exists() and self.filename.stat().st_size >= self.maxBytes:
                 # Condition still met, proceed with renaming/deletion.

                 if self.backupCount > 0:
                     # Rename existing backups: file.N-1 -> file.N, file.N-2 -> file.N-1, ..., file -> file.1
                     for i in range(self.backupCount - 1, -1, -1): # Iterate down from N-1 to 0
                         source_fn_base = self.filename.name
                         source_fn = self.filename if i == 0 else self.filename.with_name(f"{source_fn_base}.{i}")
                         dest_fn = self.filename.with_name(f"{source_fn_base}.{i + 1}")

                         if source_fn.exists():
                             # If the destination (e.g., file.N) exists, remove it first
                             if dest_fn.exists():
                                 try:
                                     dest_fn.unlink()
                                 except OSError as e_unlink:
                                      self.handle_error(f"Error removing existing backup {dest_fn} during rollover: {e_unlink}")
                                      # Decide whether to proceed or abort rotation here? For now, continue.
                             try:
                                 # Rename source to destination
                                 source_fn.rename(dest_fn)
                             except OSError as e_rename:
                                  self.handle_error(f"Error renaming {source_fn} to {dest_fn} during rollover: {e_rename}")
                                  # If renaming fails, subsequent steps might be inconsistent.

                 else: # backupCount is 0: Just remove the current log file
                     if self.filename.exists():
                         try:
                             self.filename.unlink()
                         except OSError as e_unlink_base:
                             self.handle_error(f"Error removing primary log file {self.filename} (backupCount=0) during rollover: {e_unlink_base}")

            # else: # Rotation condition no longer met after closing stream.
            #     # If we closed the stream unnecessarily, reopen it.
            #     if stream_closed_by_us:
            #         try:
            #             self._open_file()
            #         except Exception as e_reopen:
            #             self.handle_error(f"Error reopening stream {self.filename} after unnecessary close in rollover: {e_reopen}")
            #     return # Exit rollover process

        except Exception as e_fs:
             # Catch broad errors during filesystem operations
             self.handle_error(f"Unexpected error during filesystem operations in rollover for {self.filename}: {e_fs}")
             # Fall through to attempt reopening the primary log file anyway.

        # 3. Re-open the primary log file stream (mode is usually 'a' or 'w')
        # This will create the file if it was deleted/renamed.
        try:
            self._open_file() # Use the standard method to open/reopen
        except Exception as e_reopen_final:
             self.handle_error(f"Failed to reopen primary log file {self.filename} after rollover: {e_reopen_final}")
             self._stream = None # Ensure stream is None if reopen fails

        # --- End Critical Section ---

class handlers:
    """
    Namespace providing access to specific handler classes, mirroring `logging.handlers`.

    This allows accessing handlers like `RotatingFileHandler` using the familiar
    `ascii_colors.handlers.RotatingFileHandler` pattern, enhancing compatibility
    with code written for the standard `logging` module.

    Attributes:
        RotatingFileHandler (Type[RotatingFileHandler]): The rotating file handler class.
        FileHandler (Type[FileHandler]): The standard file handler class.
        StreamHandler (Type[ConsoleHandler]): The console/stream handler class (alias).
    """
    RotatingFileHandler = RotatingFileHandler
    FileHandler = FileHandler
    StreamHandler = StreamHandler # Alias for ConsoleHandler

# --- Main ASCIIColors Class ---
_T = TypeVar('_T') # TypeVar for generic return type in execute_with_animation

class ASCIIColors:
    """
    Provides static methods for colored/styled terminal output (direct printing)
    and manages the global state for the structured logging system.

    **Dual Functionality:**

    1.  **Direct Printing:** Use methods like `ASCIIColors.red()`, `ASCIIColors.bold()`,
        `ASCIIColors.print()`, `ASCIIColors.highlight()` etc., to print directly
        to the console (`sys.stdout` by default) with ANSI styling. These methods
        **bypass** the logging system. They are simple utilities for immediate output.

    2.  **Logging System Management:** This class holds the central list of handlers
        (`_handlers`), the global logging level (`_global_level`), and provides
        methods (`add_handler`, `set_log_level`, etc.) to configure the logging
        system. The logging methods (`ASCIIColors.debug()`, `info()`, etc.) and the
        compatibility layer (`getLogger`, `basicConfig`) all interact with this
        global state.

    **Color and Style Constants:**
    Numerous class attributes define ANSI escape codes for colors and styles
    (e.g., `color_red`, `style_bold`, `color_bg_green`). See the Usage documentation
    for a complete list.
    """
    # --- ANSI Reset Code ---
    color_reset: str = "\u001b[0m"
    """Resets all ANSI colors and styles to terminal default."""

    # --- Text Styles ---
    style_bold: str = "\u001b[1m"; """Bold text style."""
    style_dim: str = "\u001b[2m"; """Dim/faint text style."""
    style_italic: str = "\u001b[3m"; """Italic text style (support varies)."""
    style_underline: str = "\u001b[4m"; """Underlined text style."""
    style_blink: str = "\u001b[5m"; """Blinking text style (support varies, often discouraged)."""
    style_blink_fast: str = "\u001b[6m"; """Fast blinking text style (rarely supported)."""
    style_reverse: str = "\u001b[7m"; """Reverse video (swaps foreground and background)."""
    style_hidden: str = "\u001b[8m"; """Concealed/hidden text style (support varies)."""
    style_strikethrough: str = "\u001b[9m"; """Strikethrough text style."""

    # --- Foreground Colors (Regular Intensity) ---
    color_black: str = "\u001b[30m"; """Black foreground color."""
    color_red: str = "\u001b[31m"; """Red foreground color."""
    color_green: str = "\u001b[32m"; """Green foreground color."""
    color_yellow: str = "\u001b[33m"; """Yellow foreground color."""
    color_blue: str = "\u001b[34m"; """Blue foreground color."""
    color_magenta: str = "\u001b[35m"; """Magenta foreground color."""
    color_cyan: str = "\u001b[36m"; """Cyan foreground color."""
    color_white: str = "\u001b[37m"; """White foreground color."""
    # Common alias using 256-color mode approximation
    color_orange: str = "\u001b[38;5;208m"; """Orange foreground color (256-color approx)."""

    # --- Foreground Colors (Bright/High Intensity) ---
    color_bright_black: str = "\u001b[90m"; """Bright black (often gray) foreground color."""
    color_bright_red: str = "\u001b[91m"; """Bright red foreground color."""
    color_bright_green: str = "\u001b[92m"; """Bright green foreground color."""
    color_bright_yellow: str = "\u001b[93m"; """Bright yellow foreground color."""
    color_bright_blue: str = "\u001b[94m"; """Bright blue foreground color."""
    color_bright_magenta: str = "\u001b[95m"; """Bright magenta foreground color."""
    color_bright_cyan: str = "\u001b[96m"; """Bright cyan foreground color."""
    color_bright_white: str = "\u001b[97m"; """Bright white foreground color."""

    # --- Background Colors (Regular Intensity) ---
    color_bg_black: str = "\u001b[40m"; """Black background color."""
    color_bg_red: str = "\u001b[41m"; """Red background color."""
    color_bg_green: str = "\u001b[42m"; """Green background color."""
    color_bg_yellow: str = "\u001b[43m"; """Yellow background color."""
    color_bg_blue: str = "\u001b[44m"; """Blue background color."""
    color_bg_magenta: str = "\u001b[45m"; """Magenta background color."""
    color_bg_cyan: str = "\u001b[46m"; """Cyan background color."""
    color_bg_white: str = "\u001b[47m"; """White background color."""
    color_bg_orange: str = "\u001b[48;5;208m"; """Orange background color (256-color approx)."""

    # --- Background Colors (Bright/High Intensity) ---
    color_bg_bright_black: str = "\u001b[100m"; """Bright black (gray) background color."""
    color_bg_bright_red: str = "\u001b[101m"; """Bright red background color."""
    color_bg_bright_green: str = "\u001b[102m"; """Bright green background color."""
    color_bg_bright_yellow: str = "\u001b[103m"; """Bright yellow background color."""
    color_bg_bright_blue: str = "\u001b[104m"; """Bright blue background color."""
    color_bg_bright_magenta: str = "\u001b[105m"; """Bright magenta background color."""
    color_bg_bright_cyan: str = "\u001b[106m"; """Bright cyan background color."""
    color_bg_bright_white: str = "\u001b[107m"; """Bright white background color."""

    # --- Global Logging State (Class Attributes) ---
    _handlers: List[Handler] = []
    """Internal list holding all globally configured Handler instances."""
    _global_level: LogLevel = LogLevel.WARNING
    """Internal global minimum log level. Messages below this level are discarded
    before being passed to handlers. Defaults to WARNING."""
    _handler_lock: Lock = Lock()
    """A lock to ensure thread-safe modification of the global _handlers list
    and access during logging dispatch."""
    _basicConfig_called: bool = False
    """Internal flag to track if basicConfig() has been called. Prevents
    multiple default configurations unless force=True is used."""
    _context: threading.local = threading.local()
    """Thread-local storage for contextual data added via set_context() or context()."""

    # Default colors used by ConsoleHandler for different log levels.
    _level_colors: Dict[LogLevel, str] = {
        LogLevel.DEBUG: style_dim + color_white, # Dim white for debug
        LogLevel.INFO: color_bright_blue,        # Bright blue for info
        LogLevel.WARNING: color_bright_yellow,   # Bright yellow for warning
        LogLevel.ERROR: color_bright_red,        # Bright red for error
        LogLevel.CRITICAL: style_bold + color_bright_red, # Bold bright red for critical
    }
    """Mapping of LogLevel enums to default ANSI color codes used by ConsoleHandler."""

    # --- Logging Configuration Methods ---
    @classmethod
    def set_log_level(cls, level: LevelType) -> None:
        """
        Sets the *global* minimum log level for the entire logging system.

        Messages with a severity lower than this level will be ignored and not
        processed by any handlers.

        Args:
            level: The minimum log level (LogLevel enum or int) to set globally.
        """
        cls._global_level = LogLevel(level if isinstance(level, LogLevel) else int(level))

    @classmethod
    def add_handler(cls, handler: Handler) -> None:
        """
        Adds a Handler instance to the global list of handlers.

        All log records that pass the global level filter will be processed by
        this handler (subject to the handler's own level filter).

        Args:
            handler: The Handler instance to add.
        """
        with cls._handler_lock:
            if handler not in cls._handlers:
                cls._handlers.append(handler)

    @classmethod
    def remove_handler(cls, handler: Handler) -> None:
        """
        Removes a specific Handler instance from the global list.

        Args:
            handler: The Handler instance to remove. If the handler is not found,
                     this method does nothing.
        """
        with cls._handler_lock:
            try:
                cls._handlers.remove(handler)
            except ValueError:
                # Handler wasn't in the list, ignore
                pass

    @classmethod
    def clear_handlers(cls) -> None:
        """
        Removes all configured handlers from the global list.

        Note: This does *not* automatically call the `close()` method on the
        removed handlers. If handlers manage resources (like files), they should
        be closed explicitly or via `basicConfig(force=True)`.
        """
        # Does not close handlers, requires explicit close or basicConfig(force=True)
        with cls._handler_lock:
            cls._handlers.clear()

    @classmethod
    def set_log_file(cls, path: Union[str, Path], level: LevelType = DEBUG, formatter: Optional[Formatter] = None) -> None:
        """
        [DEPRECATED] Adds a FileHandler for the specified path.

        Warning: This method is deprecated. Use `add_handler(FileHandler(...))` instead
        for better clarity and consistency.

        Args:
            path: Path to the log file.
            level: Minimum level for this file handler. Defaults to DEBUG.
            formatter: Formatter to use for this file handler. Defaults to None.
        """
        cls.warning("ASCIIColors.set_log_file is DEPRECATED. Use ASCIIColors.add_handler(FileHandler(...)) instead.")
        cls.add_handler(FileHandler(path, level=level, formatter=formatter))

    @classmethod
    def set_template(cls, level: LogLevel, template: str) -> None:
        """
        [DEPRECATED] Sets a format template (string) for a specific level.

        Warning: This method is deprecated and its functionality was limited.
        Use `handler.setFormatter(Formatter(...))` on specific handler instances
        to control formatting. It does not work as expected with the current
        handler/formatter model.
        """
        cls.warning("ASCIIColors.set_template is DEPRECATED and may not function as expected. Use handler.setFormatter() instead.")
        # Original implementation likely modified handler formatters directly,
        # which is fragile. Current model requires explicit formatter assignment.
        pass # No longer functional in the intended way.

    # --- Context Management ---
    @classmethod
    def set_context(cls, **kwargs: Any) -> None:
        """
        Sets key-value pairs in the current thread's logging context.

        These context variables will be included in the `log_record` dictionary
        passed to formatters, allowing them to be included in log messages
        (if the format string uses them, e.g., `{request_id}`).

        Example:
            >>> ASCIIColors.set_context(user_id="user123", session_id="abc")
            >>> logger.info("User action performed.")
            # If formatter includes {user_id}, it will appear in the output.

        Args:
            **kwargs: Keyword arguments representing the context variables to set.
        """
        # `threading.local()` ensures attributes are specific to the current thread
        for key, value in kwargs.items():
            setattr(cls._context, key, value)

    @classmethod
    def clear_context(cls, *args: str) -> None:
        """
        Clears specified keys (or all keys) from the current thread's logging context.

        Args:
            *args: Optional names of context keys to remove. If no arguments are
                   provided, all context variables currently set for the thread
                   (that don't start with '_') are removed.
        """
        context_vars = vars(cls._context)
        # Determine which keys to clear
        keys_to_clear = args if args else [k for k in context_vars if not k.startswith("_")]
        for key in keys_to_clear:
             # Check if the attribute exists before deleting (it might have been cleared already)
             if hasattr(cls._context, key):
                 try:
                     delattr(cls._context, key)
                 except AttributeError:
                     # Silently ignore if deleted by another thread/clear call concurrently
                     pass

    @classmethod
    @contextmanager
    def context(cls, **kwargs: Any) -> ContextManager[None]:
        """
        Context manager to temporarily add thread-local context variables.

        Sets the provided keyword arguments as context variables upon entering
        the `with` block and restores the previous context state (removing added
        keys or restoring previous values) upon exiting the block, ensuring
        context isolation.

        Example:
            >>> with ASCIIColors.context(request_id="req-001"):
            ...     logger.info("Processing request.") # Log will include request_id
            >>> # request_id is now removed from context outside the block

        Args:
            **kwargs: Keyword arguments representing the context variables to set
                      temporarily within the `with` block.

        Yields:
            None
        """
        previous_values: Dict[str, Any] = {} # Store original values if keys existed
        added_keys: set[str] = set()       # Track keys added by this context manager

        try:
            # Set new context variables, remembering previous state
            for key, value in kwargs.items():
                if hasattr(cls._context, key):
                    # Key exists, store its current value
                    previous_values[key] = getattr(cls._context, key)
                else:
                    # Key is new, mark it for removal later
                    added_keys.add(key)
                # Set the new value for the duration of the block
                setattr(cls._context, key, value)
            yield # Execute the code inside the 'with' block
        finally:
            # Restore previous context state carefully
            for key, value in kwargs.items(): # Iterate over keys we intended to modify
                if key in added_keys:
                    # If we added this key, try to remove it
                    if hasattr(cls._context, key): # Check if it still exists
                         try:
                             delattr(cls._context, key)
                         except AttributeError: pass # Ignore if already gone
                elif key in previous_values:
                     # If the key existed before, restore its original value
                     setattr(cls._context, key, previous_values[key])
                # Else: Key didn't exist before and wasn't added by us (e.g., cleared
                # by another thread within the block) - do nothing.


    @classmethod
    def get_thread_context(cls) -> Dict[str, Any]:
        """
        Returns a dictionary containing the current thread's logging context variables.

        This is used internally by formatters but can also be called manually for
        debugging or inspection.

        Returns:
            A dictionary of the key-value pairs set via `set_context` or `context`
            for the currently executing thread.
        """
        # Return a dictionary view of the thread-local storage, excluding internal attributes.
        return {k: v for k, v in vars(cls._context).items() if not k.startswith("_")}

    # --- Core Logging Method (Internal) ---
    @classmethod
    def _log(
        cls, level: LogLevel, message: str, args: tuple = (),
        exc_info: ExcInfoType = None, logger_name: str = 'ASCIIColors', **kwargs: Any
    ) -> None:
        """
        Internal core method to process and dispatch a single log record.

        This method is called by public logging methods (`debug`, `info`, etc.)
        and by the `_AsciiLoggerAdapter` used by `getLogger`. It performs level
        checking, message formatting, exception info processing, context gathering,
        and dispatching to all configured handlers.

        Args:
            level: The severity level of the log record (LogLevel enum).
            message: The main log message string (can be a format string).
            args: Positional arguments for %-style formatting of the `message`.
            exc_info: Exception information (None, True, exception instance, or tuple).
            logger_name: The name of the logger originating this record.
            **kwargs: Additional keyword arguments passed from the logging call,
                      often used for 'extra' context data.
        """
        # --- Auto-configure Default Handler ---
        # If no handlers are configured and basicConfig hasn't been called,
        # add a default ConsoleHandler to stderr.
        with cls._handler_lock: # Check handler list safely
            if not cls._handlers and not cls._basicConfig_called:
                 default_handler = ConsoleHandler(level=cls._global_level) # Respect global level
                 # Assign a default formatter if none exists? No, let handle() do it.
                 # default_handler.setFormatter(Formatter()) # Default % style
                 cls._handlers.append(default_handler)
                 # Avoid setting _basicConfig_called = True here, only basicConfig sets it.

        # --- Global Level Filtering ---
        if level < cls._global_level:
            return # Message severity is below the global threshold

        # --- Timestamp ---
        timestamp: datetime = datetime.now()

        # --- Message Formatting (% args) ---
        final_message: str = message
        if args: # Handle %-style argument substitution if args are provided
            try:
                final_message = message % args
            except TypeError:
                # Fallback if message wasn't a format string or args mismatch
                final_message = f"{message} {args}" # Append args representation

        # --- Exception Information Processing ---
        # Convert various ExcInfoType inputs into the standard (type, value, tb) tuple
        # or None if no valid exception info is provided.
        final_exc_info: Optional[Tuple[Optional[Type[BaseException]], Optional[BaseException], Any]] = None
        processed_exc_info: Optional[Tuple[Type[BaseException], BaseException, Any]] = None
        if exc_info:
            if isinstance(exc_info, BaseException):
                # If an exception instance is passed directly
                processed_exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            elif isinstance(exc_info, tuple) and len(exc_info) == 3:
                # If a pre-formed (type, value, tb) tuple is passed
                processed_exc_info = cast(Tuple[Type[BaseException], BaseException, Any], exc_info)
            elif exc_info is True:
                # If True, capture current exception context
                processed_exc_info = cast(Tuple[Type[BaseException], BaseException, Any], sys.exc_info())

            # Ensure we only proceed if a valid exception was found/passed
            if processed_exc_info and processed_exc_info[0] is not None:
                final_exc_info = processed_exc_info

        # --- Dispatch to Handlers ---
        # Iterate over a *copy* of the handlers list to avoid issues if the list
        # is modified concurrently (e.g., by another thread calling add/remove handler).
        current_handlers: List[Handler]
        with cls._handler_lock:
            current_handlers = cls._handlers[:]

        for handler in current_handlers:
            try:
                # Let each handler process the record (applies handler level filter and formatter)
                handler.handle(level, final_message, timestamp, final_exc_info, logger_name=logger_name, **kwargs)
            except Exception as e:
                # --- PANIC ---: A handler itself failed. Log directly to stderr.
                try:
                    # Use direct print to avoid recursive logging failure
                    cls.print(
                        f"--- PANIC: Handler Error in {type(handler).__name__} ---",
                        color=cls.color_bright_red, file=sys.stderr, flush=True
                    )
                    cls.print(f"Failed Record: Level={level.name} Logger={logger_name} Msg='{final_message}'",
                              color=cls.color_bright_red, file=sys.stderr, flush=True)
                    cls.print(f"Error: {type(e).__name__} - {e}", color=cls.color_bright_red, file=sys.stderr, flush=True)
                    cls.print(f"Traceback:\n{get_trace_exception(e)}", color=cls.color_bright_red, file=sys.stderr, flush=True)
                    cls.print("--- End Handler Error ---", color=cls.color_bright_red, file=sys.stderr, flush=True)
                except Exception as panic_e:
                     # Absolute fallback if even stderr printing fails
                     print(f"PANIC FALLBACK: Handler failed AND stderr print failed: {panic_e}", file=sys.stderr, flush=True)


    # --- Semantic Logging Methods ---
    # These are the public methods users call to log messages via the ASCIIColors class.
    # They simply delegate to the internal _log method with the appropriate level.

    @classmethod
    def debug(cls, message: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level DEBUG using the configured logging system."""
        cls._log(LogLevel.DEBUG, message, args, **kwargs)

    @classmethod
    def info(cls, message: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level INFO using the configured logging system."""
        cls._log(LogLevel.INFO, message, args, **kwargs)

    @classmethod
    def warning(cls, message: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level WARNING using the configured logging system."""
        cls._log(LogLevel.WARNING, message, args, **kwargs)

    @classmethod
    def error(cls, message: str, *args: Any, exc_info: ExcInfoType = None, **kwargs: Any) -> None:
        """Logs a message with level ERROR using the configured logging system.

        Args:
            message: The log message (can be a format string).
            *args: Arguments for %-formatting of the message.
            exc_info: Optional exception information to include (None, True, Exception, tuple).
            **kwargs: Extra context data.
        """
        cls._log(LogLevel.ERROR, message, args, exc_info=exc_info, **kwargs)

    @classmethod
    def critical(cls, message: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level CRITICAL using the configured logging system."""
        cls._log(LogLevel.CRITICAL, message, args, **kwargs)


    # --- Direct Console Print Methods (Bypass Logging System) ---
    # These methods provide a simple way to print colored/styled text directly
    # to a stream (usually the console) without involving handlers or formatters.

    @staticmethod
    def print(
        text: str,
        color: str = color_white,
        style: str = "",
        background: str = "", # Added background parameter
        end: str = "\n",
        flush: bool = False,
        file: StreamType = sys.stdout
    ) -> None:
        """
        Prints text directly to a stream with specified color, style, and background.

        This method bypasses the entire logging system (`handlers`, `formatters`,
        `levels`, `context`). It's a direct wrapper around the built-in `print`.

        Args:
            text: The string to print.
            color: ANSI foreground color code (e.g., `ASCIIColors.color_red`).
                   Defaults to `color_white`.
            style: ANSI style code(s) (e.g., `ASCIIColors.style_bold`). Multiple
                   styles can be concatenated (e.g., `style_bold + style_underline`).
                   Defaults to "".
            background: ANSI background color code (e.g., `ASCIIColors.color_bg_blue`).
                        Defaults to "".
            end: String appended after the text. Defaults to newline (`\\n`).
            flush: Whether to forcibly flush the stream. Defaults to False.
            file: The stream to write to. Defaults to `sys.stdout`.
        """
        # Construct the ANSI sequence prefix
        prefix = f"{style}{background}{color}"
        # Print the styled text followed by a reset code
        print(f"{prefix}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    # --- Direct Print - Status ---
    @staticmethod
    def success(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in green color."""
        ASCIIColors.print(text, ASCIIColors.color_green, "", "", end, flush, file)

    @staticmethod
    def fail(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in red color."""
        ASCIIColors.print(text, ASCIIColors.color_red, "", "", end, flush, file)

    # --- Direct Print - Foreground Colors ---
    @staticmethod
    def black(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in black color."""
        ASCIIColors.print(text, ASCIIColors.color_black, "", "", end, flush, file)
    @staticmethod
    def red(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in red color."""
        ASCIIColors.print(text, ASCIIColors.color_red, "", "", end, flush, file)
    @staticmethod
    def green(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in green color."""
        ASCIIColors.print(text, ASCIIColors.color_green, "", "", end, flush, file)
    @staticmethod
    def yellow(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in yellow color."""
        ASCIIColors.print(text, ASCIIColors.color_yellow, "", "", end, flush, file)
    @staticmethod
    def blue(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in blue color."""
        ASCIIColors.print(text, ASCIIColors.color_blue, "", "", end, flush, file)
    @staticmethod
    def magenta(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in magenta color."""
        ASCIIColors.print(text, ASCIIColors.color_magenta, "", "", end, flush, file)
    @staticmethod
    def cyan(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in cyan color."""
        ASCIIColors.print(text, ASCIIColors.color_cyan, "", "", end, flush, file)
    @staticmethod
    def white(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in white color."""
        ASCIIColors.print(text, ASCIIColors.color_white, "", "", end, flush, file)
    @staticmethod
    def orange(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in orange color (256-color approx)."""
        ASCIIColors.print(text, ASCIIColors.color_orange, "", "", end, flush, file)
    @staticmethod
    def bright_black(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in bright black (gray) color."""
        ASCIIColors.print(text, ASCIIColors.color_bright_black, "", "", end, flush, file)
    @staticmethod
    def bright_red(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in bright red color."""
        ASCIIColors.print(text, ASCIIColors.color_bright_red, "", "", end, flush, file)
    @staticmethod
    def bright_green(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in bright green color."""
        ASCIIColors.print(text, ASCIIColors.color_bright_green, "", "", end, flush, file)
    @staticmethod
    def bright_yellow(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in bright yellow color."""
        ASCIIColors.print(text, ASCIIColors.color_bright_yellow, "", "", end, flush, file)
    @staticmethod
    def bright_blue(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in bright blue color."""
        ASCIIColors.print(text, ASCIIColors.color_bright_blue, "", "", end, flush, file)
    @staticmethod
    def bright_magenta(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in bright magenta color."""
        ASCIIColors.print(text, ASCIIColors.color_bright_magenta, "", "", end, flush, file)
    @staticmethod
    def bright_cyan(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in bright cyan color."""
        ASCIIColors.print(text, ASCIIColors.color_bright_cyan, "", "", end, flush, file)
    @staticmethod
    def bright_white(text: str, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in bright white color."""
        ASCIIColors.print(text, ASCIIColors.color_bright_white, "", "", end, flush, file)

    # --- Direct Print - Background Colors ---
    @staticmethod
    def print_with_bg(text: str, color: str = color_white, background: str = "", style: str = "", end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """
        [DEPRECATED] Helper to print with background; use `ASCIIColors.print()` with `background` parameter instead.
        Directly prints text with specified foreground color, background color, and style.
        """
        # This method is now redundant with the `background` parameter in `print`.
        # Kept for backward compatibility, simply delegates to `print`.
        ASCIIColors.print(text, color, style, background, end, flush, file)

    @staticmethod
    def bg_black(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a black background."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_black, end, flush, file)
    @staticmethod
    def bg_red(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a red background."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_red, end, flush, file)
    @staticmethod
    def bg_green(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a green background."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_green, end, flush, file)
    @staticmethod
    def bg_yellow(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a yellow background (default text: black)."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_yellow, end, flush, file)
    @staticmethod
    def bg_blue(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a blue background."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_blue, end, flush, file)
    @staticmethod
    def bg_magenta(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a magenta background."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_magenta, end, flush, file)
    @staticmethod
    def bg_cyan(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a cyan background."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_cyan, end, flush, file)
    @staticmethod
    def bg_white(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a white background (default text: black)."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_white, end, flush, file)
    @staticmethod
    def bg_orange(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with an orange background (256-color approx, default text: black)."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_orange, end, flush, file)
    @staticmethod
    def bg_bright_black(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a bright black (gray) background."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_bright_black, end, flush, file)
    @staticmethod
    def bg_bright_red(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a bright red background."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_bright_red, end, flush, file)
    @staticmethod
    def bg_bright_green(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a bright green background (default text: black)."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_bright_green, end, flush, file)
    @staticmethod
    def bg_bright_yellow(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a bright yellow background (default text: black)."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_bright_yellow, end, flush, file)
    @staticmethod
    def bg_bright_blue(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a bright blue background."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_bright_blue, end, flush, file)
    @staticmethod
    def bg_bright_magenta(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a bright magenta background."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_bright_magenta, end, flush, file)
    @staticmethod
    def bg_bright_cyan(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a bright cyan background (default text: black)."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_bright_cyan, end, flush, file)
    @staticmethod
    def bg_bright_white(text: str, color: str = color_black, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text with a bright white background (default text: black)."""
        ASCIIColors.print(text, color, "", ASCIIColors.color_bg_bright_white, end, flush, file)

    # --- Direct Print - Styles ---
    @staticmethod
    def bold(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in bold style."""
        ASCIIColors.print(text, color, ASCIIColors.style_bold, "", end, flush, file)
    @staticmethod
    def dim(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in dim style."""
        ASCIIColors.print(text, color, ASCIIColors.style_dim, "", end, flush, file)
    @staticmethod
    def italic(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in italic style."""
        ASCIIColors.print(text, color, ASCIIColors.style_italic, "", end, flush, file)
    @staticmethod
    def underline(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in underline style."""
        ASCIIColors.print(text, color, ASCIIColors.style_underline, "", end, flush, file)
    @staticmethod
    def blink(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in blinking style."""
        ASCIIColors.print(text, color, ASCIIColors.style_blink, "", end, flush, file)
    @staticmethod
    def reverse(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in reverse video style."""
        ASCIIColors.print(text, color, ASCIIColors.style_reverse, "", end, flush, file)
    @staticmethod
    def hidden(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in hidden style."""
        ASCIIColors.print(text, color, ASCIIColors.style_hidden, "", end, flush, file)
    @staticmethod
    def strikethrough(text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """Directly prints text in strikethrough style."""
        ASCIIColors.print(text, color, ASCIIColors.style_strikethrough, "", end, flush, file)


    # --- Utility & Direct Console Manipulation Methods ---
    @staticmethod
    def multicolor(texts: List[str], colors: List[str], end: str = "\n", flush: bool = False, file: StreamType = sys.stdout) -> None:
        """
        Directly prints multiple text segments with corresponding colors on one line.

        This method bypasses the logging system. Each text segment in `texts` is
        printed using the corresponding color code from `colors`. A single reset
        code is added at the very end.

        Args:
            texts: A list of strings to print sequentially.
            colors: A list of ANSI color/style codes, corresponding to `texts`. Must
                    have the same length as `texts`.
            end: String appended after all segments. Defaults to newline (`\\n`).
            flush: Whether to forcibly flush the stream. Defaults to False.
            file: The stream to write to. Defaults to `sys.stdout`.
        """
        if len(texts) != len(colors):
            raise ValueError("Length of texts and colors lists must be equal for multicolor.")

        output_parts = []
        for text, color in zip(texts, colors):
            # Apply color to each part, but don't reset yet
            output_parts.append(f"{color}{text}")

        # Join parts, add final reset, and print
        print("".join(output_parts) + ASCIIColors.color_reset, end=end, flush=flush, file=file)

    @staticmethod
    def highlight(
        text: str,
        subtext: Union[str, List[str]],
        color: str = color_white,
        highlight_color: str = color_yellow,
        whole_line: bool = False,
        end: str = "\n",
        flush: bool = False,
        file: StreamType = sys.stdout
    ) -> None:
        """
        Directly prints text, highlighting occurrences of subtext(s).

        This method bypasses the logging system. It searches for `subtext` within
        `text` and applies `highlight_color` to the matches.

        Args:
            text: The main string to print.
            subtext: The string or list of strings to highlight within `text`.
            color: The default ANSI color code for non-highlighted parts of `text`.
                   Defaults to `color_white`.
            highlight_color: The ANSI color/style code to apply to matched `subtext`.
                             Defaults to `color_yellow`. Can include styles/backgrounds.
            whole_line: If True, highlight the entire line if any part of `subtext`
                        is found in it. If False (default), only highlight the
                        matched `subtext` itself.
            end: String appended after the text. Defaults to newline (`\\n`).
            flush: Whether to forcibly flush the stream. Defaults to False.
            file: The stream to write to. Defaults to `sys.stdout`.
        """
        subtexts = [subtext] if isinstance(subtext, str) else subtext
        output: str = ""

        if whole_line:
            # Process line by line
            lines = text.splitlines(keepends=True) # Keep line endings for accurate reconstruction
            for line in lines:
                line_stripped = line.rstrip('\r\n') # Check content without endings
                should_highlight_line = any(st in line_stripped for st in subtexts)
                if should_highlight_line:
                    # Apply highlight color to the whole line (content part) + reset + original ending
                    output += f"{highlight_color}{line_stripped}{ASCIIColors.color_reset}{line[len(line_stripped):]}"
                else:
                    # Apply default color + reset + original ending
                    output += f"{color}{line_stripped}{ASCIIColors.color_reset}{line[len(line_stripped):]}"
        else:
            # Inline highlighting: Replace occurrences
            # Start with the default color applied to the whole text
            processed_text = text
            # Iterate through subtexts and replace them with highlighted versions
            # This simple replace might have issues with overlapping subtexts.
            # A more robust approach would use regex or iterative find/replace.
            for st in subtexts:
                # Construct replacement: highlight_code + subtext + original_color_code
                # We need the original color code *after* the highlight to revert back.
                replacement = f"{highlight_color}{st}{ASCIIColors.color_reset}{color}"
                processed_text = processed_text.replace(st, replacement)
            # Final output: original color prefix + processed text + reset
            output = f"{color}{processed_text}{ASCIIColors.color_reset}"

        # Use the built-in print to output the result directly
        print(output, end=end, flush=flush, file=file)


    @staticmethod
    def activate(color_or_style: str, file: StreamType = sys.stdout) -> None:
        """
        Activates a specific ANSI color or style directly on the stream.

        This method bypasses the logging system. It prints the given ANSI code
        without any text or reset code afterwards. Useful for setting a style
        that persists across multiple subsequent prints until `reset()` is called.

        Args:
            color_or_style: The ANSI code string to activate (e.g., `ASCIIColors.color_red`).
            file: The stream to write to. Defaults to `sys.stdout`.
        """
        print(f"{color_or_style}", end="", flush=True, file=file)

    @staticmethod
    def reset(file: StreamType = sys.stdout) -> None:
        """
        Resets all active ANSI colors and styles directly on the stream.

        This method bypasses the logging system. It prints the `color_reset` code.

        Args:
            file: The stream to write to. Defaults to `sys.stdout`.
        """
        print(ASCIIColors.color_reset, end="", flush=True, file=file)

    @staticmethod
    def resetAll(file: StreamType = sys.stdout) -> None: # Alias with file arg
        """Alias for `reset()`."""
        ASCIIColors.reset(file=file)


    @staticmethod
    def execute_with_animation(
        pending_text: str, func: Callable[..., _T], *args: Any, color: Optional[str] = None, **kwargs: Any
    ) -> _T:
        """
        Executes a function while displaying a console spinner animation.

        This utility uses **direct printing** (`ASCIIColors.print`) to show and
        update the spinner animation on `sys.stdout`. It runs the provided `func`
        in a separate thread. Once the function completes (or raises an exception),
        the animation stops, a final status (success ✓ or failure ✗) is printed,
        and the function's result is returned or its exception is re-raised.

        Note: Log messages generated *within* the executed `func` will still go
        through the standard logging system and appear separately from the spinner line.

        Args:
            pending_text: The text message to display next to the spinner (e.g., "Processing...").
            func: The callable (function or method) to execute.
            *args: Positional arguments to pass to `func`.
            color: Optional ANSI color code for the `pending_text`. Defaults to yellow.
            **kwargs: Keyword arguments to pass to `func`.

        Returns:
            The return value of the executed `func`.

        Raises:
            Exception: Re-raises any exception raised by the executed `func`.

        Example:
            >>> result = ASCIIColors.execute_with_animation("Loading data...", time.sleep, 2)
            # Displays "Loading data... [spinner]" for 2 seconds, then success status.
        """
        animation = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏" # Spinner characters
        stop_event = threading.Event()
        result: List[Optional[_T]] = [None] # Use list to pass result out of thread
        exception: List[Optional[BaseException]] = [None] # Use list for exception
        thread_lock = Lock() # To safely access result/exception lists

        text_color = color if color is not None else ASCIIColors.color_yellow
        success_symbol = "✓"
        failure_symbol = "✗"

        def animate() -> None:
            """Target function for the animator thread."""
            idx = 0
            while not stop_event.is_set():
                # Use direct print for the animation frame
                # '\r' moves cursor to beginning of line for overwrite
                ASCIIColors.print(f"\r{text_color}{pending_text} {animation[idx % len(animation)]}",
                                  color="", style="", end="", flush=True, file=sys.stdout)
                idx += 1
                time.sleep(0.1)
            # Clear the animation line after stopping
            # Overwrite with pending text and spaces, then reset color
            clear_line = f"\r{text_color}{pending_text}{ASCIIColors.color_reset}{' ' * (len(animation[0])+5)}"
            ASCIIColors.print(clear_line, color="", style="", end="\r", flush=True, file=sys.stdout)


        def target() -> None:
            """Target function for the worker thread executing func."""
            try:
                res = func(*args, **kwargs)
                # Store result only on success
                with thread_lock:
                    result[0] = res
            except Exception as e_inner:
                # Store exception if func fails
                with thread_lock:
                    exception[0] = e_inner
            finally:
                # Signal the animator thread to stop
                stop_event.set()

        # Create and start threads
        worker = threading.Thread(target=target)
        animator = threading.Thread(target=animate)

        worker.start()
        animator.start()

        # Wait for the worker thread (func execution) to complete
        worker.join()
        # Ensure the animator thread also finishes (it checks stop_event)
        stop_event.set() # Belt-and-suspenders signal
        animator.join()

        # Safely get result/exception after threads complete
        with thread_lock:
            final_exception = exception[0]
            final_result = result[0]

        # Determine final status symbol and color
        final_symbol, final_color = (failure_symbol, ASCIIColors.color_red) if final_exception else (success_symbol, ASCIIColors.color_green)

        # Print the final status line, overwriting the pending text/spinner
        status_line = f"\r{text_color}{pending_text} {final_color}{final_symbol}{ASCIIColors.color_reset}          " # Extra spaces to clear line
        ASCIIColors.print(status_line, color="", style="", flush=True, file=sys.stdout)
        # Print a newline to move to the next line for subsequent output
        ASCIIColors.print("", color="", style="", file=sys.stdout)

        # Re-raise exception if the function failed
        if final_exception:
            raise final_exception

        # Return the result (must cast as TypeVar doesn't guarantee non-None)
        return cast(_T, final_result)


# --- Global convenience function ---
def trace_exception(ex: BaseException) -> None:
    """
    Logs the traceback of a given exception using the configured logging system.

    This is a convenience function that calls `ASCIIColors.error` with the
    exception type as part of the message and sets `exc_info` to the exception
    instance, ensuring the traceback is captured and formatted by handlers.

    Args:
        ex: The exception instance to log.
    """
    # Uses the logging system, not direct print
    ASCIIColors.error(f"Exception Traceback ({type(ex).__name__})", exc_info=ex)

# ==============================
# --- Menu System Classes ---
# ==============================

class MenuItem:
    """Internal representation of an item within a Menu (unchanged)."""
    def __init__(
        self,
        text: str,
        item_type: str, # 'action', 'submenu', 'back', 'quit'
        target: Union[ActionCallable, 'Menu', None], # Target can be None for back/quit
    ):
        self.text = text
        self.type = item_type
        self.target = target
        # self.key removed as we use arrow navigation

class Menu:
    """
    Builds and runs interactive, styled command-line menus with arrow-key navigation.

    Leverages ASCIIColors for styling and provides an easy way to define
    actions and navigate submenus using Up/Down arrows and Enter.

    Example:
        >>> main_menu = Menu("Welcome!")
        >>> sub_menu = Menu("Options", parent=main_menu)
        >>> def say_hello(): ASCIIColors.green("Hello there!")
        >>> main_menu.add_action("Say Hello", say_hello)
        >>> main_menu.add_submenu("Go to Options", sub_menu)
        >>> sub_menu.add_action("Option 1", lambda: print("Ran option 1"))
        >>> main_menu.run() # Start the interactive menu
    """
    def __init__(
        self,
        title: str,
        parent: Optional['Menu'] = None,
        clear_screen_on_run: bool = True,
        prompt_text: str = "Use ↑/↓ arrows, Enter to select.", # Updated prompt
        invalid_choice_text: str = "Invalid key.", # Should not happen with arrow keys
        title_color: str = ASCIIColors.color_bright_yellow,
        title_style: str = ASCIIColors.style_bold,
        item_color: str = ASCIIColors.color_cyan,
        item_style: str = "",
        selected_color: str = ASCIIColors.color_black, # Text color when selected
        selected_background: str = ASCIIColors.color_bg_cyan, # BG color when selected
        selected_style: str = "",
        selected_prefix: str = "> ",
        unselected_prefix: str = "  ",
        prompt_color: str = ASCIIColors.color_green,
        error_color: str = ASCIIColors.color_red,
        hide_cursor: bool = True, # Option to hide cursor during menu interaction
        file: StreamType = sys.stdout, # Where to print the menu
    ):
        """
        Initializes a new Menu instance.

        Args:
            title: The text displayed as the menu title.
            parent: Optional reference to the parent menu (for 'Back' navigation).
            clear_screen_on_run: If True, clears the terminal before showing the menu.
            prompt_text: Informational text displayed below the menu.
            invalid_choice_text: Message shown for invalid input (less likely now).
            title_color: ANSI color code for the title.
            title_style: ANSI style code for the title.
            item_color: ANSI color code for non-selected menu item text.
            item_style: ANSI style code for non-selected menu item text.
            selected_color: ANSI color code for selected menu item text.
            selected_background: ANSI background color for selected menu item.
            selected_style: ANSI style code for selected menu item.
            selected_prefix: String prefix for the selected item (e.g., '> ').
            unselected_prefix: String prefix for non-selected items (e.g., '  ').
            prompt_color: ANSI color code for the prompt text.
            error_color: ANSI color code for error messages.
            hide_cursor: If True, attempts to hide the terminal cursor while the menu is active.
            file: The stream to print the menu output to (default: sys.stdout).
        """
        self.title = title
        self.parent = parent
        self.items: List[MenuItem] = []
        self.clear_screen_on_run = clear_screen_on_run
        self.prompt_text = prompt_text
        self.invalid_choice_text = invalid_choice_text # Kept for consistency
        self.file = file
        self.hide_cursor = hide_cursor

        # Store styling options
        self.styles = {
            "title": title_style + title_color,
            "item": item_style + item_color,
            "selected": selected_style + selected_color + selected_background,
            "prompt": prompt_color,
            "error": error_color,
        }
        self.prefixes = {
            "selected": selected_prefix,
            "unselected": unselected_prefix,
        }

    def add_action(self, text: str, action: ActionCallable) -> 'Menu':
        """
        Adds an action item to the menu. Selecting this item calls the `action` function.

        Args:
            text: The text displayed for this menu item.
            action: The function (callable with no arguments) to execute when selected.

        Returns:
            The Menu instance (self) for chaining.
        """
        self.items.append(MenuItem(text, 'action', action))
        return self

    def add_submenu(self, text: str, submenu: 'Menu') -> 'Menu':
        """
        Adds a submenu item to the menu. Selecting this item runs the `submenu`.

        Args:
            text: The text displayed for this menu item.
            submenu: The Menu instance to run when this item is selected.
                     Its `parent` will be automatically set to this menu.

        Returns:
            The Menu instance (self) for chaining.
        """
        submenu.parent = self # Set parent for back navigation
        self.items.append(MenuItem(text, 'submenu', submenu))
        return self

    def _clear_screen(self) -> None:
        """Clears the terminal screen."""
        # Hide cursor before clearing might look slightly better
        # if self.hide_cursor: self._set_cursor_visibility(False)
        command = 'cls' if platform.system().lower() == "windows" else 'clear'
        os.system(command)

    def _set_cursor_visibility(self, visible: bool):
        """Show or hide the terminal cursor using ANSI codes."""
        if self.file == sys.stdout: # Only modify cursor for stdout
            code = "\x1b[?25h" if visible else "\x1b[?25l"
            try:
                print(code, end="", flush=True, file=self.file)
            except Exception:
                # Ignore errors if stream is not a compatible terminal
                pass

    def _display_menu(self, current_selection: int, all_options: List[MenuItem]):
        """Internal method to draw the menu with the current selection highlighted."""
        if self.clear_screen_on_run:
            self._clear_screen()
        else:
            # If not clearing, attempt to move cursor up to overwrite previous menu
            # This requires knowing how many lines the previous menu took.
            # Simpler approach for now: just print without clearing.
            pass # Maybe add ANSI code to move cursor up N lines later?

        # Display Title
        ASCIIColors.print(self.title, color=self.styles['title'], style="", file=self.file)
        ASCIIColors.print("-" * len(strip_ansi(self.title)), color=self.styles['title'], style="", file=self.file)

        # Display Items
        for i, item in enumerate(all_options):
            if i == current_selection:
                prefix = self.prefixes['selected']
                style_and_color = self.styles['selected']
            else:
                prefix = self.prefixes['unselected']
                style_and_color = self.styles['item']

            # Print styled item line
            line = f"{prefix}{item.text}"
            # Apply style, print, then reset
            ASCIIColors.print(f"{style_and_color}{line}{ASCIIColors.color_reset}", file=self.file)

        # Display Prompt
        ASCIIColors.print(f"\n{self.prompt_text}", color=self.styles['prompt'], style="", file=self.file)


    def run(self) -> None:
        """
        Displays the menu, handles arrow key navigation, and executes selections.

        The loop continues until the user selects "Quit" or "Back".
        Uses Up/Down arrows for navigation and Enter for selection.
        """
        current_selection = 0
        if self.hide_cursor:
            self._set_cursor_visibility(False)

        try:
            while True:
                # Combine main items with Back/Quit options for navigation
                all_options = list(self.items) # Copy main items
                if self.parent:
                    all_options.append(MenuItem("Back", "back", None))
                else:
                    all_options.append(MenuItem("Quit", "quit", None))

                num_options = len(all_options)
                if num_options == 0:
                    ASCIIColors.print("Menu is empty.", color=self.styles['error'], file=self.file)
                    return # Nothing to select

                # Ensure selection index is valid (can happen if items change dynamically - not supported yet)
                current_selection = max(0, min(current_selection, num_options - 1))

                self._display_menu(current_selection, all_options)

                # --- Get User Input ---
                key = _get_key()

                # --- Process Input ---
                if key == 'UP':
                    current_selection = (current_selection - 1 + num_options) % num_options
                elif key == 'DOWN':
                    current_selection = (current_selection + 1) % num_options
                elif key == 'ENTER':
                    selected_item = all_options[current_selection]

                    # --- Handle Selection ---
                    if selected_item.type == 'action':
                        if self.clear_screen_on_run: self._clear_screen() # Clear before action output
                        try:
                            # Show cursor during action execution if needed
                            if self.hide_cursor: self._set_cursor_visibility(True)
                            selected_item.target() # Call the action function
                            # Hide cursor again before asking for confirmation
                            if self.hide_cursor: self._set_cursor_visibility(False)

                            ASCIIColors.print("\nPress Enter to continue...", color=self.styles['prompt'], end="", flush=True, file=self.file)
                            while _get_key() != 'ENTER': pass # Wait specifically for Enter
                        except Exception as e:
                            # Show cursor if error occurred
                            if self.hide_cursor: self._set_cursor_visibility(True)
                            ASCIIColors.error("Error executing action:", file=self.file)
                            trace_exception(e) # Log the exception
                            # Hide cursor again before confirmation
                            if self.hide_cursor: self._set_cursor_visibility(False)
                            ASCIIColors.print("\nPress Enter to continue...", color=self.styles['prompt'], end="", flush=True, file=self.file)
                            while _get_key() != 'ENTER': pass # Wait for Enter
                    elif selected_item.type == 'submenu':
                        # Show cursor before running submenu
                        # if self.hide_cursor: self._set_cursor_visibility(True)
                        selected_item.target.run() # Run the submenu
                        # Hide cursor again when returning (if needed)
                        # if self.hide_cursor: self._set_cursor_visibility(False)
                    elif selected_item.type == 'back':
                        return # Exit this menu's run loop
                    elif selected_item.type == 'quit':
                        break # Exit the main loop (only for root menu)

                elif key == 'QUIT': # Handle Ctrl+C
                     if self.parent:
                         return # Treat as 'Back' in submenus
                     else:
                         ASCIIColors.print("\nQuitting.", color=self.styles['prompt'], file=self.file)
                         break # Quit from root menu

                # Ignore other keys for now

        finally:
            # --- Ensure cursor is visible on exit ---
            if self.hide_cursor:
                self._set_cursor_visibility(True)
            # Optionally clear screen on final exit?
            # if self.clear_screen_on_run: self._clear_screen()


# --- TQDM-like ProgressBar ---

class ProgressBar:
    """
    A customizable, thread-safe progress bar similar to `tqdm`, using `ASCIIColors` for styling.

    Can be used as an iterator wrapper or a context manager for manual updates.

    Uses direct terminal printing (`ASCIIColors.print` with `\\r`) and is independent
    of the logging system.

    Example Usage:

    .. code-block:: python

        from ascii_colors import ProgressBar
        import time

        # As an iterator wrapper
        for i in ProgressBar(range(100), desc="Processing Items"):
            time.sleep(0.05)

        # Manual control with context manager
        total_steps = 50
        with ProgressBar(total=total_steps, desc="Manual Task", color=ASCIIColors.color_cyan) as pbar:
            for step in range(total_steps):
                # Simulate work
                time.sleep(0.02)
                pbar.update(1)
                if step == total_steps // 2:
                    pbar.set_description("Halfway Done")

    Attributes:
        iterable (Optional[Iterable]): The iterable being processed (if provided).
        total (Optional[int]): The total number of expected iterations.
        desc (str): Prefix for the progress bar description.
        unit (str): String that will be used to define the unit of each iteration.
        ncols (Optional[int]): The width of the entire output message. If specified,
                               disables dynamic sizing. If None (default), tries to
                               use terminal width.
        bar_format (Optional[str]): Specify a custom bar string format. May contain
                                    '{l_bar}', '{bar}', '{r_bar}'. Default includes
                                    desc, %, bar, count, rate, eta.
        leave (bool): If True, leaves the finished progress bar on screen.
        position (int): Specify the line offset to print this bar (0 - default).
                        Useful for managing multiple bars, but requires careful
                        manual management. Note: `ascii_colors` doesn't fully manage
                        nested/multiple bars like `tqdm` might.
        mininterval (float): Minimum progress display update interval (seconds).
        color (str): ANSI color code for the progress bar/text.
        style (str): ANSI style code for the progress bar/text.
        background (str): ANSI background code for the progress bar/text.
        progress_char (str): Character(s) representing filled progress.
        empty_char (str): Character(s) representing remaining progress.
        bar_style (str): Style of the bar ('fill', 'blocks'). Default 'fill'.
        file (StreamType): Specify output file (default: sys.stdout).
    """
    _default_bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{unit}]"
    _block_chars = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"] # Unicode blocks for 'blocks' style

    def __init__(
        self,
        iterable: Optional[Iterable[_T]] = None,
        total: Optional[int] = None,
        desc: str = "",
        unit: str = "it",
        ncols: Optional[int] = None,
        bar_format: Optional[str] = None,
        leave: bool = True,
        position: int = 0, # Note: Position handling is basic here
        mininterval: float = 0.1, # Minimum time between updates
        color: str = ASCIIColors.color_green, # Default color
        style: str = "",
        background: str = "",
        progress_char: str = "█", # Block character
        empty_char: str = "░", # Lighter block character
        bar_style: str = "fill", # 'fill' or 'blocks'
        file: Optional[StreamType] = None,
        *args: Any, # Absorb other tqdm args for basic compatibility
        **kwargs: Any
    ):
        self.iterable = iterable
        self.desc = desc
        self.unit = unit
        self.ncols = ncols
        self.bar_format = bar_format if bar_format is not None else self._default_bar_format
        self.leave = leave
        self.position = position # Basic support
        self.mininterval = mininterval
        self.color = color
        self.style = style
        self.background = background
        self.progress_char = progress_char
        self.empty_char = empty_char
        self.bar_style = bar_style.lower()
        self.file = file if file is not None else sys.stdout

        self._iterator: Optional[Iterator[_T]] = None
        self._lock = Lock() # For thread safety
        self.n = 0 # Current progress
        self.start_t = time.time()
        self.last_print_n = 0
        self.last_print_t = self.start_t
        self.elapsed = 0.0
        self._closed = False

        # Determine total
        if total is not None:
            self.total = total
        elif iterable is not None:
            try:
                self.total = len(cast(Sized, iterable)) # Attempt to get length
            except (TypeError, AttributeError):
                self.total = None # Cannot determine total
        else:
            self.total = None

    def __iter__(self) -> 'ProgressBar[_T]':
        if self.iterable is None:
            raise ValueError("ProgressBar needs an iterable to be used in a for loop")
        self._iterator = iter(self.iterable)
        self.start_t = time.time() # Reset timer on iteration start
        self.last_print_t = self.start_t
        self.n = 0
        self._render() # Initial render
        return self

    def __next__(self) -> _T:
        if self._iterator is None:
            raise RuntimeError("Cannot call next() before __iter__()")
        try:
            value = next(self._iterator)
            self.update(1)
            return value
        except StopIteration:
            self.close()
            raise

    def __enter__(self) -> 'ProgressBar[_T]':
        self.start_t = time.time() # Reset timer on context entry
        self.last_print_t = self.start_t
        self.n = 0
        self._render() # Initial render
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def update(self, n: int = 1) -> None:
        """Increment the progress bar by `n` steps."""
        if self._closed:
            return
        with self._lock:
            self.n += n
            # Throttle rendering based on time interval
            current_t = time.time()
            if current_t - self.last_print_t >= self.mininterval:
                self._render()
                self.last_print_t = current_t
                self.last_print_n = self.n

    def set_description(self, desc: str) -> None:
        """Update the description text."""
        with self._lock:
            self.desc = desc
            # Consider re-rendering immediately or rely on next update?
            # Re-rendering for description change is often desired.
            self._render() # Re-render to show new description

    def close(self) -> None:
        """Cleanup the progress bar."""
        if self._closed:
            return
        with self._lock:
            self._closed = True
            # Final render if leaving the bar
            if self.leave:
                self._render(final=True)
            # Move to the next line after the progress bar
            # Check if file is valid before printing newline
            if self.file and hasattr(self.file, 'write') and not getattr(self.file, 'closed', False):
                 try:
                    self.file.write("\n")
                    self.file.flush()
                 except Exception:
                     # Handle potential errors writing newline (e.g., broken pipe)
                     pass # Silently ignore on close error

    def _format_time(self, seconds: float) -> str:
        """Formats seconds into HH:MM:SS"""
        if not math.isfinite(seconds) or seconds < 0:
            return "??:??"
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
        else:
            return f"{int(m):02d}:{int(s):02d}"

    def _estimate_eta(self) -> float:
        """Estimate remaining time (ETA) in seconds."""
        if self.total is None or self.total == 0 or self.n == 0 or self.elapsed <= 0:
            return float('inf') # Cannot estimate
        rate = self.n / self.elapsed
        if rate == 0:
            return float('inf')
        remaining_items = self.total - self.n
        return remaining_items / rate

    def _get_terminal_width(self) -> int:
        """Get terminal width, default to 80 if unavailable."""
        if self.ncols is not None:
            return self.ncols
        try:
            # Use shutil.get_terminal_size, fallback to 80
            width = shutil.get_terminal_size((80, 20)).columns
            # Add a small safety margin if width is determined
            return max(10, width) # Ensure minimum width
        except (OSError, AttributeError): # Handle errors/non-terminal environments
            return 80 # Default width

    def _render(self, final: bool = False) -> None:
        """Render the progress bar to the stream."""
        # This method MUST be called with the lock held

        if self._closed and not final: # Don't render if closed unless it's the final call
             return

        # Calculate metrics
        self.elapsed = time.time() - self.start_t
        current_n = self.n
        current_total = self.total
        desc = f"{self.desc}: " if self.desc else ""

        # Percentage and Counts
        percentage_s = "?%"
        n_fmt = str(current_n)
        total_fmt = str(current_total) if current_total is not None else "?"
        if current_total is not None and current_total > 0:
            percentage = (current_n / current_total) * 100
            percentage_s = f"{percentage:3.0f}%"
        elif current_total == 0 and current_n == 0:
            percentage = 100.0 # Handle 0/0 case as 100% complete
            percentage_s = "100%"
        elif current_total == 0:
             percentage = 100.0 # If total is 0 but n > 0 (?), consider 100%? Or error?
             percentage_s = "??%"

        # Rate
        rate = 0.0
        if self.elapsed > 0:
            rate = current_n / self.elapsed
        rate_fmt = f"{rate:.2f}" if rate > 0.01 else "? "

        # Time
        elapsed_str = self._format_time(self.elapsed)
        eta_seconds = self._estimate_eta()
        remaining_str = self._format_time(eta_seconds)

        # Prepare left/right parts for bar_format
        l_bar = f"{desc}{percentage_s}"
        r_bar = f"| {n_fmt}/{total_fmt} [{elapsed_str}<{remaining_str}, {rate_fmt}{self.unit}]"

        # Calculate available width for the bar itself
        terminal_width = self._get_terminal_width()
        # Adjust for position if implemented fully (basic support here just prints)
        prefix_len = len(strip_ansi(l_bar))
        suffix_len = len(strip_ansi(r_bar))
        # Leave space for '| ' between bar and r_bar
        bar_width = terminal_width - prefix_len - suffix_len - 2 # -2 for "| "
        bar_width = max(1, bar_width) # Ensure bar is at least 1 char wide

        # --- Generate the actual progress bar string ---
        bar = ""
        if current_total is not None and current_total > 0:
            filled_len_exact = (current_n / current_total) * bar_width
            filled_len = int(filled_len_exact)
            remaining_len = bar_width - filled_len

            if self.bar_style == 'blocks':
                blocks_filled = self.progress_char * filled_len
                partial_block_idx = int((filled_len_exact - filled_len) * len(self._block_chars))
                partial_block = self._block_chars[partial_block_idx] if partial_block_idx > 0 else ""
                # Adjust remaining len if partial block is used
                actual_remaining_len = bar_width - len(blocks_filled) - (1 if partial_block else 0)
                actual_remaining_len = max(0, actual_remaining_len)
                empty_fill = self.empty_char * actual_remaining_len
                bar = f"{blocks_filled}{partial_block}{empty_fill}"

            else: # Default 'fill' style
                 bar = self.progress_char * filled_len + self.empty_char * remaining_len
        elif current_total == 0 and current_n == 0:
             bar = self.progress_char * bar_width # 100% filled for 0/0
        else: # No total, show indeterminate or just empty? Tqdm shows empty
             bar = self.empty_char * bar_width

        # Apply color/style to the bar components (example: color the filled part)
        # More complex styling (e.g., gradient) could be added here.
        bar_styled = f"{self.color}{self.style}{self.background}{bar}{ASCIIColors.color_reset}"

        # Construct final output string using bar_format placeholders
        full_bar_str = self.bar_format.format(
            l_bar=l_bar,
            r_bar=r_bar,
            bar=bar_styled, # Use the styled bar
            n=current_n, n_fmt=n_fmt,
            total=current_total, total_fmt=total_fmt,
            percentage=percentage_s.strip(), # Remove padding for format use
            elapsed=elapsed_str, remaining=remaining_str,
            rate=rate, rate_fmt=rate_fmt,
            unit=self.unit,
            desc=self.desc
        ).strip()

        # Truncate if exceedsncols (shouldn't happen often with calculation above)
        if len(strip_ansi(full_bar_str)) > terminal_width:
            # Basic truncation (might cut mid-escape code, less ideal)
            # A more robust truncate would need ANSI code awareness.
            # For now, truncate based on visible length roughly.
            cutoff = terminal_width - 3 # Room for "..."
            # This simple slice isn't ANSI-aware, but might be okay for overflow
            full_bar_str = full_bar_str[:cutoff] + "..."


        # --- Direct Print using ASCIIColors ---
        # Use '\r' to return to the beginning of the line
        prefix = "\r"
        # Note: Position handling is basic. Real multi-bar requires cursor manipulation.
        # If position > 0, we'd need ANSI codes to move cursor up, print, move down.
        # This implementation just prints on the current line.

        # Check if file is valid before printing
        if self.file and hasattr(self.file, 'write') and not getattr(self.file, 'closed', False):
            try:
                # Use ASCIIColors.print to handle the final reset code implicitly
                # We provide an empty color/style here because the bar itself contains codes
                ASCIIColors.print(
                    f"{prefix}{full_bar_str}",
                    color="", style="", background="", # Bar string already has codes+reset
                    end="", # No newline
                    flush=True,
                    file=self.file
                )
            except Exception:
                 # Handle potential write errors (e.g., closed pipe)
                 self.close() # Attempt to close the bar if writing fails



# ==============================================================================
# --- Logging Compatibility Layer ---
# ==============================================================================
# This section provides functions and classes designed to mimic the interface
# of Python's standard `logging` module, allowing `ascii_colors` to be used
# as a near drop-in replacement in many cases. These components interact with
# the global state managed by the `ASCIIColors` class.

_logger_cache: Dict[str, '_AsciiLoggerAdapter'] = {}
"""Cache for logger adapter instances, ensuring getLogger returns the same object
for the same name."""
_logger_cache_lock = Lock()
"""Lock to protect access to the logger cache during creation."""

class _AsciiLoggerAdapter:
    """
    Internal adapter class that mimics the standard `logging.Logger` interface.

    Instances of this class are returned by `getLogger()`. Its methods delegate
    logging calls (`debug`, `info`, etc.) to the central `ASCIIColors._log` method,
    and configuration methods (`setLevel`, `addHandler`, etc.) operate on the
    global state managed by the `ASCIIColors` class.

    Attributes:
        name (str): The name assigned to this logger adapter instance.
    """
    name: str
    def __init__(self, name: str):
        """Initializes the logger adapter.

        Args:
            name: The name for this logger (e.g., "root", "myapp.module").
        """
        self.name = name

    def setLevel(self, level: Union[int, str]) -> None:
        """Sets the *global* logging level. Mimics `Logger.setLevel`.

        Note: Unlike standard logging where levels can be per-logger, this
        currently modifies the single global level in `ASCIIColors`.

        Args:
            level: The minimum level (integer or string name like "INFO").
        """
        # Delegates to the global level setter
        ASCIIColors.set_log_level(LogLevel(_level_name_to_int(level)))

    def getEffectiveLevel(self) -> int:
        """Returns the current *global* effective logging level. Mimics `Logger.getEffectiveLevel`.

        Returns:
            The integer value of the global log level.
        """
        # Returns the current global level value
        return ASCIIColors._global_level.value

    def addHandler(self, hdlr: Handler) -> None:
        """Adds a handler to the *global* list of handlers. Mimics `Logger.addHandler`.

        Args:
            hdlr: The Handler instance to add globally.
        """
        # Delegates to the global handler management
        ASCIIColors.add_handler(hdlr)

    def removeHandler(self, hdlr: Handler) -> None:
        """Removes a handler from the *global* list. Mimics `Logger.removeHandler`.

        Args:
            hdlr: The Handler instance to remove globally.
        """
        # Delegates to the global handler management
        ASCIIColors.remove_handler(hdlr)

    def hasHandlers(self) -> bool:
        """Checks if any handlers are configured *globally*. Mimics `Logger.hasHandlers`.

        Returns:
            True if the global handler list is not empty, False otherwise.
        """
        # Checks the global handler list
        with ASCIIColors._handler_lock:
            return bool(ASCIIColors._handlers)

    # --- Logging Methods ---
    # These methods mirror standard Logger methods and delegate to ASCIIColors._log,
    # passing their own name as the logger_name. They check the global level before delegating.

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level DEBUG, using this adapter's name."""
        # Check global level before calling _log for slight performance gain
        if ASCIIColors._global_level <= LogLevel.DEBUG:
            ASCIIColors._log(LogLevel.DEBUG, msg, args, logger_name=self.name, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level INFO, using this adapter's name."""
        if ASCIIColors._global_level <= LogLevel.INFO:
            ASCIIColors._log(LogLevel.INFO, msg, args, logger_name=self.name, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level WARNING, using this adapter's name."""
        if ASCIIColors._global_level <= LogLevel.WARNING:
            ASCIIColors._log(LogLevel.WARNING, msg, args, logger_name=self.name, **kwargs)
    # Alias for warning
    warn = warning

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level ERROR, using this adapter's name."""
        # Note: exc_info can be passed in kwargs
        if ASCIIColors._global_level <= LogLevel.ERROR:
            ASCIIColors._log(LogLevel.ERROR, msg, args, logger_name=self.name, **kwargs)

    def exception(self, msg: str, *args: Any, exc_info: ExcInfoType = True, **kwargs: Any) -> None:
        """Logs a message with level ERROR, automatically including exception info.

        Convenience method typically called from within an exception handler.
        Sets `exc_info` to True by default.
        """
        # Explicitly set exc_info=True unless overridden in kwargs
        kwargs['exc_info'] = exc_info
        self.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level CRITICAL, using this adapter's name."""
        if ASCIIColors._global_level <= LogLevel.CRITICAL:
            ASCIIColors._log(LogLevel.CRITICAL, msg, args, logger_name=self.name, **kwargs)
    # Alias for critical
    fatal = critical

    def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with an arbitrary integer level, using this adapter's name."""
        try:
            # Attempt to convert integer level to LogLevel enum
            log_level_enum = LogLevel(level)
        except ValueError:
            # Handle cases where level is outside standard enum values
            if level > LogLevel.CRITICAL: log_level_enum = LogLevel.CRITICAL
            elif level < LogLevel.DEBUG: log_level_enum = LogLevel.DEBUG # Map below DEBUG to DEBUG? Or INFO? Logging maps to NOTSET=0
            else: log_level_enum = LogLevel.INFO # Default fallback for unknown intermediate levels
            # Consider warning about unknown level?
            # self.warning(f"Attempted to log with unknown level {level}. Using {log_level_enum.name}.")

        # Check global level before delegating
        if ASCIIColors._global_level <= log_level_enum:
            ASCIIColors._log(log_level_enum, msg, args, logger_name=self.name, **kwargs)

# --- Level Name Mapping (for compatibility) ---
_level_to_name: Dict[int, str] = {
    level.value: level.name for level in LogLevel if level != LogLevel.NOTSET
}
_level_to_name[NOTSET] = "NOTSET" # Add NOTSET mapping explicitly

_name_to_level: Dict[str, int] = {
    name: level for level, name in _level_to_name.items()
}

def getLevelName(level: int) -> str:
    """
    Return the textual representation of logging level 'level'. Mimics `logging.getLevelName`.

    If the level corresponds to a standard level (DEBUG, INFO, etc.), the uppercase
    name is returned. Otherwise, the string "Level {level}" is returned.

    Args:
        level: The integer log level.

    Returns:
        The string name of the level.
    """
    return _level_to_name.get(level, f"Level {level}")

def _level_name_to_int(level: Union[int, str]) -> int:
    """
    Internal helper to convert a level representation (int or string name)
    to its integer value. Case-insensitive for string names. Defaults to DEBUG
    if the string name is unrecognized.

    Args:
        level: The level representation (e.g., 20, "INFO", "warning").

    Returns:
        The integer value of the level.
    """
    if isinstance(level, int):
        # Ensure valid integer level? Standard logging doesn't strictly enforce this here.
        return level
    if isinstance(level, str):
        # Lookup uppercase name in mapping, default to DEBUG if not found
        return _name_to_level.get(level.upper(), DEBUG)
    # Fallback for unexpected types? Default to DEBUG.
    return DEBUG

# --- Compatibility Functions ---

def getLogger(name: Optional[str] = None) -> _AsciiLoggerAdapter:
    """
    Returns a logger adapter instance with the specified name. Mimics `logging.getLogger`.

    If `name` is None or "root", the root logger adapter is returned. Subsequent
    calls with the same name will return the same cached adapter instance.

    Args:
        name: The hierarchical name of the logger (e.g., "myapp.ui", "db.connector").
              If None, returns the root logger adapter.

    Returns:
        An `_AsciiLoggerAdapter` instance configured to use the global `ascii_colors`
        logging state.
    """
    logger_name = name if name is not None else "root"
    with _logger_cache_lock:
        # Return cached instance if it exists
        if logger_name in _logger_cache:
            return _logger_cache[logger_name]
        # Otherwise, create a new adapter, cache it, and return it
        adapter = _AsciiLoggerAdapter(logger_name)
        _logger_cache[logger_name] = adapter
        return adapter

def basicConfig(**kwargs: Any) -> None:
    """
    Performs basic configuration for the `ascii_colors` logging system. Mimics `logging.basicConfig`.

    This function configures the global logging state (level, handlers, formatters)
    based on the provided keyword arguments. It's intended to be called once at
    application startup. Subsequent calls typically have no effect unless `force=True`
    is specified.

    If no handlers are specified via the `handlers` argument, it creates a default
    handler (`ConsoleHandler`/`StreamHandler` writing to `stderr`, or `FileHandler`
    if `filename` is provided). It sets the global level and applies a default
    formatter to the implicitly created handler(s).

    Supported Keyword Arguments:
        level (Union[int, str]): Sets the global minimum logging level (e.g., INFO, "DEBUG").
            Defaults to WARNING.
        format (str): The format string for the default formatter (use `fmt=` alias too).
        datefmt (str): The date format string for the default formatter.
        style (str): The format string style ('%' or '{') for the default formatter. Defaults to '%'.
        handlers (List[Handler]): A list of handler instances to use. If provided,
            `stream` and `filename` arguments are ignored. Handlers in this list
            will have the default formatter assigned *only if* they don't already
            have one set.
        filename (Union[str, Path]): Creates a `FileHandler` for this path. Incompatible with `handlers`.
        filemode (str): Mode for `FileHandler` ('a' or 'w'). Defaults to 'a'. Requires `filename`.
        encoding (str): Encoding for `FileHandler`. Requires `filename`.
        delay (bool): Delay file opening for `FileHandler`. Defaults to False. Requires `filename`.
        stream (StreamType): Creates a `ConsoleHandler` writing to this stream. Incompatible
            with `handlers` and `filename`. Defaults to `sys.stderr` if no stream/filename/handlers
            are provided.
        force (bool): If True, removes and closes any existing global handlers before
            performing configuration. Allows re-running `basicConfig`. Defaults to False.

    """
    with ASCIIColors._handler_lock: # Ensure thread-safe configuration
        # Check if already configured and force is not set
        already_configured: bool = bool(ASCIIColors._handlers) or ASCIIColors._basicConfig_called
        force: bool = kwargs.get('force', False)

        if already_configured and not force:
            # Already configured, do nothing unless forced
            return

        # --- Force Reconfiguration: Clean up old handlers ---
        old_handlers: List[Handler] = ASCIIColors._handlers[:] # Copy before clearing
        ASCIIColors._handlers.clear() # Clear global list

        if force and old_handlers:
            # Close existing handlers if force=True
            for h in old_handlers:
                try:
                    h.close()
                except Exception as e:
                    # Use direct print for critical errors during cleanup
                    ASCIIColors.print(
                        f"PANIC: Error closing old handler {type(h).__name__} during basicConfig(force=True): {e}",
                        color=ASCIIColors.color_bright_red, file=sys.stderr, flush=True
                    )

        # --- Set Global Level ---
        # Default level is WARNING if not specified
        level_arg: Union[int, str] = kwargs.get('level', WARNING)
        level_int = _level_name_to_int(level_arg)
        ASCIIColors.set_log_level(LogLevel(level_int))
        current_level_enum = LogLevel(level_int) # Keep enum version for handlers

        # --- Create Default Formatter ---
        fmt_arg: Optional[str] = kwargs.get('format', kwargs.get('fmt')) # Allow 'fmt' alias
        datefmt_arg: Optional[str] = kwargs.get('datefmt')
        style_arg: str = kwargs.get('style', '%') # Default style is %
        # Note: Formatter uses its own defaults if fmt_arg/datefmt_arg are None
        default_formatter: Formatter = Formatter(fmt=fmt_arg, datefmt=datefmt_arg, style=style_arg)

        # --- Determine Handlers ---
        handlers_arg: Optional[List[Handler]] = kwargs.get('handlers')
        filename_arg: Optional[Union[str, Path]] = kwargs.get('filename')
        stream_arg: Optional[StreamType] = kwargs.get('stream')

        new_handlers_list: List[Handler] = []

        if handlers_arg is not None:
            # Use explicitly provided handlers
            if filename_arg or stream_arg:
                    ASCIIColors.warning("basicConfig: 'handlers' argument specified, ignoring 'filename' and 'stream'.")
            for h in handlers_arg:
                # Assign the default formatter *only if* the handler doesn't have one already
                if h.formatter is None:
                    h.setFormatter(default_formatter)
                # Ensure handler level respects the globally set level (if handler level is NOTSET?)
                # Standard logging basicConfig doesn't force handler levels down. Let's mimic that.
                # if h.level == NOTSET: h.setLevel(current_level_enum)
                new_handlers_list.append(h)

        elif filename_arg is not None:
            # Configure a FileHandler
            if stream_arg:
                ASCIIColors.warning("basicConfig: 'filename' argument specified, ignoring 'stream'.")
            mode_arg: str = kwargs.get('filemode', 'a')
            encoding_arg: Optional[str] = kwargs.get('encoding') # Defaults handled by FileHandler
            delay_arg: bool = kwargs.get('delay', False)

            # Pass formatter, level directly to FileHandler init
            file_kw: Dict[str, Any] = {
                'mode': mode_arg,
                'formatter': default_formatter, # Always assign the created formatter
                'delay': delay_arg,
                'level': current_level_enum, # Set handler level to global level
                'encoding': encoding_arg
            }
            # Remove encoding if None to let FileHandler use its default
            if encoding_arg is None:
                    del file_kw['encoding']

            try:
                file_handler = FileHandler(filename_arg, **file_kw)
                new_handlers_list.append(file_handler)
            except Exception as e_fh:
                    ASCIIColors.print(
                        f"PANIC: Failed to create FileHandler in basicConfig for {filename_arg}: {e_fh}",
                        color=ASCIIColors.color_bright_red, file=sys.stderr, flush=True
                    )
                    # Proceed without file handler if creation failed? Or re-raise? For now, continue.

        else:
            # Configure a default ConsoleHandler/StreamHandler
            # If stream_arg is None, ConsoleHandler defaults to sys.stderr
            handler: ConsoleHandler = ConsoleHandler(stream=stream_arg, level=current_level_enum)
            handler.setFormatter(default_formatter) # Assign the created formatter
            new_handlers_list.append(handler)

        # --- Set Global Handlers List ---
        ASCIIColors._handlers = new_handlers_list
        # Mark basicConfig as called to prevent auto-handler creation later
        ASCIIColors._basicConfig_called = True

# ==============================================================================
# --- Automatic Shutdown ---
# ==============================================================================
import atexit # Add this import near the top with other imports

_shutdown_called = False # Flag to prevent multiple shutdowns

def shutdown(handler_list: Optional[List[Handler]] = None) -> None:
    """
    Performs clean shutdown of the logging system.

    Closes all registered handlers (or a specific list) to release resources
    like file handles. Called automatically via atexit.

    Args:
        handler_list: Optional list of handlers to close. If None, closes
                      all handlers registered in ASCIIColors._handlers.
    """
    global _shutdown_called
    if _shutdown_called:
        return

    # Prevent recursive calls if shutdown itself logs errors causing shutdown again
    _shutdown_called = True

    handlers_to_close: List[Handler] = []
    if handler_list is not None:
        handlers_to_close = handler_list
    else:
        # Operate on a copy of the global list under lock
        with ASCIIColors._handler_lock:
            handlers_to_close = ASCIIColors._handlers[:]

    # Close handlers outside the lock to avoid potential deadlocks if
    # a handler's close() method tries logging or acquiring other locks.
    for h in handlers_to_close:
        if h: # Basic check
            try:
                # Flush might be useful before closing
                if hasattr(h, 'flush'):
                    h.flush()
                h.close()
            except Exception as e:
                # Cannot use logger here as it might be closing itself
                # Direct print to stderr as a last resort
                print(f"ascii_colors: Error closing handler {type(h).__name__}: {e}", file=sys.stderr, flush=True)
                # Optionally print traceback
                # traceback.print_exc(file=sys.stderr)


# Register the shutdown function to be called upon normal interpreter exit
atexit.register(shutdown)

# --- Example Usage Block ---
# This block is executed only when the script is run directly (python ascii_colors/__init__.py)
# It serves as a demonstration of the library's features.
if __name__ == "__main__":

    print("="*30)
    print("--- ASCIIColors Demo ---")
    print("="*30)

    # --- Direct Print Demo ---
    print("\n--- Direct Print Methods (Bypass Logging) ---")
    ASCIIColors.red("This is Red Text (direct print)")
    ASCIIColors.yellow("This is Yellow Text (direct print)")
    ASCIIColors.bold("This is Bold White Text (direct print)")
    ASCIIColors.italic("This is Italic Cyan Text (direct print)", color=ASCIIColors.color_cyan)
    ASCIIColors.underline("This is Underlined Green (direct print)", color=ASCIIColors.color_green)
    ASCIIColors.strikethrough("This is Strikethrough Magenta (direct print)", color=ASCIIColors.color_magenta)
    ASCIIColors.bg_blue("White text on Blue Background (direct print)")
    ASCIIColors.print(
        "Black text on Yellow BG (direct print) ",
        color=ASCIIColors.color_black, background=ASCIIColors.color_bg_yellow
    )
    ASCIIColors.print(
        "Bold Red on Bright White BG (direct print) ",
        color=ASCIIColors.color_red, background=ASCIIColors.color_bg_bright_white, style=ASCIIColors.style_bold
    )
    ASCIIColors.multicolor(
        ["Status: ", "OK", " | ", "Value: ", "100"],
        [ASCIIColors.color_white, ASCIIColors.color_green, ASCIIColors.color_white, ASCIIColors.color_cyan, ASCIIColors.color_bright_yellow]
    )
    ASCIIColors.highlight("Highlight the word 'ERROR' in this line.", "ERROR", highlight_color=ASCIIColors.color_bg_red)

    # --- Logging Demo (Original ASCIIColors API) ---
    print("\n--- Logging Demo (ASCIIColors Native API) ---")
    ASCIIColors.clear_handlers() # Start fresh for demo
    ASCIIColors._basicConfig_called = False # Reset flag for this section
    ASCIIColors.set_log_level(DEBUG) # Set global level

    # Add console handler with custom format using {} style, output to stdout
    console_fmt = Formatter("[{levelname}] {message} (Thread: {threadName})", style='{')
    # Explicitly set stream to stdout for demo clarity
    console_handler_ascii = ConsoleHandler(formatter=console_fmt, stream=sys.stdout, level=DEBUG)
    ASCIIColors.add_handler(console_handler_ascii)

    # Add file handler using ASCIIColors API
    log_file_ascii = Path("./temp_ascii_api.log") # Use relative path for demo
    if log_file_ascii.exists(): log_file_ascii.unlink()
    file_fmt_ascii = Formatter(
        fmt="%(asctime)s|%(levelname)-8s|%(name)s|%(message)s",
        style='%',
        datefmt='%H:%M:%S'
    )
    # Log INFO and above to the file
    file_handler_ascii = FileHandler(log_file_ascii, level=INFO, formatter=file_fmt_ascii)
    ASCIIColors.add_handler(file_handler_ascii)

    print(f"Logging configured (Console: DEBUG+, File '{log_file_ascii}': INFO+)")
    ASCIIColors.debug("This is a DEBUG message (console only).")
    ASCIIColors.info("Information message %s.", "with argument")
    ASCIIColors.warning("A WARNING occurred.")
    # Use context manager
    with ASCIIColors.context(user_id="test_user", request="REQ1"):
        ASCIIColors.error("An ERROR happened in user context.", exc_info=False) # Include context
        try:
            x = 1 / 0
        except ZeroDivisionError as e:
            ASCIIColors.critical("Critical failure!", exc_info=e) # Include context and traceback
            # Use utility function as well
            trace_exception(e) # Will log the same traceback again at ERROR level

    print(f"\nCheck console output above and '{log_file_ascii}' for file logs (INFO+).")
    if log_file_ascii.exists():
        try:
            print(f"--- Content of {log_file_ascii.name} ---")
            print(log_file_ascii.read_text())
            print(f"--- End {log_file_ascii.name} ---")
        except Exception as read_err:
            print(f"Error reading log file: {read_err}")
    else:
        print(f"Log file '{log_file_ascii}' not found.")


    # --- Logging Demo (Compatibility Layer API) ---
    print("\n--- Logging Demo (Compatibility API using 'import ascii_colors as logging') ---")
    log_file_compat = Path("./temp_compat_api.log") # Relative path
    if log_file_compat.exists(): log_file_compat.unlink()

    # Use basicConfig to set up logging (overwrites previous config due to force=True)
    # Using the alias 'logging' for clarity
    logging = sys.modules[__name__] # Get reference to this module for compat layer access

    logging.basicConfig(
        level=DEBUG, # Root level for all handlers created by basicConfig
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(funcName)s)',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename=log_file_compat, # Log to this file
        filemode='w', # Overwrite file
        force=True # IMPORTANT: Override previous ASCIIColors API setup
    )

    # basicConfig created a FileHandler. Let's add a console handler manually.
    logger_compat = logging.getLogger("CompatTest") # Get logger adapter

    # Create a StreamHandler (alias for ConsoleHandler) for INFO+ to stdout
    console_h_compat = logging.StreamHandler(level=INFO, stream=sys.stdout)
    console_h_compat.setFormatter(logging.Formatter("{name}::{levelname} >> {message}", style='{'))
    # Add it to the root logger (which affects all loggers unless they override)
    logging.getLogger().addHandler(console_h_compat) # Or logger_compat.addHandler(..)

    print(f"Logging reconfigured using basicConfig (File '{log_file_compat}': DEBUG+, Console: INFO+)")
    logger_compat.debug("Compat Debug message (file only).")
    logger_compat.info("Compat Info message (file and console).")
    logger_compat.warning("Compat Warning message.")
    logger_compat.error("Compat Error message.")
    try:
        y = int("abc")
    except ValueError:
        logger_compat.exception("Compat Exception occurred!") # Includes traceback

    print(f"\nCheck console output above and '{log_file_compat}' for file logs (DEBUG+).")
    if log_file_compat.exists():
         try:
            print(f"--- Content of {log_file_compat.name} ---")
            print(log_file_compat.read_text())
            print(f"--- End {log_file_compat.name} ---")
         except Exception as read_err:
             print(f"Error reading log file: {read_err}")
    else:
        print(f"Log file '{log_file_compat}' not found.")


    # --- ProgressBar Demo ---
    print("\n--- ProgressBar Demo ---")
    items = range(150)

    # Basic iterable usage
    print("Basic ProgressBar:")
    for item in ProgressBar(items, desc="Basic Loop"):
        time.sleep(0.01)

    # Different style and chars
    print("\nStyled ProgressBar ('blocks'):")
    for item in ProgressBar(
        range(80),
        desc="Styled",
        color=ASCIIColors.color_bright_yellow,
        style=ASCIIColors.style_bold,
        progress_char="#",
        empty_char=".",
        bar_style="blocks"
    ):
        time.sleep(0.02)

    # Manual control with context manager
    print("\nManual ProgressBar:")
    total_tasks = 120
    with ProgressBar(total=total_tasks, desc="Manual", unit=" Task", color=ASCIIColors.color_magenta) as pbar:
        for i in range(total_tasks):
            time.sleep(0.015)
            pbar.update(1)
            if i == total_tasks // 3:
                pbar.set_description("Stage 2")
            if i == 2 * total_tasks // 3:
                pbar.set_description("Final Stage")

    # Example with no total (indeterminate)
    print("\nIndeterminate ProgressBar (Requires manual updates):")
    try:
        with ProgressBar(desc="Waiting...", unit=" checks", color=ASCIIColors.color_cyan) as pbar:
            for i in range(5): # Simulate fixed number of updates
                time.sleep(0.5)
                pbar.update(1)
    except Exception as e:
        ASCIIColors.error(f"Error in indeterminate bar: {e}")

    # --- Animation Demo ---
    print("\n--- Animation Demo ---")
    def long_task(duration: float = 2, should_fail: bool = False):
        """Simulates a task that takes time and might fail."""
        # Logs inside the task use the currently configured logging system
        task_logger = logging.getLogger("LongTask")
        task_logger.info(f"Task started, will run for {duration}s...")
        time.sleep(duration)
        if should_fail:
            task_logger.error("\nTask encountered an error!")
            raise ValueError("Simulated task failure!")
        task_logger.info("\nTask completed successfully.")
        return f"Task completed after {duration}s"

    try:
        # Run a task that succeeds
        result_ok = ASCIIColors.execute_with_animation(
            "Running successful task...", long_task, 1.5, should_fail=False,
            color=ASCIIColors.color_cyan
        )
        ASCIIColors.success(f"Animation Success: {result_ok}")

        # Run a task that fails
        ASCIIColors.execute_with_animation(
            "Running failing task...", long_task, 1.0, should_fail=True,
            color=ASCIIColors.color_magenta
        )
        # This line won't be reached if the task fails
        ASCIIColors.success("This should not print.")

    except Exception as e:
        # Catch the exception raised by execute_with_animation
        ASCIIColors.fail(f"Animation Failed: {type(e).__name__} - {e}")
        # Log the exception using the logging system
        trace_exception(e)


    # --- Menu Demo ---
    print("\n--- Menu Demo (Arrow Key Navigation) ---")
    ASCIIColors.print("Note: Menu Demo requires interactive terminal with arrow key support.", color=ASCIIColors.color_yellow)

    # Define some action functions (same as before)
    def action_hello():
        ASCIIColors.success("Hello from the menu action!")

    def action_info():
        ASCIIColors.info("Displaying some info...")
        print("System Platform:", platform.system())
        print("Python Version:", sys.version.split()[0])

    def action_fail():
        ASCIIColors.warning("This action is designed to fail.")
        raise RuntimeError("Simulated action failure")

    # Create menus
    root_menu = Menu(
        title="Main Application Menu (Arrows + Enter)",
        title_color=ASCIIColors.color_bright_cyan,
        item_color=ASCIIColors.color_white,
        selected_background=ASCIIColors.color_bg_blue,
        selected_prefix="➔ ", # Use arrow prefix
        unselected_prefix="  ",
        prompt_text="Use ↑/↓ arrows, Enter to select. Ctrl+C to Quit/Back."
    )

    settings_menu = Menu(
        title="Settings Submenu",
        parent=root_menu, # Important for Back option
        title_color=ASCIIColors.color_yellow,
        item_color=ASCIIColors.color_green,
        selected_background=ASCIIColors.color_bg_magenta,
    )

    more_menu = Menu(
        title="More Options",
        parent=settings_menu, # Nested submenu
        item_color=ASCIIColors.color_magenta,
        selected_background=ASCIIColors.color_bg_bright_black,
    )

    # Add items to root menu (no keys needed)
    root_menu.add_action("Say Hello", action_hello)
    root_menu.add_action("Show System Info", action_info)
    root_menu.add_submenu("Open Settings", settings_menu)
    root_menu.add_action("Test Failing Action", action_fail)

    # Add items to settings menu
    settings_menu.add_action("Adjust Brightness (Placeholder)", lambda: print("Brightness adjusted!"))
    settings_menu.add_action("Toggle Sound (Placeholder)", lambda: print("Sound toggled!"))
    settings_menu.add_submenu("More Settings...", more_menu)

    # Add items to the nested menu
    more_menu.add_action("Reset Configuration (Placeholder)", lambda: print("Config reset!"))
    more_menu.add_action("Check for Updates (Placeholder)", lambda: print("Checking..."))

    # Run the main menu (requires interactive terminal)
    ASCIIColors.print("\nStarting interactive menu demo...\n", color=ASCIIColors.color_yellow)
    # In a non-interactive test environment, this would hang or fail.
    # Uncomment the next line to run interactively:
    root_menu.run()
    ASCIIColors.print("\nMenu demo finished or quit.", color=ASCIIColors.color_yellow)

    
    # --- Cleanup Demo Files ---
    print("\n--- Cleanup ---")
    # Explicitly call shutdown BEFORE attempting to delete files in the demo,
    # although atexit should handle the general case. This makes the demo cleanup more robust.
    print("Running manual shutdown before cleanup...")
    shutdown()
    print("Manual shutdown complete.")

    try:
        if log_file_ascii.exists():
            log_file_ascii.unlink()
            print(f"Removed '{log_file_ascii}'.")
        if log_file_compat.exists():
            # Retry unlink with a small delay, as FS might still be slow
            for attempt in range(3):
                try:
                    log_file_compat.unlink()
                    print(f"Removed '{log_file_compat}'.")
                    break
                except PermissionError as pe:
                    if attempt == 2: # Last attempt failed
                        raise pe
                    print(f"Retrying unlink for {log_file_compat} ({attempt+1}/3)...")
                    time.sleep(0.1) # Small delay
        # Remove JSON log if created
        service_log = Path("./audit.jsonl") # Assuming this path from usage example
        if service_log.exists():
             service_log.unlink()
             print(f"Removed '{service_log}'.")
    except Exception as cleanup_err:
        # Use direct print as logging might be shut down
        print(f"Cleanup Error: {type(cleanup_err).__name__} - {cleanup_err}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)


    print("\n--- Demo Finished ---")