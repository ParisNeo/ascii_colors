API Documentation
=================

This page provides auto-generated documentation from the ``ascii_colors`` source code docstrings.

Main Module (`ascii_colors`)
----------------------------

.. automodule:: ascii_colors
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: _T, _AsciiLoggerAdapter, _style_mapping, _initial_timestamp, _logger_cache, _logger_cache_lock, _level_to_name, _name_to_level, _level_name_to_int

Handler Subclasses
------------------

Handlers determine where log messages are sent.

.. autoclass:: ascii_colors.ConsoleHandler
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ascii_colors.StreamHandler
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ascii_colors.FileHandler
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ascii_colors.RotatingFileHandler
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ascii_colors.handlers.RotatingFileHandler
   :members:
   :undoc-members:
   :show-inheritance:


Formatter Subclasses
--------------------

Formatters control the layout of log messages.

.. autoclass:: ascii_colors.Formatter
   :members: format, format_exception
   :undoc-members:

.. autoclass:: ascii_colors.JSONFormatter
   :members: format
   :undoc-members:
   :show-inheritance:


Main Class (`ASCIIColors`)
--------------------------

Provides static methods for direct printing and manages global state.

.. autoclass:: ascii_colors.ASCIIColors
   :members: print, red, green, blue, yellow, magenta, cyan, white, orange, bold, underline, italic, strikethrough, bg_red, execute_with_animation, highlight, multicolor, set_context, context, add_handler, set_log_level, info, warning, error, debug, critical
   :undoc-members:
   :exclude-members: _handlers, _global_level, _handler_lock, _basicConfig_called, _context, _level_colors, _log, T # Exclude internal/duplicate attributes