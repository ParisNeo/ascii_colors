Usage Guide
===========

This guide covers the main features of ascii_colors, from basic colored output to advanced logging and interactive prompts.

Basic Colored Output
--------------------

The simplest way to use ascii_colors is for direct colored printing:

.. code-block:: python

    from ascii_colors import ASCIIColors

    # Simple colored output
    ASCIIColors.red("This is red text")
    ASCIIColors.green("This is green text")
    ASCIIColors.yellow("This is yellow text")

    # Combining styles
    ASCIIColors.print("Bold and blue", color=ASCIIColors.color_blue, style=ASCIIColors.style_bold)

    # Available colors and styles
    ASCIIColors.cyan("Cyan text")
    ASCIIColors.magenta("Magenta text")
    ASCIIColors.orange("Orange text (256-color)")
    ASCIIColors.bold("Bold text")
    ASCIIColors.italic("Italic text")

Advanced Printing Features
--------------------------

Multicolor Text
~~~~~~~~~~~~~~~

Print text with multiple colors in one call:

.. code-block:: python

    ASCIIColors.multicolor(
        ["Hello ", "World", "!"],
        [ASCIIColors.color_green, ASCIIColors.color_yellow, ASCIIColors.color_red]
    )

Text Highlighting
~~~~~~~~~~~~~~~~~

Highlight specific words or patterns in text:

.. code-block:: python

    # Highlight specific words
    ASCIIColors.highlight(
        "Error: File not found in /path/to/file",
        subtext=["Error", "not found"],
        highlight_color=ASCIIColors.color_red
    )

    # Highlight entire lines containing pattern
    ASCIIColors.highlight(
        "line1: normal\nline2: ERROR occurred\nline3: normal",
        subtext="ERROR",
        whole_line=True,
        highlight_color=ASCIIColors.color_bright_red
    )

Composed Effects
~~~~~~~~~~~~~~~~

Combine multiple effects by nesting calls:

.. code-block:: python

    # Bold green text
    bold_green = ASCIIColors.green("Success!", emit=False, end="")
    ASCIIColors.bold(bold_green)  # Or use print with both parameters

Interactive Features
--------------------

Progress Bars
~~~~~~~~~~~~~

Create beautiful progress bars similar to tqdm:

.. code-block:: python

    from ascii_colors import ProgressBar
    import time

    # Wrap an iterable
    for i in ProgressBar(range(100), desc="Processing"):
        time.sleep(0.01)

    # Manual control
    with ProgressBar(total=100, desc="Uploading", color=ASCIIColors.color_cyan) as pbar:
        for chunk in upload_chunks():
            pbar.update(len(chunk))

    # Custom styling
    pbar = ProgressBar(
        range(50),
        desc="Custom",
        progress_char="█",
        empty_char="░",
        bar_style="fill"  # or "line"
    )

Interactive Menus
~~~~~~~~~~~~~~~~~

Create interactive terminal menus with keyboard navigation:

.. code-block:: python

    from ascii_colors import Menu

    # Simple action menu
    def action_one():
        print("Action one executed!")

    def action_two():
        print("Action two executed!")

    menu = Menu("Main Menu")
    menu.add_action("Run Action One", action_one)
    menu.add_action("Run Action Two", action_two)
    menu.add_action("Exit", lambda: exit())

    menu.run()

    # Choice menu (returns selected value)
    menu = Menu("Select an option", mode='return')
    menu.add_choice("Option A", value="a")
    menu.add_choice("Option B", value="b")
    menu.add_choices([
        ("Option C", "c"),
        ("Option D", "d")
    ])

    result = menu.run()  # Returns "a", "b", "c", or "d"

    # With filtering
    menu = Menu("Search", enable_filtering=True)
    menu.add_action("Apple", lambda: None)
    menu.add_action("Banana", lambda: None)
    menu.add_action("Cherry", lambda: None)
    # User can type to filter items

    # Submenus
    sub_menu = Menu("Settings")
    sub_menu.add_action("Option 1", lambda: None)

    main_menu = Menu("Main")
    main_menu.add_submenu("Settings", sub_menu)

