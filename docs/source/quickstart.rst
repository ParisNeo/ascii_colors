Quick Start
===========

**Option 1: Logging (Recommended)**

This method uses the `logging`-compatible API for structured, leveled logging.

.. code-block:: python

    # Use ascii_colors with a logging-like interface
    import ascii_colors as logging # <-- Use alias for familiarity!
    from pathlib import Path

    # --- Configuration ---
    # Configure logging (only runs once unless force=True)
    log_file = Path("my_app.log")
    logging.basicConfig(
        level=logging.DEBUG, # Set the root logging level
        # Use standard %-style formatting for console
        format='%(asctime)s [%(levelname)-8s] %(name)s: %(message)s (%(filename)s:%(lineno)d)',
        datefmt='%Y-%m-%d %H:%M:%S',
        # By default, basicConfig adds a StreamHandler to stderr.
        # To add a file handler as well, do it manually *after* basicConfig:
    )

    # Add a file handler with a different format
    file_formatter = logging.Formatter('%(asctime)s|%(levelname)s|%(name)s|%(message)s')
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setFormatter(file_formatter)
    logging.getLogger().addHandler(file_handler) # Add handler to the root logger

    # --- Usage ---
    # Get a logger instance (like standard logging)
    logger = logging.getLogger("MyApp")

    # Log messages at different levels
    logger.debug("Debug information: connection established.")
    logger.info("Application starting up...")
    logger.warning("Configuration setting 'backup_enabled' not found, defaulting to False.")

    user = "Alice"
    logger.info("User '%s' logged in.", user) # Supports %-formatting arguments

    try:
        result = 10 / 0
    except ZeroDivisionError:
        logger.error("Critical calculation failed!", exc_info=True) # exc_info=True adds traceback
        # Or use logger.exception for errors within exception handlers
        # logger.exception("Critical calculation failed!")

    logger.critical("System integrity compromised!")

    print(f"\nCheck console output (stderr) and the log file '{log_file}'")

**Option 2: Direct Printing (For simple, immediate styled output)**

These methods print directly to the console (default: `stdout`) and bypass the logging system (levels, handlers, formatters).

.. code-block:: python

    from ascii_colors import ASCIIColors

    # These print directly to stdout and bypass the logging system
    ASCIIColors.red("This is an urgent error message.")
    ASCIIColors.green("Operation completed successfully!")
    ASCIIColors.yellow("Warning: Disk space low.")
    ASCIIColors.bold("This is important!", color=ASCIIColors.color_bright_white)
    ASCIIColors.underline("Underlined text.", color=ASCIIColors.color_cyan)
    ASCIIColors.italic("Italic blue text.", color=ASCIIColors.color_blue)
    ASCIIColors.print_with_bg(
        " Black text on Orange background ",
        color=ASCIIColors.color_black,
        background=ASCIIColors.bg_orange
    )
    ASCIIColors.print(
        " Bold Red text on Yellow background ",
        color=ASCIIColors.color_red,
        style=ASCIIColors.style_bold,
        background=ASCIIColors.bg_yellow
    )