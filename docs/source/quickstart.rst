Quick Start
===========

**Option 1: Logging (Recommended for structured logs)**

.. code-block:: python

    # Use ascii_colors with a logging-like interface
    import ascii_colors as logging # Use alias for familiarity
    from pathlib import Path

    # Configure logging (only runs once unless force=True)
    log_file = Path("my_app.log")
    logging.basicConfig(
        level=logging.DEBUG, # Set the root level
        # Use standard %-style formatting
        format='%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    # Add file handler separately if needed
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setFormatter(logging.Formatter('%(asctime)s|%(levelname)s|%(message)s'))
    logging.getLogger().addHandler(file_handler)

    # Get a logger instance
    logger = logging.getLogger("MyApp")

    # Log messages
    logger.info("Application starting...")
    logger.debug("Configuration loaded.")
    logger.warning("Settings value missing, using default.")
    user = "Alice"
    logger.info("User '%s' logged in.", user)

    try:
        result = 10 / 0
    except ZeroDivisionError:
        logger.error("Calculation failed!", exc_info=True)

    print(f"\nCheck console output (stderr) and '{log_file}'")


**Option 2: Direct Printing (For simple, immediate styled output)**

.. code-block:: python

    from ascii_colors import ASCIIColors

    # These print directly to stdout and bypass the logging system
    ASCIIColors.red("This is an urgent error message.")
    ASCIIColors.green("Operation completed successfully!")
    ASCIIColors.yellow("Warning: Disk space low.")
    ASCIIColors.bold("This is important!", color=ASCIIColors.color_bright_white)
    ASCIIColors.underline("Underlined text.", color=ASCIIColors.color_cyan)
    ASCIIColors.print_with_bg(
        " Black text on Orange background ",
        color=ASCIIColors.color_black,
        background=ASCIIColors.bg_orange
    )