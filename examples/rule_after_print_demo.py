# -*- coding: utf-8 -*-
"""Demo: rules always start on a fresh line.

Demonstrates that ``Console.rule()`` detects when the terminal cursor is
mid-line (e.g. after ``console.print(..., end="")``) and prepends a newline
so the horizontal rule is never glued onto the preceding text.

Without the fix, the output of Case 2 would look like::

    Loading modules:─────────────────────────────────────────

With the fix, it looks like::

    Loading modules:
    ─────────────────────────────────────────────────────────

Run:
    python examples/rule_after_print_demo.py
"""

from ascii_colors.rich.console import Console

_WIDTH = 60


def main() -> None:
    console = Console(force_terminal=True, force_width=_WIDTH)

    # ---------------------------------------------------------------------- 1
    # Baseline: a rule emitted while the cursor is already at column 0.
    console.print("[bold cyan]Case 1 — rule at line start (normal)[/bold cyan]")
    console.rule("Section A")
    console.print()

    # ---------------------------------------------------------------------- 2
    # Rule emitted immediately after a ``print(end="")`` — must NOT be glued
    # to the tail of "Loading modules:".
    console.print("[bold cyan]Case 2 — rule after print(end='')[/bold cyan]")
    console.print("Loading modules:", end="")
    console.rule()
    console.print()

    # ---------------------------------------------------------------------- 3
    # Titled rule after a mid-line write. The title must land on its own line.
    console.print("[bold cyan]Case 3 — titled rule after print(end='')[/bold cyan]")
    console.print("Initialization", end="")
    console.rule("Done", style="green")
    console.print()

    # ---------------------------------------------------------------------- 4
    # Custom rule characters ("═") are detected as a Rule / Divider too.
    console.print("[bold cyan]Case 4 — custom character rule[/bold cyan]")
    console.print("Building...", end="")
    console.rule(characters="═", style="magenta")
    console.print()

    # ---------------------------------------------------------------------- 5
    # Several mid-line writes interleaved with rules — each rule starts fresh.
    console.print("[bold cyan]Case 5 — interleaved print(end='') / rule()[/bold cyan]")
    console.print("Step 1", end="")
    console.rule()
    console.print("Step 2", end="")
    console.rule("Complete", align="right", style="yellow")

    # ---------------------------------------------------------------------- 6
    # Sanity check: the same mid-line behaviour applies to the ``Rule``
    # renderable when it is passed to ``console.print(Rule())``.
    from ascii_colors.rich.layout import Rule

    console.print()
    console.print("[bold cyan]Case 6 — Rule() renderable after print(end='')[/bold cyan]")
    console.print("Rendering", end="")
    console.print(Rule("Finish", characters="─", style="bright_cyan"))


if __name__ == "__main__":
    main()