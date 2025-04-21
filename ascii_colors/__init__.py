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
            **kwargs: Additional contextual keyword arguments passed via logging methods
                      or set via thread context.

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
                # Navigate up past internal logging/formatting frames
                while (
                    frame
                    and Path(frame.f_code.co_filename).parent.name == "ascii_colors"
                    and frame.f_code.co_name in ('_log', 'format', 'handle', 'emit', 'debug', 'info', 'warning', 'error', 'trace_exception')
                ):
                    frame = frame.f_back
                if frame:
                    file_name = Path(frame.f_code.co_filename).name
                    line_no = frame.f_lineno
                    func_name = frame.f_code.co_name
                # Clean up frame reference
                del frame
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
                    and frame.f_code.co_name in ('_log', 'format', 'handle', 'emit', 'debug', 'info', 'warning', 'error', 'trace_exception')
                ):
                    frame = frame.f_back
                if frame:
                    file_name = Path(frame.f_code.co_filename).name
                    line_no = frame.f_lineno
                    func_name = frame.f_code.co_name
                # Clean up frame reference
                del frame
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

    Handlers dispatch formatted log records to the appropriate destination (console, file, etc.).
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
        Handles a log record if its level meets the handler's threshold.

        Filters by level, formats the record using the assigned formatter,
        and calls the emit method.

        Args:
            level: The log level of the record.
            message: The log message.
            timestamp: The datetime of the log event.
            exc_info: Exception tuple, if any.
            **kwargs: Additional context passed for formatting.
        """
        if level >= self.level:
            formatted_message = self.formatter.format(
                level, message, timestamp, exc_info, **kwargs
            )
            self.emit(level, formatted_message) # Pass only level and formatted msg

    @abstractmethod
    def emit(self, level: LogLevel, formatted_message: str):
        """
        Emits the formatted log record. Must be implemented by subclasses.

        Args:
            level: The original log level (passed for potential handler-specific logic, like coloring).
            formatted_message: The final string produced by the formatter.
        """
        raise NotImplementedError


class ConsoleHandler(Handler):
    """
    Handles logging to the console (stdout/stderr).

    Applies ANSI color codes based on the log level.
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

    def emit(self, level: LogLevel, formatted_message: str):
        """Prints the formatted message to the console with level-based colors."""
        # Determine color based on the log level
        color = ASCIIColors._level_colors.get(level, ASCIIColors.color_white)

        # Construct the output string with color
        output = f"{color}{formatted_message}{ASCIIColors.color_reset}\n" # Add newline manually

        # Use the lock for thread-safe writing TO THE STREAM directly
        with self._lock:
            try:
                self.stream.write(output)
                self.stream.flush() # Ensure output is flushed
            except Exception as e:
                 # Fallback to stderr if writing to stream fails catastrophically
                 print(
                     f"{ASCIIColors.color_bright_red}PANIC: ConsoleHandler failed to write to stream: {e}{ASCIIColors.color_reset}",
                     file=sys.stderr,
                     flush=True
                 )


