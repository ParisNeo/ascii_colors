# -*- coding: utf-8 -*-
"""
Form (sequence of questions) for questionary compatibility.
"""

from typing import Any, Dict, List
from ascii_colors.questionary.base import Question
from ascii_colors.questionary.confirm import Confirm


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
                # Strip rich markup from key for cleaner output
                from ascii_colors.core import ASCIIColors
                key = ASCIIColors._apply_rich_markup(key)
                from ascii_colors.utils import strip_ansi
                key = strip_ansi(key)
                answers[key] = answer
            return answers
        except KeyboardInterrupt:
            print(f"\n{kbi_msg}")
            return answers


def form(*questions: Question) -> Form:
    """Create a form from multiple questions."""
    return Form(list(questions))


# Aliases for exact compatibility
ask = Form  # questionary.ask() is an alias for Form
