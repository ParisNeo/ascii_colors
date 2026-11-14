# -*- coding: utf-8 -*-
"""
Curses-style TUI framework for ascii_colors.

Build richly-styled interactive console apps with widgets, focus handling,
diff-based rendering, and alternate-screen support.

Example::

    from ascii_colors.tui import App, VBox, Box, Label, ListBox, TextInput, Button, ProgressBar

    body = VBox(gap=1, pad=1)
    body.add(Label("[bold cyan]My App[/bold cyan]", align="center"))
    body.add(ListBox(["one", "two", "three"]))
    App().set_root(body)
    App().run()
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
    "ScreenBuffer",
    "ScreenRenderer",
    "Cell",
    "Widget",
    "Container",
    "VBox",
    "HBox",
    "Box",
    "Label",
    "ListBox",
    "TextInput",
    "Button",
    "ProgressBar",
    "ScrollView",
    "Spinner",
    "StatusBar",
    "Table",
    "Tabs",
    "Checkbox",
    "Divider",
    "Sparkline",
    "BarChart",
    "BigValue",
    "BORDERS",
    "get_border",
]