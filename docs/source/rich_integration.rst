Rich Integration Guide
======================

ASCIIColors provides a complete **Rich-compatible** rendering layer that brings beautiful terminal UI components to your Python applications—**without requiring the Rich library as a dependency**.

This integration is built directly into ASCIIColors using pure Python and ANSI escape codes, giving you:

- 🖼️ **Panels** - Bordered boxes for highlighting content
- 📊 **Tables** - Structured data display with headers and rows
- 🌳 **Trees** - Hierarchical file/directory visualizations
- 🎨 **Syntax Highlighting** - Code display with language-specific colors
- 📝 **Markdown Rendering** - Terminal-friendly markdown
- 📐 **Columns** - Multi-column layouts
- ⏳ **Live Displays** - Real-time updating content
- ✨ **Status Spinners** - Animated progress indicators

Two Ways to Access Rich Features
--------------------------------

Method 1: ``ASCIIColors.*`` Convenience Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest approach—direct methods on the main class:

.. code-block:: python

    from ascii_colors import ASCIIColors

    # Quick panels, tables, trees, etc.
    ASCIIColors.panel("Hello World", title="Greeting")
    ASCIIColors.table("Name", "Age", rows=[["Alice", 30], ["Bob", 25]])
    ASCIIColors.tree("project").add("src").add("tests")

Method 2: ``ascii_colors.rich`` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Full Rich-compatible API with more control:

.. code-block:: python

    from ascii_colors import rich

    # Rich markup printing
    rich.print("[bold magenta]Styled text[/bold magenta]")
    rich.print(Panel("Content", title="Title"))
    rich.rule("Section Divider")

    # Live displays and spinners
    with rich.status("Loading...") as status:
        do_work()

Rich Markup Syntax
------------------

ASCIIColors supports Rich-style markup tags for inline styling:

Basic Tags
~~~~~~~~~~

.. code-block:: python

    from ascii_colors import rich

    # Colors
    rich.print("[red]Error message[/red]")
    rich.print("[green]Success[/green]")
    rich.print("[blue]Information[/blue]")
    rich.print("[yellow]Warning[/yellow]")
    rich.print("[magenta]Accent[/magenta]")
    rich.print("[cyan]Highlight[/cyan]")

    # Styles
    rich.print("[bold]Bold text[/bold]")
    rich.print("[italic]Italic text[/italic]")
    rich.print("[underline]Underlined[/underline]")
    rich.print("[dim]Dimmed text[/dim]")
    rich.print("[blink]Blinking text[/blink]")

    # Combined
    rich.print("[bold red]Bold red error[/bold red]")
    rich.print("[italic green]Italic green success[/italic green]")

Bright Colors
~~~~~~~~~~~~~

.. code-block:: python

    rich.print("[bright_red]Bright red[/bright_red]")
    rich.print("[bright_green]Bright green[/bright_green]")
    rich.print("[bright_blue]Bright blue[/bright_blue]")
    rich.print("[bright_yellow]Bright yellow[/bright_yellow]")
    rich.print("[bright_magenta]Bright magenta[/bright_magenta]")
    rich.print("[bright_cyan]Bright cyan[/bright_cyan]")

Background Colors
~~~~~~~~~~~~~~~~~

Use ``on <color>`` for backgrounds:

.. code-block:: python

    rich.print("[on red]White text on red background[/on red]")
    rich.print("[on green black]Black text on green[/on green black]")
    rich.print("[bold white on blue]Bold white on blue[/bold white on blue]")

Semantic Tags
~~~~~~~~~~~~~

Special tags for common use cases:

.. code-block:: python

    rich.print("[success]Operation completed successfully[/success]")
    rich.print("[error]An error occurred[/error]")
    rich.print("[warning]Warning: deprecated feature[/warning]")
    rich.print("[info]Note: processing started[/info]")
    rich.print("[danger]Critical security issue[/danger]")
    rich.print("[highlight]Important highlight[/highlight]")
    rich.print("[muted]Less important text[/muted]")

Panels
------

Panels create bordered boxes to highlight important content.

Basic Panels
~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich

    # Simple panel
    ASCIIColors.panel("This is important information!")

    # With title
    ASCIIColors.panel("Content goes here", title="Notice")

    # Styled panel
    ASCIIColors.panel(
        "[bold red]Error:[/bold red] Connection failed",
        title="Error",
        border_style="red"
    )

