"""
Demo: Graphics showcase — Sparkline, BarChart, BigValue, Divider, borders.

Run:
    python examples/tui/tui_charts_demo.py

Controls:
    Esc / Ctrl+Q   quit
"""

import math
import time

from ascii_colors.tui import (
    App,
    BarChart,
    BigValue,
    Box,
    Divider,
    HBox,
    Label,
    Sparkline,
    Spinner,
    StatusBar,
    VBox,
)

# ------------------------------------------------------------------ sample data
SALES = [124, 89, 176, 143, 210, 155, 98, 187, 224, 165, 132, 201]
QTRS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _wave(n: int) -> list:
    """A slowly oscillating series for the live sparkline."""
    t = time.time()
    return [50 + 40 * math.sin(t + i * 0.4) for i in range(n)]


class LiveDemo(VBox):
    """A VBox that recomputes its sparkline every draw."""

    def __init__(self):
        super().__init__(gap=1, pad=1)
        self.spark_lbl = Label("[bold cyan]Throughput (live)[/bold cyan]")
        self.spark = Sparkline(_wave(40), min_value=0, max_value=100)
        self.spark.min_height = 1
        self.spark.flex = 0
        self.add(self.spark_lbl)
        self.add(self.spark)

    def draw(self, buffer):
        # refresh the data before drawing
        self.spark.values = _wave(40)
        super().draw(buffer)


def main() -> None:
    # KPI tiles ---------------------------------------------------------
    total = BigValue(int(sum(SALES)), label="[dim]Total units[/dim]")
    peak = BigValue(int(max(SALES)), label="[dim]Peak month[/dim]")
    avg = BigValue(int(sum(SALES) / len(SALES)), label="[dim]Average[/dim]")

    kpis = HBox(gap=2)
    kpis.add(total)
    kpis.add(peak)
    kpis.add(avg)
    kpis.min_height = 6
    kpis.flex = 0

    # Chart panel -------------------------------------------------------
    chart = BarChart(SALES, labels=QTRS, bar_char="█", gap=1)
    chart.min_height = 8

    chart_box = Box(title=" Monthly Sales ", border="rounded", border_style="cyan", padding=1)
    chart_box.add(chart)

    # Live spark -------------------------------------------------------
    live = LiveDemo()
    live.min_height = 3
    live.flex = 0

    # Assemble ----------------------------------------------------------
    divider = Divider(title="[dim]── overview ──[/dim]", char="─")

    body = VBox(gap=1, pad=1)
    body.add(Label("[bold bright_cyan]▛ Ascii Charts Demo ▜[/bold bright_cyan]", align="center"))
    body.add(divider)
    body.add(kpis)
    body.add(chart_box)
    body.add(live)
    body.add(StatusBar(
        left="[dim]Esc quit[/dim]",
        right="[green]● live[/green]",
    ))

    app = App(fps=15.0)
    app.set_root(body)
    app.run()


if __name__ == "__main__":
    main()