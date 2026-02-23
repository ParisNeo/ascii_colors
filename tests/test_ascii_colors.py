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
from typing import Optional

# Ensure the module path is correct for testing
# Ensure the local module path is prioritized for testing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
# Import questionary compatibility
from ascii_colors.questionary import (
    Text, Password, Confirm, Select, Checkbox, Autocomplete, Form,
    Validator, ValidationError,
    text, password, confirm, select, checkbox, autocomplete, form, ask
)


# Helper to strip ANSI codes (unchanged)
ANSI_ESCAPE_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
def strip_ansi(text: str) -> str:
    """Removes ANSI escape sequences from a string."""
    if text is None:
        return ""
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

        # --- Reset global state BEFORE each test ---
        ASCIIColors.clear_handlers()
        ASCIIColors.set_log_level(LogLevel.WARNING)
        ASCIIColors._basicConfig_called = False
        ASCIIColors.clear_context()
        ascii_colors._logger_cache.clear()
        # --- End Reset ---

        # --- Also reset AFTER each test using addCleanup for reliability ---
        self.addCleanup(ASCIIColors.clear_handlers)
        self.addCleanup(lambda: ASCIIColors.set_log_level(LogLevel.WARNING))
        self.addCleanup(setattr, ASCIIColors, '_basicConfig_called', False)
        self.addCleanup(ASCIIColors.clear_context)
        self.addCleanup(ascii_colors._logger_cache.clear)
        # --- End Reset ---

        # For testing direct print methods, capture stdout/stderr
        self._stdout_capture = io.StringIO()
        self._stderr_capture = io.StringIO()
        
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def tearDown(self):
        """Clean up test environment after each test"""
        # Temp directory removal with retries (important for Windows)
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            for i in range(3):
                try:
                    shutil.rmtree(self.temp_dir, ignore_errors=False)
                    break # Success
                except OSError as e:
                    if i < 2: # Only sleep if retrying
                        time.sleep(0.2 * (i + 1)) # Exponential backoff slightly
            else:
                 print(f"\n[TEST ERROR] Could not remove temp dir {self.temp_dir} after retries.", file=sys.stderr)

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

    def assert_direct_print_output(self, expected_text_part: str, color_code: str = None, style_code: str = "", end: str = "\n", stream_capture: io.StringIO = None):
        """Asserts that direct print output contains expected content by checking stream output."""
        # Get output from the appropriate stream
        if stream_capture is None:
            # Default to stdout for most direct prints
            output = self._stdout_capture.getvalue()
            if not output:
                output = self._stderr_capture.getvalue()
        else:
            output = stream_capture.getvalue()
        
        # Strip ANSI for text content check
        stripped_output = strip_ansi(output)
        
        # Check that expected text is in output
        self.assertIn(expected_text_part, stripped_output, 
                     f"Expected text '{expected_text_part}' not found in output: {stripped_output!r}")
        
        # Check color/style if specified
        if color_code:
            self.assertIn(color_code, output, 
                         f"Color code '{color_code!r}' not found in output")
        
        if style_code:
            self.assertIn(style_code, output,
                         f"Style code '{style_code!r}' not found in output")
        
        # Check that output ends correctly (with reset code and ending)
        if end:
            # The output should contain the reset code before the end string
            self.assertIn(ASCIIColors.color_reset + end, output,
                         f"Expected suffix '{ASCIIColors.color_reset + end!r}' not in output")

    # --- Test Core Logging Functionality (ASCIIColors API) ---

    def test_log_levels_enum(self):
        """Test LogLevel enum values match logging standards"""
        self.assertEqual(LogLevel.DEBUG.value, std_logging.DEBUG)
        self.assertEqual(LogLevel.INFO.value, std_logging.INFO)
        self.assertEqual(LogLevel.WARNING.value, std_logging.WARNING)
        self.assertEqual(LogLevel.ERROR.value, std_logging.ERROR)
        self.assertEqual(LogLevel.CRITICAL.value, std_logging.CRITICAL)

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
        ASCIIColors.set_log_level(INFO)
        fmt = Formatter(fmt="%(levelname)s:%(name)s:%(message)s [%(custom)s]", style='%')
        handler, stream = self._create_capture_stream_handler(formatter=fmt)
        ASCIIColors.add_handler(handler)
        ASCIIColors.info("Msg1", custom="Val1") # Pass extra via kwargs
        self.assertIn("INFO:ASCIIColors:Msg1 [Val1]", strip_ansi(self._get_stream_value(stream)))

    def test_formatter_brace_style(self):
        """Test Formatter with { style."""
        ASCIIColors.set_log_level(WARNING)
        fmt = Formatter(fmt="{level_name}:{name}:{message} [{custom}]", style='{')
        handler, stream = self._create_capture_stream_handler(formatter=fmt)
        ASCIIColors.add_handler(handler)
        ASCIIColors.warning("Msg2", custom="Val2") # Pass extra via kwargs
        self.assertIn("WARNING:ASCIIColors:Msg2 [Val2]", strip_ansi(self._get_stream_value(stream)))

    def test_formatter_with_source_log(self):
        """Test logging formatter including source file/line/func (via ASCIIColors API)."""
        ASCIIColors.set_log_level(INFO)
        fmt = Formatter("[{func_name}] {message}", include_source=True, style='{')
        handler, stream = self._create_capture_stream_handler(formatter=fmt)
        ASCIIColors.add_handler(handler)
        ASCIIColors.info("SrcInfoMsg")
        output = strip_ansi(self._get_stream_value(stream))
        self.assertIn("SrcInfoMsg", output)
        # Check the function name is captured
        self.assertIn(f"[{inspect.currentframe().f_code.co_name}]", output)

    # --- Test JSON Formatter ---
    def test_json_formatter_log(self):
        """Test JSONFormatter basic output (via ASCIIColors API)."""
        ASCIIColors.set_log_level(ERROR)
        fmt = JSONFormatter(include_fields=["levelname", "name", "message", "user"])
        h = FileHandler(self.json_log_file, formatter=fmt)
        ASCIIColors.add_handler(h)
        ASCIIColors.error("JsonErrorMsg", user="TestUser", code=503) 
        self.assertTrue(self.json_log_file.exists())
        data = json.loads(self.json_log_file.read_text())
        self.assertEqual(data.get("levelname"), "ERROR")
        self.assertEqual(data.get("name"), "ASCIIColors")
        self.assertEqual(data.get("message"), "JsonErrorMsg")
        self.assertEqual(data.get("user"), "TestUser")

    # --- Test Handlers (ASCIIColors API context) ---
    def test_file_handler_log(self):
        """Test FileHandler operation (via ASCIIColors API)."""
        ASCIIColors.set_log_level(INFO)
        fh = FileHandler(self.log_file, formatter=Formatter("%(message)s"))
        ASCIIColors.add_handler(fh)
        ASCIIColors.info("LogToFileTest")
        self.assertTrue(self.log_file.exists())
        content = self.log_file.read_text().strip()
        self.assertEqual(content, "LogToFileTest")

    def test_rotating_file_handler_log_real_rotation(self):
        """Test RotatingFileHandler performs actual file rotation."""
        log_file = self.rotate_log_file
        max_bytes = 50 
        backup_count = 2
        fmt = Formatter("%(message)s")
        rot_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, formatter=fmt)
        ASCIIColors.add_handler(rot_handler)
        ASCIIColors.set_log_level(DEBUG) 

        # Write message 1 (40 bytes + newline = 41 bytes)
        msg1 = "A" * 40
        ASCIIColors.info(msg1)
        self.assertTrue(log_file.exists())
        self.assertFalse((log_file.parent / f"{log_file.name}.1").exists())

        # Write message 2 (40 bytes). 41 + 41 = 82 > 50. 
        # Rotation should happen BEFORE writing msg2.
        # log_file becomes log_file.1 (containing msg1).
        # msg2 is written to new log_file.
        msg2 = "B" * 40
        ASCIIColors.info(msg2)
        time.sleep(0.05) 
        self.assertTrue(log_file.exists())
        self.assertTrue((log_file.parent / f"{log_file.name}.1").exists())
        
        # Check content
        self.assertEqual(log_file.read_text().strip(), msg2)
        self.assertEqual((log_file.parent / f"{log_file.name}.1").read_text().strip(), msg1)

    # --- Test Context Management (ASCIIColors API context) ---
    def test_context_manager_log_ascii_api(self):
        """Test context manager via ASCIIColors API."""
        ASCIIColors.set_log_level(INFO)
        fmt = Formatter("S:{session}|U:{user}|M:{message}", style='{')
        handler, stream = self._create_capture_stream_handler(formatter=fmt)
        ASCIIColors.add_handler(handler)

        ASCIIColors.set_context(session="S1", user="U1")
        ASCIIColors.info("M1")
        with ASCIIColors.context(user="U2", task="T"):
            ASCIIColors.info("M2")
            self.assertEqual(ASCIIColors.get_thread_context().get('task'), 'T')
        self.assertIsNone(ASCIIColors.get_thread_context().get('task'))
        ASCIIColors.info("M3")

        output = strip_ansi(self._get_stream_value(stream))
        self.assertIn("S:S1|U:U1|M:M1", output)
        self.assertIn("S:S1|U:U2|M:M2", output)
        self.assertIn("S:S1|U:U1|M:M3", output)

    # --- Test Direct Print Methods ---
    def test_direct_print_method(self):
        """Test the static print method writes to stream."""
        # Create a capture stream
        capture = io.StringIO()
        
        txt="DirectPrint"; col=ASCIIColors.color_cyan; sty=ASCIIColors.style_underline; end="X"; flush=True
        ASCIIColors.print(txt, color=col, style=sty, end=end, flush=flush, file=capture)
        
        output = capture.getvalue()
        # Verify the output contains expected components
        self.assertIn(txt, output)
        self.assertIn(col, output)
        self.assertIn(sty, output)
        self.assertIn(end, output)
        # Should end with reset + end
        self.assertTrue(output.endswith(ASCIIColors.color_reset + end))

    def test_direct_color_methods(self):
        """Test direct color methods (red, green, etc.) write to stream."""
        # Create a capture stream
        capture = io.StringIO()
        
        ASCIIColors.red("RedDirect", file=capture)
        output = capture.getvalue()
        
        # Verify output
        self.assertIn("RedDirect", output)
        self.assertIn(ASCIIColors.color_red, output)
        self.assertTrue(output.endswith(ASCIIColors.color_reset + "\n"))

    def test_composition_of_effects(self):
        """Test composition of effects (nesting calls)."""
        # Create a capture stream
        capture = io.StringIO()
        
        inner_text = "NestedText"
        # Inner: Bold, no emit, returns string
        bolded = ASCIIColors.bold(inner_text, emit=False, end="")

        # Outer: Magenta, emit=True to capture stream
        ASCIIColors.magenta(bolded, file=capture, end="")  # no extra newline

        output = capture.getvalue()
        
        # Verify the output contains expected components
        # Should have magenta color code
        self.assertIn(ASCIIColors.color_magenta, output)
        # Should have bold style code
        self.assertIn(ASCIIColors.style_bold, output)
        # Should have the text content
        self.assertIn(inner_text, output)

    # ===========================================================
    # --- Tests for Logging Compatibility Layer ---
    # ===========================================================

    def test_getLogger_returns_adapter(self):
        logger = getLogger("test_adapter")
        self.assertIsInstance(logger, ascii_colors._AsciiLoggerAdapter)
        self.assertEqual(logger.name, "test_adapter")

    def test_getLogger_caching(self):
        logger1 = getLogger("cached_logger")
        logger2 = getLogger("cached_logger")
        self.assertIs(logger1, logger2)

    @patch('ascii_colors.ASCIIColors._log')
    def test_logger_adapter_methods_call_core_log(self, mock_core_log):
        logger = getLogger("adapter_test")
        ASCIIColors.set_log_level(DEBUG)

        logger.debug("Debug msg %s", "arg1", extra_key="dv")
        # Match the keyword arguments used by _AsciiLoggerAdapter._log
        # Note: _AsciiLoggerAdapter._log formats the message before calling core _log
        mock_core_log.assert_called_with(
            level=LogLevel.DEBUG, 
            message="Debug msg arg1", 
            args=(), 
            exc_info=False,
            logger_name="adapter_test", 
            extra_key="dv"
        )
        
        mock_core_log.reset_mock()
        try:
            raise ValueError("Test Exc")
        except ValueError:
             logger.exception("Exception msg %s", "oops", detail="ze")

        self.assertTrue(mock_core_log.called)
        call_args, call_kwargs = mock_core_log.call_args
        self.assertEqual(call_kwargs['level'], LogLevel.ERROR)
        self.assertEqual(call_kwargs.get("exc_info"), True)

    def test_logger_adapter_handler_methods(self):
        logger = getLogger("handler_test")
        ASCIIColors.clear_handlers()
        handler, _ = self._create_capture_stream_handler()
        logger.addHandler(handler)
        self.assertIn(handler, ASCIIColors._handlers)
        logger.removeHandler(handler)
        self.assertNotIn(handler, ASCIIColors._handlers)

    # --- basicConfig Tests ---

    def test_basicConfig_defaults(self):
        basicConfig()
        self.assertTrue(ASCIIColors._basicConfig_called)
        self.assertEqual(len(ASCIIColors._handlers), 1)
        handler = ASCIIColors._handlers[0]
        self.assertIsInstance(handler, ConsoleHandler)
        # Handler defaults to DEBUG in this library
        self.assertEqual(handler.level, LogLevel.DEBUG)

    def test_basicConfig_level(self):
        basicConfig(level=DEBUG)
        self.assertEqual(ASCIIColors._global_level, LogLevel.DEBUG)

    def test_basicConfig_handlers(self):
        """Test basicConfig with explicit handlers list."""
        h1_stream = io.StringIO(); self.addCleanup(h1_stream.close)
        h1 = ConsoleHandler(stream=h1_stream, level=DEBUG)
        h2 = FileHandler(self.compat_log_file, level=INFO, mode='w')
        h2.setFormatter(Formatter("FILE: %(message)s"))

        # Need global level DEBUG to allow DEBUG messages to reach h1
        basicConfig(handlers=[h1, h2], level=DEBUG, format="DEFAULT: %(message)s")

        self.assertEqual(len(ASCIIColors._handlers), 2)
        self.assertEqual(h1.formatter.fmt, "DEFAULT: %(message)s")
        self.assertEqual(h2.formatter.fmt, "FILE: %(message)s")

        logger = getLogger("handlers_test")
        logger.warning("Warn Both")   # level 30. h1(10) ok, h2(20) ok.
        logger.info("Info File Only") # level 20. h1(10) ok, h2(20) ok.
        logger.debug("Debug h1 Only") # level 10. h1(10) ok, h2(20) NO.

        output_stream = strip_ansi(self._get_stream_value(h1_stream))
        self.assertIn("DEFAULT: Warn Both", output_stream)
        self.assertIn("DEFAULT: Info File Only", output_stream)
        self.assertIn("DEFAULT: Debug h1 Only", output_stream)

        content_file = self.compat_log_file.read_text()
        self.assertIn("FILE: Warn Both", content_file)
        self.assertIn("FILE: Info File Only", content_file)
        self.assertNotIn("Debug h1 Only", content_file)

    def test_ascii_api_then_basicConfig(self):
        """Test using basicConfig after ASCIIColors API calls."""
        # Use {}-style to avoid format errors with non-tuple args
        handler_ascii, stream_ascii = self._create_capture_stream_handler(
            level=DEBUG, formatter=Formatter("ASCII: {message}", style='{')
        )
        ASCIIColors.add_handler(handler_ascii)
        self.assertGreater(len(ASCIIColors._handlers), 0, "Handlers should be present before basicConfig")
        
        ASCIIColors.set_log_level(DEBUG)
        ASCIIColors.info("Before basicConfig")

        # basicConfig without force (should do nothing)
        basicConfig(level=INFO, format="%(message)s")
        self.assertEqual(ASCIIColors._global_level, LogLevel.DEBUG) 
        self.assertIs(ASCIIColors._handlers[0], handler_ascii)

        ASCIIColors.info("After basicConfig (no force)")
        output = strip_ansi(self._get_stream_value(stream_ascii))
        self.assertIn("ASCII: Before basicConfig", output)
        self.assertIn("ASCII: After basicConfig (no force)", output)

        # basicConfig WITH force
        local_stream = io.StringIO(); self.addCleanup(local_stream.close)
        basicConfig(level=WARNING, force=True, format="BC: %(message)s", stream=local_stream)
        self.assertEqual(ASCIIColors._global_level, LogLevel.WARNING)
        self.assertIsNot(ASCIIColors._handlers[0], handler_ascii)