Advanced Panel Options
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich
    from ascii_colors.rich import Panel, BoxStyle

    # Using the rich module for more control
    panel = Panel(
        "Content with [bold]markup[/bold] support",
        title="[bold yellow]Styled Title[/bold yellow]",
        border_style="bold cyan",
        box=BoxStyle.ROUND,           # ROUND, SQUARE, DOUBLE, MINIMAL
        padding=(1, 2),               # (vertical, horizontal)
        width=60                      # Fixed width
    )
    rich.print(panel)

    # Convenience method with all options
    ASCIIColors.panel(
        "Multi-line content\nwith automatic wrapping",
        title="Features",
        border_style="green",
        box="round",
        padding=(2, 4),
        color="green",
        background=""
    )

Panel Box Styles
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Style
     - Appearance
   * - ``SQUARE`` / ``"square"``
     - ┌───┐ │   │ └───┘
   * - ``ROUND`` / ``"round"``
     - ╭───╮ │   │ ╰───╯
   * - ``DOUBLE`` / ``"double"``
     - ╔═══╗ ║   ║ ╚═══╝
   * - ``MINIMAL`` / ``"minimal"``
     - ─────

Tables
------

Display structured data in rows and columns.

Basic Tables
~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich

    # Simple table
    ASCIIColors.table(
        "Name", "Role", "Status",
        rows=[
            ["Alice", "Admin", "[green]Active[/green]"],
            ["Bob", "User", "[green]Active[/green]"],
            ["Carol", "Guest", "[yellow]Pending[/yellow]"]
        ]
    )

    # With title
    ASCIIColors.table(
        "Package", "Version", "License",
        rows=[
            ["numpy", "1.24.0", "BSD"],
            ["pandas", "2.0.0", "BSD"],
            ["requests", "2.28.0", "Apache 2.0"]
        ],
        title="Dependencies"
    )

Advanced Table Styling
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich
    from ascii_colors.rich import Table, BoxStyle

    # Using rich module for full control
    table = Table(
        "Feature", "Status", "Notes",
        title="[bold]Project Status[/bold]",
        header_style="bold cyan",
        show_lines=True,              # Show lines between rows
        box=BoxStyle.ROUND
    )

    # Add rows with mixed styling
    table.add_row(
        "Authentication",
        "[green]✓ Complete[/green]",
        "JWT-based auth implemented"
    )
    table.add_row(
        "Database",
        "[yellow]⚠ In Progress[/yellow]",
        "Migration to PostgreSQL"
    )
    table.add_row(
        "API Docs",
        "[red]✗ Not Started[/red]",
        "Pending Swagger integration"
    )

    rich.print(table)

    # Convenience method with rich markup in cells
    ASCIIColors.table(
        "Service", "Health", "Latency",
        rows=[
            ["API Gateway", "[green]● Healthy[/green]", "12ms"],
            ["Database", "[green]● Healthy[/green]", "45ms"],
            ["Cache", "[yellow]● Degraded[/yellow]", "120ms"],
            ["Queue", "[red]● Down[/red]", "timeout"]
        ],
        header_style="bold",
        show_lines=True
    )

Trees
-----

Display hierarchical structures like file systems or nested data.

Basic Trees
~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich

    # Build and display a tree
    root = ASCIIColors.tree("📁 myproject")
    src = root.add("📁 src")
    src.add("📄 __init__.py")
    src.add("📄 main.py")
    src.add("📁 utils")

    tests = root.add("📁 tests")
    tests.add("📄 test_main.py")
    tests.add("📄 test_utils.py")

    root.add("📄 README.md")
    root.add("📄 pyproject.toml")

    rich.print(root)

Advanced Tree Styling
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich
    from ascii_colors.rich import Tree, Style

    # Styled tree
    tree = Tree(
        "[bold blue]project_root[/bold blue]",
        style=Style(bold=True),
        guide_style=Style(dim=True, color="gray")
    )

    # Add styled nodes
    backend = tree.add("[bold]📁 backend[/bold]")
    backend.add("📄 server.py")
    backend.add("📄 api.py")
    backend.add("📁 models").add("📄 user.py")

    frontend = tree.add("[bold]📁 frontend[/bold]")
    frontend.add("📄 index.html")
    frontend.add("📄 app.js")

    rich.print(tree)

    # Convenience method with style parameter
    tree = ASCIIColors.tree(
        "Root",
        style="bold",
        guide_style="dim"
    )
    child = tree.add("Child 1").add("Grandchild")
    rich.print(tree)

