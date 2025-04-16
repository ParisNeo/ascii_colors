# -*- coding: utf-8 -*-
"""
ascii_colors: A Python library for colored console output, enhanced logging,
              and utility functions.

Author: Saifeddine ALOUI (ParisNeo)
License: Apache License 2.0
"""

import inspect
import json
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
                    Union)

# --- Log Level Enum ---


class LogLevel(IntEnum):
    """Log levels for filtering messages"""

    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


# --- Utility Functions ---


def get_trace_exception(ex: BaseException) -> str:
    """
    Traces an exception and returns the full traceback as a string.

    Args:
        ex: The exception instance.

    Returns:
        The formatted traceback string.
    """
    # Catch the exception and get the traceback as a list of strings
    traceback_lines = traceback.format_exception(type(ex), ex, ex.__traceback__)
    # Join the traceback lines into a single string
    traceback_text = "".join(traceback_lines)
    return traceback_text


# --- Formatter Classes ---


class Formatter:
    """
    Base class for formatting log records.

    Handles conversion of log record data into a string representation.
    Includes basic context like timestamp, level name, message,
    and optionally source file, line number, and function name.
    """

    def __init__(
        self,
        fmt: str = "[{level_name}][{datetime}] {message}",
        datefmt: str = "%Y-%m-%d %H:%M:%S",
        include_source: bool = False,
    ):
        """
        Initializes the formatter.

        Args:
            fmt: The format string. Available placeholders: {level_name},
                 {datetime}, {message}, {file_name}, {line_no}, {func_name},
                 plus any keys passed via **kwargs to logging methods or set
                 via context.
            datefmt: The format string for datetime objects.
            include_source: If True, attempts to include {file_name},
                            {line_no}, {func_name} in the record. This adds
                            overhead due to inspection.
        """
        self.fmt = fmt
        self.datefmt = datefmt
        self.include_source = include_source

    def format(
        self,
        level: LogLevel,
        message: str,
        timestamp: datetime,
        exc_info: Optional[Tuple[Type[BaseException], BaseException, Any]],
        **kwargs: Any,
    ) -> str:
        """
        Formats the log record into a string.

        Args:
            level: The log level.
            message: The log message.
            timestamp: The datetime of the log event.
            exc_info: Exception tuple (type, value, traceback), if any.
            **kwargs: Additional contextual keyword arguments.

        Returns:
            The formatted log string.
        """
        level_name = level.name
        dt_str = timestamp.strftime(self.datefmt)
        file_name = "N/A"
        line_no = 0
        func_name = "N/A"

        # Gather source info if requested (can be slow)
        if self.include_source:
            try:
                # Walk up the stack to find the caller frame outside the library
                frame = inspect.currentframe()
                while (
                    frame
                    and Path(frame.f_code.co_filename).parent.name == "ascii_colors"
                ):
                    frame = frame.f_back
                if frame:
                    file_name = Path(frame.f_code.co_filename).name
                    line_no = frame.f_lineno
                    func_name = frame.f_code.co_name
            except Exception:
                pass  # Ignore errors during inspection

        # Combine context: thread_local -> kwargs -> standard fields
        log_record = {
            **ASCIIColors.get_thread_context(),  # Add thread context first
            **kwargs,  # User-provided kwargs override thread context
            "level_name": level_name,
            "datetime": dt_str,
            "message": message,
            "file_name": file_name,
            "line_no": line_no,
            "func_name": func_name,
        }

        # Handle formatting errors gracefully
        try:
            formatted_message = self.fmt.format(**log_record)
        except KeyError as e:
            formatted_message = (
                f"[FORMAT_ERROR: Missing key {e}] {self.fmt} | Data: {log_record}"
            )
        except Exception as e:
            formatted_message = f"[FORMAT_ERROR: {e}] {self.fmt} | Data: {log_record}"

        if exc_info:
            formatted_message += "\n" + self.format_exception(exc_info)

        return formatted_message

    def format_exception(
        self, exc_info: Tuple[Type[BaseException], BaseException, Any]
    ) -> str:
        """Formats exception information."""
        return get_trace_exception(exc_info[1])