Interactive Prompts (Questionary-Compatible)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drop-in replacement for the `questionary` library with enhanced styling:

.. code-block:: python

    from ascii_colors import questionary  # or: from ascii_colors.questionary import text, confirm, select

    # Text input
    name = questionary.text("What's your name?", default="Anonymous").ask()

    # Password (hidden input with optional confirmation)
    password = questionary.password("Enter password", confirm=True).ask()

    # Confirm (yes/no)
    proceed = questionary.confirm("Continue?", default=True).ask()

    # Select from list (with arrow key navigation)
    color = questionary.select(
        "Favorite color?",
        choices=["Red", "Green", "Blue"],
        default="Blue"
    ).ask()

    # Multi-select checkbox
    toppings = questionary.checkbox(
        "Select toppings",
        choices=["Cheese", "Pepperoni", "Mushrooms", "Olives"],
        default=["Cheese"]  # Pre-selected
    ).ask()  # Returns list of selected values

    # Autocomplete
    city = questionary.autocomplete(
        "Enter city",
        choices=["New York", "Los Angeles", "Chicago", "Houston"],
        ignore_case=True,
        match_middle=True
    ).ask()

    # Forms (sequence of questions)
    answers = questionary.form(
        questionary.text("First name"),
        questionary.text("Last name"),
        questionary.confirm("Subscribe to newsletter?", default=False)
    ).ask()
    # Returns: {"First name": "...", "Last name": "...", "Subscribe to newsletter?": True/False}

    # Validation
    from ascii_colors.questionary import Validator, ValidationError

    class EmailValidator(Validator):
        def validate(self, document):
            if "@" not in document:
                raise ValidationError("Please enter a valid email")

    email = questionary.text("Email:", validate=EmailValidator()).ask()

    # Conditional questions with skip_if
    is_company = questionary.confirm("Is this a company account?").ask()

    company_name = questionary.text(
        "Company name:"
    ).skip_if(not is_company, default="N/A").ask()

Direct API (alternative import style):

.. code-block:: python

    from ascii_colors.questionary import text, password, confirm, select, checkbox, autocomplete, form

    # Same usage as above
    name = text("Name?").ask()

Animation and User Feedback
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Execute functions with animation:

.. code-block:: python

    def long_running_task():
        import time
        time.sleep(2)
        return "Result"

    # Shows spinner animation while function runs
    result = ASCIIColors.execute_with_animation(
        "Processing...",
        long_running_task,
        color=ASCIIColors.color_yellow
    )
    # Prints ✓ on success, ✗ on failure with exception re-raised

Confirmation and Input Helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simple built-in helpers:

.. code-block:: python

    # Yes/No confirmation
    if ASCIIColors.confirm("Delete file?", default_yes=False):
        delete_file()

    # Prompt with styling
    name = ASCIIColors.prompt("Your name: ", color=ASCIIColors.color_green)
    password = ASCIIColors.prompt("Password: ", hide_input=True)

Logging System
--------------

Basic Logging
~~~~~~~~~~~~~

Use the native API or the standard-library-compatible API:

.. code-block:: python

    # Native API
    from ascii_colors import ASCIIColors

    ASCIIColors.set_log_level(ASCIIColors.LogLevel.DEBUG)
    ASCIIColors.debug("Debug message")
    ASCIIColors.info("Info message")
    ASCIIColors.warning("Warning message")
    ASCIIColors.error("Error message")
    ASCIIColors.critical("Critical message")

    # Standard library compatible API
    import logging
    from ascii_colors import getLogger, basicConfig

    basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    logger = getLogger("myapp")

    logger.info("Application started")
    logger.error("An error occurred: %s", error_details)

Contextual Logging
~~~~~~~~~~~~~~~~~~

Add context fields to all log messages in a scope:

.. code-block:: python

    from ascii_colors import ASCIIColors, Formatter

    # Set global context
    ASCIIColors.set_context(user_id="12345", session="abc")

    # Use in formatter
    fmt = Formatter("{asctime} [{levelname}] user={user_id} session={session}: {message}")
    # All logs will now include user_id and session

    # Temporary context (context manager)
    with ASCIIColors.context(request_id="xyz789"):
        ASCIIColors.info("Processing request")  # Includes request_id
    # request_id no longer included

Advanced Formatters
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import Formatter, JSONFormatter

    # Percent style (like standard logging)
    percent_fmt = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Brace style (Python format strings)
    brace_fmt = Formatter("{asctime} [{levelname:>8}] {message}", style='{')

    # Include source location
    source_fmt = Formatter(
        "[{func_name}:{lineno}] {message}",
        include_source=True,
        style='{'
    )

    # JSON output
    json_fmt = JSONFormatter(
        include_fields=["timestamp", "levelname", "name", "message", "user_id"]
    )

File and Rotation Handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import FileHandler, RotatingFileHandler, Formatter

    # Simple file handler
    file_handler = FileHandler(
        "app.log",
        mode='a',  # 'a' for append, 'w' for overwrite
        formatter=Formatter("%(asctime)s - %(message)s")
    )
    ASCIIColors.add_handler(file_handler)

    # Rotating file handler (rotates when file reaches size)
    rotate_handler = RotatingFileHandler(
        "app.log",
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=5,  # Keep 5 backup files
        formatter=Formatter("%(asctime)s - %(message)s")
    )
    ASCIIColors.add_handler(rotate_handler)

Exception Handling
~~~~~~~~~~~~~~~~~~

Format and log exceptions with enhanced tracebacks:

.. code-block:: python

    from ascii_colors import trace_exception, get_trace_exception

    try:
        risky_operation()
    except Exception as e:
        # Log with standard traceback
        trace_exception(e, enhanced=False)

        # Or get enhanced formatted traceback with context
        formatted = get_trace_exception(e, enhanced=True, max_width=120)
        print(formatted)  # Beautiful boxed traceback with local variables

        # Direct logging
        ASCIIColors.error("Operation failed: %s", e, exc_info=True)

Migrating from Standard Logging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Replace `logging` imports with `ascii_colors` equivalents:

.. code-block:: python

    # Before
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("myapp")

    # After
    from ascii_colors import basicConfig, getLogger, INFO
    basicConfig(level=INFO)
    logger = getLogger("myapp")

    # Or use native API for more control
    from ascii_colors import ASCIIColors, ConsoleHandler, FileHandler, Formatter

    ASCIIColors.clear_handlers()
    ASCIIColors.add_handler(ConsoleHandler(formatter=Formatter("{level_name}: {message}")))
    ASCIIColors.add_handler(FileHandler("app.log"))
    ASCIIColors.set_log_level(ASCIIColors.LogLevel.DEBUG)

Thread Safety
~~~~~~~~~~~~~

All logging operations are thread-safe. Context variables are stored per-thread:

.. code-block:: python

    import threading

    def worker(thread_id):
        ASCIIColors.set_context(thread=thread_id)
        ASCIIColors.info("Message from thread")  # Includes correct thread id

    for i in range(5):
        threading.Thread(target=worker, args=(i,)).start()

Configuration Presets
~~~~~~~~~~~~~~~~~~~~~

Common configuration patterns:

.. code-block:: python

    # Development: verbose console output
    from ascii_colors import basicConfig, DEBUG
    basicConfig(
        level=DEBUG,
        format="%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )

    # Production: JSON to file, errors to console
    from ascii_colors import ASCIIColors, JSONFormatter, FileHandler, ConsoleHandler

    ASCIIColors.add_handler(FileHandler(
        "app.jsonl",
        formatter=JSONFormatter(include_fields=["timestamp", "level", "name", "message"])
    ))
    ASCIIColors.add_handler(ConsoleHandler(
        level=ASCIIColors.LogLevel.WARNING,
        formatter=Formatter("{level_name}: {message}")
    ))