class TestProgressBar(unittest.TestCase):
    def setUp(self):
        # ProgressBar writes directly to its file stream, not via print()
        # Use a StringIO to capture output
        self.capture_stream = io.StringIO()
        self.addCleanup(self.capture_stream.close)
        
        patcher_time = patch("time.time")
        self.mock_time = patcher_time.start()
        self.mock_time.return_value = 1000.0
        self.addCleanup(patcher_time.stop)
        
        patcher_tsize = patch("shutil.get_terminal_size")
        self.mock_tsize = patcher_tsize.start()
        self.mock_tsize.return_value = os.terminal_size((80, 24))
        self.addCleanup(patcher_tsize.stop)

    def _get_stream_output(self) -> str:
        """Get all output written to the capture stream."""
        value = self.capture_stream.getvalue()
        return value

    def _get_last_line(self) -> Optional[str]:
        """Get the last non-empty line from the capture stream."""
        value = self.capture_stream.getvalue()
        if not value:
            return None
        lines = [line for line in value.replace('\r', '\n').split('\n') if line.strip()]
        return lines[-1] if lines else None

    def test_iterable_wrapper(self):
        """Test ProgressBar wrapping an iterable."""
        data = [1, 2, 3, 4, 5]
        pbar = ProgressBar(data, desc="Iter Test", mininterval=0, file=self.capture_stream)
        list(pbar) # Consume iterator
        
        # The progress bar should have written output
        output = self._get_stream_output()
        self.assertGreater(len(output), 0)
        self.assertIn("Iter Test", output)
        self.assertIn("100%", output)

    def test_styling_options(self):
        """Test different styling parameters."""
        pbar = ProgressBar(total=10, desc="Style", progress_char=">", empty_char="-", 
                          bar_style="fill", mininterval=0, file=self.capture_stream)
        pbar.update(5)
        pbar.close()

        last_line = self._get_last_line()
        self.assertIsNotNone(last_line)
        # Check that custom chars appear in output
        self.assertIn(">", strip_ansi(last_line))

    def test_thread_safety(self):
        total = 100
        num_threads = 4
        # For thread safety test, we need a real stream that supports flush/close
        # Use the capture stream but note: concurrent writes may interleave
        pbar = ProgressBar(total=total, desc="Thread", mininterval=0.001, file=self.capture_stream)
        
        def worker():
            for _ in range(total // num_threads):
                pbar.update(1)
        
        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads: t.start()
        for t in threads: t.join()
        pbar.close()
        
        self.assertEqual(pbar.n, total)


class TestMenu(unittest.TestCase):
    """Test Menu class with injected key sources for deterministic testing."""
    
    def test_menu_creation_and_add_items(self):
        m = Menu("Test")
        sub = Menu("Sub")
        m.add_action("Action", lambda: None)
        m.add_submenu("Sub", sub)
        
        self.assertEqual(len(m.items), 2)
        self.assertEqual(m.items[0].text, "Action")
        self.assertEqual(m.items[0].item_type, 'action')
        self.assertEqual(m.items[1].item_type, 'submenu')

    def test_menu_add_choice_returns_value(self):
        """Test that add_choice returns the value on selection using injected keys."""
        # Inject keys: DOWN to move to Option B, then ENTER to select
        key_iter = iter(['DOWN', 'ENTER'])
        m = Menu("Choices", mode='return', clear_screen_on_run=False, key_source=key_iter)
        m.add_choice("Option A", value="value_a")
        m.add_choice("Option B", value="value_b")
        
        result = m.run()
        self.assertEqual(result, "value_b")

    def test_menu_run_select_action_enter(self):
        """Test that selecting an action calls it."""
        mock_action = Mock()
        # Inject keys: ENTER to select "Do", then QUIT to exit
        key_iter = iter(['ENTER', 'QUIT'])
        m = Menu("Action", clear_screen_on_run=False, key_source=key_iter, mode='execute')
        m.add_action("Do", mock_action)
        
        m.run()
        mock_action.assert_called_once()

    def test_menu_checkbox_mode(self):
        """Test checkbox selection with injected keys."""
        # Space to toggle A, DOWN to move, Space to toggle B, ENTER to confirm
        key_iter = iter([' ', 'DOWN', ' ', 'ENTER'])
        m = Menu("Checkbox Test", mode='checkbox', clear_screen_on_run=False, key_source=key_iter)
        m.add_checkbox("A", value="val_a", checked=False)
        m.add_checkbox("B", value="val_b", checked=False)
        m.add_checkbox("C", value="val_c", checked=False)
        
        result = m.run()
        self.assertIsNotNone(result)
        self.assertIn("val_a", result)
        self.assertIn("val_b", result)
        self.assertNotIn("val_c", result)

    def test_menu_checkbox_toggle_all(self):
        """Test checkbox toggle all with 'a' key."""
        key_iter = iter(['a', 'ENTER'])
        m = Menu("Checkbox All", mode='checkbox', clear_screen_on_run=False, key_source=key_iter)
        m.add_checkbox("X", value="val_x")
        m.add_checkbox("Y", value="val_y")
        m.add_checkbox("Z", value="val_z")
        
        result = m.run()
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)

    def test_menu_navigation_skips_disabled(self):
        """Test that navigation skips disabled items."""
        # DOWN should skip disabled Item B and go to Item C
        key_iter = iter(['DOWN', 'ENTER'])
        m = Menu("Skip Disabled", mode='return', clear_screen_on_run=False, key_source=key_iter)
        m.add_choice("Item A", value="a")
        m.add_choice("Item B", value="b", disabled=True)
        m.add_choice("Item C", value="c")
        
        result = m.run()
        self.assertEqual(result, "c")


