Interactive Prompts Guide
=========================

ASCIIColors provides a complete, drop-in replacement for the `questionary`_ library, offering interactive prompts for user input with beautiful styling and validation.

.. _questionary: https://github.com/tmbo/questionary

Installation Note
-----------------

No additional installation needed! The prompts are built into ascii_colors.

Basic Usage
-----------

Import Styles
~~~~~~~~~~~~~

.. code-block:: python

    # Method 1: Module-like import (drop-in questionary replacement)
    from ascii_colors import questionary

    name = questionary.text("What's your name?").ask()

    # Method 2: Direct imports
    from ascii_colors import text, confirm, select, checkbox

    name = text("What's your name?").ask()

    # Method 3: Full path
    from ascii_colors.questionary import text, confirm

    name = text("What's your name?").ask()

Question Types
--------------

Text Input
~~~~~~~~~~

Single-line text with optional default and validation:

.. code-block:: python

    from ascii_colors import questionary

    # Basic text
    name = questionary.text("What's your name?").ask()

    # With default value
    name = questionary.text(
        "What's your name?",
        default="Anonymous"
    ).ask()

    # With validation
    email = questionary.text(
        "Enter email",
        validate=lambda x: "@" in x or "Invalid email"
    ).ask()

    # Multiline text
    description = questionary.text(
        "Enter description",
        multiline=True
    ).ask()

Password Input
~~~~~~~~~~~~~~

Hidden input with optional confirmation:

.. code-block:: python

    from ascii_colors import questionary

    # Basic password (hidden)
    password = questionary.password("Enter password").ask()

    # With confirmation (enter twice)
    password = questionary.password(
        "Set password",
        confirm=True,
        confirm_message="Confirm password"
    ).ask()

Confirmation (Yes/No)
~~~~~~~~~~~~~~~~~~~~~

Boolean choice with keyboard shortcuts:

.. code-block:: python

    from ascii_colors import questionary

    # Simple yes/no
    if questionary.confirm("Continue?").ask():
        print("Continuing...")

    # With default
    proceed = questionary.confirm(
        "Proceed?",
        default=True  # Y is capitalized in [Y/n]
    ).ask()

    # Default no
    delete = questionary.confirm(
        "Delete file?",
        default=False  # N is capitalized in [y/N]
    ).ask()

Single Selection (Select)
~~~~~~~~~~~~~~~~~~~~~~~~~

Arrow-key navigable list:

.. code-block:: python

    from ascii_colors import questionary

    # Simple list
    color = questionary.select(
        "Favorite color?",
        choices=["Red", "Green", "Blue", "Yellow"]
    ).ask()

    # With dictionary choices (name shown, value returned)
    format_choice = questionary.select(
        "Export format",
        choices=[
            {"name": "JSON (recommended)", "value": "json"},
            {"name": "YAML", "value": "yaml"},
            {"name": "XML (legacy)", "value": "xml", "disabled": True},
            {"name": "CSV", "value": "csv"}
        ],
        default="json"
    ).ask()  # Returns "json", "yaml", etc., not the display name

    # With icons
    action = questionary.select(
        "Choose action",
        choices=[
            {"name": "🚀 Deploy", "value": "deploy"},
            {"name": "🧪 Test", "value": "test"},
            {"name": "📊 Metrics", "value": "metrics"}
        ]
    ).ask()

Multi-Selection (Checkbox)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Select multiple items with spacebar:

.. code-block:: python

    from ascii_colors import questionary

    # Basic checkbox
    features = questionary.checkbox(
        "Select features",
        choices=["Auth", "Logging", "Cache", "API"]
    ).ask()  # Returns list like ["Auth", "Cache"]

    # With pre-selected items
    features = questionary.checkbox(
        "Select toppings",
        choices=[
            {"name": "Cheese", "value": "cheese", "checked": True},
            {"name": "Pepperoni", "value": "pepperoni"},
            {"name": "Mushrooms", "value": "mushrooms", "checked": True}
        ]
    ).ask()

    # Minimum selection requirement
    required = questionary.checkbox(
        "Select at least one",
        choices=["Option A", "Option B", "Option C"],
        min_selected=1
    ).ask()

    # Keyboard shortcuts:
    # ↑/↓ - Navigate
    # Space - Toggle selection
    # a - Toggle all
    # Enter - Confirm

Autocomplete
~~~~~~~~~~~~

Type to filter suggestions:

