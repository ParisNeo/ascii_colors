#!/usr/bin/env python3
"""
Test script for ASCIIColors convenience functions.
Tests the rich-style convenience methods added to ASCIIColors class.
"""

import time
import random
from ascii_colors import ASCIIColors


def test_panel():
    """Test ASCIIColors.panel() convenience function."""
    print("\n" + "=" * 60)
    ASCIIColors.yellow("TEST: ASCIIColors.panel()", style=ASCIIColors.style_bold)
    print("=" * 60)
    
    # Basic panel
    ASCIIColors.panel("Hello, World!", title="Basic Panel")
    print()
    
    # Styled panel with different border
    ASCIIColors.panel(
        "[bold red]This is a warning message with important information.\nAnd this is a  new line[/bold red]",
        title="[bold yellow]⚠ Warning[/bold yellow]",
        border_style="bold yellow",
        box="round",
        padding=(1, 2)
    )
    print()
    
    # Panel with custom colors
    result = ASCIIColors.panel(
        "Success! Operation completed.",
        title="✓ Done",
        border_style="green",
        color="green"
    )
    print(result)


def test_table():
    """Test ASCIIColors.table() convenience function."""
    print("\n" + "=" * 60)
    ASCIIColors.yellow("TEST: ASCIIColors.table()", style=ASCIIColors.style_bold)
    print("=" * 60)
    
    # Basic table
    result = ASCIIColors.table(
        "Name", "Age", "City",
        rows=[
            ["Alice", "28", "New York"],
            ["Bob", "34", "London"],
            ["Charlie", "22", "Tokyo"]
        ],
        title="User Data"
    )
    print(result)
    print()
    
    # Table with rich markup in cells
    result = ASCIIColors.table(
        "Package", "Version", "Status",
        rows=[
            ["numpy", "1.24.0", "[green]✓ up to date[/green]"],
            ["pandas", "2.0.0", "[yellow]⚠ update available[/yellow]"],
            ["requests", "2.28.0", "[red]✗ security fix[/red]"]
        ],
        title="[bold]Installed Packages[/bold]",
        show_lines=True
    )
    print(result)


def test_tree():
    """Test ASCIIColors.tree() convenience function."""
    print("\n" + "=" * 60)
    ASCIIColors.yellow("TEST: ASCIIColors.tree()", style=ASCIIColors.style_bold)
    print("=" * 60)
    
    # Build a file tree using the tree convenience function
    root = ASCIIColors.tree("📁 project", style="bold")
    
    src = root.add_node("📁 src")
    src.add("📄 __init__.py")
    src.add("📄 main.py")
    utils = src.add_node("📁 utils")
    utils.add("📄 helpers.py")
    
    tests = root.add_node("📁 tests")
    tests.add("📄 test_main.py")
    
    root.add("📄 README.md")
    root.add("📄 pyproject.toml")
    
    # Print using rich module since tree returns a Tree object
    from ascii_colors import rich
    rich.print(root)


def test_syntax():
    """Test ASCIIColors.syntax() convenience function."""
    print("\n" + "=" * 60)
    ASCIIColors.yellow("TEST: ASCIIColors.syntax()", style=ASCIIColors.style_bold)
    print("=" * 60)
    
    # Python code
    python_code = '''
def greet(name):
    """Greet a person."""
    print(f"Hello, {name}!")
    return True

# Main execution
if __name__ == "__main__":
    greet("World")
'''
    
    result = ASCIIColors.syntax(python_code, language="python", line_numbers=True)
    print(result)
    print()
    
    # JSON code
    json_code = '''{
    "name": "ascii_colors",
    "version": "1.0.0",
    "features": ["colors", "logging", "panels"]
}'''
    
    result = ASCIIColors.syntax(json_code, language="json")
    print(result)


def test_markdown():
    """Test ASCIIColors.markdown() convenience function."""
    print("\n" + "=" * 60)
    ASCIIColors.yellow("TEST: ASCIIColors.markdown()", style=ASCIIColors.style_bold)
    print("=" * 60)
    
    md_content = """# ASCII Colors Library

## Features

- **Rich terminal output** with colors and styles
- **Logging system** with multiple handlers
- **Progress bars** for long-running tasks
- **Interactive menus** for user selection

## Code Example

```python
from ascii_colors import ASCIIColors

ASCIIColors.green("Success!")
```

> Note: This is a blockquote with important information.
"""
    
    result = ASCIIColors.markdown(md_content)
    print(result)


