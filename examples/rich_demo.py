#!/usr/bin/env python3
"""
Demonstration of ASCII Colors Rich compatibility features.
Run this to see all the new capabilities in action!
"""

import time
import random
from ascii_colors import (
    ASCIIColors, 
    rich, Console, Panel, Table, Tree, Text, Style, 
    Syntax, Markdown, BoxStyle, Columns
)


def demo_panels():
    """Demonstrate panel styles."""
    print("\n")
    rich.rule("PANELS", style="bold magenta")
    
    # Basic panel
    panel = Panel("Hello, World!", title="Basic")
    rich.print(panel)
    print()
    
    # Styled panel
    panel = Panel(
        "This is important information that needs to stand out.\nTesting more",
        title="[bold yellow]Warning[/bold yellow]",
        border_style="bold yellow",
        box=BoxStyle.ROUND,
        padding=(1, 2),
    )
    rich.print(panel)
    print()
    
    # Double border panel
    panel = Panel(
        "[red bold]Secure[/red bold] connection established\nEncryption: AES-256-GCM",
        title="🔒 Security",
        border_style="bold green",
        box=BoxStyle.DOUBLE,
    )
    rich.print(panel)
    print()
    
    # Using ASCIIColors convenience method - print directly
    result = ASCIIColors.panel("Quick panel via ASCIIColors.panel()", title="Convenience", border_style="red bold")
    result = ASCIIColors.panel("Quick panel via ASCIIColors.panel()", title="Convenience", border_style="red")
    


def demo_tables():
    """Demonstrate table features."""
    print("\n")
    rich.rule("TABLES", style="bold magenta")
    
    # Basic table
    table = Table("Name", "Age", "City", title="Users")
    table.add_row("Alice", "28", "New York")
    table.add_row("Bob", "34", "London")
    table.add_row("Charlie", "22", "Tokyo")
    rich.print(table)
    print()
    
    # Styled table with lines
    table = Table(
        "Package", "Version", "Status",
        title="[bold]Installed Packages[/bold]",
        header_style="bold cyan",
        show_lines=True,
        box=BoxStyle.ROUND,
    )
    table.add_row("numpy", "1.24.0", "[green]✓ up to date[/green]")
    table.add_row("pandas", "2.0.0", "[yellow]⚠ update available[/yellow]")
    table.add_row("requests", "2.28.0", "[red]✗ security fix needed[/red]")
    rich.print(table)
    print()
    
    # Compact table
    table = Table("Feature", "Supported", "Notes", box=BoxStyle.MINIMAL)
    table.add_row("Colors", "✓", "256 color support")
    table.add_row("Styles", "✓", "Bold, italic, underline")
    table.add_row("Emoji", "✓", "Unicode support")
    rich.print(table)


def demo_trees():
    """Demonstrate tree display."""
    print("\n")
    rich.rule("TREES", style="bold magenta")
    
    # File tree
    tree = Tree("📁 project", guide_style="dim")
    src = tree.add_node("📁 src")
    src.add("📄 __init__.py")
    src.add("📄 main.py")
    src.add("📁 utils")
    
    tests = tree.add_node("📁 tests")
    tests.add("📄 test_main.py")
    tests.add("📄 test_utils.py")
    
    tree.add("📄 README.md")
    tree.add("📄 pyproject.toml")
    tree.add("📄 .gitignore")
    
    rich.print(tree)
    print()
    
    # Using ASCIIColors.tree()
    print("Via ASCIIColors.tree():")
    my_tree = ASCIIColors.tree("root", style="bold")
    my_tree.add("child 1")
    my_tree.add("child 2").add("grandchild")
    rich.print(my_tree)


def demo_syntax():
    """Demonstrate syntax highlighting."""
    print("\n")
    rich.rule("SYNTAX HIGHLIGHTING", style="bold magenta")
    
    # Python code
    python_code = '''
def fibonacci(n):
    """Generate Fibonacci sequence."""
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

# Print first 10 numbers
for num in fibonacci(10):
    print(num)
'''
    
    syntax = Syntax(python_code, lexer="python", line_numbers=True)
    rich.print(syntax)
    print()
    
    # JSON
    json_code = '''{
    "name": "ascii_colors",
    "version": "1.0.0",
    "features": ["colors", "logging", "progress", "panels"],
    "enabled": true,
    "count": 42
}'''
    
    syntax = Syntax(json_code, lexer="json", line_numbers=True)
    rich.print(syntax)
    print()
    
    # Using ASCIIColors.syntax()
    print("Via ASCIIColors.syntax():")
    print(ASCIIColors.syntax("print('Hello')", language="python"))


def demo_markdown():
    """Demonstrate markdown rendering."""
    print("\n")
    rich.rule("MARKDOWN", style="bold magenta")
    
    markdown_text = """# ASCII Colors

A **powerful** library for terminal output.

## Features

- *Colors* and styles
- **Bold** and __underlined__ text
- `inline code` support

> This is a blockquote with important information.

---

### Code Example

```python
from ascii_colors import rich

rich.print("[green]Hello[/green], [bold]World[/bold]!")
```

| Feature | Status |
|---------|--------|
| Panels | ✓ |
| Tables | ✓ |
| Trees | ✓ |
"""
    
    md = Markdown(markdown_text)
    rich.print(md)


