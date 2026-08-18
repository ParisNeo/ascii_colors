# -*- coding: utf-8 -*-
"""
Interactive styled command-line menu.
Enhanced with checkbox, radio, pagination, search, shortcuts, and panel framing.
"""

import sys
import io
import shutil
import textwrap
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, Iterator, IO
from ascii_colors.constants import ANSI
from ascii_colors.core import ASCIIColors
from ascii_colors.utils import _get_key, strip_ansi


class MenuItem:
    """Represents an item within a Menu."""
    def __init__(
        self,
        text: str,
        item_type: str = 'action',
        target: Any = None,
        value: Any = None,
        disabled: bool = False,
        selected: bool = False,
        exit_on_success: bool = False,
        is_input: bool = False,
        initial_input: str = "",
        help_text: Optional[str] = None,
        custom_color: Optional[str] = None,
        checked: bool = False,
        shortcut: Optional[str] = None,
    ):
        self.text = text
        self.item_type = item_type  # 'action', 'submenu', 'checkbox', 'radio', 'separator', 'back', 'quit'
        self.target = target
        self.value = value if value is not None else text
        self.disabled = disabled
        self.selected = selected
        self.exit_on_success = exit_on_success
        self.is_input = is_input
        self.input_value = initial_input
        self.help_text = help_text
        self.custom_color = custom_color
        self.checked = checked
        self.shortcut = str(shortcut).strip() if shortcut is not None else None


