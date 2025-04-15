# ASCIIColors 🎨

[![PyPI version](https://badge.fury.io/py/ascii_colors.svg)](https://badge.fury.io/py/ascii_colors)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Versions](https://img.shields.io/pypi/pyversions/ascii_colors.svg)](https://pypi.org/project/ascii_colors/)

**ASCIIColors** is a versatile Python library designed to simplify the process of adding color, style, and structure to your console output. Whether you need simple colored text, styled messages, sophisticated logging with levels and file output, or helpful utilities like progress animations and text highlighting, ASCIIColors provides an intuitive API to enhance your command-line applications.

## ✨ Features

*   **Simple Color & Style:** Easily print text in various foreground colors (standard and bright) and apply styles like bold and underline.
*   **Convenience Methods:** Dedicated methods for common colors (`red`, `green`, `blue`, etc.) and styles (`bold`, `underline`).
*   **Structured Logging:** Implement robust logging with standard levels (DEBUG, INFO, WARNING, ERROR).
*   **Log Level Filtering:** Control the verbosity of console and file output based on log levels.
*   **Customizable Log Templates:** Define custom formats for log messages, including timestamps and user-defined fields.
*   **Thread-Safe File Logging:** Reliably log messages to a file, even in multi-threaded applications.
*   **Exception Tracing:** Automatically format and print exception tracebacks with appropriate colors.
*   **Multicolor Output:** Print a sequence of text segments, each with its own color, on a single line.
*   **Text Highlighting:** Find and highlight specific substrings within a larger text block.
*   **Execution Animation:** Display a visual animation while a function executes, providing feedback for long-running tasks.
*   **Manual Control:** Activate and deactivate specific colors or styles for fine-grained control over console output.

## 📦 Installation

Install ASCIIColors directly from the Python Package Index (PyPI):

```bash
pip install ascii_colors
```

## 🚀 Quick Start

Get started quickly with basic colored output or structured logging:

```python
from ascii_colors import ASCIIColors, LogLevel

# --- Simple Colored Output ---

# Using convenience methods
ASCIIColors.red("This is an error message.")
ASCIIColors.green("Operation successful!")
ASCIIColors.yellow("Warning: something needs attention.")
ASCIIColors.bold("This text is bold and bright red.", color=ASCIIColors.color_bright_red)
ASCIIColors.underline("This is underlined blue text.", color=ASCIIColors.color_blue)

# Using the base print method
ASCIIColors.print("Custom cyan text", color=ASCIIColors.color_cyan)
ASCIIColors.print(
    "Bold magenta text",
    color=ASCIIColors.color_magenta,
    style=ASCIIColors.style_bold
)

# --- Structured Logging ---

# Set the minimum level (e.g., show INFO and above)
ASCIIColors.set_log_level(LogLevel.INFO)

# Log messages using different levels
ASCIIColors.debug("This won't be shown with INFO level.") # Hidden
ASCIIColors.info("Application starting...")
ASCIIColors.warning("Configuration file not found, using defaults.")
ASCIIColors.error("Failed to connect to the database!")

# Log success/failure messages (uses INFO level internally)
ASCIIColors.success("Data processing complete.")
ASCIIColors.fail("Task failed unexpectedly.")
```

## ⚙️ Core Printing Methods

These methods provide the foundation for console output.

### `ASCIIColors.print(text, color=..., style=..., end=..., flush=...)`

The core method for printing text.

*   `text` (str): The text to print.
*   `color` (str): An ANSI color code (e.g., `ASCIIColors.color_red`). Defaults to `color_bright_red`.
*   `style` (str): An ANSI style code (e.g., `ASCIIColors.style_bold`). Defaults to `""`.
*   `end` (str): String appended after the text. Defaults to `\n`.
*   `flush` (bool): Whether to forcibly flush the stream. Defaults to `False`.

```python
ASCIIColors.print("Hello", color=ASCIIColors.color_green, style=ASCIIColors.style_bold, end="... ")
ASCIIColors.print("World!", color=ASCIIColors.color_blue, style=ASCIIColors.style_underline)
# Output (colored): Hello... World!
```

### Convenience Color Methods

Shortcuts for `ASCIIColors.print()` with preset colors. Examples: `red()`, `green()`, `blue()`, `yellow()`, `cyan()`, `magenta()`, `orange()`, `black()`, `white()`, and their `bright_` counterparts (e.g., `bright_red()`).

```python
ASCIIColors.bright_yellow("This is bright yellow text.")
```

### Convenience Style Methods

Shortcuts for `ASCIIColors.print()` with preset styles.

*   `bold(text, color=..., end=..., flush=...)`: Prints bold text. Defaults to `color_bright_red`.
*   `underline(text, color=..., end=..., flush=...)`: Prints underlined text. Defaults to `color_bright_red`.

```python
ASCIIColors.bold("Important!", color=ASCIIColors.color_bright_white)
ASCIIColors.underline("Read this carefully.", color=ASCIIColors.color_cyan)
```

## 🪵 Advanced Logging

ASCIIColors includes a flexible logging system built on top of its printing capabilities.

### Log Levels (`LogLevel`)

Control message verbosity using integer-based levels:

```python
from ascii_colors import LogLevel

LogLevel.DEBUG    # 0: Detailed diagnostic information
LogLevel.INFO     # 1: General operational information
LogLevel.WARNING  # 2: Indicates potential issues
LogLevel.ERROR    # 3: Indicates errors that prevented normal operation

# Set the minimum level of messages to display/log
ASCIIColors.set_log_level(LogLevel.INFO) # Default
ASCIIColors.set_log_level(LogLevel.DEBUG) # Show everything
ASCIIColors.set_log_level(LogLevel.WARNING) # Show WARNING and ERROR only
```

### Logging Methods

Methods for logging messages at specific levels. They respect the configured `_log_level`.

*   `debug(text, **kwargs)`: Logs a debug message (Magenta).
*   `info(text, **kwargs)`: Logs an info message (Blue). Can override color via `kwargs`.
*   `warning(text, **kwargs)`: Logs a warning message (Orange).
*   `error(text, **kwargs)`: Logs an error message (Red).

*   `success(text, **kwargs)`: Convenience method, logs an INFO message in Green.
*   `fail(text, **kwargs)`: Convenience method, logs an INFO message in Red.

Any additional `**kwargs` passed are available for use in custom templates.

```python
ASCIIColors.set_log_level(LogLevel.DEBUG)
ASCIIColors.debug("Detailed step 1 info.")
ASCIIColors.info("User logged in.", user_id=123) # Pass custom data
ASCIIColors.warning("Disk space low.")
ASCIIColors.error("Critical component failed.")
ASCIIColors.success("Backup completed.")
ASCIIColors.fail("Payment processing failed.")
```

### Customizable Templates (`set_template`)

Define the format for log messages per level. Templates must include `{datetime}` and `{message}` placeholders. Other keys passed via `**kwargs` to logging methods can also be used.

```python
from ascii_colors import LogLevel

# Default template: "[LEVEL][{datetime}] {message}"

# Set a custom template for INFO messages
ASCIIColors.set_template(
    LogLevel.INFO,
    "✅ [{datetime}] ({level_name}): {message} [Context: {context}]"
)

# Set a custom template for ERROR messages
ASCIIColors.set_template(
    LogLevel.ERROR,
    "🔥 ERROR [{datetime}] | {message} | Module: {module_name}"
)


# Use the custom templates (assuming log level allows)
ASCIIColors.info("Task started", level_name="INFO", context="Processing")
# Output (colored): ✅ [2023-10-27 10:30:00] (INFO): Task started [Context: Processing]

ASCIIColors.error("File not found", module_name="FileHandler")
# Output (colored): 🔥 ERROR [2023-10-27 10:30:01] | File not found | Module: FileHandler
```

### File Logging (`set_log_file`)

Log messages to a specified file in addition to the console. File output is plain text (no ANSI codes) and respects the configured log level. Operations are thread-safe.

```python
# Configure logging to a file
ASCIIColors.set_log_file("logs/my_application.log") # Creates 'logs' dir if needed

# These messages will go to console (if level permits) AND the file
ASCIIColors.info("Starting data import.")
ASCIIColors.warning("Skipping invalid record.")

# Check the contents of 'logs/my_application.log':
# [INFO][2023-10-27 10:35:00] Starting data import.
# [WARNING][2023-10-27 10:35:01] Skipping invalid record.
```

## 🛠️ Utility Functions

Helpful functions for common console tasks.

### Exception Tracing (`trace_exception`, `get_trace_exception`)

Format and print exception tracebacks clearly using error colors.

```python
from ascii_colors import trace_exception, get_trace_exception

try:
    result = 10 / 0
except Exception as ex:
    # Print the formatted traceback directly to console (using ASCIIColors.error)
    trace_exception(ex)

    # Or, get the formatted traceback as a string
    # traceback_str = get_trace_exception(ex)
    # print(f"Caught exception:\n{traceback_str}")
```

### Multicolor Text (`multicolor`)

Print different parts of a message in different colors on the same line.

```python
ASCIIColors.multicolor(
    ["Status: ", "RUNNING", " | Progress: ", "75%"],
    [
        ASCIIColors.color_white,
        ASCIIColors.color_bright_green,
        ASCIIColors.color_white,
        ASCIIColors.color_cyan
    ]
)
# Output (colored): Status: RUNNING | Progress: 75%
```

### Text Highlighting (`highlight`)

Emphasize occurrences of specific substrings within a text block.

```python
text = "Log entry: User 'admin' logged in. User 'guest' attempted login."
keywords = ["admin", "guest"]

# Highlight only the keywords
ASCIIColors.highlight(
    text,
    keywords,
    color=ASCIIColors.color_white, # Base text color
    highlight_color=ASCIIColors.color_bright_yellow # Highlight color
)
# Output (colored): Log entry: User 'admin' logged in. User 'guest' attempted login.

# Highlight the entire lines containing keywords
log_data = "INFO: System started\nERROR: Connection failed\nINFO: User 'admin' logged out"
ASCIIColors.highlight(
    log_data,
    "ERROR",
    color=ASCIIColors.color_green,
    highlight_color=ASCIIColors.color_bright_red,
    whole_line=True
)
# Output (colored):
# INFO: System started      (green)
# ERROR: Connection failed (bright red)
# INFO: User 'admin' logged out (green)

```

### Execution Animation (`execute_with_animation`)

Display a spinning animation while a function runs, providing visual feedback for potentially long operations.

```python
import time

def simulate_work(duration):
    print(f"\nStarting work for {duration} seconds...")
    time.sleep(duration)
    print("\nWork finished!")
    return f"Completed after {duration}s"

# Run the function with an animation
result = ASCIIColors.execute_with_animation(
    "Processing data...", # Text displayed next to animation
    simulate_work,        # Function to execute
    5,                    # Positional argument for simulate_work
    color=ASCIIColors.color_cyan # Color for the pending text and animation
)

# Output shows:
# Processing data... ⠋ (spinning animation in cyan)
# (After 5 seconds, the line updates)
# Processing data... ✓ (green checkmark)
#
# Starting work for 5 seconds...
# Work finished!

print(f"\nFunction returned: {result}")
# Output: Function returned: Completed after 5s
```

## 🕹️ Manual Color/Style Control

Activate and reset colors/styles manually for more complex output scenarios.

*   `activate(color_or_style)`: Prints the ANSI code to activate a color or style without adding text or a newline.
*   `reset()`, `resetAll()`: Prints the ANSI code to reset all colors and styles.
*   `resetColor()`: Resets only the color.
*   `resetStyle()`: Resets only the style (effect may vary across terminals).
*   Convenience activation methods: `activateRed()`, `activateGreen()`, `activateBold()`, `activateUnderline()`, etc.

```python
ASCIIColors.activate(ASCIIColors.color_blue)
ASCIIColors.activate(ASCIIColors.style_bold)
print("This text is bold blue.", end="")
ASCIIColors.reset() # Reset color and style
print(" This text is normal.")

ASCIIColors.activateGreen()
print("Green ", end="")
ASCIIColors.activateYellow()
print("Yellow ", end="")
ASCIIColors.resetAll()
print("Normal")
```

## 🧑‍💻 Development

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/ParisNeo/ascii_colors.git # Or your fork
cd ascii_colors

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install development dependencies (includes pytest, mypy, flake8)
# Create a requirements-dev.txt if you don't have one, e.g.:
# flake8
# mypy
# pytest
# pip install -r requirements-dev.txt # (Assuming requirements-dev.txt exists)
pip install pytest mypy flake8 # Install directly if no file

# Install pre-commit hooks (uses .pre-commit-config.yaml)
pip install pre-commit
pre-commit install
```

### Running Tests

Execute the test suite using `pytest`:

```bash
python -m pytest tests/
```

### Type Checking

Check static types using `mypy`:

```bash
mypy ascii_colors/
```

### Linting

Check code style using `flake8`:

```bash
flake8 ascii_colors/ tests/
```

(Note: The pre-commit hook `parisneo-python-check` likely runs linters and type checkers automatically.)

## 🙌 Contributing

Contributions are welcome! If you have suggestions, bug reports, or want to contribute code, please:

1.  Check the [Issues](https://github.com/ParisNeo/console_tools/issues) page to see if your topic is already discussed.
2.  Open a new issue to discuss your proposed changes or report a bug.
3.  Fork the repository, create a feature branch, and make your changes.
4.  Ensure tests pass and add new tests for your features.
5.  Ensure code style and type checks pass (run `pre-commit run --all-files`).
6.  Submit a pull request.

## 📜 License

ASCIIColors is distributed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for more details.

## 📅 Changelog

### v0.5.0 - v0.5.2
*   Added `execute_with_animation` utility.
*   Added `highlight` utility function.
*   Refined internal logging logic in `print`.
*   Updated setup classifiers and Python version support.
*   Added log levels (DEBUG, INFO, WARNING, ERROR)
*   Added customizable message templates (`set_template`)
*   Added file logging support (`set_log_file`)
*   Added thread-safe file writing
*   Added comprehensive type hints
*   Added unit tests (`pytest`)
*   Added pre-commit configuration (`.pre-commit-config.yaml`)
*   Added static type checking (`mypy`) config (`setup.cfg`)
*   Added linting (`flake8`) config (`setup.cfg`)

### v0.0.1
*   Initial release with basic color support.
*   Basic print methods (`print`, color shortcuts like `red`, `green`, etc.).
*   Simple styling options (`bold`, `underline`).
*   Basic activation/reset methods.