"""
Demo: Curses-style System Monitor Dashboard.

Showcases the extended TUI widget set:
    Table, Spinner, Tabs, ScrollView, StatusBar, ProgressBar.

Run:
    python examples/tui_dashboard_demo.py

Controls:
    Left/Right   switch tabs
    Up/Down      navigate lists
    Tab          cycle focus
    Esc / Ctrl+Q quit
"""

from ascii_colors.tui import (
    App,
    Box,
    HBox,
    Label,
    ListBox,
    ProgressBar,
    Spinner,
    StatusBar,
    Table,
    Tabs,
    VBox,
)

PROCESSES = [
    ["chrome.exe", "12.4%", "890 MB", "running"],
    ["python.exe", "3.1%", "120 MB", "running"],
    ["code.exe", "1.8%", "512 MB", "running"],
    ["firefox.exe", "8.9%", "1024 MB", "running"],
    ["docker", "0.2%", "45 MB", "stopped"],
    ["powershell", "0.1%", "80 MB", "running"],
    ["explorer.exe", "0.4%", "210 MB", "running"],
    ["svchost.exe", "0.3%", "150 MB", "running"],
]

LOG_LINES = (
    [f"[{i:03d}] startup: service loaded and initialised"]
    + [f"[{i:03d}] event: task scheduled for next cycle" for i in range(40, 80, 2)]
    + [f"[{i:03d}] warning: retry in progress" for i in range(80, 120, 5)]
)


def main() -> None:
    processes_table = Table(
        ["Process", "CPU", "Memory", "State"],
        PROCESSES,
        column_aligns=["left", "right", "right", "left"],
    )
    logs_list = ListBox(LOG_LINES)

    tabs = Tabs()
    tabs.add_tab("Processes", processes_table)
    tabs.add_tab("Logs", logs_list)

    monitor_box = Box(title=" Monitor ", border_style="cyan", padding=0)
    monitor_box.add(tabs)

    spinner = Spinner(label="[green]live[/green]", frames=Spinner.FRAMES_BLOCK, interval=0.08)

    header = HBox(gap=2)
    header.add(Label("[bold cyan]SysMon[/bold cyan]"))
    header.add(spinner)
    header.min_height = 1
    header.flex = 0

    metrics = HBox(gap=2)
    metrics.add(Label("CPU"))
    metrics.add(ProgressBar(value=42))
    metrics.add(Label("MEM"))
    metrics.add(ProgressBar(value=68, bar_char="▓", empty_char="░"))
    metrics.min_height = 1
    metrics.flex = 0

    status = StatusBar(
        left="[dim]←/→ tab · ↑/↓ navigate · Tab focus · Esc quit[/dim]",
        right="[bold green]● online[/bold green]",
    )

    body = VBox(gap=1, pad=1)
    body.add(header)
    body.add(metrics)
    body.add(monitor_box)
    body.add(status)

    App(fps=30.0).run() if False else _run(body)


def _run(root) -> None:
    app = App(fps=30.0)
    app.set_root(root)
    app.run()


if __name__ == "__main__":
    main()