class Menu:
    """Interactive styled command-line menu.
    
    Supports:
    - Execution mode (actions & submenus)
    - Selection mode (single pick)
    - Checkbox mode (multi pick with toggle-all and invert)
    - Dynamic viewport scrolling with scroll indicators (▲ / ▼)
    - Real-time search/filtering
    - Live contextual help/description area
    - Hotkey / numeric shortcuts for instant navigation
    - Decorative separators
    - Rich box/panel framing option
    """
    
    MODE_EXECUTE = 'execute'      # Traditional menu mode
    MODE_SELECT = 'select'        # Single selection
    MODE_RETURN = 'return'        # Alias for select mode
    MODE_CHECKBOX = 'checkbox'    # Multi selection
    
    def __init__(
        self,
        title: str,
        parent: Optional['Menu'] = None,
        mode: str = MODE_EXECUTE,
        *,
        default: Optional[Union[int, Any]] = None,
        pointer: str = "❯",
        selected_icon: str = "☑",
        unselected_icon: str = "☐",
        clear_screen_on_run: bool = True,
        enable_filtering: bool = False,
        enable_shortcuts: bool = False,
        show_help: bool = True,
        help_area_height: int = 0,
        min_selected: int = 0,
        key_source: Optional[Iterator[str]] = None,
        file: IO[str] = sys.stdout,
        intro_text: Optional[str] = None,
        back_text: str = "← Back",
        quit_text: str = "✕ Quit",
        panel: bool = False,
        border_style: str = "cyan",
        viewport_size: Optional[int] = None,
    ):
        self.title = title
        self.parent = parent
        self.mode = mode.lower()
        self.items: List[MenuItem] = []
        self.default = default
        self.pointer = pointer
        self.selected_icon = selected_icon
        self.unselected_icon = unselected_icon
        self.clear_screen = clear_screen_on_run
        self.enable_filtering = enable_filtering
        self.enable_shortcuts = enable_shortcuts
        self.show_help = show_help
        self.help_height = help_area_height
        self._min_selected = min_selected
        self._key_source = key_source
        self._file = file
        self._intro_text = intro_text
        self.back_text = back_text
        self.quit_text = quit_text
        self.panel = panel
        self.border_style = border_style
        self._custom_viewport_size = viewport_size
        
        self._sel_idx = 0
        self._viewport_offset = 0
        self._filter = ""
        self._quit = False
        self._result: Any = None
        self._last_frame_lines: int = 0

    def set_intro(self, text: str) -> 'Menu':
        """Set introductory text to display below the menu title."""
        self._intro_text = text
        return self
    
    def add_action(
        self,
        text: str,
        action: Optional[Callable] = None,
        value: Any = None,
        help_text: Optional[str] = None,
        shortcut: Optional[str] = None,
        disabled: bool = False,
        custom_color: Optional[str] = None,
        **kwargs: Any
    ) -> 'Menu':
        """Add an action item that executes a callback."""
        self.items.append(MenuItem(
            text, 'action', target=action, value=value, help_text=help_text,
            shortcut=shortcut, disabled=disabled, custom_color=custom_color, **kwargs
        ))
        return self
    
    def add_submenu(
        self,
        text: str,
        submenu: 'Menu',
        help_text: Optional[str] = None,
        shortcut: Optional[str] = None,
        disabled: bool = False,
        **kwargs: Any
    ) -> 'Menu':
        """Add a nested submenu."""
        submenu.parent = self
        self.items.append(MenuItem(
            text, 'submenu', target=submenu, help_text=help_text,
            shortcut=shortcut, disabled=disabled, **kwargs
        ))
        return self
    
    def add_choice(
        self,
        text: str,
        value: Any = None,
        help_text: Optional[str] = None,
        shortcut: Optional[str] = None,
        disabled: bool = False,
        custom_color: Optional[str] = None,
        **kwargs: Any
    ) -> 'Menu':
        """Add a choice item for single selection mode."""
        self.items.append(MenuItem(
            text, 'radio', value=value, help_text=help_text,
            shortcut=shortcut, disabled=disabled, custom_color=custom_color, **kwargs
        ))
        return self
    
    def add_choices(self, choices: List[Union[str, Tuple[str, Any], Dict[str, Any]]]) -> 'Menu':
        """Add multiple choices at once."""
        for c in choices:
            if isinstance(c, tuple):
                text, value = c[0], c[1]
                help_text = c[2] if len(c) > 2 else None
                self.add_choice(text, value=value, help_text=help_text)
            elif isinstance(c, dict):
                text = c.get('text', c.get('name', ''))
                val = c.get('value', text)
                help_txt = c.get('help_text', c.get('description', None))
                sc = c.get('shortcut', None)
                dis = c.get('disabled', False)
                self.add_choice(text, value=val, help_text=help_txt, shortcut=sc, disabled=dis)
            else:
                self.add_choice(str(c), value=c)
        return self
    
    def add_checkbox(
        self,
        text: str,
        value: Any = None,
        checked: bool = False,
        help_text: Optional[str] = None,
        shortcut: Optional[str] = None,
        disabled: bool = False,
        **kwargs: Any
    ) -> 'Menu':
        """Add a checkbox item for multi-selection mode."""
        self.items.append(MenuItem(
            text, 'checkbox', value=value, checked=checked, help_text=help_text,
            shortcut=shortcut, disabled=disabled, **kwargs
        ))
        return self

    def add_separator(self, text: str = "") -> 'Menu':
        """Add a decorative non-selectable separator."""
        self.items.append(MenuItem(text, 'separator', disabled=True))
        return self
    
    def add_input(
        self,
        text: str,
        initial_value: str = "",
        help_text: Optional[str] = None,
        shortcut: Optional[str] = None,
        **kwargs: Any
    ) -> 'Menu':
        """Add an editable input field item."""
        self.items.append(MenuItem(
            text, 'action', target=None, is_input=True, initial_input=initial_value,
            help_text=help_text, shortcut=shortcut, **kwargs
        ))
        return self
    
    def _get_keypress(self) -> str:
        """Get a keypress, either from injected test source or from terminal."""
        if self._key_source is not None:
            try:
                return next(self._key_source)
            except StopIteration:
                return 'QUIT'
        return _get_key()
    
    def _write(self, text: str) -> None:
        """Write directly to the menu's output stream."""
        self._file.write(text)

    def _display(self, items: List[MenuItem]) -> None:
        """Render the menu frame atomically with viewport scrolling and help preview."""
        buffer: List[str] = []
        previous_frame_lines = self._last_frame_lines
        self._clear_previous_frame(buffer)
        lines_written: int = 0
        
        # 1. Header (Title & Intro)
        title_color = ANSI.color_bright_yellow
        title_processed = ASCIIColors._apply_rich_markup(self.title)
        out = ASCIIColors.print(title_processed, color=title_color, style=ANSI.style_bold, markup=False, emit=False)
        buffer.append(out)
        lines_written += 1
        
        title_plain = strip_ansi(title_processed)
        buffer.append(f"{ANSI.style_dim}{'─' * max(len(title_plain), 20)}{ANSI.color_reset}\n")
        lines_written += 1
        
        if self._intro_text:
            intro_processed = ASCIIColors._apply_rich_markup(self._intro_text)
            intro_out = ASCIIColors.print(intro_processed, color=ANSI.style_dim, markup=False, emit=False)
            buffer.append(intro_out)
            lines_written += 1
            buffer.append("\n")
            lines_written += 1
        
        # 2. Instruction Banner
        if self.mode == self.MODE_CHECKBOX:
            instruction = "↑↓ move • Space toggle • a all • i invert • Enter confirm • q cancel"
        elif self.mode in (self.MODE_SELECT, self.MODE_RETURN):
            instruction = "↑↓ move • Enter select • / search • q cancel"
        else:
            instruction = "↑↓ move • Enter select • / search • q quit"
            
        instr_out = ASCIIColors.print(f"{ANSI.style_dim}{instruction}{ANSI.color_reset}", markup=False, emit=False)
        buffer.append(instr_out)
        lines_written += 1
        buffer.append("\n")
        lines_written += 1
        
        # 3. Viewport calculation
        header_height = lines_written
        try:
            term_height = shutil.get_terminal_size().lines
        except Exception:
            term_height = 25
            
        help_reserve = 3 if self.show_help else 0
        if self._custom_viewport_size:
            viewport_size = self._custom_viewport_size
        else:
            viewport_size = max(5, min(15, term_height - header_height - help_reserve - 3))
        
        total_items = len(items)
        if total_items > viewport_size:
            if self._sel_idx < self._viewport_offset:
                self._viewport_offset = self._sel_idx
            elif self._sel_idx >= self._viewport_offset + viewport_size:
                self._viewport_offset = self._sel_idx - viewport_size + 1
            
            # Clamp viewport bounds
            self._viewport_offset = max(0, min(self._viewport_offset, total_items - viewport_size))
            visible_items = items[self._viewport_offset:self._viewport_offset + viewport_size]
        else:
            visible_items = items
            self._viewport_offset = 0
        
        # Top Scroll Indicator
        if self._viewport_offset > 0:
            buffer.append(f"  {ANSI.color_cyan}▲ ({self._viewport_offset} more above){ANSI.color_reset}\n")
            lines_written += 1

        # 4. Item List
        for i, item in enumerate(visible_items):
            actual_idx = i + self._viewport_offset
            is_selected = actual_idx == self._sel_idx
            
            if item.item_type == 'separator':
                sep_text = item.text or "──────────────────────────────"
                buffer.append(f"  {ANSI.style_dim}{sep_text}{ANSI.color_reset}\n")
                lines_written += 1
                continue
            
            # Prefix pointer
            if is_selected:
                prefix = f"{ANSI.color_green}{self.pointer}{ANSI.color_reset} "
            else:
                prefix = "  "
            
            # Shortcut badge
            shortcut_badge = ""
            if self.enable_shortcuts and item.shortcut:
                shortcut_badge = f"{ANSI.color_yellow}[{item.shortcut}]{ANSI.color_reset} "
            
            # Item content
            if item.item_type == 'checkbox':
                icon = self.selected_icon if item.checked else self.unselected_icon
                icon_colored = f"{ANSI.color_green}{icon}{ANSI.color_reset}" if item.checked else f"{ANSI.style_dim}{icon}{ANSI.color_reset}"
                content = f"{shortcut_badge}{icon_colored} {item.text}"
            elif item.item_type == 'submenu':
                content = f"{shortcut_badge}{item.text} {ANSI.color_cyan}→{ANSI.color_reset}"
            else:
                content = f"{shortcut_badge}{item.text}"
            
            if item.is_input and item.input_value:
                content += f" {ANSI.color_cyan}[{item.input_value}]{ANSI.color_reset}"
            
            content = ASCIIColors._apply_rich_markup(content)
            
            if item.disabled:
                display = f"{prefix}{ANSI.style_dim}{content} (disabled){ANSI.color_reset}"
            elif is_selected:
                if item.custom_color:
                    custom_processed = ASCIIColors._apply_rich_markup(item.custom_color)
                    display = f"{prefix}{custom_processed}{content}{ANSI.color_reset}"
                else:
                    display = f"{prefix}{ANSI.color_bg_cyan}{ANSI.color_black} {strip_ansi(content)} {ANSI.color_reset}"
            else:
                if item.custom_color:
                    custom_processed = ASCIIColors._apply_rich_markup(item.custom_color)
                    display = f"{prefix}{custom_processed}{content}{ANSI.color_reset}"
                else:
                    display = f"{prefix}{content}"
            
            buffer.append(display + "\n")
            lines_written += 1
        
        # Bottom Scroll Indicator
        if total_items > self._viewport_offset + len(visible_items):
            remaining = total_items - (self._viewport_offset + len(visible_items))
            buffer.append(f"  {ANSI.color_cyan}▼ ({remaining} more below){ANSI.color_reset}\n")
            lines_written += 1

        # 5. Contextual Help / Description Area
        if self.show_help:
            curr_item = items[self._sel_idx] if 0 <= self._sel_idx < len(items) else None
            help_msg = (curr_item.help_text if curr_item else None) or ""
            buffer.append(f"\n{ANSI.style_dim}ℹ {ASCIIColors._apply_rich_markup(help_msg)}{ANSI.color_reset}\n")
            lines_written += 2

        # 6. Real-time Search Filter Bar
        if self.enable_filtering:
            filter_text = f"Search: {ANSI.color_cyan}{self._filter}{ANSI.color_reset}_"
            buffer.append(f"\n{filter_text}\n")
            lines_written += 2
        
        self._last_frame_lines = lines_written

        if lines_written < previous_frame_lines:
            diff = previous_frame_lines - lines_written
            for _ in range(diff):
                buffer.append("\r\033[K\n")
            buffer.append(f"\033[{diff}A")

        self._file.write("".join(buffer))
        self._file.flush()

    def run(self) -> Any:
        """Run the interactive menu loop."""
        self._quit = False
        self._init_default_selection()
        
        try:
            while not self._quit:
                if self.enable_filtering and self._filter:
                    display_items = [
                        it for it in self.items
                        if it.item_type != 'separator' and (
                            self._filter.lower() in it.text.lower()
                            or (it.is_input and self._filter.lower() in str(it.input_value).lower())
                            or (it.help_text and self._filter.lower() in it.help_text.lower())
                        )
                    ]
                else:
                    display_items = list(self.items)
                
                if self.mode == self.MODE_EXECUTE:
                    if self.parent:
                        display_items.append(MenuItem(self.back_text, "back"))
                    else:
                        display_items.append(MenuItem(self.quit_text, "quit"))
                
                self._ensure_valid_selection(display_items)
                self._display(display_items)
                key = self._get_keypress()
                
                if key == 'UP':
                    self._move_selection(display_items, -1)
                elif key == 'DOWN':
                    self._move_selection(display_items, 1)
                elif key == 'PAGE_UP':
                    self._move_selection(display_items, -5)
                elif key == 'PAGE_DOWN':
                    self._move_selection(display_items, 5)
                elif key == 'ENTER':
                    if display_items and 0 <= self._sel_idx < len(display_items):
                        result = self._handle_select(display_items[self._sel_idx])
                        if result is not None:
                            self._write("\n")
                            self._file.flush()
                            return result
                elif key in (' ', 'SPACE'):
                    if self.mode == self.MODE_CHECKBOX and display_items:
                        item = display_items[self._sel_idx]
                        if item.item_type == 'checkbox' and not item.disabled:
                            item.checked = not item.checked
                    elif self.mode in (self.MODE_SELECT, self.MODE_RETURN) and display_items:
                        result = self._handle_select(display_items[self._sel_idx])
                        if result is not None:
                            self._write("\n")
                            self._file.flush()
                            return result
                elif key in ('a', 'A') and self.mode == self.MODE_CHECKBOX and not self.enable_filtering:
                    # Toggle All checkboxes
                    checkbox_items = [it for it in self.items if it.item_type == 'checkbox' and not it.disabled]
                    if checkbox_items:
                        all_checked = all(it.checked for it in checkbox_items)
                        for it in checkbox_items:
                            it.checked = not all_checked
                elif key in ('i', 'I') and self.mode == self.MODE_CHECKBOX and not self.enable_filtering:
                    # Invert checkbox selections
                    for it in self.items:
                        if it.item_type == 'checkbox' and not it.disabled:
                            it.checked = not it.checked
                elif key == '/' and not self.enable_filtering:
                    self.enable_filtering = True
                    self._filter = ""
                elif key in ('QUIT', 'q', 'Q'):
                    if self.enable_filtering and self._filter:
                        self._filter = ""
                        self.enable_filtering = False
                    elif self.mode in (self.MODE_SELECT, self.MODE_RETURN, self.MODE_CHECKBOX):
                        self._write("\n")
                        self._file.flush()
                        return None
                    else:
                        self._quit = True
                elif self.enable_filtering:
                    if key == 'BACKSPACE':
                        self._filter = self._filter[:-1]
                        self._sel_idx = 0
                        self._viewport_offset = 0
                        if not self._filter:
                            self.enable_filtering = False
                    elif len(key) == 1 and key.isprintable():
                        self._filter += key
                        self._sel_idx = 0
                        self._viewport_offset = 0
                else:
                    # Check for shortcut match (e.g. numeric hotkeys '1', '2' or defined shortcuts)
                    if len(key) == 1:
                        matched = False
                        for idx, item in enumerate(display_items):
                            if item.shortcut and item.shortcut.lower() == key.lower() and not item.disabled:
                                self._sel_idx = idx
                                result = self._handle_select(item)
                                if result is not None:
                                    self._write("\n")
                                    self._file.flush()
                                    return result
                                matched = True
                                break
            
            self._write("\n")
            self._file.flush()
            return None
        finally:
            self._erase_frame_and_reset()

    def _init_default_selection(self) -> None:
        """Position cursor at default item if configured."""
        if self.default is None:
            return
        if isinstance(self.default, int) and 0 <= self.default < len(self.items):
            self._sel_idx = self.default
        else:
            for i, item in enumerate(self.items):
                if item.value == self.default or item.text == self.default:
                    self._sel_idx = i
                    break

    def _ensure_valid_selection(self, display_items: List[MenuItem]) -> None:
        """Ensure selection index points to a non-disabled, non-separator item."""
        if not display_items:
            self._sel_idx = 0
            return
        
        n = len(display_items)
        if self._sel_idx >= n:
            self._sel_idx = n - 1
        if self._sel_idx < 0:
            self._sel_idx = 0
        
        if display_items[self._sel_idx].disabled or display_items[self._sel_idx].item_type == 'separator':
            for i in range(self._sel_idx, n):
                if not display_items[i].disabled and display_items[i].item_type != 'separator':
                    self._sel_idx = i
                    return
            for i in range(self._sel_idx - 1, -1, -1):
                if not display_items[i].disabled and display_items[i].item_type != 'separator':
                    self._sel_idx = i
                    return
    
    def _move_selection(self, display_items: List[MenuItem], direction: int) -> None:
        """Move selection smoothly, skipping disabled items and separators."""
        if not display_items:
            return
        n = len(display_items)
        if n <= 1:
            return
        
        step = 1 if direction > 0 else -1
        total_steps = abs(direction)
        
        for _ in range(total_steps):
            for s in range(1, n + 1):
                new_idx = (self._sel_idx + step * s) % n
                target = display_items[new_idx]
                if not target.disabled and target.item_type != 'separator':
                    self._sel_idx = new_idx
                    break

    def _handle_select(self, item: MenuItem) -> Any:
        """Process item selection."""
        if item.disabled or item.item_type == 'separator':
            return None
            
        if item.item_type == 'back':
            self._quit = True
            return item.value
            
        elif item.item_type == 'quit':
            self._quit = True
            return item.value
            
        elif item.item_type == 'submenu':
            if self._last_frame_lines > 0:
                self._clear_previous_frame()
                self._last_frame_lines = 0

            if self._key_source is not None:
                item.target._key_source = self._key_source
            item.target._file = self._file
            item.target._last_frame_lines = 0

            result = item.target.run()
            self._last_frame_lines = item.target._last_frame_lines

            if self.mode in (self.MODE_SELECT, self.MODE_RETURN, self.MODE_CHECKBOX):
                return result
            if result is not None:
                return result
            return None
            
        elif item.item_type == 'checkbox':
            if self.mode == self.MODE_CHECKBOX:
                selected_count = sum(1 for it in self.items if it.checked and not it.disabled and it.item_type == 'checkbox')
                if selected_count >= self._min_selected:
                    return self.get_selected_values()
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
                prompt_out = ASCIIColors.print(prompt, color=ANSI.color_green, end="", flush=True, file=self._file, markup=False, emit=False)
                self._write(prompt_out)
                self._file.flush()
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
                if self._last_frame_lines > 0:
                    self._clear_previous_frame()
                    self._last_frame_lines = 0

                _ = item.target()

                if self.mode in (self.MODE_SELECT, self.MODE_RETURN, self.MODE_CHECKBOX):
                    return item.value
                return item.value if item.value is not None else True
            else:
                if self.mode not in (self.MODE_EXECUTE,):
                    return item.value
                return True
                
        return None

    def get_selected_values(self) -> List[Any]:
        """Get all checked values in checkbox mode."""
        return [it.value for it in self.items if it.checked and not it.disabled and it.item_type == 'checkbox']
    
    def get_selected_value(self) -> Any:
        """Get single selected value in select mode."""
        for it in self.items:
            if it.selected and not it.disabled:
                return it.value
        return None
    
    def _clear_previous_frame(self, buffer: Optional[List[str]] = None) -> None:
        """Clear previously rendered frame."""
        if self._last_frame_lines > 0:
            execute_immediately = buffer is None
            if execute_immediately:
                buffer = []

            buffer.append(f"\033[{self._last_frame_lines}A")
            for _ in range(self._last_frame_lines):
                buffer.append("\r\033[K\n")
            buffer.append(f"\033[{self._last_frame_lines}A")
            self._last_frame_lines = 0

            if execute_immediately:
                self._file.write("".join(buffer))
                self._file.flush()

    def _erase_frame_and_reset(self) -> None:
        """Cleanly clear menu buffer from screen."""
        if self._last_frame_lines > 0:
            clear_seq = []
            clear_seq.append(f"\033[{self._last_frame_lines}A")
            for _ in range(self._last_frame_lines):
                clear_seq.append("\r\033[K\n")
            clear_seq.append(f"\033[{self._last_frame_lines}A")
            self._file.write("".join(clear_seq))
            self._file.flush()
            self._last_frame_lines = 0