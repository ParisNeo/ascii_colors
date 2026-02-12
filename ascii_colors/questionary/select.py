# -*- coding: utf-8 -*-
"""
Single selection question type for questionary compatibility.
"""

from typing import Any, Dict, List, Optional, Union
from ascii_colors.menu import Menu, MenuItem
from ascii_colors.questionary.base import Question


class Select(Question):
    """Single selection from list."""
    def __init__(self, message: str, choices: List[Union[str, Dict[str, Any]]],
                 default: Optional[Union[str, int]] = None,
                 style: Optional[Dict[str, str]] = None, **kwargs):
        super().__init__(message, default, None, style, **kwargs)
        self.choices = self._normalize_choices(choices)
        self.pointer = kwargs.get('pointer', "❯")
        self.use_indicator = kwargs.get('use_indicator', True)
        self.use_shortcuts = kwargs.get('use_shortcuts', False)
    
    def _normalize_choices(self, choices: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Normalize choice list to standard format."""
        result = []
        for i, c in enumerate(choices):
            if isinstance(c, str):
                result.append({'name': c, 'value': c, 'disabled': False})
            else:
                result.append({
                    'name': c.get('name', c.get('value', str(i))),
                    'value': c.get('value', c.get('name', str(i))),
                    'disabled': c.get('disabled', False),
                })
        return result
    
    def _ask_internal(self) -> Any:
        # Build menu with injected key source
        # Process message for rich markup in title
        from ascii_colors.core import ASCIIColors
        processed_message = ASCIIColors._apply_rich_markup(self.message)
        
        menu = Menu(processed_message, mode='return', clear_screen_on_run=False, key_source=self._key_source)
        
        for choice in self.choices:
            # Process choice text for rich markup
            processed_name = ASCIIColors._apply_rich_markup(choice['name'])
            if choice['disabled']:
                # Create disabled item with processed name
                menu.items.append(MenuItem(processed_name, 'action', None, disabled=True))
            else:
                menu.add_choice(processed_name, value=choice['value'])
        
        # Set initial selection
        menu._sel_idx = 0
        while menu._sel_idx < len(menu.items) and menu.items[menu._sel_idx].disabled:
            menu._sel_idx += 1
        
        return menu.run()


def select(message: str, choices: List[Union[str, Dict[str, Any]]],
           default: Optional[Union[str, int]] = None,
           style: Optional[Dict[str, str]] = None, **kwargs) -> Select:
    """Create a single-select question."""
    return Select(message, choices, default, style, **kwargs)