def test_columns():
    """Test ASCIIColors.columns() convenience function."""
    print("\n" + "=" * 60)
    ASCIIColors.yellow("TEST: ASCIIColors.columns()", style=ASCIIColors.style_bold)
    print("=" * 60)
    
    items = [
        "Feature 1: Color support",
        "Feature 2: Logging",
        "Feature 3: Progress bars",
        "Feature 4: Menus",
        "Feature 5: Tables",
        "Feature 6: Panels"
    ]
    
    result = ASCIIColors.columns(*items, equal=True, width=30)
    print(result)


def test_rule():
    """Test ASCIIColors.rule() convenience function."""
    print("\n" + "=" * 60)
    ASCIIColors.yellow("TEST: ASCIIColors.rule()", style=ASCIIColors.style_bold)
    print("=" * 60)
    
    # Basic rule
    ASCIIColors.rule("Section Divider", style="cyan")
    print()
    
    # Left-aligned rule
    ASCIIColors.rule("Left Title", align="left", style="yellow")
    print()
    
    # Right-aligned rule with custom character
    ASCIIColors.rule("Right Title", align="right", characters="=", style="green")
    print()
    
    # Simple rule without title
    ASCIIColors.rule(style="dim")


def test_status():
    """Test ASCIIColors.status() convenience function."""
    print("\n" + "=" * 60)
    ASCIIColors.yellow("TEST: ASCIIColors.status()", style=ASCIIColors.style_bold)
    print("=" * 60)
    
    print("Showing status spinners (3 seconds each)...")
    
    # Dots spinner
    with ASCIIColors.status("Loading data...", spinner="dots", spinner_style="green") as status:
        time.sleep(2)
        status.update("Processing...")
        time.sleep(1)
    
    print("✓ First status complete")
    
    # Different spinner style
    with ASCIIColors.status("Saving...", spinner="star", spinner_style="yellow") as status:
        time.sleep(2)


def test_live():
    """Test ASCIIColors.live() convenience function."""
    print("\n" + "=" * 60)
    ASCIIColors.yellow("TEST: ASCIIColors.live()", style=ASCIIColors.style_bold)
    print("=" * 60)
    
    print("Showing live updating display...")
    
    from ascii_colors.rich import Text
    
    with ASCIIColors.live(Text("Starting..."), refresh_per_second=4) as live:
        for i in range(5):
            time.sleep(0.5)
            bar = "█" * (i + 1) + "░" * (4 - i)
            live.update(Text(f"Progress: [{bar}] {i+1}/5"))
        
        time.sleep(0.5)
        live.update(Text("[bold green]✓ Complete![/bold green]"))
        time.sleep(0.5)


def test_rich_print():
    """Test ASCIIColors.rich_print() for markup support."""
    print("\n" + "=" * 60)
    ASCIIColors.yellow("TEST: ASCIIColors.rich_print()", style=ASCIIColors.style_bold)
    print("=" * 60)
    
    ASCIIColors.rich_print("[bold magenta]Bold magenta text[/bold magenta]")
    ASCIIColors.rich_print("[green]Success[/green] and [red]Error[/red] and [yellow]Warning[/yellow]")
    ASCIIColors.rich_print("[bold][blue]Nested[/blue] [underline]styles[/underline][/bold]")


def main():
    """Run all convenience function tests."""
    # Welcome banner
    print("\n")
    ASCIIColors.rich_print(
        "[bold green]╔══════════════════════════════════════════════════════════╗\n"
        "║  [bold white]ASCII Colors Convenience Functions Test Suite[/bold white]           ║\n"
        "╚══════════════════════════════════════════════════════════╝[/bold green]"
    )
    print("\nThis script tests all the rich-style convenience methods available")
    print("directly on the ASCIIColors class.\n")
    
    input("Press Enter to start testing...")
    
    # Run all tests
    test_panel()
    input("\nPress Enter to continue to table test...")
    
    test_table()
    input("\nPress Enter to continue to tree test...")
    
    test_tree()
    input("\nPress Enter to continue to syntax test...")
    
    test_syntax()
    input("\nPress Enter to continue to markdown test...")
    
    test_markdown()
    input("\nPress Enter to continue to columns test...")
    
    test_columns()
    input("\nPress Enter to continue to rule test...")
    
    test_rule()
    input("\nPress Enter to continue to status test...")
    
    test_status()
    input("\nPress Enter to continue to live test...")
    
    test_live()
    input("\nPress Enter to continue to rich_print test...")
    
    test_rich_print()
    
    # Farewell
    print("\n")
    ASCIIColors.rule("All Tests Complete", style="bold green")
    ASCIIColors.rich_print("[bold green]✓ All convenience functions tested successfully![/bold green]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"\n\nError during testing: {e}")
        import traceback
        traceback.print_exc()