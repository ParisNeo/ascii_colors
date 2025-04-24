=============
API Reference
=============

This section details the classes, methods, functions, and constants provided by the ``ascii_colors`` library.

Core Class: ``ASCIIColors``
---------------------------

The central class managing global logging state and providing static methods for direct terminal printing.

.. autoclass:: ascii_colors.ASCIIColors
   :show-inheritance:

   .. rubric:: Direct Print Methods (Bypass Logging System)

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

   .. rubric:: Console Utilities (Using Direct Printing)

   .. automethod:: execute_with_animation

   .. rubric:: Logging Methods (Use Logging System)

   These methods create log records processed by configured handlers and formatters.

   .. automethod:: debug
   .. automethod:: info
   .. automethod:: warning
   .. automethod:: error
   .. automethod:: critical

   .. rubric:: Global Logging Configuration

   Methods to manage the global logging state (handlers, level).

   .. automethod:: set_log_level
   .. automethod:: add_handler
   .. automethod:: remove_handler
   .. automethod:: clear_handlers

   .. rubric:: Thread-Local Context Management

   Methods to manage contextual information added to log records.

   .. automethod:: set_context
   .. automethod:: clear_context
   .. automethod:: context
   .. automethod:: get_thread_context

   .. rubric:: Color and Style Constants

   Provides numerous constants like ``color_red``, ``style_bold``, ``bg_blue``.
   See the :ref:`Available Colors and Styles <direct-print-colors-styles>` section in the :doc:`usage` guide for a full list.

   .. warning::
      Deprecated methods ``set_log_file`` and ``set_template`` should not be used. Use :meth:`add_handler` with :class:`~ascii_colors.FileHandler` and :meth:`~ascii_colors.Handler.setFormatter` respectively.

Logging Compatibility API
-------------------------

Functions designed to mimic Python's standard ``logging`` module for easy integration and familiarity. These operate on the global state managed by :class:`~ascii_colors.ASCIIColors`.

.. autofunction:: ascii_colors.getLogger
.. autofunction:: ascii_colors.basicConfig
.. autofunction:: ascii_colors.getLevelName

**Level Constants**

Standard logging level integer constants, available directly from the module or via the `logging` alias.

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

Handlers direct log records to the appropriate destination (e.g., console, file).

.. autoclass:: ascii_colors.Handler
   :members: setLevel, getLevel, setFormatter, getFormatter, handle, emit, close
   :undoc-members:
   :show-inheritance:

.. autoclass:: ascii_colors.ConsoleHandler
   :members: emit, close
   :undoc-members:
   :show-inheritance:
   :canonical: ascii_colors.StreamHandler

   .. important::
      Available as ``ascii_colors.StreamHandler`` for compatibility with the standard ``logging`` module.

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
      Access via ``from ascii_colors import handlers`` then ``handlers.RotatingFileHandler``, or directly as ``ascii_colors.RotatingFileHandler``.

.. data:: ascii_colors.handlers
   A namespace providing access to handler classes (e.g., ``handlers.RotatingFileHandler``), similar to ``logging.handlers``.

Formatter Classes
-----------------
Formatters define the structure and content of the final log message string.

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