# -*- coding: utf-8 -*-
"""Advanced transcript widgets used by :mod:`ascii_colors.tui.chatbot`."""

import time
from datetime import datetime
from typing import List, Optional, Tuple

from ascii_colors.constants import ANSI
from ascii_colors.rich.layout import wrap_line_preserving_ansi
from ascii_colors.rich.style import RICH_COLOR_MAP
from ascii_colors.tui.screen import ScreenBuffer
from ascii_colors.tui.widgets import (
    BigText,
    ChatView,
    _CYAN,
    _DIM,
    _draw_scrollbar,
    _markup,
    _visible_width,
)

_WHITE = RICH_COLOR_MAP.get("bright_white", "\033[97m")
_GREEN = RICH_COLOR_MAP.get("bright_green", "\033[92m")
_YELLOW = RICH_COLOR_MAP.get("bright_yellow", "\033[93m")
_MAGENTA = RICH_COLOR_MAP.get("bright_magenta", "\033[95m")
_RED = RICH_COLOR_MAP.get("bright_red", "\033[91m")
_BLUE = RICH_COLOR_MAP.get("bright_blue", "\033[94m")
_CODE_BG = RICH_COLOR_MAP.get("bg_black", "\033[40m")


class RichChatView(ChatView):
    """A responsive, card-oriented chat transcript.

    In addition to the plain message dictionaries accepted by ``ChatView``,
    messages may contain ``timestamp``, ``elapsed``, ``tokens`` and ``status``
    metadata. Markdown code fences receive a distinct code treatment, tool
    calls use compact activity cards, and empty assistant messages display an
    animated thinking indicator while tokens are being generated.
    """

    def __init__(self, *args, show_timestamps: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_timestamps = show_timestamps
        self._visual_lines: List[Tuple[str, str, str]] = []
        self._clock = time.monotonic()

    def _timestamp(self, message: dict) -> str:
        if not self.show_timestamps:
            return ""
        value = message.get("timestamp")
        if not value:
            return ""
        if isinstance(value, str):
            return value
        try:
            return datetime.fromtimestamp(float(value)).strftime("%H:%M")
        except (TypeError, ValueError, OSError):
            return ""

    def _header(self, index: int, message: dict) -> Tuple[str, str, str]:
        role = message.get("role", "assistant")
        labels = {
            "user": self.user_label,
            "assistant": self.assistant_label,
            "system": self.system_label,
            "tool": self.tool_label,
            "error": self.error_label,
        }
        icons = {"user": "›", "assistant": "●", "system": "◆", "tool": "⚙", "error": "!"}
        styles = {
            "user": ANSI.style_bold + _CYAN,
            "assistant": ANSI.style_bold + _GREEN,
            "system": _DIM + _YELLOW,
            "tool": ANSI.style_bold + _MAGENTA,
            "error": ANSI.style_bold + _RED,
        }
        role = role if role in labels else "assistant"
        metadata = []
        timestamp = self._timestamp(message)
        if timestamp:
            metadata.append(timestamp)
        if message.get("status"):
            metadata.append(str(message["status"]))
        if message.get("elapsed") is not None:
            metadata.append(f"{float(message['elapsed']):.1f}s")
        if message.get("tokens"):
            metadata.append(f"~{int(message['tokens'])} tok")
        suffix = f"  ·  {' · '.join(metadata)}" if metadata else ""
        title = f"{icons[role]} {labels[role]}{suffix}"
        align = "right" if role == "user" else "left"
        return align, title, styles[role]

    @staticmethod
    def _empty_assistant(message: dict) -> bool:
        return (
            message.get("role") == "assistant"
            and not (message.get("content") or "").strip()
        )

    def _append_welcome(self, message: dict, width: int) -> None:
        """Render the responsive lollms welcome hero inside the transcript."""
        self._visual_lines.append(("center", "", ""))
        banner = BigText(
            "LOLLMS",
            shadow=True,
            style="[bold bright_yellow]",
            shadow_style="magenta",
        )
        grid = banner._layout_glyphs()
        art_width = len(grid[0]) if grid and grid[0] else 0

        if art_width <= width:
            main_style = ANSI.style_bold + _YELLOW
            shadow_style = _MAGENTA
            for row in grid:
                parts: List[str] = []
                active_kind = None
                for kind in row + [None]:
                    if kind != active_kind:
                        if active_kind == "main":
                            parts.append(ANSI.color_reset)
                        elif active_kind == "shadow":
                            parts.append(ANSI.color_reset)
                        if kind == "main":
                            parts.append(main_style)
                        elif kind == "shadow":
                            parts.append(shadow_style)
                        active_kind = kind
                    if kind is not None:
                        parts.append("█" if kind else " ")
                self._visual_lines.append(("center", "".join(parts), ""))
        else:
            # Narrow terminals retain the identity without clipping the font.
            for line in ("╭─────╮", "│ ● ● │", "╰─┬┬┬─╯"):
                self._visual_lines.append(("center", line, ANSI.style_bold + _YELLOW))
            self._visual_lines.append(
                ("center", "L O L L M S", ANSI.style_bold + _YELLOW)
            )

        self._visual_lines.append(("center", "", ""))
        tagline = message.get("content") or "Local intelligence. Beautifully connected."
        self._visual_lines.append(
            ("center", _markup(f"[bold bright_white]{tagline}[/bold bright_white]"), _WHITE)
        )
        self._visual_lines.append(
            ("center", "─" * min(42, max(8, width - 4)), _DIM + _MAGENTA)
        )
        hint = (
            "Start typing below  ·  /help for commands  ·  Ctrl+N for a new chat"
            if width >= 48
            else "Type below to begin  ·  /help"
        )
        self._visual_lines.append(("center", hint, _DIM + _CYAN))

    def _append_content(self, message: dict, width: int) -> None:
        role = message.get("role", "assistant")
        content = message.get("content", "") or ""
        if role == "welcome":
            self._append_welcome(message, width)
            return
        if self._empty_assistant(message):
            frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
            frame = frames[int((time.monotonic() - self._clock) * 10) % len(frames)]
            self._visual_lines.append(("left", f"  {frame} thinking…", _DIM + _YELLOW))
            return

        align = "right" if role == "user" else "left"
        base_style = _WHITE if role in ("user", "assistant") else _DIM
        if role == "error":
            base_style = _RED
        in_code = False
        code_language = ""
        for raw_line in content.split("\n"):
            stripped = raw_line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                if in_code:
                    code_language = stripped[3:].strip() or "code"
                    self._visual_lines.append(
                        ("left", f"  ╭─ {code_language}", _DIM + _BLUE)
                    )
                else:
                    self._visual_lines.append(("left", "  ╰─", _DIM + _BLUE))
                    code_language = ""
                continue

            if in_code:
                line = f"  │ {raw_line}"
                style = _GREEN + _CODE_BG
                wrapped = wrap_line_preserving_ansi(line, max(4, width))
                for part in wrapped:
                    self._visual_lines.append(("left", part, style))
                continue

            if stripped.startswith(("- ", "* ")):
                rendered = _markup(f"  • {stripped[2:]}")
            elif stripped.startswith("#"):
                rendered = _markup(f"[bold]{stripped.lstrip('#').strip()}[/bold]")
            else:
                rendered = _markup(raw_line)
            prefix = "  " if role != "user" else ""
            for part in wrap_line_preserving_ansi(prefix + rendered, max(4, width)):
                self._visual_lines.append((align, part, base_style))
        if not content:
            self._visual_lines.append((align, "", base_style))

    def _rebuild_lines_if_needed(self) -> None:
        available_width = max(8, self.w - 3)
        if not self._dirty and self._last_width == available_width:
            return
        self._last_width = available_width
        self._dirty = False
        self._visual_lines = []

        for index, message in enumerate(self.messages):
            if index:
                self._visual_lines.append(("left", "", ""))
            if self.show_labels and message.get("role") != "welcome":
                align, title, style = self._header(index, message)
                self._visual_lines.append((align, title, style))
            card_width = available_width
            if self.w >= 64:
                card_width = max(32, int(available_width * 0.86))
            self._append_content(message, card_width)

        # Keep the base class's scrolling API working without duplicating it.
        self._lines = self._visual_lines

    def draw(self, buffer: ScreenBuffer) -> None:
        if self.w <= 0 or self.h <= 0:
            return
        self._rebuild_lines_if_needed()
        total = len(self._visual_lines)
        max_scroll = max(0, total - self.h)
        if self._auto_scroll:
            self.scroll = max_scroll
        else:
            self.scroll = max(0, min(self.scroll, max_scroll))

        has_scrollbar = total > self.h
        content_width = max(1, self.w - (1 if has_scrollbar else 0))
        for row in range(self.h):
            y = self.y + row
            buffer.put(self.x, y, " " * self.w, self.style)
            index = self.scroll + row
            if index >= total:
                continue
            align, text, style = self._visual_lines[index]
            if not text:
                continue
            text_width = min(content_width, _visible_width(text))
            x = self.x
            if align == "right":
                x = self.x + max(0, content_width - text_width - 1)
            elif align == "center":
                x = self.x + max(0, (content_width - text_width) // 2)
            buffer.draw_text(x, y, text, style, max_width=max(0, self.x + content_width - x))

        if has_scrollbar:
            _draw_scrollbar(
                buffer,
                self.x + self.w - 1,
                self.y,
                self.h,
                total,
                self.h,
                self.scroll,
                _CYAN,
            )