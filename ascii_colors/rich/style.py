# -*- coding: utf-8 -*-
"""
Style and color system for rich compatibility.
"""

from enum import Enum
from typing import Dict, Optional, Tuple, Union
from ascii_colors.constants import ANSI

# Map rich color names to ANSI constants
RICH_COLOR_MAP: Dict[str, str] = {
    # Standard colors
    "black": ANSI.color_black,
    "red": ANSI.color_red,
    "green": ANSI.color_green,
    "yellow": ANSI.color_yellow,
    "blue": ANSI.color_blue,
    "magenta": ANSI.color_magenta,
    "cyan": ANSI.color_cyan,
    "white": ANSI.color_white,
    "orange": ANSI.color_orange,
    
    # Bright colors
    "bright_black": ANSI.color_bright_black,
    "bright_red": ANSI.color_bright_red,
    "bright_green": ANSI.color_bright_green,
    "bright_yellow": ANSI.color_bright_yellow,
    "bright_blue": ANSI.color_bright_blue,
    "bright_magenta": ANSI.color_bright_magenta,
    "bright_cyan": ANSI.color_bright_cyan,
    "bright_white": ANSI.color_bright_white,
    
    # Background colors
    "bg_black": ANSI.color_bg_black,
    "bg_red": ANSI.color_bg_red,
    "bg_green": ANSI.color_bg_green,
    "bg_yellow": ANSI.color_bg_yellow,
    "bg_blue": ANSI.color_bg_blue,
    "bg_magenta": ANSI.color_bg_magenta,
    "bg_cyan": ANSI.color_bg_cyan,
    "bg_white": ANSI.color_bg_white,
    "bg_orange": ANSI.color_bg_orange,
    
    # Bright background colors
    "bg_bright_black": ANSI.color_bg_bright_black,
    "bg_bright_red": ANSI.color_bg_bright_red,
    "bg_bright_green": ANSI.color_bg_bright_green,
    "bg_bright_yellow": ANSI.color_bg_bright_yellow,
    "bg_bright_blue": ANSI.color_bg_bright_blue,
    "bg_bright_magenta": ANSI.color_bg_bright_magenta,
    "bg_bright_cyan": ANSI.color_bg_bright_cyan,
    "bg_bright_white": ANSI.color_bg_bright_white,
}

# Map rich style names to ANSI constants
RICH_STYLE_MAP: Dict[str, str] = {
    "bold": ANSI.style_bold,
    "dim": ANSI.style_dim,
    "italic": ANSI.style_italic,
    "underline": ANSI.style_underline,
    "blink": ANSI.style_blink,
    "reverse": ANSI.style_reverse,
    "hidden": ANSI.style_hidden,
    "strikethrough": ANSI.style_strikethrough,
}

# Semantic tags for common use cases
SEMANTIC_TAG_MAP: Dict[str, str] = {
    "success": ANSI.color_green,
    "error": ANSI.color_red,
    "warning": ANSI.color_yellow,
    "info": ANSI.color_blue,
    "danger": ANSI.color_bright_red,
    "highlight": ANSI.color_bright_yellow,
    "muted": ANSI.style_dim + ANSI.color_bright_black,
    "primary": ANSI.color_cyan,
    "secondary": ANSI.color_magenta,
}


