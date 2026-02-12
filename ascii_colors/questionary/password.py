# -*- coding: utf-8 -*-
"""
Password input question type for questionary compatibility.
"""

from typing import Any, Callable, Dict, Optional, Union
from ascii_colors.constants import ANSI
from ascii_colors.core import ASCIIColors
from ascii_colors.questionary.base import Question, Validator, ValidationError
from ascii_colors.questionary.text import PromptText


class Password(PromptText):
    """Password input (hidden)."""
    def __init__(self, message: str, default: str = "",
                 validate: Optional[Union[Callable[[str], bool], Validator]] = None,
                 style: Optional[Dict[str, str]] = None, **kwargs):
        super().__init__(message, default, validate, style, **kwargs)
        self.confirm = kwargs.get('confirm', False)
        self.confirm_message = kwargs.get('confirm_message', "Confirm password")
    
    def _get_password(self, prompt: str = "") -> str:
        """Get password, either from injected source or from getpass."""
        if self._input_source is not None:
            try:
                return next(self._input_source)
            except StopIteration:
                return self.default or ""
        import getpass
        try:
            return getpass.getpass(prompt)
        except (EOFError, OSError):
            return self.default or ""
    
    def _ask_internal(self) -> str:
        import getpass
        color = self.style.get('question', ANSI.color_bright_yellow)
        
        while True:
            # Process message for rich markup
            processed_message = ASCIIColors._apply_rich_markup(self.message)
            ASCIIColors.print(f"{processed_message}: ", color=color, end="", flush=True, markup=False)
            value = self._get_password()
            
            if not value and self.default:
                value = self.default
            
            if not self._validate_input(value):
                ASCIIColors.print("  ✗ Invalid input, please try again.", color=ANSI.color_red)
                continue
            
            if self.confirm:
                processed_confirm = ASCIIColors._apply_rich_markup(self.confirm_message)
                ASCIIColors.print(f"{processed_confirm}: ", color=color, end="", flush=True, markup=False)
                confirm_value = self._get_password()
                if value != confirm_value:
                    ASCIIColors.print("  ✗ Passwords do not match.", color=ANSI.color_red)
                    continue
            
            ASCIIColors.print("  → " + "*" * min(len(value), 8), color=ANSI.style_dim)
            return value


def password(message: str, default: str = "",
             validate: Optional[Union[Callable[[str], bool], Validator]] = None,
             style: Optional[Dict[str, str]] = None, **kwargs) -> Password:
    """Create a password input question."""
    return Password(message, default, validate, style, **kwargs)
