# -*- coding: utf-8 -*-
"""
Base classes for questionary-compatible interactive prompts.
"""

import sys
from typing import Any, Callable, Dict, Iterator, Optional, Union
from ascii_colors.constants import ANSI
from ascii_colors.core import ASCIIColors
from ascii_colors.utils import _get_key


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
