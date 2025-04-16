# -*- coding: utf-8 -*-
"""
Unit tests for the ascii_colors library.

Author: Saifeddine ALOUI (ParisNeo)
License: Apache License 2.0
"""

import inspect  # <-- Added missing import
import io
import json
# Need regex for stripping ANSI codes in get_console_output
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure the module path is correct for testing
try:
    from ascii_colors import Handler  # <-- Added Handler
    from ascii_colors import (ASCIIColors, ConsoleHandler, FileHandler,
                              Formatter, JSONFormatter, LogLevel,
                              RotatingFileHandler, get_trace_exception,
                              trace_exception)
except ImportError:
    # If running directly from tests directory, adjust path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from ascii_colors import Handler  # <-- Added Handler
    from ascii_colors import (ASCIIColors, ConsoleHandler, FileHandler,
                              Formatter, JSONFormatter, LogLevel,
                              RotatingFileHandler, get_trace_exception,
                              trace_exception)


class TestASCIIColors(unittest.TestCase):
    """Test suite for ASCIIColors class and related components"""

    def setUp(self):
        """Set up test environment before each test"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.log_file = self.temp_dir / "test.log"
        self.json_log_file = self.temp_dir / "test.jsonl"
        self.rotate_log_file = self.temp_dir / "rotate.log"

        # Reset ASCIIColors state before each test
        ASCIIColors.clear_handlers()
        ASCIIColors.set_log_level(LogLevel.DEBUG)  # Default to lowest level for tests
        ASCIIColors.clear_context()  # Clear any leftover context
        # Add a default console handler for tests that check console output
        self.mock_stdout = io.StringIO()
        # Use a simple formatter for most console tests to avoid date/time issues
        simple_formatter = Formatter("{level_name}:{message}")
        self.default_console_handler = ConsoleHandler(
            stream=self.mock_stdout, formatter=simple_formatter
        )
        ASCIIColors.add_handler(self.default_console_handler)

    def tearDown(self):
        """Clean up test environment after each test"""
        ASCIIColors.clear_handlers()
        ASCIIColors.clear_context()
        # Close the mock stream
        self.mock_stdout.close()
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)

    def get_console_output(self) -> str:
        """Helper to get captured stdout content."""
        # Strip color codes for easier assertion in many cases
        output = self.mock_stdout.getvalue()
        # Simple regex to remove ANSI codes
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", output)

    def get_raw_console_output(self) -> str:
        """Helper to get captured stdout content with color codes."""
        return self.mock_stdout.getvalue()

    # --- Test Core Functionality ---

    def test_log_levels_enum(self):
        """Test LogLevel enum values"""
        self.assertEqual(LogLevel.DEBUG, 0)
        self.assertEqual(LogLevel.INFO, 1)
        self.assertEqual(LogLevel.WARNING, 2)
        self.assertEqual(LogLevel.ERROR, 3)

    def test_default_handler_present(self):
        """Test that a ConsoleHandler is present by default (in setUp)."""
        self.assertEqual(len(ASCIIColors._handlers), 1)
        self.assertIsInstance(ASCIIColors._handlers[0], ConsoleHandler)

    def test_add_remove_clear_handlers(self):
        """Test adding, removing, and clearing handlers."""
        initial_count = len(ASCIIColors._handlers)
        file_handler = FileHandler(self.log_file)
        ASCIIColors.add_handler(file_handler)
        self.assertEqual(len(ASCIIColors._handlers), initial_count + 1)
        self.assertIn(file_handler, ASCIIColors._handlers)

        ASCIIColors.remove_handler(file_handler)
        self.assertEqual(len(ASCIIColors._handlers), initial_count)
        self.assertNotIn(file_handler, ASCIIColors._handlers)

        # Test removing non-existent handler
        ASCIIColors.remove_handler(file_handler)  # Should not raise error
        self.assertEqual(len(ASCIIColors._handlers), initial_count)

        ASCIIColors.clear_handlers()
        self.assertEqual(len(ASCIIColors._handlers), 0)

    def test_global_log_level_filtering(self):
        """Test filtering based on the global log level."""
        ASCIIColors.set_log_level(LogLevel.WARNING)
        file_handler = FileHandler(self.log_file)
        ASCIIColors.add_handler(file_handler)

        ASCIIColors.debug("Debug message")
        ASCIIColors.info("Info message")
        ASCIIColors.warning("Warning message")
        ASCIIColors.error("Error message")

        # Check console output (should also be filtered)
        console_output = self.get_console_output()
        self.assertNotIn("Debug message", console_output)
        self.assertNotIn("Info message", console_output)
        self.assertIn("Warning message", console_output)
        self.assertIn("Error message", console_output)

        # Check file output
        self.assertTrue(self.log_file.exists())
        content = self.log_file.read_text()
        # Use default formatter format for file check
        self.assertNotIn("Debug message", content)
        self.assertNotIn("Info message", content)
        self.assertIn("Warning message", content)
        self.assertIn("Error message", content)
        self.assertRegex(
            content,
            r"\[WARNING\]\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] Warning message",
        )

    def test_handler_level_filtering(self):
        """Test filtering based on individual handler levels."""
        ASCIIColors.set_log_level(LogLevel.DEBUG)  # Global level allows all
        file_handler = FileHandler(self.log_file, level=LogLevel.ERROR)
        ASCIIColors.add_handler(file_handler)

        ASCIIColors.debug("Debug msg")
        ASCIIColors.info("Info msg")
        ASCIIColors.warning("Warning msg")
        ASCIIColors.error("Error msg")

        # Console should get everything (default handler is DEBUG with simple format)
        console_output = self.get_console_output()
        self.assertIn("DEBUG:Debug msg", console_output)
        self.assertIn("INFO:Info msg", console_output)
        self.assertIn("WARNING:Warning msg", console_output)
        self.assertIn("ERROR:Error msg", console_output)

        # File should only get ERROR
        self.assertTrue(self.log_file.exists())
        content = self.log_file.read_text()
        self.assertNotIn("Debug msg", content)
        self.assertNotIn("Info msg", content)
        self.assertNotIn("Warning msg", content)
        self.assertIn("Error msg", content)
        self.assertRegex(
            content, r"\[ERROR\]\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] Error msg"
        )

    # --- Test Formatters ---

    def test_default_formatter(self):
        """Test the default Formatter output (re-add handler with default fmt)."""
        ASCIIColors.remove_handler(self.default_console_handler)  # remove simple one
        default_fmt_handler = ConsoleHandler(stream=self.mock_stdout)
        ASCIIColors.add_handler(default_fmt_handler)

        ASCIIColors.info("Test default format")
        raw_output = self.get_raw_console_output()  # Need raw for color codes
        # Example: \x1b[34;1m[INFO][2023-10-27 10:00:00] Test default format\x1b[0m
        self.assertRegex(
            raw_output,
            r"\[INFO\]\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] Test default format",
        )
        self.assertTrue(raw_output.startswith(ASCIIColors.color_bright_blue))
        self.assertTrue(raw_output.strip().endswith(ASCIIColors.color_reset))

    def test_custom_formatter_basic(self):
        """Test a custom format string."""
        # setUp provides simple formatter {level_name}:{message}
        ASCIIColors.warning("Custom format test")
        output = self.get_console_output()
        self.assertIn("WARNING:Custom format test", output)

    def test_formatter_with_source(self):
        """Test formatter including source file/line/func."""
        # Need to replace the default handler with one using include_source
        ASCIIColors.remove_handler(self.default_console_handler)
        formatter = Formatter(
            "[{file_name}:{line_no} {func_name}] {message}", include_source=True
        )
        source_handler = ConsoleHandler(stream=self.mock_stdout, formatter=formatter)
        ASCIIColors.add_handler(source_handler)

        current_line = inspect.currentframe().f_lineno + 1  # Line where info is called
        ASCIIColors.info("Source info test")

        output = self.get_console_output()  # Strips colors
        test_file_name = Path(__file__).name  # Get current test file name
        self.assertIn(
            f"[{test_file_name}:{current_line} test_formatter_with_source] Source info test",
            output,
        )

    def test_formatter_with_kwargs(self):
        """Test formatter using extra kwargs."""
        formatter = Formatter("{message} user={user_id}")
        self.default_console_handler.set_formatter(
            formatter
        )  # Apply to existing handler
        ASCIIColors.info("Login attempt", user_id=123)
        output = self.get_console_output()
        self.assertIn("Login attempt user=123", output)

    def test_json_formatter(self):
        """Test JSONFormatter output including kwargs."""
        # Use include_fields=None to ensure kwargs are included
        json_formatter = JSONFormatter(include_fields=None, include_source=False)
        json_handler = FileHandler(self.json_log_file, formatter=json_formatter)
        ASCIIColors.add_handler(json_handler)

        test_key = "my_test_key"
        test_value = "my_test_value"
        test_num = 123.45

        ASCIIColors.warning(
            "JSON test log", **{test_key: test_value, "num": test_num}
        )  # Pass kwargs explicitly

        self.assertTrue(self.json_log_file.exists())
        content = self.json_log_file.read_text().strip()
        log_entry = None
        try:
            log_entry = json.loads(content)
        except json.JSONDecodeError as e:
            self.fail(f"Failed to parse JSON log: {e}\nContent: {content}")

        # Add debugging print if assertion fails
        fail_msg = f"JSON content mismatch. Got: {log_entry}"
        self.assertIsNotNone(
            log_entry, "log_entry should not be None"
        )  # Check parsing worked
        self.assertEqual(log_entry.get("level_name"), "WARNING", fail_msg)
        self.assertEqual(log_entry.get("message"), "JSON test log", fail_msg)
        self.assertEqual(
            log_entry.get(test_key), test_value, fail_msg
        )  # Check dynamic key
        self.assertEqual(log_entry.get("num"), test_num, fail_msg)
        self.assertIn("datetime", log_entry, fail_msg)

    def test_json_formatter_iso_date(self):
        """Test JSONFormatter with ISO date format."""
        json_formatter = JSONFormatter(datefmt="iso")  # Default is ISO now
        json_handler = FileHandler(self.json_log_file, formatter=json_formatter)
        ASCIIColors.add_handler(json_handler)
        ASCIIColors.info("ISO date test")
        content = self.json_log_file.read_text().strip()
        log_entry = json.loads(content)
        # Check if datetime looks like ISO format (e.g., 2023-10-27T12:34:56.123456)
        self.assertRegex(
            log_entry["datetime"], r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?"
        )

    # --- Test Handlers ---

    def test_file_handler(self):
        """Test basic FileHandler operation."""
        file_handler = FileHandler(self.log_file)
        ASCIIColors.add_handler(file_handler)
        test_message = "Message for file handler"
        ASCIIColors.info(test_message)

        self.assertTrue(self.log_file.exists())
        content = self.log_file.read_text()
        # Default file format example: [INFO][2023-10-27 10:00:00] Message for file handler
        self.assertRegex(
            content, r"\[INFO\]\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] " + test_message
        )
        # Check for \u001b specifically for ANSI codes
        self.assertNotIn("\u001b", content)  # Ensure no color codes in file

    def test_rotating_file_handler(self):
        """Test RotatingFileHandler functionality."""
        # Use small size for testing rotation
        max_bytes = 500
        backup_count = 2
        rot_handler = RotatingFileHandler(
            self.rotate_log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        # Use simple formatter for predictable size
        rot_handler.set_formatter(Formatter("{message}"))
        ASCIIColors.add_handler(rot_handler)

        # Log messages until rotation should occur multiple times
        base_msg = "Rotating log message."
        # Estimate message size (including newline)
        est_msg_len = len(base_msg) + 5 + 1  # Base + space + up to 3 digits + newline

        # Calculate number of messages to ensure backupCount rotations happen
        num_msgs_to_rotate = (max_bytes // est_msg_len) * (
            backup_count + 1
        ) + 5  # Log enough for all backups + new file

        for i in range(num_msgs_to_rotate):
            ASCIIColors.info(f"{base_msg} {i}")

        # Check that rotation happened as expected
        log_path = self.temp_dir / self.rotate_log_file.name
        self.assertTrue(log_path.exists())
        self.assertTrue((self.temp_dir / f"{log_path.name}.1").exists())
        self.assertTrue(
            (self.temp_dir / f"{log_path.name}.2").exists()
        )  # Now this should pass
        # Ensure oldest backup (.3 with backupCount=2) doesn't exist
        self.assertFalse(
            (self.temp_dir / f"{log_path.name}.{backup_count + 1}").exists()
        )

        # Check current file size is small (just started new file after last rotation)
        self.assertLess(log_path.stat().st_size, max_bytes)

    # --- Test Context Management ---

    def test_set_clear_context(self):
        """Test setting and clearing thread-local context."""
        formatter = Formatter("{message} | context: {my_val}")
        self.default_console_handler.set_formatter(formatter)

        ASCIIColors.set_context(my_val="initial")
        ASCIIColors.info("Msg 1")
        self.assertIn("Msg 1 | context: initial", self.get_console_output())

        ASCIIColors.set_context(my_val="updated")
        ASCIIColors.info("Msg 2")
        self.assertIn("Msg 2 | context: updated", self.get_console_output())

        ASCIIColors.clear_context("my_val")
        ASCIIColors.info("Msg 3")  # Context key removed
        # Check for the new format error message instead of the raw placeholder
        self.assertIn("[FORMAT_ERROR: Missing key 'my_val']", self.get_console_output())
        # Check that the original format string part is still there
        self.assertIn("{message} | context: {my_val}", self.get_console_output())

        ASCIIColors.set_context(val1="A", val2="B")
        ASCIIColors.clear_context()  # Clear all
        self.assertEqual(ASCIIColors.get_thread_context(), {})

    def test_context_manager(self):
        """Test the context() context manager."""
        formatter = Formatter(
            "msg='{message}' session='{session_id}' user='{user_id}' task='{task}'"
        )
        self.default_console_handler.set_formatter(formatter)

        ASCIIColors.set_context(
            session_id="S1", user_id="U_outer", task="T_outer"
        )  # Add task here too
        ASCIIColors.info("Outer 1")
        self.assertIn(
            "msg='Outer 1' session='S1' user='U_outer' task='T_outer'",
            self.get_console_output(),
        )

        with ASCIIColors.context(
            user_id="U_inner", task="T_inner"
        ):  # Override user, task
            ASCIIColors.info("Inner 1")
            # Context should be merged/overridden: session=S1, user=U_inner, task=T_inner
            self.assertIn(
                "msg='Inner 1' session='S1' user='U_inner' task='T_inner'",
                self.get_console_output(),
            )

            with ASCIIColors.context(session_id="S2"):  # Override session
                ASCIIColors.info("Nested Inner")
                # Context: session=S2, user=U_inner, task=T_inner
                self.assertIn(
                    "msg='Nested Inner' session='S2' user='U_inner' task='T_inner'",
                    self.get_console_output(),
                )

            ASCIIColors.info("Inner 2")  # Back from nested context
            # Back to user=U_inner, task=T_inner, session=S1
            self.assertIn(
                "msg='Inner 2' session='S1' user='U_inner' task='T_inner'",
                self.get_console_output(),
            )

        ASCIIColors.info("Outer 2")  # Back from outer context
        # Back to original context: session=S1, user=U_outer, task=T_outer
        self.assertIn(
            "msg='Outer 2' session='S1' user='U_outer' task='T_outer'",
            self.get_console_output(),
        )

    # --- Test Backward Compatibility & Direct Color Methods ---

    def test_deprecated_set_log_file(self):
        """Test the backward-compatible set_log_file adds a FileHandler."""
        ASCIIColors.clear_handlers()  # Start clean
        ASCIIColors.set_log_file(self.log_file)
        self.assertEqual(len(ASCIIColors._handlers), 1)
        self.assertIsInstance(ASCIIColors._handlers[0], FileHandler)
        self.assertEqual(ASCIIColors._handlers[0].filename, self.log_file)

        # Test it adds, not replaces
        ASCIIColors.set_log_file(self.temp_dir / "another.log")
        self.assertEqual(len(ASCIIColors._handlers), 2)

    def test_deprecated_set_template_warning(self):
        """Test that set_template logs a warning."""
        ASCIIColors.clear_handlers()  # Start clean
        mock_handler = MagicMock(spec=Handler)  # Now Handler is imported
        ASCIIColors.add_handler(mock_handler)
        ASCIIColors.set_template(LogLevel.INFO, "some template")

        # Check if the handler received the warning message
        # handle args: level, message, timestamp, exc_info, **kwargs
        self.assertTrue(mock_handler.handle.called)
        call_args = mock_handler.handle.call_args[0]  # Get positional args tuple
        self.assertEqual(call_args[0], LogLevel.WARNING)  # Check level
        self.assertIn("set_template is DEPRECATED", call_args[1])  # Check message

    def test_direct_color_methods_output(self):
        """Test direct color methods log to INFO and color console."""
        ASCIIColors.clear_handlers()  # Remove default console handler first
        file_handler = FileHandler(self.log_file)
        file_handler.set_formatter(Formatter("{level_name}:{message}"))
        ASCIIColors.add_handler(file_handler)

        ASCIIColors.red("Red message")
        ASCIIColors.green("Green message")

        # Re-add console handler to check colors there too
        ASCIIColors.add_handler(self.default_console_handler)  # Uses simple format
        ASCIIColors.blue("Blue message")  # This now goes to both handlers

        # Check file content (should have all messages as INFO, no color)
        content = self.log_file.read_text()
        self.assertIn("INFO:Red message", content)
        self.assertIn("INFO:Green message", content)
        self.assertIn(
            "INFO:Blue message", content
        )  # <-- Correction: Blue SHOULD be in the file now
        self.assertNotIn("\u001b", content)  # No color codes

        # Check console output (only blue message captured after handler added)
        console_output = self.get_console_output()
        self.assertIn("INFO:Blue message", console_output)

        # To check color, get raw output for the blue message part
        raw_console_output = self.get_raw_console_output()
        # The default_console_handler uses simple format, but ConsoleHandler.emit applies colors
        self.assertTrue(raw_console_output.strip().startswith(ASCIIColors.color_blue))
        self.assertIn("INFO:Blue message", raw_console_output)  # Message content
        self.assertTrue(raw_console_output.strip().endswith(ASCIIColors.color_reset))

    def test_success_fail_methods(self):
        """Test success (INFO green) and fail (ERROR red) methods."""
        ASCIIColors.success("It worked")
        ASCIIColors.fail("It failed")

        raw_console_output = self.get_raw_console_output()  # Check raw for colors

        # Success: INFO, green
        self.assertTrue(raw_console_output.startswith(ASCIIColors.color_green))
        self.assertIn("INFO:It worked", raw_console_output)

        # Fail: ERROR, red (will be after success message)
        self.assertIn(
            ASCIIColors.color_red + "ERROR:It failed" + ASCIIColors.color_reset,
            raw_console_output,
        )

    def test_print_method_backward_compatibility(self):
        """Test the overridden print method."""
        # Need handler that respects _raw_color and _raw_style
        # The default ConsoleHandler does this. Let's use raw output.
        ASCIIColors.print(
            "Old print message",
            color=ASCIIColors.color_cyan,
            style=ASCIIColors.style_bold,
        )

        raw_console_output = self.get_raw_console_output()
        # ConsoleHandler.emit prepends style+color, then formatted msg, then reset
        # Default test formatter is "{level_name}:{message}"
        expected_start = ASCIIColors.style_bold + ASCIIColors.color_cyan
        expected_message_part = "INFO:Old print message"  # Print logs as INFO
        expected_end = ASCIIColors.color_reset

        self.assertTrue(raw_console_output.startswith(expected_start))
        self.assertIn(expected_message_part, raw_console_output)
        self.assertTrue(raw_console_output.strip().endswith(expected_end))

    # --- Test Exception Handling ---

    def test_get_trace_exception(self):
        """Test the get_trace_exception utility."""
        try:
            1 / 0
        except ZeroDivisionError as e:
            trace = get_trace_exception(e)
            self.assertIsInstance(trace, str)
            self.assertIn("Traceback (most recent call last):", trace)
            self.assertIn("ZeroDivisionError: division by zero", trace)
            # Check for function name from *this* frame
            self.assertIn("test_get_trace_exception", trace)

    def test_trace_exception_utility(self):
        """Test the trace_exception convenience function."""
        ASCIIColors.clear_handlers()  # Use file handler for clean capture
        file_handler = FileHandler(self.log_file)
        # Default Formatter handles exc_info by appending format_exception output
        ASCIIColors.add_handler(file_handler)

        test_error_msg = "Test error for trace"
        try:
            raise ValueError(test_error_msg)
        except ValueError as e:
            trace_exception(e)  # Calls ASCIIColors.error with exc_info=e

        content = self.log_file.read_text()
        # Check for the original message logged by trace_exception()
        self.assertIn("Exception Traceback (ValueError)", content)
        # Check for the actual traceback content appended by the formatter
        self.assertIn("Traceback (most recent call last):", content)
        self.assertIn(f"ValueError: {test_error_msg}", content)

    def test_error_with_exc_info_true(self):
        """Test logging error with exc_info=True."""
        ASCIIColors.clear_handlers()
        file_handler = FileHandler(self.log_file)
        # Default Formatter handles exc_info
        ASCIIColors.add_handler(file_handler)

        try:
            int("abc")
        except ValueError as e:
            # Call error *inside* the except block for sys.exc_info() to work
            ASCIIColors.error(f"Conversion failed: {e}", exc_info=True)

        content = self.log_file.read_text()
        self.assertIn("Conversion failed", content)
        self.assertIn("Traceback (most recent call last):", content)
        self.assertIn(
            "ValueError: invalid literal for int() with base 10: 'abc'", content
        )

    # --- Test Other Utilities ---
    # Need to patch print for highlight/multicolor as they print directly
    @patch("builtins.print")
    def test_highlight(self, mock_print):
        """Test the highlight utility (direct print)."""
        ASCIIColors.highlight(
            "Some text with KEYWORD.",
            "KEYWORD",
            color=ASCIIColors.color_blue,
            highlight_color=ASCIIColors.color_red,
        )

        # Check the single call to print
        self.assertEqual(mock_print.call_count, 1)
        args, kwargs = mock_print.call_args
        output_str = args[0]

        # Build expected string carefully
        expected = (
            ASCIIColors.color_blue
            + "Some text with "
            + ASCIIColors.color_red
            + "KEYWORD"
            + ASCIIColors.color_blue
            + "."  # Ensure original color resumes
            + ASCIIColors.color_reset
        )
        self.assertEqual(output_str, expected)

    @patch("builtins.print")
    def test_multicolor(self, mock_print):
        """Test the multicolor utility (direct print)."""
        texts = ["Red ", "Green ", "Blue"]
        colors = [
            ASCIIColors.color_red,
            ASCIIColors.color_green,
            ASCIIColors.color_blue,
        ]
        ASCIIColors.multicolor(texts, colors, end="END\n")

        # Check calls to print: one per color segment + final reset
        self.assertEqual(mock_print.call_count, len(texts) + 1)
        # Check first call
        args, kwargs = mock_print.call_args_list[0]
        self.assertEqual(args[0], ASCIIColors.color_red + texts[0])
        self.assertEqual(kwargs.get("end"), "")
        # Check second call
        args, kwargs = mock_print.call_args_list[1]
        self.assertEqual(args[0], ASCIIColors.color_green + texts[1])
        # Check third call
        args, kwargs = mock_print.call_args_list[2]
        self.assertEqual(args[0], ASCIIColors.color_blue + texts[2])
        # Check final call (reset)
        args, kwargs = mock_print.call_args_list[-1]
        self.assertEqual(args[0], ASCIIColors.color_reset)
        self.assertEqual(kwargs.get("end"), "END\n")  # Check custom end parameter

    @patch("time.sleep", return_value=None)  # Mock sleep to speed up test
    @patch("builtins.print")  # Mock print to check animation output
    def test_execute_with_animation_success(self, mock_print, mock_sleep):
        """Test execute_with_animation on successful function."""

        def my_func(a, b):
            print(">>> Function executing <<<")
            return a + b

        result = ASCIIColors.execute_with_animation(
            "Calculating...", my_func, 5, 3, color=ASCIIColors.color_cyan
        )

        self.assertEqual(result, 8)

        # Get ALL calls, including those with empty args like print()
        all_calls = mock_print.call_args_list
        # Extract the first argument from calls that HAVE arguments
        call_args_list = [
            call[0][0] for call in all_calls if call[0]
        ]  # Filter if args tuple is not empty

        # Check animation frame print (example) - uses \r
        self.assertTrue(
            any(
                "\r" + ASCIIColors.color_cyan + "Calculating... " in call
                for call in call_args_list
            ),
            "Animation frame not found",
        )
        # Check print from inside function
        self.assertIn(
            ">>> Function executing <<<",
            call_args_list,
            "Inner function print not found",
        )

        # Check final status print (success) - uses \r
        status_line_found = any(
            (
                "\r"
                + ASCIIColors.color_cyan
                + "Calculating... "
                + ASCIIColors.color_green
                + "✓"
                + ASCIIColors.color_reset
            )
            in call
            for call in call_args_list
        )
        self.assertTrue(
            status_line_found, "Final success status line not found in print calls"
        )

        # Check final newline print - the last call should be print() -> args=(), kwargs={}
        self.assertTrue(len(all_calls) > 0, "No print calls captured")
        self.assertEqual(
            all_calls[-1][0],
            (),
            f"Last print call args were not empty: {all_calls[-1][0]}",
        )

    @patch("time.sleep", return_value=None)
    @patch("builtins.print")
    def test_execute_with_animation_failure(self, mock_print, mock_sleep):
        """Test execute_with_animation on function raising exception."""
        error_message = "Task failed spectacularly"

        def my_failing_func():
            raise ValueError(error_message)

        with self.assertRaises(ValueError) as cm:
            ASCIIColors.execute_with_animation(
                "Trying...", my_failing_func, color=ASCIIColors.color_yellow
            )

        self.assertEqual(str(cm.exception), error_message)

        # Get ALL calls, including those with empty args like print()
        all_calls = mock_print.call_args_list
        # Extract the first argument from calls that HAVE arguments
        call_args_list = [
            call[0][0] for call in all_calls if call[0]
        ]  # Filter if args tuple is not empty

        # Check final status print (failure) - uses \r
        status_line_found = any(
            (
                "\r"
                + ASCIIColors.color_yellow
                + "Trying... "
                + ASCIIColors.color_red
                + "✗"
                + ASCIIColors.color_reset
            )
            in call
            for call in call_args_list
        )
        self.assertTrue(
            status_line_found, "Final failure status line not found in print calls"
        )

        # Check final newline print - the last call should be print() -> args=(), kwargs={}
        self.assertTrue(len(all_calls) > 0, "No print calls captured")
        self.assertEqual(
            all_calls[-1][0],
            (),
            f"Last print call args were not empty: {all_calls[-1][0]}",
        )


if __name__ == "__main__":
    unittest.main()