class JSONFormatter(Formatter):
    """
    Formats log records as JSON strings.
    """

    def __init__(
        self,
        include_fields: Optional[List[str]] = None,
        include_source: bool = False,
        datefmt: str = "iso",  # Use 'iso' for ISO 8601 format
    ):
        """
        Initializes the JSON formatter.

        Args:
            include_fields: A list of fields to include in the JSON output.
                            If None, includes default fields plus any context/kwargs.
            include_source: If True, attempts to include file, line, func context.
            datefmt: Specifies date format ('iso' or standard strftime).
        """
        # Base init is mostly ignored, but call for potential future use
        super().__init__(include_source=include_source)
        # Store the list of fields to include, if provided
        self.include_fields = include_fields
        if datefmt.lower() == "iso":
            self._format_date = lambda dt: dt.isoformat()
        else:
            self.datefmt = datefmt
            self._format_date = lambda dt: dt.strftime(self.datefmt)

    def format(
        self,
        level: LogLevel,
        message: str,
        timestamp: datetime,
        exc_info: Optional[Tuple[Type[BaseException], BaseException, Any]],
        **kwargs: Any,
    ) -> str:
        """Formats the log record into a JSON string."""
        level_name = level.name
        dt_str = self._format_date(timestamp)
        file_name = "N/A"
        line_no = 0
        func_name = "N/A"

        if self.include_source:
            try:
                # Walk up the stack to find the caller frame outside the library
                frame = inspect.currentframe()
                while (
                    frame
                    and Path(frame.f_code.co_filename).parent.name == "ascii_colors"
                ):
                    frame = frame.f_back
                if frame:
                    file_name = Path(frame.f_code.co_filename).name
                    line_no = frame.f_lineno
                    func_name = frame.f_code.co_name
            except Exception:
                pass  # Ignore errors during inspection

        # Build record: standard fields first, then context, then kwargs override
        log_record = {
            "level": level,
            "level_name": level_name,
            "datetime": dt_str,
            "message": message,
            "file_name": file_name,
            "line_no": line_no,
            "func_name": func_name,
        }
        log_record.update(ASCIIColors.get_thread_context())  # Add/override with context
        log_record.update(kwargs)  # Add/override with direct kwargs

        # Add exception info BEFORE filtering
        if exc_info:
            # Ensure exception info is serializable
            try:
                log_record["exception"] = self.format_exception(exc_info)
            except Exception as e:
                log_record["exception"] = f"Error formatting exception: {e}"

        # Filter fields if requested (self.include_fields is a list)
        if self.include_fields is not None:
            filtered_record = {
                k: v for k, v in log_record.items() if k in self.include_fields
            }
        else:  # If include_fields is None, include everything
            filtered_record = log_record

        try:
            # Use default=str for types JSON doesn't know (like Path, datetime if not iso)
            return json.dumps(filtered_record, default=str)
        except Exception as e:
            # Fallback in case of unexpected serialization errors
            # Try to report keys that were present before the error
            present_keys = list(filtered_record.keys())
            return json.dumps(
                {"json_format_error": str(e), "record_keys": present_keys}
            )


# --- Handler Classes ---


class Handler(ABC):
    """
    Abstract base class for log handlers.

    Handlers dispatch log records to the appropriate destination (console, file, etc.).
    """

    def __init__(
        self,
        level: LogLevel = LogLevel.DEBUG,
        formatter: Optional[Formatter] = None,
    ):
        """
        Initializes the handler.

        Args:
            level: The minimum log level this handler will process.
            formatter: The formatter to use for output. Defaults to a basic Formatter.
        """
        self.level = level
        self.formatter = formatter if formatter else Formatter()
        self._lock = Lock()  # Thread safety for emitting records

    def set_formatter(self, formatter: Formatter):
        """Sets the formatter for this handler."""
        with self._lock:
            self.formatter = formatter

    def handle(
        self,
        level: LogLevel,
        message: str,
        timestamp: datetime,
        exc_info: Optional[Tuple[Type[BaseException], BaseException, Any]],
        **kwargs: Any,
    ):
        """
        Handles a log record.

        Filters by level, formats the record, and emits it.

        Args:
            level: The log level of the record.
            message: The log message.
            timestamp: The datetime of the log event.
            exc_info: Exception tuple, if any.
            **kwargs: Additional context for formatting.
        """
        if level >= self.level:
            formatted_message = self.formatter.format(
                level, message, timestamp, exc_info, **kwargs
            )
            self.emit(
                level, formatted_message, **kwargs
            )  # Pass kwargs for handler-specific logic

    @abstractmethod
    def emit(self, level: LogLevel, formatted_message: str, **kwargs: Any):
        """
        Emits the formatted log record. Must be implemented by subclasses.

        Args:
            level: The log level (passed for potential handler-specific logic).
            formatted_message: The string produced by the formatter.
            **kwargs: Original kwargs passed to the log call, useful for
                      handler-specific behavior (e.g., console colors).
        """
        raise NotImplementedError