class TestQuestionaryCompat(unittest.TestCase):
    """Tests for questionary-style interactive prompts with injected inputs."""

    def test_text_question_basic(self):
        """Test basic text input question."""
        # Inject input directly
        q = Text("What is your name", input_source=iter(["test answer"]))
        result = q.ask()
        self.assertEqual(result, "test answer")

    def test_text_question_with_default(self):
        """Test text input with default value."""
        # Empty input should use default
        q = Text("What is your name", default="Anonymous", input_source=iter([""]))
        result = q.ask()
        self.assertEqual(result, "Anonymous")

    def test_text_question_validation(self):
        """Test text input with validation - retries until valid."""
        # First invalid, then valid
        q = Text("Enter code", validate=lambda x: x.isalnum(), input_source=iter(["invalid!", "valid123"]))
        result = q.ask()
        self.assertEqual(result, "valid123")

    def test_password_question(self):
        """Test password input."""
        q = Password("Enter password", input_source=iter(["secret123"]))
        result = q.ask()
        self.assertEqual(result, "secret123")

    def test_password_question_with_confirm(self):
        """Test password with confirmation."""
        q = Password("Enter password", confirm=True, input_source=iter(["secret123", "secret123"]))
        result = q.ask()
        self.assertEqual(result, "secret123")

    def test_password_confirm_mismatch_then_match(self):
        """Test password confirmation mismatch then match."""
        # First attempt: password and confirmation don't match
        # Second attempt: they match
        q = Password("Enter password", confirm=True, 
                    input_source=iter(["secret123", "wrong", "secret123", "secret123"]))
        result = q.ask()
        self.assertEqual(result, "secret123")

    def test_confirm_question_yes(self):
        """Test confirm question with yes answer."""
        q = Confirm("Continue?", default=False, input_source=iter(["y"]))
        result = q.ask()
        self.assertTrue(result)

    def test_confirm_question_no(self):
        """Test confirm question with no answer."""
        q = Confirm("Continue?", default=True, input_source=iter(["n"]))
        result = q.ask()
        self.assertFalse(result)

    def test_confirm_question_default(self):
        """Test confirm question with default (empty input)."""
        q = Confirm("Continue?", default=True, input_source=iter([""]))
        result = q.ask()
        self.assertTrue(result)

    def test_select_question_navigation(self):
        """Test select question with navigation using injected keys."""
        # DOWN, DOWN, ENTER to select C
        q = Select("Choose", choices=["A", "B", "C"], key_source=iter(['DOWN', 'DOWN', 'ENTER']))
        result = q.ask()
        self.assertEqual(result, "C")

    def test_select_question_with_dict_choices(self):
        """Test select with dictionary choices (name/value)."""
        q = Select("Choose", choices=[
            {"name": "Option One", "value": "opt1"},
            {"name": "Option Two", "value": "opt2"}
        ], key_source=iter(['ENTER']))
        result = q.ask()
        self.assertEqual(result, "opt1")

    def test_select_question_disabled_skipped(self):
        """Test that disabled options are skipped during navigation."""
        # First option is disabled, so DOWN should go to second enabled
        q = Select("Choose", choices=[
            {"name": "Disabled", "value": "bad", "disabled": True},
            {"name": "Enabled", "value": "good"},
        ], key_source=iter(['ENTER']))
        result = q.ask()
        self.assertEqual(result, "good")

    def test_checkbox_question_basic(self):
        """Test basic checkbox (multi-select)."""
        # Space to toggle A, DOWN, Space to toggle B, ENTER to confirm
        q = Checkbox("Select items", choices=["A", "B", "C"], 
                    key_source=iter([' ', 'DOWN', ' ', 'ENTER']))
        result = q.ask()
        self.assertIsNotNone(result)
        self.assertIn("A", result)
        self.assertIn("B", result)
        self.assertNotIn("C", result)

    def test_checkbox_toggle_all(self):
        """Test checkbox toggle all with 'a' key."""
        q = Checkbox("Select all", choices=["X", "Y", "Z"],
                    key_source=iter(['a', 'ENTER']))
        result = q.ask()
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)

    def test_checkbox_min_selected(self):
        """Test checkbox with minimum selection requirement."""
        # ENTER with nothing selected (should not work in real UI, but with our implementation
        # we need to actually select something), so: select A, then ENTER
        q = Checkbox("Select at least one", choices=["A", "B"], min_selected=1,
                    key_source=iter([' ', 'ENTER']))
        result = q.ask()
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    def test_convenience_functions(self):
        """Test that convenience functions create correct types."""
        self.assertIsInstance(text("Q"), Text)
        self.assertIsInstance(password("Q"), Password)
        self.assertIsInstance(confirm("Q"), Confirm)
        self.assertIsInstance(select("Q", ["a"]), Select)
        self.assertIsInstance(checkbox("Q", ["a"]), Checkbox)
        self.assertIsInstance(autocomplete("Q", ["a"]), Autocomplete)
        self.assertIsInstance(form(text("Q")), Form)


if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()

