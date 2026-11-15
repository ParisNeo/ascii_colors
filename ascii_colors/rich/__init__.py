# -*- coding: utf-8 -*-
"""
Rich-compatible rendering layer for ``ascii_colors``.

This subpackage re-implements a useful subset of `rich <https://rich.readthedocs.io>`_
with zero external dependencies so applications that already depend on
``ascii_colors`` can render panels, tables, trees, columns, syntax blocks,
markdown, rules, live displays, and status spinners without pulling in
``rich`` itself.

Top-level re-exports (``ascii_colors.rich``):

* :class:`Text` — styled text segments.
* :class:`Panel` — bordered, optionally titled box.
* :class:`Table` — tabular data with headers and row callbacks.
* :class:`Tree` — hierarchical tree view.
* :class:`Columns` — horizontal column layout.
* :class:`Rule` — horizontal divider with optional title.
* :class:`Console` — terminal writer with markup, logging and recording.
* :class:`Prompt` / :class:`Confirm` — interactive input helpers.
* :class:`Live` — periodically refreshed renderable.
* :class:`Status` — spinner + message.
* :class:`Markdown` — Markdown renderer.
* :class:`Syntax` — syntax-highlighted code block.
* :class:`BoxStyle` — border-style registry.
* :data:`rich` — self-reference so ``from ascii_colors.rich import rich`` works.
* :func:`print` / :func:`log` / :func:`rule` / :func:`prompt` — module-level
  convenience wrappers over a shared default :class:`Console` instance.

The convenience methods on :class:`ascii_colors.ASCIIColors` (``panel``,
``table``, ``tree``, ``columns``, ``syntax``, ``markdown``, ``rule``,
``live``, ``status``) are thin wrappers over these classes.
"""

import sys as _sys

from ascii_colors.rich.text import Text, wcswidth, Renderable
from ascii_colors.rich.content import Markdown, Syntax
from ascii_colors.rich.layout import Panel, Padding, Columns, Rule
from ascii_colors.rich.style import (
    Style,
    Color,
    BoxStyle,
    box,
    RICH_COLOR_MAP,
    RICH_STYLE_MAP,
    SEMANTIC_TAG_MAP,
)
from ascii_colors.rich.table import Table
from ascii_colors.rich.tree import Tree
from ascii_colors.rich.console import (
    Console,
    ConsoleOptions,
    Measurement,
    Prompt,
    Confirm,
)
from ascii_colors.rich.live import Live, Status

try:
    from ascii_colors.rich.console import ConsoleRenderable
except ImportError:  # pragma: no cover - typing-only symbol
    ConsoleRenderable = None  # type: ignore[assignment]

try:
    from ascii_colors.rich.layout import RichError
except ImportError:  # pragma: no cover - defensive fallback
    class RichError(Exception):
        """Base exception for the ``ascii_colors.rich`` rendering layer."""


# Shared default console used by the module-level convenience functions.
_default_console: "Console" = None


def _console() -> "Console":
    """Return (creating on first use) the shared default console."""
    global _default_console
    if _default_console is None:
        _default_console = Console()
    return _default_console


def print(*objects, **kwargs) -> None:  # noqa: A001 - rich-compatible name
    """Print via the shared default console (``rich.print`` equivalent)."""
    _console().print(*objects, **kwargs)


def log(*objects, **kwargs) -> None:
    """Log via the shared default console (``rich.log`` equivalent)."""
    _console().log(*objects, **kwargs)


def rule(title="", characters="─", style=None, align="center") -> None:
    """Render a horizontal rule via the shared default console."""
    _console().rule(title=title, characters=characters, style=style, align=align)


def prompt(text: str = "", **kwargs):
    """Ask via :class:`Prompt` using the shared default console."""
    return Prompt.ask(text, console=_console(), **kwargs)


# Self-reference so ``from ascii_colors.rich import rich`` works.
rich = _sys.modules[__name__]


__all__ = [
    "Text",
    "wcswidth",
    "Renderable",
    "Panel",
    "Padding",
    "Columns",
    "Rule",
    "Markdown",
    "Syntax",
    "Style",
    "Color",
    "BoxStyle",
    "box",
    "RICH_COLOR_MAP",
    "RICH_STYLE_MAP",
    "SEMANTIC_TAG_MAP",
    "Table",
    "Tree",
    "Console",
    "ConsoleOptions",
    "Measurement",
    "Prompt",
    "Confirm",
    "Live",
    "Status",
    "RichError",
    "ConsoleRenderable",
    "rich",
    "print",
    "log",
    "rule",
    "prompt",
]