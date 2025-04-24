==============
Usage Guide
==============

This guide provides detailed examples and explains the core concepts of ``ascii_colors``.

.. _direct-vs-logging:

Core Concepts: Direct Print vs. Logging
---------------------------------------

``ascii_colors`` offers two fundamentally different ways to generate styled terminal output:

.. important:: Understanding this distinction is key to using the library effectively.

   1.  **Direct Print Methods** (`ASCIIColors.red`, `print`, `bold`, `bg_red`, etc.)
       *   **What they do:** Print strings **directly** to a stream (default: `sys.stdout`) using Python's built-in `print` function.
       *   **How they work:** Apply ANSI escape codes for colors and styles *immediately* before printing.
       *   **Logging System:** They **completely bypass** the logging system. Levels, Handlers, Formatters, and Context **are ignored**.
       *   **Use Case:** Best for simple, immediate visual feedback, status messages, user prompts, banners, or decorative output where structured logging isn't needed.

   2.  **Logging System** (`basicConfig`, `getLogger`, `logger.info`, Handlers, Formatters)
       *   **What it does:** Provides a structured, leveled logging framework, similar to Python's standard `logging`.
       *   **How it works:** Log messages are created as `LogRecord`-like objects. They are filtered by level, processed by `Formatter`\ s to create strings, and then sent by `Handler`\ s to destinations (console, files, etc.).
       *   **Styling:** Console output (via `ConsoleHandler`/`StreamHandler`) is typically colored based on the **log level** (e.g., Warnings Yellow, Errors Red) by default. Formatting is highly customizable.
       *   **Interaction:** Use the recommended `logging`-compatible API (`import ascii_colors as logging`) or the `ASCIIColors` class methods (`ASCIIColors.info`, `add_handler`). Both control the same underlying global logging state.
       *   **Use Case:** Ideal for application logs, debugging information, tracing events, and any scenario requiring structured, filterable, and configurable output routing.

.. _logging-compat-layer:

Using the Logging Compatibility Layer (`import ascii_colors as logging`)
--------------------------------------------------------------------------

The most convenient and recommended way to utilize the logging features is through the compatibility layer. It allows you to use familiar functions and patterns from Python's standard `logging` module.

.. code-block:: python
   :caption: using_compat_layer.py
   :linenos:

   import ascii_colors as logging # The crucial import alias

   # Configure using basicConfig (similar to standard logging)
   logging.basicConfig(
       level=logging.INFO, # Set the minimum level to log
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       datefmt='%H:%M:%S'
       # Default handler is StreamHandler to stderr with level-based coloring
   )

   # Get logger instances
   logger = logging.getLogger('MyModule')
   another_logger = logging.getLogger('Another.Component')

   # Log messages using standard methods
   logger.debug("This won't be shown (global level is INFO)")
   logger.info("Module started.")
   another_logger.warning("Something looks suspicious.")
   another_logger.error("Failed to process request.")

   # Benefit: Console output is automatically colored by level!

This approach provides a smooth transition for projects already using standard `logging` or a familiar interface for new projects.

.. _direct-print-colors-styles:

Available Colors and Styles (for Direct Printing)
-------------------------------------------------

These constants are attributes of the :class:`~ascii_colors.ASCIIColors` class. Use them with direct print methods like :meth:`~ascii_colors.ASCIIColors.print`, :meth:`~ascii_colors.ASCIIColors.bold`, :meth:`~ascii_colors.ASCIIColors.bg_red`, :meth:`~ascii_colors.ASCIIColors.multicolor`, etc.

.. note::
   Actual rendering depends on the capabilities of your terminal emulator. Most modern terminals support these styles and basic/bright colors. 256-color support (used for `orange`) is also common but not universal.

**Reset Code**
*************

*   ``ASCIIColors.color_reset``: Resets all styles and colors to the terminal default. Automatically appended by most direct print methods.

**Text Styles**
**************

*   ``ASCIIColors.style_bold``
*   ``ASCIIColors.style_dim``
*   ``ASCIIColors.style_italic``
*   ``ASCIIColors.style_underline``
*   ``ASCIIColors.style_blink`` *(support varies)*
*   ``ASCIIColors.style_reverse`` *(swaps foreground/background)*
*   ``ASCIIColors.style_hidden`` *(conceals text; support varies)*
*   ``ASCIIColors.style_strikethrough``

**Foreground Colors (Regular)**
*******************************

