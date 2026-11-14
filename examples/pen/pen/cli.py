# -*- coding: utf-8 -*-
"""
pen — a small, dependency-free terminal text editor built on the
ascii_colors TUI framework.

Usage:
    pen [file]

Controls (press F1 inside the editor for the full list):
    Arrows / Home / End / PgUp / PgDn   move the cursor
    Shift + arrows                      extend the selection
    Ctrl+A / Ctrl+B                     select all / toggle the selection mark
    Ctrl+C / Ctrl+X / Ctrl+V            copy / cut / paste
    Ctrl+Z / Ctrl+Y                     undo / redo
    Ctrl+S / F2                         save / save as
    Ctrl+O / Ctrl+N / F5                open / new buffer / reload from disk
    Ctrl+F / Ctrl+G                     find / go to line
    Ctrl+Q                              quit (asks before discarding changes)

The editor is not Python-specific: syntax highlighting is chosen from the
file extension (Python, JavaScript/TypeScript, C-family, JSON, shell,
TOML/INI/YAML) and falls back to plain text for everything else.

The buffer watches the file on disk. When another program rewrites it the
status line warns, saving asks for confirmation, and F5 reloads.
"""

import os
import platform
import re
import shutil
import subprocess
import sys
import time
from typing import Callable as Callback
from typing import Dict, List, Optional, Sequence, Tuple

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
_ST_COMMENT = ANSI.style_dim + RICH_COLOR_MAP.get("bright_black", "\033[90m")
_ST_STRING = RICH_COLOR_MAP.get("bright_green", "\033[92m")
_ST_NUMBER = RICH_COLOR_MAP.get("bright_cyan", "\033[96m")
_ST_KEYWORD = ANSI.style_bold + RICH_COLOR_MAP.get("bright_magenta", "\033[95m")
_ST_BUILTIN = RICH_COLOR_MAP.get("bright_blue", "\033[94m")
_ST_GUTTER = ANSI.style_dim + RICH_COLOR_MAP.get("bright_black", "\033[90m")
_ST_GUTTER_CURRENT = ANSI.style_bold + RICH_COLOR_MAP.get("bright_yellow", "\033[93m")
_ST_CURSOR = ANSI.style_reverse
_ST_SELECTION = ANSI.style_reverse
_ST_BORDER = RICH_COLOR_MAP.get("bright_cyan", "\033[96m")


# ------------------------------------------------------------------- languages
_PYTHON_KEYWORDS = frozenset(
    """
    def class if elif else for while in return yield import from as with try
    except finally raise pass break continue lambda global nonlocal assert del
    and or not is True False None async await match case
    """.split()
)
_PYTHON_BUILTINS = frozenset(
    """
    print len range str int float bool list dict set tuple open input type
    isinstance issubclass enumerate zip map filter sum min max abs sorted
    reversed any all repr id hash iter next super object Exception ValueError
    TypeError KeyError IndexError OSError RuntimeError
    """.split()
)
_JS_KEYWORDS = frozenset(
    """
    var let const function return if else for while do switch case break
    continue class extends new typeof instanceof delete in of this super yield
    async await import export from default try catch finally throw null true
    false undefined void
    """.split()
)
_C_KEYWORDS = frozenset(
    """
    int char float double void long short unsigned signed struct union enum
    typedef static const extern register volatile return if else for while do
    switch case break continue goto sizeof class public private protected
    virtual override final namespace using template typename new delete this
    nullptr true false auto import package interface extends implements throws
    try catch finally func var fn let mut pub impl trait use match loop
    """.split()
)
_SHELL_KEYWORDS = frozenset(
    """
    if then else elif fi for while do done case esac function return export
    local readonly shift set unset source alias echo exit
    """.split()
)

_LANGUAGE_SPECS: Dict[str, dict] = {
    "python": {
        "comment": "#",
        "strings": (
            r'"""(?:[^"\\]|\\.)*"""',
            r"'''(?:[^'\\]|\\.)*'''",
            r'"(?:[^"\\]|\\.)*"',
            r"'(?:[^'\\]|\\.)*'",
        ),
        "keywords": _PYTHON_KEYWORDS,
        "builtins": _PYTHON_BUILTINS,
    },
    "javascript": {
        "comment": "//",
        "strings": (r'"(?:[^"\\]|\\.)*"', r"'(?:[^'\\]|\\.)*'", r"`[^`]*`"),
        "keywords": _JS_KEYWORDS,
        "builtins": frozenset({"console", "JSON", "Math", "Object", "Array"}),
    },
    "c": {
        "comment": "//",
        "strings": (r'"(?:[^"\\]|\\.)*"', r"'(?:[^'\\]|\\.)*'"),
        "keywords": _C_KEYWORDS,
        "builtins": frozenset(),
    },
    "json": {
        "comment": None,
        "strings": (r'"(?:[^"\\]|\\.)*"',),
        "keywords": frozenset({"true", "false", "null"}),
        "builtins": frozenset(),
    },
    "shell": {
        "comment": "#",
        "strings": (r'"(?:[^"\\]|\\.)*"', r"'[^']*'"),
        "keywords": _SHELL_KEYWORDS,
        "builtins": frozenset(),
    },
    "config": {
        "comment": "#",
        "strings": (r'"(?:[^"\\]|\\.)*"', r"'[^']*'"),
        "keywords": frozenset({"true", "false", "null", "yes", "no", "on", "off"}),
        "builtins": frozenset(),
    },
}

