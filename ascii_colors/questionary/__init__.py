# -*- coding: utf-8 -*-
"""
Questionary-compatible API for ascii_colors.
Provides drop-in replacement for questionary library with enhanced styling.
"""

from ascii_colors.questionary.base import (
    Question,
    Validator,
    ValidationError,
)

from ascii_colors.questionary.text import (
    PromptText,
    text,
)

from ascii_colors.questionary.password import (
    Password,
    password,
)

from ascii_colors.questionary.confirm import (
    Confirm,
    confirm,
)

from ascii_colors.questionary.select import (
    Select,
    select,
)

from ascii_colors.questionary.checkbox import (
    Checkbox,
    checkbox,
)

from ascii_colors.questionary.autocomplete import (
    Autocomplete,
    autocomplete,
)

from ascii_colors.questionary.form import (
    Form,
    form,
    ask,
)


# For backward compatibility, expose PromptText as Text
# This matches questionary's API where questionary.Text is the text input class
Text = PromptText


__all__ = [
    # Base classes
    "Question",
    "Validator",
    "ValidationError",
    # Question types
    "Text",  # This is PromptText, for questionary API compatibility
    "PromptText",  # Also expose the explicit name
    "Password",
    "Confirm",
    "Select",
    "Checkbox",
    "Autocomplete",
    "Form",
    # Convenience functions
    "text",
    "password",
    "confirm",
    "select",
    "checkbox",
    "autocomplete",
    "form",
    "ask",
]
