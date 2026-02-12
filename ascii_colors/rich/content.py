# -*- coding: utf-8 -*-
"""
Content components: Syntax and Markdown for rich compatibility.
"""

import re
from typing import Dict, Iterator, List, Optional, Tuple, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ascii_colors.rich.console import Console, ConsoleOptions

from ascii_colors.constants import ANSI
from ascii_colors.rich.text import Text, Renderable


class Syntax(Renderable):
    """Syntax highlighted code."""
    
    def __init__(
        self,
        code: str,
        lexer: str = "python",
        line_numbers: bool = False,
        line_number_start: int = 1,
        highlight_lines: Optional[List[int]] = None,
        code_width: Optional[int] = None,
        tab_size: int = 4,
        theme: Optional[Dict[str, str]] = None,
        word_wrap: bool = False,
        indent_guides: bool = False,
        padding: int = 0,
    ):
        self.code = code
        self.lexer = lexer
        self.line_numbers = line_numbers
        self.line_number_start = line_number_start
        self.highlight_lines = highlight_lines or []
        self.code_width = code_width
        self.tab_size = tab_size
        self.theme = theme or self._default_theme()
        self.word_wrap = word_wrap
        self.indent_guides = indent_guides
        self.padding = padding
    
    def _default_theme(self) -> Dict[str, str]:
        return {
            "keyword": ANSI.color_magenta,
            "string": ANSI.color_green,
            "number": ANSI.color_cyan,
            "comment": ANSI.color_bright_black,
            "function": ANSI.color_blue,
            "class": ANSI.color_yellow,
            "operator": ANSI.color_red,
            "default": ANSI.color_white,
        }
    
    def _tokenize(self, code: str) -> List[Tuple[str, str]]:
        lines = code.split("\n")
        tokens = []
        
        for line in lines:
            i = 0
            while i < len(line):
                char = line[i]
                
                if char.isspace():
                    j = i
                    while j < len(line) and line[j].isspace():
                        j += 1
                    tokens.append(("whitespace", line[i:j]))
                    i = j
                    continue
                
                if char == "#":
                    tokens.append(("comment", line[i:]))
                    break
                
                if char in "\"'":
                    quote = char
                    j = i + 1
                    while j < len(line):
                        if line[j] == quote and (j == i + 1 or line[j-1] != "\\"):
                            j += 1
                            break
                        j += 1
                    tokens.append(("string", line[i:j]))
                    i = j
                    continue
                
                if char.isdigit():
                    j = i
                    while j < len(line) and (line[j].isdigit() or line[j] == "."):
                        j += 1
                    tokens.append(("number", line[i:j]))
                    i = j
                    continue
                
                if char.isalpha() or char == "_":
                    j = i
                    while j < len(line) and (line[j].isalnum() or line[j] == "_"):
                        j += 1
                    word = line[i:j]
                    keywords = {
                        "def", "class", "if", "elif", "else", "for", "while",
                        "try", "except", "finally", "with", "import", "from",
                        "return", "yield", "async", "await", "lambda", "pass",
                        "break", "continue", "raise", "assert", "del", "global",
                        "nonlocal", "in", "is", "not", "and", "or", "True",
                        "False", "None",
                    }
                    if word in keywords:
                        tokens.append(("keyword", word))
                    elif word[0].isupper():
                        tokens.append(("class", word))
                    else:
                        tokens.append(("default", word))
                    i = j
                    continue
                
                if char in "+-*/=<>!&|^%~:":
                    j = i
                    while j < len(line) and line[j] in "+-*/=<>!&|^%~:":
                        j += 1
                    tokens.append(("operator", line[i:j]))
                    i = j
                    continue
                
                tokens.append(("default", char))
                i += 1
            
            tokens.append(("newline", "\n"))
        
        return tokens
    
    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[str]:
        tokens = self._tokenize(self.code)
        
        lines = []
        current_line = []
        
        for token_type, text in tokens:
            if token_type == "newline":
                lines.append(current_line)
                current_line = []
            else:
                color = self.theme.get(token_type, self.theme["default"])
                current_line.append(f"{color}{text}{ANSI.color_reset}")
        
        if current_line:
            lines.append(current_line)
        
        line_num = self.line_number_start
        max_line_num = self.line_number_start + len(lines) - 1
        line_num_width = len(str(max_line_num))
        
        for line in lines:
            if self.line_numbers:
                is_highlighted = line_num in self.highlight_lines
                line_style = ANSI.style_bold if is_highlighted else ANSI.style_dim
                prefix = f"{line_style}{line_num:>{line_num_width}} │ {ANSI.color_reset}"
                yield prefix + "".join(line)
            else:
                yield "".join(line)
            
            line_num += 1
    
    def __rich_measure__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> "Measurement":
        from ascii_colors.rich.console import Measurement
        lines = self.code.split("\n")
        max_len = max(len(line) for line in lines) if lines else 0
        return Measurement(min(20, max_len), options.max_width)


class Markdown(Renderable):
    """Markdown rendering for terminal."""
    
    def __init__(
        self,
        markup: str,
        code_theme: Optional[str] = None,
        justify: Optional[str] = None,
        style: Optional[Union[str, "Style"]] = None,
        hyperlinks: bool = True,
    ):
        self.markup = markup
        self.code_theme = code_theme
        self.justify = justify
        self.style = style
        self.hyperlinks = hyperlinks
    
    def _parse_markdown(self) -> List[Tuple[str, str, int]]:
        lines = self.markup.split("\n")
        result = []
        
        in_code = False
        code_lang = ""
        code_content = []
        
        for line in lines:
            if line.strip().startswith("```"):
                if in_code:
                    result.append(("code", "\n".join(code_content), code_lang))
                    code_content = []
                    in_code = False
                else:
                    code_lang = line.strip()[3:].strip()
                    in_code = True
                continue
            
            if in_code:
                code_content.append(line)
                continue
            
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if header_match:
                level = len(header_match.group(1))
                result.append(("header", header_match.group(2), level))
                continue
            
            if line.startswith(">"):
                result.append(("quote", line[1:].strip(), 0))
                continue
            
            list_match = re.match(r"^([\*\-\+]|\d+\.)\s+(.+)$", line)
            if list_match:
                result.append(("list", list_match.group(2), 0))
                continue
            
            if not line.strip():
                result.append(("empty", "", 0))
                continue
            
            result.append(("para", line, 0))
        
        return result
    
    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[Union[str, Renderable]]:
        elements = self._parse_markdown()
        
        for elem_type, content, level in elements:
            if elem_type == "header":
                styles = {
                    1: ANSI.style_bold + ANSI.color_bright_white,
                    2: ANSI.style_bold + ANSI.color_white,
                    3: ANSI.color_bright_white,
                    4: ANSI.color_white + ANSI.style_underline,
                    5: ANSI.color_white,
                    6: ANSI.style_dim,
                }
                style = styles.get(level, ANSI.color_white)
                underline = "═" * min(len(content), options.max_width) if level <= 2 else ""
                
                yield f"{style}{content}{ANSI.color_reset}"
                if underline:
                    yield f"{style}{underline}{ANSI.color_reset}"
                yield ""
            
            elif elem_type == "para":
                yield content
                yield ""
            
            elif elem_type == "list":
                yield f"  • {content}"
            
            elif elem_type == "quote":
                yield f"{ANSI.style_dim}│ {content}{ANSI.color_reset}"
            
            elif elem_type == "code":
                from ascii_colors.rich.content import Syntax
                syntax = Syntax(content, lexer=content if content else "text", line_numbers=False)
                for line in console.render(syntax, options):
                    yield line
                yield ""
            
            elif elem_type == "empty":
                yield ""
    
    def __rich_measure__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> "Measurement":
        from ascii_colors.rich.console import Measurement
        return Measurement(20, options.max_width)
