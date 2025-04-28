# -*- coding: utf-8 -*-
"""
Unit tests for the ascii_colors library, including logging compatibility layer.
Refactored for improved stability and resource management.

Author: Saifeddine ALOUI (ParisNeo)
License: Apache License 2.0
"""

import inspect
import io
import json
import logging as std_logging # Import standard logging for comparison/constants
import os
import re
import shutil
import stat
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, ANY
from threading import Lock
import threading # Needed for ProgressBar tests

# Ensure the module path is correct for testing
try:
    # Import core components
    import ascii_colors # Import the module itself for easier access
    from ascii_colors import (
        ASCIIColors, LogLevel, Formatter, JSONFormatter,
        Handler, ConsoleHandler, FileHandler, RotatingFileHandler,
        ProgressBar, Menu, MenuItem,
        get_trace_exception, trace_exception
    )
    # Import compatibility layer components
    from ascii_colors import (
        getLogger, basicConfig, handlers, # Compatibility functions/objects
        StreamHandler, # Alias for ConsoleHandler
        DEBUG, INFO, WARNING, ERROR, CRITICAL, # Level constants
    )
except ImportError:
    # If running directly from tests directory as script
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import ascii_colors
    from ascii_colors import (
        ASCIIColors, LogLevel, Formatter, JSONFormatter,
        Handler, ConsoleHandler, FileHandler, RotatingFileHandler,
        get_trace_exception, trace_exception
    )
    from ascii_colors import (
        getLogger, basicConfig, handlers, StreamHandler,
        DEBUG, INFO, WARNING, ERROR, CRITICAL,
    )


# Helper to strip ANSI codes (unchanged)
ANSI_ESCAPE_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
def strip_ansi(text: str) -> str:
    """Removes ANSI escape sequences from a string."""
    return ANSI_ESCAPE_REGEX.sub("", text)


