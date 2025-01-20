import os
import string
import threading
import time
import traceback
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Union


class LogLevel(IntEnum):
    """Log levels for filtering messages"""

    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


def get_trace_exception(ex):
    """
    Traces an exception (useful for debug) and returns the full trace of the exception
    """
    # Catch the exception and get the traceback as a list of strings
    traceback_lines = traceback.format_exception(type(ex), ex, ex.__traceback__)

    # Join the traceback lines into a single string
    traceback_text = "".join(traceback_lines)
    return traceback_text


def trace_exception(ex):
    """
    Traces an exception (useful for debug)
    """
    ASCIIColors.error(get_trace_exception(ex))


class ASCIIColors:
    """
    A class for working with colors and styles in the console.

    This class provides methods for printing text with various colors and styles,
    as well as functions for handling exceptions and displaying them in a formatted way.
    """

    # Reset
    color_reset = "\u001b[0m"

    # Regular colors
    color_black = "\u001b[30m"
    color_red = "\u001b[31m"
    color_green = "\u001b[32m"
    color_yellow = "\u001b[33m"
    color_blue = "\u001b[34m"
    color_magenta = "\u001b[35m"
    color_cyan = "\u001b[36m"
    color_white = "\u001b[37m"
    color_orange = "\u001b[38;5;202m"

    # Bright colors
    color_bright_black = "\u001b[30;1m"
    color_bright_red = "\u001b[31;1m"
    color_bright_green = "\u001b[32;1m"
    color_bright_yellow = "\u001b[33;1m"
    color_bright_blue = "\u001b[34;1m"
    color_bright_magenta = "\u001b[35;1m"
    color_bright_cyan = "\u001b[36;1m"
    color_bright_white = "\u001b[37;1m"
    color_bright_orange = "\u001b[38;5;208m"

    # Additional style codes
    style_bold = "\u001b[1m"
    style_underline = "\u001b[4m"

    # New class variables for logging configuration
    _log_level: LogLevel = LogLevel.INFO
    _log_file: Optional[Path] = None
    _file_lock = Lock()  # For thread-safe file operations

    # Default templates
    _templates: Dict[LogLevel, str] = {
        LogLevel.DEBUG: "[DEBUG][{datetime}] {message}",
        LogLevel.INFO: "[INFO][{datetime}] {message}",
        LogLevel.WARNING: "[WARNING][{datetime}] {message}",
        LogLevel.ERROR: "[ERROR][{datetime}] {message}",
    }

    # Color mapping for different log levels
    _level_colors = {
        LogLevel.DEBUG: color_bright_magenta,
        LogLevel.INFO: color_bright_blue,
        LogLevel.WARNING: color_bright_orange,
        LogLevel.ERROR: color_bright_red,
    }

    @classmethod
    def set_log_level(cls, level: Union[LogLevel, int]) -> None:
        """
        Set the minimum log level to display.

        Args:
            level: The minimum log level to display
        """
        cls._log_level = LogLevel(level)

    @classmethod
    def set_template(cls, level: LogLevel, template: str) -> None:
        """
        Set a custom template for a specific log level.

        Args:
            level: The log level to set the template for
            template: The template string with placeholders {datetime} and {message}
        """
        # Validate template
        try:
            template.format(datetime="test", message="test")
        except KeyError as e:
            raise ValueError(
                f"Invalid template. Must contain {{datetime}} and {{message}} placeholders. Error: {e}"
            )

        cls._templates[level] = template

    @classmethod
    def set_log_file(cls, path: Union[str, Path]) -> None:
        """
        Set the log file path.

        Args:
            path: Path to the log file
        """
        cls._log_file = Path(path)
        cls._log_file.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _log_to_file(cls, message: str) -> None:
        """Internal method to handle file logging with thread safety."""
        if cls._log_file:
            try:
                with cls._file_lock:
                    with cls._log_file.open("a", encoding="utf-8") as f:
                        f.write(message + "\n")
            except Exception as e:
                print(
                    f"{cls.color_bright_red}Failed to write to log file: {e}{cls.color_reset}"
                )

    @classmethod
    def _format_message(cls, level: LogLevel, message: str, **kwargs) -> str:
        """Internal method to format the message using the template."""
        template = cls._templates[level]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return template.format(datetime=now, message=message, **kwargs)

    @classmethod
    def print(
        cls,
        text: str,
        color: str = color_bright_red,
        style: str = "",
        end: str = "\n",
        flush: bool = False,
    ) -> None:
        """Original print method (kept for backward compatibility)"""
        formatted = f"{style}{color}{text}{cls.color_reset}"
        print(formatted, end=end, flush=flush)
        cls._log_to_file(text)

    @classmethod
    def debug(cls, text: str, **kwargs) -> None:
        """
        Print a debug message if the log level allows it.

        Args:
            text: The message to print
            **kwargs: Additional template variables
        """
        if cls._log_level <= LogLevel.DEBUG:
            formatted = cls._format_message(LogLevel.DEBUG, text, **kwargs)
            cls.print(formatted, cls._level_colors[LogLevel.DEBUG])

    @classmethod
    def info(cls, text: str, **kwargs) -> None:
        """
        Print an info message if the log level allows it.

        Args:
            text: The message to print
            **kwargs: Additional template variables. If 'color' is provided,
                    it will be used instead of the default info color
        """
        if cls._log_level <= LogLevel.INFO:
            # Extract color if provided, otherwise use default
            color = kwargs.pop("color", cls._level_colors[LogLevel.INFO])
            formatted = cls._format_message(LogLevel.INFO, text, **kwargs)
            cls.print(formatted, color)

    @classmethod
    def warning(cls, text: str, **kwargs) -> None:
        """
        Print a warning message if the log level allows it.

        Args:
            text: The message to print
            **kwargs: Additional template variables
        """
        if cls._log_level <= LogLevel.WARNING:
            formatted = cls._format_message(LogLevel.WARNING, text, **kwargs)
            cls.print(formatted, cls._level_colors[LogLevel.WARNING])

    @classmethod
    def error(cls, text: str, **kwargs) -> None:
        """
        Print an error message if the log level allows it.

        Args:
            text: The message to print
            **kwargs: Additional template variables
        """
        if cls._log_level <= LogLevel.ERROR:
            formatted = cls._format_message(LogLevel.ERROR, text, **kwargs)
            cls.print(formatted, cls._level_colors[LogLevel.ERROR])

    @staticmethod
    def success(text, end="\n", flush=False):
        """
        Prints text in a success style.

        Args:
            text (str): The text to be printed.
            end (str, optional): The string to print at the end. Defaults to a newline.
            flush (bool, optional): Whether to flush the output. Defaults to False.
        """
        ASCIIColors.info(text, color=ASCIIColors.color_green, end=end, flush=flush)

    @staticmethod
    def fail(text, end="\n", flush=False):
        """
        Prints text in a success style.

        Args:
            text (str): The text to be printed.
            end (str, optional): The string to print at the end. Defaults to a newline.
            flush (bool, optional): Whether to flush the output. Defaults to False.
        """
        ASCIIColors.info(text, color=ASCIIColors.color_red, end=end, flush=flush)

    @staticmethod
    def black(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_black, end=end, flush=flush)

    @staticmethod
    def white(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_white, end=end, flush=flush)

    @staticmethod
    def red(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_red, end=end, flush=flush)

    @staticmethod
    def orange(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_orange, end=end, flush=flush)

    @staticmethod
    def green(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_green, end=end, flush=flush)

    @staticmethod
    def blue(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_blue, end=end, flush=flush)

    @staticmethod
    def yellow(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_yellow, end=end, flush=flush)

    @staticmethod
    def magenta(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_magenta, end=end, flush=flush)

    @staticmethod
    def cyan(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_cyan, end=end, flush=flush)

    @staticmethod
    def bright_black(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_bright_black, end=end, flush=flush)

    @staticmethod
    def bright_white(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_bright_white, end=end, flush=flush)

    @staticmethod
    def bright_red(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_bright_red, end=end, flush=flush)

    @staticmethod
    def bright_orange(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_bright_orange, end=end, flush=flush)

    @staticmethod
    def bright_green(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_bright_green, end=end, flush=flush)

    @staticmethod
    def bright_blue(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_bright_blue, end=end, flush=flush)

    @staticmethod
    def bright_yellow(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_bright_yellow, end=end, flush=flush)

    @staticmethod
    def bright_magenta(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_bright_magenta, end=end, flush=flush)

    @staticmethod
    def bright_cyan(text, end="\n", flush=False):
        ASCIIColors.print(text, ASCIIColors.color_bright_cyan, end=end, flush=flush)

    @staticmethod
    def multicolor(texts: list, colors: list, end="\n", flush=False):
        for text, color in zip(texts, colors):
            ASCIIColors.print(text, color, end="", flush=True)
        print(ASCIIColors.color_reset, color, end=end, flush=flush)

    @staticmethod
    def bold(text, color=color_bright_red, end="\n", flush=False):
        ASCIIColors.print(text, color, ASCIIColors.style_bold, end=end, flush=flush)

    @staticmethod
    def underline(text, color=color_bright_red, end="\n", flush=False):
        ASCIIColors.print(
            text, color, ASCIIColors.style_underline, end=end, flush=flush
        )

    @staticmethod
    def activate(color_or_style):
        print(f"{color_or_style}", end="", flush=True)

    @staticmethod
    def reset():
        print(ASCIIColors.color_reset, end="", flush=True)

    @staticmethod
    def activateRed():
        ASCIIColors.activate(ASCIIColors.color_red)

    @staticmethod
    def activateGreen():
        ASCIIColors.activate(ASCIIColors.color_green)

    @staticmethod
    def activateBlue():
        ASCIIColors.activate(ASCIIColors.color_blue)

    @staticmethod
    def activateYellow():
        ASCIIColors.activate(ASCIIColors.color_yellow)

    # Static methods for activating styles
    @staticmethod
    def activateBold():
        ASCIIColors.activate(ASCIIColors.style_bold)

    @staticmethod
    def activateUnderline():
        ASCIIColors.activate(ASCIIColors.style_underline)

    # ... Other style functions ...

    @staticmethod
    def resetColor():
        ASCIIColors.activate(ASCIIColors.color_reset)

    @staticmethod
    def resetStyle():
        ASCIIColors.activate("")  # Reset style

    @staticmethod
    def resetAll():
        ASCIIColors.reset()

    @staticmethod
    def highlight(
        text: str,
        subtext: Union[str, List[str]],
        color: str = "\u001b[33m",
        highlight_color: str = "\u001b[31m",
        whole_line: bool = False,
    ):
        """
        This method takes a text string, another text string or a list of text strings to search for inside the first one,
        the color of the text to print, the color of the subtext to highlight, and whether or not to highlight a whole line or just the text.

        Args:
        text (str): The main text string
        subtext (Union[str, List[str]]): The text or list of texts to search for inside the main text
        color (str): The color of the main text
        highlight_color (str): The color of the subtext to highlight
        whole_line (bool): Whether to highlight the whole line or just the text

        Returns:
        None
        """
        if isinstance(subtext, str):
            subtext = [subtext]

        if whole_line:
            lines = text.split("\n")
            for line in lines:
                if any(st in line for st in subtext):
                    ASCIIColors.print(
                        f"{highlight_color}{line}{ASCIIColors.color_reset}"
                    )
                else:
                    ASCIIColors.print(f"{color}{line}{ASCIIColors.color_reset}")
        else:
            for st in subtext:
                text = text.replace(st, f"{highlight_color}{st}{color}")
            ASCIIColors.print(f"{color}{text}{ASCIIColors.color_reset}")

    @staticmethod
    def execute_with_animation(
        pending_text: str, func: Callable, *args, color: Optional[str] = None, **kwargs
    ) -> Any:
        """
        Executes a function while displaying a pending text with an animation,
        followed by a checkbox upon completion.

        Args:
            pending_text (str): The text to display while the function is executing.
            func (Callable): The function to execute.
            *args: Positional arguments to pass to the function.
            color (Optional[str]): Color to use for the pending text and animation.
                                Defaults to yellow if not specified.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            Any: The return value of the executed function.
        """
        animation = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        stop_event = threading.Event()
        result = None

        # Default to yellow if no color is specified
        text_color = color if color else ASCIIColors.color_yellow
        checkbox = "✓"

        def animate():
            idx = 0
            while not stop_event.is_set():
                print(
                    f"\r{text_color}{pending_text} {animation[idx % len(animation)]}{ASCIIColors.color_reset}  ",
                    end="",
                    flush=True,
                )
                idx += 1
                time.sleep(0.1)

        animation_thread = threading.Thread(target=animate)
        animation_thread.start()

        try:
            result = func(*args, **kwargs)
        finally:
            stop_event.set()
            animation_thread.join()
            # Clear the line and show completion with checkbox
            print(
                f"\r{text_color}{pending_text} {ASCIIColors.color_green}{checkbox}{ASCIIColors.color_reset}",
                flush=True,
            )

        return result


if __name__ == "__main__":
    # Test colors
    ASCIIColors.multicolor(
        ["text1 ", "text 2"], [ASCIIColors.color_red, ASCIIColors.color_blue]
    )
    ASCIIColors.highlight(
        "ParisNeo: Hello Lollms how you doing man?\nLoLLMs: I'm fine. What do you need?\nParisNeo: Nothin special. Just testing the ASCII_COLORS library.\nLoLLMs: OK, I ope it tests fine :)",
        ["ParisNeo", "LoLLMs"],
    )

    def some_long_running_function(param1, param2):
        # Simulating a long-running operation
        time.sleep(5)
        return f"Result: {param1} + {param2}"

    result = ASCIIColors.execute_with_animation(
        "Processing...",
        some_long_running_function,
        "Hello",
        "World",
        color=ASCIIColors.color_cyan,
    )
    print(result)

    ASCIIColors.success("Succeeded!")
    ASCIIColors.fail("Failed!")
