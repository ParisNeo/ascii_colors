API Reference
=============

This page provides an auto-generated summary of the main `ascii_colors` API components.

Core Class (`ASCIIColors`)
--------------------------
The main class providing direct print methods and managing global state.

.. autoclass:: ascii_colors.ASCIIColors
   :members: print, success, fail, red, green, blue, yellow, magenta, cyan, white, orange,
             bright_red, bright_green, bright_yellow, bright_blue, bright_magenta, bright_cyan, bright_white,
             bg_red, bg_green, bg_yellow, bg_blue, bg_magenta, bg_cyan, bg_white, bg_orange,
             bg_bright_red, bg_bright_green, bg_bright_yellow, bg_bright_blue, bg_bright_magenta, bg_bright_cyan, bg_bright_white,
             print_with_bg,
             bold, dim, italic, underline, blink, reverse, hidden, strikethrough,
             multicolor, highlight, activate, reset, resetAll,
             execute_with_animation,
             set_log_level, add_handler, remove_handler, clear_handlers,
             set_context, clear_context, context, get_thread_context,
             # Exclude internal/deprecated/less common methods if desired
   :exclude-members: _log, set_log_file, set_template
   :undoc-members:
   :show-inheritance:

.. note::
   Color and style constants (e.g., `color_red`, `style_bold`) are also available
   directly on the `ASCIIColors` class but are numerous and listed in the Usage section
   for brevity here.

Logging Compatibility API
-------------------------
Functions mimicking the standard `logging` module.

.. autofunction:: ascii_colors.getLogger
.. autofunction:: ascii_colors.basicConfig
.. autofunction:: ascii_colors.getLevelName

Level Constants
~~~~~~~~~~~~~~~
Standard logging level constants available directly from the module.

.. data:: ascii_colors.CRITICAL
.. data:: ascii_colors.ERROR
.. data:: ascii_colors.WARNING
.. data:: ascii_colors.INFO
.. data:: ascii_colors.DEBUG
.. data:: ascii_colors.NOTSET

Handler Classes
---------------
Used to direct logging output.

.. autoclass:: ascii_colors.Handler
   :members: setLevel, setFormatter, handle, emit, close
   :undoc-members:
   :show-inheritance:

.. autoclass:: ascii_colors.StreamHandler
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ascii_colors.FileHandler
   :members: emit, close, flush
   :undoc-members:
   :show-inheritance:

.. autoclass:: ascii_colors.handlers.RotatingFileHandler
   :members: emit, should_rotate, do_rollover
   :undoc-members:
   :show-inheritance:
   :canonical: ascii_colors.RotatingFileHandler

.. note::
   Access `RotatingFileHandler` via `ascii_colors.handlers.RotatingFileHandler` or
   directly as `ascii_colors.RotatingFileHandler`. The alias `ascii_colors.StreamHandler`
   points to `ascii_colors.ConsoleHandler`.

Formatter Classes
-----------------

.. autoclass:: ascii_colors.Formatter
   :members: format, format_exception
   :undoc-members:
   :show-inheritance:

.. autoclass:: ascii_colors.JSONFormatter
   :members: format
   :undoc-members:
   :show-inheritance:


Utility Functions
-----------------

.. autofunction:: ascii_colors.get_trace_exception
.. autofunction:: ascii_colors.trace_exception