class TestASCIIColors(unittest.TestCase):
    """Test suite for ASCIIColors class and related components"""

    def setUp(self):
        """Set up test environment before each test"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ascii_colors_test_")).resolve()
        # Define log file paths within the temp dir
        self.log_file = self.temp_dir / "test.log"
        self.json_log_file = self.temp_dir / "test.jsonl"
        self.rotate_log_file = self.temp_dir / "rotate.log"
        self.compat_log_file = self.temp_dir / "compat.log"

        # --- Reset global state using addCleanup for reliability ---
        self.addCleanup(ASCIIColors.clear_handlers)
        self.addCleanup(lambda: ASCIIColors.set_log_level(LogLevel.WARNING)) # Reset level
        self.addCleanup(setattr, ASCIIColors, '_basicConfig_called', False) # Reset basicConfig flag
        self.addCleanup(ASCIIColors.clear_context)
        # Clear logger cache as well for isolation
        self.addCleanup(ascii_colors._logger_cache.clear)
        # --- End Reset ---

        # Patch builtins.print for testing DIRECT print methods
        # Use addCleanup to ensure the patch is always stopped
        patcher = patch("builtins.print")
        self.mock_builtin_print = patcher.start()
        self.addCleanup(patcher.stop)

        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # Remove the shared mock_log_stream from setup
        # Tests will create their own streams if needed

    def tearDown(self):
        """Clean up test environment after each test"""
        # Temp directory removal with retries (important for Windows)
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            for i in range(3):
                try:
                    shutil.rmtree(self.temp_dir, ignore_errors=False)
                    # print(f"DEBUG: Removed temp dir {self.temp_dir} on attempt {i+1}") # Optional debug
                    break # Success
                except OSError as e:
                    # print(f"DEBUG: Failed removal attempt {i+1} for {self.temp_dir}: {e}", file=sys.stderr) # Optional debug
                    if i < 2: # Only sleep if retrying
                        time.sleep(0.2 * (i + 1)) # Exponential backoff slightly
            else:
                 print(f"\n[TEST ERROR] Could not remove temp dir {self.temp_dir} after retries.", file=sys.stderr)
        elif hasattr(self, 'temp_dir'):
            pass # print(f"DEBUG: Temp dir {self.temp_dir} did not exist in tearDown.") # Optional debug


    # --- Helper methods ---
    def _create_capture_stream_handler(self, level=DEBUG, formatter=None):
        """Creates a ConsoleHandler writing to a new StringIO stream and returns both."""
        capture_stream = io.StringIO()
        self.addCleanup(capture_stream.close) # Ensure stream is closed after test
        if formatter is None:
             formatter = Formatter("{message}", style='{') # Simple default for tests
        handler = ConsoleHandler(stream=capture_stream, level=level, formatter=formatter)
        return handler, capture_stream

    def _get_stream_value(self, stream: io.StringIO) -> str:
        """Gets the value from a StringIO stream."""
        if stream.closed:
            return "[Stream Closed]"
        stream.seek(0)
        return stream.read()

    def assert_direct_print_called_with(self, expected_text_part: str, color_code: str = None, style_code: str = "", **kwargs):
        """Asserts that builtins.print (mocked) was called with expected args."""
        # (Implementation unchanged from previous version, seems okay)
        found_call = False; time.sleep(0.05); calls = self.mock_builtin_print.call_args_list
        expected_file = kwargs.get('file', self.original_stdout)
        for call in calls:
            args, kwargs_call = call
            if not args: continue
            printed_text = args[0]
            if not isinstance(printed_text, str): continue
            stripped_printed = strip_ansi(printed_text).lower().strip()
            # Be more flexible with the text check
            if expected_text_part.lower() in stripped_printed and \
               kwargs_call.get('file', self.original_stdout) == expected_file:
                found_call = True
                expected_start = style_code + (color_code if color_code else "")
                # Allow for potential \r prefix from animation calls captured here
                self.assertTrue(printed_text.lstrip('\r').startswith(expected_start), f"Direct print start mismatch. Expected prefix: '{expected_start}', Got: '{printed_text}'")
                self.assertTrue(printed_text.endswith(ASCIIColors.color_reset), f"Direct print reset mismatch. Got: '{printed_text}'")
                self.assertEqual(kwargs_call.get('end', '\n'), kwargs.get('end', '\n'))
                self.assertEqual(kwargs_call.get('flush', False), kwargs.get('flush', False))
                break
        self.assertTrue(found_call, f"Direct print call containing '{expected_text_part}' with file={expected_file} not found in calls:\n{calls}")

    # --- Test Core Logging Functionality (ASCIIColors API) ---

    def test_log_levels_enum(self):
        """Test LogLevel enum values match logging standards"""
        self.assertEqual(LogLevel.DEBUG.value, std_logging.DEBUG)
        self.assertEqual(LogLevel.INFO.value, std_logging.INFO)
        self.assertEqual(LogLevel.WARNING.value, std_logging.WARNING)
        self.assertEqual(LogLevel.ERROR.value, std_logging.ERROR)
        self.assertEqual(LogLevel.CRITICAL.value, std_logging.CRITICAL)
        self.assertEqual(DEBUG, std_logging.DEBUG)
        self.assertEqual(INFO, std_logging.INFO)
        self.assertEqual(WARNING, std_logging.WARNING)
        self.assertEqual(ERROR, std_logging.ERROR)
        self.assertEqual(CRITICAL, std_logging.CRITICAL)

    def test_default_handler_auto_creation(self):
        """Test that a default handler is added automatically on first log if none configured."""
        self.assertEqual(len(ASCIIColors._handlers), 0)
        ASCIIColors.info("Trigger auto-handler")
        self.assertEqual(len(ASCIIColors._handlers), 1)
        handler = ASCIIColors._handlers[0]
        self.assertIsInstance(handler, ConsoleHandler)
        self.assertEqual(handler.stream, sys.stderr)
        self.assertIsInstance(handler.formatter, Formatter)
        self.assertEqual(handler.formatter.style, '%')

    def test_add_remove_clear_handlers_ascii_api(self):
        """Test adding/removing handlers via ASCIIColors API."""
        ASCIIColors.info("Ensure default handler created if needed") # Trigger if empty
        initial_count = len(ASCIIColors._handlers)
        file_handler = FileHandler(self.log_file)
        ASCIIColors.add_handler(file_handler)
        self.assertEqual(len(ASCIIColors._handlers), initial_count + 1)
        ASCIIColors.remove_handler(file_handler)
        self.assertEqual(len(ASCIIColors._handlers), initial_count)
        ASCIIColors.clear_handlers()
        self.assertEqual(len(ASCIIColors._handlers), 0)

    def test_global_log_level_filtering_ascii_api(self):
        """Test filtering via ASCIIColors.set_log_level."""
        handler, stream = self._create_capture_stream_handler(level=DEBUG)
        ASCIIColors.add_handler(handler)

        ASCIIColors.set_log_level(WARNING) # Global filter set to WARNING
        ASCIIColors.debug("D")
        ASCIIColors.info("I")
        ASCIIColors.warning("W")
        ASCIIColors.error("E")

        output = strip_ansi(self._get_stream_value(stream))
        self.assertNotIn("D", output)
        self.assertNotIn("I", output)
        self.assertIn("W", output)
        self.assertIn("E", output)

    def test_handler_level_filtering_ascii_api(self):
        """Test filtering by handler level via ASCIIColors API."""
        ASCIIColors.set_log_level(DEBUG) # Global allows all
        handler, stream = self._create_capture_stream_handler(level=WARNING) # Handler filters
        ASCIIColors.add_handler(handler)

        ASCIIColors.debug("D"); ASCIIColors.info("I"); ASCIIColors.warning("W"); ASCIIColors.error("E")
        output = strip_ansi(self._get_stream_value(stream))
        self.assertNotIn("D", output); self.assertNotIn("I", output)
        self.assertIn("W", output); self.assertIn("E", output)

    # --- Test Formatters (ASCIIColors API context) ---
    def test_formatter_percent_style(self):
        """Test Formatter with % style."""
        fmt = Formatter(fmt="%(levelname)s:%(name)s:%(message)s [%(custom)s]", style='%')
        handler, stream = self._create_capture_stream_handler(formatter=fmt)
        ASCIIColors.add_handler(handler)
        ASCIIColors.info("Msg1", custom="Val1") # Pass extra via kwargs
        self.assertIn("INFO:ASCIIColors:Msg1 [Val1]", strip_ansi(self._get_stream_value(stream)))

    def test_formatter_brace_style(self):
        """Test Formatter with { style."""
        fmt = Formatter(fmt="{level_name}:{name}:{message} [{custom}]", style='{')
        handler, stream = self._create_capture_stream_handler(formatter=fmt)
        ASCIIColors.add_handler(handler)
        ASCIIColors.warning("Msg2", custom="Val2") # Pass extra via kwargs
        self.assertIn("WARNING:ASCIIColors:Msg2 [Val2]", strip_ansi(self._get_stream_value(stream)))

    def test_formatter_with_source_log(self):
        """Test logging formatter including source file/line/func (via ASCIIColors API)."""
        fmt = Formatter("[{func_name}] {message}", include_source=True, style='{')
        handler, stream = self._create_capture_stream_handler(formatter=fmt)
        ASCIIColors.add_handler(handler)
        ASCIIColors.info("SrcInfoMsg")
        output = strip_ansi(self._get_stream_value(stream))
        self.assertIn("SrcInfoMsg", output)
        # Check the function name is captured (might be test runner dependent)
        self.assertIn(f"[{inspect.currentframe().f_code.co_name}]", output)


    # --- Test JSON Formatter ---
    def test_json_formatter_log(self):
        """Test JSONFormatter basic output (via ASCIIColors API)."""
        fmt = JSONFormatter(include_fields=["levelname", "name", "message", "user"])
        h = FileHandler(self.json_log_file, formatter=fmt)
        ASCIIColors.add_handler(h)
        ASCIIColors.error("JsonErrorMsg", user="TestUser", code=503) # code ignored by include_fields
        self.assertTrue(self.json_log_file.exists())
        data = json.loads(self.json_log_file.read_text())
        self.assertEqual(data.get("levelname"), "ERROR")
        self.assertEqual(data.get("name"), "ASCIIColors")
        self.assertEqual(data.get("message"), "JsonErrorMsg")
        self.assertEqual(data.get("user"), "TestUser")
        self.assertNotIn("code", data)

    # --- Test Handlers (ASCIIColors API context) ---
    def test_file_handler_log(self):
        """Test FileHandler operation (via ASCIIColors API)."""
        fh = FileHandler(self.log_file, formatter=Formatter("%(message)s"))
        ASCIIColors.add_handler(fh)
        ASCIIColors.info("LogToFileTest")
        self.assertTrue(self.log_file.exists())
        content = self.log_file.read_text().strip()
        self.assertEqual(content, "LogToFileTest")

    def test_rotating_file_handler_log_real_rotation(self):
        """Test RotatingFileHandler performs actual file rotation."""
        log_file = self.rotate_log_file
        max_bytes = 50 # Small limit for testing
        backup_count = 2
        # Use a simple formatter writing only the message
        fmt = Formatter("%(message)s")
        rot_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, formatter=fmt)
        ASCIIColors.add_handler(rot_handler)
        ASCIIColors.set_log_level(DEBUG) # Ensure all messages go through

        # Write message 1 (below limit)
        msg1 = "A" * 40
        ASCIIColors.info(msg1)
        self.assertTrue(log_file.exists())
        self.assertLess(log_file.stat().st_size, max_bytes)
        self.assertFalse((log_file.parent / f"{log_file.name}.1").exists())

        # Write message 2 (triggers rotation 1)
        msg2 = "B" * 40
        ASCIIColors.info(msg2)
        time.sleep(0.05) # Give FS time
        self.assertTrue(log_file.exists(), "Log file should exist after rotation")
        self.assertTrue((log_file.parent / f"{log_file.name}.1").exists(), "Backup .1 should exist")
        self.assertFalse((log_file.parent / f"{log_file.name}.2").exists())
        # Check content
        self.assertEqual(log_file.read_text().strip(), msg2)
        self.assertEqual((log_file.parent / f"{log_file.name}.1").read_text().strip(), msg1)

        # Write message 3 (triggers rotation 2)
        msg3 = "C" * 40
        ASCIIColors.info(msg3)
        time.sleep(0.05)
        self.assertTrue(log_file.exists())
        self.assertTrue((log_file.parent / f"{log_file.name}.1").exists())
        self.assertTrue((log_file.parent / f"{log_file.name}.2").exists(), "Backup .2 should exist")
        self.assertFalse((log_file.parent / f"{log_file.name}.3").exists())
        # Check content
        self.assertEqual(log_file.read_text().strip(), msg3)
        self.assertEqual((log_file.parent / f"{log_file.name}.1").read_text().strip(), msg2)
        self.assertEqual((log_file.parent / f"{log_file.name}.2").read_text().strip(), msg1) # Oldest backup

        # Write message 4 (triggers rotation 3, oldest (.2) is deleted)
        msg4 = "D" * 40
        ASCIIColors.info(msg4)
        time.sleep(0.05)
        self.assertTrue(log_file.exists())
        self.assertTrue((log_file.parent / f"{log_file.name}.1").exists())
        self.assertTrue((log_file.parent / f"{log_file.name}.2").exists(), "Backup .2 should still exist (was .1)")
        self.assertFalse((log_file.parent / f"{log_file.name}.3").exists(), "Backup .3 should not exist")
         # Check content
        self.assertEqual(log_file.read_text().strip(), msg4)
        self.assertEqual((log_file.parent / f"{log_file.name}.1").read_text().strip(), msg3)
        self.assertEqual((log_file.parent / f"{log_file.name}.2").read_text().strip(), msg2) # msg1 backup is gone


    # --- Test Context Management (ASCIIColors API context) ---
    def test_context_manager_log_ascii_api(self):
        """Test context manager via ASCIIColors API."""
        fmt = Formatter("S:{session}|U:{user}|M:{message}", style='{')
        handler, stream = self._create_capture_stream_handler(formatter=fmt)
        ASCIIColors.add_handler(handler)

        ASCIIColors.set_context(session="S1", user="U1")
        ASCIIColors.info("M1")
        with ASCIIColors.context(user="U2", task="T"): # Add task
            ASCIIColors.info("M2")
            # Check context includes task temporarily
            self.assertEqual(ASCIIColors.get_thread_context().get('task'), 'T')
        # Check context reverted
        self.assertIsNone(ASCIIColors.get_thread_context().get('task'))
        ASCIIColors.info("M3")

        output = strip_ansi(self._get_stream_value(stream))
        self.assertIn("S:S1|U:U1|M:M1", output)
        self.assertIn("S:S1|U:U2|M:M2", output) # Task won't show as it's not in format string
        self.assertIn("S:S1|U:U1|M:M3", output)

    # --- Test Direct Print Methods (Still Bypass Logging) ---
    def test_direct_print_method(self):
        """Test the static print method calls builtins.print directly."""
        txt="DirectPrint"; col=ASCIIColors.color_cyan; sty=ASCIIColors.style_underline; end="X"; flush=True; file=self.original_stderr
        ASCIIColors.print(txt, color=col, style=sty, end=end, flush=flush, file=file)
        self.assert_direct_print_called_with(txt, color_code=col, style_code=sty, end=end, flush=flush, file=file)

    def test_direct_color_methods(self):
        """Test direct color methods (red, green, etc.) call builtins.print."""
        ASCIIColors.red("RedDirect")
        self.assert_direct_print_called_with("RedDirect", color_code=ASCIIColors.color_red)
        self.mock_builtin_print.reset_mock() # Reset for next assertion
        ASCIIColors.green("GreenDirect", end='')
        self.assert_direct_print_called_with("GreenDirect", color_code=ASCIIColors.color_green, end='')


    # ===========================================================
    # --- Tests for Logging Compatibility Layer ---
    # ===========================================================

    def test_getLogger_returns_adapter(self):
        """Test getLogger returns the correct adapter type."""
        logger = getLogger("test_adapter")
        # Access private class via module object for check
        self.assertIsInstance(logger, ascii_colors._AsciiLoggerAdapter)
        self.assertEqual(logger.name, "test_adapter")

    def test_getLogger_caching(self):
        """Test that getLogger caches adapter instances."""
        logger1 = getLogger("cached_logger")
        logger2 = getLogger("cached_logger")
        self.assertIs(logger1, logger2)
        logger3 = getLogger("other_logger")
        self.assertIsNot(logger1, logger3)

    def test_getLogger_root(self):
        """Test getLogger() returns root logger adapter."""
        root_logger = getLogger()
        self.assertEqual(root_logger.name, "root")
        root_logger_none = getLogger(None)
        self.assertIs(root_logger, root_logger_none)
        
    @patch('ascii_colors.ASCIIColors._log')
    def test_logger_adapter_methods_call_core_log(self, mock_core_log):
        """Test adapter methods delegate to ASCIIColors._log with correct args."""
        logger = getLogger("adapter_test")
        ASCIIColors.set_log_level(DEBUG)

        # ... (debug, info, warning, error calls/assertions) ...
        logger.debug("Debug msg %s", "arg1", extra_key="dv")
        mock_core_log.assert_called_with(LogLevel.DEBUG, "Debug msg %s", ("arg1",), logger_name="adapter_test", extra_key="dv")
        logger.info("Info msg")
        mock_core_log.assert_called_with(LogLevel.INFO, "Info msg", (), logger_name="adapter_test")
        logger.warning("Warn msg %d %d", 1, 2)
        mock_core_log.assert_called_with(LogLevel.WARNING, "Warn msg %d %d", (1, 2), logger_name="adapter_test")
        logger.error("Error msg", exc_info=False, data=1) # Pass exc_info explicitly
        mock_core_log.assert_called_with(LogLevel.ERROR, "Error msg", (), logger_name="adapter_test", exc_info=False, data=1)


        mock_core_log.reset_mock()
        try:
            raise ValueError("Test Exc")
        except ValueError:
             logger.exception("Exception msg %s", "oops", detail="ze")

        self.assertTrue(mock_core_log.called)
        call_args, call_kwargs = mock_core_log.call_args
        self.assertEqual(call_args[0], LogLevel.ERROR)
        self.assertEqual(call_args[1], "Exception msg %s")
        self.assertEqual(call_args[2], ("oops",))
        self.assertEqual(call_kwargs.get("logger_name"), "adapter_test")
        # Fix 11: Assert that _log was called with exc_info=True
        self.assertEqual(call_kwargs.get("exc_info"), True)
        self.assertEqual(call_kwargs.get("detail"), "ze")

        # ... (critical, log calls/assertions) ...
        logger.critical("Critical msg")
        mock_core_log.assert_called_with(LogLevel.CRITICAL, "Critical msg", (), logger_name="adapter_test")
        logger.log(INFO, "Log msg %s", "level_info")
        mock_core_log.assert_called_with(LogLevel.INFO, "Log msg %s", ("level_info",), logger_name="adapter_test")

    def test_logger_adapter_level_methods(self):
        """Test logger adapter setLevel/getEffectiveLevel operate globally."""
        logger = getLogger("level_test")
        ASCIIColors.set_log_level(INFO) # Start at INFO globally
        self.assertEqual(logger.getEffectiveLevel(), INFO)

        logger.setLevel(DEBUG)
        self.assertEqual(ASCIIColors._global_level, LogLevel.DEBUG)
        self.assertEqual(logger.getEffectiveLevel(), DEBUG)

        logger.setLevel("WARNING") # Use string name
        self.assertEqual(ASCIIColors._global_level, LogLevel.WARNING)
        self.assertEqual(logger.getEffectiveLevel(), WARNING)

    def test_logger_adapter_handler_methods(self):
        """Test logger adapter add/removeHandler operate globally."""
        logger = getLogger("handler_test")
        ASCIIColors.clear_handlers()
        self.assertFalse(logger.hasHandlers())

        handler, _ = self._create_capture_stream_handler()
        logger.addHandler(handler)
        self.assertTrue(logger.hasHandlers())
        self.assertIn(handler, ASCIIColors._handlers)
        self.assertEqual(len(ASCIIColors._handlers), 1)

        fh = FileHandler(self.log_file)
        logger.addHandler(fh)
        self.assertIn(fh, ASCIIColors._handlers)
        self.assertEqual(len(ASCIIColors._handlers), 2)

        logger.removeHandler(handler)
        self.assertNotIn(handler, ASCIIColors._handlers)
        self.assertEqual(len(ASCIIColors._handlers), 1)
        self.assertTrue(logger.hasHandlers())

        logger.removeHandler(fh)
        self.assertFalse(logger.hasHandlers())
        self.assertEqual(len(ASCIIColors._handlers), 0)


    # --- basicConfig Tests ---

    def test_basicConfig_defaults(self):
        """Test basicConfig with no arguments."""
        basicConfig()
        self.assertTrue(ASCIIColors._basicConfig_called)
        self.assertEqual(len(ASCIIColors._handlers), 1)
        handler = ASCIIColors._handlers[0]
        self.assertIsInstance(handler, ConsoleHandler)
        self.assertEqual(handler.stream, sys.stderr)
        self.assertEqual(handler.level, LogLevel.WARNING) # Default level
        self.assertEqual(ASCIIColors._global_level, LogLevel.WARNING)
        self.assertEqual(handler.formatter.style, '%')

    def test_basicConfig_level(self):
        """Test basicConfig setting level."""
        basicConfig(level=DEBUG)
        self.assertEqual(ASCIIColors._global_level, LogLevel.DEBUG)
        self.assertEqual(ASCIIColors._handlers[0].level, LogLevel.DEBUG)

        basicConfig(level="ERROR", force=True) # Reconfigure with force
        self.assertEqual(ASCIIColors._global_level, LogLevel.ERROR)
        self.assertEqual(ASCIIColors._handlers[0].level, LogLevel.ERROR)

    def test_basicConfig_format_datefmt_style(self):
        """Test basicConfig setting format, datefmt, style."""
        fmt = "{asctime} - {name} - {message}"
        datefmt = "%H:%M"
        style = '{'
        # Use a local stream for capture in this test
        local_stream = io.StringIO(); self.addCleanup(local_stream.close)
        basicConfig(format=fmt, datefmt=datefmt, style=style, level=INFO, stream=local_stream)

        handler = ASCIIColors._handlers[0]
        formatter = handler.formatter
        self.assertEqual(formatter.fmt, fmt)
        self.assertEqual(formatter.datefmt, datefmt)
        self.assertEqual(formatter.style, style)

        logger = getLogger("fmt_test")
        logger.info("Testing format") # Log goes to local_stream via basicConfig handler
        output = strip_ansi(self._get_stream_value(local_stream))
        self.assertRegex(output, r"\d{2}:\d{2} - fmt_test - Testing format")

    def test_basicConfig_filename_filemode(self):
        """Test basicConfig with filename and filemode."""
        self.assertFalse(self.compat_log_file.exists())
        basicConfig(filename=self.compat_log_file, filemode='w', level=INFO, format="%(message)s")

        self.assertEqual(len(ASCIIColors._handlers), 1)
        handler = ASCIIColors._handlers[0]
        self.assertIsInstance(handler, FileHandler)
        self.assertEqual(handler.filename, self.compat_log_file)
        self.assertEqual(handler.mode, 'w')

        logger = getLogger("file_test")
        logger.info("Write to file")
        logger.warning("Second line")

        self.assertTrue(self.compat_log_file.exists())
        content = self.compat_log_file.read_text()
        self.assertEqual(content.strip(), "Write to file\nSecond line")

        # Test append mode with force=True
        basicConfig(filename=self.compat_log_file, filemode='a', level=INFO, format="%(message)s", force=True)
        logger.error("Append this")
        content = self.compat_log_file.read_text()
        self.assertEqual(content.strip(), "Write to file\nSecond line\nAppend this")


    def test_basicConfig_stream(self):
        """Test basicConfig with stream argument."""
        local_stream = io.StringIO(); self.addCleanup(local_stream.close)
        basicConfig(stream=local_stream, level=INFO, format="%(message)s")

        self.assertEqual(len(ASCIIColors._handlers), 1)
        handler = ASCIIColors._handlers[0]
        self.assertIsInstance(handler, ConsoleHandler)
        self.assertIs(handler.stream, local_stream)

        logger = getLogger("stream_test")
        logger.info("Write to stream")
        self.assertIn("Write to stream", strip_ansi(self._get_stream_value(local_stream)))

    def test_basicConfig_handlers(self):
        """Test basicConfig with explicit handlers list."""
        h1_stream = io.StringIO(); self.addCleanup(h1_stream.close)
        h1 = ConsoleHandler(stream=h1_stream, level=DEBUG) # No formatter initially
        h2 = FileHandler(self.compat_log_file, level=INFO, mode='w')
        h2.setFormatter(Formatter("FILE: %(message)s")) # Pre-set formatter

        basicConfig(handlers=[h1, h2], level=WARNING, format="DEFAULT: %(message)s")

        self.assertEqual(len(ASCIIColors._handlers), 2)
        self.assertIn(h1, ASCIIColors._handlers)
        self.assertIn(h2, ASCIIColors._handlers)

        # Check formatters were applied/kept correctly
        self.assertEqual(h1.formatter.fmt, "DEFAULT: %(message)s") # Got default
        self.assertEqual(h2.formatter.fmt, "FILE: %(message)s") # Kept its own

        logger = getLogger("handlers_test")
        logger.warning("Warn Both")   # Goes to both
        logger.info("Info File Only") # Below h1 level
        logger.debug("Debug h1 Only") # Below h2 level, but allowed by h1

        # Check stream output (Warn + Debug)
        output_stream = strip_ansi(self._get_stream_value(h1_stream))
        self.assertIn("DEFAULT: Warn Both", output_stream)
        self.assertNotIn("Info File Only", output_stream)
        self.assertIn("DEFAULT: Debug h1 Only", output_stream)

        # Check file output (Warn + Info)
        content_file = self.compat_log_file.read_text()
        self.assertIn("FILE: Warn Both", content_file)
        self.assertIn("FILE: Info File Only", content_file)
        self.assertNotIn("Debug h1 Only", content_file)

    def test_basicConfig_force(self):
        """Test basicConfig force=True allows reconfiguration."""
        basicConfig(level=INFO)
        initial_handler = ASCIIColors._handlers[0]

        basicConfig(level=DEBUG) # No force, should do nothing
        self.assertEqual(ASCIIColors._global_level, LogLevel.INFO)
        self.assertIs(ASCIIColors._handlers[0], initial_handler)

        local_stream = io.StringIO(); self.addCleanup(local_stream.close)
        basicConfig(level=WARNING, force=True, stream=local_stream, format="Forced: %(message)s")
        self.assertEqual(ASCIIColors._global_level, LogLevel.WARNING)
        self.assertEqual(len(ASCIIColors._handlers), 1)
        self.assertIsNot(ASCIIColors._handlers[0], initial_handler) # New handler
        new_handler = ASCIIColors._handlers[0]
        self.assertIs(new_handler.stream, local_stream)
        self.assertEqual(new_handler.formatter.fmt, "Forced: %(message)s")

    # --- Test Handler/Formatter Aliases ---
    def test_handler_aliases(self):
        """Test logging-compatible handler aliases."""
        self.assertIs(StreamHandler, ConsoleHandler)
        self.assertIs(handlers.RotatingFileHandler, RotatingFileHandler)
        self.assertTrue(hasattr(ascii_colors, 'FileHandler'))

    def test_formatter_alias(self):
        """Test logging-compatible Formatter alias."""
        self.assertTrue(hasattr(ascii_colors, 'Formatter'))


    # --- Test interaction between APIs ---
    def test_basicConfig_then_ascii_api(self):
        """Test using ASCIIColors API after basicConfig."""
        local_stream = io.StringIO(); self.addCleanup(local_stream.close)
        basicConfig(level=INFO, stream=local_stream, format="BC: %(name)s - %(message)s")
        logger = getLogger("compat")

        ASCIIColors.warning("Msg from ASCII API")
        logger.error("Msg from logger")

        output = strip_ansi(self._get_stream_value(local_stream))
        self.assertIn("BC: ASCIIColors - Msg from ASCII API", output)
        self.assertIn("BC: compat - Msg from logger", output)

        # Add handler via ASCIIColors API
        # Fix 6: Use formatter= kwarg
        fh = FileHandler(self.compat_log_file, mode='w', formatter=Formatter("%(message)s"))
        self.addCleanup(fh.close)
        ASCIIColors.add_handler(fh)
        self.assertEqual(len(ASCIIColors._handlers), 2)

        ASCIIColors.info("ASCII to both")
        logger.info("Logger to both")

        stream_out = strip_ansi(self._get_stream_value(local_stream))
        file_out = self.compat_log_file.read_text()

        self.assertIn("BC: ASCIIColors - ASCII to both", stream_out)
        self.assertIn("BC: compat - Logger to both", stream_out)
        self.assertIn("ASCII to both", file_out)
        self.assertIn("Logger to both", file_out)

    def test_ascii_api_then_basicConfig(self):
        """Test using basicConfig after ASCIIColors API calls."""
        handler_ascii, stream_ascii = self._create_capture_stream_handler(level=DEBUG, formatter=Formatter("ASCII: {message}"))
        ASCIIColors.add_handler(handler_ascii)
        ASCIIColors.set_log_level(DEBUG)
        ASCIIColors.info("Before basicConfig")

        # basicConfig without force (should do nothing)
        basicConfig(level=INFO, format="%(message)s")
        self.assertEqual(ASCIIColors._global_level, LogLevel.DEBUG) # Unchanged
        self.assertIs(ASCIIColors._handlers[0], handler_ascii) # Unchanged

        ASCIIColors.info("After basicConfig (no force)")
        output = strip_ansi(self._get_stream_value(stream_ascii))
        self.assertIn("ASCII: Before basicConfig", output)
        self.assertIn("ASCII: After basicConfig (no force)", output)

        # basicConfig WITH force
        basicConfig(level=WARNING, force=True, format="BC: %(message)s", stream=sys.stderr) # Use stderr
        self.assertEqual(ASCIIColors._global_level, LogLevel.WARNING)
        self.assertEqual(len(ASCIIColors._handlers), 1)
        self.assertIsNot(ASCIIColors._handlers[0], handler_ascii) # New handler

        # Log again (won't go to original stream_ascii)
        ASCIIColors.warning("After basicConfig (force)")
        output_after_force = strip_ansi(self._get_stream_value(stream_ascii))
        self.assertNotIn("After basicConfig (force)", output_after_force)

class TestProgressBar(unittest.TestCase):

    def setUp(self):
        # Mock print and time/terminal size for controlled testing
        patcher_print = patch("ascii_colors.ASCIIColors.print")
        self.mock_ascii_print = patcher_print.start()
        self.addCleanup(patcher_print.stop)

        patcher_time = patch("time.time")
        self.mock_time = patcher_time.start()
        self.mock_time.return_value = 1000.0 # Start time
        self.addCleanup(patcher_time.stop)

        patcher_sleep = patch("time.sleep") # Mock sleep to speed up tests
        self.mock_sleep = patcher_sleep.start()
        self.addCleanup(patcher_sleep.stop)

        patcher_tsize = patch("shutil.get_terminal_size")
        self.mock_tsize = patcher_tsize.start()
        self.mock_tsize.return_value = os.terminal_size((80, 24)) # Default size
        self.addCleanup(patcher_tsize.stop)

        # Use StringIO to capture potential direct prints if needed, though mocking is better
        self.capture_stream = io.StringIO()
        self.addCleanup(self.capture_stream.close)
        self.original_stdout = sys.stdout # Keep original reference if needed

    def _advance_time(self, seconds):
        self.mock_time.return_value += seconds

    def _get_last_print_args(self):
        if not self.mock_ascii_print.called:
            return None
        # Get the arguments of the last call to ASCIIColors.print
        # Expected call: print(text, color="", style="", background="", end="", flush=True, file=sys.stdout)
        last_call_args, last_call_kwargs = self.mock_ascii_print.call_args
        return last_call_args[0] # Return the main text argument

    def test_iterable_wrapper(self):
        """Test ProgressBar wrapping an iterable."""
        data = list(range(5))
        start_time = self.mock_time.return_value

        # Make __len__ work for the list
        with patch.object(list, '__len__', return_value=len(data)):
             pbar = ProgressBar(data, desc="Iter Test", mininterval=0) # No throttle

             # Initial print
             list(pbar) # Consume the iterator

        # Check calls to print
        # Should be called len(data) + 1 (initial) + 1 (final) times if mininterval=0
        self.assertEqual(self.mock_ascii_print.call_count, len(data) + 2)

        # Check final rendered output (last call before newline)
        # Need to simulate time advancing
        # This requires more detailed mocking/checking of each render call

        # Simplified check: Look at the last rendered bar content
        final_render_text = self._get_last_print_args()
        self.assertIn("\rIter Test: 100%", final_render_text)
        self.assertIn("| 5/5 [", final_render_text) # Check counts

    def test_context_manager(self):
        """Test ProgressBar as a context manager."""
        total = 10
        start_time = self.mock_time.return_value

        with ProgressBar(total=total, desc="Ctx Test", mininterval=0) as pbar:
            # Initial render
            self.mock_ascii_print.assert_called_once()
            initial_text = self._get_last_print_args()
            self.assertIn("\rCtx Test:   0%", initial_text)
            self.assertIn("| 0/10 [", initial_text)

            self.mock_ascii_print.reset_mock()
            for i in range(total):
                self._advance_time(0.01) # Simulate work time
                pbar.update(1)

        # Check updates and final render
        self.assertEqual(self.mock_ascii_print.call_count, total + 1) # +1 for final render in close()
        final_text = self._get_last_print_args()
        self.assertIn("\rCtx Test: 100%", final_text)
        self.assertIn(f"| {total}/{total} [", final_text)

    def test_styling_options(self):
        """Test different styling parameters."""
        with ProgressBar(total=10, desc="Style", color=ASCIIColors.color_red, style=ASCIIColors.style_bold, progress_char=">", empty_char="-", bar_style="fill", mininterval=0) as pbar:
            pbar.update(5)

        render_text = self._get_last_print_args()
        # Check bar characters and presence of color/style codes
        self.assertTrue(ASCIIColors.color_red in render_text)
        self.assertTrue(ASCIIColors.style_bold in render_text)
        # Regex to find the bar part approximately: look for > and - between | and |
        bar_match = re.search(r"\|([^|]+)\|", strip_ansi(render_text))
        self.assertTrue(bar_match, f"Bar content not found in '{strip_ansi(render_text)}'")
        bar_content = bar_match.group(1).strip()
        # Expect something like >>>>>-----
        self.assertTrue(bar_content.startswith(">"*2), f"Bar content mismatch: {bar_content}") # Adjust multiplier based on width calculation
        self.assertTrue(bar_content.endswith("-"*2), f"Bar content mismatch: {bar_content}")

    def test_thread_safety(self):
        """Simulate concurrent updates to test locking (basic check)."""
        total = 100
        num_threads = 4
        updates_per_thread = total // num_threads

        results = []
        exceptions = []

        pbar = ProgressBar(total=total, desc="Thread Test", mininterval=0.01)

        def worker(start_index):
            try:
                for i in range(updates_per_thread):
                    # No sleep needed, just call update quickly
                    pbar.update(1)
                    # time.sleep(0.001) # Optional tiny sleep
                results.append(True)
            except Exception as e:
                exceptions.append(e)

        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i * updates_per_thread,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        pbar.close()

        # Basic assertions: No exceptions and final count is correct
        self.assertEqual(len(exceptions), 0, f"Exceptions occurred in threads: {exceptions}")
        self.assertEqual(pbar.n, total, f"Final progress count mismatch. Expected {total}, got {pbar.n}")
        # Check print was called multiple times (difficult to assert exact number due to throttling)
        self.assertGreater(self.mock_ascii_print.call_count, num_threads)


# Updated TestMenu class
class TestMenu(unittest.TestCase):

    def setUp(self):
        patcher_print = patch("ascii_colors.ASCIIColors.print")
        self.mock_ascii_print = patcher_print.start()
        self.addCleanup(patcher_print.stop)

        # Mock _get_key directly
        patcher_get_key = patch("ascii_colors._get_key")
        self.mock_get_key = patcher_get_key.start()
        self.addCleanup(patcher_get_key.stop)

        patcher_clear = patch("ascii_colors.Menu._clear_screen")
        self.mock_clear_screen = patcher_clear.start()
        self.addCleanup(patcher_clear.stop)

        patcher_cursor = patch("ascii_colors.Menu._set_cursor_visibility")
        self.mock_set_cursor = patcher_cursor.start()
        self.addCleanup(patcher_cursor.stop)


        # Mock action functions
        self.mock_action_a = Mock()
        self.mock_action_b = Mock()
        self.mock_action_fail = Mock(side_effect=ValueError("Mock Fail"))

    def _get_printed_lines(self, strip=True):
        """Helper to get lines printed via ASCIIColors.print mock."""
        lines = []
        # Iterate through calls *before* the last prompt print
        # prompt_call_index = -1
        # for i, call in enumerate(reversed(self.mock_ascii_print.call_args_list)):
        #     args, _ = call
        #     if args and isinstance(args[0], str) and args[0].strip().startswith("Use ↑/↓"):
        #         prompt_call_index = len(self.mock_ascii_print.call_args_list) -1 - i
        #         break

        calls_to_check = self.mock_ascii_print.call_args_list # Check all for now
        for call in calls_to_check:
            args, _ = call
            if args and isinstance(args[0], str):
                line = args[0]
                if strip:
                    line = strip_ansi(line)
                lines.append(line)
        return lines

    def _find_last_menu_print_state(self):
        """Finds the printed lines corresponding to the last full menu render."""
        # Find the latest title print, then collect lines until the prompt
        last_title_index = -1
        calls = self.mock_ascii_print.call_args_list
        for i, call in enumerate(reversed(calls)):
            args, _ = call
            # Simplistic check for title - improve if needed
            if args and isinstance(args[0], str) and strip_ansi(args[0]).startswith("---"):
                 # Assume line before was the title
                 last_title_index = len(calls) - 1 - i -1
                 break

        if last_title_index == -1: return [] # No menu found

        menu_lines = []
        for i in range(last_title_index, len(calls)):
            args, _ = calls[i]
            if args and isinstance(args[0], str):
                 line = strip_ansi(args[0])
                 if line.strip().startswith("Use ↑/↓"): # Stop before prompt
                     break
                 menu_lines.append(line)
        return menu_lines


    def test_menu_creation_and_add_items(self):
        """Test creating a menu and adding actions/submenus (no keys now)."""
        m = Menu("Test Menu")
        sub = Menu("Sub")
        m.add_action("Action A", self.mock_action_a)
        m.add_submenu("Go Sub", sub)

        self.assertEqual(m.title, "Test Menu")
        self.assertEqual(len(m.items), 2)
        self.assertEqual(m.items[0].text, "Action A")
        self.assertEqual(m.items[0].type, 'action')
        self.assertEqual(m.items[1].text, "Go Sub")
        self.assertEqual(m.items[1].type, 'submenu')
        self.assertIs(m.items[1].target, sub)
        self.assertIs(sub.parent, m)

    def test_menu_run_display_highlight(self):
        """Test the display output and highlighting."""
        m = Menu("Display Test", clear_screen_on_run=False)
        m.add_action("Item One", lambda: None)
        m.add_action("Item Two", lambda: None)

        # Simulate keys: Down, then Quit
        self.mock_get_key.side_effect = ['DOWN', 'QUIT']
        m.run()

        # Find the last menu state printed
        last_menu_state = self._find_last_menu_print_state()

        # Check title
        self.assertTrue(last_menu_state[0].startswith("Display Test"), f"State: {last_menu_state}")
        self.assertTrue(last_menu_state[1].startswith("------------"))
        # Check items - Item Two should be selected (index 1)
        self.assertTrue(last_menu_state[2].startswith(m.prefixes['unselected'] + "Item One")) # Item 0 not selected
        self.assertTrue(last_menu_state[3].startswith(m.prefixes['selected'] + "Item Two")) # Item 1 selected
        # Check Quit option
        self.assertTrue(any("Quit" in line for line in last_menu_state))

    def test_menu_run_select_action_enter(self):
        """Test selecting an action using Enter."""
        m = Menu("Action Test", clear_screen_on_run=False)
        m.add_action("Do A", self.mock_action_a)
        m.add_action("Do B", self.mock_action_b)

        # Simulate keys: Down (select B), Enter, Enter (confirm), Quit
        self.mock_get_key.side_effect = ['DOWN', 'ENTER', 'ENTER', 'QUIT']
        m.run()

        self.mock_action_a.assert_not_called()
        self.mock_action_b.assert_called_once()
        # Check for the "Press Enter to continue" prompt print
        self.assertTrue(any("Press Enter to continue" in strip_ansi(c.args[0])
                           for c in self.mock_ascii_print.call_args_list if c.args))

    @patch('ascii_colors.trace_exception')
    def test_menu_run_action_exception_arrows(self, mock_trace):
        """Test error handling with arrow navigation."""
        m = Menu("Fail Test", clear_screen_on_run=False)
        m.add_action("OK Action", self.mock_action_a)
        m.add_action("Fail Me", self.mock_action_fail)

        # Simulate: Down (select Fail Me), Enter, Enter (confirm), Quit
        self.mock_get_key.side_effect = ['DOWN', 'ENTER', 'ENTER', 'QUIT']
        m.run()

        self.mock_action_a.assert_not_called()
        self.mock_action_fail.assert_called_once()
        mock_trace.assert_called_once() # Check logging was called
        self.assertTrue(any("Error executing action:" in strip_ansi(c.args[0])
                           for c in self.mock_ascii_print.call_args_list if c.args)) # Check error message print


    def test_menu_run_submenu_and_back_arrows(self):
        """Test submenu navigation and Back with arrows."""
        root = Menu("Root", clear_screen_on_run=False)
        sub = Menu("Sub", parent=root, clear_screen_on_run=False)
        sub.add_action("Sub Action A", self.mock_action_a)
        root.add_action("Root Action B", self.mock_action_b)
        root.add_submenu("Go Sub", sub) # Added at index 1

        # Sequence:
        # 1. In Root, Down (select Go Sub), Enter -> Enters Sub
        # 2. In Sub, Enter (select Sub Action A)
        # 3. Enter (confirm Sub Action A)
        # 4. In Sub, Down (select Back), Enter -> Returns to Root
        # 5. In Root, Quit
        self.mock_get_key.side_effect = [
            'DOWN', 'ENTER', # Enter Sub
            'ENTER', 'ENTER', # Select and confirm Sub Action A
            'DOWN', 'ENTER', # Select Back in Sub and return
            'QUIT'           # Quit Root
        ]
        root.run()

        self.mock_action_a.assert_called_once() # Sub action called
        self.mock_action_b.assert_not_called() # Root action not called


    def test_menu_ctrl_c_handling(self):
        """Test Ctrl+C (QUIT signal) handling."""
        root = Menu("Root", clear_screen_on_run=False)
        sub = Menu("Sub", parent=root, clear_screen_on_run=False)
        root.add_submenu("Go Sub", sub)

        # --- Test Ctrl+C in Root (should quit) ---
        self.mock_get_key.side_effect = ['QUIT']
        root.run()
        # Check that the loop exited (no mocks called after QUIT)

        # --- Test Ctrl+C in Sub (should go back) ---
        self.mock_get_key.reset_mock()
        # Simulate: Enter (go to sub), then Ctrl+C (go back), then Quit root
        self.mock_get_key.side_effect = ['ENTER', 'QUIT', 'QUIT']
        root.run()
        # Difficult to assert "back" happened cleanly without inspecting print state changes


    def test_menu_cursor_visibility(self):
        """Test cursor hiding/showing option."""
        # Test hiding enabled
        m_hide = Menu("Hide Cursor", hide_cursor=True)
        m_hide.add_action("Action", lambda: None)
        self.mock_get_key.side_effect = ['QUIT']
        m_hide.run()
        # Check hide (False) was called on start, show (True) on exit
        self.mock_set_cursor.assert_any_call(False)
        self.mock_set_cursor.assert_called_with(True) # Last call should be True

        self.mock_set_cursor.reset_mock()

        # Test hiding disabled
        m_show = Menu("Show Cursor", hide_cursor=False)
        m_show.add_action("Action", lambda: None)
        self.mock_get_key.side_effect = ['QUIT']
        m_show.run()
        # Check set_cursor was NOT called
        self.mock_set_cursor.assert_not_called()

if __name__ == "__main__":
    unittest.main()