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
        from ascii_colors.utils import strip_ansi
        q_color = self._get_style('question', ANSI.color_bright_yellow)
        sug_color = self._get_style('suggestion', ANSI.style_dim)
        
        processed_message = ASCIIColors._apply_rich_markup(self.message)
        
        buffer = list(self.default) if self.default else[]
        cursor_pos = len(buffer)
        
        # Keep track of what the user actually *types* as the filter.
        # Start empty so all options show initially.
        typed_text = ""
        match_idx = -1
        
        # If there's a default, highlight it in the list initially
        if self.default:
            for i, choice in enumerate(self.choices):
                if choice == self.default:
                    match_idx = i
                    break
        
        while True:
            # Always get matches based on what was actually TYPED
            matches = self._get_matches(typed_text)
            current = ''.join(buffer)
            
            # Clear line and redraw prompt + current buffer
            print(f"\r\033[2K", end="") # Clear entire line
            ASCIIColors.print(f"{processed_message}: ", color=q_color, end="", flush=False, markup=False)
            print(current, end="")
            
            if matches:
                # Calculate sliding window for suggestions if many matches exist
                start_window = 0
                if match_idx >= self.max_suggestions:
                    start_window = match_idx - self.max_suggestions + 1
                
                end_window = start_window + self.max_suggestions
                visible_matches = matches[start_window:end_window]
                
                display_parts =[]
                for i, m in enumerate(visible_matches):
                    actual_idx = start_window + i
                    if actual_idx == match_idx:
                        display_parts.append(f"{ANSI.color_bg_cyan}{ANSI.color_black}{m}{ANSI.color_reset}")
                    else:
                        display_parts.append(m)
                
                # Show navigation hint and windowed suggestions
                prefix = "..." if start_window > 0 else ""
                suffix = "..." if len(matches) > end_window else ""
                suggestion_text = f" {sug_color}({len(matches)} matches: {prefix}{', '.join(display_parts)}{suffix}){ANSI.color_reset}"
                print(suggestion_text, end="")
            
            # Return cursor to the correct position within the buffer text
            prompt_len = len(strip_ansi(processed_message)) + 2
            print(f"\r\033[{prompt_len + cursor_pos}C", end="", flush=True)
            
            key = self._get_key()
            
            if key == 'ENTER':
                final = ''.join(buffer)
                if self._validate_input(final):
                    print() # Move to next line
                    return final
                ASCIIColors.print("\n  ✗ Invalid input", color=ANSI.color_red)
                # Small pause to show error before redrawing
                import time; time.sleep(0.5) 
            elif key == 'BACKSPACE':
                if cursor_pos > 0:
                    buffer.pop(cursor_pos - 1)
                    cursor_pos -= 1
                    typed_text = "".join(buffer)
                    match_idx = -1
            elif key == 'LEFT':
                cursor_pos = max(0, cursor_pos - 1)
            elif key == 'RIGHT':
                cursor_pos = min(len(buffer), cursor_pos + 1)
            elif key == 'QUIT':
                raise KeyboardInterrupt
            elif key == 'UP' or key == 'DOWN':
                if matches:
                    if match_idx == -1:
                        match_idx = 0 if key == 'DOWN' else len(matches) - 1
                    else:
                        if key == 'DOWN':
                            match_idx = (match_idx + 1) % len(matches)
                        else: # UP
                            match_idx = (match_idx - 1) % len(matches)
                    
                    # Update buffer with the selected suggestion
                    selected = matches[match_idx]
                    buffer = list(selected)
                    cursor_pos = len(buffer)
            elif len(key) == 1:
                # Insert character at cursor position
                buffer.insert(cursor_pos, key)
                cursor_pos += 1
                typed_text = "".join(buffer)
                match_idx = -1

    def _get_matches(self, text: str) -> List[str]:
        """Get matching suggestions."""
        if not text:
            return self.choices

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
