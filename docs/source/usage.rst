Usage Examples
==============

Core Concepts
-------------

``ascii_colors`` provides two distinct ways to output styled text:

1.  **Direct Print Methods** (`ASCIIColors.red`, `print`, `bold`, `bg_red`, etc.):
    *   Print **directly** to the console (`sys.stdout` by default).
    *   **Bypass the logging system**.
    *   Use for simple, immediate, styled terminal output.

2.  **Logging System** (`basicConfig`, `getLogger`, `logger.info`, `ASCIIColors.info`, Handlers, Formatters):
    *   Structured, leveled logging.
    *   Processed by **Handlers** (Console, File, etc.).
    *   Formatted by **Formatters** (Timestamps, levels, source info, context).
    *   Filtered by **levels**.
    *   Use the familiar `getLogger()` API or the `ASCIIColors` class methods.

Direct Printing Examples
------------------------

.. code-block:: python

    from ascii_colors import ASCIIColors

    # Styles
    ASCIIColors.bold("Bold Text")
    ASCIIColors.underline("Underlined Text", color=ASCIIColors.color_yellow)
    ASCIIColors.italic("Italic Magenta", color=ASCIIColors.color_magenta)

    # Backgrounds
    ASCIIColors.bg_yellow("Black text on Yellow", color=ASCIIColors.color_black)

    # Combine
    ASCIIColors.print(
        " Bold, Underlined, Bright Red ",
        color=ASCIIColors.color_bright_red,
        style=ASCIIColors.style_bold + ASCIIColors.style_underline
    )

    # Multicolor
    ASCIIColors.multicolor(
        ["File: ", "config.yaml", " | Status: ", "LOADED"],
        [ASCIIColors.color_white, ASCIIColors.color_cyan, ASCIIColors.color_white, ASCIIColors.color_green]
    )

    # Highlight
    log_line = "INFO: User 'test' logged out."
    ASCIIColors.highlight(log_line, ["INFO", "test", "logged out"],
                          highlight_color=ASCIIColors.color_bright_yellow)

Logging System Examples
-----------------------

**Setup with basicConfig**

.. code-block:: python

    import ascii_colors as logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("MyApp")
    logger.info("Basic config in use.")

**Manual Setup**

.. code-block:: python

    from ascii_colors import ASCIIColors, LogLevel, ConsoleHandler, Formatter
    import sys

    ASCIIColors.clear_handlers()
    ASCIIColors.set_log_level(LogLevel.DEBUG)
    fmt = Formatter("[{levelname}] {message}", style='{')
    handler = ConsoleHandler(level=LogLevel.INFO, stream=sys.stdout, formatter=fmt)
    ASCIIColors.add_handler(handler)
    # ... add more handlers ...

**Logging Messages**

.. code-block:: python

    logger.info("Processing file '%s' for user %d", "data.csv", 123)
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("Division failed") # Includes traceback


Context Management
------------------

.. code-block:: python

    from ascii_colors import ASCIIColors, getLogger
    import threading

    # Assumes handler/formatter using context keys is set up
    logger = getLogger("WebApp")

    def process_request(req_id, user):
        with ASCIIColors.context(request_id=req_id, user=user):
            logger.info("Processing started.")
            # ... work ...
            logger.info("Processing finished.")

    t1 = threading.Thread(target=process_request, args=("req-001", "alice"))
    t1.start()
    t1.join()


Utilities
---------

**Animation**

.. code-block:: python

    import time
    from ascii_colors import ASCIIColors

    def simulate_work(duration):
        time.sleep(duration)
        return "Data processed!"

    result = ASCIIColors.execute_with_animation("Processing...", simulate_work, 1)
    ASCIIColors.success(f"Work result: {result}")

**Trace Exception**

.. code-block:: python

    from ascii_colors import trace_exception

    try:
        1 / 0
    except ZeroDivisionError as e:
        trace_exception(e) # Logs ERROR with traceback