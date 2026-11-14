# -*- coding: utf-8 -*-
"""
pen — a minimalist terminal text editor built on the ascii_colors TUI.

Usage:
    python examples/pen.py [file]

Controls:
    Arrows / Home / End / PgUp / PgDn    move the cursor
    Enter / Backspace / Delete          edit text
    Ctrl+S                              save (prompts for a path if untitled)
    Ctrl+O                              open a file
    Ctrl+Q                              quit

The editor demonstrates:
  * a hand-rolled syntax highlighter (keywords / strings / numbers / comments)
  * line numbers, status bar and title bar widgets
  * vertical + horizontal scrolling driven by the cursor
  * modal file dialogs built with the framework's ``push_modal`` API
"""

import re
import sys
from typing import List, Optional, Tuple

from ascii_colors.constants import ANSI
from ascii_colors.rich.style import RICH_COLOR_MAP
from ascii_colors.rich.text import wcswidth
from ascii_colors.tui import (
    App,
    Box,
    Divider,
    Label,
    TextInput,
    VBox,
    Widget,
)
from ascii_colors.tui.screen import ScreenBuffer
from ascii_colors.tui.widgets import _markup, _visible_width


# --------------------------------------------------------------------- styling
_ST_DEFAULT = ""
_ST_COMMENT = ANSI.style_dim + RICH_COLOR_MAP.get("bright_black", "\033[90m")
_ST_STRING = RICH_COLOR_MAP.get("bright_green", "\033[92m")
_ST_NUMBER = RICH_COLOR_MAP.get("bright_cyan", "\033[96m")
_ST_KEYWORD = ANSI.style_bold + RICH_COLOR_MAP.get("bright_magenta", "\033[95m")
_ST_BUILTIN = RICH_COLOR_MAP.get("bright_blue", "\033[94m")
_ST_GUTTER = ANSI.style_dim + RICH_COLOR_MAP.get("bright_black", "\033[90m")
_ST_GUTTER_CURRENT = ANSI.style_bold + RICH_COLOR_MAP.get("bright_yellow", "\033[93m")
_ST_CURSOR = ANSI.style_reverse
_ST_BORDER = RICH_COLOR_MAP.get("bright_cyan", "\033[96m")


_KEYWORDS = frozenset({
    "def", "class", "if", "elif", "else", "for", "while", "in", "return",
    "yield", "import", "from", "as", "with", "try", "except", "finally",
    "raise", "pass", "break", "continue", "lambda", "global", "nonlocal",
    "assert", "del", "and", "or", "not", "is", "True", "False", "None",
    "async", "await", "match", "case",
})

_BUILTINS = frozenset({
    "print", "len", "range", "str", "int", "float", "bool", "list", "dict",
    "set", "tuple", "open", "input", "type", "isinstance", "issubclass",
    "enumerate", "zip", "map", "filter", "sum", "min", "max", "abs",
    "sorted", "reversed", "any", "all", "repr", "id", "hash", "iter",
    "next", "super", "object", "Exception", "ValueError", "TypeError",
})


_TOKEN_PATTERN = re.compile(
    r"(?P<comment>#[^\n]*)"
    r'|(?P<string>"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'
    r"|(?P<number>\b\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?\b)"
    r"|(?P<ident>[A-Za-z_]\w*)"
    r"|(?P<space>\s+)"
    r"|(?P<other>.)",
    re.DOTALL,
)


