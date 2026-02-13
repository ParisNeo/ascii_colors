Basic Usage Guide
=================

This guide covers the fundamental features of ascii_colors: colors, styles, direct printing, progress bars, and interactive menus.

Colors and Styles
-----------------

ASCIIColors provides simple methods for colored terminal output.

Direct Color Methods
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors

    # Standard foreground colors
    ASCIIColors.black("Black text")
    ASCIIColors.red("Red text")
    ASCIIColors.green("Green text")
    ASCIIColors.yellow("Yellow text")
    ASCIIColors.blue("Blue text")
    ASCIIColors.magenta("Magenta text")
    ASCIIColors.cyan("Cyan text")
    ASCIIColors.white("White text")
    ASCIIColors.orange("Orange text (256-color)")

    # Style modifiers
    ASCIIColors.bold("Bold text")
    ASCIIColors.dim("Dim text")
    ASCIIColors.italic("Italic text")
    ASCIIColors.underline("Underlined text")
    ASCIIColors.blink("Blinking text")

The ``print()`` Method
~~~~~~~~~~~~~~~~~~~~~~

Full control over styling:

.. code-block:: python

    from ascii_colors import ASCIIColors

    ASCIIColors.print(
        "Complex styling",
        color=ASCIIColors.color_cyan,
        background=ASCIIColors.color_bg_black,
        style=ASCIIColors.style_bold + ASCIIColors.style_italic,
        end="\n\n",
        flush=True,
        file=sys.stderr
    )

Bright Colors and Backgrounds
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Bright variants
    ASCIIColors.print("Bright red", color=ASCIIColors.color_bright_red)
    ASCIIColors.print("Bright green", color=ASCIIColors.color_bright_green)

    # Background colors
    ASCIIColors.print("Red background", background=ASCIIColors.color_bg_red)
    ASCIIColors.print(
        "Black on bright yellow",
        color=ASCIIColors.color_black,
        background=ASCIIColors.color_bg_bright_yellow
    )

Advanced Printing Features
--------------------------

Multicolor Text
~~~~~~~~~~~~~~~

Print multiple colors in one call:

.. code-block:: python

    ASCIIColors.multicolor(
        ["Status: ", "ACTIVE", " | Load: ", "85%", " | Memory: ", "OK"],
        [
            ASCIIColors.color_white,
            ASCIIColors.color_green,
            ASCIIColors.color_white,
            ASCIIColors.color_yellow,
            ASCIIColors.color_white,
            ASCIIColors.color_green
        ]
    )

Text Highlighting
~~~~~~~~~~~~~~~~~

Highlight patterns in text:

.. code-block:: python

    # Highlight specific words
    ASCIIColors.highlight(
        "ERROR: File not found in /path/to/file",
        subtext=["ERROR", "not found"],
        highlight_color=ASCIIColors.color_bright_red
    )

    # Highlight entire lines
    log_output = """\
    INFO: Server starting...
    ERROR: Database connection failed
    INFO: Retrying...
    ERROR: Max retries exceeded
    """
    ASCIIColors.highlight(
        log_output,
        subtext="ERROR",
        whole_line=True,
        highlight_color=ASCIIColors.color_bg_bright_red
    )

Composed Effects
~~~~~~~~~~~~~~~~

Nest calls for complex styling:

.. code-block:: python

    # Build styled string without printing
    styled = ASCIIColors.green("Success: ", emit=False, end="")
    styled += ASCIIColors.bold("Operation completed", emit=False)
    print(styled)  # Or use ASCIIColors.print(styled)

Progress Bars
-------------

The ``ProgressBar`` class provides ``tqdm``-like progress indication.

Basic Usage
~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ProgressBar
    import time

    # Wrap an iterable
    for item in ProgressBar(range(100), desc="Processing"):
        time.sleep(0.01)

Custom Styling
~~~~~~~~~~~~~~

.. code-block:: python

    # Custom colors and characters
    for item in ProgressBar(
        range(1000),
        desc="Uploading",
        color=ASCIIColors.color_cyan,
        bar_style="fill",
        progress_char="█",
        empty_char="░"
    ):
        process(item)

    # Emoji style
    for item in ProgressBar(
        range(100),
        desc="Building",
        bar_style="emoji",
        progress_char="🚀",
        empty_char="⬛"
    ):
        build_step()

Manual Control
~~~~~~~~~~~~~~

.. code-block:: python

    # Context manager
    with ProgressBar(total=1024*1024, desc="Uploading", unit="B") as pbar:
        while chunk := read_chunk():
            pbar.update(len(chunk))

    # Manual control
    pbar = ProgressBar(total=100, desc="Custom")
    pbar.update(10)
    pbar.update(20)
    pbar.n = 50       # Set absolute position
    pbar.refresh()
    pbar.close()

Interactive Menus
-----------------

Create keyboard-navigable menus with the ``Menu`` class.

Return Mode (Single Selection)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import Menu

    menu = Menu("Choose format", mode='return')
    menu.add_choice("JSON", value="json")
    menu.add_choice("YAML", value="yaml")
    menu.add_choice("XML", value="xml")

    result = menu.run()  # Returns "json", "yaml", or "xml"

Execute Mode (Action Menu)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def show_status():
        ASCIIColors.green("All systems operational")

    def restart_service():
        ASCIIColors.yellow("Restarting...")

    menu = Menu("System Manager", mode='execute')
    menu.add_action("Show Status", show_status)
    menu.add_action("Restart Service", restart_service)
    menu.add_action("Quit", lambda: exit(0))

    menu.run()  # Loops until quit selected

Checkbox Mode (Multi-Selection)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    menu = Menu("Select features", mode='checkbox')
    menu.add_checkbox("Authentication", value="auth", checked=True)
    menu.add_checkbox("Logging", value="logging", checked=True)
    menu.add_checkbox("Caching", value="cache")

    selected = menu.run()  # Returns list like ['auth', 'logging']

Advanced Menu Features
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # With filtering (type to filter choices)
    menu = Menu("Select user", mode='return', enable_filtering=True)
    menu.add_choices([
        ("Alice Anderson", "alice"),
        ("Bob Baker", "bob"),
        ("Charlie Chen", "charlie"),
    ])

    # Submenus
    settings = Menu("Settings")
    settings.add_action("General", lambda: None)

    main = Menu("Main", mode='execute')
    main.add_submenu("Settings", settings)

    # Custom styling
    menu = Menu(
        "Styled Menu",
        pointer="▶",
        selected_icon="●",
        unselected_icon="○"
    )

Utility Functions
-----------------

Execute with Animation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors

    def long_task():
        import time
        time.sleep(3)
        return "result"

    result = ASCIIColors.execute_with_animation(
        "Processing...",
        long_task,
        color=ASCIIColors.color_yellow
    )
    # Shows ✓ on success, ✗ on failure

Confirmation Prompt
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    if ASCIIColors.confirm("Delete this file?", default_yes=False):
        delete_file()

Styled Input Prompt
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    name = ASCIIColors.prompt("Your name: ", color=ASCIIColors.color_green)
    password = ASCIIColors.prompt("Password: ", hide_input=True)

Next Steps
----------

- See :doc:`logging_guide` for the complete logging system
- See :doc:`rich_integration` for advanced UI components (panels, tables, etc.)
- See :doc:`interactive_prompts` for questionary-compatible prompts
- See :doc:`api` for complete API reference
