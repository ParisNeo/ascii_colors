"""
Demo: Curses-style Task Manager built with the ascii_colors TUI framework.

Run:
    python examples/tui/tui_demo.py

Controls:
    Tab          cycle focus between list / input / buttons
    Up/Down      navigate the task list
    Enter        toggle task (when list is focused)
    Esc          quit
"""

from ascii_colors.tui import (
    App,
    Box,
    Button,
    HBox,
    Label,
    ListBox,
    ProgressBar,
    TextInput,
    VBox,
)


TASKS = [
    "Buy groceries",
    "Finish the quarterly report",
    "Call the dentist",
    "Review pull requests",
    "Write tests for the TUI framework",
]


def main() -> None:
    title = Label("[bold cyan]📋  Task Manager[/bold cyan]", align="center")
    hint = Label("[dim]Tab cycle · ↑/↓ move · Enter toggle · Esc quit[/dim]", align="center")

    task_list = ListBox(TASKS)

    task_input = TextInput(placeholder="Type a new task and press Enter…")
    add_button = Button("Add", on_press=lambda: _add_task(task_input, task_list))

    input_row = HBox(gap=1)
    input_row.add(task_input)
    input_row.add(add_button)
    input_row.min_height = 1
    input_row.flex = 0

    progress = ProgressBar(value=_completion(task_list.items))

    def _add_task(inp: TextInput, lst: ListBox) -> None:
        text = inp.value.strip()
        if not text:
            return
        lst.items.append(text)
        inp.value = ""
        inp.cursor = 0
        progress.value = _completion(lst.items)

    def _on_select(item: str, idx: int) -> None:
        current = task_list.items[idx]
        if current.startswith("✔ "):
            task_list.items[idx] = current[2:]
        else:
            task_list.items[idx] = "✔ " + current
        progress.value = _completion(task_list.items)

    task_list.on_select = _on_select

    list_box = Box(title=" Tasks ", border_style="cyan", padding=1)
    list_box.add(task_list)

    body = VBox(gap=1, pad=1)
    body.add(title)
    body.add(hint)
    body.add(list_box)
    body.add(input_row)
    body.add(progress)

    app = App(fps=20.0)
    app.set_root(body)
    app.run()


def _completion(items) -> float:
    if not items:
        return 0.0
    done = sum(1 for t in items if t.startswith("✔ "))
    return 100.0 * done / len(items)


if __name__ == "__main__":
    main()