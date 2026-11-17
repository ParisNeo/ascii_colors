# -*- coding: utf-8 -*-
"""Tests for the advanced chat console without starting a terminal loop."""

import io
import time

import pytest

from ascii_colors import ASCIIColors
from ascii_colors.constants import INFO
from ascii_colors.tui import (
    App,
    ChatbotApp,
    RichChatView,
    ScreenBuffer,
    TerminalLogBuffer,
)
from ascii_colors.tui.log_capture import MemoryLogHandler


@pytest.fixture(autouse=True)
def _restore_global_log_level():
    """Isolate capture tests from logging-level changes in other test modules."""
    previous_level = ASCIIColors._global_level
    ASCIIColors.set_log_level(INFO)
    yield
    ASCIIColors.set_log_level(previous_level)


def _wait(app: ChatbotApp) -> None:
    deadline = time.monotonic() + 3.0
    while app.active_session.busy and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not app.active_session.busy


def test_new_session_preserves_previous_transcript():
    app = ChatbotApp(lambda prompt, history: f"echo: {prompt}")
    first = app.active_session
    app.send("hello")
    _wait(app)
    assert first.messages[-1]["content"] == "echo: hello"

    second = app.new_session()
    assert second is app.active_session
    assert app.chat_view.messages is second.messages
    assert first.messages[-1]["content"] == "echo: hello"
    assert second.title == "New conversation"


def test_commands_create_rename_and_describe_sessions():
    app = ChatbotApp(lambda prompt, history: prompt)
    app.send("/title Research")
    assert app.active_session.title == "Research"
    app.send("/model")
    assert "Generator" in app.active_session.messages[-1]["content"]
    app.send("/new")
    assert len(app.sessions) == 2
    assert app.active_session.title == "New conversation"


def test_worker_records_latency_and_token_metadata():
    app = ChatbotApp(lambda prompt, history: "a useful answer")
    app.send("question")
    _wait(app)
    answer = app.active_session.messages[-1]
    assert answer["content"] == "a useful answer"
    assert answer["elapsed"] >= 0
    assert answer["tokens"] > 0


def test_rich_transcript_renders_code_and_tool_cards():
    view = RichChatView()
    view.add_message("user", "show code")
    view.add_message("assistant", "```python\nprint('ok')\n```")
    view.add_message("tool", "workspace loaded")
    buffer = ScreenBuffer(70, 20)
    view.layout(0, 0, 70, 20)
    view.draw(buffer)
    rendered = "\n".join("".join(cell.char for cell in row) for row in buffer.cells)
    assert "python" in rendered
    assert "workspace loaded" in rendered


def test_default_console_branding():
    app = ChatbotApp(lambda prompt, history: prompt)
    assert app.title == "lollms console"
    assert app.header.left.startswith("[bold bright_yellow]◈ lollms console")
    assert app.active_session.messages[0]["role"] == "welcome"

def test_welcome_banner_renders_large_and_falls_back_cleanly():
    view = RichChatView()
    view.messages.append({"role": "welcome", "content": "Beautifully connected."})
    buffer = ScreenBuffer(72, 20)
    view.layout(0, 0, 72, 20)
    view.draw(buffer)
    rendered = "\n".join("".join(cell.char for cell in row) for row in buffer.cells)
    assert "Beautifully connected." in rendered
    assert "Start typing below" in rendered
    assert "█" in rendered

    narrow_buffer = ScreenBuffer(20, 14)
    view.layout(0, 0, 20, 14)
    view.draw(narrow_buffer)
    narrow = "\n".join("".join(cell.char for cell in row) for row in narrow_buffer.cells)
    assert "L O L L M S" in narrow

def test_composer_can_be_focused_directly():
    console = ChatbotApp(lambda prompt, history: prompt)
    app = App(stream=io.StringIO())
    app.set_root(console.root)
    app.refresh_focus()
    assert app.focus(console.input)
    assert console.input._focused
    assert not console.session_list._focused

def test_settings_command_invokes_host_panel_callback():
    opened = []
    console = ChatbotApp(lambda prompt, history: prompt, on_settings=lambda: opened.append(True))
    console.send("/settings")
    assert opened == [True]


def test_log_buffer_filters_and_bounds_records():
    buffer = TerminalLogBuffer(max_entries=100)
    buffer.append("ordinary output", "INFO", "demo")
    buffer.append("bad output", "ERROR", "demo")
    assert len(buffer.lines(level="ERROR")) == 1
    assert "bad output" in buffer.text("bad")
    buffer.clear()
    assert not buffer.lines()

def test_console_capture_is_idempotent_and_stores_ascii_colors_logs():
    console = ChatbotApp(lambda prompt, history: prompt)
    other = ChatbotApp(lambda prompt, history: prompt)
    assert other.log_buffer is console.log_buffer
    ASCIIColors.info("captured-test-message")
    assert "captured-test-message" in console.log_buffer.text()

def test_slash_completion_filters_accepts_and_executes():
    console = ChatbotApp(lambda prompt, history: prompt)
    console.input.handle_key("/")
    assert len(console.input.completion_items) == len(console.command_specs)

    console.input.handle_key("l")
    assert [item[1] for item in console.input.completion_items] == [
        "/logs", "/logs clear"
    ]
    assert console.input.handle_key("TAB")
    assert console.input.value == "/logs"
    assert not console.input.completion_active

    console.input.value = "/he"
    console.input.cursor = 3
    console.input._refresh_completions()
    console.input.handle_key("ENTER")
    assert "Commands:" in console.active_session.messages[-1]["content"]


def test_log_buffer_filters_and_captures_ascii_colors_records():
    buffer = TerminalLogBuffer(max_entries=100)
    console = ChatbotApp(lambda prompt, history: prompt, log_buffer=buffer)
    ASCIIColors.info("captured-test-message")
    assert "captured-test-message" in console.log_buffer.text()
    assert console.log_buffer.lines("missing") == []
    console.log_buffer.clear()
    assert len(console.log_buffer) == 0


def test_completion_escape_does_not_quit_application():
    console = ChatbotApp(lambda prompt, history: prompt)
    app = App(stream=io.StringIO())
    app.set_root(console.root)
    app.refresh_focus()
    app.focus(console.input)
    console.input.handle_key("/")
    assert console.input.completion_active
    app._dispatch_key("ESCAPE")
    assert not console.input.completion_active
    assert not app._stop_event.is_set()


def test_application_key_binding_runs_before_focus_dispatch():
    app = App(stream=io.StringIO())
    called = []
    app.bind("CTRL_N", lambda: called.append("new"))
    app._dispatch_key("CTRL_N")
    assert called == ["new"]