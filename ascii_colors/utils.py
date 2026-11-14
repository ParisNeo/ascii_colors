import inspect
import os
import platform
import re
import shutil
import sys
import traceback
from pathlib import Path
from typing import List, Optional

from ascii_colors.constants import ANSI

if platform.system() == "Windows":
    import msvcrt
else:
    import select
    import termios
    import tty

ANSI_ESCAPE_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

_KEY_MAP_WINDOWS = {
    "H": "UP",
    "P": "DOWN",
    "K": "LEFT",
    "M": "RIGHT",
    "G": "HOME",
    "O": "END",
    "S": "DELETE",
    "I": "PAGE_UP",
    "Q": "PAGE_DOWN",
    # Function keys arrive after a NUL prefix as their raw ASCII code.
    ";": "F1",
    "<": "F2",
    "=": "F3",
    ">": "F4",
    "?": "F5",
    "@": "F6",
    "A": "F7",
    "B": "F8",
    "C": "F9",
    "D": "F10",
    # F11 / F12 use the 0xE0 prefix on modern consoles.
    "\x85": "F11",
    "\x86": "F12",
}

_KEY_MAP_WINDOWS_REGULAR = {
    "\r": "ENTER",
    "\n": "ENTER",
    "\x03": "CTRL_C",
    "\x11": "CTRL_Q",
    "\x08": "BACKSPACE",
    "\x1b": "ESCAPE",
    "\t": "TAB",
}

_KEY_MAP_UNIX_ARROWS = {
    "A": "UP",
    "B": "DOWN",
    "C": "RIGHT",
    "D": "LEFT",
    "H": "HOME",
    "F": "END",
    "Z": "BACKTAB",
}

_KEY_MAP_UNIX_SS3 = {
    "P": "F1",
    "Q": "F2",
    "R": "F3",
    "S": "F4",
    "M": "ENTER",
}

_KEY_MAP_UNIX_TILDE = {
    "1": "HOME",
    "2": "INSERT",
    "3": "DELETE",
    "4": "END",
    "5": "PAGE_UP",
    "6": "PAGE_DOWN",
    "7": "HOME",
    "8": "END",
    "15": "F5",
    "17": "F6",
    "18": "F7",
    "19": "F8",
    "20": "F9",
    "21": "F10",
    "23": "F11",
    "24": "F12",
}


def _modifier_prefix(params: str) -> str:
    """Translate an xterm ``;N`` modifier parameter into a key-name prefix.

    ``ESC [ 1 ; 2 A`` is Shift+Up, ``;5`` is Ctrl+Up, ``;6`` is
    Ctrl+Shift+Up. Bits are ``1 = shift``, ``2 = alt``, ``4 = ctrl``.
    """
    parts = params.split(";")
    if len(parts) < 2:
        return ""
    try:
        bits = int(parts[1]) - 1
    except ValueError:
        return ""
    tokens = []
    if bits & 1:
        tokens.append("SHIFT")
    if bits & 2:
        tokens.append("ALT")
    if bits & 4:
        tokens.append("CTRL")
    return "".join(f"{token}_" for token in tokens)


_WIN_CTRL_C_IGNORED = False


