import traceback

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

    @staticmethod
    def warning(text, end="\n", flush=False):
        """
        Prints text in a warning style.

        Args:
            text (str): The text to be printed.
            end (str, optional): The string to print at the end. Defaults to a newline.
            flush (bool, optional): Whether to flush the output. Defaults to False.
        """
        print(f"{ASCIIColors.color_bright_orange}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def error(text, end="\n", flush=False):
        """
        Prints text in an error style.

        Args:
            text (str): The text to be printed.
            end (str, optional): The string to print at the end. Defaults to a newline.
            flush (bool, optional): Whether to flush the output. Defaults to False.
        """
        print(f"{ASCIIColors.color_bright_red}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def success(text, end="\n", flush=False):
        """
        Prints text in a success style.

        Args:
            text (str): The text to be printed.
            end (str, optional): The string to print at the end. Defaults to a newline.
            flush (bool, optional): Whether to flush the output. Defaults to False.
        """
        print(f"{ASCIIColors.color_green}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def info(text, end="\n", flush=False):
        """
        Prints text in an info style.

        Args:
            text (str): The text to be printed.
            end (str, optional): The string to print at the end. Defaults to a newline.
            flush (bool, optional): Whether to flush the output. Defaults to False.
        """
        print(f"{ASCIIColors.color_bright_blue}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def black(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_black}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def white(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_white}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def red(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_red}{text}{ASCIIColors.color_reset}", end=end, flush=flush)
    @staticmethod
    def orange(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_orange}{text}{ASCIIColors.color_reset}", end=end, flush=flush)        
    @staticmethod
    def green(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_green}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def blue(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_blue}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def yellow(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_yellow}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def magenta(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_magenta}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def cyan(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_cyan}{text}{ASCIIColors.color_reset}", end=end, flush=flush)



    @staticmethod
    def bright_black(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_bright_black}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def bright_white(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_bright_white}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def bright_red(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_bright_red}{text}{ASCIIColors.color_reset}", end=end, flush=flush)
    @staticmethod
    def bright_orange(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_bright_orange}{text}{ASCIIColors.color_reset}", end=end, flush=flush)        
    @staticmethod
    def bright_green(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_bright_green}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def bright_blue(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_bright_blue}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def bright_yellow(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_bright_yellow}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def bright_magenta(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_bright_magenta}{text}{ASCIIColors.color_reset}", end=end, flush=flush)

    @staticmethod
    def bright_cyan(text, end="\n", flush=False):
        print(f"{ASCIIColors.color_bright_cyan}{text}{ASCIIColors.color_reset}", end=end, flush=flush)




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
    def hilight(text, subtext, color, hilight_color, whole_line):
        """
        This method takes a text string, another text string to search for inside the first one, the color of the text to print, 
        the color of the subtext to highlight, and whether or not to highlight a whole line or just the text.

        Args:
        text (str): The main text string
        subtext (str): The text to search for inside the main text
        color (str): The color of the main text
        hilight_color (str): The color of the subtext to highlight
        whole_line (bool): Whether to highlight the whole line or just the text

        Returns:
        None
        """
        if whole_line:
            lines = text.split('\n')
            for line in lines:
                if subtext in line:
                    print(f"{color}{line}{ASCIIColors.color_reset}")
                else:
                    print(f"{hilight_color}{line}{ASCIIColors.color_reset}")
        else:
            print(f"{color}{text.replace(subtext, f'{hilight_color}{subtext}{color}')}{ASCIIColors.color_reset}")

    