===========
Quick Start
===========

Get up and running with ``ascii_colors`` in minutes.

**Option 1: Logging (Recommended)**
-----------------------------------

This is the preferred method for structured, leveled application logs. It leverages the `logging`-compatible API.

.. important::
   The key is to import the library with a familiar alias:
   ``import ascii_colors as logging``

.. code-block:: python
   :caption: quickstart_logging.py
   :linenos:

   # Use ascii_colors with a logging-like interface
   import ascii_colors as logging # <-- Use alias for familiarity!
   from pathlib import Path
   import sys

   # --- Configuration ---
   # Configure logging (only runs once unless force=True)
   log_file = Path("my_app.log")
   logging.basicConfig(
       level=logging.DEBUG, # Set the root logging level
       # Use standard %-style formatting for console
       format='%(asctime)s [%(levelname)-8s] %(name)s: %(message)s (%(filename)s:%(lineno)d)',
       datefmt='%Y-%m-%d %H:%M:%S',
       # By default, basicConfig adds a StreamHandler to stderr.
       # Override the default stream:
       stream=sys.stdout
   )

   # Add a file handler with a different format and level
   file_formatter = logging.Formatter('%(asctime)s|%(levelname)s|%(name)s|%(message)s')
   file_handler = logging.FileHandler(log_file, mode='w')
   file_handler.setLevel(logging.INFO) # Log only INFO and above to the file
   file_handler.setFormatter(file_formatter)
   logging.getLogger().addHandler(file_handler) # Add handler to the root logger

   # --- Usage ---
   # Get a logger instance (like standard logging)
   logger = logging.getLogger("MyApp")

   # Log messages at different levels
   logger.debug("Debug information: connection established.") # To stdout only
   logger.info("Application starting up...")                 # To stdout and file
   logger.warning("Config setting 'backup_enabled' not found.") # To stdout and file

   user = "Alice"
   logger.info("User '%s' logged in.", user) # Supports %-formatting arguments

   try:
       result = 10 / 0
   except ZeroDivisionError:
       # logger.error() with exc_info=True logs the error and traceback
       logger.error("Critical calculation failed!", exc_info=True)
       # logger.exception() is a shorthand for error() inside except blocks
       # logger.exception("Critical calculation failed!")

   logger.critical("System integrity compromised!") # To stdout and file

   print(f"\nCheck console output (stdout) and the log file '{log_file}'")

**Option 2: Direct Printing**
-----------------------------

Use these methods for simple, immediate styled output directly to the console. They **do not** use the logging system (handlers, levels, formatters).

.. code-block:: python
   :caption: quickstart_direct_print.py
   :linenos:

   from ascii_colors import ASCIIColors

   # Direct print methods bypass the logging system
   ASCIIColors.red("This is an urgent error message.")
   ASCIIColors.green("Operation completed successfully!")
   ASCIIColors.yellow("Warning: Disk space low.")

   # Combine with styles and specific colors
   ASCIIColors.bold("This is important!", color=ASCIIColors.color_bright_white)
   ASCIIColors.underline("Underlined text.", color=ASCIIColors.color_cyan)
   ASCIIColors.italic("Italic blue text.", color=ASCIIColors.color_blue)

   # Use background colors
   ASCIIColors.print_with_bg(
       " Black text on Orange background ",
       color=ASCIIColors.color_black,
       background=ASCIIColors.bg_orange
   )

   # Combine foreground, background, and style
   ASCIIColors.print(
       " Bold Red text on Yellow background ",
       color=ASCIIColors.color_red,
       style=ASCIIColors.style_bold,
       background=ASCIIColors.bg_yellow
   )