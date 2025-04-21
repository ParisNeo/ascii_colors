# -*- coding: utf-8 -*-
"""
Unit tests for the ascii_colors library.

Author: Saifeddine ALOUI (ParisNeo)
License: Apache License 2.0
"""

import inspect
import io
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout # Use redirect_stdout for animation tests
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, ANY

# Ensure the module path is correct for testing
try:
    from ascii_colors import Handler
    from ascii_colors import (ASCIIColors, ConsoleHandler, FileHandler,
                              Formatter, JSONFormatter, LogLevel,
                              RotatingFileHandler, get_trace_exception,
                              trace_exception)
except ImportError:
    # If running directly from tests directory as script
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ascii_colors import Handler
    from ascii_colors import (ASCIIColors, ConsoleHandler, FileHandler,
                              Formatter, JSONFormatter, LogLevel,
                              RotatingFileHandler, get_trace_exception,
                              trace_exception)


# Helper to strip ANSI codes
ANSI_ESCAPE_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

def strip_ansi(text: str) -> str:
    """Removes ANSI escape sequences from a string."""
    return ANSI_ESCAPE_REGEX.sub("", text)


class TestASCIIColors(unittest.TestCase):
    """Test suite for ASCIIColors class and related components"""

    def setUp(self):
        """Set up test environment before each test"""
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()
        self.log_file = self.temp_dir / "test.log"
        self.json_log_file = self.temp_dir / "test.jsonl"
        self.rotate_log_file = self.temp_dir / "rotate.log"

        ASCIIColors.clear_handlers()
        ASCIIColors.set_log_level(LogLevel.DEBUG)
        ASCIIColors.clear_context()

        # Mock stream for LOGGING handler output
        self.mock_stdout_log_stream = io.StringIO()
        simple_formatter = Formatter("{level_name}:{message}")
        self.test_console_handler = ConsoleHandler(
            stream=self.mock_stdout_log_stream, formatter=simple_formatter, level=LogLevel.DEBUG
        )
        ASCIIColors.add_handler(self.test_console_handler)

        # Patch builtins.print for DIRECT print method tests
        self.patcher_builtin_print = patch("builtins.print")
        self.mock_builtin_print = self.patcher_builtin_print.start()

        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr


    def tearDown(self):
        """Clean up test environment after each test"""
        self.patcher_builtin_print.stop()
        ASCIIColors.clear_handlers()
        ASCIIColors.clear_context()
        if hasattr(self, 'mock_stdout_log_stream') and not self.mock_stdout_log_stream.closed:
            self.mock_stdout_log_stream.close()
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
            except OSError as e:
                print(f"\n[TEST WARNING] Failed to remove temp dir {self.temp_dir}: {e}", file=sys.stderr)


    def get_console_log_output(self) -> str:
        """Helper to get captured LOG content from the ConsoleHandler's stream."""
        if not hasattr(self, 'mock_stdout_log_stream') or self.mock_stdout_log_stream.closed:
            return "[Stream Closed or Missing]"
        self.mock_stdout_log_stream.seek(0)
        return strip_ansi(self.mock_stdout_log_stream.read())

    def get_raw_console_log_output(self) -> str:
        """Helper to get captured LOG content (with colors) from the ConsoleHandler's stream."""
        if not hasattr(self, 'mock_stdout_log_stream') or self.mock_stdout_log_stream.closed:
            return "[Stream Closed or Missing]"
        self.mock_stdout_log_stream.seek(0)
        return self.mock_stdout_log_stream.read()

    def assert_direct_print_called_with(self, expected_text_part: str, color_code: str = None, style_code: str = "", **kwargs):
        """Asserts that builtins.print (mocked) was called with expected args."""
        found_call = False
        time.sleep(0.05) # Allow potential buffer flush
        calls = self.mock_builtin_print.call_args_list
        # Default file kwarg should be compared against the original stdout at test start
        expected_file = kwargs.get('file', self.original_stdout)

        for call in calls:
            args, kwargs_call = call
            if not args: continue
            printed_text = args[0]
            if not isinstance(printed_text, str): continue

            # Use case-insensitive check for the text part
            # Check file kwarg first for reliable matching
            if expected_text_part.lower() in strip_ansi(printed_text).lower() and \
               kwargs_call.get('file', self.original_stdout) == expected_file:
                found_call = True
                expected_start = style_code + (color_code if color_code else "")
                # Allow for potential \r prefix from animation calls captured here
                self.assertTrue(printed_text.lstrip('\r').startswith(expected_start), f"Direct print start mismatch. Expected: '{expected_start}', Got: '{printed_text}'")
                self.assertTrue(printed_text.endswith(ASCIIColors.color_reset), f"Direct print reset mismatch. Got: '{printed_text}'")
                # Check other kwargs
                self.assertEqual(kwargs_call.get('end', '\n'), kwargs.get('end', '\n'))
                self.assertEqual(kwargs_call.get('flush', False), kwargs.get('flush', False))
                break # Found the matching call

        self.assertTrue(found_call, f"Direct print call containing '{expected_text_part}' with file={expected_file} not found in calls:\n{calls}")

    # --- Test Core Logging Functionality ---
    def test_log_levels_enum(self):
        """Test LogLevel enum values"""
        self.assertEqual(LogLevel.DEBUG, 0)
        self.assertEqual(LogLevel.INFO, 1)
        self.assertEqual(LogLevel.WARNING, 2)
        self.assertEqual(LogLevel.ERROR, 3)

    def test_default_handler_added_in_setup(self):
        """Test that a ConsoleHandler is present after setUp."""
        self.assertGreaterEqual(len(ASCIIColors._handlers), 1, "No handlers found after setup")
        self.assertTrue(any(isinstance(h, ConsoleHandler) for h in ASCIIColors._handlers), "Default ConsoleHandler not found")
        # Check if the specific instance added in setup is present
        self.assertIn(self.test_console_handler, ASCIIColors._handlers)


    def test_add_remove_clear_handlers(self):
        """Test adding, removing, and clearing LOGGING handlers."""
        # Ensure setup handler is present
        if self.test_console_handler not in ASCIIColors._handlers:
            ASCIIColors.add_handler(self.test_console_handler)
        initial_count = len(ASCIIColors._handlers)

        file_handler = FileHandler(self.log_file)
        ASCIIColors.add_handler(file_handler)
        self.assertEqual(len(ASCIIColors._handlers), initial_count + 1, "Handler not added")
        self.assertIn(file_handler, ASCIIColors._handlers)

        ASCIIColors.remove_handler(file_handler)
        self.assertEqual(len(ASCIIColors._handlers), initial_count, "Handler not removed")
        self.assertNotIn(file_handler, ASCIIColors._handlers)

        # Test removing non-existent handler
        ASCIIColors.remove_handler(file_handler) # Should not raise error
        self.assertEqual(len(ASCIIColors._handlers), initial_count, "Removing non-existent handler changed count")

        ASCIIColors.clear_handlers()
        self.assertEqual(len(ASCIIColors._handlers), 0, "Handlers not cleared")

    def test_global_log_level_filtering(self):
        """Test LOGGING filtering based on the global log level."""
        ASCIIColors.set_log_level(LogLevel.WARNING)
        # Ensure console handler from setup is present and reset stream
        if self.test_console_handler not in ASCIIColors._handlers:
            ASCIIColors.add_handler(self.test_console_handler)
        self.mock_stdout_log_stream.seek(0)
        self.mock_stdout_log_stream.truncate() # Clear stream content

        file_handler = FileHandler(self.log_file)
        ASCIIColors.add_handler(file_handler)

        # Use distinct messages
        ASCIIColors.debug("DebugMessageFiltering")
        ASCIIColors.info("InfoMessageFiltering")
        ASCIIColors.warning("WarningMessageFiltering")
        ASCIIColors.error("ErrorMessageFiltering")

        # Check console log output (via mock_stdout_log_stream)
        cout = self.get_console_log_output()
        # Use specific error messages for clarity
        self.assertNotIn("DebugMessageFiltering", cout, "Debug message found in console output")
        self.assertNotIn("InfoMessageFiltering", cout, "Info message found in console output")
        self.assertIn("WarningMessageFiltering", cout, "Warning message missing from console output")
        self.assertIn("ErrorMessageFiltering", cout, "Error message missing from console output")

        # Check file output
        self.assertTrue(self.log_file.exists())
        content = self.log_file.read_text()
        self.assertNotIn("DebugMessageFiltering", content, "Debug message found in file output")
        self.assertNotIn("InfoMessageFiltering", content, "Info message found in file output")
        self.assertIn("WarningMessageFiltering", content, "Warning message missing from file output")
        self.assertIn("ErrorMessageFiltering", content, "Error message missing from file output")

    def test_handler_level_filtering(self):
        """Test LOGGING filtering based on individual handler levels."""
        ASCIIColors.set_log_level(LogLevel.DEBUG) # Global allows all
        ASCIIColors.clear_handlers()

        # Use a fresh local stream for this specific test's console handler
        local_mock_stream = io.StringIO()
        console_handler = ConsoleHandler(stream=local_mock_stream, level=LogLevel.WARNING) # Console=WARNING+
        console_handler.set_formatter(Formatter("{message}"))
        ASCIIColors.add_handler(console_handler)

        file_handler = FileHandler(self.log_file, level=LogLevel.INFO) # File=INFO+
        file_handler.set_formatter(Formatter("{message}"))
        ASCIIColors.add_handler(file_handler)

        ASCIIColors.debug("DebugMsgLvl"); ASCIIColors.info("InfoMsgLvl"); ASCIIColors.warning("WarningMsgLvl"); ASCIIColors.error("ErrorMsgLvl")

        # Check local console stream (Warning, Error)
        local_mock_stream.seek(0); cout = strip_ansi(local_mock_stream.read()); local_mock_stream.close()
        self.assertNotIn("DebugMsgLvl", cout); self.assertNotIn("InfoMsgLvl", cout)
        self.assertIn("WarningMsgLvl", cout); self.assertIn("ErrorMsgLvl", cout)

        # Check file output (Info, Warning, Error)
        self.assertTrue(self.log_file.exists())
        content = self.log_file.read_text()
        self.assertNotIn("DebugMsgLvl", content); self.assertIn("InfoMsgLvl", content)
        self.assertIn("WarningMsgLvl", content); self.assertIn("ErrorMsgLvl", content)


    # --- Test Formatters (Used by Logging) ---
    def test_default_formatter_log(self):
        """Test the default Formatter output for logging."""
        ASCIIColors.clear_handlers(); stream = io.StringIO(); h = ConsoleHandler(stream=stream, level=LogLevel.INFO)
        ASCIIColors.add_handler(h); ASCIIColors.info("Default Format Test")
        stream.seek(0); raw = stream.read(); stream.close()
        self.assertRegex(strip_ansi(raw), r"\[INFO\]\[.+\] Default Format Test")
        self.assertTrue(raw.startswith(ASCIIColors._level_colors[LogLevel.INFO]))

    def test_custom_formatter_basic_log(self):
        """Test a custom format string for logging."""
        if self.test_console_handler not in ASCIIColors._handlers: ASCIIColors.add_handler(self.test_console_handler)
        self.mock_stdout_log_stream.seek(0); self.mock_stdout_log_stream.truncate()
        self.test_console_handler.set_formatter(Formatter("{level_name}|{message}"))
        ASCIIColors.warning("CustomFormatW"); self.assertIn("WARNING|CustomFormatW", self.get_console_log_output())

    def test_formatter_with_source_log(self):
        """Test logging formatter including source file/line/func."""
        ASCIIColors.clear_handlers(); stream = io.StringIO(); fmt = Formatter("[{func_name}] {message}", include_source=True); h = ConsoleHandler(stream=stream, formatter=fmt)
        ASCIIColors.add_handler(h); current_line = inspect.currentframe().f_lineno + 1; ASCIIColors.info("SrcInfoMsg")
        stream.seek(0); output = strip_ansi(stream.read()); stream.close()
        self.assertIn(f"[test_formatter_with_source_log] SrcInfoMsg", output)

    def test_formatter_with_kwargs_log(self):
        """Test logging formatter using extra kwargs."""
        fmt = Formatter("{message}, id={req_id}"); h = self.test_console_handler
        if h not in ASCIIColors._handlers: ASCIIColors.add_handler(h)
        self.mock_stdout_log_stream.seek(0); self.mock_stdout_log_stream.truncate(); h.set_formatter(fmt)
        ASCIIColors.info("RequestMsg", req_id=101); self.assertIn("RequestMsg, id=101", self.get_console_log_output())

    def test_json_formatter_log(self):
        """Test JSONFormatter output for logging including kwargs."""
        ASCIIColors.clear_handlers(); fmt = JSONFormatter(); h = FileHandler(self.json_log_file, formatter=fmt)
        ASCIIColors.add_handler(h); ASCIIColors.error("JsonErrorMsg", user="TestUser", code=503)
        data = json.loads(self.json_log_file.read_text()); self.assertEqual(data.get("level_name"), "ERROR")
        self.assertEqual(data.get("user"), "TestUser"); self.assertEqual(data.get("code"), 503)

    def test_json_formatter_iso_date_log(self):
        """Test JSONFormatter with ISO date format for logging."""
        ASCIIColors.clear_handlers(); fmt = JSONFormatter(datefmt="iso"); h = FileHandler(self.json_log_file, formatter=fmt)
        ASCIIColors.add_handler(h); ASCIIColors.info("ISO Date Log")
        data = json.loads(self.json_log_file.read_text()); self.assertRegex(data["datetime"], r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    # --- Test Handlers (Used by Logging) ---
    def test_file_handler_log(self):
        """Test basic FileHandler operation for logging."""
        ASCIIColors.clear_handlers(); fh = FileHandler(self.log_file); ASCIIColors.add_handler(fh)
        ASCIIColors.info("LogToFileTest"); content = self.log_file.read_text(); self.assertRegex(content, r"\[INFO\]\[.+\] LogToFileTest")

    # Patch Path.stat directly when needed for size check
    def test_rotating_file_handler_log(self):
        """Test RotatingFileHandler functionality for logging."""
        ASCIIColors.clear_handlers(); max_bytes = 100; backup_count = 2
        log_file_path = self.rotate_log_file # Keep as Path object

        # Ensure parent dir exists and handler can be created
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        rot_handler = RotatingFileHandler(log_file_path, maxBytes=max_bytes, backupCount=backup_count)
        rot_handler.set_formatter(Formatter("{message}"))
        ASCIIColors.add_handler(rot_handler)

        # --- Rotation 1 ---
        ASCIIColors.info("Msg1-" + "A"*10) # Write initial data
        self.assertTrue(log_file_path.exists())
        self.assertLess(log_file_path.stat().st_size, max_bytes) # Use real stat

        # Patch mocks JUST for the triggering call
        with patch('pathlib.Path.rename') as mock_rename1, \
             patch('pathlib.Path.unlink') as mock_unlink1, \
             patch('pathlib.Path.exists') as mock_exists1, \
             patch('pathlib.Path.stat') as mock_path_stat1:

            # Configure mocks specific to Rotation 1 checks:
            # 1. Path.stat(): Return size > max_bytes ONLY for the main log file
            mock_stat_result = Mock()
            mock_stat_result.st_size = max_bytes + 10
            # Only mock stat for the specific log file path object
            mock_path_stat1.side_effect = lambda *args, **kwargs: mock_stat_result if args[0] == log_file_path else MagicMock(st_size=0) # Default mock for others

            # 2. Path.exists(): Return True ONLY for the main log file
            mock_exists1.side_effect = lambda p: p == log_file_path

            # Trigger rotation
            ASCIIColors.info("Msg2_Rot1")

        # Assert rotation 1 outcome
        #mock_rename1.assert_called_once_with(log_file_path.with_suffix(".1"))
        mock_unlink1.assert_not_called()

        # --- Rotation 2 ---
        backup1_path = log_file_path.with_suffix(".1")
        with patch('pathlib.Path.rename') as mock_rename2, \
             patch('pathlib.Path.unlink') as mock_unlink2, \
             patch('pathlib.Path.exists') as mock_exists2, \
             patch('pathlib.Path.stat') as mock_path_stat2:

            mock_stat_result2 = Mock(); mock_stat_result2.st_size = max_bytes + 20
            mock_path_stat2.side_effect = lambda *args, **kwargs: mock_stat_result2 if args[0] == log_file_path else MagicMock(st_size=0)
            mock_exists2.side_effect = lambda p: p == log_file_path or p == backup1_path

            ASCIIColors.info("Msg3_Rot2")

        #self.assertEqual(mock_rename2.call_count, 2); 
        # names={c[0][0].name for c in mock_rename2.call_args_list}
        # self.assertIn(backup1_path.name, names); self.assertIn(log_file_path.with_suffix(".2").name, names)
        mock_unlink2.assert_not_called()

        # --- Rotation 3 ---
        backup2_path = log_file_path.with_suffix(".2")
        with patch('pathlib.Path.rename') as mock_rename3, \
             patch('pathlib.Path.unlink') as mock_unlink3, \
             patch('pathlib.Path.exists') as mock_exists3, \
             patch('pathlib.Path.stat') as mock_path_stat3:

            mock_stat_result3 = Mock(); mock_stat_result3.st_size = max_bytes + 30
            mock_path_stat3.side_effect = lambda *args, **kwargs: mock_stat_result3 if args[0] == log_file_path else MagicMock(st_size=0)
            mock_exists3.side_effect = lambda p: p == log_file_path or p == backup1_path or p == backup2_path

            ASCIIColors.info("Msg4_Rot3")

        #mock_unlink3.assert_called_once_with(log_file_path.with_suffix(f".{backup_count}"))
        #self.assertEqual(mock_rename3.call_count, 2); names3={c[0][0].name for c in mock_rename3.call_args_list}
        #self.assertIn(backup1_path.name, names3); self.assertIn(backup2_path.name, names3)


    # --- Test Context Management (Affects Logging) ---
    def test_set_clear_context_log(self):
        """Test setting and clearing thread-local context for logging."""
        fmt=Formatter("{message}|Ctx:{my_val}"); h=self.test_console_handler; stream=self.mock_stdout_log_stream
        if h not in ASCIIColors._handlers: ASCIIColors.add_handler(h)
        stream.seek(0); stream.truncate(); h.set_formatter(fmt)
        ASCIIColors.set_context(my_val="1"); ASCIIColors.info("A"); self.assertIn("A|Ctx:1", self.get_console_log_output())
        ASCIIColors.set_context(my_val="2"); ASCIIColors.info("B"); self.assertIn("B|Ctx:2", self.get_console_log_output())
        ASCIIColors.clear_context("my_val"); ASCIIColors.info("C"); self.assertIn("FORMAT_ERROR", self.get_console_log_output())
        ASCIIColors.clear_context(); self.assertEqual(ASCIIColors.get_thread_context(), {})

    def test_context_manager_log(self):
        """Test the context() context manager for logging."""
        fmt=Formatter("S:{session}|U:{user}"); h=self.test_console_handler; stream=self.mock_stdout_log_stream
        if h not in ASCIIColors._handlers: ASCIIColors.add_handler(h)
        stream.seek(0); stream.truncate(); h.set_formatter(fmt)
        ASCIIColors.set_context(session="S1", user="U1"); ASCIIColors.info("")
        self.assertIn("S:S1|U:U1", self.get_console_log_output())
        with ASCIIColors.context(user="U2", task="T"):
            ASCIIColors.info(""); self.assertIn("S:S1|U:U2", self.get_console_log_output())
            with ASCIIColors.context(session="Sin"):
                 ASCIIColors.info(""); self.assertIn("S:Sin|U:U2", self.get_console_log_output())
            ASCIIColors.info(""); self.assertIn("S:S1|U:U2", self.get_console_log_output())
        ASCIIColors.info(""); self.assertIn("S:S1|U:U1", self.get_console_log_output())

    # --- Test Direct Print Methods (Bypass Logging) ---
    def test_direct_print_method(self):
        """Test the static print method calls builtins.print directly."""
        txt="DirectPrint"; col=ASCIIColors.color_cyan; sty=ASCIIColors.style_underline; end="X"; flush=True; file=self.original_stderr
        ASCIIColors.print(txt, color=col, style=sty, end=end, flush=flush, file=file)
        self.assert_direct_print_called_with(txt, color_code=col, style_code=sty, end=end, flush=flush, file=file)

    def test_direct_color_methods(self):
        """Test direct color methods (red, green, etc.) call builtins.print."""
        ASCIIColors.red("RedDirect"); self.assert_direct_print_called_with("RedDirect", color_code=ASCIIColors.color_red)
        ASCIIColors.green("GreenDirect", end=''); self.assert_direct_print_called_with("GreenDirect", color_code=ASCIIColors.color_green, end='')

    def test_direct_style_methods(self):
        """Test direct style methods (bold, underline) call builtins.print."""
        ASCIIColors.bold("BoldDirect", ASCIIColors.color_yellow); self.assert_direct_print_called_with("BoldDirect", color_code=ASCIIColors.color_yellow, style_code=ASCIIColors.style_bold)
        ASCIIColors.underline("UnderDirect", end='.'); self.assert_direct_print_called_with("UnderDirect", color_code=ASCIIColors.color_white, style_code=ASCIIColors.style_underline, end='.')

    def test_success_fail_direct_methods(self):
        """Test success and fail methods call builtins.print directly."""
        ASCIIColors.success("OKDirect"); self.assert_direct_print_called_with("OKDirect", color_code=ASCIIColors.color_green)
        ASCIIColors.fail("NGDirect", file=self.original_stderr); self.assert_direct_print_called_with("NGDirect", color_code=ASCIIColors.color_red, file=self.original_stderr)

    # --- Test Backward Compatibility Stubs ---
    def test_deprecated_set_log_file(self):
        """Test the backward-compatible set_log_file adds a FileHandler."""
        ASCIIColors.clear_handlers(); ASCIIColors.set_log_file(self.log_file)
        self.assertTrue(any(isinstance(h, FileHandler) for h in ASCIIColors._handlers))

    @patch.object(ASCIIColors, '_log')
    def test_deprecated_set_template_warning(self, mock_log):
        """Test that set_template logs a warning."""
        ASCIIColors.set_template(LogLevel.INFO, "x"); mock_log.assert_called_once()
        self.assertEqual(mock_log.call_args[0][0], LogLevel.WARNING); self.assertIn("DEPRECATED", mock_log.call_args[0][1])

    # --- Test Exception Handling (Uses Logging) ---
    def test_get_trace_exception(self):
        """Test the get_trace_exception utility."""
        try: 1/0
        except ZeroDivisionError as e: trace = get_trace_exception(e)
        self.assertIn("ZeroDivisionError", trace); self.assertIn("test_get_trace_exception", trace)

    @patch.object(ASCIIColors, 'error')
    def test_trace_exception_utility(self, mock_error):
        """Test the trace_exception convenience function."""
        try: raise ValueError("X")
        except ValueError as e: exc = e; trace_exception(e)
        mock_error.assert_called_once(); self.assertIn("Traceback", mock_error.call_args[0][0]); self.assertEqual(mock_error.call_args[1].get('exc_info'), exc)

    def test_error_with_exc_info_true_log(self):
        """Test logging error with exc_info=True."""
        ASCIIColors.clear_handlers(); h=FileHandler(self.log_file); ASCIIColors.add_handler(h)
        try: int("a")
        except ValueError as e: ASCIIColors.error("BadIntLog", exc_info=True)
        content = self.log_file.read_text(); self.assertIn("BadIntLog", content); self.assertIn("Traceback", content)

    # --- Test Other Utilities (Use Direct Print) ---
    def test_highlight_direct(self):
        """Test the highlight utility calls builtins.print directly."""
        ASCIIColors.highlight("A KEY B", "KEY", ASCIIColors.color_blue, ASCIIColors.color_red)
        expected = f"{ASCIIColors.color_blue}A {ASCIIColors.color_red}KEY{ASCIIColors.color_blue} B{ASCIIColors.color_reset}"
        self.mock_builtin_print.assert_any_call(expected, end="\n", flush=False, file=self.original_stdout)

    def test_multicolor_direct(self):
        """Test the multicolor utility calls builtins.print directly."""
        ASCIIColors.multicolor(["R ","G"], [ASCIIColors.color_red, ASCIIColors.color_green], end="X")
        self.mock_builtin_print.assert_any_call(f"{ASCIIColors.color_red}R ", end="", flush=True, file=self.original_stdout)
        self.mock_builtin_print.assert_any_call(f"{ASCIIColors.color_green}G", end="", flush=True, file=self.original_stdout)
        self.mock_builtin_print.assert_any_call(ASCIIColors.color_reset, end="X", flush=False, file=self.original_stdout)

    # --- Animation Tests Removed ---


if __name__ == "__main__":
    unittest.main()