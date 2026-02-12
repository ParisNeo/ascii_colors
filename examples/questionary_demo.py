#!/usr/bin/env python3
"""
Demonstration of ASCII Colors Questionary compatibility features.
Run this to see all the interactive prompt capabilities in action!
"""

import os
import sys
from ascii_colors import questionary, ASCIIColors, rich


def print_header(title):
    """Print a section header."""
    print("\n")
    rich.rule(f"[bold cyan]{title}[/bold cyan]", style="cyan")


def demo_text():
    """Demonstrate text input prompts."""
    print_header("TEXT INPUT")
    
    ASCIIColors.print("Basic text input - just press Enter with default:", color="dim")
    name = questionary.text("What's your name?", default="Anonymous").ask()
    rich.print(f"[green]✓[/green] Hello, [bold]{name}[/bold]!")
    
    ASCIIColors.print("\nText with validation (must be at least 3 characters):", color="dim")
    username = questionary.text(
        "Choose a username",
        validate=lambda x: len(x) >= 3 or "Must be at least 3 characters"
    ).ask()
    rich.print(f"[green]✓[/green] Username: [bold]{username}[/bold]")


def demo_password():
    """Demonstrate password input."""
    print_header("PASSWORD INPUT")
    
    ASCIIColors.print("Password input (hidden, no confirmation):", color="dim")
    pwd = questionary.password("Enter a password (just demo, not saved)").ask()
    rich.print(f"[green]✓[/green] Password entered: [dim]{'•' * len(pwd)} ({len(pwd)} chars)[/dim]")
    
    ASCIIColors.print("\nPassword with confirmation:", color="dim")
    pwd2 = questionary.password(
        "Set a password",
        confirm=True,
        confirm_message="Confirm the password"
    ).ask()
    if pwd2:
        rich.print(f"[green]✓[/green] Password confirmed and set!")
    else:
        rich.print("[yellow]⚠[/yellow] Password setup cancelled or mismatched")


def demo_confirm():
    """Demonstrate yes/no confirmation."""
    print_header("CONFIRMATION")
    
    ASCIIColors.print("Simple yes/no with default=True:", color="dim")
    proceed = questionary.confirm("Do you want to continue?", default=True).ask()
    rich.print(f"[blue]→[/blue] Answer: [bold]{'Yes' if proceed else 'No'}[/bold]")
    
    ASCIIColors.print("\nAnother confirmation with default=False:", color="dim")
    delete = questionary.confirm("Delete all temporary files?", default=False).ask()
    rich.print(f"[blue]→[/blue] Will delete files: [bold]{'Yes' if delete else 'No'}[/bold]")


def demo_select():
    """Demonstrate single selection."""
    print_header("SINGLE SELECTION")
    
    ASCIIColors.print("Select from a simple list:", color="dim")
    color = questionary.select(
        "Pick your favorite color",
        choices=["Red", "Green", "Blue", "Yellow", "Purple", "Orange"],
        default="Blue"
    ).ask()
    rich.print(f"[green]✓[/green] You selected: [bold {color.lower()}]{color}[/bold {color.lower()}]")
    
    ASCIIColors.print("\nSelect with displayed names and return values:", color="dim")
    format_choice = questionary.select(
        "Choose export format",
        choices=[
            {"name": "JSON (JavaScript Object Notation)", "value": "json"},
            {"name": "YAML (YAML Ain't Markup Language)", "value": "yaml"},
            {"name": "XML (eXtensible Markup Language)", "value": "xml", "disabled": True},
            {"name": "CSV (Comma Separated Values)", "value": "csv"},
            {"name": "TOML (Tom's Obvious Minimal Language)", "value": "toml"},
        ],
        default="json"
    ).ask()
    rich.print(f"[green]✓[/green] Export format: [bold]{format_choice.upper()}[/bold]")
    
    ASCIIColors.print("\nSelect with icons:", color="dim")
    action = questionary.select(
        "What would you like to do?",
        choices=[
            {"name": "🚀 Deploy to production", "value": "deploy"},
            {"name": "🧪 Run tests", "value": "test"},
            {"name": "📊 View metrics", "value": "metrics"},
            {"name": "⚙️  Configure settings", "value": "config"},
        ]
    ).ask()
    rich.print(f"[green]✓[/green] Action: [bold]{action}[/bold]")


