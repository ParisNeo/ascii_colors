# -*- coding: utf-8 -*-
"""
Questionary-compatible API for ascii_colors.
Provides drop-in replacement for questionary library with enhanced styling.
"""

import sys
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, Iterator, Sequence
from ascii_colors.constants import ANSI, LogLevel
from ascii_colors.core import ASCIIColors
from ascii_colors.menu import Menu, MenuItem
from ascii_colors.utils import _get_key, strip_ansi

_T = TypeVar('_T')


class ValidationError(Exception):
    """Exception raised when validation fails."""
    def __init__(self, message: str = "invalid input"):
        self.message = message
        super().__init__(self.message)


class Validator:
    """Base class for input validators."""
    def __init__(self, message: str = "invalid input"):
        self.message = message
    
    def validate(self, document: str) -> None:
        """Validate the input. Raise ValidationError if invalid."""
        raise NotImplementedError
    
    def __call__(self, document: str) -> bool:
        try:
            self.validate(document)
            return True
        except ValidationError:
            return False


class Question:
    """Base class for all question types."""
    def __init__(self, message: str, default: Any = None, 
                 validate: Optional[Union[Callable[[str], bool], Validator]] = None,
                 style: Optional[Dict[str, str]] = None, **kwargs):
        self.message = message
        self.default = default
        self.validate = validate
        self.style = style or {}
        self.kwargs = kwargs
        self._answers: Dict[str, Any] = {}
        # Allow injecting input for testing
        self._input_source: Optional[Iterator[str]] = kwargs.get('input_source', None)
        self._key_source: Optional[Iterator[str]] = kwargs.get('key_source', None)
    
    def ask(self, patch_stdout: bool = False, kbi_msg: str = "Cancelled by user") -> Any:
        """Ask the question and return the answer."""
        try:
            return self._ask_internal()
        except KeyboardInterrupt:
            print(f"\n{kbi_msg}")
            return None
    
    def _ask_internal(self) -> Any:
        raise NotImplementedError
    
    def unsafe_ask(self, patch_stdout: bool = False) -> Any:
        """Ask without catching KeyboardInterrupt."""
        return self._ask_internal()
    
    def skip_if(self, condition: bool, default: Any = None) -> 'Question':
        """Skip this question if condition is true."""
        if condition:
            self._ask_internal = lambda: default  # type: ignore
        return self
    
    def _get_input(self, prompt: str = "") -> str:
        """Get input, either from injected source or from stdin."""
        if self._input_source is not None:
            try:
                return next(self._input_source)
            except StopIteration:
                return self.default or ""
        try:
            return input(prompt)
        except (EOFError, OSError):
            return self.default or ""
    
    def _get_key(self) -> str:
        """Get keypress, either from injected source or from terminal."""
        if self._key_source is not None:
            try:
                return next(self._key_source)
            except StopIteration:
                return 'QUIT'
        return _get_key()
    
    def _validate_input(self, value: str) -> bool:
        """Run validation on input."""
        if self.validate is None:
            return True
        if isinstance(self.validate, Validator):
            try:
                self.validate.validate(value)
                return True
            except ValidationError:
                return False
        else:
            try:
                result = self.validate(value)
                return bool(result)
            except Exception:
                return False


class Text(Question):
    """Text input question."""
    def __init__(self, message: str, default: str = "", 
                 validate: Optional[Union[Callable[[str], bool], Validator]] = None,
                 style: Optional[Dict[str, str]] = None, **kwargs):
        super().__init__(message, default, validate, style, **kwargs)
        self.multiline = kwargs.get('multiline', False)
    def append(self, text:str):
        self.message += text
        
    def _ask_internal(self) -> str:
        color = self.style.get('question', ANSI.color_bright_yellow)
        answer_color = self.style.get('answer', ANSI.color_white)
        
        while True:
            prompt_text = f"{self.message}: "
            if self.default:
                prompt_text = f"{self.message} [{self.default}]: "
            
            ASCIIColors.print(prompt_text, color=color, end="", flush=True)
            
            try:
                if self.multiline:
                    lines = []
                    print("(Enter empty line to finish)")
                    while True:
                        line = self._get_input()
                        if not line and not lines:
                            if self.default:
                                value = self.default
                                break
                            continue
                        if not line:
                            break
                        lines.append(line)
                    value = "\n".join(lines)
                else:
                    value = self._get_input()
                    if not value and self.default:
                        value = self.default
            except (EOFError, OSError):
                value = self.default or ""
            
            if self._validate_input(value):
                ASCIIColors.print(f"  → {value}", color=answer_color)
                return value
            
            ASCIIColors.print("  ✗ Invalid input, please try again.", color=ANSI.color_red)


