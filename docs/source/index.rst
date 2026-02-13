############################################
Welcome to ascii_colors's Documentation! 🎨
############################################

Welcome to ascii_colors! A Python library for rich terminal output with advanced logging features, interactive prompts, and Rich-compatible components.

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


Stop wrestling with multiple CLI libraries. **ASCIIColors** unifies everything you need for modern terminal applications into a single, elegant toolkit.

| 🎨 **Colors & Styles** | 🪵 **Logging System** | 📊 **Progress Bars** |
|:---|:---|:---|
| 256-color support, bright variants, backgrounds, bold/italic/underline/blink | Full `logging` compatibility with handlers, formatters, JSON output, rotation | `tqdm`-like bars with custom styles (fill, blocks, line, emoji), thread-safe |

| 🖥️ **Rich Components** | ❓ **Smart Prompts** | 🛠️ **Utilities** |
|:---|:---|:---|
| Panels, tables, trees, syntax highlighting, live displays, markdown | Drop-in `questionary` replacement: text, password, confirm, select, checkbox, autocomplete | Spinners, enhanced tracebacks, multicolor text, confirm/prompt helpers |

---

Quick Start
-----------

.. code-block:: python

   from ascii_colors import ASCIIColors, rich

   # Rich markup anywhere
   rich.print("[bold green]Success![/bold green] Operation [italic]completed[/italic]")

   # Convenience methods
   ASCIIColors.panel("Important message", title="Notice", border_style="yellow")

   # Or use the standard logging API
   import ascii_colors as logging
   logging.basicConfig(level=logging.INFO)
   logging.info("Application started")

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   basic_usage
   logging_guide
   rich_integration
   interactive_prompts
   api

Features
--------

- **Rich Colors & Styles**: 256-color support with bright variants, backgrounds, and text styles
- **Dual API**: Native fluent API + standard logging compatibility
- **Rich Integration**: Full Rich-compatible components (panels, tables, trees, syntax, markdown, live displays)
- **Advanced Formatting**: Percent-style, brace-style, and JSON formatters
- **Contextual Logging**: Thread-local context fields automatically included in all logs
- **Progress Bars**: Customizable progress bars with multiple styles
- **Interactive Menus**: Keyboard-navigable menus with filtering and submenus
- **Questionary Compatibility**: Drop-in replacement for the popular `questionary` library
- **Enhanced Tracebacks**: Beautiful exception formatting with local variable inspection
- **Cross-Platform**: Works on Windows, Linux, and macOS

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