.. code-block:: python

    from ascii_colors import questionary

    cities = ["Amsterdam", "Athens", "Bangkok", "Barcelona", "Berlin", "Boston"]

    # Basic autocomplete
    city = questionary.autocomplete(
        "Enter city",
        choices=cities
    ).ask()

    # Case-insensitive with middle matching
    tech = questionary.autocomplete(
        "Search technology",
        choices=["Python", "JavaScript", "TypeScript", "Java", "Go", "Rust"],
        ignore_case=True,
        match_middle=True,  # "script" matches "JavaScript"
        max_suggestions=5
    ).ask()

Forms (Multiple Questions)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Chain questions together:

.. code-block:: python

    from ascii_colors import questionary

    # Sequential form
    user_info = questionary.form(
        questionary.text("First name"),
        questionary.text("Last name"),
        questionary.password("Password", confirm=True),
        questionary.confirm("Subscribe to newsletter?", default=False)
    ).ask()
    # Returns: {
    #     "First name": "...",
    #     "Last name": "...",
    #     "Password": "...",
    #     "Subscribe to newsletter?": True/False
    # }

Advanced Features
-----------------

Custom Validators
~~~~~~~~~~~~~~~~~

Create reusable validation logic:

.. code-block:: python

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
                raise ValidationError("Need uppercase letter")
            if not any(c.islower() for c in document):
                raise ValidationError("Need lowercase letter")
            if not any(c.isdigit() for c in document):
                raise ValidationError("Need digit")

    # Usage
    email = questionary.text("Email:", validate=EmailValidator()).ask()
    password = questionary.password(
        "Create password",
        validate=StrongPasswordValidator()
    ).ask()

Conditional Questions
~~~~~~~~~~~~~~~~~~~~~

Skip questions based on previous answers:

.. code-block:: python

    from ascii_colors import questionary

    # Basic skip
    is_company = questionary.confirm("Is this a company account?").ask()

    company_name = questionary.text(
        "Company name"
    ).skip_if(not is_company, default="N/A").ask()

    # In forms, previous answers are available
    def ask_details(answers):
        if answers.get("is_company"):
            return questionary.text("Company size")
        return questionary.text("Personal website").skip_if(True, default=None)

    # Note: skip_if returns the default value when condition is True

Custom Styling
~~~~~~~~~~~~~~

Apply colors to prompts:

.. code-block:: python

    from ascii_colors import questionary, ASCIIColors

    # Custom colors
    name = questionary.text(
        "Your name",
        style={
            "question": ASCIIColors.color_bright_green,
        }
    ).ask()

    # The style dict supports:
    # - question: Prompt color
    # - answer: Answer display color
    # - pointer: Selection pointer color
    # - highlight: Selected item highlight
    # - text: Input text color

Keyboard Navigation
~~~~~~~~~~~~~~~~~~~

All prompts support:

- **↑ / ↓** - Navigate up/down in lists
- **Enter** - Confirm selection
- **Space** - Toggle checkbox items
- **a** - Toggle all (checkbox mode)
- **q / Ctrl+C** - Cancel (raises KeyboardInterrupt)

Error Handling
--------------

Keyboard Interrupt
~~~~~~~~~~~~~~~~~~

Handle user cancellation gracefully:

.. code-block:: python

    from ascii_colors import questionary

    try:
        result = questionary.confirm("Continue?").ask()
    except KeyboardInterrupt:
        print("User cancelled")
        result = None

    # Or use the kbi_msg parameter
    result = questionary.confirm("Continue?").ask(kbi_msg="Operation cancelled")

Unsafe Ask (No Exception Handling)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let KeyboardInterrupt propagate:

.. code-block:: python

    # Regular ask catches KeyboardInterrupt
    result = questionary.text("Name?").ask()  # Returns None on Ctrl+C

    # Unsafe ask propagates the exception
    result = questionary.text("Name?").unsafe_ask()  # Raises KeyboardInterrupt

Complete Examples
-----------------

User Registration
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import questionary, rich

    def register_user():
        rich.print("[bold]User Registration[/bold]\n")

        # Basic info
        first_name = questionary.text("First name").ask()
        last_name = questionary.text("Last name").ask()

        # Email with validation
        from ascii_colors.questionary import Validator, ValidationError

        class EmailValidator(Validator):
            def validate(self, document):
                if "@" not in document or "." not in document.split("@")[-1]:
                    raise ValidationError("Please enter a valid email")

        email = questionary.text("Email", validate=EmailValidator()).ask()

        # Account type
        is_premium = questionary.confirm(
            "Upgrade to premium?",
            default=False
        ).ask()

        # Premium features selection
        if is_premium:
            features = questionary.checkbox(
                "Select premium features",
                choices=[
                    {"name": "Advanced analytics", "value": "analytics", "checked": True},
                    {"name": "Priority support", "value": "support", "checked": True},
                    {"name": "Custom integrations", "value": "integrations"}
                ]
            ).ask()
        else:
            features = []

        # Password
        password = questionary.password(
            "Create password",
            confirm=True
        ).ask()

        # Terms
        accept_terms = questionary.confirm(
            "Accept terms of service?",
            default=False
        ).ask()

        if not accept_terms:
            rich.print("[red]Registration cancelled[/red]")
            return None

        return {
            "name": f"{first_name} {last_name}",
            "email": email,
            "premium": is_premium,
            "features": features,
            "password_set": bool(password)
        }