*   ``ASCIIColors.color_black``
*   ``ASCIIColors.color_red``
*   ``ASCIIColors.color_green``
*   ``ASCIIColors.color_yellow``
*   ``ASCIIColors.color_blue``
*   ``ASCIIColors.color_magenta``
*   ``ASCIIColors.color_cyan``
*   ``ASCIIColors.color_white``
*   ``ASCIIColors.color_orange`` *(256-color approximation)*

**Foreground Colors (Bright)**
******************************

*   ``ASCIIColors.color_bright_black`` *(often gray)*
*   ``ASCIIColors.color_bright_red``
*   ``ASCIIColors.color_bright_green``
*   ``ASCIIColors.color_bright_yellow``
*   ``ASCIIColors.color_bright_blue``
*   ``ASCIIColors.color_bright_magenta``
*   ``ASCIIColors.color_bright_cyan``
*   ``ASCIIColors.color_bright_white``

**Background Colors (Regular)**
*******************************

*   ``ASCIIColors.bg_black``
*   ``ASCIIColors.bg_red``
*   ``ASCIIColors.bg_green``
*   ``ASCIIColors.bg_yellow``
*   ``ASCIIColors.bg_blue``
*   ``ASCIIColors.bg_magenta``
*   ``ASCIIColors.bg_cyan``
*   ``ASCIIColors.bg_white``
*   ``ASCIIColors.bg_orange`` *(256-color approximation)*

**Background Colors (Bright)**
******************************

*   ``ASCIIColors.bg_bright_black``
*   ``ASCIIColors.bg_bright_red``
*   ``ASCIIColors.bg_bright_green``
*   ``ASCIIColors.bg_bright_yellow``
*   ``ASCIIColors.bg_bright_blue``
*   ``ASCIIColors.bg_bright_magenta``
*   ``ASCIIColors.bg_bright_cyan``
*   ``ASCIIColors.bg_bright_white``

Direct Printing Examples
------------------------

.. code-block:: python
   :caption: direct_print_examples.py
   :linenos:

   from ascii_colors import ASCIIColors

   # --- Simple Colors ---
   ASCIIColors.red("Error: File not found.")
   ASCIIColors.green("Success: Configuration saved.")
   ASCIIColors.blue("Info: Processing request...")

   # --- Styles ---
   ASCIIColors.bold("Important Announcement")
   ASCIIColors.underline("Section Header", color=ASCIIColors.color_yellow)
   ASCIIColors.italic("Note: This feature is experimental.", color=ASCIIColors.color_magenta)
   ASCIIColors.dim("Less important details.")
   ASCIIColors.strikethrough("Deprecated option.")

   # --- Backgrounds ---
   ASCIIColors.bg_yellow("WARNING", color=ASCIIColors.color_black) # Black text on yellow BG
   ASCIIColors.print_with_bg(
       " Critical Failure! ",
       color=ASCIIColors.color_bright_white,
       background=ASCIIColors.bg_bright_red
   )

   # --- Combining ---
   ASCIIColors.print(
       " Status: OK ",
       color=ASCIIColors.color_black, # Text color
       style=ASCIIColors.style_bold + ASCIIColors.style_reverse, # Bold and Reverse video
       background=ASCIIColors.bg_bright_green # Base background (reversed)
   )

   # --- Multicolor ---
   ASCIIColors.multicolor(
       ["Task: ", "Upload", " | Progress: ", "100%", " | Status: ", "DONE"],
       [
           ASCIIColors.color_white, ASCIIColors.color_cyan,           # Task
           ASCIIColors.color_white, ASCIIColors.color_bright_yellow, # Progress
           ASCIIColors.color_white, ASCIIColors.color_bright_green   # Status
       ]
   )

   # --- Highlight ---
   log_line = "INFO: User 'admin' logged in from 127.0.0.1"
   ASCIIColors.highlight(
       text=log_line,
       subtext=["INFO", "admin", "127.0.0.1"], # Words/phrases to highlight
       color=ASCIIColors.color_white,           # Default text color
       highlight_color=ASCIIColors.bg_blue + ASCIIColors.color_bright_white # Style for highlights
   )

Logging System Examples
-----------------------

**Setup with `basicConfig`**
****************************

The simplest way to configure logging. Ideal for scripts or basic applications.

