# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# 2026-01-14
- feat(logging): change default global level to INFO# [Unreleased]

- chore(release): bump version to 0.11.6 and update .gitignore

## [2026-03-01 15:01]

- feat: expose context management methods at module level

## [2026-02-23 02:38]

- refactor: improve logging thread safety and Rich component rendering

## [2026-02-18 02:58]

- feat(rich): add Live display refresh rate and Panel text stripping

## [2026-02-16 02:08]

- feat(logging): add logging compatibility layer with rich terminal support

## [2026-02-13 15:38]

- chore(release): bump version to 0.11.11 with docs cleanup and threading fix

## [2026-02-13 15:38]

- docs: remove usage guide and restructure documentation

## [2026-02-13 14:35]

- feat(rich): add Rich-style panel rendering with multi-line support

## [2026-02-13 13:58]

- chore: bump version to 0.11.10 and clean up formatting

## [2026-02-12 08:37]

- refactor!: rename compatibility modules and remove _compat suffix

## [2026-02-10 13:48]

- refactor: Simplify library structure and overhaul documentation

## [0.11.1] - 2025-05-02

### Added
*   **`Menu.add_choices()`:** Added a convenience method to the `Menu` class to add multiple choice items from a list of (text, value) tuples, useful for select modes.

## [0.11.0] - 2025-04-28

*(No unique public changes noted compared to previous documented versions)*

### Added
*   **`ASCIIColors.confirm()`:** Added a static utility method to ask yes/no questions interactively, handling defaults and input validation. Uses direct printing.
*   **`ASCIIColors.prompt()`:** Added a static utility method to get text input from the user with a styled prompt. Uses direct printing.
*   Added tests for `confirm` and `prompt` methods.
*   Added documentation for `confirm` and `prompt` to README, usage guide, and API reference.

### Changed
*   Now `add_action` can also receive an optional `item_color` to set the item color in the menu.

## [0.10.0] - 2025-04-28

### Added
*   **Interactive `Menu` Class:** Introduced `ascii_colors.Menu` for creating interactive, styled command-line menus featuring:
    *   **Arrow Key Navigation:** Use Up/Down arrows to navigate items.
    *   **Enter Selection:** Select items using the Enter key.
    *   Automatic 'Back'/'Quit' options.
    *   Customizable styling for title, items, selection, and prompt using `ASCIIColors`.
    *   Option to hide the cursor during interaction.
    *   Error handling for actions.
*   Added `Menu` demonstration to the `if __name__ == "__main__":` block in `__init__.py`.
*   Added `Menu` tests to `tests/test_ascii_colors.py` (mocking terminal input).
*   Added `Menu` documentation to `usage.rst` and `api.rst`.
*   Added internal `_get_key()` helper for cross-platform single-character input reading.
*   Added necessary imports (`platform`, `msvcrt`, `termios`, `tty`).

### Changed
*   **Menu Input:** Replaced previous number/letter key selection in `Menu` with arrow key navigation and Enter selection. Removed `key` parameter from `add_action` and `add_submenu`.

### Fixed
*   Improved cleanup logic in `if __name__ == "__main__"` block to attempt removal of specific test files.

## [0.9.0] - 2025-04-27  <!-- Corrected date typo -->

### Added
*   **`ProgressBar`:** Introduced a thread-safe, customizable progress bar utility (`ascii_colors.ProgressBar`) mimicking the `tqdm` interface (iterable wrapping, context manager). Supports ANSI colors, styles, and different bar formats using direct terminal printing.
*   Added `shutil` usage for terminal size detection in `ProgressBar`.

### Changed
*   Updated main module docstring and README to include `ProgressBar`.
*   Added `ProgressBar` demonstration to the `if __name__ == "__main__":` block in `__init__.py`.
*   Expanded type hints in `__init__.py` for `ProgressBar`.

## [0.8.1] - 2025-04-25

### Changed
*   **Documentation Overhaul:**
    *   Rewrote and significantly expanded the Sphinx documentation.
    *   Added a clear "Core Concepts: Direct Print vs. Logging" section.
    *   Improved Quick Start guide, emphasizing the `import ascii_colors as logging` pattern.
    *   Greatly expanded the Usage Guide with examples for `basicConfig`, manual setup (multiple handlers, JSON, rotation), context management, and utilities.
    *   Added a comprehensive list of color/style constants to the Usage Guide.
    *   Updated API Reference (`api.rst`) for completeness and clarity.
    *   Configured Sphinx (`conf.py`) to use the Furo theme and read project metadata from `pyproject.toml`.
    *   Updated `README.md` to reflect documentation structure, improved examples, and added core concept explanation.