class Color:
    """Represents a color for terminal output."""
    
    def __init__(
        self,
        name: Optional[str] = None,
        rgb: Optional[Tuple[int, int, int]] = None,
    ):
        self.name = name
        self.rgb = rgb
    
    @classmethod
    def parse(cls, color_str: Optional[str]) -> Optional["Color"]:
        """Parse a color string into a Color object."""
        if color_str is None:
            return None
            
        # Handle hex colors
        if color_str.startswith("#"):
            hex_val = color_str[1:]
            if len(hex_val) == 3:
                rgb = tuple(int(c * 2, 16) for c in hex_val)
            elif len(hex_val) == 6:
                rgb = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
            else:
                rgb = (255, 255, 255)
            return cls(rgb=rgb)
        
        # Handle named colors
        color_map = {
            "black": (0, 0, 0),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "yellow": (255, 255, 0),
            "blue": (0, 0, 255),
            "magenta": (255, 0, 255),
            "cyan": (0, 255, 255),
            "white": (255, 255, 255),
            "bright_black": (85, 85, 85),
            "bright_red": (255, 85, 85),
            "bright_green": (85, 255, 85),
            "bright_yellow": (255, 255, 85),
            "bright_blue": (85, 85, 255),
            "bright_magenta": (255, 85, 255),
            "bright_cyan": (85, 255, 255),
            "bright_white": (255, 255, 255),
        }
        
        rgb = color_map.get(color_str.lower(), (255, 255, 255))
        return cls(name=color_str, rgb=rgb)
    
    def __str__(self) -> str:
        if self.name:
            return self.name
        if self.rgb:
            r, g, b = self.rgb
            return f"#{r:02x}{g:02x}{b:02x}"
        return "default"


class Style:
    """Represents text styling (color, bold, italic, etc.)."""
    
    def __init__(
        self,
        color: Optional[Union[str, Color]] = None,
        background: Optional[Union[str, Color]] = None,
        bold: Optional[bool] = None,
        dim: Optional[bool] = None,
        italic: Optional[bool] = None,
        underline: Optional[bool] = None,
        blink: Optional[bool] = None,
        reverse: Optional[bool] = None,
        strike: Optional[bool] = None,
    ):
        self.color = Color.parse(color) if isinstance(color, str) else color
        self.background = Color.parse(background) if isinstance(background, str) else background
        self.bold = bold
        self.dim = dim
        self.italic = italic
        self.underline = underline
        self.blink = blink
        self.reverse = reverse
        self.strike = strike
    
    @classmethod
    def parse(cls, style_str: Optional[str]) -> Optional["Style"]:
        """Parse a style string like 'bold red on blue'."""
        if style_str is None:
            return None
            
        style = cls()
        
        parts = style_str.lower().split()
        i = 0
        while i < len(parts):
            part = parts[i]
            
            if part == "bold":
                style.bold = True
            elif part == "dim":
                style.dim = True
            elif part == "italic":
                style.italic = True
            elif part == "underline":
                style.underline = True
            elif part == "blink":
                style.blink = True
            elif part == "reverse":
                style.reverse = True
            elif part == "strike" or part == "strikethrough":
                style.strike = True
            elif part == "on" and i + 1 < len(parts):
                i += 1
                style.background = Color.parse(parts[i])
            else:
                # Assume it's a color
                style.color = Color.parse(part)
            
            i += 1
        
        return style
    
    def __str__(self) -> str:
        """Convert style to ANSI escape codes."""
        codes = []
        
        if self.bold:
            codes.append(ANSI.style_bold)
        if self.dim:
            codes.append(ANSI.style_dim)
        if self.italic:
            codes.append(ANSI.style_italic)
        if self.underline:
            codes.append(ANSI.style_underline)
        if self.blink:
            codes.append(ANSI.style_blink)
        if self.reverse:
            codes.append(ANSI.style_reverse)
        if self.strike:
            codes.append(ANSI.style_strikethrough)
        
        # Foreground color
        if self.color:
            if self.color.rgb:
                r, g, b = self.color.rgb
                codes.append(f"\033[38;2;{r};{g};{b}m")
            elif self.color.name:
                name = self.color.name.lower()
                color_map = {
                    "black": ANSI.color_black, "red": ANSI.color_red,
                    "green": ANSI.color_green, "yellow": ANSI.color_yellow,
                    "blue": ANSI.color_blue, "magenta": ANSI.color_magenta,
                    "cyan": ANSI.color_cyan, "white": ANSI.color_white,
                    "bright_black": ANSI.color_bright_black,
                    "bright_red": ANSI.color_bright_red,
                    "bright_green": ANSI.color_bright_green,
                    "bright_yellow": ANSI.color_bright_yellow,
                    "bright_blue": ANSI.color_bright_blue,
                    "bright_magenta": ANSI.color_bright_magenta,
                    "bright_cyan": ANSI.color_bright_cyan,
                    "bright_white": ANSI.color_bright_white,
                }
                if name in color_map:
                    codes.append(color_map[name])
        
        # Background color
        if self.background:
            if self.background.rgb:
                r, g, b = self.background.rgb
                codes.append(f"\033[48;2;{r};{g};{b}m")
            elif self.background.name:
                name = self.background.name.lower()
                bg_map = {
                    "black": ANSI.color_bg_black, "red": ANSI.color_bg_red,
                    "green": ANSI.color_bg_green, "yellow": ANSI.color_bg_yellow,
                    "blue": ANSI.color_bg_blue, "magenta": ANSI.color_bg_magenta,
                    "cyan": ANSI.color_bg_cyan, "white": ANSI.color_bg_white,
                    "bright_black": ANSI.color_bg_bright_black,
                    "bright_red": ANSI.color_bg_bright_red,
                    "bright_green": ANSI.color_bg_bright_green,
                    "bright_yellow": ANSI.color_bg_bright_yellow,
                    "bright_blue": ANSI.color_bg_bright_blue,
                    "bright_magenta": ANSI.color_bg_bright_magenta,
                    "bright_cyan": ANSI.color_bg_bright_cyan,
                    "bright_white": ANSI.color_bg_bright_white,
                }
                if name in bg_map:
                    codes.append(bg_map[name])
        
        return "".join(codes)
    
    def __add__(self, other: "Style") -> "Style":
        """Combine two styles."""
        return Style(
            color=other.color or self.color,
            background=other.background or self.background,
            bold=other.bold if other.bold is not None else self.bold,
            dim=other.dim if other.dim is not None else self.dim,
            italic=other.italic if other.italic is not None else self.italic,
            underline=other.underline if other.underline is not None else self.underline,
            blink=other.blink if other.blink is not None else self.blink,
            reverse=other.reverse if other.reverse is not None else self.reverse,
            strike=other.strike if other.strike is not None else self.strike,
        )