def demo_checkbox():
    """Demonstrate multi-selection (checkbox)."""
    print_header("MULTI-SELECTION (CHECKBOX)")
    
    ASCIIColors.print("Select features to install (Space to toggle, Enter to confirm):", color="dim")
    features = questionary.checkbox(
        "Select features for your project",
        choices=[
            {"name": "🔐 Authentication", "value": "auth", "checked": True},
            {"name": "📝 Logging system", "value": "logging", "checked": True},
            {"name": "💾 Database ORM", "value": "orm"},
            {"name": "🌐 REST API", "value": "rest"},
            {"name": "📈 Analytics", "value": "analytics"},
            {"name": "📧 Email service", "value": "email"},
            {"name": "🔔 Push notifications", "value": "push"},
        ],
        min_selected=1
    ).ask()
    
    if features:
        rich.print(f"[green]✓[/green] Selected [bold]{len(features)}[/bold] features:")
        for f in features:
            rich.print(f"  • [cyan]{f}[/cyan]")
    else:
        rich.print("[yellow]⚠[/yellow] No features selected")
    
    ASCIIColors.print("\nQuick select all with 'a' key, then Enter:", color="dim")
    all_items = questionary.checkbox(
        "Select all items (try pressing 'a')",
        choices=["Item A", "Item B", "Item C", "Item D"]
    ).ask()
    rich.print(f"[green]✓[/green] Selected: [bold]{all_items}[/bold]")


def demo_autocomplete():
    """Demonstrate autocomplete input."""
    print_header("AUTOCOMPLETE")
    
    cities = [
        "Amsterdam", "Athens", "Bangkok", "Barcelona", "Berlin", "Boston",
        "Brussels", "Budapest", "Cairo", "Chicago", "Copenhagen", "Dubai",
        "Dublin", "Helsinki", "Hong Kong", "Istanbul", "Jakarta", "Lisbon",
        "London", "Los Angeles", "Madrid", "Melbourne", "Mexico City", "Miami",
        "Milan", "Montreal", "Moscow", "Mumbai", "Munich", "New York",
        "Oslo", "Paris", "Prague", "Rome", "San Francisco", "Seoul",
        "Shanghai", "Singapore", "Stockholm", "Sydney", "Taipei", "Tokyo",
        "Toronto", "Vancouver", "Vienna", "Warsaw", "Zurich"
    ]
    
    ASCIIColors.print("Type to filter cities (case-insensitive, matches start):", color="dim")
    city = questionary.autocomplete(
        "Enter a city name",
        choices=cities,
        ignore_case=True,
        match_middle=False,
        max_suggestions=5
    ).ask()
    rich.print(f"[green]✓[/green] Selected city: [bold]{city}[/bold]")
    
    ASCIIColors.print("\nAutocomplete with middle matching:", color="dim")
    tech = questionary.autocomplete(
        "Search technology (try 'script' to find 'JavaScript', 'TypeScript')",
        choices=[
            "Python", "JavaScript", "TypeScript", "Java", "Kotlin",
            "Go", "Rust", "C++", "C#", "Ruby", "PHP", "Swift",
            "Scala", "Clojure", "Haskell", "Erlang", "Elixir"
        ],
        ignore_case=True,
        match_middle=True,
        max_suggestions=4
    ).ask()
    rich.print(f"[green]✓[/green] Technology: [bold]{tech}[/bold]")


def demo_form():
    """Demonstrate multi-question forms."""
    print_header("FORMS (MULTI-QUESTION)")
    
    ASCIIColors.print("Answer a series of questions in one form:", color="dim")
    
    answers = questionary.form(
        questionary.text("First name", validate=lambda x: len(x) > 0 or "Required"),
        questionary.text("Last name", validate=lambda x: len(x) > 0 or "Required"),
        questionary.confirm("Are you a developer?", default=True),
        questionary.select(
            "Years of experience",
            choices=["0-2 years", "3-5 years", "6-10 years", "10+ years"]
        ),
        questionary.checkbox(
            "Technologies you use",
            choices=["Python", "JavaScript", "Go", "Rust", "Java", "C++", "Other"]
        ),
        questionary.confirm("Subscribe to newsletter?", default=False)
    ).ask()
    
    rich.print("[green]✓[/green] Form completed! Summary:")
    for key, value in answers.items():
        display_value = value
        if isinstance(value, list):
            display_value = ", ".join(value) if value else "(none)"
        rich.print(f"  [dim]{key}:[/dim] [bold]{display_value}[/bold]")


def demo_conditional():
    """Demonstrate conditional questions."""
    print_header("CONDITIONAL QUESTIONS")
    
    ASCIIColors.print("Questions can be skipped based on conditions:", color="dim")
    
    is_company = questionary.confirm("Is this a company account?", default=False).ask()
    
    company_name = questionary.text("Company name").skip_if(
        not is_company,
        default="N/A (Personal account)"
    ).ask()
    
    employee_count = questionary.select(
        "Company size",
        choices=["1-10", "11-50", "51-200", "201-500", "500+"]
    ).skip_if(not is_company, default=None).ask()
    
    personal_role = questionary.text("Your role/title").skip_if(
        is_company,
        default=None
    ).ask()
    
    rich.print("[green]✓[/green] Account information:")
    rich.print(f"  [dim]Type:[/dim] {'Company' if is_company else 'Personal'}")
    rich.print(f"  [dim]Company:[/dim] {company_name}")
    if employee_count:
        rich.print(f"  [dim]Size:[/dim] {employee_count} employees")
    if personal_role:
        rich.print(f"  [dim]Role:[/dim] {personal_role}")