def demo_columns():
    """Demonstrate column layout."""
    print("\n")
    rich.rule("COLUMNS", style="bold magenta")
    
    items = [
        "Item 1: First column content",
        "Item 2: Second column content",
        "Item 3: Third column content",
        "Item 4: More content here",
        "Item 5: Even more to show",
        "Item 6: Last item in grid",
    ]
    
    cols = Columns([Text(item) for item in items], equal=True)
    rich.print(cols)


def demo_live():
    """Demonstrate live display."""
    print("\n")
    rich.rule("LIVE DISPLAY", style="bold magenta")
    
    from ascii_colors.rich import Live, Text
    
    # Simulate a process with live updates
    with Live(Text("Starting process..."), refresh_per_second=4) as live:
        for i in range(10):
            time.sleep(0.3)
            # Update with progress
            bar = "█" * (i + 1) + "░" * (9 - i)
            live.update(Text(f"Processing... [{bar}] {i+1}/10"))
        
        time.sleep(0.3)
        live.update(Text("[bold green]✓ Complete![/bold green]"))
        time.sleep(0.5)


def demo_status():
    """Demonstrate status spinners."""
    print("\n")
    rich.rule("STATUS SPINNERS", style="bold magenta")
    
    print("Different spinner styles:")
    
    # Dots spinner
    with rich.status("Loading data...", spinner="dots") as status:
        time.sleep(1.5)
        status.update("Processing...")
        time.sleep(1.5)
    
    # Line spinner
    with rich.status("Connecting...", spinner="line", spinner_style="yellow") as status:
        time.sleep(1.5)
    
    # Pulse spinner
    with rich.status("Saving...", spinner="pulse", spinner_style="cyan") as status:
        time.sleep(1.5)
    
    # Using ASCIIColors.status()
    print("\nVia ASCIIColors.status():")
    with ASCIIColors.status("Working...", spinner="star") as status:
        time.sleep(2)


def demo_styled_text():
    """Demonstrate styled text features."""
    print("\n")
    rich.rule("STYLED TEXT", style="bold magenta")
    
    # From markup - use rich markup directly
    rich.print("[bold red]Error:[/bold red] [yellow]Something went wrong[/yellow]")
    print()
    
    # Programmatic styling
    text = Text("Hello ")
    text.append("World", Style(bold=True, color="green"))
    text.append("!", Style(blink=True, color="red"))
    rich.print(text)
    print()
    
    # Justified text
    text = Text("This text is centered", justify="center")
    rich.print(text)
    print()
    
    text = Text("This text is right-aligned", justify="right")
    rich.print(text)


def demo_combined():
    """Show combined rich features."""
    print("\n")
    rich.rule("COMBINED EXAMPLE", style="bold magenta")
    
    # Create a complex layout
    
    # Header panel using markup string directly
    header = Panel(
        "[bold white]ASCII Colors Demo[/bold white]\n[dim]Rich library compatibility[/dim]",
        style="bold white on blue",
        box=BoxStyle.DOUBLE,
    )
    rich.print(header)
    print()
    
    # Two column layout
    left = Panel(
        Syntax("def hello():\n    print('world')", lexer="python"),
        title="Code",
        box=BoxStyle.ROUND,
    )
    
    table = Table("Key", "Value", box=BoxStyle.MINIMAL)
    table.add_row("Name", "ascii_colors")
    table.add_row("Version", "1.0.0")
    table.add_row("Python", "3.8+")
    
    right = Panel(table, title="Info", box=BoxStyle.ROUND)
    
    # Simple side-by-side (in real app, use proper layout)
    rich.print(left)
    print()
    rich.print(right)


def demo_rich_console():
    """Demonstrate Console features."""
    print("\n")
    rich.rule("CONSOLE FEATURES", style="bold magenta")
    
    # Create custom console
    console = Console(width=60)
    
    console.print("[bold]Custom width console[/bold]")
    console.rule("Section 1")
    console.print("This is a narrower console for compact output")
    console.rule("Section 2", align="left")
    console.print("Left-aligned rule above")
    
    # Log with timestamp
    print("\nConsole logging:")
    console.log("Application started")
    time.sleep(0.1)
    console.log("Processing request")
    time.sleep(0.1)
    console.log("Request completed")


def main():
    """Run all demos."""
    # Welcome
    rich.print(
        "[bold green]╔══════════════════════════════════════╗\n"
        "║     [bold white]ASCII Colors Rich Demo[/bold white]           ║\n"
        "║  [dim]Modern terminal UI for Python[/dim]       ║\n"
        "╚══════════════════════════════════════╝[/bold green]"
    )
    
    print("\nThis demo showcases the rich library compatibility features.")
    print("Each section demonstrates different capabilities.\n")
    input("Press Enter to start...")
    
    # Run demos
    demo_panels()
    input("\nPress Enter to continue...")
    
    demo_tables()
    input("\nPress Enter to continue...")
    
    demo_trees()
    input("\nPress Enter to continue...")
    
    demo_syntax()
    input("\nPress Enter to continue...")
    
    demo_markdown()
    input("\nPress Enter to continue...")
    
    demo_columns()
    input("\nPress Enter to continue...")
    
    demo_styled_text()
    input("\nPress Enter to continue...")
    
    demo_live()
    input("\nPress Enter to continue...")
    
    demo_status()
    input("\nPress Enter to continue...")
    
    demo_rich_console()
    input("\nPress Enter to continue...")
    
    demo_combined()
    
    # Farewell
    print("\n")
    rich.rule(style="bold green")
    rich.print("[bold green]✓ Demo complete![/bold green]")
    rich.print("For more information, see: https://github.com/ParisNeo/ascii_colors")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()