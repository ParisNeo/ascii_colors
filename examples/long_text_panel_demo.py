"""
Demo: Handling panels with long lines of text.

This example demonstrates that ASCIIColors correctly wraps long lines
of text inside a Panel without breaking ANSI color codes, splitting
wide characters, or misaligning the borders.
"""

import textwrap
from ascii_colors import ASCIIColors


def get_long_text() -> str:
    """Generate a long string with no newlines and embedded rich markup."""
    base_text = (
        "This is a deliberately long line of text designed to exceed the standard "
        "width of a terminal window. When placed inside a panel, it must be wrapped "
        "automatically to ensure the borders remain perfectly aligned and the text "
        "remains readable. "
    )
    # Repeat to ensure it's definitely longer than 80-120 chars
    long_text = base_text * 3
    return f"[bold cyan]Important Notice:[/bold cyan] {long_text}"


def get_paragraph_text() -> str:
    """Generate multiple long paragraphs with rich markup."""
    paragraph1 = (
        "[bold green]Success:[/bold green] The system has successfully processed the batch "
        "of files that were uploaded to the server. All files passed validation checks "
        "and have been stored in the designated database. You can now safely access them "
        "via the standard API endpoints without any risk of data corruption."
    )
    paragraph2 = (
        "[yellow]Warning:[/yellow] While the upload was successful, we noticed that some "
        "files were missing optional metadata fields. This will not affect core functionality, "
        "but it is highly recommended that you update the metadata to improve searchability "
        "and indexing performance in the long run."
    )
    return f"{paragraph1}\n\n{paragraph2}"


def main() -> None:
    # Show terminal width for context
    term_width = ASCIIColors._get_terminal_width()
    ASCIIColors.info(f"Current terminal width: {term_width}")
    ASCIIColors.rule("Standard Print (No Wrapping)", style="dim")
    
    # Print raw to show it doesn't wrap naturally
    raw_text = get_long_text()
    ASCIIColors.rich_print(raw_text)
    
    ASCIIColors.rule("Panel with Long Single Line", style="bold blue")
    # The panel should automatically wrap the long single line
    ASCIIColors.panel(
        raw_text,
        title="Auto-Wrapping Panel",
        border_style="blue",
        padding=(1, 2)
    )
    
    ASCIIColors.rule("Panel with Multiple Long Paragraphs", style="bold magenta")
    # The panel should respect explicit newlines and wrap each paragraph
    ASCIIColors.panel(
        get_paragraph_text(),
        title="System Status Report",
        border_style="magenta",
        box="round",
        padding=(0, 1)
    )

    ASCIIColors.rule("Panel fit() with Long Text", style="bold green")
    # Using the rich module directly to show the fit classmethod
    from ascii_colors import Panel
    panel = Panel.fit(
        get_paragraph_text(),
        title="Fit Panel",
        border_style="green"
    )
    ASCIIColors.rich_print(panel)


if __name__ == "__main__":
    main()