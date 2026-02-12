# -*- coding: utf-8 -*-
"""
Tree component for rich compatibility.
"""

from typing import Iterator, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ascii_colors.rich.console import Console, ConsoleOptions

from ascii_colors.constants import ANSI
from ascii_colors.rich.style import Style
from ascii_colors.rich.text import Text, Renderable


class Tree(Renderable):
    """A tree structure for display."""
    
    def __init__(
        self,
        label: Union[str, Text, Renderable],
        *,
        style: Optional[Union[str, Style]] = None,
        guide_style: Optional[Union[str, Style]] = None,
        expanded: bool = True,
        highlight: bool = False,
    ):
        self.label = label if isinstance(label, (Text, Renderable)) else Text(label)
        self.style = style if isinstance(style, Style) else (Style.parse(style) if style else None)
        self.guide_style = guide_style if isinstance(guide_style, Style) else (Style.parse(guide_style) if guide_style else Style(dim=True))
        self.expanded = expanded
        self.highlight = highlight
        self.children: List[Tree] = []
    
    def add(
        self,
        label: Union[str, Text, "Tree"],
        *,
        style: Optional[Union[str, Style]] = None,
    ) -> "Tree":
        """Add a child node."""
        if isinstance(label, Tree):
            child = label
        else:
            if isinstance(label, Text):
                child = Tree(label, style=style or self.style)
            else:
                child = Tree(str(label), style=style or self.style)
        self.children.append(child)
        return child
    
    def add_node(self, label: Union[str, Text]) -> "Tree":
        """Add a child node and return it for chaining."""
        if isinstance(label, Text):
            child = Tree(label, style=self.style)
        else:
            child = Tree(str(label), style=self.style)
        self.children.append(child)
        return child
    
    def __rich_console__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> Iterator[Union[str, Renderable]]:
        style_ansi = str(self.style) if self.style else ""
        guide_ansi = str(self.guide_style) if self.guide_style else ""
        reset = ANSI.color_reset
        
        if isinstance(self.label, str):
            label_str = self.label
        elif isinstance(self.label, Text):
            label_str = self.label.plain if isinstance(self.label.plain, str) else str(self.label.plain)
        else:
            try:
                rendered = list(console.render(self.label, options))
                label_str = rendered[0] if rendered else str(self.label)
            except:
                label_str = str(self.label)
        
        yield f"{style_ansi}{label_str}{reset}"
        
        for i, child in enumerate(self.children):
            is_last = i == len(self.children) - 1
            
            if is_last:
                branch = "└── "
                guide = "    "
            else:
                branch = "├── "
                guide = "│   "
            
            child_lines = list(console.render(child, options))
            
            for j, line in enumerate(child_lines):
                if j == 0:
                    yield f"{guide_ansi}{branch}{reset}{line}"
                else:
                    yield f"{guide_ansi}{guide}{reset}{line}"
    
    def __rich_measure__(
        self,
        console: "Console",
        options: "ConsoleOptions",
    ) -> "Measurement":
        from ascii_colors.rich.console import Measurement
        return Measurement(10, options.max_width)
