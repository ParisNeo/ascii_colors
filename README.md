# ASCIIColors v0.6.0

ASCIIColors is a Python library designed for rich terminal output. It provides an easy way to add color and style to text, alongside a flexible and powerful logging system that surpasses basic needs while remaining intuitive. It features multiple handlers (console, file, rotating files), customizable formatters (including JSON), thread-local context management, and utility functions for enhanced console applications.

## Table of Contents

- [Installation](#installation)
- [Quick Start: Logging](#quick-start-logging)
- [Basic Color Printing (Legacy)](#basic-color-printing-legacy)
- [Core Logging Concepts](#core-logging-concepts)
  - [Log Levels](#log-levels)
  - [Handlers](#handlers)
  - [Formatters](#formatters)
  - [Context Management](#context-management)
- [Advanced Usage Examples](#advanced-usage-examples)
  - [Multiple Handlers (Console & File)](#multiple-handlers-console--file)
  - [Rotating Log Files](#rotating-log-files)
  - [JSON Logging](#json-logging)
  - [Custom Formatting with Context](#custom-formatting-with-context)
- [Utility Functions](#utility-functions)
  - [Exception Tracing](#exception-tracing)
  - [Multicolor Text](#multicolor-text)
  - [Highlighting Text](#highlighting-text)
  - [Execution with Animation](#execution-with-animation)
- [Available Colors and Styles](#available-colors-and-styles)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)
- [Changelog](#changelog)

## Installation

Install ASCIIColors via `pip` from the Python Package Index (PyPI):

```bash
pip install ascii_colors
```

## Quick Start: Logging

Get started with enhanced logging immediately. By default, logs go to the console with colors.

```python
from ascii_colors import ASCIIColors, LogLevel

# Set the minimum level to display (optional, default is INFO)
ASCIIColors.set_log_level(LogLevel.DEBUG)

ASCIIColors.debug("Detailed information for developers.")
ASCIIColors.info("General progress message.")
ASCIIColors.warning("Something requires attention.")
ASCIIColors.error("An error occurred.", user_id=123) # Can pass extra context

try:
    result = 1 / 0
except Exception as e:
    # Log error with traceback automatically included
    ASCIIColors.error("Calculation failed", exc_info=e)
    # Or use the utility function
    # from ascii_colors import trace_exception
    # trace_exception(e)
```

## Basic Color Printing (Legacy)

While the focus is now on structured logging, the original simple color printing methods remain for backward compatibility and quick, direct console output. These methods now route through the INFO level logger by default.

```python
from ascii_colors import ASCIIColors

# Print text in bright red (logs as INFO)
ASCIIColors.print("Hello, world!", ASCIIColors.color_bright_red)

# Use specific color methods (also log as INFO)
ASCIIColors.red("This is red.")
ASCIIColors.green("This is green.")
ASCIIColors.blue("This is blue.")
ASCIIColors.yellow("This is yellow.")
ASCIIColors.magenta("This is magenta.")
ASCIIColors.cyan("This is cyan.")

# Style methods (log as INFO)
ASCIIColors.bold("This is bold white text.", color=ASCIIColors.color_white)
ASCIIColors.underline("This is underlined.", color=ASCIIColors.color_yellow)

# Semantic methods (log at appropriate levels)
ASCIIColors.success("Operation succeeded!") # Logs as INFO, green
ASCIIColors.fail("Operation failed!")     # Logs as ERROR, red
```
**Note:** Color/style arguments in these methods primarily affect the default `ConsoleHandler`. Other handlers (like `FileHandler`) will typically receive the formatted message without color codes.

## Core Logging Concepts

ASCIIColors adopts a flexible logging system based on Handlers and Formatters, similar to Python's standard `logging` module.

### Log Levels

Control the verbosity of your logs. Messages below the set global level are ignored.

```python
from ascii_colors import LogLevel, ASCIIColors

ASCIIColors.set_log_level(LogLevel.INFO) # Default level

# Available Levels (from lowest to highest):
# LogLevel.DEBUG    (Value: 0) - Detailed diagnostic information
# LogLevel.INFO     (Value: 1) - General operational messages
# LogLevel.WARNING  (Value: 2) - Indications of potential issues
# LogLevel.ERROR    (Value: 3) - Errors that prevented normal operation
```

### Handlers

Handlers determine where log messages are sent. You can add multiple handlers.

```python
from ascii_colors import ConsoleHandler, FileHandler, RotatingFileHandler

# Default handler is ConsoleHandler(stream=sys.stdout)

# Add a handler to log INFO and above to a file
file_handler = FileHandler("app.log", level=LogLevel.INFO)
ASCIIColors.add_handler(file_handler)

# Add a handler for rotating log files (e.g., 5MB limit, 3 backups)
rotating_handler = RotatingFileHandler(
    "app_rotate.log",
    maxBytes=5*1024*1024, # 5 MB
    backupCount=3
)
ASCIIColors.add_handler(rotating_handler)

# Add a handler to send errors specifically to stderr (console)
error_console_handler = ConsoleHandler(level=LogLevel.ERROR, stream=sys.stderr)
ASCIIColors.add_handler(error_console_handler)

# --- Managing Handlers ---
# ASCIIColors.remove_handler(file_handler) # Remove a specific handler
# ASCIIColors.clear_handlers()           # Remove all handlers
```

### Formatters

Formatters control the layout of log messages within each handler.

```python
from ascii_colors import Formatter, JSONFormatter

# Create a custom format string
# Available placeholders: {level_name}, {datetime}, {message}
# Optional (if include_source=True): {file_name}, {line_no}, {func_name}
# Plus any keys from context or **kwargs passed to log methods.
custom_format = "[{datetime:%Y-%m-%d %H:%M:%S.%f}] {level_name} ({func_name}): {message}"
my_formatter = Formatter(fmt=custom_format, include_source=True)

# Apply the formatter to a specific handler
file_handler.set_formatter(my_formatter)

# Use a JSON formatter for structured logging
json_formatter = JSONFormatter(include_fields=["datetime", "level_name", "message", "user_id"])
json_file_handler = FileHandler("app_structured.jsonl", formatter=json_formatter)
ASCIIColors.add_handler(json_file_handler)
```

### Context Management

Add contextual information (like user ID, request ID) to logs automatically within a specific thread or scope.

```python
# Set context for the current thread
ASCIIColors.set_context(request_id="req-123", user_id="alice")
ASCIIColors.info("Processing user request.")
# Output (depending on formatter): ... request_id='req-123' user_id='alice' ...

# Use a context manager for temporary context
with ASCIIColors.context(task="data_upload"):
    ASCIIColors.info("Starting upload task.")
    # Context manager automatically restores previous context on exit
    with ASCIIColors.context(user_id="bob"): # Override user_id temporarily
         ASCIIColors.warning("Nested context.")

ASCIIColors.info("Back to original context.")

# Clear specific context keys or all context for the thread
ASCIIColors.clear_context("user_id")
ASCIIColors.clear_context() # Clears all
```
Context variables are available as placeholders (e.g., `{request_id}`) in `Formatter` strings and are included in `JSONFormatter` output if not filtered out.

## Advanced Usage Examples

### Multiple Handlers (Console & File)

Log debug messages to console and info messages to a file with different formats.

```python
from ascii_colors import ASCIIColors, LogLevel, ConsoleHandler, FileHandler, Formatter

ASCIIColors.clear_handlers() # Start fresh
ASCIIColors.set_log_level(LogLevel.DEBUG) # Global level allows debug

# Console Handler for DEBUG+ with simple format
console_formatter = Formatter("{level_name}: {message}")
console_handler = ConsoleHandler(level=LogLevel.DEBUG, formatter=console_formatter)
ASCIIColors.add_handler(console_handler)

# File Handler for INFO+ with detailed format
file_formatter = Formatter(
    fmt="[{datetime}] {level_name} [{file_name}:{line_no}] - {message}",
    include_source=True
)
file_handler = FileHandler("detailed.log", level=LogLevel.INFO, formatter=file_formatter)
ASCIIColors.add_handler(file_handler)

ASCIIColors.debug("This goes only to console.")
ASCIIColors.info("This goes to console and file with different formats.")
```

### Rotating Log Files

```python
from ascii_colors import RotatingFileHandler, Formatter, LogLevel

# Keep logs up to 10MB, with 5 backup files
rotating_handler = RotatingFileHandler(
    filename="app_rotating.log",
    maxBytes=10 * 1024 * 1024, # 10 MB
    backupCount=5,
    level=LogLevel.INFO,
    formatter=Formatter("[{datetime}] {level_name}: {message}")
)
ASCIIColors.add_handler(rotating_handler)

# Log messages... rotation will happen automatically
for i in range(100000):
    ASCIIColors.info(f"Logging message number {i}")
```

### JSON Logging

Output logs in JSON Lines format for easy parsing.

```python
from ascii_colors import FileHandler, JSONFormatter, LogLevel

# Configure JSON output
json_formatter = JSONFormatter(
    include_fields=["datetime", "level_name", "message", "request_id", "user", "file_name"],
    include_source=True # To get file_name
)
json_handler = FileHandler("logs.jsonl", level=LogLevel.INFO, formatter=json_formatter)
ASCIIColors.add_handler(json_handler)

# Log with extra context
with ASCIIColors.context(request_id="req-789"):
    ASCIIColors.info("User logged in", user="charlie")
    ASCIIColors.warning("Disk space low", user="system", free_mb=500)

# Example output line in logs.jsonl:
# {"datetime": "2023-10-27T15:30:00.123456", "level_name": "INFO", "message": "User logged in", "request_id": "req-789", "user": "charlie", "file_name": "my_app.py"}
```

### Custom Formatting with Context

Combine custom formatters and context management.

```python
from ascii_colors import Formatter, ConsoleHandler

formatter = Formatter(
    "[{datetime:%H:%M:%S}] {level_name} | Req:{request_id} | User:{user_id} | {message}"
)
# Set this formatter on the default console handler (or add a new one)
# Assuming default handler is at index 0 or added explicitly:
ASCIIColors._handlers[0].set_formatter(formatter)

with ASCIIColors.context(request_id="abc", user_id="guest"):
    ASCIIColors.info("Page loaded.")
    with ASCIIColors.context(user_id="admin"):
        ASCIIColors.warning("Admin action performed.")

# Example Console Output:
# [16:45:10] INFO | Req:abc | User:guest | Page loaded.
# [16:45:10] WARNING | Req:abc | User:admin | Admin action performed.
```

## Utility Functions

Beyond logging, ASCIIColors provides helpful console utilities.

### Exception Tracing

Easily log formatted exception tracebacks.

```python
from ascii_colors import trace_exception, ASCIIColors

try:
    # Code that might raise an exception
    data = {}
    print(data['missing_key'])
except Exception as ex:
    # Logs the error message + full traceback using ASCIIColors.error()
    trace_exception(ex)
    # OR log manually with exc_info
    # ASCIIColors.error("Failed to access data", exc_info=ex)
```

### Multicolor Text

Print a single line with multiple color segments (direct console print).

```python
ASCIIColors.multicolor(
    ["Success: ", "Processed ", "100 items."],
    [ASCIIColors.color_green, ASCIIColors.color_white, ASCIIColors.color_cyan]
)
# Output: Green "Success: " White "Processed " Cyan "100 items." Reset
```

### Highlighting Text

Highlight specific words or lines in output (direct console print).

```python
ASCIIColors.highlight(
    "Error found in line 123: Critical issue.",
    ["Error", "Critical"],
    highlight_color=ASCIIColors.color_bright_red
)

ASCIIColors.highlight(
    "Line 1\nImportant Line 2\nLine 3",
    "Important",
    whole_line=True, # Highlights the entire line containing "Important"
    highlight_color=ASCIIColors.color_yellow
)
```

### Execution with Animation

Display a spinner animation while a function executes.

```python
import time

def long_running_task(duration):
    print(f"\nTask started (sleeping for {duration}s)") # Can print inside
    time.sleep(duration)
    return "Task finished successfully!"

result = ASCIIColors.execute_with_animation(
    "Processing data...", # Text shown with spinner
    long_running_task,    # Function to run
    5,                    # Arguments for the function (duration=5)
    color=ASCIIColors.color_cyan # Optional color for spinner text
)
ASCIIColors.success(f"Task result: {result}")

# Handles exceptions too:
def failing_task():
    time.sleep(2)
    raise RuntimeError("Something failed!")

try:
    ASCIIColors.execute_with_animation("Running failing task...", failing_task)
except RuntimeError as e:
    ASCIIColors.fail(f"Caught task failure: {e}")
```
The animation shows a checkmark (✓) on success or a cross mark (✗) on failure.

## Available Colors and Styles

Use these constants with `ASCIIColors.print()`, `ASCIIColors.bold()`, etc., or directly.

```python
# --- ANSI Color/Style Codes ---
ASCIIColors.color_reset

# Regular colors
ASCIIColors.color_black
ASCIIColors.color_red
ASCIIColors.color_green
ASCIIColors.color_yellow
ASCIIColors.color_blue
ASCIIColors.color_magenta
ASCIIColors.color_cyan
ASCIIColors.color_white
ASCIIColors.color_orange

# Bright colors
ASCIIColors.color_bright_black
ASCIIColors.color_bright_red
ASCIIColors.color_bright_green
ASCIIColors.color_bright_yellow
ASCIIColors.color_bright_blue
ASCIIColors.color_bright_magenta
ASCIIColors.color_bright_cyan
ASCIIColors.color_bright_white
ASCIIColors.color_bright_orange

# Styles
ASCIIColors.style_bold
ASCIIColors.style_underline
```

## Development

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/ParisNeo/ascii_colors.git
cd ascii_colors

# Recommended: Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # or venv\Scripts\activate on Windows

# Install development dependencies (if any, e.g., pytest)
# pip install -r requirements-dev.txt # (Create this file if needed)
pip install pytest # For running tests

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

### Running Tests

```bash
python -m unittest tests/test_ascii_colors.py
# or using pytest
pytest tests/
```

### Type Checking (using mypy)

```bash
pip install mypy
mypy ascii_colors/
```

## Contributing

Contributions to ASCIIColors are welcome! If you have ideas for improvements, bug fixes, or new features, please feel free to open an issue or submit a pull request. Adhering to existing code style and adding tests for new functionality is appreciated.

## License

ASCIIColors is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Changelog

### v0.7.0 (Major Refactor)
- **Breaking Change (Conceptual):** Logging core refactored to use Handlers and Formatters.
- **New:** Introduced `Handler` base class and `ConsoleHandler`, `FileHandler`, `RotatingFileHandler` implementations.
- **New:** Introduced `Formatter` base class and `JSONFormatter`.
- **New:** Added thread-local context management (`ASCIIColors.set_context`, `ASCIIColors.clear_context`, `ASCIIColors.context`). Formatters can access context variables.
- **New:** Formatters can now optionally include source info (`{file_name}`, `{line_no}`, `{func_name}`).
- **New:** Added `exc_info` parameter to `ASCIIColors.error()` and `trace_exception()` utility for easy traceback logging.
- **Update:** Default behavior logs INFO+ to console with colors.
- **Update:** Legacy print methods (`print`, `red`, `green`, etc.) now route through the logging system (default INFO level) and respect handlers/formatters. Color/style args primarily affect `ConsoleHandler`.
- **Update:** `set_log_level()` now sets a *global* filter level. Handlers manage their own levels.
- **Update:** Improved `execute_with_animation` to show success (✓) or failure (✗) status and handle exceptions correctly.
- **Deprecation:** `ASCIIColors.set_template()` is deprecated; configure formatters on handlers instead.
- **Deprecation:** `ASCIIColors.set_log_file()` is kept for backward compatibility but now *adds* a `FileHandler` instead of replacing the log target.
- **Fix:** Enhanced thread safety around handler management and file writing.
- **Docs:** Major README update reflecting new architecture and features.
- **Tests:** Significantly expanded test suite covering handlers, formatters, context, rotation, JSON, and backward compatibility.

### v0.5.x
- Added log levels (DEBUG, INFO, WARNING, ERROR)
- Added basic customizable message templates (now deprecated)
- Added basic file logging support (now superseded by FileHandler)
- Added basic thread safety for file writing
- Added type hints, unit tests, pre-commit config

### v0.0.1
- Initial release with basic color support
- Basic print methods
- Simple styling options
```