class ConsoleHandler(Handler):
    """
    Handles logging to the console (stdout/stderr).

    Applies ANSI color codes based on the log level or provided arguments.
    """

    def __init__(
        self,
        level: LogLevel = LogLevel.DEBUG,
        formatter: Optional[Formatter] = None,
        stream: TextIO = sys.stdout,
    ):
        """
        Initializes the console handler.

        Args:
            level: Minimum level to handle.
            formatter: Formatter instance.
            stream: The output stream (default: sys.stdout). Use sys.stderr for errors.
        """
        super().__init__(level, formatter)
        self.stream = stream

    def emit(self, level: LogLevel, formatted_message: str, **kwargs: Any):
        """Prints the formatted message to the console with appropriate colors."""
        # Backward compatibility: Check for raw color/style/end/flush from print/color methods
        raw_color = kwargs.get("_raw_color")
        raw_style = kwargs.get("_raw_style", "")
        raw_end = kwargs.get("_raw_end", "\n")
        raw_flush = kwargs.get("_raw_flush", False)

        # Determine color: Use raw color if provided, else use level color
        color = (
            raw_color
            if raw_color
            else ASCIIColors._level_colors.get(level, ASCIIColors.color_white)
        )

        # Construct the output string
        output = f"{raw_style}{color}{formatted_message}{ASCIIColors.color_reset}"

        # Use the lock for thread-safe printing
        with self._lock:
            print(output, end=raw_end, flush=raw_flush, file=self.stream)


class FileHandler(Handler):
    """
    Handles logging to a file.
    """

    def __init__(
        self,
        filename: Union[str, Path],
        level: LogLevel = LogLevel.DEBUG,
        formatter: Optional[Formatter] = None,
        encoding: str = "utf-8",
    ):
        """
        Initializes the file handler.

        Args:
            filename: Path to the log file.
            level: Minimum level to handle.
            formatter: Formatter instance. Defaults to basic Formatter (no colors).
            encoding: File encoding.
        """
        # Ensure formatter doesn't include source by default for file perf
        default_formatter = Formatter(include_source=False)
        super().__init__(level, formatter if formatter else default_formatter)
        self.filename = Path(filename)
        self.encoding = encoding
        # Ensure directory exists
        self.filename.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, level: LogLevel, formatted_message: str, **kwargs: Any):
        """Writes the formatted message to the log file."""
        try:
            # File operations are protected by the handler's lock
            with self._lock:
                with open(self.filename, "a", encoding=self.encoding) as f:
                    f.write(formatted_message + "\n")
        except Exception as e:
            # Critical error: Cannot write to log file. Print directly to stderr.
            # Use direct print to avoid potential recursion if stderr uses this handler.
            print(
                f"{ASCIIColors.color_bright_red}PANIC: Failed to write to log file "
                f"{self.filename}: {e}{ASCIIColors.color_reset}",
                file=sys.stderr,
            )


class RotatingFileHandler(FileHandler):
    """
    Handles logging to a file, rotating it when it reaches a certain size.
    """

    def __init__(
        self,
        filename: Union[str, Path],
        level: LogLevel = LogLevel.DEBUG,
        formatter: Optional[Formatter] = None,
        encoding: str = "utf-8",
        maxBytes: int = 0,  # Max size in bytes before rotation (0 = no rotation)
        backupCount: int = 0,  # Number of backup files to keep (0 = no backups)
    ):
        """
        Initializes the rotating file handler.

        Args:
            filename: Path to the log file.
            level: Minimum level to handle.
            formatter: Formatter instance.
            encoding: File encoding.
            maxBytes: Maximum file size in bytes before rotation.
            backupCount: Number of backup log files to keep.
        """
        super().__init__(filename, level, formatter, encoding)
        self.maxBytes = maxBytes
        self.backupCount = backupCount

    def emit(self, level: LogLevel, formatted_message: str, **kwargs: Any):
        """Writes to the file after potentially rotating it."""
        if self.should_rotate():
            self.do_rollover()
        super().emit(
            level, formatted_message, **kwargs
        )  # Call parent FileHandler's emit

    def should_rotate(self) -> bool:
        """Checks if the log file needs rotation based on size."""
        if self.maxBytes <= 0:
            return False
        try:
            # Check file size only if it exists and we need rotation
            if self.filename.exists():
                file_size = self.filename.stat().st_size
                return file_size >= self.maxBytes
        except OSError:  # Handle potential race condition or permission error
            return False
        return False  # Default case if file doesn't exist or maxBytes is 0

    def do_rollover(self):
        """Performs the log file rotation."""
        # Use lock to ensure rotation is atomic relative to writes
        with self._lock:
            if not self.should_rotate():  # Double check inside lock
                return

            # Standard rollover logic (similar to logging.handlers.RotatingFileHandler)
            if self.backupCount > 0:
                # Delete oldest log file (.5 -> .6 ignored, .4 -> .5, ..., .1 -> .2, current -> .1)
                oldest_log = f"{self.filename}.{self.backupCount}"
                if Path(oldest_log).exists():
                    try:
                        Path(oldest_log).unlink()
                    except OSError:
                        pass  # Ignore errors deleting oldest

                # Rename existing backup files
                for i in range(self.backupCount - 1, 0, -1):
                    sfn = f"{self.filename}.{i}"
                    dfn = f"{self.filename}.{i + 1}"
                    if Path(sfn).exists():
                        try:
                            Path(sfn).rename(dfn)
                        except OSError:
                            pass  # Ignore errors renaming

                # Rename current log file to .1
                if self.filename.exists():
                    try:
                        self.filename.rename(f"{self.filename}.1")
                    except OSError:
                        pass  # Ignore errors renaming current

            else:  # No backup count, just remove the current file before writing new
                if self.filename.exists():
                    try:
                        self.filename.unlink()
                    except OSError:
                        pass  # Ignore errors deleting current


