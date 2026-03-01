# -*- coding: utf-8 -*-
"""
ascii_colors: A Python library for rich terminal output with advanced logging features.
Now with questionary-compatible interactive prompts and rich library compatibility!
"""

from ascii_colors.constants import (
    LogLevel, CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
)
from ascii_colors.utils import strip_ansi, get_trace_exception
from ascii_colors.formatters import Formatter, JSONFormatter
from ascii_colors.handlers import (
    Handler, ConsoleHandler, StreamHandler, FileHandler, RotatingFileHandler, handlers
)
from ascii_colors.core import ASCIIColors
from ascii_colors.progress import ProgressBar
from ascii_colors.menu import Menu, MenuItem

# Expose context methods at module level for convenience
set_context = ASCIIColors.set_context
clear_context = ASCIIColors.clear_context
context = ASCIIColors.context
get_thread_context = ASCIIColors.get_thread_context

# Logging compatibility
from ascii_colors.logging import (
    getLogger, basicConfig, shutdown, _logger_cache, _AsciiLoggerAdapter
)

# Questionary compatibility (interactive prompts)
# Note: Text here is PromptText (question input), not rich.Text (styled text)
from ascii_colors.questionary import (
    # Classes
    PromptText,  # The actual class, renamed to avoid conflict with rich.Text
    Password, Confirm, Select, Checkbox, Autocomplete, 
    Form, Validator, ValidationError,
    # Functions
    password, confirm, select, checkbox, autocomplete, form, ask,
)

# Rich library compatibility (new!)
from ascii_colors.rich import (
    # Core classes
    Console, Text as RichText, Style, Renderable, ConsoleOptions, Measurement,
    # Layout
    Panel, Padding, Columns,
    # Data display
    Table, Tree,
    # Content
    Syntax, Markdown,
    # Live display
    Live, Status,
    # Enums
    BoxStyle,
    # Default instances
    rich,
    # Convenience functions
    print as rich_print,
    log as rich_log,
    rule as rich_rule,
)

from ascii_colors.rich.text import Text

# Create questionary module alias for drop-in replacement
class _QuestionaryModule:
    """Module-like object for drop-in questionary compatibility."""
    def __init__(self):
        # Import here to avoid circular imports
        from ascii_colors.questionary import PromptText, Password, Confirm, Select, Checkbox, Autocomplete, Form, Validator, ValidationError, text, password, confirm, select, checkbox, autocomplete, form, ask
        
        # Use PromptText as Text for questionary API compatibility
        self.Text = PromptText
        self.Password = Password
        self.Confirm = Confirm
        self.Select = Select
        self.Checkbox = Checkbox
        self.Autocomplete = Autocomplete
        self.Form = Form
        self.Validator = Validator
        self.ValidationError = ValidationError
        # Function aliases
        self.text = text
        self.password = password
        self.confirm = confirm
        self.select = select
        self.checkbox = checkbox
        self.autocomplete = autocomplete
        self.form = form
        self.ask = ask  # alias
    
    def __getattr__(self, name):
        # Forward any other attribute access
        raise AttributeError(f"questionary has no attribute '{name}'")

# Create singleton instance
questionary = _QuestionaryModule()


def trace_exception(ex: BaseException, enhanced: bool = False, max_width: int = None) -> None:
    """Logs the traceback of a given exception."""
    formatted = get_trace_exception(ex, enhanced=enhanced, max_width=max_width)
    ASCIIColors._log(LogLevel.ERROR, formatted, (), exc_info=None, logger_name='trace_exception')


__all__ = [
    # Core
    "ASCIIColors", "LogLevel", "Formatter", "JSONFormatter", "Handler",
    "ConsoleHandler", "StreamHandler", "FileHandler", "RotatingFileHandler",
    "handlers", "ProgressBar", "Menu", "MenuItem",
    # Context management
    "set_context", "clear_context", "context", "get_thread_context",
    # Logging compat
    "getLogger", "basicConfig", "shutdown", "trace_exception", 
    "strip_ansi", "get_trace_exception",
    "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET",
    "_logger_cache", "_AsciiLoggerAdapter",
    # Questionary compat
    "questionary",  # Module-like object for `from ascii_colors import questionary`
    "PromptText",  # Explicit name for questionary text input class
    "Password", "Confirm", "Select", "Checkbox", 
    "Autocomplete", "Form", "Validator", "ValidationError",
    "text", "password", "confirm", "select", "checkbox", "autocomplete", 
    "form", "ask",
    # Rich compat (new!)
    "rich",  # Module-like object for `from ascii_colors import rich`
    "Console", "Style", "Renderable", "ConsoleOptions", "Measurement",
    "Panel", "Padding", "Columns",
    "Table", "Tree",
    "Syntax", "Markdown",
    "Live", "Status",
    "BoxStyle",
    "rich_print", "rich_log", "rich_rule",  # Convenience functions
    # Aliases to avoid name conflicts
    "RichText",
]
