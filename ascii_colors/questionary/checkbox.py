# -*- coding: utf-8 -*-
"""
Multi-select checkbox question type for questionary compatibility.
"""

from typing import Any, Dict, List, Optional, Union, Iterator
from ascii_colors.menu import Menu
from ascii_colors.questionary.base import Question


class Checkbox(Question):
    """Multiple selection from list."""
    def __init__(self, message: str, choices: List[Union[str, Dict[str, Any]]],
                 default: Optional[List[Union[str, int]]] = None,
                 style: Optional[Dict[str, str]] = None, **kwargs):
        # Don't call super().__init__ directly
        self.message = message
        self.default = default
        self.validate = None
        self.style = style or {}
        self.kwargs = kwargs
        self._answers: Dict[str, Any] = {}
        self._input_source = kwargs.get('input_source', None)
        self._key_source = kwargs.get('key_source', None)
        self.choices = self._normalize_choices(choices)
        self.pointer = kwargs.get('pointer', "❯")
        self.selected_icon = kwargs.get('selected_icon', "☑")
        self.unselected_icon = kwargs.get('unselected_icon', "☐")
        self.min_selected = kwargs.get('min_selected', 0)
        
        # Set default selections
        if default:
            for d in default:
                if isinstance(d, int) and 0 <= d < len(self.choices):
                    self.choices[d]['checked'] = True
                else:
                    for c in self.choices:
                        if c['value'] == d or c['name'] == d:
                            c['checked'] = True
                            break
    
    def _normalize_choices(self, choices: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Normalize choice list with checked state."""
        result = []
        for i, c in enumerate(choices):
            if isinstance(c, str):
                result.append({
                    'name': c, 'value': c, 'disabled': False, 'checked': False
                })
            else:
                result.append({
                    'name': c.get('name', c.get('value', str(i))),
                    'value': c.get('value', c.get('name', str(i))),
                    'disabled': c.get('disabled', False),
                    'checked': c.get('checked', False),
                })
        return result
    
    def ask(self, patch_stdout: bool = False, kbi_msg: str = "Cancelled by user") -> Any:
        """Ask the question and return the answer."""
        try:
            return self._ask_internal()
        except KeyboardInterrupt:
            print(f"\n{kbi_msg}")
            return None
    
    def _ask_internal(self) -> List[Any]:
        from ascii_colors.core import ASCIIColors
        
        # Process message for rich markup
        processed_message = ASCIIColors._apply_rich_markup(self.message)
        
        # Build menu with injected key source
        menu = Menu(processed_message, mode='checkbox', clear_screen_on_run=False, 
                   min_selected=self.min_selected, key_source=self._key_source)
        
        for choice in self.choices:
            # Process choice text for rich markup
            processed_name = ASCIIColors._apply_rich_markup(choice['name'])
            menu.add_checkbox(processed_name, value=choice['value'], 
                            checked=choice['checked'], disabled=choice['disabled'])
        
        result = menu.run()
        if result is None:
            return []
        return result if isinstance(result, list) else [result]
    
    def skip_if(self, condition: bool, default: Any = None) -> 'Checkbox':
        """Skip this question if condition is true."""
        if condition:
            self._ask_internal = lambda: default  # type: ignore
        return self
    
    def unsafe_ask(self, patch_stdout: bool = False) -> List[Any]:
        """Ask without catching KeyboardInterrupt."""
        return self._ask_internal()


def checkbox(message: str, choices: List[Union[str, Dict[str, Any]]],
             default: Optional[List[Union[str, int]]] = None,
             style: Optional[Dict[str, str]] = None, **kwargs) -> Checkbox:
    """Create a multi-select checkbox question."""
    return Checkbox(message, choices, default, style, **kwargs)