class BoxStyle(Enum):
    """Box drawing styles."""
    
    SQUARE = "square"
    ROUND = "round"
    MINIMAL = "minimal"
    MINIMAL_HEAVY_HEAD = "minimal_heavy_head"
    SIMPLE = "simple"
    SIMPLE_HEAD = "simple_head"
    DOUBLE = "double"
    
    def get_chars(self) -> Dict[str, str]:
        """Get characters for this box style."""
        chars = {
            "top_left": "┌", "top_right": "┐",
            "bottom_left": "└", "bottom_right": "┘",
            "horizontal": "─", "vertical": "│",
            "left_t": "├", "right_t": "┤",
            "top_t": "┬", "bottom_t": "┴",
            "cross": "┼",
        }
        
        if self == BoxStyle.ROUND:
            chars["top_left"] = "╭"
            chars["top_right"] = "╮"
            chars["bottom_left"] = "╰"
            chars["bottom_right"] = "╯"
        elif self == BoxStyle.DOUBLE:
            chars["top_left"] = "╔"
            chars["top_right"] = "╗"
            chars["bottom_left"] = "╚"
            chars["bottom_right"] = "╝"
            chars["horizontal"] = "═"
            chars["vertical"] = "║"
            chars["left_t"] = "╠"
            chars["right_t"] = "╣"
            chars["top_t"] = "╦"
            chars["bottom_t"] = "╩"
            chars["cross"] = "╬"
        elif self == BoxStyle.MINIMAL:
            chars = {
                "top_left": " ", "top_right": " ",
                "bottom_left": " ", "bottom_right": " ",
                "horizontal": "─", "vertical": " ",
                "left_t": " ", "right_t": " ",
                "top_t": "─", "bottom_t": "─",
                "cross": "─",
            }
        
        return chars
