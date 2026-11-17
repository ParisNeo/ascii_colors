# -*- coding: utf-8 -*-
"""Tests for ``Console.rule()`` (and the ``Rule`` renderable) line-start behavior.

A rule must always be emitted on a fresh line, never glued onto preceding
mid-line output. Concretely, given::

    console.print("Status:", end="")
    console.rule()

the output must be::

    Status:
    ────────────────────────────────────────

and not::

    Status:────────────────────────────────────────
"""

import io
import re

import pytest

from ascii_colors.core import ASCIIColors
from ascii_colors.rich.console import Console
from ascii_colors.rich.layout import Rule


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
_RULE_CHARS = set("─═━")
_WIDTH = 40


@pytest.fixture(autouse=True)
def _reset_line_state():
    """Each test starts from a known cursor state (column 0)."""
    ASCIIColors._set_at_line_start(True)
    yield
    ASCIIColors._set_at_line_start(True)


def _make_console():
    stream = io.StringIO()
    console = Console(file=stream, force_terminal=True, force_width=_WIDTH)
    return console, stream


def _visible(text: str) -> str:
    # CR is terminal cursor control, not visible rule content. Raw CRLF
    # behavior remains pinned separately by test_ensure_line_start_uses_explicit_crlf.
    return _ANSI_RE.sub("", text).replace("\r", "")


def test_rule_starts_on_new_line_after_mid_line_print():
    """A rule following ``print(..., end='')`` must start at column 0."""
    console, stream = _make_console()
    console.print("Status:", end="")
    console.rule()

    lines = _visible(stream.getvalue()).split("\n")
    assert lines[0].strip() == "Status:", lines
    assert lines[1].strip(), f"rule must be on its own line: {lines!r}"
    assert set(lines[1]) <= _RULE_CHARS, f"expected only rule chars: {lines[1]!r}"


def test_rule_with_title_starts_on_new_line_after_mid_line_print():
    """A titled rule must not be glued to the previous text either."""
    console, stream = _make_console()
    console.print("Working...", end="")
    console.rule("Done")

    lines = _visible(stream.getvalue()).split("\n")
    assert lines[0].strip() == "Working...", lines
    assert "Done" in lines[1], f"title must be on the rule line: {lines!r}"
    assert lines[1].lstrip().startswith(tuple(_RULE_CHARS)), lines[1]


def test_rule_does_not_insert_blank_line_when_already_at_line_start():
    """No spurious blank line when the cursor is already at column 0."""
    console, stream = _make_console()
    console.print("Header")
    console.rule()

    lines = _visible(stream.getvalue()).split("\n")
    assert lines[0].strip() == "Header", lines
    assert lines[1].strip(), f"rule must directly follow header: {lines!r}"
    assert set(lines[1]) <= _RULE_CHARS, lines[1]


def test_rule_renderable_starts_on_new_line_via_console_print():
    """The ``Rule`` renderable goes through the same guard as ``console.rule``."""
    console, stream = _make_console()
    console.print("Preamble", end="")
    console.print(Rule())

    lines = _visible(stream.getvalue()).split("\n")
    assert lines[0].strip() == "Preamble", lines
    assert lines[1].strip(), f"Rule renderable must be on its own line: {lines!r}"
    assert set(lines[1]) <= _RULE_CHARS, lines[1]


def test_rule_with_custom_heavy_char_starts_on_new_line():
    """Custom rule characters still force a fresh line."""
    console, stream = _make_console()
    console.print("Section", end="")
    console.rule(characters="═")

    lines = _visible(stream.getvalue()).split("\n")
    assert lines[0].strip() == "Section", lines
    assert set(lines[1]) <= _RULE_CHARS, f"expected rule chars: {lines[1]!r}"


def test_ensure_line_start_uses_explicit_crlf():
    """The cursor-reset before a box char must be a full CR+LF.

    A bare ``\\n`` only produces a linefeed on terminals whose OPOST/ONLCR
    output processing is disabled (e.g. while another thread is inside
    ``_get_key()``'s raw-mode window). That is why the fix must emit the
    carriage return explicitly. This test pins that behaviour so a
    regression back to a bare ``\\n`` is caught.
    """
    console, stream = _make_console()
    console.print("Status:", end="")
    console.rule()

    raw = stream.getvalue()
    # We expect: "Status:" + CRLF + rule line + CRLF
    assert "Status:\r\n" in raw, (
        f"box-drawing line break must be CRLF, got {raw!r}"
    )
    assert raw.endswith("\r\n"), (
        f"rule must end with CRLF so the next write starts at col 0, got {raw!r}"
    )


def test_consecutive_rules_each_start_on_new_line():
    """Interleaved ``print(end='')`` + ``rule()`` calls each reset to column 0."""
    console, stream = _make_console()
    console.print("A", end="")
    console.rule()
    console.print("B", end="")
    console.rule()

    lines = [ln for ln in _visible(stream.getvalue()).split("\n") if ln]
    assert lines[0] == "A", lines
    assert set(lines[1]) <= _RULE_CHARS, lines[1]
    assert lines[2] == "B", lines
    assert set(lines[3]) <= _RULE_CHARS, lines[3]