class FileHandler(Handler):
    """
    Handles logging to a file. Does not add color codes.
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
            formatter: Formatter instance. Defaults to basic Formatter (no source info).
            encoding: File encoding.
        """
        # Ensure formatter doesn't include source by default for file perf
        default_formatter = Formatter(include_source=False)
        super().__init__(level, formatter if formatter else default_formatter)
        self.filename = Path(filename)
        self.encoding = encoding
        # Ensure directory exists
        self.filename.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, level: LogLevel, formatted_message: str):
        """Writes the formatted message to the log file."""
        try:
            # File operations are protected by the handler's lock
            with self._lock:
                with open(self.filename, "a", encoding=self.encoding) as f:
                    f.write(formatted_message + "\n")
        except Exception as e:
            # Critical error: Cannot write to log file. Print directly to stderr.
            # Use direct print to avoid potential recursion if stderr uses this handler.
            # Also use direct color codes for panic message.
            print(
                f"{ASCIIColors.color_bright_red}PANIC: Failed to write to log file "
                f"{self.filename}: {e}{ASCIIColors.color_reset}",
                file=sys.stderr,
                flush=True
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

    def emit(self, level: LogLevel, formatted_message: str):
        """Writes to the file after potentially rotating it."""
        if self.should_rotate():
            self.do_rollover()
        super().emit(
            level, formatted_message
        )  # Call parent FileHandler's emit

    def should_rotate(self) -> bool:
        """Checks if the log file needs rotation based on size."""
        if self.maxBytes <= 0:
            return False
        try:
            # Check file size only if it exists and we need rotation
            if self.filename.exists():
                with self._lock: # Ensure consistent size check
                    file_size = self.filename.stat().st_size
                return file_size >= self.maxBytes
        except OSError:  # Handle potential race condition or permission error
            return False
        return False  # Default case if file doesn't exist or maxBytes is 0

    def do_rollover(self):
        """Performs the log file rotation."""
        # Use lock to ensure rotation is atomic relative to writes
        with self._lock:
            # Re-check condition inside lock to prevent race conditions
            if not self.filename.exists() or self.filename.stat().st_size < self.maxBytes:
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
                # Need to check existence again as check+rename is not atomic outside lock
                if self.filename.exists():
                    try:
                        self.filename.rename(f"{self.filename}.1")
                    except OSError:
                        pass  # Ignore errors renaming current

            else:  # No backup count, just truncate the current file
                if self.filename.exists():
                    try:
                        # Open in 'w' mode to truncate
                        with open(self.filename, 'w', encoding=self.encoding) as f:
                            f.truncate(0)
                    except OSError:
                        pass # Ignore errors truncating


# --- Main ASCIIColors Class ---


class ASCIIColors:
    """
    Provides methods for colored console output and enhanced logging.

    Logging Methods (debug, info, warning, error): Use handlers/formatters.
    Direct Print Methods (red, green, print, etc.): Print directly to console with color.
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
        LogLevel.INFO: color_bright_blue,
        LogLevel.WARNING: color_bright_orange,
        LogLevel.ERROR: color_bright_red,
    }

    # --- Thread-Local Context ---
    _context = threading.local()

    # --- Logging Configuration Methods ---

    @classmethod
    def set_log_level(cls, level: Union[LogLevel, int]) -> None:
        """
        Sets the *global* minimum log level for the logging system.

        Messages below this level will not be processed by any handler via
        the debug(), info(), warning(), error() methods.
        Direct print methods (red(), green(), etc.) are unaffected.

        Args:
            level: The minimum LogLevel or its integer value.
        """
        cls._global_level = LogLevel(level)

    @classmethod
    def add_handler(cls, handler: Handler) -> None:
        """Adds a log handler to the list of active handlers for the logging system."""
        with cls._handler_lock:
            if handler not in cls._handlers:
                cls._handlers.append(handler)

    @classmethod
    def remove_handler(cls, handler: Handler) -> None:
        """Removes a specific handler instance from the logging system."""
        with cls._handler_lock:
            try:
                cls._handlers.remove(handler)
            except ValueError:
                pass  # Handler not found, ignore

    @classmethod
    def clear_handlers(cls) -> None:
        """Removes all configured handlers from the logging system."""
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
        [Backward Compatibility] Adds a FileHandler for the given path to the logging system.

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

        This method is no longer functional as formatting is handler-specific.
        Calling it will log a warning.

        Args:
            level: The log level (ignored).
            template: The template string (ignored).
        """
        cls.warning(
            "ASCIIColors.set_template is DEPRECATED and has no effect. "
            "Configure formatters on individual handlers instead."
        )

    # --- Context Management (for Logging System) ---

    @classmethod
    def set_context(cls, **kwargs: Any) -> None:
        """
        Sets key-value pairs in the current thread's context for logging.

        These values will be available to formatters ({key}) when using
        debug(), info(), warning(), error().
        """
        for key, value in kwargs.items():
            setattr(cls._context, key, value)

    @classmethod
    def clear_context(cls, *args: str) -> None:
        """
        Clears keys from the current thread's logging context.

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
        Context manager to temporarily add thread-local context for logging.

        Usage:
            with ASCIIColors.context(request_id="123"):
                ASCIIColors.info("Processing request") # Log includes request_id
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
                        try:
                            delattr(cls._context, key)
                        except AttributeError: pass # Might have been deleted externally
                elif key in previous_values:
                    setattr(cls._context, key, previous_values[key])
                # Else: key wasn't present before and wasn't added/restored, do nothing

    @classmethod
    def get_thread_context(cls) -> Dict[str, Any]:
        """Returns a dictionary of the current thread's logging context."""
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
        Internal method to dispatch a log record to configured handlers.

        Args:
            level: The log level.
            message: The main log message.
            exc_info: Optional exception information.
                      If True, sys.exc_info() is used.
                      If an Exception instance, its info is used.
                      If a tuple (type, value, tb), it's used directly.
            **kwargs: Additional data passed to formatters via context merge.
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
                try:
                    final_exc_info = sys.exc_info()
                    # Ensure an actual exception is being handled
                    if final_exc_info[0] is None or final_exc_info[1] is None:
                        final_exc_info = None
                except Exception: # If sys.exc_info() fails unexpectedly
                    final_exc_info = None


        # Iterate safely over handlers
        current_handlers: List[Handler] = []
        with cls._handler_lock:
            current_handlers = cls._handlers[:]  # Create a copy

        for handler in current_handlers:
            try:
                # Pass kwargs which will be merged with thread context by formatter
                handler.handle(level, message, timestamp, final_exc_info, **kwargs)
            except Exception as e:
                # If a handler fails, report error directly to stderr
                # Use direct print with color codes to avoid recursion
                print(
                    f"{cls.color_bright_red}PANIC: Handler {type(handler).__name__} "
                    f"failed: {e}\n{get_trace_exception(e)}{cls.color_reset}",
                    file=sys.stderr,
                    flush=True
                )

    # --- Semantic Logging Methods (Use Handlers/Formatters) ---

    @classmethod
    def debug(cls, message: str, **kwargs: Any) -> None:
        """Logs a message with DEBUG level using the configured logging handlers."""
        cls._log(LogLevel.DEBUG, message, **kwargs)

    @classmethod
    def info(cls, message: str, **kwargs: Any) -> None:
        """Logs a message with INFO level using the configured logging handlers."""
        cls._log(LogLevel.INFO, message, **kwargs)

    @classmethod
    def warning(cls, message: str, **kwargs: Any) -> None:
        """Logs a message with WARNING level using the configured logging handlers."""
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
        Logs a message with ERROR level using the configured logging handlers.

        Args:
            message: The error message.
            exc_info: Optional exception info to include in the log output.
                      Set to True to capture current exception, or pass
                      an exception instance or tuple (type, value, traceback).
            **kwargs: Additional context for formatters.
        """
        cls._log(LogLevel.ERROR, message, exc_info=exc_info, **kwargs)

    # --- Direct Console Print Methods (Bypass Logging System) ---

    @staticmethod
    def print(
        text: str,
        color: str = color_white, # Default to white for general print
        style: str = "",
        end: str = "\n",
        flush: bool = False,
        file: TextIO = sys.stdout, # Allow specifying output stream
    ) -> None:
        """
        Prints text directly to the console with specified color and style.
        Bypasses the logging system (handlers/formatters/levels).

        Args:
            text: The text to print.
            color: ANSI color code (e.g., ASCIIColors.color_red).
            style: ANSI style code (e.g., ASCIIColors.style_bold).
            end: String appended after the message.
            flush: Whether to forcibly flush the stream.
            file: The output stream (default: sys.stdout).
        """
        print(f"{style}{color}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    # Static methods for direct color printing (bypass logging)
    @staticmethod
    def success(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        """Prints text directly to console in green."""
        print(f"{ASCIIColors.color_green}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def fail(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        """Prints text directly to console in red."""
        print(f"{ASCIIColors.color_red}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    # Color-specific static methods for direct printing
    @staticmethod
    def black(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_black}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def red(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_red}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def green(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_green}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def yellow(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_yellow}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def blue(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_blue}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def magenta(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_magenta}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def cyan(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_cyan}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def white(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_white}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def orange(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_orange}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    # Bright color methods for direct printing
    @staticmethod
    def bright_black(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_bright_black}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def bright_red(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_bright_red}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def bright_green(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_bright_green}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def bright_yellow(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_bright_yellow}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def bright_blue(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_bright_blue}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def bright_magenta(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_bright_magenta}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def bright_cyan(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_bright_cyan}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def bright_white(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_bright_white}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def bright_orange(text: str, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout) -> None:
        print(f"{ASCIIColors.color_bright_orange}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    # Style methods for direct printing
    @staticmethod
    def bold(
        text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout
    ) -> None:
        """Prints bold text directly to console."""
        print(f"{ASCIIColors.style_bold}{color}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    @staticmethod
    def underline(
        text: str, color: str = color_white, end: str = "\n", flush: bool = False, file: TextIO = sys.stdout
    ) -> None:
        """Prints underlined text directly to console."""
        print(f"{ASCIIColors.style_underline}{color}{text}{ASCIIColors.color_reset}", end=end, flush=flush, file=file)

    # --- Utility & Direct Console Manipulation Methods ---
    # These methods interact directly with print and do not use the logging system.

    @staticmethod
    def multicolor(
        texts: List[str], colors: List[str], end: str = "\n", flush: bool = False, file: TextIO = sys.stdout
    ) -> None:
        """Prints multiple text segments with corresponding colors directly to console."""
        # No need for lock as it uses builtin print directly
        for text, color in zip(texts, colors):
            print(f"{color}{text}", end="", flush=True, file=file) # Flush each part
        print(ASCIIColors.color_reset, end=end, flush=flush, file=file) # Reset at the end

    @staticmethod
    def highlight(
        text: str,
        subtext: Union[str, List[str]],
        color: str = color_white,
        highlight_color: str = color_yellow,
        whole_line: bool = False,
        end: str = "\n",
        flush: bool = False,
        file: TextIO = sys.stdout,
    ) -> None:
        """Highlights occurrences of subtext within text directly on the console."""
        if isinstance(subtext, str):
            subtext = [subtext]

        output = ""
        if whole_line:
            lines = text.splitlines() # Use splitlines to handle different line endings
            for i, line in enumerate(lines):
                is_last_line = i == len(lines) - 1
                line_end = "" if is_last_line else "\n" # Add newline except for last line
                if any(st in line for st in subtext):
                    output += f"{highlight_color}{line}{ASCIIColors.color_reset}{line_end}"
                else:
                    output += f"{color}{line}{ASCIIColors.color_reset}{line_end}"
        else:
            processed_text = text
            for st in subtext:
                # Ensure reset happens correctly after highlight
                replacement = f"{highlight_color}{st}{color}" # Go back to base color
                processed_text = processed_text.replace(st, replacement)
            # Apply initial color and final reset
            output = f"{color}{processed_text}{ASCIIColors.color_reset}"

        # Print the final result directly
        print(output, end=end, flush=flush, file=file)

    @staticmethod
    def activate(color_or_style: str, file: TextIO = sys.stdout) -> None:
        """Activates a color or style directly on the console."""
        print(f"{color_or_style}", end="", flush=True, file=file)

    @staticmethod
    def reset(file: TextIO = sys.stdout) -> None:
        """Resets all colors and styles directly on the console."""
        print(ASCIIColors.color_reset, end="", flush=True, file=file)

    # --- Convenience activation methods ---
    # These activate colors/styles directly on stdout by default
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
        ASCIIColors.reset() # Resetting color resets all

    @staticmethod
    def resetStyle() -> None:
        ASCIIColors.reset() # Resetting style resets all

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
        Executes a function while displaying a pending text animation (direct print).
        Uses ASCIIColors.print internally for animation frames and status.

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
        result = [None]
        exception = [None]
        thread_lock = Lock()

        text_color = color if color else ASCIIColors.color_yellow
        success_symbol = "✓"
        failure_symbol = "✗"

        def animate():
            idx = 0
            while not stop_event.is_set():
                animation_char = animation[idx % len(animation)]
                # Use ASCIIColors.print for animation frames
                # Ensure file=sys.stdout for animation
                ASCIIColors.print(
                    f"\r{text_color}{pending_text} {animation_char}", # No reset here yet
                    color="", # Color is applied manually above
                    style="",
                    end="",
                    flush=True,
                    file=sys.stdout # Explicitly stdout
                )
                idx += 1
                time.sleep(0.1)
            # Clear the animation character after stopping
            ASCIIColors.print(f"\r{text_color}{pending_text}  ", color="", style="", end="", flush=True, file=sys.stdout)


        def target():
            try:
                res = func(*args, **kwargs)
                with thread_lock: result[0] = res
            except Exception as e_inner:
                with thread_lock: exception[0] = e_inner
            finally: stop_event.set()

        worker_thread = threading.Thread(target=target)
        animation_thread = threading.Thread(target=animate)

        worker_thread.start(); animation_thread.start()
        worker_thread.join(); stop_event.set(); animation_thread.join()

        with thread_lock:
            final_exception = exception[0]; final_result = result[0]

        final_symbol = success_symbol; final_color = ASCIIColors.color_green
        if final_exception:
            final_symbol = failure_symbol; final_color = ASCIIColors.color_red

        # Use ASCIIColors.print for final status line
        # Overwrite the pending text line
        status_line = f"\r{text_color}{pending_text} {final_color}{final_symbol}{ASCIIColors.color_reset}          "
        ASCIIColors.print(status_line, color="", style="", flush=True, file=sys.stdout)
        # Move to next line using ASCIIColors.print
        ASCIIColors.print("", color="", style="", file=sys.stdout) # Essentially prints a newline

        if final_exception: raise final_exception
        return final_result


# --- Global convenience function (Uses Logging) ---
def trace_exception(ex: BaseException) -> None:
    """
    Logs the traceback of an exception using ASCIIColors.error (logging system).

    Args:
        ex: The exception instance.
    """
    ASCIIColors.error(f"Exception Traceback ({type(ex).__name__})", exc_info=ex)


# --- Example Usage (Updated) ---
if __name__ == "__main__":
    print("--- Direct Color/Style Print Demo (Bypasses Logging) ---")
    ASCIIColors.red("This is red text (direct print)")
    ASCIIColors.green("This is green text (direct print)")
    ASCIIColors.yellow("This is yellow text (direct print)")
    ASCIIColors.blue("This is blue text (direct print)")
    ASCIIColors.bold("This is bold white text (direct print)", color=ASCIIColors.color_white)
    ASCIIColors.underline("This is underlined cyan text (direct print)", color=ASCIIColors.color_cyan)
    ASCIIColors.print( # Uses the direct print method
        "Custom direct print: Orange bold",
        color=ASCIIColors.color_orange,
        style=ASCIIColors.style_bold,
    )

    print("\n--- Multicolor & Highlight Demo (Direct Print) ---")
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

    print("\n--- Logging Demo (Uses Handlers/Formatters) ---")
    # Reset handlers and level for demo clarity
    ASCIIColors.clear_handlers()
    ASCIIColors.add_handler(ConsoleHandler(level=LogLevel.DEBUG)) # Add default console handler back
    ASCIIColors.set_log_level(LogLevel.DEBUG)  # Show all levels for logging

    ASCIIColors.debug("This is a debug log message.")
    ASCIIColors.info("This is an info log message.")
    ASCIIColors.warning("This is a warning log message.")
    ASCIIColors.error("This is an error log message.")

    print("\n--- Logging with File Handler (No Colors in File) ---")
    log_file = Path("temp_app.log")
    if log_file.exists():
        log_file.unlink()  # Clean up previous run

    # Setup console handler (shows DEBUG+) and file handler (shows INFO+)
    ASCIIColors.clear_handlers()
    ASCIIColors.add_handler(ConsoleHandler(level=LogLevel.DEBUG))

    file_formatter = Formatter(
        fmt="[{datetime}] {level_name:<8} [{func_name}] {message}", # Include func_name
        datefmt="%Y-%m-%d %H:%M:%S",
        include_source=True
    )
    file_handler = FileHandler(log_file, level=LogLevel.INFO, formatter=file_formatter)
    ASCIIColors.add_handler(file_handler)
    ASCIIColors.set_log_level(LogLevel.DEBUG) # Global level allows DEBUG

    print(f"\nLogging DEBUG+ to console, INFO+ to '{log_file}'")
    ASCIIColors.debug("This debug log goes only to console.")
    ASCIIColors.info("Info log logged to console and file.")
    ASCIIColors.warning("Warning log logged to console and file.")
    try:
        x = 1 / 0
    except ZeroDivisionError as e:
        ASCIIColors.error("An error occurred!", exc_info=e, detail="Division by zero")
        # Also demonstrating trace_exception utility (uses logging)
        trace_exception(e)

    print(f"\nCheck '{log_file}' for file output (should contain INFO, WARNING, ERROR logs).")
    if log_file.exists():
        print("--- Log File Content ---")
        print(log_file.read_text())
        print("--- End Log File Content ---")


    print("\n--- Context Management Demo (Affects Logging Only) ---")
    # Need a formatter that uses context variables
    context_formatter = Formatter("[{level_name}] (Session:{session_id}) {message}")
    # Apply to the first handler (console)
    if ASCIIColors._handlers:
         ASCIIColors._handlers[0].set_formatter(context_formatter)

    ASCIIColors.set_context(session_id="XYZ")
    ASCIIColors.info("Processing with session context (logged).") # Logged
    ASCIIColors.red("This direct red print ignores context.") # Direct print

    with ASCIIColors.context(user_id=123, task="upload"): # user_id, task not in formatter
        ASCIIColors.info("Inside user task context (logged).") # Logged, still shows session_id
        ASCIIColors.set_context(sub_task="chunk_1") # sub_task not in formatter
        ASCIIColors.info("Deeper context added (logged).") # Logged, still shows session_id
    ASCIIColors.info("Outside user task context (logged, session_id still present).") # Logged
    ASCIIColors.clear_context()  # Clear all thread context
    # Change formatter back or expect format errors
    if ASCIIColors._handlers:
         ASCIIColors._handlers[0].set_formatter(Formatter("[{level_name}] {message}"))
    ASCIIColors.info("Context cleared (logged).") # Logged

    print("\n--- Animation Demo (Uses Direct Print) ---")

    def long_task(duration: float, task_name: str):
        # Use direct print inside the task if needed, or logging
        ASCIIColors.blue(f">> Starting task '{task_name}' (will take {duration}s)...")
        time.sleep(duration)
        return f"Task '{task_name}' completed successfully."

    result = ASCIIColors.execute_with_animation(
        "Running long task...",
        long_task,
        2, # Shorter duration for testing
        "Data Processing",
        color=ASCIIColors.color_cyan,
    )
    # Use direct print for animation result message
    ASCIIColors.success(f"Animation Result: {result}")

    # Example of animation with failure
    def failing_task():
        time.sleep(1)
        raise ValueError("Something went wrong in the task")

    try:
        ASCIIColors.execute_with_animation(
            "Running failing task...", failing_task, color=ASCIIColors.color_magenta
        )
    except ValueError as e:
        # Use direct print for failure message
        ASCIIColors.fail(f"Caught expected exception from animation: {e}")

    # Clean up log file if needed
    # if log_file.exists(): log_file.unlink()