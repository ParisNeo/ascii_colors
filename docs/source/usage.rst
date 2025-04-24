Usage Examples
==============

Core Concepts: Direct Print vs. Logging
---------------------------------------

``ascii_colors`` offers two distinct ways to output styled text to the terminal:

1.  **Direct Print Methods** (`ASCIIColors.red`, `print`, `bold`, `bg_red`, etc.):
    *   Print **directly** to the console (default: `sys.stdout`) using the built-in `print` function.
    *   They **bypass the logging system entirely**. Levels, handlers, formatters, and context are **not** involved.
    *   Color and style are applied immediately as specified in the method call.
    *   Use these for simple, immediate, styled terminal output like status messages, prompts, banners, or decorative elements where structured logging is not required.

2.  **Logging System** (`basicConfig`, `getLogger`, `logger.info`, `ASCIIColors.info`, Handlers, Formatters):
    *   Provides structured, leveled logging similar to Python's standard `logging` module.
    *   Messages are created as records and processed by **Handlers** (`StreamHandler`, `FileHandler`, `RotatingFileHandler`, etc.) which direct the output (e.g., to console, files).
    *   Output format is controlled by **Formatters** (`Formatter`, `JSONFormatter`), allowing customization with timestamps, levels, source info, thread names, logger names, and custom context variables.
    *   Messages are filtered based on **global and handler-specific levels**.
    *   Console output color in the default `ConsoleHandler` is typically determined by the **log level** (e.g., warnings yellow, errors red).
    *   You can interact with this system using:
        *   **The `logging`-compatible API:** `import ascii_colors as logging`, then use `logging.getLogger()`, `logging.basicConfig()`, `logger.info()`, etc. **This is the recommended approach** for familiarity and best practice.
        *   **The `ASCIIColors` class methods:** `ASCIIColors.info()`, `ASCIIColors.warning()`, `ASCIIColors.add_handler()`, etc. Both APIs control the *same underlying global state* (handlers, levels, formatters).

Utilities like `highlight`, `multicolor`, and `execute_with_animation` use **direct printing**. The `trace_exception` utility uses the **logging system** (`ASCIIColors.error`).

Using the Logging Compatibility Layer (`import ascii_colors as logging`)
--------------------------------------------------------------------------

The most straightforward way to use the logging features is by importing the library with a familiar alias:

.. code-block:: python

    import ascii_colors as logging

    # Now you can use standard logging functions and constants:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

    logger = logging.getLogger('MyModule')

    logger.debug("This won't be shown (level is INFO)")
    logger.info("This will be shown.")
    logger.warning("A potential issue.")

This provides a near drop-in replacement for the standard `logging` module for many common use cases, while benefiting from `ascii_colors`'s built-in colored console output (via the default `ConsoleHandler`).

Available Colors and Styles (for Direct Printing)
-------------------------------------------------

You can use these constants directly from the `ASCIIColors` class when using direct print methods like `ASCIIColors.print()`, `ASCIIColors.bold()`, `ASCIIColors.bg_red()`, `ASCIIColors.multicolor()`, etc.

**Reset Code:**

*   `ASCIIColors.color_reset`: Resets all styles and colors to the terminal default.

**Text Styles:**

*   `ASCIIColors.style_bold`
*   `ASCIIColors.style_dim`
*   `ASCIIColors.style_italic`
*   `ASCIIColors.style_underline`
*   `ASCIIColors.style_blink` (support varies)
*   `ASCIIColors.style_reverse` (swaps foreground/background)
*   `ASCIIColors.style_hidden` (conceals text, useful for passwords; support varies)
*   `ASCIIColors.style_strikethrough`

**Foreground Colors (Regular):**

*   `ASCIIColors.color_black`
*   `ASCIIColors.color_red`
*   `ASCIIColors.color_green`
*   `ASCIIColors.color_yellow`
*   `ASCIIColors.color_blue`
*   `ASCIIColors.color_magenta`
*   `ASCIIColors.color_cyan`
*   `ASCIIColors.color_white`
*   `ASCIIColors.color_orange` (approximation using 256 colors)

**Foreground Colors (Bright):**

*   `ASCIIColors.color_bright_black` (often appears as gray)
*   `ASCIIColors.color_bright_red`
*   `ASCIIColors.color_bright_green`
*   `ASCIIColors.color_bright_yellow`
*   `ASCIIColors.color_bright_blue`
*   `ASCIIColors.color_bright_magenta`
*   `ASCIIColors.color_bright_cyan`
*   `ASCIIColors.color_bright_white`

**Background Colors (Regular):**