Configuration Wizard
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ascii_colors import questionary, rich

    def setup_project():
        rich.print("[bold green]Project Setup Wizard[/bold green]\n")

        # Project basics
        config = questionary.form(
            questionary.text("Project name"),
            questionary.select(
                "Project type",
                choices=["Web App", "API", "CLI Tool", "Library"]
            ),
            questionary.select(
                "Python version",
                choices=["3.8", "3.9", "3.10", "3.11", "3.12"],
                default="3.11"
            )
        ).ask()

        # Features based on type
        features = []
        if config["Project type"] in ["Web App", "API"]:
            features = questionary.checkbox(
                "Select web features",
                choices=[
                    "Authentication",
                    "Database",
                    "Caching",
                    "Background jobs",
                    "WebSocket"
                ]
            ).ask()

        # Database selection if needed
        db = None
        if "Database" in (features or []):
            db = questionary.select(
                "Database",
                choices=["PostgreSQL", "MySQL", "SQLite", "MongoDB"]
            ).ask()

        # Deployment target
        deploy = questionary.select(
            "Deployment target",
            choices=[
                {"name": "Docker (recommended)", "value": "docker"},
                {"name": "AWS", "value": "aws"},
                {"name": "Google Cloud", "value": "gcp"},
                {"name": "Azure", "value": "azure"},
                {"name": "Self-hosted", "value": "self"}
            ]
        ).ask()

        # CI/CD
        cicd = questionary.confirm("Setup CI/CD?", default=True).ask()

        rich.print("\n[bold]Configuration Summary:[/bold]")
        for key, value in config.items():
            rich.print(f"  [dim]{key}:[/dim] [cyan]{value}[/cyan]")
        rich.print(f"  [dim]Features:[/dim] [cyan]{features or 'None'}[/cyan]")
        rich.print(f"  [dim]Database:[/dim] [cyan]{db or 'None'}[/cyan]")
        rich.print(f"  [dim]Deploy:[/dim] [cyan]{deploy}[/cyan]")
        rich.print(f"  [dim]CI/CD:[/dim] [cyan]{'Yes' if cicd else 'No'}[/cyan]")

        return {
            **config,
            "features": features,
            "database": db,
            "deployment": deploy,
            "cicd": cicd
        }

Best Practices
--------------

1. **Always handle KeyboardInterrupt** - Users may cancel at any time

2. **Use validators for input quality** - Don't rely on post-validation

3. **Provide sensible defaults** - Speed up common workflows

4. **Group related questions in forms** - Better UX than individual asks

5. **Use conditional skips** - Don't ask irrelevant questions

6. **Test with various terminal sizes** - Ensure layout works

7. **Provide clear, action-oriented labels** - "Deploy to production" vs "Production"

API Compatibility
-----------------

ASCIIColors' questionary module is designed for **drop-in compatibility**:

+-------------------------+-----------------------------+
| Feature                 | Status                      |
+=========================+=============================+
| ``text()``              | ✓ Fully compatible          |
+-------------------------+-----------------------------+
| ``password()``          | ✓ Fully compatible          |
+-------------------------+-----------------------------+
| ``confirm()``           | ✓ Fully compatible          |
+-------------------------+-----------------------------+
| ``select()``            | ✓ Fully compatible          |
+-------------------------+-----------------------------+
| ``checkbox()``          | ✓ Fully compatible          |
+-------------------------+-----------------------------+
| ``autocomplete()``      | ✓ Fully compatible          |
+-------------------------+-----------------------------+
| ``form()``              | ✓ Fully compatible          |
+-------------------------+-----------------------------+
| Custom validators       | ✓ Compatible                |
+-------------------------+-----------------------------+
| ``skip_if()``           | ✓ Compatible                |
+-------------------------+-----------------------------+
| ``ask()``               | ✓ Compatible                |
+-------------------------+-----------------------------+
| ``unsafe_ask()``        | ✓ Compatible                |
+-------------------------+-----------------------------+
| Styling dict            | ✓ Compatible (subset)       |
+-------------------------+-----------------------------+

Differences from original questionary:

- Simpler styling system (ANSI colors vs Rich styles)
- No external dependencies
- Built on ASCIIColors' menu system
- Keyboard navigation identical

See :doc:`api` for complete class documentation.
