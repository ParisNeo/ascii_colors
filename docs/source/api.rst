API Reference
=============

Core Classes and Functions
--------------------------

ASCIIColors
~~~~~~~~~~~

The main class for colored output and logging. Inherits all ANSI color constants.

.. autoclass:: ascii_colors.ASCIIColors
   :members:
   :undoc-members:

   .. automethod:: print
   .. automethod:: multicolor
   .. automethod:: highlight
   .. automethod:: execute_with_animation
   .. automethod:: confirm
   .. automethod:: prompt

   **Direct color methods:**
   
   .. automethod:: red
   .. automethod:: green
   .. automethod:: yellow
   .. automethod:: blue
   .. automethod:: magenta
   .. automethod:: cyan
   .. automethod:: white
   .. automethod:: orange
   .. automethod:: bold
   .. automethod:: italic

   **Logging methods:**

   .. automethod:: debug
   .. automethod:: info
   .. automethod:: warning
   .. automethod:: error
   .. automethod:: critical

   **Configuration methods:**

   .. automethod:: set_log_level
   .. automethod:: add_handler
   .. automethod:: remove_handler
   .. automethod:: clear_handlers
   .. automethod:: set_context
   .. automethod:: clear_context
   .. automethod:: context
   .. automethod:: get_thread_context

Constants
~~~~~~~~~

.. autoclass:: ascii_colors.LogLevel
   :members:
   :undoc-members:

   .. autoattribute:: DEBUG
   .. autoattribute:: INFO
   .. autoattribute:: WARNING
   .. autoattribute:: ERROR
   .. autoattribute:: CRITICAL

Level Constants
~~~~~~~~~~~~~~~

.. data:: ascii_colors.DEBUG
   :value: 10

.. data:: ascii_colors.INFO
   :value: 20

.. data:: ascii_colors.WARNING
   :value: 30

.. data:: ascii_colors.ERROR
   :value: 40

.. data:: ascii_colors.CRITICAL
   :value: 50

.. data:: ascii_colors.NOTSET
   :value: 0

ANSI Color Constants
~~~~~~~~~~~~~~~~~~~~

All available as class attributes on ``ASCIIColors``:

**Styles:**
   - ``style_bold``, ``style_dim``, ``style_italic``, ``style_underline``
   - ``style_blink``, ``style_reverse``, ``style_hidden``, ``style_strikethrough``

**Colors:**
   - ``color_black``, ``color_red``, ``color_green``, ``color_yellow``
   - ``color_blue``, ``color_magenta``, ``color_cyan``, ``color_white``, ``color_orange``
   - Bright variants: ``color_bright_*``
   - Background colors: ``color_bg_*`` and ``color_bg_bright_*``

**Reset:**
   - ``color_reset``

Logging Components
------------------

Formatters
~~~~~~~~~~

.. autoclass:: ascii_colors.Formatter
   :members:
   :undoc-members:

   .. automethod:: __init__
   .. automethod:: format
   .. automethod:: format_exception

.. autoclass:: ascii_colors.JSONFormatter
   :members:
   :undoc-members:

   .. automethod:: __init__
   .. automethod:: format

Handlers
~~~~~~~~

.. autoclass:: ascii_colors.Handler
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.ConsoleHandler
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.StreamHandler
   :show-inheritance:

.. autoclass:: ascii_colors.FileHandler
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.RotatingFileHandler
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.handlers
   :members:

Standard Library Compatibility
------------------------------

.. autofunction:: ascii_colors.getLogger

.. autofunction:: ascii_colors.basicConfig

.. autofunction:: ascii_colors.shutdown

.. autofunction:: ascii_colors.trace_exception

.. autofunction:: ascii_colors.get_trace_exception

.. autofunction:: ascii_colors.strip_ansi

Interactive Components
----------------------

ProgressBar
~~~~~~~~~~~

.. autoclass:: ascii_colors.ProgressBar
   :members:
   :undoc-members:

   .. automethod:: __init__
   .. automethod:: update
   .. automethod:: close

Menu System
~~~~~~~~~~~

.. autoclass:: ascii_colors.Menu
   :members:
   :undoc-members:

   .. automethod:: __init__
   .. automethod:: add_action
   .. automethod:: add_submenu
   .. automethod:: add_choice
   .. automethod:: add_choices
   .. automethod:: add_input
   .. automethod:: run

.. autoclass:: ascii_colors.MenuItem
   :members:
   :undoc-members:

Questionary Compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~

Drop-in replacement for the `questionary` library.

.. autoclass:: ascii_colors.questionary.Question
   :members:
   :undoc-members:

   .. automethod:: ask
   .. automethod:: unsafe_ask
   .. automethod:: skip_if

.. autoclass:: ascii_colors.questionary.Text
   :show-inheritance:
   :members:

.. autoclass:: ascii_colors.questionary.Password
   :show-inheritance:
   :members:

.. autoclass:: ascii_colors.questionary.Confirm
   :show-inheritance:
   :members:

.. autoclass:: ascii_colors.questionary.Select
   :show-inheritance:
   :members:

.. autoclass:: ascii_colors.questionary.Checkbox
   :show-inheritance:
   :members:

.. autoclass:: ascii_colors.questionary.Autocomplete
   :show-inheritance:
   :members:

.. autoclass:: ascii_colors.questionary.Form
   :members:
   :undoc-members:

   .. automethod:: ask

Validation
~~~~~~~~~~

.. autoclass:: ascii_colors.questionary.Validator
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.questionary.ValidationError
   :show-inheritance:

Convenience Functions
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: ascii_colors.questionary.text

.. autofunction:: ascii_colors.questionary.password

.. autofunction:: ascii_colors.questionary.confirm

.. autofunction:: ascii_colors.questionary.select

.. autofunction:: ascii_colors.questionary.checkbox

.. autofunction:: ascii_colors.questionary.autocomplete

.. autofunction:: ascii_colors.questionary.form

.. autofunction:: ascii_colors.questionary.ask

Module-Level Access
~~~~~~~~~~~~~~~~~~~

For drop-in replacement of ``questionary``:

.. data:: ascii_colors.questionary
   :type: _QuestionaryModule

   Module-like object with all questionary functions and classes as attributes.

   Example usage::

      from ascii_colors import questionary

      name = questionary.text("Your name?").ask()
      color = questionary.select("Favorite color?", choices=["Red", "Blue"]).ask()

Utility Functions
-----------------

.. autofunction:: ascii_colors.get_trace_exception

   Get a formatted string representation of an exception and its traceback.

   :param ex: The exception to format
   :param enhanced: If True, use enhanced formatting with colors and box drawing
   :param max_width: Maximum width for output (auto-detected if None)
   :return: Formatted traceback string

.. autofunction:: ascii_colors.strip_ansi

   Remove ANSI escape sequences from a string.

   :param text: String potentially containing ANSI codes
   :return: Clean string without ANSI codes

Internal Classes
----------------

These classes are primarily for internal use but may be useful for advanced customization.

.. autoclass:: ascii_colors._AsciiLoggerAdapter
   :members:
   :undoc-members:

   Adapter class that provides the standard logging.Logger interface while using ascii_colors backend.

.. autoclass:: ascii_colors._QuestionaryModule
   :members:
   :undoc-members:

   Module-like object for questionary compatibility.
