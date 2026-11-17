# -*- coding: utf-8 -*-
"""HERMES-AGENT — responsive ASCII-art and mouse-driven TUI demo.

Run from the repository root::

    python examples/tui/tui_agent_demo.py

Move the pointer to see live coordinates, click tools/skills/buttons, and use
the wheel over either list. The layout shrinks without overlap on small
terminals; the large banner falls back to a one-line title when necessary.
"""

import sys

from ascii_colors.tui import (
    App,
    AsciiArt,
    BigText,
    Box,
    Button,
    Checkbox,
    Divider,
    HBox,
    Label,
    ListBox,
    MouseEvent,
    Spinner,
    StatusBar,
    VBox,
)


LOGO = AsciiArt(
    [
        "       ▄▄█████▄▄       ",
        "     ▄███████████▄     ",
        "    ███▀███████▀███    ",
        "   ███  █▀███▀█  ███   ",
        "   ███  █ ███ █  ███   ",
        "   ███▄  ▀▀▀▀▀  ▄███   ",
        "    ▀█████████████▀    ",
        "      ▀██▀   ▀██▀      ",
        "       ██     ██       ",
    ],
    style="bright_cyan",
    char_styles={"▀": "cyan", "▄": "cyan"},
    valign="center",
)

TOOLS = {
    "browser": "back · click · screenshot · navigate",
    "clarify": "Ask a focused clarifying question",
    "code": "Execute code in an isolated runtime",
    "cronjob": "Schedule a recurring task",
    "delegate": "Spawn a scoped sub-agent",
    "file": "patch · read · search · write",
    "home": "call_service · get_state · entities",
    "image": "Generate an image from a prompt",
    "memory": "Store and recall long-term facts",
    "search": "Query the live web",
}

SKILLS = {
    "agents": "claude-code · codex · hermes · opencode",
    "creative": "ascii-art · ascii-video · excalidraw",
    "data": "jupyter-live-kernel",
    "devops": "webhook-subscriptions",
    "email": "himalaya",
    "gaming": "minecraft · pokemon-player",
    "github": "inspection · auth · code-review",
    "leisure": "find-nearby",
}


def build_demo():
    details = Label(
        "[dim]Click a tool or skill. Wheel over a list to scroll.[/dim]",
        wrap=True,
    )
    status = StatusBar(
        left="[dim]Click · wheel · Tab · Esc[/dim]",
        right="[bright_black]pointer: —[/bright_black]",
    )
    clicks = [0]

    def show(kind: str, name: str, description: str) -> None:
        details.text = (
            f"[bold bright_yellow]{kind}[/bold bright_yellow] "
            f"[bold bright_white]{name}[/bold bright_white]\n"
            f"[bright_white]{description}[/bright_white]"
        )

    def clicked() -> None:
        clicks[0] += 1
        details.text = (
            f"[bold bright_green]Button press #{clicks[0]}[/bold bright_green]\n"
            "[dim]The press was captured and dispatched on the UI thread.[/dim]"
        )

    def verbose_changed(enabled: bool) -> None:
        details.text = f"[dim]Verbose events: {'on' if enabled else 'off'}[/dim]"

    tools = ListBox(
        list(TOOLS),
        on_select=lambda name, _: show("Tool", name, TOOLS[name]),
    )
    skills = ListBox(
        list(SKILLS),
        on_select=lambda name, _: show("Skill", name, SKILLS[name]),
    )

    banner = BigText(
        "HERMES-AGENT",
        shadow=True,
        style="[bold bright_yellow]",
        shadow_style="red",
    )

    agent_info = Label(
        "[bold bright_yellow]gpt-5.4[/bold bright_yellow] "
        "[bright_white]Nous Research[/bright_white]\n"
        "[bright_cyan]/home/brlan[/bright_cyan]\n"
        "[bright_black]20260418_120319_750246[/bright_black]",
        wrap=True,
    )
    agent_info.min_height = 3

    left = VBox(gap=0)
    left.add(LOGO)
    left.add(Divider(char="·", style="bright_black"))
    left.add(agent_info)
    left.min_width = 23
    left.flex = 0

    tools_box = Box(
        title=" Tools ", border="rounded", border_style="bright_cyan", padding=0
    )
    tools_box.add(tools)
    skills_box = Box(
        title=" Skills ", border="rounded", border_style="bright_magenta", padding=0
    )
    skills_box.add(skills)

    lists = HBox(gap=1)
    lists.add(tools_box)
    lists.add(skills_box)
    lists.min_height = 7
    lists.flex = 2

    details_box = Box(
        title=" Inspector ", border="rounded", border_style="bright_yellow", padding=0
    )
    details_box.add(details)
    details_box.min_height = 4
    details_box.flex = 1

    right = VBox(gap=1)
    right.add(lists)
    right.add(details_box)

    content = HBox(gap=1)
    content.add(left)
    content.add(right)

    controls = HBox(gap=1)
    controls.add(Button("Click me", on_press=clicked))
    controls.add(Checkbox("verbose events", on_change=verbose_changed))
    controls.add(Spinner(label="[bright_black]ready[/bright_black]", interval=0.12))
    controls.min_height = 1
    controls.flex = 0

    body = VBox(gap=0, pad=1)
    body.add(banner)
    body.add(Divider(char="═", style="yellow"))
    body.add(content)
    body.add(controls)
    body.add(status)

    frame = Box(border="rounded", border_style="yellow", padding=0)
    frame.add(body)
    return frame, status


def main() -> int:
    root, status = build_demo()
    app = App(fps=30.0, mouse=True)
    app.set_root(root)

    def pointer_moved(event: MouseEvent) -> None:
        status.right = (
            f"[bright_black]pointer {event.x:03d},{event.y:03d} · "
            f"{event.action}[/bright_black]"
        )

    app.on_mouse = pointer_moved
    try:
        app.run()
    except RuntimeError as exc:
        print(f"tui_agent_demo: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())