_EXT_LANGUAGE = {
    ".py": "python", ".pyw": "python", ".pyi": "python",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".jsx": "javascript", ".ts": "javascript", ".tsx": "javascript",
    ".c": "c", ".h": "c", ".cpp": "c", ".cc": "c", ".cxx": "c", ".hpp": "c",
    ".cs": "c", ".java": "c", ".go": "c", ".rs": "c", ".kt": "c", ".swift": "c",
    ".json": "json", ".jsonc": "json",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell", ".ps1": "shell",
    ".toml": "config", ".ini": "config", ".cfg": "config", ".conf": "config",
    ".yaml": "config", ".yml": "config",
}


def _compile_spec(spec: dict) -> "re.Pattern":
    """Build the tokenizer regex for one language specification."""
    parts = []
    if spec["comment"]:
        parts.append(r"(?P<comment>%s[^\n]*)" % re.escape(spec["comment"]))
    parts.append(r"(?P<string>%s)" % "|".join(spec["strings"]))
    parts.append(r"(?P<number>\b\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?\b)")
    parts.append(r"(?P<ident>[A-Za-z_]\w*)")
    parts.append(r"(?P<space>\s+)")
    parts.append(r"(?P<other>.)")
    return re.compile("|".join(parts), re.DOTALL)


_LEXERS: Dict[str, "re.Pattern"] = {
    name: _compile_spec(spec) for name, spec in _LANGUAGE_SPECS.items()
}


def _language_for_path(path: Optional[str]) -> Optional[str]:
    """Pick a lexer name from a file extension (``None`` means plain text)."""
    if not path:
        return None
    return _EXT_LANGUAGE.get(os.path.splitext(path)[1].lower())


def _highlight(line: str, language: Optional[str]) -> List[Tuple[str, str]]:
    """Split a single source line into ``(text, ansi_style)`` tokens."""
    if not language or not line:
        return [(line, "")] if line else []
    spec = _LANGUAGE_SPECS[language]
    tokens: List[Tuple[str, str]] = []
    for match in _LEXERS[language].finditer(line):
        kind = match.lastgroup
        text = match.group(0)
        if kind == "comment":
            style = _ST_COMMENT
        elif kind == "string":
            style = _ST_STRING
        elif kind == "number":
            style = _ST_NUMBER
        elif kind == "ident" and text in spec["keywords"]:
            style = _ST_KEYWORD
        elif kind == "ident" and text in spec["builtins"]:
            style = _ST_BUILTIN
        else:
            style = ""
        tokens.append((text, style))
    return tokens


# -------------------------------------------------------------------- clipboard
def _windows_read_clipboard() -> str:
    import ctypes

    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    user32.GetClipboardData.restype = ctypes.c_void_p
    if not user32.OpenClipboard(None):
        return ""
    try:
        handle = user32.GetClipboardData(13)  # CF_UNICODETEXT
        if not handle:
            return ""
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            return ""
        try:
            return ctypes.wstring_at(pointer)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def _windows_write_clipboard(text: str) -> None:
    import ctypes

    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    payload = text.encode("utf-16-le") + b"\x00\x00"
    if not user32.OpenClipboard(None):
        return
    try:
        user32.EmptyClipboard()
        handle = kernel32.GlobalAlloc(0x0002, len(payload))  # GMEM_MOVEABLE
        if not handle:
            return
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            return
        ctypes.memmove(pointer, payload, len(payload))
        kernel32.GlobalUnlock(handle)
        user32.SetClipboardData(ctypes.c_uint(13), ctypes.c_void_p(handle))
    finally:
        user32.CloseClipboard()


def _run_clipboard_tool(command: Sequence[str]) -> str:
    completed = subprocess.run(command, capture_output=True, check=False)
    return completed.stdout.decode("utf-8", errors="replace")


def _pipe_to_clipboard_tool(command: Sequence[str], text: str) -> None:
    subprocess.run(
        command, input=text.encode("utf-8"), capture_output=True, check=False
    )


def _pick_clipboard_reader() -> Optional[Callback[[], str]]:
    system = platform.system()
    if system == "Windows":
        return _windows_read_clipboard
    if system == "Darwin":
        return lambda: _run_clipboard_tool(["pbpaste"])
    for command in (
        ["xclip", "-selection", "clipboard", "-o"],
        ["xsel", "--clipboard", "--output"],
    ):
        if shutil.which(command[0]):
            return lambda command=command: _run_clipboard_tool(command)
    return None


def _pick_clipboard_writer() -> Optional[Callback[[str], None]]:
    system = platform.system()
    if system == "Windows":
        return _windows_write_clipboard
    if system == "Darwin":
        return lambda text: _pipe_to_clipboard_tool(["pbcopy"], text)
    for command in (
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
    ):
        if shutil.which(command[0]):
            return lambda text, command=command: _pipe_to_clipboard_tool(command, text)
    return None


class _Clipboard:
    """Best-effort system clipboard with an in-process fallback."""

    def __init__(self) -> None:
        self._text = ""
        self._reader = _pick_clipboard_reader()
        self._writer = _pick_clipboard_writer()

    def copy(self, text: str) -> None:
        self._text = text
        if self._writer is None:
            return
        try:
            self._writer(text)
        except Exception:
            pass

    def paste(self) -> str:
        if self._reader is not None:
            try:
                data = self._reader()
            except Exception:
                data = ""
            if data:
                self._text = data
        return self._text


