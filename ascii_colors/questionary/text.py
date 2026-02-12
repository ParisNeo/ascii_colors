# -*- coding: utf-8 -*-
"""
Text input question type for questionary compatibility.
"""

from typing import Any, Callable, Dict, Optional, Union
from ascii_colors.constants import ANSI
from ascii_colors.core import ASCIIColors
from ascii_colors.questionary.base import Question, Validator


class PromptText(Question):
    """Text input question."""
    def __init__(self, message: str, default: str = "",
                 validate: Optional[Union[Callable[[str], bool], Validator]] = None,
                 style: Optional[Dict[str, str]] = None, **kwargs):
        super().__init__(message, default, validate, style, **kwargs)
        self.multiline = kwargs.get('multiline', False)
    
    def _ask_internal(self) -> str:
        color = self.style.get('question', ANSI.color_bright_yellow)
        
        while True:
            # Process message for rich markup - get ANSI codes applied
            try:
                from ascii_colors.rich.console import Console
                console = Console(force_terminal=True, no_color=False)
                processed_message = console._apply_markup(self.message)
            except Exception:
                # Fallback: use message as-is
                processed_message = self.message
            
            # Print with markup=False since we already processed it
            # Use the color parameter for the prompt color, but the message already has ANSI codes
            # We need to print without any additional color processing
            if processed_message != self.message:
                # Message was processed, print directly without color override
                print(f"{processed_message}: ", end="", flush=True)
            else:
                # No markup processing happened, use standard colored print
                ASCIIColors.print(f"{processed_message}: ", color=color, end="", flush=True, markup=False)
            
            value = self._get_input()
            
            if not value and self.default:
                value = self.default
            
            # Validate the input
            is_valid = self._validate_input(value)
            
            if not is_valid:
                # Validation failed - print error and retry
                ASCIIColors.print("  ✗ Invalid input, please try again.", color=ANSI.color_red)
                continue
            
            # Validation passed - print success and return
            ASCIIColors.print(f"  → {value}", color=ANSI.color_green)
            return value


def text(message: str, default: str = "",
         validate: Optional[Union[Callable[[str], bool], Validator]] = None,
         style: Optional[Dict[str, str]] = None, **kwargs) -> PromptText:
    """Create a text input question."""
    return PromptText(message, default, validate, style, **kwargs)
