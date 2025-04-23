# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

Standard coloring andsimple logging