# ------------------------------------------------------------------ text helper
def _prefix_cells(line: str, column: int, tab_width: int) -> int:
    """Visible cell width of ``line[:column]`` with tab expansion."""
    cells = 0
    for char in line[:column]:
        if char == "\t":
            cells += tab_width - (cells % tab_width)
        else:
            cells += max(1, wcswidth(char))
    return cells


# ------------------------------------------------------------------ text editor
class TextEditor(Widget):
    """A scrollable, syntax-aware, multi-line text editor widget."""

    def __init__(
        self,
        lines: Optional[List[str]] = None,
        *,
        filepath: Optional[str] = None,
        indent_width: int = 4,
        tab_width: int = 8,
    ) -> None:
        super().__init__()
        self.lines: List[str] = list(lines) if lines else [""]
        if not self.lines:
            self.lines = [""]
        self.filepath = filepath
        self.language = _language_for_path(filepath)
        self.indent_width = max(1, indent_width)
        self.tab_width = max(1, tab_width)
        self.use_tabs = any(line.startswith("\t") for line in self.lines)

        self.cursor_line = 0
        self.cursor_col = 0
        self.scroll_line = 0
        self.scroll_col = 0
        self.mark: Optional[Tuple[int, int]] = None
        self.modified = False
        self.last_message = ""

        self._clipboard = _Clipboard()
        self._undo: List[Tuple[List[str], int, int]] = []
        self._redo: List[Tuple[List[str], int, int]] = []
        self._token_cache: Dict[str, List[Tuple[str, str]]] = {}
        self._disk_signature: Optional[Tuple[int, int]] = None
        self._disk_changed = False
        self._last_disk_check = 0.0
        self._search_query = ""

        self.focusable = True
        self.min_height = 5
        self.min_width = 10
        self.flex = 1
        self._refresh_disk_signature()

    # ------------------------------------------------------------ construction
    @classmethod
    def open_file(cls, path: str) -> "TextEditor":
        with open(path, "rb") as handle:
            raw = handle.read()
        if b"\x00" in raw[:4096]:
            raise ValueError("binary file")
        text = raw.decode("utf-8", errors="replace")
        return cls(lines=text.split("\n"), filepath=path)

    # ------------------------------------------------------------------ saving
    def save(self, path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        target = path or self.filepath
        if not target:
            return False, "no file path set"
        try:
            with open(target, "w", encoding="utf-8", newline="\n") as handle:
                handle.write("\n".join(self.lines))
        except OSError as exc:
            return False, str(exc)
        if target != self.filepath:
            self.filepath = target
            self.language = _language_for_path(target)
            self._token_cache.clear()
        self.modified = False
        self._refresh_disk_signature()
        self.last_message = f"saved {os.path.basename(target)}"
        return True, None

    # ------------------------------------------------------- disk change watch
    def _stat_signature(self) -> Optional[Tuple[int, int]]:
        if not self.filepath:
            return None
        try:
            stat = os.stat(self.filepath)
        except OSError:
            return None
        return (stat.st_mtime_ns, stat.st_size)

    def _refresh_disk_signature(self) -> None:
        self._disk_signature = self._stat_signature()
        self._disk_changed = False

    def _poll_disk(self) -> None:
        """Re-stat the file at most once per second and flag external edits."""
        now = time.monotonic()
        if now - self._last_disk_check >= 1.0:
            self._last_disk_check = now
            if self._disk_signature is not None:
                self._disk_changed = self._stat_signature() != self._disk_signature
        if self._disk_changed and not self.last_message:
            suffix = " (discards edits)" if self.modified else ""
            self.last_message = f"disk copy changed — Ctrl+S overwrite · F5 reload{suffix}"

    # ------------------------------------------------------------------ tokens
    def _tokens_for(self, line: str) -> List[Tuple[str, str]]:
        cached = self._token_cache.get(line)
        if cached is None:
            cached = _highlight(line, self.language)
            if len(self._token_cache) > 4096:
                self._token_cache.clear()
            self._token_cache[line] = cached
        return cached

    # --------------------------------------------------------------- selection
    def _selection_bounds(self) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        if self.mark is None:
            return None
        cursor = (self.cursor_line, self.cursor_col)
        if self.mark == cursor:
            return None
        return (self.mark, cursor) if self.mark < cursor else (cursor, self.mark)

    def _line_selection(
        self,
        selection: Optional[Tuple[Tuple[int, int], Tuple[int, int]]],
        line_index: int,
    ) -> Tuple[Optional[int], Optional[int]]:
        if selection is None:
            return (None, None)
        (first_line, first_col), (last_line, last_col) = selection
        if line_index < first_line or line_index > last_line:
            return (None, None)
        start = first_col if line_index == first_line else 0
        end = last_col if line_index == last_line else len(self.lines[line_index])
        return (start, end)

    def _selected_text(self) -> str:
        selection = self._selection_bounds()
        if selection is None:
            return ""
        (first_line, first_col), (last_line, last_col) = selection
        if first_line == last_line:
            return self.lines[first_line][first_col:last_col]
        parts = [self.lines[first_line][first_col:]]
        parts.extend(self.lines[i] for i in range(first_line + 1, last_line))
        parts.append(self.lines[last_line][:last_col])
        return "\n".join(parts)

    def _delete_selection(self) -> bool:
        selection = self._selection_bounds()
        if selection is None:
            return False
        (first_line, first_col), (last_line, last_col) = selection
        merged = self.lines[first_line][:first_col] + self.lines[last_line][last_col:]
        self.lines[first_line : last_line + 1] = [merged]
        self.cursor_line, self.cursor_col = first_line, first_col
        self.mark = None
        return True

    # -------------------------------------------------------------- undo stack
    def _snapshot(self) -> None:
        self._undo.append((list(self.lines), self.cursor_line, self.cursor_col))
        if len(self._undo) > 500:
            del self._undo[0]
        self._redo.clear()

    def _restore(self, state: Tuple[List[str], int, int]) -> None:
        lines, line, column = state
        self.lines = list(lines)
        self.cursor_line, self.cursor_col = line, column
        self.mark = None
        self._token_cache.clear()

    def undo(self) -> None:
        if not self._undo:
            return
        self._redo.append((list(self.lines), self.cursor_line, self.cursor_col))
        self._restore(self._undo.pop())
        self.modified = True
        self.last_message = "undo"

    def redo(self) -> None:
        if not self._redo:
            return
        self._undo.append((list(self.lines), self.cursor_line, self.cursor_col))
        self._restore(self._redo.pop())
        self.modified = True
        self.last_message = "redo"

    # --------------------------------------------------------------- insertion
    def _insert_text(self, text: str) -> None:
        if not text:
            return
        self._snapshot()
        self._delete_selection()
        parts = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        line = self.lines[self.cursor_line]
        head, tail = line[: self.cursor_col], line[self.cursor_col:]
        if len(parts) == 1:
            self.lines[self.cursor_line] = head + parts[0] + tail
            self.cursor_col += len(parts[0])
        else:
            replacement = [head + parts[0]]
            replacement.extend(parts[1:-1])
            replacement.append(parts[-1] + tail)
            self.lines[self.cursor_line : self.cursor_line + 1] = replacement
            self.cursor_line += len(parts) - 1
            self.cursor_col = len(parts[-1])
        self.modified = True

    # ------------------------------------------------------------------ scroll
    def _sync_scroll(self, text_width: int) -> None:
        self.cursor_line = max(0, min(len(self.lines) - 1, self.cursor_line))
        self.cursor_col = max(0, min(len(self.lines[self.cursor_line]), self.cursor_col))

        if self.cursor_line < self.scroll_line:
            self.scroll_line = self.cursor_line
        elif self.cursor_line >= self.scroll_line + self.h:
            self.scroll_line = self.cursor_line - self.h + 1
        self.scroll_line = max(0, min(self.scroll_line, max(0, len(self.lines) - 1)))

        cursor_cells = _prefix_cells(
            self.lines[self.cursor_line], self.cursor_col, self.tab_width
        )
        if cursor_cells < self.scroll_col:
            self.scroll_col = cursor_cells
        elif cursor_cells >= self.scroll_col + text_width:
            self.scroll_col = cursor_cells - text_width + 1
        self.scroll_col = max(0, self.scroll_col)

    # -------------------------------------------------------------------- draw
    def _gutter(self) -> int:
        return max(3, len(str(len(self.lines))) + 1)

    def _char_cells(self, char: str, cell: int) -> int:
        if char == "\t":
            return self.tab_width - (cell % self.tab_width)
        return max(1, wcswidth(char))

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        self._poll_disk()
        gutter = self._gutter()
        text_width = self.w - gutter
        if text_width <= 0:
            return
        self._sync_scroll(text_width)
        selection = self._selection_bounds()
        for row in range(self.h):
            line_index = self.scroll_line + row
            y = self.y + row
            if line_index >= len(self.lines):
                buffer.put(self.x, y, " " * self.w, "")
                continue
            self._draw_line(buffer, line_index, y, text_width, gutter, selection)

    def _draw_line(
        self,
        buffer: ScreenBuffer,
        line_index: int,
        y: int,
        text_width: int,
        gutter: int,
        selection: Optional[Tuple[Tuple[int, int], Tuple[int, int]]],
    ) -> None:
        line = self.lines[line_index]
        is_current = line_index == self.cursor_line and self._focused
        number_style = _ST_GUTTER_CURRENT if is_current else _ST_GUTTER
        buffer.put(self.x, y, f"{line_index + 1:>{gutter - 1}} ", number_style)

        sel_start, sel_end = self._line_selection(selection, line_index)
        start_x = self.x + gutter
        cell = 0
        index = 0
        for chunk, style in self._tokens_for(line):
            for char in chunk:
                width = self._char_cells(char, cell)
                selected = (
                    sel_start is not None
                    and sel_end is not None
                    and sel_start <= index < sel_end
                )
                if cell >= self.scroll_col and cell < self.scroll_col + text_width:
                    x = start_x + (cell - self.scroll_col)
                    visible = min(width, self.scroll_col + text_width - cell)
                    self._draw_char(buffer, x, y, char, visible, style, selected)
                cell += width
                index += 1
                if cell >= self.scroll_col + text_width:
                    break
            else:
                continue
            break

        if is_current:
            cursor_cells = _prefix_cells(line, self.cursor_col, self.tab_width)
            if self.scroll_col <= cursor_cells < self.scroll_col + text_width:
                x = start_x + (cursor_cells - self.scroll_col)
                char = line[self.cursor_col] if self.cursor_col < len(line) else " "
                self._draw_char(buffer, x, y, char, 1, "", False, _ST_CURSOR)

    def _draw_char(
        self,
        buffer: ScreenBuffer,
        x: int,
        y: int,
        char: str,
        width: int,
        style: str,
        selected: bool,
        override: str = "",
    ) -> None:
        cell_style = override or (style + _ST_SELECTION if selected else style)
        if char == "\t":
            buffer.put(x, y, " " * max(1, width), cell_style)
            return
        buffer.set_cell(x, y, char, cell_style)
        if width >= 2:
            buffer.set_cell(x + 1, y, "", cell_style)

    # ------------------------------------------------------------ edit helpers
    def _move(self, delta_line: int, delta_col: int, extend: bool = False) -> None:
        if extend and self.mark is None:
            self.mark = (self.cursor_line, self.cursor_col)
        elif not extend:
            self.mark = None
        line = max(0, min(len(self.lines) - 1, self.cursor_line + delta_line))
        column = max(0, min(len(self.lines[line]), self.cursor_col + delta_col))
        self.cursor_line, self.cursor_col = line, column

    def _move_to(self, line: int, column: int, extend: bool = False) -> None:
        if extend and self.mark is None:
            self.mark = (self.cursor_line, self.cursor_col)
        elif not extend:
            self.mark = None
        self.cursor_line = max(0, min(len(self.lines) - 1, line))
        self.cursor_col = max(0, min(len(self.lines[self.cursor_line]), column))

    def _copy(self) -> None:
        text = self._selected_text()
        if text:
            self.last_message = "copied selection"
        else:
            text = self.lines[self.cursor_line]
            self.last_message = "copied line"
        self._clipboard.copy(text)
        self.mark = None

    def _cut(self) -> None:
        text = self._selected_text()
        self._snapshot()
        if text:
            self._clipboard.copy(text)
            self._delete_selection()
            self.last_message = "cut selection"
        else:
            self._clipboard.copy(self.lines[self.cursor_line])
            del self.lines[self.cursor_line]
            if not self.lines:
                self.lines = [""]
            self.cursor_line = min(self.cursor_line, len(self.lines) - 1)
            self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_line]))
            self.last_message = "cut line"
        self.modified = True

    def _paste(self) -> None:
        text = self._clipboard.paste()
        if not text:
            self.last_message = "clipboard is empty"
            return
        self._insert_text(text)
        self.last_message = "pasted"

    def _select_all(self) -> None:
        self.mark = (0, 0)
        self.cursor_line = len(self.lines) - 1
        self.cursor_col = len(self.lines[-1])

    def _toggle_mark(self) -> None:
        self.mark = None if self.mark is not None else (self.cursor_line, self.cursor_col)
        self.last_message = "selection mark set" if self.mark else "selection cleared"

    # -------------------------------------------------------------- key input
    def handle_key(self, key: str) -> bool:
        self.last_message = ""

        if key == "F1":
            self._show_help()
            return True
        if key == "F2":
            self._prompt_save_as()
            return True
        if key == "F5":
            self._reload()
            return True
        if key == "ESCAPE":
            self.mark = None
            return True

        shortcuts = {
            "CTRL_C": self._copy,
            "\x18": self._cut,          # Ctrl+X
            "\x16": self._paste,        # Ctrl+V
            "\x01": self._select_all,   # Ctrl+A
            "\x02": self._toggle_mark,  # Ctrl+B
            "\x1a": self.undo,          # Ctrl+Z
            "\x19": self.redo,          # Ctrl+Y
            "\x13": self._request_save,  # Ctrl+S
            "\x0f": self._request_open,  # Ctrl+O
            "\x0e": self._request_new,   # Ctrl+N
            "\x06": self._prompt_find,   # Ctrl+F
            "\x07": self._prompt_goto,   # Ctrl+G
            "CTRL_Q": self._request_quit,
        }
        handler = shortcuts.get(key)
        if handler is not None:
            handler()
            return True

        extend = key.startswith("SHIFT_")
        name = key[len("SHIFT_") :] if extend else key
        steps = {
            "LEFT": (0, -1),
            "RIGHT": (0, 1),
            "UP": (-1, 0),
            "DOWN": (1, 0),
        }
        if name in steps:
            self._move(*steps[name], extend=extend)
            return True
        if name == "HOME":
            self._move_to(self.cursor_line, 0, extend)
            return True
        if name == "END":
            self._move_to(self.cursor_line, len(self.lines[self.cursor_line]), extend)
            return True
        if name == "PAGE_UP":
            self._move_to(max(0, self.cursor_line - max(1, self.h)), self.cursor_col, extend)
            return True
        if name == "PAGE_DOWN":
            target = min(len(self.lines) - 1, self.cursor_line + max(1, self.h))
            self._move_to(target, self.cursor_col, extend)
            return True

        if key == "TAB":
            self._insert_text("\t" if self.use_tabs else " " * self.indent_width)
            return True

        if key == "ENTER":
            self._snapshot()
            self._delete_selection()
            line = self.lines[self.cursor_line]
            head, tail = line[: self.cursor_col], line[self.cursor_col:]
            indent = re.match(r"[ \t]*", head).group(0) if not head.strip() else ""
            self.lines[self.cursor_line] = head
            self.lines.insert(self.cursor_line + 1, indent + tail)
            self.cursor_line += 1
            self.cursor_col = len(indent)
            self.modified = True
            return True

        if key == "BACKSPACE":
            if self._selection_bounds() is not None:
                self._snapshot()
                self._delete_selection()
                self.modified = True
            elif self.cursor_col > 0:
                self._snapshot()
                line = self.lines[self.cursor_line]
                self.lines[self.cursor_line] = (
                    line[: self.cursor_col - 1] + line[self.cursor_col :]
                )
                self.cursor_col -= 1
                self.modified = True
            elif self.cursor_line > 0:
                self._snapshot()
                previous = self.lines[self.cursor_line - 1]
                self.lines[self.cursor_line - 1] = previous + self.lines[self.cursor_line]
                self.lines.pop(self.cursor_line)
                self.cursor_line -= 1
                self.cursor_col = len(previous)
                self.modified = True
            return True

        if key == "DELETE":
            line = self.lines[self.cursor_line]
            if self._selection_bounds() is not None:
                self._snapshot()
                self._delete_selection()
                self.modified = True
            elif self.cursor_col < len(line):
                self._snapshot()
                self.lines[self.cursor_line] = (
                    line[: self.cursor_col] + line[self.cursor_col + 1 :]
                )
                self.modified = True
            elif self.cursor_line < len(self.lines) - 1:
                self._snapshot()
                self.lines[self.cursor_line] = line + self.lines[self.cursor_line + 1]
                self.lines.pop(self.cursor_line + 1)
                self.modified = True
            return True

        if len(key) == 1 and key.isprintable():
            self._insert_text(key)
            return True

        return False

    # ------------------------------------------------------------ file actions
    def _confirm(
        self,
        title: str,
        message: str,
        on_confirm: Optional[Callback[[], None]] = None,
        on_decline: Optional[Callback[[], None]] = None,
        on_dismiss: Optional[Callback[[], None]] = None,
    ) -> None:
        if self._app is None:
            return
        self._app.push_modal(
            _ConfirmDialog(title, message, on_confirm, on_decline, on_dismiss)
        )

    def _save_now(self, on_success: Optional[Callback[[], None]] = None) -> None:
        if not self.filepath:
            self._prompt_save_as(on_success)
            return
        success, error = self.save()
        if not success:
            self.last_message = f"save failed: {error}"
            return
        if on_success is not None:
            on_success()

    def _request_save(self) -> None:
        if self.filepath and self._disk_changed:
            self._confirm(
                " Overwrite? ",
                "The file changed on disk since it was opened.\n"
                "Overwrite it with the editor buffer?",
                on_confirm=self._save_now,
            )
            return
        self._save_now()

    def _prompt_save_as(self, on_success: Optional[Callback[[], None]] = None) -> None:
        if self._app is None:
            return
        app = self._app
        default_name = os.path.basename(self.filepath) if self.filepath else "untitled.txt"
        dialog = _ModalTextInput(value=default_name, placeholder="path or file name")

        def submit(text: str) -> None:
            app.pop_modal()
            path = text.strip()
            if not path:
                return
            success, error = self.save(path)
            if not success:
                self.last_message = f"save failed: {error}"
                return
            if on_success is not None:
                on_success()

        dialog.on_submit = submit
        dialog.on_escape = app.pop_modal
        app.push_modal(
            _build_dialog(" Save As ", "Save file as:", dialog, "Enter save · Esc cancel")
        )

    def _request_open(self) -> None:
        if self.modified:
            self._confirm(
                " Unsaved changes ",
                "Save the current buffer before opening another file?",
                on_confirm=lambda: self._save_now(self._prompt_open),
                on_decline=self._prompt_open,
            )
            return
        self._prompt_open()

    def _prompt_open(self) -> None:
        if self._app is None:
            return
        app = self._app
        dialog = _ModalTextInput(
            value=self.filepath or "", placeholder="path/to/file"
        )

        def submit(text: str) -> None:
            app.pop_modal()
            path = text.strip()
            if not path:
                return
            try:
                loaded = TextEditor.open_file(path)
            except (OSError, ValueError) as exc:
                self.last_message = f"open failed: {exc}"
                return
            self.lines = loaded.lines
            self.filepath = loaded.filepath
            self.language = loaded.language
            self.use_tabs = loaded.use_tabs
            self._token_cache.clear()
            self.cursor_line = self.cursor_col = 0
            self.scroll_line = self.scroll_col = 0
            self.mark = None
            self.modified = False
            self._undo.clear()
            self._redo.clear()
            self._refresh_disk_signature()
            self.last_message = f"opened {os.path.basename(path)}"

        dialog.on_submit = submit
        dialog.on_escape = app.pop_modal
        app.push_modal(
            _build_dialog(" Open File ", "Open file:", dialog, "Enter open · Esc cancel")
        )

    def _request_new(self) -> None:
        if self.modified:
            self._confirm(
                " Unsaved changes ",
                "Save the current buffer before starting a new file?",
                on_confirm=lambda: self._save_now(self._reset_buffer),
                on_decline=self._reset_buffer,
            )
            return
        self._reset_buffer()

    def _reset_buffer(self) -> None:
        self.lines = [""]
        self.filepath = None
        self.language = None
        self.use_tabs = False
        self._token_cache.clear()
        self.cursor_line = self.cursor_col = 0
        self.scroll_line = self.scroll_col = 0
        self.mark = None
        self.modified = False
        self._undo.clear()
        self._redo.clear()
        self._disk_signature = None
        self._disk_changed = False
        self._search_query = ""
        self.last_message = "new buffer"

    def _reload(self) -> None:
        if not self.filepath:
            self.last_message = "nothing to reload"
            return
        if self.modified:
            self._confirm(
                " Reload ",
                "Discard unsaved changes and reload from disk?",
                on_confirm=self._reload_now,
            )
            return
        self._reload_now()

    def _reload_now(self) -> None:
        try:
            loaded = TextEditor.open_file(self.filepath)
        except (OSError, ValueError) as exc:
            self.last_message = f"reload failed: {exc}"
            return
        self.lines = loaded.lines
        self.language = loaded.language
        self.use_tabs = loaded.use_tabs
        self._token_cache.clear()
        self.cursor_line = self.cursor_col = 0
        self.scroll_line = self.scroll_col = 0
        self.mark = None
        self.modified = False
        self._undo.clear()
        self._redo.clear()
        self._refresh_disk_signature()
        self.last_message = "reloaded from disk"

    def _request_quit(self) -> None:
        if self._app is None:
            return
        if not self.modified:
            self._app.exit()
            return
        self._confirm(
            " Unsaved changes ",
            "Save the buffer before quitting?",
            on_confirm=lambda: self._save_now(self._app.exit),
            on_decline=self._app.exit,
        )

    # ------------------------------------------------------------ navigation
    def _prompt_find(self) -> None:
        if self._app is None:
            return
        app = self._app
        dialog = _ModalTextInput(value=self._search_query, placeholder="search text")

        def submit(text: str) -> None:
            app.pop_modal()
            if not text:
                return
            self._search_query = text
            self._find_next(text)

        dialog.on_submit = submit
        dialog.on_escape = app.pop_modal
        app.push_modal(
            _build_dialog(" Find ", "Search for:", dialog, "Enter search · Esc cancel")
        )

    def _find_next(self, query: str) -> None:
        start_line, start_col = self.cursor_line, self.cursor_col
        if self.lines[start_line].startswith(query, start_col):
            start_col += len(query)
        for offset in range(len(self.lines)):
            index = (start_line + offset) % len(self.lines)
            column = self.lines[index].find(query, start_col if offset == 0 else 0)
            if column != -1:
                self.cursor_line, self.cursor_col = index, column
                self.mark = (index, column + len(query))
                self.last_message = f"found '{query}'"
                return
        self.last_message = f"'{query}' not found"

    def _prompt_goto(self) -> None:
        if self._app is None:
            return
        app = self._app
        dialog = _ModalTextInput(placeholder="line number")

        def submit(text: str) -> None:
            app.pop_modal()
            try:
                number = int(text.strip())
            except ValueError:
                self.last_message = "not a line number"
                return
            if 1 <= number <= len(self.lines):
                self.cursor_line = number - 1
                self.cursor_col = 0
                self.mark = None
            else:
                self.last_message = f"line {number} out of range"

        dialog.on_submit = submit
        dialog.on_escape = app.pop_modal
        app.push_modal(
            _build_dialog(" Go to line ", "Line number:", dialog, "Enter jump · Esc cancel")
        )

    def _show_help(self) -> None:
        if self._app is None:
            return
        self._app.push_modal(_HelpDialog())


