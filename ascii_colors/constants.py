from enum import IntEnum

class LogLevel(IntEnum):
    """Enumeration defining standard logging levels."""
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0

# Standard logging level constants
CRITICAL: int = LogLevel.CRITICAL.value
ERROR: int = LogLevel.ERROR.value
WARNING: int = LogLevel.WARNING.value
INFO: int = LogLevel.INFO.value
DEBUG: int = LogLevel.DEBUG.value
NOTSET: int = LogLevel.NOTSET.value

class ANSI:
    """Internal container for ANSI escape codes."""
    color_reset: str = "\u001b[0m"
    
    style_bold: str = "\u001b[1m"
    style_dim: str = "\u001b[2m"
    style_italic: str = "\u001b[3m"
    style_underline: str = "\u001b[4m"
    style_blink: str = "\u001b[5m"
    style_blink_fast: str = "\u001b[6m"
    style_reverse: str = "\u001b[7m"
    style_hidden: str = "\u001b[8m"
    style_strikethrough: str = "\u001b[9m"

    color_black: str = "\u001b[30m"
    color_red: str = "\u001b[31m"
    color_green: str = "\u001b[32m"
    color_yellow: str = "\u001b[33m"
    color_blue: str = "\u001b[34m"
    color_magenta: str = "\u001b[35m"
    color_cyan: str = "\u001b[36m"
    color_white: str = "\u001b[37m"
    color_orange: str = "\u001b[38;5;208m"

    color_bright_black: str = "\u001b[90m"
    color_bright_red: str = "\u001b[91m"
    color_bright_green: str = "\u001b[92m"
    color_bright_yellow: str = "\u001b[93m"
    color_bright_blue: str = "\u001b[94m"
    color_bright_magenta: str = "\u001b[95m"
    color_bright_cyan: str = "\u001b[96m"
    color_bright_white: str = "\u001b[97m"

    color_bg_black: str = "\u001b[40m"
    color_bg_red: str = "\u001b[41m"
    color_bg_green: str = "\u001b[42m"
    color_bg_yellow: str = "\u001b[43m"
    color_bg_blue: str = "\u001b[44m"
    color_bg_magenta: str = "\u001b[45m"
    color_bg_cyan: str = "\u001b[46m"
    color_bg_white: str = "\u001b[47m"
    color_bg_orange: str = "\u001b[48;5;208m"

    color_bg_bright_black: str = "\u001b[100m"
    color_bg_bright_red: str = "\u001b[101m"
    color_bg_bright_green: str = "\u001b[102m"
    color_bg_bright_yellow: str = "\u001b[103m"
    color_bg_bright_blue: str = "\u001b[104m"
    color_bg_bright_magenta: str = "\u001b[105m"
    color_bg_bright_cyan: str = "\u001b[106m"
    color_bg_bright_white: str = "\u001b[107m"