class Password(Text):
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
            ASCIIColors.print(f"{self.message}: ", color=color, end="", flush=True)
            value = self._get_password()
            
            if not value and self.default:
                value = self.default
            
            if not self._validate_input(value):
                ASCIIColors.print("  ✗ Invalid input, please try again.", color=ANSI.color_red)
                continue
            
            if self.confirm:
                ASCIIColors.print(f"{self.confirm_message}: ", color=color, end="", flush=True)
                confirm_value = self._get_password()
                if value != confirm_value:
                    ASCIIColors.print("  ✗ Passwords do not match.", color=ANSI.color_red)
                    continue
            
            ASCIIColors.print("  → " + "*" * min(len(value), 8), color=ANSI.style_dim)
            return value


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
            ASCIIColors.print(f"{self.message} {suffix}? ", color=color, end="", flush=True)
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
        menu = Menu(self.message, mode='return', clear_screen_on_run=False, key_source=self._key_source)
        
        for choice in self.choices:
            if choice['disabled']:
                menu.items.append(MenuItem(choice['name'], 'action', None, disabled=True))
            else:
                menu.add_choice(choice['name'], value=choice['value'])
        
        # Set initial selection
        menu._sel_idx = 0
        while menu._sel_idx < len(menu.items) and menu.items[menu._sel_idx].disabled:
            menu._sel_idx += 1
        
        return menu.run()


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
        # Build menu with injected key source
        menu = Menu(self.message, mode='checkbox', clear_screen_on_run=False, 
                   min_selected=self.min_selected, key_source=self._key_source)
        
        for choice in self.choices:
            menu.add_checkbox(choice['name'], value=choice['value'], 
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


class Autocomplete(Text):
    """Text input with autocomplete suggestions."""
    def __init__(self, message: str, choices: List[str], default: str = "",
                 validate: Optional[Union[Callable[[str], bool], Validator]] = None,
                 style: Optional[Dict[str, str]] = None, **kwargs):
        super().__init__(message, default, validate, style, **kwargs)
        self.choices = choices
        self.ignore_case = kwargs.get('ignore_case', True)
        self.match_middle = kwargs.get('match_middle', False)
        self.max_suggestions = kwargs.get('max_suggestions', 5)
    
    def _ask_internal(self) -> str:
        q_color = self.style.get('question', ANSI.color_bright_yellow)
        sug_color = self.style.get('suggestion', ANSI.style_dim)
        
        ASCIIColors.print(f"{self.message}: ", color=q_color, end="", flush=True)
        
        buffer = list(self.default) if self.default else []
        cursor_pos = len(buffer)
        
        while True:
            current = ''.join(buffer)
            matches = self._get_matches(current)
            
            # Clear and redraw
            print(f"\r\033[K{q_color}{self.message}: {ANSI.color_reset}", end="")
            print(current, end="")
            
            if matches and current:
                print(f" {sug_color}(suggestions: {', '.join(matches[:self.max_suggestions])}){ANSI.color_reset}", end="")
            
            print(f"\r\033[{len(self.message) + 2 + cursor_pos}C", end="", flush=True)
            
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


class Form:
    """Group of questions to ask in sequence."""
    def __init__(self, questions: List[Question]):
        self.questions = questions
    
    def ask(self, patch_stdout: bool = False, kbi_msg: str = "Cancelled by user") -> Dict[str, Any]:
        """Ask all questions and return answers dict."""
        answers: Dict[str, Any] = {}
        try:
            for q in self.questions:
                q._answers = answers
                answer = q.ask(patch_stdout=patch_stdout, kbi_msg=kbi_msg)
                if answer is None and isinstance(q, Confirm) and q.default is False:
                    return answers
                key = getattr(q, 'name', None) or q.message
                answers[key] = answer
            return answers
        except KeyboardInterrupt:
            print(f"\n{kbi_msg}")
            return answers


# Convenience function API (matches questionary exactly)

def text(message: str, default: str = "", 
         validate: Optional[Union[Callable[[str], bool], Validator]] = None,
         style: Optional[Dict[str, str]] = None, **kwargs) -> Text:
    """Create a text input question."""
    return Text(message, default, validate, style, **kwargs)


def password(message: str, default: str = "",
             validate: Optional[Union[Callable[[str], bool], Validator]] = None,
             style: Optional[Dict[str, str]] = None, **kwargs) -> Password:
    """Create a password input question."""
    return Password(message, default, validate, style, **kwargs)


def confirm(message: str, default: bool = True,
            style: Optional[Dict[str, str]] = None, **kwargs) -> Confirm:
    """Create a yes/no confirmation question."""
    return Confirm(message, default, style, **kwargs)


def select(message: str, choices: List[Union[str, Dict[str, Any]]],
           default: Optional[Union[str, int]] = None,
           style: Optional[Dict[str, str]] = None, **kwargs) -> Select:
    """Create a single-select question."""
    return Select(message, choices, default, style, **kwargs)


def checkbox(message: str, choices: List[Union[str, Dict[str, Any]]],
             default: Optional[List[Union[str, int]]] = None,
             style: Optional[Dict[str, str]] = None, **kwargs) -> Checkbox:
    """Create a multi-select checkbox question."""
    return Checkbox(message, choices, default, style, **kwargs)


def autocomplete(message: str, choices: List[str], default: str = "",
                 validate: Optional[Union[Callable[[str], bool], Validator]] = None,
                 style: Optional[Dict[str, str]] = None, **kwargs) -> Autocomplete:
    """Create an autocomplete text input question."""
    return Autocomplete(message, choices, default, validate, style, **kwargs)


def form(*questions: Question) -> Form:
    """Create a form from multiple questions."""
    return Form(list(questions))


# Aliases for exact compatibility
ask = Form  # questionary.ask() is an alias for Form
