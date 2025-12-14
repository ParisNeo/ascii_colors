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

    def assert_direct_print_called_with(self, expected_text_part: str, color_code: str = None, style_code: str = "", **kwargs):
        """Asserts that builtins.print (mocked) was called with expected args."""
        found_call = False; time.sleep(0.01); calls = self.mock_builtin_print.call_args_list
        expected_file = kwargs.get('file', self.original_stdout)
        expected_end = kwargs.get('end', '\n')
        
        for call in calls:
            args, kwargs_call = call
            if not args: continue
            printed_text = args[0]
            if not isinstance(printed_text, str): continue
            stripped_printed = strip_ansi(printed_text).lower().strip()
            
            if expected_text_part.lower() in stripped_printed and \
               kwargs_call.get('file', self.original_stdout) == expected_file:
                found_call = True
                expected_start = style_code + (color_code if color_code else "")
                
                # Check formatting
                # Note: ASCIIColors.print constructs the string as: prefix + text + reset + end
                # BUT when calling print(..., end="", ...), the 'end' char is embedded in the string passed to print?
                # No, ASCIIColors.print adds 'end' to the string it constructs: output = ... + end
                # Then calls print(output, end="", ...)
                
                # Check start
                self.assertTrue(printed_text.lstrip('\r').startswith(expected_start), f"Direct print start mismatch. Expected prefix: '{expected_start}', Got: '{printed_text}'")
                
                # Check end: Should end with Reset Code + Expected End Char
                full_expected_suffix = ASCIIColors.color_reset + expected_end
                self.assertTrue(printed_text.endswith(full_expected_suffix), f"Direct print suffix mismatch. Expected endswith: '{full_expected_suffix!r}', Got: '{printed_text!r}'")
                
                # Check kwargs passed to builtin print
                self.assertEqual(kwargs_call.get('end', '\n'), "") # ASCIIColors.print forces end="" in builtin call
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
        """Test the static print method calls builtins.print directly."""
        txt="DirectPrint"; col=ASCIIColors.color_cyan; sty=ASCIIColors.style_underline; end="X"; flush=True; file=self.original_stderr
        ASCIIColors.print(txt, color=col, style=sty, end=end, flush=flush, file=file)
        self.assert_direct_print_called_with(txt, color_code=col, style_code=sty, end=end, flush=flush, file=file)

    def test_direct_color_methods(self):
        """Test direct color methods (red, green, etc.) call builtins.print."""
        ASCIIColors.red("RedDirect")
        self.assert_direct_print_called_with("RedDirect", color_code=ASCIIColors.color_red)
        self.mock_builtin_print.reset_mock()
        ASCIIColors.green("GreenDirect", end='')
        self.assert_direct_print_called_with("GreenDirect", color_code=ASCIIColors.color_green, end='')

    def test_composition_of_effects(self):
        """Test composition of effects (nesting calls)."""
        # When nesting with emit=False for inner, we build a complex string
        inner_text = "NestedText"
        # Inner: Bold, no emit, no newline to keep it simple
        bolded = ASCIIColors.bold(inner_text, emit=False, end="")
        
        # Outer: Magenta, emit=True
        ASCIIColors.magenta(bolded)
        
        # Verify the print call
        # The printed string should start with magenta code
        # And contain the bold code + text
        # And end with resets
        
        # Check calls manually to ensure composition structure
        found = False
        for call in self.mock_builtin_print.call_args_list:
            args, _ = call
            if args and isinstance(args[0], str):
                printed = args[0]
                # Check for structure: MAGENTA + BOLD + text
                if (printed.startswith(ASCIIColors.color_magenta) and 
                    ASCIIColors.style_bold in printed and 
                    inner_text in printed):
                    found = True
                    break
        self.assertTrue(found, "Composition of Magenta(Bold(...)) not found in print calls")

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
        mock_core_log.assert_called_with(LogLevel.DEBUG, "Debug msg %s", ("arg1",), logger_name="adapter_test", extra_key="dv")
        
        mock_core_log.reset_mock()
        try:
            raise ValueError("Test Exc")
        except ValueError:
             logger.exception("Exception msg %s", "oops", detail="ze")

        self.assertTrue(mock_core_log.called)
        call_args, call_kwargs = mock_core_log.call_args
        self.assertEqual(call_args[0], LogLevel.ERROR)
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
        self.assertEqual(handler.level, LogLevel.WARNING)

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

    # --- Test ProgressBar ---
    
    class TestProgressBar(unittest.TestCase):
        def setUp(self):
            patcher_print = patch("ascii_colors.ASCIIColors.print")
            self.mock_ascii_print = patcher_print.start()
            self.addCleanup(patcher_print.stop)
            
            patcher_time = patch("time.time")
            self.mock_time = patcher_time.start()
            self.mock_time.return_value = 1000.0
            self.addCleanup(patcher_time.stop)
            
            patcher_tsize = patch("shutil.get_terminal_size")
            self.mock_tsize = patcher_tsize.start()
            self.mock_tsize.return_value = os.terminal_size((80, 24))
            self.addCleanup(patcher_tsize.stop)

        def _get_last_print_args(self):
            if not self.mock_ascii_print.called: return None
            return self.mock_ascii_print.call_args[0][0]

        def test_iterable_wrapper(self):
            """Test ProgressBar wrapping an iterable."""
            data = [1, 2, 3, 4, 5]
            pbar = ProgressBar(data, desc="Iter Test", mininterval=0)
            list(pbar) # Consume iterator
            
            self.assertEqual(self.mock_ascii_print.call_count, len(data) + 2) # Init + 5 updates + Final
            final_text = self._get_last_print_args()
            self.assertIn("Iter Test: 100%", strip_ansi(final_text))

        def test_styling_options(self):
            """Test different styling parameters."""
            with ProgressBar(total=10, desc="Style", progress_char=">", empty_char="-", bar_style="fill", mininterval=0) as pbar:
                pbar.update(5)

            render_text = self._get_last_print_args()
            bar_match = re.search(r"\|([^|]+)\|", strip_ansi(render_text))
            self.assertTrue(bar_match)
            bar_content = bar_match.group(1).strip()
            self.assertTrue(">" in bar_content)
            self.assertTrue("-" in bar_content)

        def test_thread_safety(self):
            total = 100
            num_threads = 4
            pbar = ProgressBar(total=total, desc="Thread", mininterval=0.001)
            
            def worker():
                for _ in range(total // num_threads):
                    pbar.update(1)
            
            threads = [threading.Thread(target=worker) for _ in range(num_threads)]
            for t in threads: t.start()
            for t in threads: t.join()
            pbar.close()
            
            self.assertEqual(pbar.n, total)
            self.assertGreater(self.mock_ascii_print.call_count, 1)

    # --- Test Menu ---

    class TestMenu(unittest.TestCase):
        def setUp(self):
            self.mock_print = patch("ascii_colors.ASCIIColors.print").start()
            self.addCleanup(patch.stopall)
            self.mock_get_key = patch("ascii_colors._get_key").start()
            patch("ascii_colors.Menu._clear_screen").start()
            patch("ascii_colors.Menu._set_cursor_visibility").start()
            
            self.mock_action = Mock()

        def _find_last_menu_print_state(self):
            lines = []
            for call in self.mock_print.call_args_list:
                arg = call[0][0]
                if isinstance(arg, str):
                    lines.append(strip_ansi(arg))
            return lines

        def test_menu_creation_and_add_items(self):
            m = Menu("Test")
            sub = Menu("Sub")
            m.add_action("Action", self.mock_action)
            m.add_submenu("Sub", sub)
            
            self.assertEqual(len(m.items), 2)
            self.assertEqual(m.items[0].text, "Action")
            self.assertEqual(m.items[0].item_type, 'action')
            self.assertEqual(m.items[1].item_type, 'submenu')

        def test_menu_run_display_highlight(self):
            m = Menu("Display", clear_screen_on_run=False)
            m.add_action("Item 1", lambda: None)
            m.add_action("Item 2", lambda: None)
            
            self.mock_get_key.side_effect = ['DOWN', 'QUIT']
            m.run()
            
            lines = self._find_last_menu_print_state()
            # Depending on how many times print called, verify content
            # Just verify that items are printed
            self.assertTrue(any("Item 1" in l for l in lines))
            self.assertTrue(any("Item 2" in l for l in lines))

        def test_menu_run_select_action_enter(self):
            m = Menu("Action", clear_screen_on_run=False)
            m.add_action("Do", self.mock_action)
            
            self.mock_get_key.side_effect = ['ENTER', 'ENTER', 'QUIT'] # Enter (do), Enter (confirm), Quit
            m.run()
            self.mock_action.assert_called_once()

if __name__ == "__main__":
    unittest.main()
