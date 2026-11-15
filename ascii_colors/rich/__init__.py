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
* :class:`Live` — periodically refreshed renderable.
* :class:`Status` — spinner + message.
* :class:`Markdown` — Markdown renderer.
* :class:`Syntax` — syntax-highlighted code block.
* :class:`BoxStyle` — border-style registry.

The convenience methods on :class:`ascii_colors.ASCIIColors` (``panel``,
``table``, ``tree``, ``columns``, ``syntax``, ``markdown``, ``rule``,
``live``, ``status``) are thin wrappers over these classes.
"""

from ascii_colors.rich.text import Text, wcswidth
from ascii_colors.rich.content import Markdown, Syntax
from ascii_colors.rich.layout import Panel, Padding, Columns

from ascii_colors.rich.layout import Rule
from ascii_colors.rich.style import Style, BoxStyle
from ascii_colors.rich.table import Table
from ascii_colors.rich.tree import Tree
from ascii_colors.rich.console import Console, ConsoleOptions, Measurement
from ascii_colors.rich.live import Live, Status
from ascii_colors.rich.text import Renderable

try:
    from ascii_colors.rich.console import ConsoleRenderable
except ImportError:  # pragma: no cover - typing-only symbol
    ConsoleRenderable = None  # type: ignore[assignment]

try:
    from ascii_colors.rich.layout import RichError
except ImportError:  # pragma: no cover - defensive fallback
    class RichError(Exception):
        """Base exception for the ``ascii_colors.rich`` rendering layer."""

__all__ = [
    "Text",
    "wcswidth",
    "Panel",
    "Padding",
    "Columns",
    "Rule",
    "Markdown",
    "Syntax",
    "Style",
    "BoxStyle",
    "Table",
    "Tree",
    "Console",
    "Live",
    "Status",
    "RichError",
]