.. code-block:: python
   :caption: logging_setup_basic.py
   :linenos:

   import ascii_colors as logging
   import sys

   logging.basicConfig(
       level=logging.DEBUG, # Log everything from DEBUG upwards
       stream=sys.stdout,   # Send logs to standard output
       format='%(levelname)s:%(name)s:%(message)s' # Simple format
   )

   logger = logging.getLogger("BasicApp")
   logger.debug("Starting process...")
   logger.info("User interaction needed.")

**Manual Setup for Advanced Control**
*************************************

Provides full control over handlers, formatters, and levels.

.. code-block:: python
   :caption: logging_setup_manual.py
   :linenos:

   import ascii_colors as logging
   from ascii_colors import handlers # Access RotatingFileHandler
   import sys
   from pathlib import Path

   # --- Get the root logger to configure ---
   root_logger = logging.getLogger()

   # --- Clear existing handlers (important if re-configuring) ---
   root_logger.handlers.clear()
   # Alternatively, use: logging.basicConfig(force=True, ...) to reset

   # --- Set overall level for the logger ---
   root_logger.setLevel(logging.DEBUG) # Allow all messages to pass to handlers

   # --- Configure Console Handler ---
   console_formatter = logging.Formatter(
       # Using {}-style formatting
       fmt='[{asctime}] <{name}> {levelname:^8s}: {message}',
       style='{',
       datefmt='%H:%M:%S'
   )
   console_handler = logging.StreamHandler(stream=sys.stdout)
   console_handler.setLevel(logging.INFO) # Console shows INFO and above
   console_handler.setFormatter(console_formatter)
   root_logger.addHandler(console_handler)

   # --- Configure File Handler ---
   log_file = Path("app_detailed.log")
   file_formatter = logging.Formatter(
       # Using %-style formatting with source info
       fmt='%(asctime)s|%(levelname)-8s|%(name)s:%(lineno)d|%(message)s',
       style='%',
       datefmt='%Y-%m-%d %H:%M:%S',
       include_source=True # Capture file/line number (adds overhead)
   )
   file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
   file_handler.setLevel(logging.DEBUG) # File logs everything (DEBUG and above)
   file_handler.setFormatter(file_formatter)
   root_logger.addHandler(file_handler)

   # --- Configure Rotating JSON File Handler ---
   json_log_file = Path("audit.jsonl")
   json_formatter = logging.JSONFormatter(
       # Define the structure of the JSON output
       fmt={
           "ts": "asctime",
           "level": "levelname",
           "logger": "name",
           "msg": "message",
           "req_id": "request_id", # Include custom context
           "user": "user_name",   # Include custom context
           "file": "filename",
           "line": "lineno",
       },
       datefmt="iso", # ISO8601 timestamp format
       style='%', # Style applies to how fmt values are looked up
       json_ensure_ascii=False
   )
   # Use the handlers namespace
   rotating_json_handler = handlers.RotatingFileHandler(
       json_log_file,
       maxBytes=5 * 1024 * 1024, # 5 MB
       backupCount=5,
       encoding='utf-8'
   )
   rotating_json_handler.setLevel(logging.WARNING) # Log WARNING and above as JSON
   rotating_json_handler.setFormatter(json_formatter)
   root_logger.addHandler(rotating_json_handler)


   # --- Now, log messages using any logger ---
   main_logger = logging.getLogger("MainApp")
   util_logger = logging.getLogger("MainApp.Utils")

   main_logger.debug("Low-level detail.") # File only
   util_logger.info("Utility function called.") # Console and File
   main_logger.warning(
       "Possible issue detected.",
       extra={"request_id": "xyz789", "user_name": "guest"} # Add context
   ) # Console, File, and JSON
   main_logger.error(
       "Operation failed!",
       extra={"request_id": "xyz789", "user_name": "admin"}
   ) # Console, File, and JSON

**Logging Messages**
********************

Use standard logger methods.

.. code-block:: python
   :caption: logging_messages.py
   :linenos:

   import ascii_colors as logging

   # Assume logging is configured (e.g., via basicConfig or manual setup)
   logger = logging.getLogger("DataProcessor")

   # Standard levels
   logger.debug("Starting data validation for batch %d.", 101)
   logger.info("Processing %d records.", 5000)
   logger.warning("Record %d has missing field 'email'. Skipping.", 1234)
   logger.error("Failed to connect to database '%s'.", "prod_db")
   logger.critical("Data corruption detected! Halting process.")

   # Logging exceptions
   try:
       data = {}
       value = data['required_key']
   except KeyError as e:
       # Option 1: Log error with traceback automatically
       logger.exception("Missing required data key!")
       # Option 2: Log error manually including traceback
       # logger.error("Missing required data key!", exc_info=True)
       # Option 3: Use the utility function (logs at ERROR level)
       # from ascii_colors import trace_exception
       # trace_exception(e)

