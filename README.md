# ASCIIColors

ASCIIColors is a Python utility that provides an easy way to add color and style to text output in the console. It offers a simple interface for printing text with various colors and styles, making it especially useful for enhancing the readability of console-based applications or adding emphasis to specific messages. It also includes advanced logging capabilities with customizable templates, log levels, and file logging support.

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Standard Methods](#standard-methods)
- [Colors and Styles](#colors-and-styles)
- [Advanced Logging](#advanced-logging)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Installation

You can install ASCIIColors via `pip` from the Python Package Index (PyPI):

```bash
pip install ascii_colors
```

## Basic Usage

ASCIIColors provides a set of methods for printing text with different colors and styles:

```python
from asciicolors import ASCIIColors

# Print text in bright red color
ASCIIColors.print("Hello, world!", ASCIIColors.color_bright_red)
```

## Standard Methods

ASCIIColors provides the following methods for formatting and printing text:

- `print(text, color=color_bright_red, style="", end="\n", flush=False)`: Prints text with the specified color and style.
- `warning(text, end="\n", flush=False)`: Prints text in a warning style.
- `error(text, end="\n", flush=False)`: Prints text in an error style.
- `success(text, end="\n", flush=False)`: Prints text in a success style.
- `info(text, end="\n", flush=False)`: Prints text in an info style.

Color-specific methods:
- `red(text, end="\n", flush=False)`
- `green(text, end="\n", flush=False)`
- `blue(text, end="\n", flush=False)`
- `yellow(text, end="\n", flush=False)`
- `magenta(text, end="\n", flush=False)`
- `cyan(text, end="\n", flush=False)`

Style methods:
- `bold(text, color=color_bright_red, end="\n", flush=False)`
- `underline(text, color=color_bright_red, end="\n", flush=False)`

Control methods:
- `activate(color_or_style)`
- `reset()`
- `resetColor()`
- `resetStyle()`
- `resetAll()`

## Colors and Styles

Available colors:
```python
# Regular colors
color_black
color_red
color_green
color_yellow
color_blue
color_magenta
color_cyan
color_white
color_orange

# Bright colors
color_bright_black
color_bright_red
color_bright_green
color_bright_yellow
color_bright_blue
color_bright_magenta
color_bright_cyan
color_bright_white
color_bright_orange

# Styles
style_bold
style_underline
```

## Advanced Logging

### Log Levels

ASCIIColors now supports four log levels:

```python
from ascii_colors import LogLevel

LogLevel.DEBUG    # Detailed information for debugging
LogLevel.INFO     # General information
LogLevel.WARNING  # Warning messages
LogLevel.ERROR    # Error messages

# Set minimum log level
ASCIIColors.set_log_level(LogLevel.WARNING)  # Only show WARNING and ERROR messages
```

### Customizable Templates

You can customize the message format for each log level:

```python
# Custom template with datetime and additional fields
ASCIIColors.set_template(
    LogLevel.INFO,
    "ℹ️ {datetime} | {message} | {custom_field}"
)

# Using the template
ASCIIColors.info("Hello", custom_field="test")
# Output: ℹ️ 2025-01-12 21:38:05 | Hello | test
```

### File Logging

Enable logging to a file:

```python
# Set up file logging
ASCIIColors.set_log_file("logs/app.log")

# All subsequent messages will be written to both console and file
ASCIIColors.info("This message is logged to file")
```

## Exception Tracing

Trace and color your exceptions:

```python
from asciicolors import trace_exception

try:
    # some code that might raise an exception
    pass
except Exception as ex:
    trace_exception(ex)
```

## Multicolor Text

Print text with multiple colors:

```python
ASCIIColors.multicolor(
    ["Green text", "red text", "yellow text"],
    [ASCIIColors.color_green, ASCIIColors.color_red, ASCIIColors.color_yellow]
)
```

## Development

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/ascii_colors.git
cd ascii_colors

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
python -m pytest tests/
```

### Type Checking

```bash
mypy ascii_colors.py
```

## Contributing

Contributions to ASCIIColors are welcome! If you have ideas for improvements or new features, please feel free to open an issue or submit a pull request. Make sure to follow the contribution guidelines.

## License

ASCIIColors is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Changelog

### v0.5.0
- Added log levels (DEBUG, INFO, WARNING, ERROR)
- Added customizable message templates
- Added file logging support
- Added thread-safe operations
- Added comprehensive type hints
- Added unit tests
- Added pre-commit configuration

### v0.0.1
- Initial release with basic color support
- Basic print methods
- Simple styling options