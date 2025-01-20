# tests/test_ascii_colors.py
import tempfile
import unittest
from pathlib import Path

from ascii_colors import ASCIIColors, LogLevel


class TestASCIIColors(unittest.TestCase):
    """Test suite for ASCIIColors class"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "test.log"
        ASCIIColors.set_log_level(LogLevel.DEBUG)

    def tearDown(self):
        """Clean up test environment"""
        if self.log_file.exists():
            self.log_file.unlink()

    def test_log_levels(self):
        """Test log level functionality"""
        self.assertEqual(LogLevel.DEBUG, 0)
        self.assertEqual(LogLevel.INFO, 1)
        self.assertEqual(LogLevel.WARNING, 2)
        self.assertEqual(LogLevel.ERROR, 3)

    def test_template_setting(self):
        """Test template customization"""
        test_template = "TEST [{datetime}] - {message}"
        ASCIIColors.set_template(LogLevel.INFO, test_template)
        self.assertEqual(ASCIIColors._templates[LogLevel.INFO], test_template)

    def test_invalid_template(self):
        """Test invalid template handling"""
        with self.assertRaises(ValueError):
            ASCIIColors.set_template(LogLevel.INFO, "Invalid template {invalid}")

    def test_file_logging(self):
        """Test file logging functionality"""
        ASCIIColors.set_log_file(self.log_file)
        test_message = "Test log message"
        ASCIIColors.info(test_message)

        self.assertTrue(self.log_file.exists())
        content = self.log_file.read_text()
        self.assertIn(test_message, content)

    def test_log_level_filtering(self):
        """Test log level filtering"""
        ASCIIColors.set_log_level(LogLevel.WARNING)
        ASCIIColors.set_log_file(self.log_file)

        debug_msg = "Debug message"
        info_msg = "Info message"
        warning_msg = "Warning message"

        ASCIIColors.debug(debug_msg)
        ASCIIColors.info(info_msg)
        ASCIIColors.warning(warning_msg)

        content = self.log_file.read_text()
        self.assertNotIn(debug_msg, content)
        self.assertNotIn(info_msg, content)
        self.assertIn(warning_msg, content)