*   `ASCIIColors.bg_black`
*   `ASCIIColors.bg_red`
*   `ASCIIColors.bg_green`
*   `ASCIIColors.bg_yellow`
*   `ASCIIColors.bg_blue`
*   `ASCIIColors.bg_magenta`
*   `ASCIIColors.bg_cyan`
*   `ASCIIColors.bg_white`
*   `ASCIIColors.bg_orange` (approximation using 256 colors)

**Background Colors (Bright):**

*   `ASCIIColors.bg_bright_black`
*   `ASCIIColors.bg_bright_red`
*   `ASCIIColors.bg_bright_green`
*   `ASCIIColors.bg_bright_yellow`
*   `ASCIIColors.bg_bright_blue`
*   `ASCIIColors.bg_bright_magenta`
*   `ASCIIColors.bg_bright_cyan`
*   `ASCIIColors.bg_bright_white`

Direct Printing Examples
------------------------

.. code-block:: python

    from ascii_colors import ASCIIColors

    # Styles
    ASCIIColors.bold("Bold Text")
    ASCIIColors.underline("Underlined Text", color=ASCIIColors.color_yellow)
    ASCIIColors.italic("Italic Magenta", color=ASCIIColors.color_magenta)
    ASCIIColors.dim("Dimmed text")
    ASCIIColors.strikethrough("Strikethrough text")

    # Backgrounds
    ASCIIColors.bg_yellow("Black text on Yellow", color=ASCIIColors.color_black)
    ASCIIColors.bg_bright_blue("White text on bright blue", color=ASCIIColors.color_white)

    # Combine styles, colors, and backgrounds
    ASCIIColors.print(
        " Bold, Underlined, Bright Red on Cyan Background ",
        color=ASCIIColors.color_bright_red,
        style=ASCIIColors.style_bold + ASCIIColors.style_underline,
        background=ASCIIColors.bg_cyan # Use the background parameter
    )
    # Or using print_with_bg helper
    ASCIIColors.print_with_bg(
        " Bold Red on Bright White BG ",
        color=ASCIIColors.color_red,
        background=ASCIIColors.bg_bright_white,
        style=ASCIIColors.style_bold
    )

    # Multicolor
    ASCIIColors.multicolor(
        ["File: ", "config.yaml", " | Status: ", "LOADED", " | Valid: ", "Yes"],
        [
            ASCIIColors.color_white, ASCIIColors.color_cyan,
            ASCIIColors.color_white, ASCIIColors.color_green,
            ASCIIColors.color_white, ASCIIColors.color_bright_green
        ]
    )

    # Highlight
    log_line = "INFO: User 'test' logged out successfully from 192.168.1.10."
    ASCIIColors.highlight(log_line, ["INFO", "test", "successfully", "192.168.1.10"],
                          color=ASCIIColors.color_white, # Base color
                          highlight_color=ASCIIColors.color_bright_yellow + ASCIIColors.style_bold)

Logging System Examples
-----------------------

**Setup with basicConfig**

This is the simplest way to get started with logging. It configures a root logger, sets the level, and adds a handler (default: `StreamHandler` to `stderr`).

.. code-block:: python

    import ascii_colors as logging
    import sys

    # Log INFO and above to stdout with a specific format
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout, # Default is stderr
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger("MyApp")
    logger.info("Basic config in use, logging to stdout.")
    logger.debug("This debug message won't appear.")

**Manual Setup for More Control**

Allows configuring multiple handlers with different levels and formatters.

.. code-block:: python

    # Use the logging alias for consistency
    import ascii_colors as logging
    from ascii_colors import handlers # Access RotatingFileHandler etc.
    import sys
    from pathlib import Path

    # --- Reset state if re-configuring ---
    logging.getLogger().handlers.clear() # Clear handlers from root logger
    # Alternatively use basicConfig(force=True) if starting over

    # --- Set global level (optional, handlers can override) ---
    logging.getLogger().setLevel(logging.DEBUG) # Let DEBUG messages pass to handlers

    # --- Configure Handlers ---
    # 1. Console Handler (Colored, simple format, INFO+, to stdout)
    console_fmt = logging.Formatter("[{levelname}] {message}", style='{')
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_fmt)
    logging.getLogger().addHandler(console_handler)

    # 2. File Handler (Detailed format, DEBUG+, to app.log)
    log_file = Path("app.log")
    file_fmt = logging.Formatter(
        fmt="%(asctime)s|%(levelname)-8s|%(name)s:%(lineno)d|%(threadName)s|%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        style='%',
        include_source=True # Enable source info capture
    )
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_fmt)
    logging.getLogger().addHandler(file_handler)

    # 3. Rotating File Handler (JSON Format, WARNING+, to service.jsonl)
    service_log = Path("service.jsonl")
    json_fmt = logging.JSONFormatter(
        include_fields=["timestamp", "levelname", "name", "message", "process", "threadName", "user_id", "request_id"],
        datefmt="iso", # Use ISO 8601 format for timestamps
        json_ensure_ascii=False
    )
    rotating_handler = handlers.RotatingFileHandler(
        service_log,
        maxBytes=1024 * 100, # 100 KB rotation size
        backupCount=3,      # Keep 3 backup files
        encoding='utf-8'
    )
    rotating_handler.setLevel(logging.WARNING)
    rotating_handler.setFormatter(json_fmt)
    logging.getLogger().addHandler(rotating_handler)


    # --- Logging Messages ---
    logger = logging.getLogger("ComplexApp")

    logger.debug("Detailed trace for developers.") # Goes only to file_handler
    logger.info("User action completed.")         # Goes to console_handler and file_handler
    logger.warning("Potential configuration issue.") # Goes to all handlers
    # Log with extra context for the JSON handler
    logger.error("Data validation failed.", extra={'user_id': 'user123', 'request_id': 'req-abc'})


