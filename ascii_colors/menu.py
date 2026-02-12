# -*- coding: utf-8 -*-
"""
Interactive styled command-line menu.
Enhanced with checkbox support for questionary compatibility.
"""

import sys
import shutil
import textwrap
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, Iterator
from ascii_colors.constants import ANSI
from ascii_colors.core import ASCIIColors
from ascii_colors.utils import _get_key, strip_ansi


class MenuItem:
    """Represents an item within a Menu."""
    def __init__(self, text: str, item_type: str = 'action', target: Any = None, value: Any = None, 
                 disabled: bool = False, selected: bool = False, exit_on_success: bool = False, 
                 is_input: bool = False, initial_input: str = "", help_text: Optional[str] = None, 
                 custom_color: Optional[str] = None, checked: bool = False):
        self.text = text
        self.item_type = item_type  # 'action', 'submenu', 'checkbox', 'radio', 'back', 'quit'
        self.target = target
        self.value = value if value is not None else text
        self.disabled = disabled
        self.selected = selected
        self.exit_on_success = exit_on_success
        self.is_input = is_input
        self.input_value = initial_input
        self.help_text = help_text
        self.custom_color = custom_color
        self.checked = checked  # For checkbox items


class Menu:
    """Interactive styled command-line menu.
    
    Now supports checkbox and radio modes for questionary-like behavior.
    """
    
    MODE_EXECUTE = 'execute'      # Traditional menu mode
    MODE_SELECT = 'select'        # Single selection (like questionary.select)
    MODE_RETURN = 'return'        # Alias for select mode
    MODE_CHECKBOX = 'checkbox'    # Multi selection (like questionary.checkbox)
    
    def __init__(self, title: str, parent: Optional['Menu'] = None, 
                 mode: str = MODE_EXECUTE, **kwargs):
        self.title = title
        self.parent = parent
        self.mode = mode.lower()
        self.items: List[MenuItem] = []
        self.clear_screen = kwargs.get('clear_screen_on_run', True)
        self.enable_filtering = kwargs.get('enable_filtering', False)
        self.help_height = kwargs.get('help_area_height', 0)
        self.selected_icon = kwargs.get('selected_icon', "☑")
        self.unselected_icon = kwargs.get('unselected_icon', "☐")
        self.pointer = kwargs.get('pointer', "❯")
        self._sel_idx = 0
        self._filter = ""
        self._quit = False
        self._result: Any = None
        self._min_selected = kwargs.get('min_selected', 0)
        # Allow injecting a key source for testing
        self._key_source: Optional[Iterator[str]] = kwargs.get('key_source', None)
    
    def add_action(self, text: str, action: Optional[Callable] = None, **kwargs) -> 'Menu':
        """Add an action item."""
        self.items.append(MenuItem(text, 'action', target=action, **kwargs))
        return self
    
    def add_submenu(self, text: str, submenu: 'Menu', **kwargs) -> 'Menu':
        """Add a submenu."""
        submenu.parent = self
        self.items.append(MenuItem(text, 'submenu', target=submenu, **kwargs))
        return self
    
    def add_choice(self, text: str, value: Any = None, **kwargs) -> 'Menu':
        """Add a choice item (for select mode)."""
        self.items.append(MenuItem(text, 'radio', value=value, **kwargs))
        return self
    
    def add_choices(self, choices: List[Tuple[str, Any]]) -> 'Menu':
        """Add multiple choices at once."""
        for text, value in choices:
            self.add_choice(text, value)
        return self
    
    def add_checkbox(self, text: str, value: Any = None, checked: bool = False, **kwargs) -> 'Menu':
        """Add a checkbox item (for checkbox mode)."""
        self.items.append(MenuItem(text, 'checkbox', value=value, checked=checked, **kwargs))
        return self
    
    def add_input(self, text: str, **kwargs) -> 'Menu':
        """Add an input field item."""
        self.items.append(MenuItem(text, 'action', target=None, is_input=True, **kwargs))
        return self
    
    def _get_keypress(self) -> str:
        """Get a keypress, either from injected source or from terminal."""
        if self._key_source is not None:
            try:
                return next(self._key_source)
            except StopIteration:
                return 'QUIT'
        return _get_key()
    
    def _clear_screen(self) -> None:
        """Clear the screen in a cross-platform way."""
        # Use ANSI escape codes first
        print("\033[2J\033[H", end="")
        # Also try Windows-specific clear if needed
        if sys.platform == 'win32':
            try:
                import os
                os.system('cls')
            except:
                pass
        # Flush to ensure it's applied
        sys.stdout.flush()
    
    def _display(self, items: List[MenuItem]) -> None:
        """Render the menu display."""
        if self.clear_screen:
            self._clear_screen()
        
        # Title - process rich markup
        title_color = ANSI.color_bright_yellow
        title_processed = ASCIIColors._apply_rich_markup(self.title)
        ASCIIColors.print(title_processed, color=title_color, style=ANSI.style_bold, markup=False)
        
        # Title underline
        title_plain = strip_ansi(title_processed)
        print("-" * len(title_plain))
        
        # Instructions based on mode - process rich markup
        if self.mode == self.MODE_CHECKBOX:
            instruction = "↑↓ navigate • Space toggle • Enter confirm • a toggle all"
            ASCIIColors.print(ASCIIColors._apply_rich_markup(instruction), color=ANSI.style_dim, markup=False)
        elif self.mode in (self.MODE_SELECT, self.MODE_RETURN):
            instruction = "↑↓ navigate • Enter select • q cancel"
            ASCIIColors.print(ASCIIColors._apply_rich_markup(instruction), color=ANSI.style_dim, markup=False)
        else:
            instruction = "↑↓ navigate • Enter select • q quit"
            ASCIIColors.print(ASCIIColors._apply_rich_markup(instruction), color=ANSI.style_dim, markup=False)
        print()
        
        for i, item in enumerate(items):
            is_selected = i == self._sel_idx
            
            # Build prefix
            if is_selected:
                prefix = f"{ANSI.color_green}{self.pointer}{ANSI.color_reset} "
            else:
                prefix = "  "
            
            # Build content based on item type
            if item.item_type == 'checkbox':
                icon = self.selected_icon if item.checked else self.unselected_icon
                icon_colored = f"{ANSI.color_green}{icon}{ANSI.color_reset}" if item.checked else icon
                content = f"{icon_colored} {item.text}"
            else:
                content = item.text
            
            # Add input value indicator
            if item.is_input and item.input_value:
                content += f" [{item.input_value}]"
            
            # Process rich markup in content
            content = ASCIIColors._apply_rich_markup(content)
            
            # Apply colors
            if item.disabled:
                display = f"{prefix}{ANSI.style_dim}{content} (disabled){ANSI.color_reset}"
            elif is_selected:
                if item.custom_color:
                    custom_processed = ASCIIColors._apply_rich_markup(item.custom_color)
                    display = f"{prefix}{custom_processed}{content}{ANSI.color_reset}"
                else:
                    # Highlight selected item with cyan background
                    display = f"{prefix}{ANSI.color_bg_cyan}{ANSI.color_black} {content} {ANSI.color_reset}"
            else:
                if item.custom_color:
                    custom_processed = ASCIIColors._apply_rich_markup(item.custom_color)
                    display = f"{prefix}{custom_processed}{content}{ANSI.color_reset}"
                else:
                    display = f"{prefix}{content}"
            
            # Print with markup=False since we've already processed it
            print(display)
        
        if self.enable_filtering:
            filter_text = f"\nFilter: {self._filter}_"
            ASCIIColors.print(ASCIIColors._apply_rich_markup(filter_text), color="", markup=False)
    
    def run(self) -> Any:
        """Run the menu and return result based on mode."""
        while not self._quit:
            # Filter items
            if self.enable_filtering and self._filter:
                display_items = [it for it in self.items 
                               if self._filter.lower() in it.text.lower() 
                               or (it.is_input and self._filter.lower() in str(it.input_value).lower())]
            else:
                display_items = list(self.items)  # Don't use copy(), just reference
            
            # Add navigation items
            if self.parent:
                display_items.append(MenuItem("← Back", "back"))
            elif self.mode == self.MODE_EXECUTE:
                display_items.append(MenuItem("✕ Quit", "quit"))
            
            # Ensure selection is valid and points to a non-disabled item
            self._ensure_valid_selection(display_items)
            
            self._display(display_items)
            key = self._get_keypress()
            
            if key == 'UP':
                self._move_selection(display_items, -1)
                    
            elif key == 'DOWN':
                self._move_selection(display_items, 1)
                    
            elif key == 'ENTER':
                result = self._handle_select(display_items[self._sel_idx])
                if result is not None:
                    return result
                    
            elif key == ' ' or key == 'SPACE':
                # Toggle checkbox
                if self.mode == self.MODE_CHECKBOX:
                    item = display_items[self._sel_idx]
                    if item.item_type == 'checkbox' and not item.disabled:
                        item.checked = not item.checked
                elif self.mode in (self.MODE_SELECT, self.MODE_RETURN):
                    # In select mode, space also selects and returns
                    result = self._handle_select(display_items[self._sel_idx])
                    if result is not None:
                        return result
                        
            elif key == 'a' or key == 'A':
                # Toggle all checkboxes
                if self.mode == self.MODE_CHECKBOX:
                    # Get all checkbox items from original items list (not display_items which may have nav items)
                    checkbox_items = [it for it in self.items if it.item_type == 'checkbox' and not it.disabled]
                    if checkbox_items:
                        all_checked = all(it.checked for it in checkbox_items)
                        for it in self.items:
                            if it.item_type == 'checkbox' and not it.disabled:
                                it.checked = not all_checked
                            
            elif key == 'QUIT' or key == 'q':
                if self.mode in (self.MODE_SELECT, self.MODE_RETURN, self.MODE_CHECKBOX):
                    raise KeyboardInterrupt
                self._quit = True
                
            elif self.enable_filtering:
                if key == 'BACKSPACE':
                    self._filter = self._filter[:-1]
                elif len(key) == 1 and key.isprintable():
                    self._filter += key
                    self._sel_idx = 0
        
        return None
    
    def _ensure_valid_selection(self, display_items: List[MenuItem]) -> None:
        """Ensure the current selection index points to a valid, non-disabled item."""
        if not display_items:
            self._sel_idx = 0
            return
        
        n = len(display_items)
        
        # Clamp to valid range first
        if self._sel_idx >= n:
            self._sel_idx = n - 1
        if self._sel_idx < 0:
            self._sel_idx = 0
        
        # If current selection is disabled, find the nearest non-disabled one
        if display_items[self._sel_idx].disabled:
            # Search forward
            for i in range(self._sel_idx, n):
                if not display_items[i].disabled:
                    self._sel_idx = i
                    return
            # Search backward
            for i in range(self._sel_idx - 1, -1, -1):
                if not display_items[i].disabled:
                    self._sel_idx = i
                    return
    
    def _move_selection(self, display_items: List[MenuItem], direction: int) -> None:
        """Move selection in the given direction, skipping disabled items."""
        if not display_items:
            return
        
        n = len(display_items)
        if n <= 1:
            return
        
        # Use modular arithmetic to find next non-disabled item
        current = self._sel_idx
        for step in range(1, n + 1):
            new_idx = (current + direction * step) % n
            if not display_items[new_idx].disabled:
                self._sel_idx = new_idx
                return
    
    def _handle_select(self, item: MenuItem) -> Any:
        """Handle selection of an item. Returns value to return, or None to continue."""
        if item.disabled:
            return None
            
        if item.item_type == 'back':
            self._quit = True
            return None
            
        elif item.item_type == 'quit':
            self._quit = True
            return None
            
        elif item.item_type == 'submenu':
            # Temporarily set key source on submenu if we have one
            if self._key_source is not None:
                item.target._key_source = self._key_source
            result = item.target.run()
            if self.mode in (self.MODE_SELECT, self.MODE_RETURN, self.MODE_CHECKBOX):
                return result
            if result is not None:
                return result
            return None
            
        elif item.item_type == 'checkbox':
            # In checkbox mode, Enter key confirms and returns the selected values
            # Do NOT toggle here - Space toggles, Enter confirms
            if self.mode == self.MODE_CHECKBOX:
                selected_count = sum(1 for it in self.items 
                                   if it.checked and not it.disabled and it.item_type == 'checkbox')
                if selected_count >= self._min_selected:
                    return self.get_selected_values()
                # Not enough selected, continue waiting
                return None
            return None
            
        elif item.item_type == 'radio':
            if self.mode in (self.MODE_SELECT, self.MODE_RETURN):
                return item.value
            if callable(item.target):
                result = item.target()
                if item.exit_on_success and result is not False:
                    return item.value
            return item.value
            
        elif item.item_type == 'action':
            if item.is_input:
                prompt = f"{item.text}: "
                ASCIIColors.print(prompt, color=ANSI.color_green, end="", flush=True)
                try:
                    try:
                        value = input()
                    except (OSError, EOFError):
                        value = item.input_value or ""
                    if not value and item.input_value:
                        value = item.input_value
                    item.input_value = value
                except EOFError:
                    pass
                return None
            
            if callable(item.target):
                result = item.target()
                if item.exit_on_success and result is not False:
                    return item.value
                return None
            else:
                if self.mode not in (self.MODE_EXECUTE,):
                    return item.value
                return None
                
        return None
    
    def get_selected_values(self) -> List[Any]:
        """Get all checked values (for checkbox mode)."""
        return [it.value for it in self.items if it.checked and not it.disabled and it.item_type == 'checkbox']
    
    def get_selected_value(self) -> Any:
        """Get single selected value (for select mode)."""
        for it in self.items:
            if it.selected and not it.disabled:
                return it.value
        return None
