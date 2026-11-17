# -*- coding: utf-8 -*-
"""
Demo: Curses-style System Monitor Dashboard.

Showcases the extended TUI widget set: BigValue KPI tiles, Sparkline,
BarChart, Table, Spinner, Tabs and StatusBar.

Run:
    python examples/tui/tui_dashboard_demo.py

Controls:
    Left/Right    switch tabs
    Up/Down       navigate lists
    Tab           cycle focus
    Esc / Ctrl+Q  quit
"""

from ascii_colors.tui import (
    App,
    BarChart,
    BigValue,
    Box,
    HBox,
    Label,
    ListBox,
    Sparkline,
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
    ["[000] startup: service loaded and initialised"]
    + [f"[{i:03d}] event: task scheduled for next cycle" for i in range(40, 80, 2)]
    + [f"[{i:03d}] warning: retry in progress" for i in range(80, 120, 5)]
)

# Snapshot data backing the CPU tile and the two charts.
CPU_HISTORY = [18, 24, 21, 30, 42, 37, 45, 52, 48, 61, 55, 42, 58, 63]
REQUESTS = [124, 89, 176, 143, 210, 168, 195]
HOURS = ["00", "04", "08", "12", "16", "20", "24"]


def _build_header() -> HBox:
    """Application title with an animated live indicator."""
    spinner = Spinner(
        label="[green]live[/green]",
        frames=Spinner.FRAMES_BLOCK,
        interval=0.08,
    )
    header = HBox(gap=2)
    header.add(Label("[bold cyan]SysMon[/bold cyan]"))
    header.add(spinner)
    header.min_height = 1
    header.flex = 0
    return header


def _build_kpis() -> HBox:
    """Row of dashboard KPI tiles rendered with block-digit ``BigValue``."""
    row = HBox(gap=6)
    row.add(BigValue("42%", label="[dim]CPU[/dim]"))
    row.add(BigValue("68%", label="[dim]MEM[/dim]"))
    row.add(BigValue("55%", label="[dim]DISK[/dim]"))
    row.min_height = 6
    row.flex = 0
    return row


def _build_charts() -> HBox:
    """Side-by-side CPU sparkline and hourly-requests bar chart."""
    spark_body = VBox(gap=0)
    spark_body.add(Sparkline(CPU_HISTORY, style="green"))
    spark_body.add(Label("[dim]avg 44% · peak 63%[/dim]"))

    spark_box = Box(
        title=" CPU ",
        border="rounded",
        border_style="cyan",
        padding=0,
    )
    spark_box.add(spark_body)

    bar_box = Box(
        title=" Requests / hour ",
        border="rounded",
        border_style="magenta",
        padding=0,
    )
    bar_box.add(BarChart(REQUESTS, labels=HOURS, fill_style="magenta"))

    row = HBox(gap=2)
    row.add(spark_box)
    row.add(bar_box)
    row.min_height = 7
    row.flex = 0
    return row


def _build_monitor() -> Box:
    """Tabs holding the live process table and the scrolling event log."""
    processes_table = Table(
        ["Process", "CPU", "Memory", "State"],
        PROCESSES,
        column_aligns=["left", "right", "right", "left"],
    )
    logs_list = ListBox(LOG_LINES)

    tabs = Tabs()
    tabs.add_tab("Processes", processes_table)
    tabs.add_tab("Logs", logs_list)

    box = Box(title=" Monitor ", border_style="cyan", padding=0)
    box.add(tabs)
    box.flex = 1
    return box


def _build_status() -> StatusBar:
    return StatusBar(
        left="[dim]←/→ tab · ↑/↓ navigate · Tab focus · Esc quit[/dim]",
        right="[bold green]● online[/bold green]",
    )


def main() -> None:
    body = VBox(gap=1, pad=1)
    body.add(_build_header())
    body.add(_build_kpis())
    body.add(_build_charts())
    body.add(_build_monitor())
    body.add(_build_status())

    app = App(fps=30.0)
    app.set_root(body)
    app.run()


if __name__ == "__main__":
    main()