# ------------------------------------------------------------------ text editor
class TextEditor(Widget):
    """A minimal, syntax-aware, scrollable, multi-line text editor widget."""

    def __init__(
        self,
        lines: Optional[List[str]] = None,
        *,
        filepath: Optional[str] = None,
        gutter_width: int = 5,
    ):
        super().__init__()
        self.lines: List[str] = list(lines) if lines is not None else [""]
        if not self.lines:
            self.lines = [""]
        self.filepath = filepath
        self.gutter_width = max(3, gutter_width)
        self.cursor_line = 0
        self.cursor_col = 0
        self.scroll_line = 0
        self.scroll_col = 0
        self.modified = False
        self.last_message = ""
        self.focusable = True
        self.min_height = 5
        self.min_width = self.gutter_width + 10
        self.flex = 1

    # ------------------------------------------------------------ construction
    @classmethod
    def open_file(cls, path: str) -> "TextEditor":
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return cls(lines=content.split("\n"), filepath=path)

    # ------------------------------------------------------------------ saving
    def save(self, path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        target = path or self.filepath
        if not target:
            return False, "no file path set"
        try:
            with open(target, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(self.lines))
        except OSError as exc:
            return False, str(exc)
        self.filepath = target
        self.modified = False
        self.last_message = f"saved {target}"
        return True, None

    # -------------------------------------------------------------- tokenizer
    @staticmethod
    def _tokenize(line: str) -> List[Tuple[str, str]]:
        tokens: List[Tuple[str, str]] = []
        for match in _TOKEN_PATTERN.finditer(line):
            kind = match.lastgroup
            text = match.group(0)
            if kind == "comment":
                style = _ST_COMMENT
            elif kind == "string":
                style = _ST_STRING
            elif kind == "number":
                style = _ST_NUMBER
            elif kind == "ident":
                if text in _KEYWORDS:
                    style = _ST_KEYWORD
                elif text in _BUILTINS:
                    style = _ST_BUILTIN
                else:
                    style = _ST_DEFAULT
            else:
                style = _ST_DEFAULT
            tokens.append((text, style))
        return tokens

    # ------------------------------------------------------------------ scroll
    def _sync_scroll(self, text_width: int) -> None:
        self.cursor_line = max(0, min(len(self.lines) - 1, self.cursor_line))
        self.cursor_col = max(0, min(len(self.lines[self.cursor_line]), self.cursor_col))

        if self.cursor_line < self.scroll_line:
            self.scroll_line = self.cursor_line
        elif self.cursor_line >= self.scroll_line + self.h:
            self.scroll_line = self.cursor_line - self.h + 1

        if self.cursor_col < self.scroll_col:
            self.scroll_col = self.cursor_col
        elif self.cursor_col >= self.scroll_col + text_width:
            self.scroll_col = self.cursor_col - text_width + 1
        self.scroll_col = max(0, self.scroll_col)

    # -------------------------------------------------------------------- draw
    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        text_width = self.w - self.gutter_width
        if text_width <= 0:
            return
        self._sync_scroll(text_width)
        for row in range(self.h):
            line_idx = self.scroll_line + row
            y = self.y + row
            if line_idx < len(self.lines):
                self._draw_line(buffer, line_idx, y, text_width)
            else:
                buffer.put(self.x, y, " " * self.w, "")

    def _draw_line(self, buffer: ScreenBuffer, line_idx: int, y: int, text_width: int) -> None:
        line = self.lines[line_idx]
        is_cursor_line = line_idx == self.cursor_line and self._focused

        num_style = _ST_GUTTER_CURRENT if is_cursor_line else _ST_GUTTER
        num = f"{line_idx + 1:>{self.gutter_width - 1}} "
        buffer.put(self.x, y, num, num_style)

        start_x = self.x + self.gutter_width
        end_x = self.x + self.w

        char_idx = 0
        visible_cells = 0
        cx = start_x
        for token_text, token_style in self._tokenize(line):
            for ch in token_text:
                cw = wcswidth(ch)
                if char_idx < self.scroll_col:
                    char_idx += 1
                    continue
                if visible_cells + cw > text_width or cx + cw > end_x:
                    break
                buffer.set_cell(cx, y, ch, token_style)
                if cw >= 2 and cx + 1 < end_x:
                    buffer.cells[y][cx + 1].char = ""
                    buffer.cells[y][cx + 1].style = token_style
                cx += cw
                visible_cells += cw
                char_idx += 1
            else:
                continue
            break

        if is_cursor_line:
            scroll_cells = sum(wcswidth(c) for c in line[: self.scroll_col])
            cursor_cells = sum(wcswidth(c) for c in line[: self.cursor_col])
            cursor_offset = cursor_cells - scroll_cells
            if 0 <= cursor_offset < text_width:
                cursor_x = start_x + cursor_offset
                if cursor_x < end_x:
                    cursor_ch = line[self.cursor_col] if self.cursor_col < len(line) else " "
                    buffer.set_cell(cursor_x, y, cursor_ch, _ST_CURSOR)

    # -------------------------------------------------------------- key input
    def handle_key(self, key: str) -> bool:
        self.last_message = ""

        if key == "\x13":  # Ctrl+S
            if self.filepath:
                success, error = self.save()
                if not success:
                    self.last_message = f"save failed: {error}"
            else:
                self._prompt_save_as()
            return True

        if key == "\x0f":  # Ctrl+O
            self._prompt_open()
            return True

        if key == "LEFT":
            if self.cursor_col > 0:
                self.cursor_col -= 1
            elif self.cursor_line > 0:
                self.cursor_line -= 1
                self.cursor_col = len(self.lines[self.cursor_line])
            return True

        if key == "RIGHT":
            if self.cursor_col < len(self.lines[self.cursor_line]):
                self.cursor_col += 1
            elif self.cursor_line < len(self.lines) - 1:
                self.cursor_line += 1
                self.cursor_col = 0
            return True

        if key == "UP":
            if self.cursor_line > 0:
                self.cursor_line -= 1
                self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_line]))
            return True

        if key == "DOWN":
            if self.cursor_line < len(self.lines) - 1:
                self.cursor_line += 1
                self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_line]))
            return True

        if key == "HOME":
            self.cursor_col = 0
            return True

        if key == "END":
            self.cursor_col = len(self.lines[self.cursor_line])
            return True

        if key == "PAGE_UP":
            self.cursor_line = max(0, self.cursor_line - max(1, self.h))
            self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_line]))
            return True

        if key == "PAGE_DOWN":
            self.cursor_line = min(len(self.lines) - 1, self.cursor_line + max(1, self.h))
            self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_line]))
            return True

        if key == "ENTER":
            current = self.lines[self.cursor_line]
            self.lines[self.cursor_line] = current[: self.cursor_col]
            self.lines.insert(self.cursor_line + 1, current[self.cursor_col:])
            self.cursor_line += 1
            self.cursor_col = 0
            self.modified = True
            return True

        if key == "BACKSPACE":
            if self.cursor_col > 0:
                line = self.lines[self.cursor_line]
                self.lines[self.cursor_line] = line[: self.cursor_col - 1] + line[self.cursor_col:]
                self.cursor_col -= 1
                self.modified = True
            elif self.cursor_line > 0:
                previous = self.lines[self.cursor_line - 1]
                current = self.lines[self.cursor_line]
                self.lines[self.cursor_line - 1] = previous + current
                self.lines.pop(self.cursor_line)
                self.cursor_line -= 1
                self.cursor_col = len(previous)
                self.modified = True
            return True

        if key == "DELETE":
            line = self.lines[self.cursor_line]
            if self.cursor_col < len(line):
                self.lines[self.cursor_line] = line[: self.cursor_col] + line[self.cursor_col + 1:]
                self.modified = True
            elif self.cursor_line < len(self.lines) - 1:
                self.lines[self.cursor_line] = line + self.lines[self.cursor_line + 1]
                self.lines.pop(self.cursor_line + 1)
                self.modified = True
            return True

        if len(key) == 1 and key.isprintable() and key not in ("\t", "\n", "\r"):
            line = self.lines[self.cursor_line]
            self.lines[self.cursor_line] = line[: self.cursor_col] + key + line[self.cursor_col:]
            self.cursor_col += 1
            self.modified = True
            return True

        return False

    # ------------------------------------------------------------- file dialogs
    def _prompt_save_as(self) -> None:
        if self._app is None:
            return
        app = self._app
        dialog = _ModalTextInput(value=self.filepath or "untitled.py", placeholder="filename")

        def on_save(text: str) -> pd:
            path = text.strip()
            if path:
                success, error = self.save(path)
                if not success:
                    self.last_message = f"save failed: {error}"
            app.pop_modal()

        def on_cancel() -> None:
            app.pop_modal()

        dialog.on_submit = on_save
        dialog.on_escape = on_cancel
        app.push_modal(_build_dialog(" Save As ", "Save file as:", dialog, "Enter save · Esc cancel"))

    def _prompt_open(self) -> None:
        if self._app is None:
            return
        app = self._app
        dialog = _ModalTextInput(value=self.filepath or "", placeholder="path/to/file.py")

        def on_open(text: str) -> None:
            path = text.strip()
            if path:
                try:
                    loaded = TextEditor.open_file(path)
                    self.lines = loaded.lines
                    self.filepath = loaded.filepath
                    self.cursor_line = 0
                    self.cursor_col = 0
                    self.scroll_line = 0
                    self.scroll_col = 0
                    self.modified = False
                    self.last_message = f"opened {path}"
                except (OSError, UnicodeDecodeError) as exc:
                    self.last_message = f"open failed: {exc}"
            app.pop_modal()

        def on_cancel() -> None:
            app.pop_modal()

        dialog.on_submit = on_open
        dialog.on_escape = on_cancel
        app.push_modal(_build_dialog(" Open File ", "Open file:", dialog, "Enter open · Esc cancel"))