Syntax Highlighting
-------------------

Display code with language-specific colors.

Basic Syntax Highlighting
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich

    # Python code
    code = '''
    def fibonacci(n):
        """Generate Fibonacci sequence."""
        a, b = 0, 1
        for _ in range(n):
            yield a
            a, b = b, a + b

    for num in fibonacci(10):
        print(num)
    '''

    ASCIIColors.syntax(code, language="python", line_numbers=True)

    # JSON data
    json_data = '''{
        "name": "ascii_colors",
        "version": "1.0.0",
        "features": ["colors", "logging", "rich"]
    }'''

    ASCIIColors.syntax(json_data, language="json", line_numbers=False)

Advanced Syntax Options
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import rich
    from ascii_colors.rich import Syntax

    # Full control over syntax display
    syntax = Syntax(
        code="""
        import asyncio

        async def main():
            await asyncio.sleep(1)
            print("Hello, async!")

        asyncio.run(main())
        """,
        lexer="python",
        line_numbers=True,
        line_number_start=1,
        highlight_lines=[4, 5],      # Highlight specific lines
        theme={
            "keyword": "[bold magenta]",
            "string": "[green]",
            "comment": "[dim]",
            "function": "[cyan]"
        }
    )

    rich.print(syntax)

Supported Languages
~~~~~~~~~~~~~~~~~~~

The syntax highlighter includes basic tokenization for:

- ``python`` - Python code
- ``json`` - JSON data
- ``javascript`` / ``js`` - JavaScript
- ``bash`` / ``shell`` - Shell scripts
- ``yaml`` / ``yml`` - YAML files
- ``sql`` - SQL queries
- ``text`` / ``plain`` - Plain text (no highlighting)

Markdown Rendering
------------------

Render Markdown content in the terminal.

Basic Markdown
~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich

    markdown_content = """
    # Heading 1

    ## Heading 2

    This is a paragraph with **bold** and *italic* text.

    - Bullet point 1
    - Bullet point 2

    > This is a blockquote

    ```
    code block here
    ```
    """

    ASCIIColors.markdown(markdown_content)

Advanced Markdown
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import rich
    from ascii_colors.rich import Markdown

    md = Markdown("""
    # API Documentation

    ## Authentication

    All requests require a **Bearer token** in the Authorization header:

        Authorization: Bearer <your_token>

    ## Endpoints

    | Method | Endpoint | Description |
    |--------|----------|-------------|
    | GET | /api/users | List all users |
    | POST | /api/users | Create new user |

    > ⚠️ Rate limiting: 100 requests per minute
    """)

    rich.print(md)

Columns Layout
--------------

Arrange content in multiple columns.

Basic Columns
~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich

    # Display items in columns
    items = [
        "Feature 1: Colors",
        "Feature 2: Styles",
        "Feature 3: Panels",
        "Feature 4: Tables",
        "Feature 5: Trees",
        "Feature 6: Syntax"
    ]

    ASCIIColors.columns(*items)

Advanced Column Options
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import rich
    from ascii_colors.rich import Columns, Text

    # Equal-width columns
    cols = Columns(
        [Text(f"Item {i}") for i in range(1, 10)],
        equal=True,
        width=20
    )
    rich.print(cols)

    # Or using convenience method
    ASCIIColors.columns(
        "Short",
        "Medium length text",
        "This is a longer piece of content",
        equal=True,
        width=25
    )

Rules (Dividers)
----------------

Horizontal dividers with optional titles.

.. code-block:: python

    from ascii_colors import ASCIIColors, rich

    # Simple rule
    ASCIIColors.rule()

    # Rule with title
    ASCIIColors.rule("Section Title", style="cyan")

    # Styled rule with alignment
    ASCIIColors.rule("Centered", style="bold magenta")
    ASCIIColors.rule("Left", align="left", style="yellow")
    ASCIIColors.rule("Right", align="right", style="green")

    # Custom characters
    ASCIIColors.rule("Double", characters="═", style="blue")
    ASCIIColors.rule("Thick", characters="━", style="red")

    # Using rich module
    rich.rule("Using rich.rule()", style="bold cyan")

