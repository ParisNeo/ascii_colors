import time
import random
from ascii_colors import ASCIIColors, rich
from ascii_colors.rich import Panel

# We use a helper function to create our panel based on current state
def create_status_panel(step, total, message):
    progress = int((step / total) * 20)
    bar = f"[green]{'█' * progress}[/green]{'░' * (20 - progress)}"
    
    content = f"Task: {message}\nProgress: [{bar}] {step}/{total}"
    
    return Panel(
        content,
        title="[bold cyan]System Monitor[/bold cyan]",
        border_style="blue",
        padding=(1, 2),
        width=50
    )

# 1. Start with an initial display
total_steps = 20
with ASCIIColors.live(create_status_panel(0, total_steps, "Initializing...")) as live:
    for i in range(1, total_steps + 1):
        time.sleep(0.3)
        
        # 2. Update the live display with a FRESH panel instance
        msg = "Processing Data..." if i < 15 else "Finalizing..."
        live.update(create_status_panel(i, total_steps, msg))

    # 3. Final update for completion
    live.update(Panel(
        "[bold green]✓ Operation Successful![/bold green]",
        title="[bold cyan]System Monitor[/bold cyan]",
        border_style="green",
        width=50
    ))