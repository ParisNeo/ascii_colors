
# -*- coding: utf-8 -*-
"""Widget-based TUI framework built on top of :mod:`ascii_colors`.

Public surface:

* :class:`App` — the application event loop (alternate screen, render thread,
  focus cycling, modals).
* :class:`ScreenBuffer` / :class:`ScreenRenderer` — 2D styled cell grid and
  diff-based renderer.
* Layout containers: :class:`VBox`, :class:`HBox`, :class:`Box`,
  :class:`Container`, :class:`ScrollView`, :class:`Tabs`.
* Leaf widgets: :class:`Label`, :class:`Divider`, :class:`Button`,
  :class:`Checkbox`, :class:`TextInput`, :class:`ListBox`, :class:`Table`,
  :class:`Spinner`, :class:`StatusBar`.
* Charts: :class:`Sparkline`, :class:`BarChart`, :class:`BigValue`.
* Borders: :data:`BORDERS`, :func:`get_border`.

Example::

    from ascii_colors.tui import App, VBox, Label, ListBox

    body = VBox(gap=1, pad=1)
    body.add(Label("[bold cyan]My App[/bold cyan]", align="center"))
    body.add(ListBox(["one", "two", "three"]))

    app = App()
    app.set_root(body)
    app.run()
"""

from ascii_colors.tui.app import App
from ascii_colors.tui.borders import BORDERS, get_border
from ascii_colors.tui.screen import Cell, ScreenBuffer, ScreenRenderer
from ascii_colors.tui.widgets import (
    BarChart,
    BigValue,
    Box,
    Button,
    Checkbox,
    Container,
    Divider,
    HBox,
    Label,
    ListBox,
    ProgressBar,
    ScrollView,
    Sparkline,
    Spinner,
    StatusBar,
    Table,
    Tabs,
    TextInput,
    VBox,
    Widget,
)

__all__ = [
    "App",
    "BORDERS",
    "get_border",
    "Cell",
    "ScreenBuffer",
    "ScreenRenderer",
    "Widget",
    "Container",
    "VBox",
    "HBox",
    "Box",
    "ScrollView",
    "Tabs",
    "Label",
    "Divider",
    "Button",
    "Checkbox",
    "TextInput",
    "ListBox",
    "Table",
    "Spinner",
    "StatusBar",
    "ProgressBar",
    "Sparkline",
    "BarChart",
    "BigValue",
]