# --------------------------------------------------------------- modal helpers
class _ModalTextInput(TextInput):
    """TextInput that can be dismissed with ``ESCAPE``."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.on_escape = None

    def handle_key(self, key: str) -> bool:
        if key == "ESCAPE":
            if self.on_escape:
                self.on_escape()
            return True
        return super().handle_key(key)


def _build_dialog(title: str, prompt: str, input_widget: TextInput, hint: str) -> Box:
    box = Box(title=title, border="rounded", border_style=_ST_BORDER, padding=1)
    box.add(Label(f"[bold]{prompt}[/bold]"))
    box.add(input_widget)
    box.add(Divider())
    box.add(Label(f"[dim]{hint}[/dim]"))
    box.w = 62
    box.h = 8
    return box


# ---------------------------------------------------------------- chrome bars
class _TitleBar(Widget):
    def __init__(self, editor: TextEditor):
        super().__init__()
        self.editor = editor
        self.min_height = 1
        self.flex = 0

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0:
            return
        editor = self.editor
        name = editor.filepath or "untitled.py"
        marker = " [yellow]●[/yellow]" if editor.modified else ""
        text = (
            f" [bold bright_cyan]◈ pen[/bold bright_cyan]"
            f"  [dim]│[/dim]  [white]{name}[/white]{marker}"
        )
        buffer.put(self.x, self.y, " " * self.w, self.style)
        buffer.draw_text(self.x, self.y, _markup(text), self.style, max_width=self.w)


class _StatusLine(Widget):
    def __init__(self, editor: TextEditor):
        super().__init__()
        self.editor = editor
        self.min_height = 1
        self.flex = 0

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0:
            return
        editor = self.editor
        buffer.put(self.x, self.y, " " * self.w, self.style)

        if editor.last_message:
            left = f"[bold bright_yellow]ⓘ {editor.last_message}[/bold bright_yellow]"
        else:
            left = (
                f"[dim]Ln[/dim] [bold]{editor.cursor_line + 1}[/bold]"
                f"[dim],[/dim] [dim]Col[/dim] [bold]{editor.cursor_col + 1}[/bold]"
            )

        right = "[dim]Ctrl+S save · Ctrl+O open · Ctrl+Q quit[/dim]"

        left_rendered = _markup(left)
        buffer.draw_text(self.x + 1, self.y, left_rendered, self.style, max_width=max(0, self.w - 2))

        right_rendered = _markup(right)
        right_w = _visible_width(right_rendered)
        right_x = self.x + self.w - 1 - right_w
        if right_x > self.x + 1 + _visible_width(left_rendered) + 2:
            buffer.draw_text(right_x, self.y, right_rendered, self.style, max_width=right_w)


# ---------------------------------------------------------------- sample text
SAMPLE = (
    "# Welcome to pen — a tiny terminal text editor with syntax highlighting.\n"
    "#\n"
    "# Edit this sample, then press Ctrl+S to save.\n"
    "\n"
    "import math\n"
    "\n"
    "\n"
    "def fibonacci(n: int) -> int:\n"
    "    a, b = 0, 1\n"
    "    for _ in range(n):\n"
    "        a, b = b, a + b\n"
    "    return a\n"
    "\n"
    "\n"
    "def show_sequence(count: int = 10) -> None:\n"
    "    for i in range(count):\n"
    "        value = fibonacci(i)\n"
    "        print(f'fib({i}) = {value}')\n"
    "\n"
    "\n"
    "# Approximate pi using the Basel series.\n"
    "def approximate_pi(terms: int = 10_000) -> float:\n"
    "    total = 0.0\n"
    "    for k in range(1, terms + 1):\n"
    "        total += 1.0 / (k * k)\n"
    "    return math.sqrt(6.0 * total)\n"
    "\n"
    "\n"
    "if __name__ == '__main__':\n"
    "    show_sequence(10)\n"
    "    print(f'pi ~= {approximate_pi():.6f}')\n"
)


# ---------------------------------------------------------------------- main
def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if path:
        try:
            editor = TextEditor.open_file(path)
        except (OSError, UnicodeDecodeError) as exc:
            print(f"pen: cannot open {path}: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        editor = TextEditor(lines=SAMPLE.rstrip("\n").split("\n"))

    editor_box = Box(title=" Editor ", border="rounded", border_style=_ST_BORDER, padding=0)
    editor_box.add(editor)

    body = VBox(gap=0)
    body.add(_TitleBar(editor))
    body.add(editor_box)
    body.add(_StatusLine(editor))

    # ``quit_keys=[]`` means the App will not auto-exit on Escape — the editor
    # uses Escape to cancel its modals; Ctrl+Q (handled by App.run) exits.
    app = App(fps=20.0, quit_keys=[])
    app.set_root(body)
    app.run()


if __name__ == "__main__":
    main()