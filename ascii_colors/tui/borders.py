# -*- coding: utf-8 -*-
"""
Border character presets for TUI widgets.

Use named presets with any bordered widget::

    Box(title="Panel", border="rounded")
    Box(title="Panel", border="double")

Or pass a custom mapping with the same keys::

    Box(chars={"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"})
"""

from typing import Dict, Optional, Union

BORDERS: Dict[str, Dict[str, str]] = {
    "none":   {"tl": "", "tr": "", "bl": "", "br": "", "h": "", "v": ""},
    "simple": {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"},
    "rounded": {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"},
    "heavy":   {"tl": "┏", "tr": "┓", "bl": "┗", "br": "┛", "h": "━", "v": "┃"},
    "double":  {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║"},
    "ascii":   {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|"},
    "dots":    {"tl": "·", "tr": "·", "bl": "·", "br": "·", "h": "·", "v": "·"},
    "block":   {"tl": "▛", "tr": "▜", "bl": "▙", "br": "▟", "h": "▀", "v": "▌"},
}

BorderSpec = Union[str, Dict[str, str], None]


def get_border(spec: BorderSpec = None) -> Dict[str, str]:
    """Return a fresh dict of border characters for ``spec``."""
    if spec is None:
        return dict(BORDERS["simple"])
    if isinstance(spec, dict):
        base = dict(BORDERS["simple"])
        base.update(spec)
        return base
    return dict(BORDERS.get(spec, BORDERS["simple"]))