# -*- coding: utf-8 -*-
"""
Rich library compatibility layer for ascii_colors.
Provides a pure-Python implementation of Rich's core features
for terminal rendering without external dependencies.

This module is organized into submodules for better maintainability.
"""

from ascii_colors.rich.console import Console, ConsoleOptions, Measurement
from ascii_colors.rich.style import Style, Color, BoxStyle
from ascii_colors.rich.text import Text, Renderable
from ascii_colors.rich.layout import Panel, Padding, Columns
from ascii_colors.rich.table import Table
from ascii_colors.rich.tree import Tree
from ascii_colors.rich.content import Syntax, Markdown
from ascii_colors.rich.live import Live, Status

# Module-like interface
class RichModule:
    """Module-like interface for rich compatibility."""
    
    def __init__(self):
        self._console = Console()
    
    @property
    def console(self) -> Console:
        """Get the default console."""
        return self._console
    
    def print(
        self,
        *objects,
        sep=" ",
        end="\n",
        style=None,
        justify=None,
        overflow=None,
        no_wrap=None,
        emoji=None,
        markup=None,
        highlight=None,
    ):
        """Print to the default console."""
        self._console.print(
            *objects,
            sep=sep,
            end=end,
            style=style,
            justify=justify,
            overflow=overflow,
            no_wrap=no_wrap,
            emoji=emoji,
            markup=markup,
            highlight=highlight,
        )
    
    def log(
        self,
        *objects,
        sep=" ",
        end="\n",
        style=None,
    ):
        """Log to the default console."""
        self._console.log(*objects, sep=sep, end=end, style=style)
    
    def rule(
        self,
        title="",
        characters="─",
        style=None,
        align="center",
    ):
        """Print a rule to the default console."""
        self._console.rule(title, characters=characters, style=style, align=align)
    
    def status(
        self,
        status,
        *,
        spinner="dots",
        spinner_style=None,
        speed=1.0,
    ):
        """Create a status spinner."""
        return Status(
            status,
            console=self._console,
            spinner=spinner,
            spinner_style=spinner_style,
            speed=speed,
        )
    
    def live(
        self,
        renderable=None,
        *,
        refresh_per_second=4,
        screen=False,
    ):
        """Create a live display."""
        return Live(
            renderable,
            console=self._console,
            refresh_per_second=refresh_per_second,
            screen=screen,
        )
    
    # Expose classes
    Console = Console
    Text = Text
    Style = Style
    Panel = Panel
    Padding = Padding
    Columns = Columns
    Table = Table
    Tree = Tree
    Syntax = Syntax
    Markdown = Markdown
    Live = Live
    Status = Status
    BoxStyle = BoxStyle
    Renderable = Renderable
    ConsoleOptions = ConsoleOptions
    Measurement = Measurement


# Create module instance
rich = RichModule()

# Convenience functions
def print(*objects, **kwargs):
    """Print using the rich module."""
    rich.print(*objects, **kwargs)

def log(*objects, **kwargs):
    """Log using the rich module."""
    rich.log(*objects, **kwargs)

def rule(title="", **kwargs):
    """Print a rule using the rich module."""
    rich.rule(title, **kwargs)


# Re-export all public classes for direct import
__all__ = [
    # Core
    "rich", "print", "log", "rule",
    "Console", "ConsoleOptions", "Measurement",
    # Style
    "Style", "Color", "BoxStyle", "Renderable",
    # Text and Content
    "Text",
    # Layout
    "Panel", "Padding", "Columns",
    # Data Display
    "Table", "Tree",
    # Content
    "Syntax", "Markdown",
    # Live Display
    "Live", "Status",
]
