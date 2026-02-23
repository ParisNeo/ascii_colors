#!/usr/bin/env python3
"""
Demonstration of ASCIIColors Live display features.
Shows real-time updating terminal displays with various use cases.
"""

import time
import random
from ascii_colors import ASCIIColors, rich
from ascii_colors.rich import Panel, Table, Text, Style


def demo_simple_live():
    """Basic live display with updating text."""
    print("\n")
    ASCIIColors.yellow("Demo 1: Simple Live Text Update", style=ASCIIColors.style_bold)
    print("=" * 50)
    
    # Create a live display that updates 4 times per second
    with ASCIIColors.live(Text("Starting process...", style="bold")) as live:
        for i in range(10):
            time.sleep(0.3)
            # Update with new content
            progress_bar = "█" * (i + 1) + "░" * (9 - i)
            live.update(Text(
                f"[bold cyan]Progress: [{progress_bar}] {i+1}/10[/bold cyan]",
                style="cyan"
            ))
        
        # Final state
        live.update(Text("[bold green]✓ Complete![/bold green]", style="green"))
        time.sleep(0.5)


def demo_live_with_panel():
    """Live display inside a styled panel."""
    print("\n")
    ASCIIColors.yellow("Demo 2: Live Panel with Dynamic Content", style=ASCIIColors.style_bold)
    print("=" * 50)
    
    def create_status_panel(step, total, message, status):
        """Create a panel with current status."""
        progress = int((step / total) * 20)
        bar = f"[green]{'█' * progress}[/green][dim]{'░' * (20 - progress)}[/dim]"
        
        content = (
            f"[bold]{message}[/bold]\n\n"
            f"Status: [{status}]\n"
            f"Progress: [{bar}] {step}/{total}\n"
            f"Time: {time.strftime('%H:%M:%S')}"
        )
        
        return Panel(
            content,
            title="[bold cyan]🖥️ System Monitor[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
            box="round"
        )
    
    statuses = ["[yellow]Initializing[/yellow]", "[blue]Processing[/blue]", 
                "[magenta]Optimizing[/magenta]", "[green]Finalizing[/green]"]
    
    with ASCIIColors.live(create_status_panel(0, 20, "Booting...", statuses[0])) as live:
        for i in range(1, 21):
            time.sleep(0.15)
            status_idx = min(i // 6, len(statuses) - 1)
            live.update(create_status_panel(
                i, 20, 
                f"Task: Data Processing", 
                statuses[status_idx]
            ))
        
        # Success state
        live.update(Panel(
            "[bold green]✓ All tasks completed successfully![/bold green]",
            title="[bold cyan]🖥️ System Monitor[/bold cyan]",
            border_style="green",
            padding=(1, 2),
            box="round"
        ))
        time.sleep(1)


def demo_live_table():
    """Live display with updating table data."""
    print("\n")
    ASCIIColors.yellow("Demo 3: Live Updating Table", style=ASCIIColors.style_bold)
    print("=" * 50)
    
    def create_metrics_table():
        """Create a table with simulated metrics."""
        table = Table(
            "Service", "Status", "CPU %", "Memory", "Latency",
            title="[bold]Live System Metrics[/bold]",
            header_style="bold cyan",
            box="round"
        )
        
        services = [
            ("API Gateway", random.choice(["[green]● Healthy[/green]", "[yellow]● Degraded[/yellow]"])),
            ("Database", "[green]● Healthy[/green]"),
            ("Cache", "[green]● Healthy[/green]"),
            ("Queue", random.choice(["[green]● Healthy[/green]", "[red]● Critical[/red]"])),
            ("Worker", "[green]● Healthy[/green]"),
        ]
        
        for service, status in services:
            cpu = random.randint(10, 95)
            memory = f"{random.randint(100, 800)}MB"
            latency = f"{random.randint(5, 200)}ms"
            
            cpu_color = "green" if cpu < 50 else "yellow" if cpu < 80 else "red"
            
            table.add_row(
                service,
                status,
                f"[{cpu_color}]{cpu}%[/{cpu_color}]",
                memory,
                latency
            )
        
        return table
    
    with ASCIIColors.live(create_metrics_table(), refresh_per_second=2) as live:
        for _ in range(15):
            time.sleep(0.5)
            live.update(create_metrics_table())


def demo_combined_live():
    """Complex dashboard with multiple elements."""
    print("\n")
    ASCIIColors.yellow("Demo 4: Combined Live Dashboard", style=ASCIIColors.style_bold)
    print("=" * 50)
    
    from ascii_colors.rich import Columns
    
    def create_dashboard(phase, progress, logs):
        """Build a multi-panel dashboard layout."""
        # Status panel
        phase_colors = {
            "Initializing": "yellow",
            "Processing": "blue", 
            "Optimizing": "magenta",
            "Finalizing": "cyan",
            "Complete": "green"
        }
        phase_color = phase_colors.get(phase, "white")
        
        status_panel = Panel(
            f"[bold {phase_color}]{phase}[/bold {phase_color}]",
            title="[bold]Phase[/bold]",
            border_style=phase_color,
            width=30,
            padding=(1, 1)
        )
        
        # Progress panel
        bar_width = 20
        filled = int((progress / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        progress_panel = Panel(
            f"[bold][{bar}][/bold] {progress}%",
            title="[bold]Progress[/bold]",
            border_style="cyan",
            width=30,
            padding=(1, 1)
        )
        
        # Recent logs panel
        log_lines = logs[-4:] if logs else ["Waiting to start..."]
        log_content = "\n".join([
            f"[dim]{i+1}.[/dim] {log}" 
            for i, log in enumerate(log_lines)
        ])
        logs_panel = Panel(
            log_content,
            title="[bold]Recent Logs[/bold]",
            border_style="dim",
            padding=(1, 1),
            height=6
        )


def main():
    """Run all live display demos."""
    # Welcome banner
    ASCIIColors.rich_print(
        "[bold green]╔══════════════════════════════════════════════════════╗[/bold green]\n"
        "[bold green]║  [bold white]ASCIIColors Live Display Demo Suite[/bold white]                 ║[/bold green]\n"
        "[bold green]║  [dim]Real-time updating terminal displays[/dim]                ║[/bold green]\n"
        "[bold green]╚══════════════════════════════════════════════════════╝[/bold green]"
    )
    
    ASCIIColors.print("\nThis demo showcases ASCIIColors.live() for dynamic terminal updates.")
    ASCIIColors.print("Perfect for progress bars, dashboards, and real-time data displays.\n")
    
    input("Press Enter to start the demos...")
    
    # Run all demos
    try:
        demo_simple_live()
        input("\nPress Enter to continue...")
        
        demo_live_with_panel()
        input("\nPress Enter to continue...")
        
        demo_live_table()
        input("\nPress Enter to continue...")
        
        demo_combined_live()
        input("\nPress Enter to continue...")
        with ASCIIColors.status("doing it"):
            time.sleep(1)

        
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        return
    
    # Farewell
    print("\n")
    ASCIIColors.rule("All Demos Complete", style="bold green")
    ASCIIColors.rich_print("[bold green]✓ Live display demonstrations finished![/bold green]")


if __name__ == "__main__":
    main()