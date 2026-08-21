"""
Demo: Panel with an emoji in the title.

Shows that ASCIIColors correctly renders panels when the title contains
emoji characters alongside rich markup, without corrupting the border
alignment or truncating the title.
"""

from ascii_colors import ASCIIColors


def main() -> None:
    term_width = ASCIIColors._get_terminal_width()
    ASCIIColors.info(f"Current terminal width: {term_width}")
    
    ASCIIColors.rule("Panel with Emoji Title", style="bold blue")
    
    ASCIIColors.panel(
        "This panel has an emoji in its title. The border alignment and title rendering should remain perfectly intact.",
        title="[bold yellow]⚠ Warning[/bold yellow]",
        border_style="yellow",
        box="round",
        padding=(1, 2)
    )

    ASCIIColors.panel(
        "Another example with a different emoji and a cyan border.",
        title="🔒 Security Notice",
        border_style="cyan",
        box="square"
    )

    ASCIIColors.panel(
        "Testing with an emoji and no explicit border color.",
        title="🚀 Deployment Status",
        box="double"
    )
    
    ASCIIColors.panel(
        "Just a test\nWith\nShort\nWidth",
        title="🚀 This is a test with a title that is way longer than the content",
    )
    ASCIIColors.panel(
        (
            f"\n[cyan]Parameters:[/cyan]\n[dim]2[/dim]\n"
            f"\n[cyan]Status:[/cyan] [yellow]⏳ Executing...[/yellow]"
        ),
        title=f"[bold blue]🛠️ Executing: a tool that is malformed[/bold blue]",
        border_style="blue"
    )
    print("Here is a non return test",end="")
    ASCIIColors.panel(
        "The line preceding this panel doesn't provide a \\n",
        title="🚀 Testing a panel with no return",
    )
if __name__ == "__main__":
    main()