Live Displays
-------------

Real-time updating content for progress indication.

Basic Live Display
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich
    from ascii_colors.rich import Text
    import time

    # Simple progress with live display
    with ASCIIColors.live("Starting...", refresh_per_second=4) as live:
        for i in range(10):
            time.sleep(0.5)
            bar = "█" * (i + 1) + "░" * (9 - i)
            live.update(Text(f"Progress: [{bar}] {i+1}/10"))

        time.sleep(0.3)
        live.update(Text("[bold green]✓ Complete![/bold green]"))

Advanced Live Display
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import rich
    from ascii_colors.rich import Live, Panel, Table
    import time

    # Live updating table
    table = Table("Task", "Status", "Progress")
    table.add_row("Download", "[yellow]Running[/yellow]", "0%")

    with Live(table, refresh_per_second=2) as live:
        for progress in [25, 50, 75, 100]:
            time.sleep(1)
            table.rows.clear()
            table.add_row(
                "Download",
                "[yellow]Running[/yellow]" if progress < 100 else "[green]Done[/green]",
                f"{progress}%"
            )
            live.update(table)

Status Spinners
---------------

Animated spinners for long-running operations.

Basic Status Spinner
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich
    import time

    # Default dots spinner
    with ASCIIColors.status("Loading data...") as status:
        time.sleep(3)  # Your work here

    # Custom style
    with ASCIIColors.status("Processing", spinner_style="yellow") as status:
        time.sleep(2)

Spinner Styles
~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich
    import time

    # Available spinner animations
    spinners = ["dots", "line", "arrow", "pulse", "star", "moon"]

    for spinner_name in spinners:
        with ASCIIColors.status(
            f"Testing {spinner_name} spinner...",
            spinner=spinner_name,
            spinner_style="cyan"
        ) as status:
            time.sleep(2)

Advanced Status Usage
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import rich
    from ascii_colors.rich import Status
    import time

    # Status with updates
    with rich.status("Connecting...") as status:
        time.sleep(1)
        status.update("Authenticating...")
        time.sleep(1)
        status.update("Fetching data...")
        time.sleep(1)

    # Different spinner speeds
    with ASCIIColors.status("Fast", spinner="dots", speed=2.0) as status:
        time.sleep(2)

Console and Advanced Features
-----------------------------

Direct Console Access
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import rich
    from ascii_colors.rich import Console

    # Custom console instance
    console = Console(width=60, no_color=False)

    console.print("[bold]Narrow console output[/bold]")
    console.rule("Section")
    console.log("Log message with timestamp")

    # Input with styled prompt
    name = console.input("[green]Enter name:[/green] ")

    # Capture output
    with console.capture() as capture:
        console.print("[red]This will be captured[/red]")
        console.print(Panel("Captured content"))

    output = capture.get()

    # Export as text
    text_output = console.export_text()

Combined Examples
-----------------

Dashboard Example
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich
    from ascii_colors.rich import Panel, Table, Columns
    import random

    def show_dashboard():
        # Header
        rich.print("[bold blue]╔══════════════════════════════════════╗[/bold blue]")
        rich.print("[bold blue]║     [/bold blue][bold white]System Dashboard[/bold white][bold blue]              ║[/bold blue]")
        rich.print("[bold blue]╚══════════════════════════════════════╝[/bold blue]")
        rich.print()

        # Stats in panels
        stats = Columns([
            Panel(
                f"[bold green]{random.randint(90, 99)}%[/bold green]\nCPU Usage",
                border_style="green"
            ),
            Panel(
                f"[bold blue]{random.randint(4, 16)}GB[/bold blue]\nMemory",
                border_style="blue"
            ),
            Panel(
                f"[bold yellow]{random.randint(100, 500)}[/bold yellow]\nActive Users",
                border_style="yellow"
            ),
        ], equal=True)

        rich.print(stats)
        rich.print()

        # Service status table
        table = Table(
            "Service", "Status", "Uptime", "Load",
            header_style="bold cyan"
        )

        services = [
            ("API Gateway", "[green]● Healthy[/green]", "99.9%", "12%"),
            ("Database", "[green]● Healthy[/green]", "99.9%", "45%"),
            ("Cache", "[yellow]● Warning[/yellow]", "99.5%", "78%"),
            ("Queue Worker", "[green]● Healthy[/green]", "99.9%", "23%"),
        ]

        for svc in services:
            table.add_row(*svc)

        rich.print(Panel(table, title="[bold]Service Health[/bold]"))
        rich.print()

        # Recent logs
        logs = [
            "[dim]10:42:31[/dim] [green]INFO[/green] Request completed in 45ms",
            "[dim]10:42:30[/dim] [green]INFO[/green] User login: alice@example.com",
            "[dim]10:42:28[/dim] [yellow]WARN[/yellow] Cache miss for key: user:1234",
            "[dim]10:42:25[/dim] [green]INFO[/green] Database connection pool: 8/20",
        ]

        rich.print(Panel(
            "\n".join(logs),
            title="[bold]Recent Logs[/bold]",
            border_style="dim"
        ))

