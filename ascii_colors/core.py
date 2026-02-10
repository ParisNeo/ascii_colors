import sys
import os
import threading
import time
import getpass
from datetime import datetime
from threading import Lock
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast, ContextManager, IO
from ascii_colors.constants import LogLevel, ANSI, INFO
from ascii_colors.utils import strip_ansi, get_trace_exception, _get_key
from ascii_colors.handlers import Handler, ConsoleHandler, FileHandler
from ascii_colors.formatters import Formatter

_T = TypeVar('_T')

class ASCIIColors(ANSI):
    """Direct printing and logging state manager."""
    _handlers: List[Handler] = []
    _global_level: LogLevel = LogLevel.INFO
    _handler_lock: Lock = Lock()
    _basicConfig_called: bool = False
    _context: threading.local = threading.local()

    _level_colors: Dict[LogLevel, str] = {
        LogLevel.DEBUG: ANSI.style_dim + ANSI.color_white,
        LogLevel.INFO: ANSI.color_bright_blue,
        LogLevel.WARNING: ANSI.color_bright_yellow,
        LogLevel.ERROR: ANSI.color_bright_red,
        LogLevel.CRITICAL: ANSI.style_bold + ANSI.color_bright_red,
    }

    @classmethod
    def set_log_level(cls, level: Union[LogLevel, int]) -> None:
        cls._global_level = LogLevel(level)

    @classmethod
    def add_handler(cls, handler: Handler) -> None:
        with cls._handler_lock:
            if handler not in cls._handlers: cls._handlers.append(handler)

    @classmethod
    def remove_handler(cls, handler: Handler) -> None:
        with cls._handler_lock:
            if handler in cls._handlers: cls._handlers.remove(handler)

    @classmethod
    def clear_handlers(cls) -> None:
        with cls._handler_lock: cls._handlers.clear()

    @classmethod
    def set_context(cls, **kwargs: Any) -> None:
        for key, value in kwargs.items(): setattr(cls._context, key, value)

    @classmethod
    def clear_context(cls, *args: str) -> None:
        v = vars(cls._context)
        for k in (args if args else [k for k in v if not k.startswith("_")]):
            if hasattr(cls._context, k): delattr(cls._context, k)

    @classmethod
    @contextmanager
    def context(cls, **kwargs: Any) -> ContextManager[None]:
        prev, added = {}, set()
        for k, v in kwargs.items():
            if hasattr(cls._context, k): prev[k] = getattr(cls._context, k)
            else: added.add(k)
            setattr(cls._context, k, v)
        try: yield
        finally:
            for k in kwargs:
                if k in added:
                    if hasattr(cls._context, k): delattr(cls._context, k)
                elif k in prev: setattr(cls._context, k, prev[k])

    @classmethod
    def get_thread_context(cls) -> Dict[str, Any]:
        return {k: v for k, v in vars(cls._context).items() if not k.startswith("_")}

    @classmethod
    def _log(cls, level: LogLevel, message: str, args: tuple = (), exc_info: Any = None, logger_name: str = 'ASCIIColors', **kwargs: Any) -> None:
        with cls._handler_lock:
            if not cls._handlers and not cls._basicConfig_called:
                h = ConsoleHandler(level=cls._global_level)
                h.setFormatter(Formatter())
                cls._handlers.append(h)
        
        if level < cls._global_level: return
        ts = datetime.now()
        final_msg = (message % args) if args else message
        
        final_exc = None
        if exc_info:
            if isinstance(exc_info, BaseException): final_exc = (type(exc_info), exc_info, exc_info.__traceback__)
            elif isinstance(exc_info, tuple) and len(exc_info) == 3: final_exc = exc_info
            elif exc_info is True: final_exc = sys.exc_info()

        with cls._handler_lock: hdlrs = cls._handlers[:]
        for h in hdlrs:
            try: h.handle(level, final_msg, ts, final_exc, logger_name=logger_name, **kwargs)
            except Exception as e:
                print(f"PANIC: Handler error: {e}\n{get_trace_exception(e)}", file=sys.stderr)

    @classmethod
    def debug(cls, m: str, *a, **k): cls._log(LogLevel.DEBUG, m, a, **k)
    @classmethod
    def info(cls, m: str, *a, **k): cls._log(LogLevel.INFO, m, a, **k)
    @classmethod
    def warning(cls, m: str, *a, **k): cls._log(LogLevel.WARNING, m, a, **k)
    @classmethod
    def error(cls, m: str, *a, **k): cls._log(LogLevel.ERROR, m, a, **k)
    @classmethod
    def critical(cls, m: str, *a, **k): cls._log(LogLevel.CRITICAL, m, a, **k)

    @staticmethod
    def print(text: str, color: str = ANSI.color_white, style: str = "", background: str = "", end: str = "\n", flush: bool = False, file: Any = sys.stdout, emit: bool = True) -> str:
        out = f"{style}{background}{color}{text}{ANSI.color_reset}{end}"
        if emit: print(out, end="", flush=flush, file=file)
        return out

    @staticmethod
    def success(t: str, **k): return ASCIIColors.print(t, ANSI.color_green, **k)
    @staticmethod
    def fail(t: str, **k): return ASCIIColors.print(t, ANSI.color_red, **k)
    @staticmethod
    def red(t: str, **k): return ASCIIColors.print(t, ANSI.color_red, **k)
    @staticmethod
    def green(t: str, **k): return ASCIIColors.print(t, ANSI.color_green, **k)
    @staticmethod
    def yellow(t: str, **k): return ASCIIColors.print(t, ANSI.color_yellow, **k)
    @staticmethod
    def blue(t: str, **k): return ASCIIColors.print(t, ANSI.color_blue, **k)
    @staticmethod
    def magenta(t: str, **k): return ASCIIColors.print(t, ANSI.color_magenta, **k)
    @staticmethod
    def cyan(t: str, **k): return ASCIIColors.print(t, ANSI.color_cyan, **k)
    @staticmethod
    def white(t: str, **k): return ASCIIColors.print(t, ANSI.color_white, **k)
    @staticmethod
    def orange(t: str, **k): return ASCIIColors.print(t, ANSI.color_orange, **k)
    @staticmethod
    def bold(t: str, **k): return ASCIIColors.print(t, style=ANSI.style_bold, **k)
    @staticmethod
    def italic(t: str, **k): return ASCIIColors.print(t, style=ANSI.style_italic, **k)

    @staticmethod
    def multicolor(texts: List[str], colors: List[str], end: str = "\n", flush: bool = False, file: Any = sys.stdout, emit: bool = True) -> None:
        if len(texts) != len(colors): raise ValueError("Mismatch")
        out = "".join([f"{c}{t}" for t, c in zip(texts, colors)]) + ANSI.color_reset + end
        print(out, end="", flush=flush, file=file)

    @staticmethod
    def highlight(text: str, subtext: Union[str, List[str]], color: str = ANSI.color_white, highlight_color: str = ANSI.color_yellow, whole_line: bool = False, end: str = "\n", flush: bool = False, file: Any = sys.stdout) -> None:
        subtexts = [subtext] if isinstance(subtext, str) else subtext
        if whole_line:
            out = ""
            for line in text.splitlines(True):
                s_l = line.rstrip('\r\n')
                c = highlight_color if any(st in s_l for st in subtexts) else color
                out += f"{c}{s_l}{ANSI.color_reset}{line[len(s_l):]}"
        else:
            processed = text
            for st in subtexts: processed = processed.replace(st, f"{highlight_color}{st}{ANSI.color_reset}{color}")
            out = f"{color}{processed}{ANSI.color_reset}"
        print(out + end, end="", flush=flush, file=file)

    @staticmethod
    def execute_with_animation(pending_text: str, func: Callable[..., _T], *args: Any, color: Optional[str] = None, **kwargs: Any) -> _T:
        anim, stop, res, exc, lock = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏", threading.Event(), [None], [None], Lock()
        c = color or ANSI.color_yellow
        def animate():
            idx = 0
            while not stop.is_set():
                ASCIIColors.print(f"\r{c}{pending_text} {anim[idx % len(anim)]}", color="", end="", flush=True)
                idx += 1; time.sleep(0.1)
            ASCIIColors.print(f"\r{c}{pending_text}{ANSI.color_reset}{' ' * 10}", color="", end="\r", flush=True)
        def target():
            try:
                r = func(*args, **kwargs)
                with lock:
                    res[0] = r
            except Exception as e:
                with lock:
                    exc[0] = e
            finally:
                stop.set()
        w, a = threading.Thread(target=target), threading.Thread(target=animate)
        w.start(); a.start(); w.join(); stop.set(); a.join()
        with lock:
            f_exc, f_res = exc[0], res[0]
        sym, f_c = ("✗", ANSI.color_red) if f_exc else ("✓", ANSI.color_green)
        ASCIIColors.print(f"\r{c}{pending_text} {f_c}{sym}{ANSI.color_reset}{' ' * 10}\n", color="", flush=True)
        if f_exc:
            raise f_exc
        return cast(_T, f_res)

    @staticmethod
    def confirm(question: str, default_yes: Optional[bool] = None, prompt_color: str = ANSI.color_yellow, file: Any = sys.stdout) -> bool:
        suff = "[Y/n]" if default_yes is True else ("[y/N]" if default_yes is False else "[y/n]")
        p = f"{question} {suff}? "
        while True:
            try:
                ASCIIColors.print(p, color=prompt_color, end="", flush=True, file=file)
                c = input().lower().strip()
                if c in ('y', 'yes'): return True
                if c in ('n', 'no'): return False
                if c == '' and default_yes is not None: return default_yes
                ASCIIColors.print("Invalid input.", color=ANSI.color_red, file=file)
            except KeyboardInterrupt: return False

    @staticmethod
    def prompt(text: str, color: str = ANSI.color_green, style: str = "", hide_input: bool = False, file: Any = sys.stdout) -> str:
        full = f"{style}{color}{text}{ANSI.color_reset}"
        try:
            print(full, end="", flush=True, file=file)
            return getpass.getpass(prompt="") if hide_input else input()
        except KeyboardInterrupt: print(file=file); return ""

    # ============== New Rich-style methods ==============

    @staticmethod
    def panel(
        content: str,
        title: Optional[str] = None,
        border_style: str = "",
        box: str = "square",
        padding: Union[int, Tuple[int, ...]] = (0, 1),
        width: Optional[int] = None,
        color: str = "",
        background: str = "",
    ) -> str:
        """
        Create a bordered panel around content. Returns string for printing.
        
        New rich-style convenience method.
        """
        from ascii_colors.rich_compat import Panel, BoxStyle, Style, Text, Console
        
        # Convert string box name to enum
        box_style = BoxStyle.SQUARE
        try:
            box_style = BoxStyle(box)
        except ValueError:
            pass
        
        # Parse style
        style_obj = Style()
        if border_style:
            style_obj = Style.parse(border_style)
        if color:
            style_obj = Style(color=color)
        if background:
            style_obj = Style(background=background)
        
        # Create panel with explicit width
        text_obj = Text(content)
        
        # Calculate appropriate width
        term_width = ASCIIColors._get_terminal_width()
        if width is None:
            panel_width = min(term_width - 4, max(40, len(content) + 10))
        else:
            panel_width = min(width, term_width - 2)
        
        panel = Panel(
            text_obj,
            title=title,
            border_style=style_obj,
            box=box_style,
            padding=padding,
            width=panel_width,
        )
        
        # Render to string using capture
        console = Console(width=panel_width + 2, force_terminal=False)
        with console.capture() as capture:
            console.print(panel)
        
        result = capture.get()
        # Remove trailing newlines to prevent double spacing
        return result.rstrip('\n')

    @staticmethod
    def table(
        *headers: str,
        rows: Optional[List[List[str]]] = None,
        title: Optional[str] = None,
        box: str = "square",
        show_lines: bool = False,
        header_style: str = "bold",
    ) -> str:
        """
        Create a formatted table. Returns string for printing.
        
        New rich-style convenience method.
        """
        from ascii_colors.rich_compat import Table, BoxStyle, Console
        
        box_style = BoxStyle.SQUARE
        try:
            box_style = BoxStyle(box)
        except ValueError:
            pass
        
        table = Table(
            *headers,
            title=title,
            box=box_style,
            show_lines=show_lines,
            header_style=header_style,
        )
        
        if rows:
            for row in rows:
                table.add_row(*row)
        
        # Calculate width based on content
        term_width = ASCIIColors._get_terminal_width()
        table_width = min(term_width - 4, 120)
        
        console = Console(width=table_width, force_terminal=False)
        with console.capture() as capture:
            console.print(table)
        
        return capture.get().rstrip('\n')

    @staticmethod
    def tree(
        label: str,
        style: str = "",
        guide_style: str = "dim",
    ) -> 'Tree':
        """
        Create a tree structure for display.
        
        New rich-style convenience method.
        Returns a Tree object that can have children added.
        """
        from ascii_colors.rich_compat import Tree, Style
        
        style_obj = Style.parse(style) if style else Style()
        guide_obj = Style.parse(guide_style) if guide_style else Style(dim=True)
        
        return Tree(label, style=style_obj, guide_style=guide_obj)

    @staticmethod
    def syntax(
        code: str,
        language: str = "python",
        line_numbers: bool = False,
        theme: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Syntax highlight code. Returns string for printing.
        
        New rich-style convenience method.
        """
        from ascii_colors.rich_compat import Syntax, Console
        
        syntax = Syntax(
            code,
            lexer=language,
            line_numbers=line_numbers,
            theme=theme,
        )
        
        term_width = ASCIIColors._get_terminal_width()
        console = Console(width=min(term_width - 4, 120), force_terminal=False)
        with console.capture() as capture:
            console.print(syntax)
        
        return capture.get().rstrip('\n')

    @staticmethod
    def markdown(markup: str) -> str:
        """
        Render markdown to terminal. Returns string for printing.
        
        New rich-style convenience method.
        """
        from ascii_colors.rich_compat import Markdown, Console
        
        md = Markdown(markup)
        
        term_width = ASCIIColors._get_terminal_width()
        console = Console(width=min(term_width - 4, 100), force_terminal=False)
        with console.capture() as capture:
            console.print(md)
        
        return capture.get().rstrip('\n')

    @staticmethod
    def columns(
        *items: str,
        equal: bool = False,
        width: Optional[int] = None,
    ) -> str:
        """
        Arrange items in columns. Returns string for printing.
        
        New rich-style convenience method.
        """
        from ascii_colors.rich_compat import Columns, Text, Console
        
        renderables = [Text(item) for item in items]
        cols = Columns(renderables, equal=equal, width=width)
        
        term_width = ASCIIColors._get_terminal_width()
        col_width = width or min(term_width - 4, 100)
        console = Console(width=col_width, force_terminal=False)
        with console.capture() as capture:
            console.print(cols)
        
        return capture.get().rstrip('\n')

    @staticmethod
    def rule(
        title: str = "",
        characters: str = "─",
        style: str = "",
        align: str = "center",
    ) -> None:
        """
        Print a horizontal rule with optional title.
        
        New rich-style convenience method.
        """
        from ascii_colors.rich_compat import Console, Style
        
        console = Console(width=ASCIIColors._get_terminal_width())
        style_obj = Style.parse(style) if style else None
        
        console.rule(title, characters=characters, style=style_obj, align=align)

    @staticmethod
    def status(
        message: str,
        spinner: str = "dots",
        spinner_style: str = "green",
    ) -> 'Status':
        """
        Show a spinner status indicator.
        
        New rich-style convenience method. Use as context manager.
        
        Example:
            with ASCIIColors.status("Processing..."):
                do_work()
        """
        from ascii_colors.rich_compat import Status, Console, Style
        
        console = Console(width=ASCIIColors._get_terminal_width())
        style_obj = Style.parse(spinner_style) if spinner_style else Style(color=ANSI.color_green)
        
        return Status(
            message,
            console=console,
            spinner=spinner,
            spinner_style=style_obj,
        )

    @staticmethod
    def live(renderable: Any, refresh_per_second: float = 4) -> 'Live':
        """
        Create a live updating display.
        
        New rich-style convenience method. Use as context manager.
        
        Example:
            with ASCIIColors.live(some_renderable) as live:
                while updating:
                    live.update(new_renderable)
        """
        from ascii_colors.rich_compat import Live, Console
        
        console = Console(width=ASCIIColors._get_terminal_width())
        
        from ascii_colors.rich_compat import Text
        if isinstance(renderable, str):
            renderable = Text(renderable)
        
        return Live(renderable, console=console, refresh_per_second=refresh_per_second)

    @staticmethod
    def _get_mini_console(width: int) -> 'Console':
        """Get a minimal console for string capture."""
        from ascii_colors.rich_compat import Console
        return Console(width=width, force_terminal=False)

    @staticmethod
    def _get_terminal_width() -> int:
        """Get terminal width."""
        import shutil
        try:
            return shutil.get_terminal_size().columns
        except Exception:
            return 80
