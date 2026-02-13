API Reference
=============

Core Classes and Functions
--------------------------

ASCIIColors
~~~~~~~~~~~

The main class for colored output and logging. Provides both direct printing methods and rich integration convenience functions.

.. autoclass:: ascii_colors.ASCIIColors
   :members:
   :undoc-members:

Direct Printing Methods
^^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: print
.. automethod:: multicolor
.. automethod:: highlight
.. automethod:: execute_with_animation
.. automethod:: confirm
.. automethod:: prompt

Color Shortcuts
^^^^^^^^^^^^^^^

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
.. automethod:: underline

Logging Methods
^^^^^^^^^^^^^^^

.. automethod:: debug
.. automethod:: info
.. automethod:: warning
.. automethod:: error
.. automethod:: critical

Configuration Methods
^^^^^^^^^^^^^^^^^^^^^

.. automethod:: set_log_level
.. automethod:: add_handler
.. automethod:: remove_handler
.. automethod:: clear_handlers
.. automethod:: set_context
.. automethod:: clear_context
.. automethod:: context
.. automethod:: get_thread_context

Rich Integration Convenience Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: rich_print
.. automethod:: panel
.. automethod:: table
.. automethod:: tree
.. automethod:: syntax
.. automethod:: markdown
.. automethod:: columns
.. automethod:: rule
.. automethod:: status
.. automethod:: live

Constants
~~~~~~~~~

.. autoclass:: ascii_colors.LogLevel
   :members:
   :undoc-members:

Level Constants
^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^

All available as class attributes on ``ASCIIColors``:

**Styles:**
   - ``style_bold``, ``style_dim``, ``style_italic``, ``style_underline``
   - ``style_blink``, ``style_reverse``, ``style_hidden``, ``style_strikethrough``

**Foreground Colors:**
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

.. autoclass:: ascii_colors.JSONFormatter
   :members:
   :undoc-members:

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

Menu System
~~~~~~~~~~~

.. autoclass:: ascii_colors.Menu
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.MenuItem
   :members:
   :undoc-members:

Rich Integration Module
-----------------------

The ``ascii_colors.rich`` module provides Rich-compatible components.

Rich Module Instance
~~~~~~~~~~~~~~~~~~~~

.. data:: ascii_colors.rich
   :type: RichModule

   Module-like object providing Rich-compatible functionality.

   Example::

      from ascii_colors import rich
      rich.print("[bold red]Hello[/bold red]")
      rich.rule("Section")

Console
~~~~~~~

.. autoclass:: ascii_colors.rich.Console
   :members:
   :undoc-members:

Style and Color
~~~~~~~~~~~~~~~

.. autoclass:: ascii_colors.rich.Style
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.rich.Color
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.rich.BoxStyle
   :members:
   :undoc-members:

Text and Renderables
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ascii_colors.rich.Text
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.rich.Renderable
   :members:
   :undoc-members:

Layout Components
~~~~~~~~~~~~~~~~~

.. autoclass:: ascii_colors.rich.Panel
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.rich.Padding
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.rich.Columns
   :members:
   :undoc-members:

Data Display
~~~~~~~~~~~~

.. autoclass:: ascii_colors.rich.Table
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.rich.Tree
   :members:
   :undoc-members:

Content Components
~~~~~~~~~~~~~~~~~~

.. autoclass:: ascii_colors.rich.Syntax
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.rich.Markdown
   :members:
   :undoc-members:

Live Display
~~~~~~~~~~~~

.. autoclass:: ascii_colors.rich.Live
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.rich.Status
   :members:
   :undoc-members:

Questionary Compatibility
-------------------------

Drop-in replacement for the `questionary` library.

Base Classes
~~~~~~~~~~~~

.. autoclass:: ascii_colors.questionary.Question
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.questionary.Validator
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.questionary.ValidationError
   :show-inheritance:

Question Types
~~~~~~~~~~~~~~

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

   Module-like object with all questionary functions and classes.

   Example::

      from ascii_colors import questionary
      name = questionary.text("Your name?").ask()

Utility Functions
-----------------

.. autofunction:: ascii_colors.get_trace_exception

.. autofunction:: ascii_colors.strip_ansi

Internal Classes
----------------

.. autoclass:: ascii_colors._AsciiLoggerAdapter
   :members:
   :undoc-members:

.. autoclass:: ascii_colors._QuestionaryModule
   :members:
   :undoc-members:

.. autoclass:: ascii_colors.rich.RichModule
   :members:
   :undoc-members:
