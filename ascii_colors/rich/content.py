# -*- coding: utf-8 -*-
"""
Content components: Syntax and Markdown for rich compatibility.
"""

import re
from typing import Dict, Iterator, List, Optional, Tuple, TYPE_CHECKING, Union, Any

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
    
    def _parse_markdown(self) -> List[Tuple[str, Any, int]]:
        lines = self.markup.split("\n")
        result = []
        
        in_code = False
        code_lang = ""
        code_content = []
        in_table = False
        table_headers = []
        table_rows = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Code blocks
            if line.strip().startswith("```"):
                if in_code:
                    result.append(("code", "\n".join(code_content), code_lang))
                    code_content = []
                    in_code = False
                else:
                    code_lang = line.strip()[3:].strip()
                    in_code = True
                i += 1
                continue
            
            if in_code:
                code_content.append(line)
                i += 1
                continue
            
            # Tables: check for |...| pattern
            if "|" in line and not in_table:
                # Check if this looks like a table header
                potential_headers = [c.strip() for c in line.split("|") if c.strip()]
                if potential_headers:
                    # Look ahead for separator line
                    if i + 1 < len(lines) and re.match(r"^\s*\|?[\s\-:|]+\|?\s*$", lines[i + 1]):
                        in_table = True
                        table_headers = potential_headers
                        table_rows = []
                        i += 2  # Skip header and separator
                        continue
            
            if in_table:
                # Check if line is part of table
                if "|" in line and line.strip():
                    cells = [c.strip() for c in line.split("|") if c.strip()]
                    if cells:
                        table_rows.append(cells)
                    i += 1
                    continue
                else:
                    # End of table
                    result.append(("table", {"headers": table_headers, "rows": table_rows}, 0))
                    in_table = False
                    table_headers = []
                    table_rows = []
                    continue
            
            # Headers
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if header_match:
                level = len(header_match.group(1))
                result.append(("header", header_match.group(2), level))
                i += 1
                continue
            
            # Blockquotes
            if line.startswith(">"):
                result.append(("quote", line[1:].strip(), 0))
                i += 1
                continue
            
            # Lists
            list_match = re.match(r"^([\*\-\+]|\d+\.)\s+(.+)$", line)
            if list_match:
                result.append(("list", list_match.group(2), 0))
                i += 1
                continue
            
            # Empty lines
            if not line.strip():
                i += 1
                continue
            
            # Paragraphs
            result.append(("para", line, 0))
            i += 1
        
        # Handle unclosed table at end
        if in_table:
            result.append(("table", {"headers": table_headers, "rows": table_rows}, 0))
        
        return result
    
    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[Union[str, Renderable]]:
        elements = self._parse_markdown()
        
        prev_was_para = False
        
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
                prev_was_para = False
            
            elif elem_type == "para":
                # Process inline formatting
                para = self._process_inline(content)
                yield para
                prev_was_para = True
            
            elif elem_type == "list":
                yield f"  • {self._process_inline(content)}"
                prev_was_para = False
            
            elif elem_type == "quote":
                yield f"{ANSI.style_dim}│ {content}{ANSI.color_reset}"
                prev_was_para = False
            
            elif elem_type == "code":
                from ascii_colors.rich.content import Syntax
                syntax = Syntax(content, lexer=content if content else "text", line_numbers=False)
                for line in console.render(syntax, options):
                    yield line
                prev_was_para = False
            
            elif elem_type == "table":
                from ascii_colors.rich.table import Table
                table_data = content
                table = Table(
                    *table_data["headers"],
                    box="square",
                    show_lines=False,
                    padding=(0, 1),
                )
                for row in table_data["rows"]:
                    # Ensure row has same number of cells as headers
                    while len(row) < len(table_data["headers"]):
                        row.append("")
                    table.add_row(*row)
                yield table
                prev_was_para = False
    
    def _process_inline(self, text: str) -> str:
        """Process inline markdown formatting."""
        # Bold: **text** or __text__
        text = re.sub(r"\*\*(.+?)\*\*", r"[bold]\1[/bold]", text)
        text = re.sub(r"__(.+?)__", r"[bold]\1[/bold]", text)
        # Italic: *text* or _text_
        text = re.sub(r"\*(.+?)\*", r"[italic]\1[/italic]", text)
        text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"[italic]\1[/italic]", text)
        # Code: `text`
        text = re.sub(r"`(.+?)`", r"[dim]\1[/dim]", text)
        return text

    def __rich_measure__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> "Measurement":
        from ascii_colors.rich.console import Measurement
        return Measurement(20, options.max_width)
