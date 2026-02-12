# -*- coding: utf-8 -*-
"""
Autocomplete text input question type for questionary compatibility.
"""

from typing import Any, Callable, Dict, List, Optional, Union
from ascii_colors.constants import ANSI
from ascii_colors.core import ASCIIColors
from ascii_colors.questionary.base import Question, Validator
from ascii_colors.questionary.text import PromptText


class Autocomplete(PromptText):
    """Text input with autocomplete suggestions."""
    def __init__(self, message: str, choices: List[str], default: str = "",
                 validate: Optional[Union[Callable[[str], bool], Validator]] = None,
                 style: Optional[Dict[str, str]] = None, **kwargs):
        # Initialize parent Text class properly
        super().__init__(message, default, validate, style, **kwargs)
        self.choices = choices
        self.ignore_case = kwargs.get('ignore_case', True)
        self.match_middle = kwargs.get('match_middle', False)
        self.max_suggestions = kwargs.get('max_suggestions', 5)
    
    def _ask_internal(self) -> str:
        from ascii_colors.questionary.text import PromptText
        q_color = self.style.get('question', ANSI.color_bright_yellow)
        sug_color = self.style.get('suggestion', ANSI.style_dim)
        
        # Process message for rich markup
        processed_message = ASCIIColors._apply_rich_markup(self.message)
        ASCIIColors.print(f"{processed_message}: ", color=q_color, end="", flush=True, markup=False)
        
        buffer = list(self.default) if self.default else []
        cursor_pos = len(buffer)
        
        while True:
            current = ''.join(buffer)
            matches = self._get_matches(current)
            
            # Clear and redraw
            # Move cursor to beginning of line and clear
            print(f"\r\033[K", end="")
            ASCIIColors.print(f"{processed_message}: ", color=q_color, end="", flush=True, markup=False)
            print(current, end="")
            
            if matches and current:
                suggestion_text = f" (suggestions: {', '.join(matches[:self.max_suggestions])})"
                ASCIIColors.print(suggestion_text, color=sug_color, end="", markup=False)
            
            # Position cursor correctly
            total_len = len(processed_message) + 2 + len(current)
            print(f"\r\033[{total_len + cursor_pos}C", end="", flush=True)
            
            key = self._get_key()
            
            if key == 'ENTER':
                final = ''.join(buffer)
                if self._validate_input(final):
                    print()
                    return final
                ASCIIColors.print("\n  ✗ Invalid input", color=ANSI.color_red)
            elif key == 'BACKSPACE':
                if cursor_pos > 0:
                    buffer.pop(cursor_pos - 1)
                    cursor_pos -= 1
            elif key == 'LEFT':
                cursor_pos = max(0, cursor_pos - 1)
            elif key == 'RIGHT':
                cursor_pos = min(len(buffer), cursor_pos + 1)
            elif key == 'QUIT':
                raise KeyboardInterrupt
            elif key == 'UP' or key == 'DOWN':
                if matches and key == 'DOWN':
                    buffer = list(matches[0])
                    cursor_pos = len(buffer)
            elif len(key) == 1:
                buffer.insert(cursor_pos, key)
                cursor_pos += 1
    
    def _get_matches(self, text: str) -> List[str]:
        """Get matching suggestions."""
        if not text:
            return []
        
        search = text.lower() if self.ignore_case else text
        matches = []
        
        for choice in self.choices:
            cmp = choice.lower() if self.ignore_case else choice
            if self.match_middle:
                if search in cmp:
                    matches.append(choice)
            else:
                if cmp.startswith(search):
                    matches.append(choice)
        
        return matches


def autocomplete(message: str, choices: List[str], default: str = "",
                 validate: Optional[Union[Callable[[str], bool], Validator]] = None,
                 style: Optional[Dict[str, str]] = None, **kwargs) -> Autocomplete:
    """Create an autocomplete text input question."""
    return Autocomplete(message, choices, default, validate, style, **kwargs)