# --- Main ASCIIColors Class ---


class ASCIIColors:
    """
    Provides methods for colored console output and enhanced logging.

    Manages handlers, formatters, global log level, and thread context.
    Offers both semantic logging methods (info, warning, etc.) and
    direct color printing methods for backward compatibility.
    """

    # --- ANSI Color/Style Codes ---
    color_reset = "\u001b[0m"
    # Regular colors
    color_black = "\u001b[30m"
    color_red = "\u001b[31m"
    color_green = "\u001b[32m"
    color_yellow = "\u001b[33m"
    color_blue = "\u001b[34m"
    color_magenta = "\u001b[35m"
    color_cyan = "\u001b[36m"
    color_white = "\u001b[37m"
    color_orange = "\u001b[38;5;202m"
    # Bright colors
    color_bright_black = "\u001b[30;1m"
    color_bright_red = "\u001b[31;1m"
    color_bright_green = "\u001b[32;1m"
    color_bright_yellow = "\u001b[33;1m"
    color_bright_blue = "\u001b[34;1m"
    color_bright_magenta = "\u001b[35;1m"
    color_bright_cyan = "\u001b[36;1m"
    color_bright_white = "\u001b[37;1m"
    color_bright_orange = "\u001b[38;5;208m"
    # Styles
    style_bold = "\u001b[1m"
    style_underline = "\u001b[4m"

    # --- Logging Configuration ---
    _handlers: List[Handler] = [ConsoleHandler()]  # Default: log to console
    _global_level: LogLevel = LogLevel.INFO  # Default global level
    _handler_lock = Lock()  # Lock for modifying the _handlers list

    # Color mapping for default ConsoleHandler level coloring
    _level_colors: Dict[LogLevel, str] = {
        LogLevel.DEBUG: color_bright_magenta,
        LogLevel.INFO: color_bright_blue,  # Default info color
        LogLevel.WARNING: color_bright_orange,
        LogLevel.ERROR: color_bright_red,
    }

    # --- Thread-Local Context ---
    _context = threading.local()

    # --- Configuration Methods ---

    @classmethod
    def set_log_level(cls, level: Union[LogLevel, int]) -> None:
        """
        Sets the *global* minimum log level.

        Messages below this level will not be processed by any handler.
        Individual handlers may have their own higher level setting.

        Args:
            level: The minimum LogLevel or its integer value.
        """
        cls._global_level = LogLevel(level)

    @classmethod
    def add_handler(cls, handler: Handler) -> None:
        """Adds a log handler to the list of active handlers."""
        with cls._handler_lock:
            if handler not in cls._handlers:
                cls._handlers.append(handler)

    @classmethod
    def remove_handler(cls, handler: Handler) -> None:
        """Removes a specific handler instance."""
        with cls._handler_lock:
            try:
                cls._handlers.remove(handler)
            except ValueError:
                pass  # Handler not found, ignore

    @classmethod
    def clear_handlers(cls) -> None:
        """Removes all configured handlers."""
        with cls._handler_lock:
            cls._handlers.clear()

    @classmethod
    def set_log_file(
        cls,
        path: Union[str, Path],
        level: LogLevel = LogLevel.DEBUG,
        formatter: Optional[Formatter] = None,
    ) -> None:
        """
        Adds a FileHandler for the given path (Backward Compatibility).

        Note: This *adds* a handler. If you want this to be the *only*
        file handler, call clear_handlers() or remove existing file handlers first.

        Args:
            path: Path to the log file.
            level: Minimum level for this file handler.
            formatter: Optional formatter for this file handler.
        """
        cls.add_handler(FileHandler(path, level, formatter))

    @classmethod
    def set_template(cls, level: LogLevel, template: str) -> None:
        """
        DEPRECATED: Use set_formatter on specific handlers instead.

        This method used to set a global template per level, which is
        incompatible with the handler/formatter architecture.

        Args:
            level: The log level (ignored).
            template: The template string (ignored).
        """
        cls.warning(
            "ASCIIColors.set_template is DEPRECATED and has no effect. "
            "Configure formatters on individual handlers instead."
        )

    # --- Context Management ---

    @classmethod
    def set_context(cls, **kwargs: Any) -> None:
        """
        Sets key-value pairs in the current thread's context.

        These values will be available to formatters (e.g., `{my_key}`).
        """
        for key, value in kwargs.items():
            setattr(cls._context, key, value)

    @classmethod
    def clear_context(cls, *args: str) -> None:
        """
        Clears keys from the current thread's context.

        If no arguments are provided, clears all context for the thread.
        Otherwise, clears only the specified keys.
        """
        if not args:
            # Clear all context for this thread
            for key in list(vars(cls._context).keys()):  # Iterate over copy of keys
                if not key.startswith("_"):
                    try:
                        delattr(cls._context, key)
                    except AttributeError:
                        pass  # Already deleted
        else:
            # Clear specific keys
            for key in args:
                if hasattr(cls._context, key):
                    try:
                        delattr(cls._context, key)
                    except AttributeError:
                        pass  # Already deleted

    @classmethod
    @contextmanager
    def context(cls, **kwargs: Any):
        """
        Context manager to temporarily add thread-local context.

        Usage:
            with ASCIIColors.context(request_id="123"):
                ASCIIColors.info("Processing request")
        """
        previous_values = {}
        added_keys = set()
        try:
            # Store previous values and set new ones
            for key, value in kwargs.items():
                if hasattr(cls._context, key):
                    previous_values[key] = getattr(cls._context, key)
                else:
                    added_keys.add(key)  # Mark key as newly added
                setattr(cls._context, key, value)
            yield  # Enter the 'with' block
        finally:
            # Restore previous state
            for key, value in kwargs.items():
                if key in added_keys:
                    if hasattr(cls._context, key):  # Check if still exists
                        delattr(cls._context, key)
                elif key in previous_values:
                    setattr(cls._context, key, previous_values[key])
                # Else: key wasn't present before and wasn't added, do nothing

    @classmethod
    def get_thread_context(cls) -> Dict[str, Any]:
        """Returns a dictionary of the current thread's context."""
        return {k: v for k, v in vars(cls._context).items() if not k.startswith("_")}

    # --- Core Logging Method ---

    @classmethod
    def _log(
        cls,
        level: LogLevel,
        message: str,
        exc_info: Optional[
            Union[bool, BaseException, Tuple[Type[BaseException], BaseException, Any]]
        ] = None,
        **kwargs: Any,
    ) -> None:
        """
        Internal method to dispatch a log record to handlers.

        Args:
            level: The log level.
            message: The main log message.
            exc_info: Optional exception information.
                      If True, sys.exc_info() is used.
                      If an Exception instance, its info is used.
                      If a tuple (type, value, tb), it's used directly.
            **kwargs: Additional data passed to formatters and handlers.
                      Internal kwargs like _raw_color are used by ConsoleHandler.
        """
        if level < cls._global_level:
            return  # Filtered out by global level

        timestamp = datetime.now()
        final_exc_info = None

        # Process exc_info
        if exc_info:
            if isinstance(exc_info, BaseException):
                final_exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            elif isinstance(exc_info, tuple) and len(exc_info) == 3:
                final_exc_info = exc_info
            elif exc_info is True:  # Check explicitly for True
                final_exc_info = sys.exc_info()
                if final_exc_info[0] is None:  # No active exception
                    final_exc_info = None

        # Iterate safely over handlers
        current_handlers: List[Handler] = []
        with cls._handler_lock:
            current_handlers = cls._handlers[:]  # Create a copy

        for handler in current_handlers:
            try:
                handler.handle(level, message, timestamp, final_exc_info, **kwargs)
            except Exception as e:
                # If a handler fails, report error directly to stderr
                # Use direct print to avoid recursion
                print(
                    f"{cls.color_bright_red}PANIC: Handler {type(handler).__name__} "
                    f"failed: {e}\n{get_trace_exception(e)}{cls.color_reset}",
                    file=sys.stderr,
                )

    # --- Semantic Logging Methods ---

    @classmethod
    def debug(cls, message: str, **kwargs: Any) -> None:
        """Logs a message with DEBUG level."""
        cls._log(LogLevel.DEBUG, message, **kwargs)

    @classmethod
    def info(cls, message: str, **kwargs: Any) -> None:
        """
        Logs a message with INFO level.

        Note: The 'color' kwarg previously used here is deprecated.
              Use specific color methods (e.g., ASCIIColors.green) or
              configure handler formatters if custom console color is needed.
        """
        if "color" in kwargs:
            # If old 'color' kwarg is passed, map it for ConsoleHandler
            kwargs["_raw_color"] = kwargs.pop("color")
        cls._log(LogLevel.INFO, message, **kwargs)

    @classmethod
    def warning(cls, message: str, **kwargs: Any) -> None:
        """Logs a message with WARNING level."""
        cls._log(LogLevel.WARNING, message, **kwargs)

    @classmethod
    def error(
        cls,
        message: str,
        exc_info: Optional[
            Union[bool, BaseException, Tuple[Type[BaseException], BaseException, Any]]
        ] = None,
        **kwargs: Any,
    ) -> None:
        """
        Logs a message with ERROR level.

        Args:
            message: The error message.
            exc_info: Optional exception info to include in the log.
                      Set to True to capture current exception, or pass
                      an exception instance or tuple.
            **kwargs: Additional context.
        """
        cls._log(LogLevel.ERROR, message, exc_info=exc_info, **kwargs)

    # --- Backward Compatibility & Direct Color Methods ---

    @classmethod
    def print(
        cls,
        text: str,
        color: str = color_white,  # Default to white for general print
        style: str = "",
        end: str = "\n",
        flush: bool = False,
    ) -> None:
        """
        Prints a message, routing through the INFO level logger.

        Color/Style args primarily affect ConsoleHandler.
        End/Flush args only affect ConsoleHandler.

        Prefer using semantic methods (info, warning, etc.) or specific
        color methods (red, green, etc.) for clarity.

        Args:
            text: The text to print.
            color: ANSI color code.
            style: ANSI style code.
            end: String appended after the message (console only).
            flush: Whether to forcibly flush the stream (console only).
        """
        cls._log(
            LogLevel.INFO,
            text,
            _raw_color=color,
            _raw_style=style,
            _raw_end=end,
            _raw_flush=flush,
        )

    # Static methods for direct color printing (map to INFO level)
    @staticmethod
    def success(text: str, end: str = "\n", flush: bool = False) -> None:
        """Prints text in green using INFO level."""
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_green,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def fail(text: str, end: str = "\n", flush: bool = False) -> None:
        """Prints text in red using ERROR level."""
        ASCIIColors._log(
            LogLevel.ERROR,
            text,
            _raw_color=ASCIIColors.color_red,
            _raw_end=end,
            _raw_flush=flush,
        )

    # Color-specific static methods (all map to INFO level by default)
    @staticmethod
    def black(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_black,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def red(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_red,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def green(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_green,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def yellow(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_yellow,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def blue(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_blue,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def magenta(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_magenta,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def cyan(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_cyan,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def white(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_white,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def orange(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_orange,
            _raw_end=end,
            _raw_flush=flush,
        )

    # Bright color methods
    @staticmethod
    def bright_black(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_bright_black,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def bright_red(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_bright_red,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def bright_green(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_bright_green,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def bright_yellow(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_bright_yellow,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def bright_blue(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_bright_blue,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def bright_magenta(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_bright_magenta,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def bright_cyan(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_bright_cyan,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def bright_white(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_bright_white,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def bright_orange(text: str, end: str = "\n", flush: bool = False) -> None:
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=ASCIIColors.color_bright_orange,
            _raw_end=end,
            _raw_flush=flush,
        )

    # Style methods
    @staticmethod
    def bold(
        text: str, color: str = color_white, end: str = "\n", flush: bool = False
    ) -> None:
        """Prints bold text using INFO level."""
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=color,
            _raw_style=ASCIIColors.style_bold,
            _raw_end=end,
            _raw_flush=flush,
        )

    @staticmethod
    def underline(
        text: str, color: str = color_white, end: str = "\n", flush: bool = False
    ) -> None:
        """Prints underlined text using INFO level."""
        ASCIIColors._log(
            LogLevel.INFO,
            text,
            _raw_color=color,
            _raw_style=ASCIIColors.style_underline,
            _raw_end=end,
            _raw_flush=flush,
        )

    # --- Utility & Direct Console Manipulation Methods ---
    # These methods interact directly with print and are not routed through logging handlers

    @staticmethod
    def multicolor(
        texts: List[str], colors: List[str], end: str = "\n", flush: bool = False
    ) -> None:
        """Prints multiple text segments with corresponding colors directly to console."""
        with ASCIIColors._handler_lock:  # Use lock just in case, though direct print is less safe
            for text, color in zip(texts, colors):
                print(f"{color}{text}", end="", flush=True)  # Flush each part
            print(ASCIIColors.color_reset, end=end, flush=flush)  # Reset at the end

    @staticmethod
    def highlight(
        text: str,
        subtext: Union[str, List[str]],
        color: str = color_white,
        highlight_color: str = color_yellow,  # Changed default highlight
        whole_line: bool = False,
    ) -> None:
        """Highlights occurrences of subtext within text directly on the console."""
        if isinstance(subtext, str):
            subtext = [subtext]

        output = ""
        if whole_line:
            lines = text.split("\n")
            for line in lines:
                if any(st in line for st in subtext):
                    output += f"{highlight_color}{line}{ASCIIColors.color_reset}\n"
                else:
                    output += f"{color}{line}{ASCIIColors.color_reset}\n"
            # Remove trailing newline added by loop
            output = output.rstrip("\n")
        else:
            processed_text = text
            for st in subtext:
                # Ensure reset happens correctly after highlight
                replacement = f"{highlight_color}{st}{color}"
                processed_text = processed_text.replace(st, replacement)
            output = f"{color}{processed_text}{ASCIIColors.color_reset}"

        # Print the final result directly
        with ASCIIColors._handler_lock:  # Use lock for safety
            print(output)

    @staticmethod
    def activate(color_or_style: str) -> None:
        """Activates a color or style directly on the console."""
        # Direct print - not thread safe with logging if handlers also use stdout
        print(f"{color_or_style}", end="", flush=True)

    @staticmethod
    def reset() -> None:
        """Resets all colors and styles directly on the console."""
        print(ASCIIColors.color_reset, end="", flush=True)

    # --- Convenience activation methods ---
    @staticmethod
    def activateRed() -> None:
        ASCIIColors.activate(ASCIIColors.color_red)

    @staticmethod
    def activateGreen() -> None:
        ASCIIColors.activate(ASCIIColors.color_green)

    @staticmethod
    def activateBlue() -> None:
        ASCIIColors.activate(ASCIIColors.color_blue)

    @staticmethod
    def activateYellow() -> None:
        ASCIIColors.activate(ASCIIColors.color_yellow)

    @staticmethod
    def activateBold() -> None:
        ASCIIColors.activate(ASCIIColors.style_bold)

    @staticmethod
    def activateUnderline() -> None:
        ASCIIColors.activate(ASCIIColors.style_underline)

    @staticmethod
    def resetColor() -> None:
        ASCIIColors.reset()  # Resetting color resets all

    @staticmethod
    def resetStyle() -> None:
        ASCIIColors.reset()  # Resetting style resets all

    @staticmethod
    def resetAll() -> None:
        ASCIIColors.reset()

    # --- Other Utilities ---

    @staticmethod
    def execute_with_animation(
        pending_text: str,
        func: Callable[..., Any],
        *args: Any,
        color: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Executes a function while displaying a pending text animation.

        Args:
            pending_text: Text to display during execution.
            func: The function to execute.
            *args: Positional arguments for func.
            color: Optional ANSI color for the pending text (defaults to yellow).
            **kwargs: Keyword arguments for func.

        Returns:
            The return value of the executed function.
        """
        animation = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        stop_event = threading.Event()
        result = [None]  # Use list to pass result out of thread scope if needed
        exception = [None]  # To capture exception from thread
        thread_lock = Lock()  # To protect access to result/exception

        # Default to yellow if no color is specified
        text_color = color if color else ASCIIColors.color_yellow
        checkbox = "✓"

        def animate():
            idx = 0
            while not stop_event.is_set():
                # Direct print for animation control
                animation_char = animation[idx % len(animation)]
                # Split print for line length
                print(
                    f"\r{text_color}{pending_text} {animation_char}{ASCIIColors.color_reset}  ",
                    end="",
                    flush=True,
                )
                idx += 1
                time.sleep(0.1)

        def target():
            try:
                res = func(*args, **kwargs)
                with thread_lock:
                    result[0] = res
            except Exception as e_inner:
                with thread_lock:
                    exception[0] = e_inner
            finally:
                stop_event.set()

        worker_thread = threading.Thread(target=target)
        animation_thread = threading.Thread(target=animate)

        worker_thread.start()
        animation_thread.start()

        worker_thread.join()  # Wait for the worker to finish
        stop_event.set()  # Ensure animation stops even if worker finished quickly
        animation_thread.join()  # Wait for animation to print final state

        with thread_lock:
            final_exception = exception[0]
            final_result = result[0]

        # Determine final status symbol and color
        final_symbol = checkbox
        final_color = ASCIIColors.color_green
        if final_exception:
            final_symbol = "✗"  # Cross mark for failure
            final_color = ASCIIColors.color_red

        # Clear the line and show completion status
        # Ensure this print happens after animation thread joined
        status_line = f"\r{text_color}{pending_text} {final_color}{final_symbol}\
{ASCIIColors.color_reset}          "
        print(status_line, flush=True)
        print()  # Move to next line

        # Re-raise exception if one occurred
        if final_exception:
            raise final_exception

        return final_result


# --- Global convenience function ---
def trace_exception(ex: BaseException) -> None:
    """
    Logs the traceback of an exception using ASCIIColors.error.

    Args:
        ex: The exception instance.
    """
    ASCIIColors.error(f"Exception Traceback ({type(ex).__name__})", exc_info=ex)


# --- Example Usage ---
if __name__ == "__main__":
    print("--- Basic Color/Style Demo ---")
    ASCIIColors.red("This is red text")
    ASCIIColors.green("This is green text (success style)")
    ASCIIColors.yellow("This is yellow text")
    ASCIIColors.blue("This is blue text")
    ASCIIColors.bold("This is bold white text", color=ASCIIColors.color_white)
    ASCIIColors.underline("This is underlined cyan text", color=ASCIIColors.color_cyan)
    ASCIIColors.print(
        "Custom print: Orange bold",
        color=ASCIIColors.color_orange,
        style=ASCIIColors.style_bold,
    )

    print("\n--- Multicolor & Highlight Demo ---")
    ASCIIColors.multicolor(
        ["Formatted ", "using ", "multicolor "],
        [ASCIIColors.color_red, ASCIIColors.color_green, ASCIIColors.color_blue],
    )
    ASCIIColors.highlight(
        "Find the KEYWORD in this line.",
        "KEYWORD",
        highlight_color=ASCIIColors.color_bright_magenta,
    )
    ASCIIColors.highlight(
        "Highlight\nthe whole line\nif it contains a keyword.",
        ["line", "keyword"],
        whole_line=True,
    )

    print("\n--- Logging Demo (Console Only - Default) ---")
    ASCIIColors.set_log_level(LogLevel.DEBUG)  # Show all levels
    ASCIIColors.debug("This is a debug message.")
    ASCIIColors.info("This is an info message.")
    ASCIIColors.warning("This is a warning message.")
    ASCIIColors.error("This is an error message.")

    print("\n--- Logging with File Handler ---")
    log_file = Path("temp_app.log")
    if log_file.exists():
        log_file.unlink()  # Clean up previous run
    file_handler = FileHandler(
        log_file, level=LogLevel.INFO
    )  # Log INFO and above to file
    # Customize file formatter
    file_formatter = Formatter(
        fmt="[{datetime}] {level_name}: {message} (from {func_name})",
        include_source=True,
    )
    file_handler.set_formatter(file_formatter)
    ASCIIColors.add_handler(file_handler)
    print(f"Logging INFO, WARNING, ERROR to {log_file}")
    ASCIIColors.debug(
        "This debug message goes only to console."
    )  # Below file handler level
    ASCIIColors.info("Info message logged to console and file.")
    ASCIIColors.warning("Warning logged to console and file.")
    try:
        x = 1 / 0
    except ZeroDivisionError as e:
        ASCIIColors.error("An error occurred!", exc_info=e)  # Log error with traceback
        # Also demonstrating trace_exception utility
        trace_exception(e)

    print(f"Check '{log_file}' for file output.")

    print("\n--- Context Management Demo ---")
    ASCIIColors.set_context(session_id="XYZ")
    ASCIIColors.info("Processing with session context.")
    with ASCIIColors.context(user_id=123, task="upload"):
        ASCIIColors.info("Inside user task context.")
        ASCIIColors.set_context(sub_task="chunk_1")
        ASCIIColors.info("Deeper context added.")
    ASCIIColors.info("Outside user task context (session_id still present).")
    ASCIIColors.clear_context()  # Clear all thread context
    ASCIIColors.info("Context cleared.")

    print("\n--- Animation Demo ---")

    def long_task(duration: float, task_name: str):
        print(
            f"\nStarting task '{task_name}' (will take {duration}s)..."
        )  # Direct print inside task
        time.sleep(duration)
        return f"Task '{task_name}' completed successfully."

    result = ASCIIColors.execute_with_animation(
        "Running long task...",
        long_task,
        3,
        "Data Processing",
        color=ASCIIColors.color_cyan,
    )
    ASCIIColors.success(f"Animation Result: {result}")

    # Example of animation with failure
    def failing_task():
        time.sleep(2)
        raise ValueError("Something went wrong in the task")

    try:
        ASCIIColors.execute_with_animation(
            "Running failing task...", failing_task, color=ASCIIColors.color_magenta
        )
    except ValueError as e:
        ASCIIColors.fail(f"Caught expected exception from animation: {e}")

    # Clean up log file if needed
    # if log_file.exists(): log_file.unlink()