Context Management
------------------

Add thread-local context to enrich log records automatically. Formatters must be configured to include the context keys.

.. code-block:: python
   :caption: logging_context.py
   :linenos:

   import ascii_colors as logging
   from ascii_colors import ASCIIColors # Needed for context manager
   import threading
   import time
   import sys
   import random

   # Setup a formatter that includes 'request_id' and 'user'
   log_format = "[{asctime}] Req:{request_id}|User:{user} ({name}) {levelname}: {message}"
   formatter = logging.Formatter(log_format, style='{', datefmt='%H:%M:%S')
   handler = logging.StreamHandler(stream=sys.stdout)
   handler.setFormatter(formatter)
   logging.basicConfig(level=logging.INFO, handlers=[handler], force=True) # Reset config

   logger = logging.getLogger("WebServer")

   def handle_web_request(req_id, user):
       # Use the context manager: sets context vars for this thread's scope
       with ASCIIColors.context(request_id=req_id, user=user):
           logger.info("Request received.")
           # Simulate work
           time.sleep(random.uniform(0.1, 0.3))
           if user == "guest":
               logger.warning("Guest access has limited permissions.")
           logger.info("Request processed successfully.")
           # Context (request_id, user) is automatically cleared upon exiting 'with'

   # Simulate multiple concurrent requests
   threads = []
   for i in range(3):
       user = random.choice(['alice', 'bob', 'guest'])
       req_id = f"req-{i+1:03d}"
       thread = threading.Thread(target=handle_web_request, args=(req_id, user))
       threads.append(thread)
       thread.start()

   for t in threads:
       t.join()

   # Outside the threads/context, the keys are not set
   # logger.info("Finished processing all requests.") # Would cause KeyError if context keys missing

Utilities
---------

**Animation Spinner (`execute_with_animation`)**
*************************************************

Displays a spinner while a function executes. Uses **direct printing** for the spinner itself.

.. code-block:: python
   :caption: utility_animation.py
   :linenos:

   import time
   from ascii_colors import ASCIIColors
   import ascii_colors as logging # For logging within the task

   # Configure logging if the task needs it
   logging.basicConfig(level=logging.INFO, format='%(message)s')

   def simulate_database_query(query_id):
       logging.info(f"[Task {query_id}] Starting query...")
       duration = random.uniform(1, 3)
       time.sleep(duration)
       if random.random() < 0.2: # Simulate occasional failures
           raise ConnectionError(f"DB connection lost during query {query_id}")
       logging.info(f"[Task {query_id}] Query finished.")
       return f"Query {query_id} results (found {random.randint(10,100)} rows)"

   # --- Execute with animation ---
   query_to_run = "Q101"
   try:
       # result = ASCIIColors.execute_with_animation(
       #     pending_text=f"Running database query {query_to_run}...",
       #     func=simulate_database_query,
       #     # *args for func:
       #     query_id=query_to_run,
       #     # Optional color for the pending text:
       #     color=ASCIIColors.color_cyan
       # )
       # Use the direct print methods for the overall status of the animated task
       # ASCIIColors.success(f"Animation completed: {result}")
       # Dummy call for example build without randomness
       ASCIIColors.success("Animation completed: Query Q101 results (...)")

   except Exception as e:
       ASCIIColors.fail(f"Animation failed: {e}")
       # Optionally log the failure using the logging system
       # logging.exception(f"Database query {query_to_run} failed")

**Trace Exception (`trace_exception`)**
***************************************

A convenience function to log an exception and its traceback using the configured logging system at the `ERROR` level.

.. code-block:: python
   :caption: utility_trace_exception.py
   :linenos:

   import ascii_colors as logging
   from ascii_colors import trace_exception

   # Assumes logging is configured
   logging.basicConfig(level=logging.INFO)

   try:
       value = int("not_a_number")
   except ValueError as e:
       # Instead of logger.error("...", exc_info=True) or logger.exception(...)
       trace_exception(e) # Logs the error message and full traceback