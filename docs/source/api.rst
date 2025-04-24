API Reference
=============

This page provides an auto-generated summary of the main `ascii_colors` API components.

Core Class (`ASCIIColors`)
--------------------------
The `ASCIIColors` class provides static methods for direct terminal printing and manages the global logging state (handlers, level).

.. autoclass:: ascii_colors.ASCIIColors
   :members:
   :undoc-members:
   :show-inheritance:

   **Direct Print Methods (Bypass Logging)**
      These methods print directly to the console (default `sys.stdout`).

      .. automethod:: print
      .. automethod:: print_with_bg
      .. automethod:: success
      .. automethod:: fail
      .. automethod:: black
      .. automethod:: red
      .. automethod:: green
      .. automethod:: yellow
      .. automethod:: blue
      .. automethod:: magenta
      .. automethod:: cyan
      .. automethod:: white
      .. automethod:: orange
      .. automethod:: bright_black
      .. automethod:: bright_red
      .. automethod:: bright_green
      .. automethod:: bright_yellow
      .. automethod:: bright_blue
      .. automethod:: bright_magenta
      .. automethod:: bright_cyan
      .. automethod:: bright_white
      .. automethod:: bg_black
      .. automethod:: bg_red
      .. automethod:: bg_green
      .. automethod:: bg_yellow
      .. automethod:: bg_blue
      .. automethod:: bg_magenta
      .. automethod:: bg_cyan
      .. automethod:: bg_white
      .. automethod:: bg_orange
      .. automethod:: bg_bright_black
      .. automethod:: bg_bright_red
      .. automethod:: bg_bright_green
      .. automethod:: bg_bright_yellow
      .. automethod:: bg_bright_blue
      .. automethod:: bg_bright_magenta
      .. automethod:: bg_bright_cyan
      .. automethod:: bg_bright_white
      .. automethod:: bold
      .. automethod:: dim
      .. automethod:: italic
      .. automethod:: underline
      .. automethod:: blink
      .. automethod:: reverse
      .. automethod:: hidden
      .. automethod:: strikethrough
      .. automethod:: multicolor
      .. automethod:: highlight
      .. automethod:: activate
      .. automethod:: reset
      .. automethod:: resetAll
      .. automethod:: execute_with_animation

   **Logging Methods (Use Logging System)**
      These methods create log records processed by handlers and formatters.

      .. automethod:: debug
      .. automethod:: info
      .. automethod:: warning
      .. automethod:: error
      .. automethod:: critical

   **Logging Configuration Methods**
      These methods configure the global logging state.

      .. automethod:: set_log_level
      .. automethod:: add_handler
      .. automethod:: remove_handler
      .. automethod:: clear_handlers

   **Context Methods**
      Manage thread-local context for log records.

      .. automethod:: set_context
      .. automethod:: clear_context
      .. automethod:: context
      .. automethod:: get_thread_context

   **Color and Style Constants**
      Numerous constants like `color_red`, `style_bold`, `bg_blue` are available directly on the class. See the :doc:`usage` page for a full list.

   .. DANGER::
      Avoid using deprecated methods like `set_log_file` and `set_template`. Use `add_handler(FileHandler(...))` and `handler.setFormatter(...)` instead.

Logging Compatibility API
-------------------------
Functions designed to mimic Python's standard `logging` module for easy integration and familiarity. These functions interact with the global state managed by `ASCIIColors`.

.. autofunction:: ascii_colors.getLogger
.. autofunction:: ascii_colors.basicConfig
.. autofunction:: ascii_colors.getLevelName

Level Constants
~~~~~~~~~~~~~~~
Standard logging level integer constants, available directly from the module.

.. data:: ascii_colors.CRITICAL
   :value: 50
.. data:: ascii_colors.ERROR
   :value: 40
.. data:: ascii_colors.WARNING
   :value: 30
.. data:: ascii_colors.INFO
   :value: 20
.. data:: ascii_colors.DEBUG
   :value: 10
.. data:: ascii_colors.NOTSET
   :value: 0

Handler Classes
---------------
Handlers determine where log records are sent (e.g., console, file). They can be configured with levels and formatters.

.. autoclass:: ascii_colors.Handler
   :members: setLevel, getLevel, setFormatter, getFormatter, handle, emit, close
   :undoc-members:
   :show-inheritance:

.. autoclass:: ascii_colors.ConsoleHandler
   :members: emit, close
   :undoc-members:
   :show-inheritance:
   :canonical: ascii_colors.StreamHandler

   .. note::
      This class is also available as `ascii_colors.StreamHandler` for compatibility with the standard `logging` module.

.. autoclass:: ascii_colors.FileHandler
   :members: emit, close, flush
   :undoc-members:
   :show-inheritance:

.. autoclass:: ascii_colors.RotatingFileHandler
   :members: emit, should_rotate, do_rollover, close
   :undoc-members:
   :show-inheritance:
   :canonical: ascii_colors.handlers.RotatingFileHandler

   .. note::
      Access this handler via `ascii_colors.handlers.RotatingFileHandler` or `from ascii_colors import handlers` then `handlers.RotatingFileHandler`. It's also aliased at the top level as `ascii_colors.RotatingFileHandler`.

.. data:: ascii_colors.handlers
   A namespace object providing access to handler classes like `handlers.RotatingFileHandler`, similar to `logging.handlers`.

Formatter Classes
-----------------
Formatters convert log records into strings before they are emitted by handlers.

.. autoclass:: ascii_colors.Formatter
   :members: __init__, format, format_exception
   :undoc-members:
   :show-inheritance:

.. autoclass:: ascii_colors.JSONFormatter
   :members: __init__, format
   :undoc-members:
   :show-inheritance:


Utility Functions
-----------------

.. autofunction:: ascii_colors.get_trace_exception
.. autofunction:: ascii_colors.trace_exception