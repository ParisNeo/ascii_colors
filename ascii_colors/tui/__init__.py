
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
* Chatbot: :class:`ChatbotApp`, :class:`GeneratorProtocol`,
  :class:`CallableGenerator`, :class:`LollmsAdapter`.

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
    AsciiArt,
    BarChart,
    BigText,
    BigValue,
    Box,
    Button,
    ChatView,
    Checkbox,
    Container,
    Divider,
    HBox,
    Label,
    MultiLineInput,
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
from ascii_colors.utils import MouseEvent
from ascii_colors.tui.chat_widgets import RichChatView
from ascii_colors.tui.log_capture import (
    CapturedLog,
    MemoryLogHandler,
    TerminalLogBuffer,
    attach_log_capture,
)
from ascii_colors.tui.chatbot import (
    ChatSession,
    CallableGenerator,
    ChatbotApp,
    GeneratorProtocol,
    LollmsAdapter,
    LollmsDiscussionAdapter,
    try_build_lollms_generator,
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
    "AsciiArt",
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
    "BigText",
    "MouseEvent",
    "ChatView",
    "RichChatView",
    "CapturedLog",
    "TerminalLogBuffer",
    "MemoryLogHandler",
    "attach_log_capture",
    "MultiLineInput",
    "ChatSession",
    "ChatbotApp",
    "GeneratorProtocol",
    "CallableGenerator",
    "LollmsAdapter",
    "LollmsDiscussionAdapter",
    "try_build_lollms_generator",
]