import os
import sys
import re
import platform
import inspect
import shutil
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from ascii_colors.constants import ANSI

if platform.system() == "Windows":
    import msvcrt
else:
    import termios
    import tty

ANSI_ESCAPE_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

_KEY_MAP_WINDOWS = {
    b'H': 'UP', b'P': 'DOWN', b'K': 'LEFT', b'M': 'RIGHT',
    b'\r': 'ENTER', b'\x03': 'QUIT', b'\x08': 'BACKSPACE',
}

_KEY_MAP_UNIX_ESCAPE = {'A': 'UP', 'B': 'DOWN', 'D': 'LEFT', 'C': 'RIGHT'}

def strip_ansi(text: str) -> str:
    """Removes ANSI escape sequences from a string."""
    if not isinstance(text, str):
        return str(text)
    return ANSI_ESCAPE_REGEX.sub("", text)

def _get_key() -> str:
    """Reads a single keypress from the terminal across platforms."""
    if platform.system() == "Windows":
        ch = msvcrt.getch()
        if ch in (b'\xe0', b'\x00'):
            ch2 = msvcrt.getch()
            return _KEY_MAP_WINDOWS.get(ch2, '')
        mapped = _KEY_MAP_WINDOWS.get(ch)
        if mapped: return mapped
        try: return ch.decode('utf-8')
        except UnicodeDecodeError: return '?'
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                next_chars = sys.stdin.read(2)
                if next_chars.startswith('['):
                    return _KEY_MAP_UNIX_ESCAPE.get(next_chars[1], '')
                return 'ESCAPE'
            elif ch in ('\r', '\n'): return 'ENTER'
            elif ch == '\x03': return 'QUIT'
            elif ch == '\x7f': return 'BACKSPACE'
            else: return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def get_trace_exception(ex: BaseException, enhanced: bool = True, max_width: Optional[int] = None) -> str:
    """Formats an exception and its traceback into a string."""
    if not enhanced:
        traceback_lines: List[str] = traceback.format_exception(type(ex), ex, ex.__traceback__)
        return "".join(traceback_lines)
    
    if max_width is None:
        try: max_width = shutil.get_terminal_size((100, 30)).columns
        except Exception: max_width = 100
    max_width = max(80, min(max_width, 200))

    C_ERROR, C_PATH, C_LINE, C_CODE, C_DIM, C_RESET, C_BOLD, C_YELLOW, C_MAGENTA = (
        ANSI.color_bright_red, ANSI.color_cyan, ANSI.color_bright_green, ANSI.color_white,
        ANSI.style_dim + ANSI.color_bright_black, ANSI.color_reset, ANSI.style_bold,
        ANSI.color_yellow, ANSI.color_magenta
    )
    
    BOX_TOP, BOX_HORZ, BOX_VERT, BOX_BOTTOM, BOX_RIGHT, BOX_LEFT, BOX_T_LEFT, BOX_T_RIGHT = (
        "╭", "─", "│", "╰", "╮", "╯", "├", "┤"
    )

    lines: List[str] = []
    error_name, error_msg = type(ex).__name__, str(ex)
    header = f"{C_ERROR}{C_BOLD}💥 {error_name}{C_RESET}"
    if error_msg: header += f"{C_ERROR}: {error_msg}{C_RESET}"
    lines.extend([header, ""])

    tb, frames = ex.__traceback__, []
    while tb is not None:
        frame = tb.tb_frame
        filename, lineno, name = frame.f_code.co_filename, tb.tb_lineno, frame.f_code.co_name
        try:
            source_lines, start_line = inspect.getsourcelines(frame)
            line_index = lineno - start_line
            source_line = source_lines[line_index].strip() if 0 <= line_index < len(source_lines) else ""
        except Exception:
            source_lines, start_line, source_line = [], lineno, ""
        
        locals_dict = {k: (repr(v)[:117] + "..." if len(repr(v)) > 120 else repr(v))
                       for k, v in frame.f_locals.items() if not (k.startswith('__') and k.endswith('__'))}
        
        frames.append({'filename': filename, 'lineno': lineno, 'name': name, 'source_line': source_line,
                       'source_lines': source_lines, 'start_line': start_line, 'line_index': line_index,
                       'locals': locals_dict, 'is_last': tb.tb_next is None})
        tb = tb.tb_next

    trace_title = "Traceback (most recent call last)"
    padding = max_width - len(trace_title) - 6
    lines.append(f"{C_DIM}{BOX_TOP}{BOX_HORZ * 2} {trace_title} {BOX_HORZ * padding}{BOX_RIGHT}{C_RESET}")

    for i, f in enumerate(frames):
        try: display_path = str(Path(f['filename']).relative_to(Path.cwd()))
        except Exception: display_path = f['filename']
        
        lines.append(f"{C_DIM}{BOX_VERT}  {C_RESET}{C_PATH}{display_path}{C_RESET}{C_DIM}:{C_LINE}{f['lineno']}{C_DIM} in {C_YELLOW}{f['name']}{C_RESET}")
        
        if f['source_line']:
            prefix_len = 5
            if f['line_index'] > 0:
                lines.append(f"{C_DIM}{BOX_VERT}    {f['start_line'] + f['line_index'] - 1:4d} {C_RESET}{C_DIM}{f['source_lines'][f['line_index'] - 1].rstrip()[:max_width-prefix_len-6]}{C_RESET}")
            lines.append(f"{C_DIM}{BOX_VERT}    {f['lineno']:4d} {C_ERROR}❱{C_RESET} {C_CODE}{f['source_line'][:max_width-prefix_len-8]}{C_RESET}")
            if f['line_index'] < len(f['source_lines']) - 1:
                lines.append(f"{C_DIM}{BOX_VERT}    {f['start_line'] + f['line_index'] + 1:4d} {C_RESET}{C_DIM}{f['source_lines'][f['line_index'] + 1].rstrip()[:max_width-prefix_len-6]}{C_RESET}")
        
        if f['locals']:
            lines.append(f"{C_DIM}{BOX_T_LEFT}{BOX_HORZ} locals {BOX_HORZ * (max_width - 12)}{BOX_T_RIGHT}{C_RESET}")
            local_items = list(f['locals'].items())
            for j in range(0, len(local_items), 2):
                chunk = local_items[j:j+2]
                joined = " │ ".join([f"{C_MAGENTA}{k}{C_RESET} = {C_YELLOW}{v}{C_RESET}" for k, v in chunk])
                if len(strip_ansi(joined)) > max_width - 4: joined = joined[:max_width-7] + "..."
                lines.append(f"{C_DIM}{BOX_VERT}  {C_RESET}{joined}")
            if not f['is_last']: lines.append(f"{C_DIM}{BOX_VERT}{C_RESET}")
        if not f['is_last']: lines.append(f"{C_DIM}{BOX_VERT}{C_RESET}")
    
    lines.append(f"{C_DIM}{BOX_BOTTOM}{BOX_HORZ * (max_width - 2)}{BOX_LEFT}{C_RESET}")
    lines.append(f"\n{C_ERROR}{C_BOLD}{error_name}{C_RESET}{C_ERROR}: {error_msg}{C_RESET}")
    return "\n".join(lines)