Progress with Rich Components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import ASCIIColors, rich
    from ascii_colors.rich import Live, Panel, Text
    import time

    def process_with_visualization():
        tasks = [
            ("Loading configuration", 2),
            ("Connecting to database", 3),
            ("Fetching user data", 2),
            ("Processing analytics", 4),
            ("Generating report", 2),
        ]

        total_time = sum(t for _, t in tasks)
        current_time = 0

        with ASCIIColors.live(
            Panel("Starting...", title="[bold]Task Progress[/bold]"),
            refresh_per_second=2
        ) as live:

            for task_name, duration in tasks:
                start_time = time.time()

                while time.time() - start_time < duration:
                    elapsed = time.time() - start_time
                    progress = elapsed / duration
                    bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))

                    current_time += elapsed

                    content = f"""
    [bold cyan]{task_name}[/bold cyan]
    [{bar}] {int(progress * 100)}%

    Overall: [{current_time:.1f}s / {total_time}s]
                    """.strip()

                    live.update(Panel(
                        content,
                        title="[bold]Task Progress[/bold]",
                        border_style="cyan"
                    ))

                    time.sleep(0.1)

        rich.print("[bold green]✓ All tasks completed![/bold green]")

Best Practices
--------------

1. **Use convenience methods for simple cases** - ``ASCIIColors.panel()``, ``ASCIIColors.table()``

2. **Use rich module for complex layouts** - When you need precise control over styling and layout

3. **Prefer markup over manual ANSI codes** - ``[red]text[/red]`` is more readable than manual escape sequences

4. **Combine components** - Panels inside tables, tables inside panels, trees with styled nodes

5. **Use live displays for progress** - Keep users informed during long operations

6. **Keep terminal width in mind** - Use ``Console(width=...)`` or check ``shutil.get_terminal_size()``

7. **Test with ``no_color=True``** - Ensure output is still readable without colors

Migration from Rich
-------------------

ASCIIColors' rich compatibility is designed to feel familiar to Rich users:

+-------------------------+-------------------------+
| Rich                    | ASCIIColors             |
+=========================+=========================+
| ``from rich import *``  | ``from ascii_colors     |
|                         | import rich``           |
+-------------------------+-------------------------+
| ``rich.print()``        | ``rich.print()`` ✓      |
+-------------------------+-------------------------+
| ``Panel()``             | ``rich.Panel()`` ✓      |
+-------------------------+-------------------------+
| ``Table()``             | ``rich.Table()`` ✓      |
+-------------------------+-------------------------+
| ``Tree()``              | ``rich.Tree()`` ✓       |
+-------------------------+-------------------------+
| ``Syntax()``            | ``rich.Syntax()`` ✓     |
+-------------------------+-------------------------+
| ``Markdown()``          | ``rich.Markdown()`` ✓   |
+-------------------------+-------------------------+
| ``Live()``              | ``rich.Live()`` ✓       |
+-------------------------+-------------------------+
| ``Status()``            | ``rich.Status()`` ✓     |
+-------------------------+-------------------------+
| ``console.rule()``      | ``rich.rule()`` ✓       |
+-------------------------+-------------------------+

**Key differences:**

- No dependency on Rich library (pure Python implementation)
- Uses ANSI escape codes instead of Rich's advanced color system
- Slightly different theme system for syntax highlighting
- Console options are simplified but cover common use cases