*   **Code Refinements:**
    *   Minor improvements to docstrings for clarity and consistency.
    *   Reviewed `basicConfig`, formatter, and handler logic to ensure alignment with documentation. (No significant behavior changes from 0.8.0).
*   **Project Files:**
    *   Updated `pyproject.toml` version and added `toml` to dev dependencies. Added documentation URL.
    *   Updated `README.md` with new documentation link and content.

## [0.8.0] - 2025-04-24


### Added

*   **Logging Compatibility Layer:** Introduced functions `getLogger()`, `basicConfig()`, level constants (`DEBUG`, `INFO`, etc.), `StreamHandler` alias, and `handlers` namespace to mimic the standard Python `logging` module interface.
*   Added `critical` logging level and corresponding `ASCIIColors.critical()` / `logger.critical()` methods.
*   Added `logger.exception()` method for convenience logging errors with tracebacks.
*   Added `getLevelName()` utility function.
*   Implemented `close()` method for `Handler`, `ConsoleHandler`, `FileHandler`, `RotatingFileHandler` for explicit resource cleanup.
*   Added many more color and style constants (backgrounds, dim, italic, strikethrough, etc.) to `ASCIIColors`.
*   Added direct print methods for background colors (`bg_red`, etc.) and styles (`dim`, `italic`, etc.).
*   Added `flush()` method to `FileHandler`.

### Changed

*   **Core Logging Refactor:** `ASCIIColors._log` now handles `%args` formatting and accepts `logger_name` for better compatibility and context.
*   **Formatter Enhancements:**
    *   `Formatter` now robustly supports both `%` and `{` style format strings.
    *   `Formatter` recognizes and populates standard `logging` record attributes (e.g., `levelname`, `name`, `pathname`, `lineno`, `funcName`, `asctime`).
    *   Default `Formatter` style is now `%` (was previously unspecified, implicitly `{`).
    *   Default format string when `fmt=None` is now `%(levelname)s:%(name)s:%(message)s` (matches logging more closely).
    *   `Formatter.format` logic improved for handling `{}` style and defaults.
*   **Handler Initialization:** Handlers no longer create a default `Formatter` instance if `formatter=None` is passed during initialization. Defaults are applied during `handle()` if needed.
*   **`basicConfig` Behavior:**
    *   Now manages global state (`ASCIIColors._handlers`, `_global_level`, `_basicConfig_called`) correctly.
    *   Handles `force=True` correctly, including closing old handlers.
    *   Assigns levels correctly to implicitly created handlers.
    *   Assigns the specified formatter correctly to handlers passed via the `handlers` list only if they don't have one.
*   **Default Global Level:** Changed default global log level (`ASCIIColors._global_level`) from `INFO` to `WARNING` to align with standard `logging`.
*   **Default Handler:** Auto-created default handler (if no handlers are configured and `basicConfig` not called) now defaults to `stderr` and uses `%` style formatter.
*   **`RotatingFileHandler` Logic:** Improved rotation logic (`do_rollover`) to explicitly flush and close the stream *before* filesystem operations (rename/unlink) for better reliability, especially on Windows. Changed `emit` to check rotation *after* writing.
*   **Direct Print Methods:** Clarified that `ASCIIColors.red`, `print`, etc. **bypass** the logging system entirely and print directly to the terminal. They do *not* log messages.
*   **Source Info Detection:** Improved robustness and added depth limit to stack walking for `include_source=True`.

### Fixed

*   Fixed potential deadlock in `basicConfig(force=True)` due to nested lock acquisition.
*   Fixed `NameError: name 'ascii_colors' is not defined` within `basicConfig`.
*   Fixed numerous test failures related to incorrect formatting (especially `{}` style), empty log output, incorrect level/formatter assignment in `basicConfig`, and file rotation failures.
*   Fixed `TypeError` in tests due to incorrect keyword argument (`format` instead of `formatter`).
*   Fixed incorrect assertion in tests for `logger.exception()` regarding `exc_info`.
*   Ensured `FileHandler` and subclasses correctly handle `formatter=None`.

### Deprecated

*   `ASCIIColors.set_template()` is deprecated. Use `setFormatter()` on specific handler instances instead.

## [0.7.6] - Previous Version Date *(Example)*

Standard coloring and simple logging. *(Implied baseline state before 0.8.0)*