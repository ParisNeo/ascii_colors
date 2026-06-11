# -*- coding: utf-8 -*-
"""
Unit tests for FolderRouterHandler.
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

# Ensure ascii_colors is importable from source
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ascii_colors.handlers import FolderRouterHandler, RotatingFileHandler
from ascii_colors.constants import DEBUG, INFO, WARNING, ERROR
from ascii_colors.formatters import Formatter
from ascii_colors.core import ASCIIColors


class TestFolderRouterHandler:
    """Tests for the FolderRouterHandler class."""

    def setup_method(self):
        """Create a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory and handlers."""
        ASCIIColors.clear_handlers()
        ASCIIColors._basicConfig_called = False
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_folder(self):
        """Test that handler creates the log folder if it doesn't exist."""
        folder = Path(self.temp_dir) / "nonexistent" / "nested"
        assert not folder.exists()
        handler = FolderRouterHandler(folder)
        assert folder.exists()
        assert folder.is_dir()
        handler.close()

    def test_invalid_mode_raises_value_error(self):
        """Test that an invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="mode must be 'rolling', 'overwrite', or 'timestamp'"):
            FolderRouterHandler(self.temp_dir, mode="invalid")

    def test_overwrite_mode_truncates_file(self):
        """Test overwrite mode creates fresh files each run."""
        handler = FolderRouterHandler(self.temp_dir, mode="overwrite")
        ts = datetime.now()
        handler.handle(INFO, "first run", ts, None, logger_name="app")
        handler.close()

        log_file = Path(self.temp_dir) / "app.log"
        assert log_file.exists()
        assert "first run" in log_file.read_text()

        # Second handler should truncate
        handler2 = FolderRouterHandler(self.temp_dir, mode="overwrite")
        handler2.handle(INFO, "second run", ts, None, logger_name="app")
        handler2.close()

        content = log_file.read_text()
        assert "second run" in content
        assert "first run" not in content

    def test_timestamp_mode_creates_dated_file(self):
        """Test timestamp mode includes run timestamp in filename."""
        handler = FolderRouterHandler(self.temp_dir, mode="timestamp")
        ts = datetime.now()
        handler.handle(INFO, "ts message", ts, None, logger_name="service")
        expected_name = f"service_{handler._run_timestamp}.log"
        handler.close()

        expected_file = Path(self.temp_dir) / expected_name
        assert expected_file.exists()
        assert "ts message" in expected_file.read_text()

    def test_rolling_mode_uses_rotating_file_handler(self):
        """Test rolling mode creates RotatingFileHandler and rotates."""
        handler = FolderRouterHandler(
            self.temp_dir,
            mode="rolling",
            maxBytes=50,
            backupCount=2
        )
        ts = datetime.now()
        # Write enough data to trigger rotation
        for i in range(10):
            handler.handle(INFO, f"line {i}" + "x" * 20, ts, None, logger_name="roll")
        handler.close()

        log_file = Path(self.temp_dir) / "roll.log"
        assert log_file.exists()

        backups = list(Path(self.temp_dir).glob("roll.log.*"))
        assert len(backups) > 0

    def test_routes_by_logger_name(self):
        """Test that different logger names route to different files."""
        handler = FolderRouterHandler(self.temp_dir, mode="overwrite")
        ts = datetime.now()
        handler.handle(INFO, "ui event", ts, None, logger_name="QwidgetUI")
        handler.handle(INFO, "api call", ts, None, logger_name="api")
        handler.handle(DEBUG, "db query", ts, None, logger_name="database")
        handler.close()

        ui_file = Path(self.temp_dir) / "QwidgetUI.log"
        api_file = Path(self.temp_dir) / "api.log"
        db_file = Path(self.temp_dir) / "database.log"

        assert ui_file.exists()
        assert api_file.exists()
        assert db_file.exists()

        assert "ui event" in ui_file.read_text()
        assert "api call" in api_file.read_text()
        assert "db query" in db_file.read_text()

        # Ensure separation
        assert "api call" not in ui_file.read_text()
        assert "ui event" not in api_file.read_text()

    def test_sanitizes_logger_name(self):
        """Test that special characters in logger names are sanitized."""
        handler = FolderRouterHandler(self.temp_dir, mode="overwrite")
        ts = datetime.now()
        handler.handle(INFO, "msg", ts, None, logger_name="my/logger@home!")
        handler.close()

        files = list(Path(self.temp_dir).glob("*.log"))
        assert len(files) == 1
        assert files[0].name == "my_logger_home_.log"

    def test_formatter_applied(self):
        """Test that the formatter is used when writing logs."""
        formatter = Formatter(fmt="[%(levelname)s] %(name)s: %(message)s")
        handler = FolderRouterHandler(
            self.temp_dir,
            mode="overwrite",
            formatter=formatter
        )
        ts = datetime.now()
        handler.handle(WARNING, "formatted warning", ts, None, logger_name="fmt")
        handler.close()

        log_file = Path(self.temp_dir) / "fmt.log"
        content = log_file.read_text()
        assert "[WARNING]" in content
        assert "fmt: formatted warning" in content

    def test_close_closes_all_sub_handlers(self):
        """Test that close() closes all internally created file handlers."""
        handler = FolderRouterHandler(self.temp_dir, mode="overwrite")
        ts = datetime.now()
        handler.handle(INFO, "msg1", ts, None, logger_name="a")
        handler.handle(INFO, "msg2", ts, None, logger_name="b")

        assert len(handler._file_handlers) == 2
        handler.close()

        assert handler.closed
        for h in handler._file_handlers.values():
            assert h.closed

    def test_flush_does_not_raise(self):
        """Test that flush() works without errors."""
        handler = FolderRouterHandler(self.temp_dir, mode="overwrite")
        ts = datetime.now()
        handler.handle(INFO, "flushable", ts, None, logger_name="flush")
        handler.flush()
        handler.close()

        log_file = Path(self.temp_dir) / "flush.log"
        assert "flushable" in log_file.read_text()

    def test_ignores_logs_below_level(self):
        """Test that logs below handler level are ignored."""
        handler = FolderRouterHandler(
            self.temp_dir,
            mode="overwrite",
            level=WARNING
        )
        ts = datetime.now()
        handler.handle(INFO, "ignored", ts, None, logger_name="level_test")
        handler.handle(ERROR, "captured", ts, None, logger_name="level_test")
        handler.close()

        log_file = Path(self.temp_dir) / "level_test.log"
        assert "captured" in log_file.read_text()
        assert "ignored" not in log_file.read_text()


class TestBasicConfigFolderRouting:
    """Tests for basicConfig integration with log_folder parameters."""

    def setup_method(self):
        """Prepare isolated environment."""
        self.temp_dir = tempfile.mkdtemp()
        ASCIIColors.clear_handlers()
        ASCIIColors._basicConfig_called = False
        ASCIIColors.set_log_level(INFO)

    def teardown_method(self):
        """Clean up environment."""
        ASCIIColors.clear_handlers()
        ASCIIColors._basicConfig_called = False
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basicConfig_rolling_mode(self):
        """Test basicConfig with log_folder and rolling mode."""
        import ascii_colors as logging
        logging.basicConfig(
            log_folder=self.temp_dir,
            log_folder_mode="rolling",
            log_folder_maxBytes=512,
            log_folder_backupCount=1,
            force=True
        )

        logger = logging.getLogger("basic_roll")
        logger.info("basic rolling")

        logging.shutdown()

        log_file = Path(self.temp_dir) / "basic_roll.log"
        assert log_file.exists()
        assert "basic rolling" in log_file.read_text()

    def test_basicConfig_overwrite_mode(self):
        """Test basicConfig with log_folder and overwrite mode."""
        import ascii_colors as logging
        logging.basicConfig(
            log_folder=self.temp_dir,
            log_folder_mode="overwrite",
            force=True
        )

        logger = logging.getLogger("basic_over")
        logger.info("basic overwrite")

        logging.shutdown()

        log_file = Path(self.temp_dir) / "basic_over.log"
        assert log_file.exists()
        assert "basic overwrite" in log_file.read_text()

    def test_basicConfig_timestamp_mode(self):
        """Test basicConfig with log_folder and timestamp mode."""
        import ascii_colors as logging
        logging.basicConfig(
            log_folder=self.temp_dir,
            log_folder_mode="timestamp",
            force=True
        )

        logger = logging.getLogger("basic_ts")
        logger.info("basic timestamp")

        logging.shutdown()

        files = list(Path(self.temp_dir).glob("basic_ts_*.log"))
        assert len(files) == 1
        assert "basic timestamp" in files[0].read_text()

    def test_basicConfig_log_folder_replaces_console(self):
        """Test that basicConfig with log_folder does not add console handler."""
        import ascii_colors as logging
        logging.basicConfig(
            log_folder=self.temp_dir,
            log_folder_mode="overwrite",
            force=True
        )

        # Should only have the FolderRouterHandler
        assert len(ASCIIColors._handlers) == 1
        assert isinstance(ASCIIColors._handlers[0], FolderRouterHandler)

        logging.shutdown()

    def test_basicConfig_rolling_propagates_maxBytes(self):
        """Test that log_folder_maxBytes is correctly propagated to the RotatingFileHandler.

        This ensures the rolling parameter from basicConfig is not silently
        dropped by the FolderRouterHandler wrapper.
        """
        import ascii_colors as logging
        logging.basicConfig(
            log_folder=self.temp_dir,
            log_folder_mode="rolling",
            log_folder_maxBytes=2048,
            log_folder_backupCount=4,
            force=True
        )

        # Trigger creation of the per-logger RotatingFileHandler
        logger = logging.getLogger("propagate_test")
        logger.info("trigger handler creation")

        # Inspect the wrapper
        folder_handler = ASCIIColors._handlers[0]
        assert isinstance(folder_handler, FolderRouterHandler)

        # Inspect the inner RotatingFileHandler
        rolling_handler = folder_handler._file_handlers["propagate_test"]
        assert isinstance(rolling_handler, RotatingFileHandler)
        assert rolling_handler.maxBytes == 2048
        assert rolling_handler.backupCount == 4

        logging.shutdown()

    def test_basicConfig_rolling_propagates_backupCount(self):
        """Test that log_folder_backupCount is correctly propagated to the RotatingFileHandler."""
        import ascii_colors as logging
        logging.basicConfig(
            log_folder=self.temp_dir,
            log_folder_mode="rolling",
            log_folder_maxBytes=512,
            log_folder_backupCount=7,
            force=True
        )

        logger = logging.getLogger("backup_count_test")
        logger.info("trigger")

        folder_handler = ASCIIColors._handlers[0]
        rolling_handler = folder_handler._file_handlers["backup_count_test"]
        assert isinstance(rolling_handler, RotatingFileHandler)
        assert rolling_handler.backupCount == 7
        assert rolling_handler.maxBytes == 512

        logging.shutdown()

    def test_basicConfig_rolling_rotates_when_size_exceeded(self):
        """Test that file rotation actually occurs when the log exceeds log_folder_maxBytes.

        With a tiny maxBytes, writing a handful of messages should produce
        at least one backup file, demonstrating that rotation is functional
        end-to-end through basicConfig -> FolderRouterHandler -> RotatingFileHandler.
        """
        import ascii_colors as logging
        logging.basicConfig(
            log_folder=self.temp_dir,
            log_folder_mode="rolling",
            format="%(message)s",  # Minimal format to make size predictable
            log_folder_maxBytes=100,  # Small to force rotation
            log_folder_backupCount=3,
            force=True
        )

        logger = logging.getLogger("rotation_test")
        # Each message: "message XXXXX" = 13 chars + newline = 14 bytes
        # So ~7 messages = 98 bytes, 8th message triggers rotation (98+14=112 >= 100)
        for i in range(30):
            logger.info(f"message {i:05d}")

        logging.shutdown()

        # Current file exists and contains the most recent message
        log_file = Path(self.temp_dir) / "rotation_test.log"
        assert log_file.exists()
        content = log_file.read_text()
        assert "message 00029" in content

        # At least one backup file should have been created
        backup_files = list(Path(self.temp_dir).glob("rotation_test.log.*"))
        assert len(backup_files) > 0, "Expected at least one backup file from rotation"

    def test_basicConfig_rolling_respects_backupCount_limit(self):
        """Test that the number of backup files is bounded by log_folder_backupCount.

        Writes many small messages to force repeated rotations, then asserts
        that no more than backupCount backup files exist (i.e. oldest ones
        were correctly deleted during rollover).
        """
        import ascii_colors as logging
        logging.basicConfig(
            log_folder=self.temp_dir,
            log_folder_mode="rolling",
            format="%(message)s",
            log_folder_maxBytes=50,  # Very small to force many rotations
            log_folder_backupCount=2,  # Keep only 2 backups
            force=True
        )

        logger = logging.getLogger("limit_test")
        # Write many messages to force multiple rotations.
        # Each message: "xXXXXy" = 7 chars + newline = 8 bytes.
        for i in range(50):
            logger.info(f"x{i:04d}y")

        logging.shutdown()

        # Rotation must have happened for this test to be meaningful
        backup_files = list(Path(self.temp_dir).glob("limit_test.log.*"))
        assert len(backup_files) > 0, "Expected rotation to have produced backup files"

        # With backupCount=2, we should have at most .1 and .2
        assert len(backup_files) <= 2, (
            f"Expected at most 2 backup files, found {len(backup_files)}: "
            f"{[f.name for f in backup_files]}"
        )

        # Verify backup file numbering is within the allowed range
        for f in backup_files:
            suffix = f.name.split(".")[-1]
            assert suffix.isdigit() and int(suffix) <= 2, (
                f"Unexpected backup file name: {f.name}"
            )

    def test_basicConfig_rolling_backup_preserves_content(self):
        """Test that rotated backup files contain log data (not just empty stubs).

        Verifies the full pipeline: messages are written, rotation happens,
        and the rotated file retains its content for later inspection
        (which is the whole point of the VSCoder debugging workflow).
        """
        import ascii_colors as logging
        logging.basicConfig(
            log_folder=self.temp_dir,
            log_folder_mode="rolling",
            format="[%(message)s]",
            log_folder_maxBytes=80,
            log_folder_backupCount=3,
            force=True
        )

        logger = logging.getLogger("content_test")
        # Each message: "[msg XXXX extra]" = 17 chars + newline = 18 bytes
        # 80 / 18 is approximately 4-5 messages per file
        for i in range(20):
            logger.info(f"msg {i:04d} extra")

        logging.shutdown()

        # Check that backup files exist and contain message content
        backup_files = sorted(Path(self.temp_dir).glob("content_test.log.*"))
        assert len(backup_files) > 0, "Expected at least one backup file"

        # Every backup file should have some content (not just be a renamed empty file)
        for f in backup_files:
            content = f.read_text()
            assert "msg " in content, (
                f"Backup file {f.name} is missing expected message content: {content!r}"
            )