def set_windows_ctrl_c_ignored(ignored: bool) -> None:
    """Make Ctrl+C arrive as a keypress instead of raising KeyboardInterrupt.

    Only meaningful on Windows; it flips the console control handler so that a
    full-screen TUI can implement copy/paste. No-op on other platforms.
    """
    global _WIN_CTRL_C_IGNORED
    if platform.system() != "Windows":
        return
    if _WIN_CTRL_C_IGNORED == ignored:
        return
    try:
        import ctypes

        ctypes.windll.kernel32.SetConsoleCtrlHandler(None, bool(ignored))
    except Exception:
        return
    _WIN_CTRL_C_IGNORED = ignored


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from a string."""
    if not isinstance(text, str):
        return str(text)
    return ANSI_ESCAPE_REGEX.sub("", text)


def _read_unix_byte(fd: int, timeout: Optional[float] = None) -> str:
    """Read one byte without waiting longer than ``timeout`` when specified."""
    if timeout is not None:
        readable, _, _ = select.select([fd], [], [], timeout)
        if not readable:
            return ""
    data = os.read(fd, 1)
    return data.decode("utf-8", errors="ignore") if data else ""


def _get_key(intercept_control: bool = False) -> str:
    """Read a single keypress from the terminal across platforms.

    A standalone Escape key is distinguished from an ANSI escape sequence by
    briefly polling for a continuation. This avoids blocking on Unix after
    the user presses Escape.

    ``intercept_control`` delivers Ctrl+C / Ctrl+Z as ordinary key names
    (``"CTRL_C"`` / ``"\\x1a"``) instead of raising ``KeyboardInterrupt`` or
    suspending the process. Full-screen applications enable it so the focused
    widget can implement copy/paste.
    """
    if platform.system() == "Windows":
        char = msvcrt.getwch()
        if char in ("\xe0", "\x00"):
            extension = msvcrt.getwch()
            return _KEY_MAP_WINDOWS.get(extension, "")
        mapped = _KEY_MAP_WINDOWS_REGULAR.get(char)
        return mapped if mapped is not None else char

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        # Single-key mode without line buffering or echo. Crucially we also
        # clear IXON/IXOFF: otherwise the tty driver consumes Ctrl+S (XOFF)
        # and Ctrl+Q (XON) itself, so those keys never reach us and the next
        # read blocks forever. That is why Ctrl+Q "does nothing" and the app
        # then hangs on Linux/macOS terminals.
        # tcgetattr()/tcsetattr() use the documented attribute-list layout:
        # [iflag, oflag, cflag, lflag, ispeed, ospeed, cc]. Index it
        # positionally because termios.IFLAG / termios.LFLAG are not exported
        # by every Python build, but the list order is guaranteed by the API.
        _IFLAG, _LFLAG, _CC = 0, 3, 6
        mode = termios.tcgetattr(fd)
        mode[_LFLAG] &= ~(termios.ECHO | termios.ICANON)
        mode[_IFLAG] &= ~(termios.IXON | termios.IXOFF)
        if intercept_control:
            # Ctrl+C / Ctrl+Z must reach us as bytes, not as signals.
            mode[_LFLAG] &= ~termios.ISIG
        mode[_CC][termios.VMIN] = 1
        mode[_CC][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSADRAIN, mode)
        char = _read_unix_byte(fd)
        if not char:
            return ""

        if char == "\x1b":
            # Distinguish a lone Escape keypress from a CSI/SS3 control
            # sequence (arrow keys, Home/End, Delete, function keys, ...).
            # The ESC byte is only the *first* byte of a sequence: we must wait
            # briefly for the continuation instead of consuming it immediately.
            second = _read_unix_byte(fd, 0.05)
            if not second:
                return "ESCAPE"
            if second == "O":
                third = _read_unix_byte(fd, 0.05)
                if not third:
                    return "ESCAPE"
                return _KEY_MAP_UNIX_SS3.get(third) or _KEY_MAP_UNIX_ARROWS.get(
                    third, ""
                )
            if second != "[":
                # ESC followed by an ordinary character: treat as Escape.
                return "ESCAPE"

            # Accumulate a CSI sequence: parameters (0x20-0x3F) followed by a
            # single final byte (0x40-0x7E), e.g. ESC [ 1 ; 2 A or ESC [ 3 ~.
            body = _read_unix_byte(fd, 0.05)
            if not body:
                return "ESCAPE"
            while body and not ("@" <= body[-1] <= "~"):
                next_char = _read_unix_byte(fd, 0.02)
                if not next_char:
                    break
                body += next_char
            if not body:
                return ""
            final, params = body[-1], body[:-1]
            if final == "~":
                name = _KEY_MAP_UNIX_TILDE.get(params.split(";", 1)[0], "")
            else:
                name = _KEY_MAP_UNIX_ARROWS.get(final, "")
            if not name:
                return ""
            return f"{_modifier_prefix(params)}{name}"

        if char in ("\r", "\n"):
            return "ENTER"
        if char == "\x03":
            return "CTRL_C"
        if char == "\x11":
            return "CTRL_Q"
        if char == "\x7f":
            return "BACKSPACE"
        if char == "\x08":
            return "DELETE"
        if char == "\t":
            return "TAB"
        return char
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def get_trace_exception(
    ex: BaseException, enhanced: bool = True, max_width: Optional[int] = None
) -> str:
    """Format an exception and its traceback into a string."""
    if not enhanced:
        traceback_lines: List[str] = traceback.format_exception(
            type(ex), ex, ex.__traceback__
        )
        return "".join(traceback_lines)

    if max_width is None:
        try:
            max_width = shutil.get_terminal_size((100, 30)).columns
        except Exception:
            max_width = 100
    max_width = max(80, min(max_width, 200))

    C_ERROR, C_PATH, C_LINE, C_CODE, C_DIM, C_RESET, C_BOLD, C_YELLOW, C_MAGENTA = (
        ANSI.color_bright_red,
        ANSI.color_cyan,
        ANSI.color_bright_green,
        ANSI.color_white,
        ANSI.style_dim + ANSI.color_bright_black,
        ANSI.color_reset,
        ANSI.style_bold,
        ANSI.color_yellow,
        ANSI.color_magenta,
    )

    BOX_TOP, BOX_HORZ, BOX_VERT, BOX_BOTTOM, BOX_RIGHT, BOX_LEFT, BOX_T_LEFT, BOX_T_RIGHT = (
        "╭",
        "─",
        "│",
        "╰",
        "╮",
        "╯",
        "├",
        "┤",
    )

    lines: List[str] = []
    error_name, error_msg = type(ex).__name__, str(ex)
    header = f"{C_ERROR}{C_BOLD}💥 {error_name}{C_RESET}"
    if error_msg:
        header += f"{C_ERROR}: {error_msg}{C_RESET}"
    lines.extend([header, ""])

    tb, frames = ex.__traceback__, []
    while tb is not None:
        frame = tb.tb_frame
        filename, lineno, name = (
            frame.f_code.co_filename,
            tb.tb_lineno,
            frame.f_code.co_name,
        )
        try:
            source_lines, start_line = inspect.getsourcelines(frame)
            line_index = lineno - start_line
            source_line = (
                source_lines[line_index].strip()
                if 0 <= line_index < len(source_lines)
                else ""
            )
        except Exception:
            source_lines, start_line, source_line = [], lineno, ""

        locals_dict = {
            key: (repr(value)[:117] + "..." if len(repr(value)) > 120 else repr(value))
            for key, value in frame.f_locals.items()
            if not (key.startswith("__") and key.endswith("__"))
        }

        frames.append(
            {
                "filename": filename,
                "lineno": lineno,
                "name": name,
                "source_line": source_line,
                "source_lines": source_lines,
                "start_line": start_line,
                "line_index": line_index,
                "locals": locals_dict,
                "is_last": tb.tb_next is None,
            }
        )
        tb = tb.tb_next

    trace_title = "Traceback (most recent call last)"
    padding = max_width - len(trace_title) - 6
    lines.append(
        f"{C_DIM}{BOX_TOP}{BOX_HORZ * 2} {trace_title} "
        f"{BOX_HORZ * padding}{BOX_RIGHT}{C_RESET}"
    )

    for frame_info in frames:
        try:
            display_path = str(Path(frame_info["filename"]).relative_to(Path.cwd()))
        except Exception:
            display_path = frame_info["filename"]

        lines.append(
            f"{C_DIM}{BOX_VERT}  {C_RESET}{C_PATH}{display_path}{C_RESET}"
            f"{C_DIM}:{C_LINE}{frame_info['lineno']}{C_DIM} in "
            f"{C_YELLOW}{frame_info['name']}{C_RESET}"
        )

        if frame_info["source_line"]:
            prefix_len = 5
            if frame_info["line_index"] > 0:
                lines.append(
                    f"{C_DIM}{BOX_VERT}    "
                    f"{frame_info['start_line'] + frame_info['line_index'] - 1:4d} "
                    f"{C_RESET}{C_DIM}"
                    f"{frame_info['source_lines'][frame_info['line_index'] - 1].rstrip()[:max_width-prefix_len-6]}"
                    f"{C_RESET}"
                )
            lines.append(
                f"{C_DIM}{BOX_VERT}    {frame_info['lineno']:4d} {C_ERROR}❱{C_RESET} "
                f"{C_CODE}{frame_info['source_line'][:max_width-prefix_len-8]}{C_RESET}"
            )
            if frame_info["line_index"] < len(frame_info["source_lines"]) - 1:
                lines.append(
                    f"{C_DIM}{BOX_VERT}    "
                    f"{frame_info['start_line'] + frame_info['line_index'] + 1:4d} "
                    f"{C_RESET}{C_DIM}"
                    f"{frame_info['source_lines'][frame_info['line_index'] + 1].rstrip()[:max_width-prefix_len-6]}"
                    f"{C_RESET}"
                )

        if frame_info["locals"]:
            lines.append(
                f"{C_DIM}{BOX_T_LEFT}{BOX_HORZ} locals "
                f"{BOX_HORZ * (max_width - 12)}{BOX_T_RIGHT}{C_RESET}"
            )
            local_items = list(frame_info["locals"].items())
            for index in range(0, len(local_items), 2):
                chunk = local_items[index : index + 2]
                joined = " │ ".join(
                    [
                        f"{C_MAGENTA}{key}{C_RESET} = {C_YELLOW}{value}{C_RESET}"
                        for key, value in chunk
                    ]
                )
                if len(strip_ansi(joined)) > max_width - 4:
                    joined = joined[: max_width - 7] + "..."
                lines.append(f"{C_DIM}{BOX_VERT}  {C_RESET}{joined}")
            if not frame_info["is_last"]:
                lines.append(f"{C_DIM}{BOX_VERT}{C_RESET}")
        if not frame_info["is_last"]:
            lines.append(f"{C_DIM}{BOX_VERT}{C_RESET}")

    lines.append(
        f"{C_DIM}{BOX_BOTTOM}{BOX_HORZ * (max_width - 2)}{BOX_LEFT}{C_RESET}"
    )
    lines.append(
        f"\n{C_ERROR}{C_BOLD}{error_name}{C_RESET}{C_ERROR}: {error_msg}{C_RESET}"
    )
    return "\n".join(lines)