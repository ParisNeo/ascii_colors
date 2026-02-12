# -*- coding: utf-8 -*-
"""
Yes/No confirmation question type for questionary compatibility.
"""

from typing import Any, Dict, Optional
from ascii_colors.constants import ANSI
from ascii_colors.core import ASCIIColors
from ascii_colors.questionary.base import Question


class Confirm(Question):
    """Yes/No confirmation question."""
    def __init__(self, message: str, default: bool = True,
                 style: Optional[Dict[str, str]] = None, **kwargs):
        super().__init__(message, default, None, style, **kwargs)
        self.auto_enter = kwargs.get('auto_enter', True)
    
    def _ask_internal(self) -> bool:
        color = self.style.get('question', ANSI.color_bright_yellow)
        suffix = "[Y/n]" if self.default else "[y/N]"
        
        while True:
            # Process message for rich markup
            processed_message = ASCIIColors._apply_rich_markup(self.message)
            ASCIIColors.print(f"{processed_message} {suffix}? ", color=color, end="", flush=True, markup=False)
            response = self._get_input().strip().lower()
            
            if not response:
                result = self.default
                break
            elif response in ('y', 'yes'):
                result = True
                break
            elif response in ('n', 'no'):
                result = False
                break
            else:
                ASCIIColors.print("  Please enter 'y' or 'n'.", color=ANSI.color_red)
        
        answer_color = ANSI.color_green if result else ANSI.color_red
        ASCIIColors.print(f"  → {'Yes' if result else 'No'}", color=answer_color)
        return result


def confirm(message: str, default: bool = True,
            style: Optional[Dict[str, str]] = None, **kwargs) -> Confirm:
    """Create a yes/no confirmation question."""
    return Confirm(message, default, style, **kwargs)
