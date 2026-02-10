############################################
Welcome to ascii_colors's Documentation! 🎨
############################################

Welcome to ascii_colors! A Python library for rich terminal output with advanced logging features and interactive prompts.



.. image:: https://img.shields.io/pypi/v/ascii_colors.svg
   :target: https://pypi.org/project/ascii-colors/
   :alt: PyPI version
.. image:: https://img.shields.io/pypi/pyversions/ascii_colors.svg
   :target: https://pypi.org/project/ascii-colors/
   :alt: Python versions
.. image:: https://img.shields.io/pypi/l/ascii_colors.svg
   :target: https://github.com/ParisNeo/ascii_colors/blob/main/LICENSE
   :alt: License
.. image:: https://img.shields.io/pypi/dm/ascii_colors.svg
   :target: https://pypi.org/project/ascii-colors/
   :alt: PyPI Downloads


Tired of bland terminal output? Need powerful logging without the boilerplate?
**ASCIIColors** is your Python solution for vibrant terminal applications!

It elegantly combines:

*   ✨ **Effortless Color Printing:** Directly output text with a wide range of ANSI colors and styles using simple, intuitive methods.
*   🪵 **Flexible Logging System:** A robust, leveled logging framework with handlers, formatters, and context management.
*   🐍 **`logging` Compatibility:** Features a familiar API (`import ascii_colors as logging`) for seamless integration or transition from Python's standard logging module.
*   🛠️ **Handy Utilities:** Includes useful tools like console spinners and text highlighting.

Whether you're building CLI tools, backend services, or just want more informative script output, ASCIIColors makes your terminal interactions clearer and more expressive.

.. note::
   For a quick overview and installation instructions, you can also check the
   `README file on GitHub <https://github.com/ParisNeo/ascii_colors/blob/main/README.md>`_.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   usage
   api

Features
--------

- **Rich Colors & Styles**: 256-color support with bright variants, backgrounds, and text styles (bold, italic, underline, etc.)
- **Dual API**: Native fluent API + standard logging compatibility
- **Advanced Formatting**: Percent-style, brace-style, and JSON formatters
- **Contextual Logging**: Thread-local context fields automatically included in all logs
- **Progress Bars**: Customizable progress bars with multiple styles
- **Interactive Menus**: Keyboard-navigable menus with filtering and submenus
- **Questionary Compatibility**: Drop-in replacement for the popular `questionary` library
- **Enhanced Tracebacks**: Beautiful exception formatting with local variable inspection
- **Cross-Platform**: Works on Windows, Linux, and macOS

Quick Example
-------------

.. code-block:: python

   from ascii_colors import ASCIIColors, getLogger, basicConfig, LogLevel
   import logging

   # Direct colored output
   ASCIIColors.green("✓ Success!", style=ASCIIColors.style_bold)
   ASCIIColors.multicolor(["Error: ", "File not found"], 
                          [ASCIIColors.color_red, ASCIIColors.color_white])

   # Standard logging compatibility
   basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
   logger = getLogger("myapp")
   logger.info("Application started")

   # Interactive prompts (questionary-compatible)
   from ascii_colors import questionary

   name = questionary.text("What's your name?").ask()
   proceed = questionary.confirm("Continue?", default=True).ask()

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