# --------------------------------------------------------------- modal helpers
class _ModalTextInput(TextInput):
    """A ``TextInput`` that can be dismissed with ``ESCAPE``."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.on_escape: Optional[Callback[[], None]] = None

    def handle_key(self, key: str) -> bool:
        if key == "ESCAPE":
            if self.on_escape is not None:
                self.on_escape()
            return True
        return super().handle_key(key)


class _ConfirmDialog(Box):
    """A compact modal that answers to single keypresses."""

    def __init__(
        self,
        title: str,
        message: str,
        on_confirm: Optional[Callback[[], None]] = None,
        on_decline: Optional[Callback[[], None]] = None,
        on_dismiss: Optional[Callback[[], None]] = None,
    ) -> None:
        super().__init__(
            title=title, border="rounded", border_style=_ST_BORDER, padding=1
        )
        self.on_confirm = on_confirm
        self.on_decline = on_decline
        self.on_dismiss = on_dismiss
        lines = message.split("\n")
        for line in lines:
            self.add(Label(line))
        self.add(Divider())
        self.add(Label("[dim]Enter / y confirm · n decline · Esc cancel[/dim]"))
        self.focusable = True
        self.w = 68
        self.h = len(lines) + 6

    def handle_key(self, key: str) -> bool:
        if key in ("ENTER", "y", "Y", " "):
            self._finish(self.on_confirm)
            return True
        if key in ("n", "N"):
            self._finish(self.on_decline)
            return True
        if key == "ESCAPE":
            self._finish(self.on_dismiss)
            return True
        return False

    def _finish(self, callback: Optional[Callback[[], None]]) -> None:
        if self._app is not None:
            self._app.pop_modal()
        if callback is not None:
            callback()


_HELP_LINES = [
    "Arrows · Home · End · PgUp · PgDn     move the cursor",
    "Shift + arrows                        extend the selection",
    "Ctrl+A / Ctrl+B                       select all / toggle mark",
    "Ctrl+C · Ctrl+X · Ctrl+V              copy · cut · paste",
    "Ctrl+Z · Ctrl+Y                       undo · redo",
    "Ctrl+S · F2                           save · save as",
    "Ctrl+O · Ctrl+N · F5                  open · new · reload",
    "Ctrl+F · Ctrl+G                       find · go to line",
    "Ctrl+Q                                quit",
]


class _HelpDialog(Box):
    """A modal listing every shortcut."""

    def __init__(self) -> None:
        super().__init__(
            title=" Shortcuts ", border="rounded", border_style=_ST_BORDER, padding=1
        )
        for line in _HELP_LINES:
            self.add(Label(line))
        self.add(Divider())
        self.add(Label("[dim]Press Esc or Enter to close[/dim]"))
        self.focusable = True
        self.w = 68
        self.h = len(_HELP_LINES) + 7

    def handle_key(self, key: str) -> bool:
        if key in ("ESCAPE", "ENTER", "q"):
            if self._app is not None:
                self._app.pop_modal()
            return True
        return False


def _build_dialog(title: str, prompt: str, input_widget: TextInput, hint: str) -> Box:
    box = Box(title=title, border="rounded", border_style=_ST_BORDER, padding=1)
    box.add(Label(f"[bold]{prompt}[/bold]"))
    box.add(input_widget)
    box.add(Divider())
    box.add(Label(f"[dim]{hint}[/dim]"))
    box.w = 64
    box.h = 8
    return box


# ------------------------------------------------------------------ chrome bars
class _TitleBar(Widget):
    """The top line: application name, file name, language and flags."""

    def __init__(self, editor: TextEditor) -> None:
        super().__init__()
        self.editor = editor
        self.min_height = 1
        self.flex = 0

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0:
            return
        editor = self.editor
        name = editor.filepath or "untitled"
        language = f" [dim]({editor.language or 'text'})[/dim]"
        flags = ""
        if editor.modified:
            flags += " [yellow]●[/yellow]"
        if editor._disk_changed:
            flags += " [red]⚠[/red]"
        text = (
            f" [bold bright_cyan]◈ pen[/bold bright_cyan]"
            f"  [dim]│[/dim]  [white]{name}[/white]{language}{flags}"
        )
        buffer.put(self.x, self.y, " " * self.w, self.style)
        buffer.draw_text(self.x, self.y, _markup(text), self.style, max_width=self.w)


class _StatusLine(Widget):
    """The bottom line: position or message, plus the most used shortcuts."""

    def __init__(self, editor: TextEditor) -> None:
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
        right = "[dim]Ctrl+S save · F1 help · Ctrl+Q quit[/dim]"

        left_rendered = _markup(left)
        buffer.draw_text(
            self.x + 1, self.y, left_rendered, self.style, max_width=max(0, self.w - 2)
        )

        right_rendered = _markup(right)
        right_width = _visible_width(right_rendered)
        right_x = self.x + self.w - 1 - right_width
        if right_x > self.x + 1 + _visible_width(left_rendered) + 2:
            buffer.draw_text(right_x, self.y, right_rendered, self.style, max_width=right_width)


# ---------------------------------------------------------------------- main
def _parse_path(args: List[str]) -> Tuple[Optional[str], Optional[int]]:
    """Return ``(path, exit_code)``. ``exit_code`` is set when the CLI
    should terminate immediately (help / version / bad option)."""
    if not args:
        return None, None
    first = args[0]
    if first in ("-h", "--help"):
        print(__doc__)
        return None, 0
    if first in ("-v", "--version", "-V"):
        from pen import __version__

        print(f"pen {__version__}")
        return None, 0
    if first.startswith("-"):
        print(f"pen: unknown option {first}", file=sys.stderr)
        print("Try 'pen --help' for more information.", file=sys.stderr)
        return None, 2
    return first, None


def _load_editor(path: Optional[str]) -> Tuple[Optional[TextEditor], Optional[int]]:
    """Return ``(editor, exit_code)``. ``editor`` is ``None`` on failure."""
    if path is None:
        return TextEditor(), None
    if os.path.exists(path):
        try:
            return TextEditor.open_file(path), None
        except (OSError, ValueError) as exc:
            print(f"pen: cannot open {path}: {exc}", file=sys.stderr)
            return None, 1
    # Non-existent path: start with an empty buffer pre-bound to the path so
    # the first Ctrl+S will create the file.
    return TextEditor(filepath=path), None


def main() -> int:
    """Console-script entry point."""
    path, early = _parse_path(sys.argv[1:])
    if early is not None:
        return early

    editor, error = _load_editor(path)
    if editor is None:
        return error or 1

    editor_box = Box(title=" Editor ", border="rounded", border_style=_ST_BORDER)
    editor_box.add(editor)

    body = VBox(gap=0)
    body.add(_TitleBar(editor))
    body.add(editor_box)
    body.add(_StatusLine(editor))

    # ``quit_keys=[]`` keeps Escape free for the editor (clearing selections)
    # and lets Ctrl+C / Ctrl+Q reach the widget, which owns the save prompt.
    app = App(fps=20.0, quit_keys=[])
    app.set_root(body)
    try:
        app.run()
    except RuntimeError as exc:
        # e.g. ``pen file.py | cat`` — app.run() refuses a non-TTY stream.
        print(f"pen: {exc}", file=sys.stderr)
        return 1
    return 0