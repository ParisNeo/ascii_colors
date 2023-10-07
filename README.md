# console_tools

[![PyPI version](https://badge.fury.io/py/console-tools.svg)](https://badge.fury.io/py/console-tools)

**console_tools** is a Python library for enhancing console output with colors, styles, and exception handling, making it easy to create visually appealing command-line interfaces.

## Features

- Display text on the console with various text colors and styles.
- Handle exceptions gracefully and display error messages in a user-friendly manner.
- Simplify console formatting for improved readability.

## Installation

You can install **console_tools** via pip:

```bash
pip install console-tools
```

## Usage

Here's a quick example of how to use **console_tools**:

```python
from console_tools import colored_print, handle_exception

try:
    # Some code that might raise an exception
    result = 10 / 0
except ZeroDivisionError as e:
    handle_exception(e)

colored_print("This is a colored message.", color="green", style="bold")
colored_print("This is an error message.", color="red", style="underline")
```

For more detailed usage instructions, refer to the [documentation](https://github.com/ParisNeo/console_tools).

## Contributing

If you'd like to contribute to **console_tools**, please check out the [Contribution Guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- ParisNeo (@ParisNeo) - [GitHub Profile](https://github.com/ParisNeo)

## Acknowledgments

- Special thanks to the Python community for inspiration and support.

Feel free to reach out if you have any questions or encounter issues with the library. Happy coding!