def demo_validation():
    """Demonstrate custom validators."""
    print_header("CUSTOM VALIDATORS")
    
    from ascii_colors.questionary import Validator, ValidationError
    
    class EmailValidator(Validator):
        def validate(self, document):
            if "@" not in document:
                raise ValidationError("Email must contain @")
            if "." not in document.split("@")[-1]:
                raise ValidationError("Email must have valid domain")
    
    class StrongPasswordValidator(Validator):
        def validate(self, document):
            if len(document) < 8:
                raise ValidationError("Password must be at least 8 characters")
            if not any(c.isupper() for c in document):
                raise ValidationError("Password must contain uppercase letter")
            if not any(c.islower() for c in document):
                raise ValidationError("Password must contain lowercase letter")
            if not any(c.isdigit() for c in document):
                raise ValidationError("Password must contain digit")
    
    ASCIIColors.print("Email validation with custom validator:", color="dim")
    email = questionary.text("Enter your email", validate=EmailValidator()).ask()
    rich.print(f"[green]✓[/green] Valid email: [bold]{email}[/bold]")
    
    ASCIIColors.print("\nStrong password validation:", color="dim")
    ASCIIColors.print("  Requirements: 8+ chars, upper, lower, digit", color="dim")
    # Use password with validator for hidden input
    strong_pwd = questionary.password(
        "Create strong password",
        validate=StrongPasswordValidator()
    ).ask()
    rich.print(f"[green]✓[/green] Password meets all requirements!")


def demo_styled():
    """Demonstrate styled prompts."""
    print_header("STYLED PROMPTS")
    
    ASCIIColors.print("Custom colors for different question types:", color="dim")
    
    # Note: style dict keys are 'question', 'answer', 'pointer', etc.
    name = questionary.text(
        "Your name (green question style)",
        style={"question": ASCIIColors.color_bright_green}
    ).ask()
    
    color = questionary.select(
        "Pick a color (yellow question, custom pointer)",
        choices=["Red", "Green", "Blue"],
        style={
            "question": ASCIIColors.color_bright_yellow,
        }
    ).ask()
    
    rich.print(f"[green]✓[/green] Hello [bold {color.lower()}]{name}[/bold {color.lower()}]!")


def main():
    """Run all questionary demos."""
    # Clear screen for clean start
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
    
    # Welcome banner
    rich.print(
        "[bold green]╔══════════════════════════════════════════════════════════╗\n"
        "║          [bold white]ASCII Colors Questionary Demo[/bold white]                ║\n"
        "║     [dim]Interactive prompts for Python CLI apps[/dim]            ║\n"
        "╚══════════════════════════════════════════════════════════╝[/bold green]"
    )
    
    rich.print(
        "\n[yellow]This demo showcases the questionary-compatible interactive prompts.[/yellow]\n"
        "Navigate with [bold]↑/↓[/bold] arrows, select with [bold]Enter[/bold], "
        "toggle checkboxes with [bold]Space[/bold].\n"
        "Press [bold]q[/bold] or [bold]Ctrl+C[/bold] to skip a question.\n"
    )
    
    input("Press Enter to start the demo...")
    
    try:
        demo_text()
        input("\nPress Enter to continue...")
        
        demo_password()
        input("\nPress Enter to continue...")
        
        demo_confirm()
        input("\nPress Enter to continue...")
        
        demo_select()
        input("\nPress Enter to continue...")
        
        demo_checkbox()
        input("\nPress Enter to continue...")
        
        demo_autocomplete()
        input("\nPress Enter to continue...")
        
        demo_form()
        input("\nPress Enter to continue...")
        
        demo_conditional()
        input("\nPress Enter to continue...")
        
        demo_validation()
        input("\nPress Enter to continue...")
        
        demo_styled()
        
    except KeyboardInterrupt:
        rich.print("\n\n[yellow]Demo interrupted by user.[/yellow]")
        return
    
    # Farewell
    print("\n")
    rich.rule(style="bold green")
    rich.print("[bold green]✓ Demo complete![/bold green]")
    rich.print(
        "For more information, visit:\n"
        "  [cyan]https://github.com/ParisNeo/ascii_colors[/cyan]\n"
        "  [cyan]https://pypi.org/project/ascii-colors/[/cyan]"
    )


if __name__ == "__main__":
    main()
