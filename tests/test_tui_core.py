# -*- coding: utf-8 -*-
"""Regression tests for layout, graphics, focus and mouse-independent rendering."""

import io

from ascii_colors.tui import (
    App,
    AsciiArt,
    BigText,
    Box,
    Button,
    HBox,
    Label,
    ListBox,
    ScreenBuffer,
    ScreenRenderer,
    TextInput,
    VBox,
)
from ascii_colors.tui.screen import Cell
from ascii_colors.utils import MouseEvent, _parse_sgr_mouse


def test_vertical_layout_never_overflows_when_minimums_exceed_space():
    root = VBox()
    first = Label("first")
    second = Label("second")
    first.min_height = 8
    second.min_height = 8
    root.add(first)
    root.add(second)
    root.layout(0, 0, 20, 6)

    assert first.y == 0
    assert second.y + second.h <= 6
    assert first.h + second.h == 6


def test_horizontal_layout_ignores_invisible_children():
    root = HBox()
    first = Label("first")
    hidden = Label("hidden")
    hidden.visible = False
    root.add(first)
    root.add(hidden)
    root.layout(0, 0, 30, 2)

    assert first.w == 30
    assert hidden.w == 0
    assert hidden.h == 0


def test_wrapped_label_reports_intrinsic_height():
    label = Label("one two three four", wrap=True)
    assert label.measure(5, 20)[1] >= 4


def test_ascii_art_draws_multiline_and_transparent_spaces():
    art = AsciiArt(["█ █", " █ "])
    buffer = ScreenBuffer(3, 2)
    art.layout(0, 0, 3, 2)
    art.draw(buffer)

    assert buffer.cells[0][0].char == "█"
    assert buffer.cells[0][1].char == " "
    assert buffer.cells[0][2].char == "█"
    assert buffer.cells[1][1].char == "█"


def test_big_text_falls_back_instead_of_clipping_on_narrow_terminal():
    banner = BigText("HERMES")
    buffer = ScreenBuffer(6, 1)
    banner.layout(0, 0, 6, 1)
    banner.draw(buffer)
    assert "".join(cell.char for cell in buffer.cells[0]) == "HERMES"


def test_focus_refresh_preserves_current_widget():
    app = App(stream=io.StringIO())
    root = VBox()
    first = Button("first")
    second = Button("second")
    root.add(first)
    root.add(second)
    app.set_root(root)
    app.refresh_focus()
    app._cycle_focus(1)
    assert second._focused

    app.refresh_focus()
    assert second._focused
    assert not first._focused


def test_mouse_parser_decodes_press_release_and_wheel():
    press = _parse_sgr_mouse("0;10;5", "M")
    release = _parse_sgr_mouse("0;10;5", "m")
    wheel_up = _parse_sgr_mouse("64;10;5", "M")
    wheel_down = _parse_sgr_mouse("65;10;5", "M")

    assert press == MouseEvent(9, 4, "left", "press")
    assert release.action == "release"
    assert wheel_up.button == "wheel_up"
    assert wheel_down.button == "wheel_down"
    assert wheel_down.action == "wheel"


def test_renderer_updates_only_changed_spans_and_synchronizes():
    stream = io.StringIO()
    renderer = ScreenRenderer(stream)
    buffer = ScreenBuffer(10, 1)
    buffer.put(0, 0, "abcdefghij")
    renderer.draw(buffer)
    first_frame = stream.getvalue()
    assert "\033[?2026h" in first_frame
    assert "abcdefghij" in first_frame

    stream.seek(0)
    stream.truncate(0)
    buffer.set_cell(4, 0, "Z")
    renderer.draw(buffer)
    second_frame = stream.getvalue()
    assert ";5H" in second_frame
    assert "Z" in second_frame
    assert "abcdefghij" not in second_frame


def test_modal_escape_bubbles_from_focused_child_to_dialog():
    class Dialog(VBox):
        def __init__(self):
            super().__init__()
            self.closed = False

        def handle_key(self, key):
            if key == "ESCAPE":
                self.closed = True
                return True
            return False

    app = App(stream=io.StringIO())
    dialog = Dialog()
    editor = TextInput("text")
    dialog.add(editor)
    app.set_root(VBox())
    app.push_modal(dialog)
    assert app.focus(editor)

    app._dispatch_key("ESCAPE")
    assert dialog.closed
    assert not app._stop_event.is_set()


def test_box_is_opaque_and_can_opt_out():
    buffer = ScreenBuffer(8, 4)
    buffer.fill(0, 0, 8, 4, "x")

    panel = Box(border="rounded")
    panel.layout(0, 0, 8, 4)
    panel.draw(buffer)
    assert buffer.cells[1][1].char == " "
    assert buffer.cells[2][6].char == " "

    transparent = Box(border="rounded", opaque=False)
    transparent.layout(0, 0, 8, 4)
    transparent.draw(buffer)
    buffer.fill(0, 0, 8, 4, "x")
    transparent.draw(buffer)
    assert buffer.cells[1][1].char == "x"

def test_unhandled_escape_closes_generic_modal_without_quitting():
    app = App(stream=io.StringIO())
    app.set_root(VBox())
    app.push_modal(Box(title="Help"))
    app._dispatch_key("ESCAPE")
    assert not app._modals
    assert not app._stop_event.is_set()

def test_refresh_repaints_current_state_immediately():
    stream = io.StringIO()
    app = App(stream=stream, synchronized_output=False)
    label = Label("before")
    root = VBox()
    root.add(label)
    app.set_root(root)
    app.width, app.height = 12, 1
    app.buffer = ScreenBuffer(12, 1)

    label.text = "after"
    app.refresh()

    assert "after" in stream.getvalue()

def test_renderer_rejects_literal_non_ansi_style_names():
    stream = io.StringIO()
    renderer = ScreenRenderer(stream, synchronized_output=False)
    buffer = ScreenBuffer(2, 1)
    buffer.cells[0] = [Cell("O", "cyan"), Cell("K", "cyan")]
    renderer.draw(buffer)
    assert "cyan" not in stream.getvalue()