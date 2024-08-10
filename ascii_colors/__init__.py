import traceback
import os
import threading
import time
from typing import List, Union, Callable, Any, Optional

def get_trace_exception(ex):
    """
    Traces an exception (useful for debug) and returns the full trace of the exception
    """
    # Catch the exception and get the traceback as a list of strings
    traceback_lines = traceback.format_exception(type(ex), ex, ex.__traceback__)

    # Join the traceback lines into a single string
    traceback_text = ''.join(traceback_lines)        
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
    color_reset = '\u001b[0m'

    # Regular colors
    color_black = '\u001b[30m'
    color_red = '\u001b[31m'
    color_green = '\u001b[32m'
    color_yellow = '\u001b[33m'
    color_blue = '\u001b[34m'
    color_magenta = '\u001b[35m'
    color_cyan = '\u001b[36m'
    color_white = '\u001b[37m'
    color_orange = '\u001b[38;5;202m'

    # Bright colors
    color_bright_black = '\u001b[30;1m'
    color_bright_red = '\u001b[31;1m'
    color_bright_green = '\u001b[32;1m'
    color_bright_yellow = '\u001b[33;1m'
    color_bright_blue = '\u001b[34;1m'
    color_bright_magenta = '\u001b[35;1m'
    color_bright_cyan = '\u001b[36;1m'
    color_bright_white = '\u001b[37;1m'
    color_bright_orange = '\u001b[38;5;208m'

    # Additional style codes
    style_bold = '\u001b[1m'
    style_underline = '\u001b[4m'

    # logging
    log_path = ""


    @staticmethod
    def print(text, color=color_bright_red, style="", end="\n", flush=False):
        """
        Prints text with a specified color and style.

        Args:
            text (str): The text to be printed.
            color (str, optional): The color code. Defaults to bright red.
            style (str, optional): The style code. Defaults to an empty string.
            end (str, optional): The string to print at the end. Defaults to a newline.
            flush (bool, optional): Whether to flush the output. Defaults to False.
        """
        print(f"{style}{color}{text}{ASCIIColors.color_reset}", end=end, flush=flush)
        if ASCIIColors.log_path!="":
            try:
                if os.path.exists(ASCIIColors.log_path):
                    with open(ASCIIColors.log_path,"a", encoding="utf8") as f:
                        f.write(text+end)
                else:
                    with open(ASCIIColors.log_path,"w", encoding="utf8") as f:
                        f.write(text+end)
            except:
                print(f"{ASCIIColors.color_bright_red}Coudln't create log file, make sure you have the permission to create it or try setting a different path.\nLogging will be disabled.{ASCIIColors.color_reset}")
                ASCIIColors.log_path=""    
    
    @staticmethod
    def warning(text, end="\n", flush=False):
        """
        Prints text in a warning style.

        Args:
            text (str): The text to be printed.
            end (str, optional): The string to print at the end. Defaults to a newline.
            flush (bool, optional): Whether to flush the output. Defaults to False.
        """
        ASCIIColors.print(text, ASCIIColors.color_bright_orange, end=end, flush=flush)

    @staticmethod
    def error(text, end="\n", flush=False):
        """
        Prints text in an error style.

        Args:
            text (str): The text to be printed.
            end (str, optional): The string to print at the end. Defaults to a newline.
            flush (bool, optional): Whether to flush the output. Defaults to False.
        """
        ASCIIColors.print(text, ASCIIColors.color_bright_red, end=end, flush=flush)

    @staticmethod
    def success(text, end="\n", flush=False):
        """
        Prints text in a success style.

        Args:
            text (str): The text to be printed.
            end (str, optional): The string to print at the end. Defaults to a newline.
            flush (bool, optional): Whether to flush the output. Defaults to False.
        """
        ASCIIColors.print(text, ASCIIColors.color_green, end=end, flush=flush)

    @staticmethod
    def info(text, end="\n", flush=False):
        """
        Prints text in an info style.

        Args:
            text (str): The text to be printed.
            end (str, optional): The string to print at the end. Defaults to a newline.
            flush (bool, optional): Whether to flush the output. Defaults to False.
        """
        ASCIIColors.print(text, ASCIIColors.color_bright_blue, end=end, flush=flush)

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
    def multicolor(texts:list, colors:list, end="\n", flush=False):
        for text, color in zip(texts, colors):
            ASCIIColors.print(text, color, end="", flush=True)
        print(ASCIIColors.color_reset, color, end=end, flush=flush)

    @staticmethod
    def bold(text, color=color_bright_red, end="\n", flush=False):
        ASCIIColors.print(text, color, ASCIIColors.style_bold, end=end, flush=flush)

    @staticmethod
    def underline(text, color=color_bright_red, end="\n", flush=False):
        ASCIIColors.print(text, color, ASCIIColors.style_underline, end=end, flush=flush)



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
        ASCIIColors.activate('')  # Reset style

    @staticmethod
    def resetAll():
        ASCIIColors.reset()
        
    @staticmethod
    def highlight(text: str, subtext: Union[str, List[str]], color: str = '\u001b[33m', highlight_color: str = '\u001b[31m', whole_line: bool = False):
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
            lines = text.split('\n')
            for line in lines:
                if any(st in line for st in subtext):
                    print(f"{highlight_color}{line}{ASCIIColors.color_reset}")
                else:
                    print(f"{color}{line}{ASCIIColors.color_reset}")
        else:
            for st in subtext:
                text = text.replace(st, f'{highlight_color}{st}{color}')
            print(f"{color}{text}{ASCIIColors.color_reset}")

        if ASCIIColors.log_path:
            try:
                log_path = Path(ASCIIColors.log_path)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with log_path.open("a", encoding="utf8") as f:
                    f.write(text + "\n")
            except Exception as e:
                print(f"{ASCIIColors.color_bright_red}Couldn't create log file: {e}{ASCIIColors.color_reset}")
                ASCIIColors.log_path = ""

    @staticmethod
    def execute_with_animation(pending_text: str, func: Callable, *args, color: Optional[str] = None, **kwargs) -> Any:
        """
        Executes a function while displaying a pending text with an animation.
        
        Args:
            pending_text (str): The text to display while the function is executing.
            func (Callable): The function to execute.
            *args: Positional arguments to pass to the function.
            color (Optional[str]): Color to use for the pending text and animation. Defaults to yellow if not specified.
            **kwargs: Keyword arguments to pass to the function.
        
        Returns:
            Any: The return value of the executed function.
        """
        animation = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        stop_event = threading.Event()
        result = None
        
        # Default to yellow if no color is specified
        text_color = color if color else ASCIIColors.color_yellow
        
        def animate():
            idx = 0
            while not stop_event.is_set():
                print(f"\r{text_color}{pending_text} {animation[idx % len(animation)]}{ASCIIColors.color_reset}  ", end="", flush=True)
                idx += 1
                time.sleep(0.1)
        
        animation_thread = threading.Thread(target=animate)
        animation_thread.start()
        
        try:
            result = func(*args, **kwargs)
        finally:
            stop_event.set()
            animation_thread.join()
            print(f"\r{' ' * (len(pending_text) + 2)}", end="\r")  # Clear the line
        
        return result

if __name__=="__main__":
    # Test colors
    ASCIIColors.multicolor(["text1 ","text 2"], [ASCIIColors.color_red, ASCIIColors.color_blue])
    ASCIIColors.highlight("ParisNeo: Hello Lollms how you doing man?\nLoLLMs: I'm fine. What do you need?\nParisNeo: Nothin special. Just testing the ASCII_COLORS library.\nLoLLMs: OK, I ope it tests fine :)",["ParisNeo", "LoLLMs"])
    def some_long_running_function(param1, param2):
        # Simulating a long-running operation
        time.sleep(5)
        return f"Result: {param1} + {param2}"

    result = ASCIIColors.execute_with_animation(
        "Processing...",
        some_long_running_function,
        "Hello",
        "World",
        color=ASCIIColors.color_cyan
    )
    print(result)