**Logging Messages**

.. code-block:: python

    # Assuming logger is configured as above
    import ascii_colors as logging
    logger = logging.getLogger("MyApp") # Get the same logger instance

    # Standard logging methods
    logger.info("Processing file '%s' for user %d", "data.csv", 123) # %-args
    logger.warning("Disk space low: %d%% remaining", 15)

    # Logging exceptions
    try:
        config = {}
        val = config['missing_key']
    except KeyError:
        logger.error("Configuration key missing!", exc_info=True)
        # OR logger.exception("Configuration key missing!")

    logger.critical("Unrecoverable error detected!")

Context Management
------------------

Easily add thread-local context to log records. The formatter needs to include the context keys (e.g., `{request_id}`).

.. code-block:: python

    import ascii_colors as logging
    from ascii_colors import ASCIIColors # Need ASCIIColors for context()
    import threading
    import time
    import sys

    # Setup formatter to include context keys 'request_id' and 'user'
    fmt = logging.Formatter(
        "[{asctime}] ({name}) [Req:{request_id}|User:{user}] {levelname}: {message}",
        style='{', datefmt='%H:%M:%S'
    )
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(fmt)
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True) # Configure with handler

    logger = logging.getLogger("WebApp")

    def process_request(req_id, user):
        # Use the context manager - context is automatically cleared on exit
        with ASCIIColors.context(request_id=req_id, user=user):
            logger.info("Processing started.")
            time.sleep(0.1)
            if user == "admin":
                logger.warning("Admin user action.")
            logger.info("Processing finished.")

    t1 = threading.Thread(target=process_request, args=("req-001", "alice"))
    t2 = threading.Thread(target=process_request, args=("req-002", "bob"))
    t3 = threading.Thread(target=process_request, args=("req-003", "admin"))
    t1.start(); t2.start(); t3.start()
    t1.join(); t2.join(); t3.join()

    # Context 'request_id' and 'user' are automatically included in logs from within the 'with' block


Utilities
---------

**Animation Spinner**

Displays a spinner during function execution (uses **direct printing**).

.. code-block:: python

    import time
    from ascii_colors import ASCIIColors

    def simulate_long_work(duration):
        # Note: Logs from inside this function will use the configured logging system
        # but won't interfere with the direct-printed spinner line.
        ASCIIColors.info(f"Task started inside animation, duration: {duration}s")
        time.sleep(duration)
        if duration > 2:
             raise ValueError("Task took too long!")
        return f"Work completed in {duration}s!"

    try:
        result = ASCIIColors.execute_with_animation(
            "Processing data...", # Text displayed next to spinner
            simulate_long_work,   # Function to execute
            1.5,                  # *args for the function
            color=ASCIIColors.color_cyan # Color for the pending text
        )
        # Use direct print for success/failure message relating to the animation call itself
        ASCIIColors.success(f"Animation Success: {result}")
    except Exception as e:
        ASCIIColors.fail(f"Animation Failed: {e}")
        # Optionally log the exception using the logging system
        # import ascii_colors as logging
        # logging.getLogger().exception("Animation task failed")

**Trace Exception**

Logs an exception with its traceback using the logging system at the `ERROR` level.

.. code-block:: python

    import ascii_colors as logging
    from ascii_colors import trace_exception

    # Assumes logging is configured (e.g., via basicConfig)
    logging.basicConfig(level=logging.INFO)

    try:
        x = 1 / 0
    except ZeroDivisionError as e:
        # Instead of logger.error(..., exc_info=True) or logger.exception()
        trace_exception(e) # Logs the error message and full traceback