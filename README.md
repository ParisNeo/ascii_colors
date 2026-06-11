# ASCIIColors 🎨 Rich Terminal Output Made Simple

[![PyPI version](https://img.shields.io/pypi/v/ascii_colors.svg)](https://pypi.org/project/ascii-colors/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/ascii_colors.svg)](https://pypi.org/project/ascii-colors/)
[![PyPI license](https://img.shields.io/pypi/l/ascii_colors.svg)](https://github.com/ParisNeo/ascii_colors/blob/main/LICENSE)
[![PyPI downloads](https://img.shields.io/pypi/dm/ascii_colors.svg)](https://pypi.org/project/ascii-colors/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **One library. Colors. Logging. Progress. Menus. Prompts. Panels. Tables. Done.**

Stop wrestling with multiple CLI libraries. **ASCIIColors** unifies everything you need for modern terminal applications into a single, elegant toolkit — from quick colored output to production-grade logging, interactive menus, smart prompts, and rich UI components.

| 🎨 **Colors & Styles** | 🪵 **Logging System** | 📊 **Progress Bars** |
|:---|:---|:---|
| 256-color support, bright variants, backgrounds, bold/italic/underline/blink | Full `logging` compatibility, **per-logger file routing for AI debugging**, JSON output, rotation, contextual logging | `tqdm`-like bars with custom styles (fill, blocks, line, emoji), thread-safe |

| 🖥️ **Rich Components** | ❓ **Smart Prompts** | 🛠️ **Utilities** |
|:---|:---|:---|
| Panels, tables, trees, syntax highlighting, live displays, markdown | Drop-in `questionary` replacement: text, password, confirm, select, checkbox, autocomplete | Spinners, syntax highlighting, enhanced tracebacks with locals, multicolor text, confirm/prompt helpers |

---

## 📦 Installation

```bash
pip install ascii_colors
```

**Optional dependencies:**

```bash
# For accurate emoji/wide-character support in progress bars
pip install ascii_colors[wcwidth]  # or: pip install wcwidth

# For development
pip install ascii_colors[dev]
```

**Requirements:** Python 3.8+

---

## 🚀 Quick Start

### Choose Your API

ASCIIColors offers **three complementary approaches** that work seamlessly together:

| Approach | Best For | API Style |
|:---|:---|:---|
| **Direct Print** | Immediate visual feedback, status messages, user interaction | `ASCIIColors.green("text")` |
| **Logging System** | Structured application logs, filtering, multiple outputs | `import ascii_colors as logging` |
| **Rich Components** | Beautiful UI: panels, tables, trees, syntax highlighting | `ASCIIColors.panel()` or `ASCIIColors.rich_print()` |

### 1. Direct Print — Instant Visual Feedback

Perfect for CLI tools, status messages, and user-facing output:

```python
from ascii_colors import ASCIIColors

# Simple color methods — print immediately to terminal
ASCIIColors.red("Error: Connection failed")
ASCIIColors.green("✓ Success!")
ASCIIColors.yellow("Warning: Low memory", style=ASCIIColors.style_bold)
ASCIIColors.blue("Info: Processing item 42")

# Full control with .print()
ASCIIColors.print(
    " CRITICAL ALERT ",
    color=ASCIIColors.color_black,
    background=ASCIIColors.color_bg_red,
    style=ASCIIColors.style_bold + ASCIIColors.style_blink
)

# Rich markup for inline styling
ASCIIColors.rich_print("[bold red]Error:[/bold red] [yellow]Something went wrong[/yellow]")
```

### 2. Logging System — Production-Grade Structured Logging

Full compatibility with Python's standard `logging` module:

```python
import sys
import ascii_colors as logging  # Familiar alias for drop-in replacement!

# Configure once at application startup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)

# Add multiple outputs with different formats
json_handler = logging.FileHandler("app.jsonl", mode='a')
json_handler.setFormatter(logging.JSONFormatter(
    include_fields=["timestamp", "levelname", "name", "message", "pathname", "lineno"]
))
json_handler.setLevel(logging.WARNING)
logging.getLogger().addHandler(json_handler)

# Use throughout your application
logger = logging.getLogger("MyService")
logger.info("Service started on port %d", 8080)
logger.warning("Disk usage at %d%%", 85)
logger.error("Failed to connect to database")
```

### 3. Rich Components — Beautiful Terminal UI

Create stunning terminal interfaces with panels, tables, trees, and more:

```python
from ascii_colors import ASCIIColors, rich

# Panels for highlighting content
ASCIIColors.panel("Deployment successful!", title="✓ Success", border_style="green")

# Tables for structured data
ASCIIColors.table(
    "Service", "Status", "Latency",
    rows=[
        ["API Gateway", "[green]● Healthy[/green]", "12ms"],
        ["Database", "[yellow]● Degraded[/yellow]", "120ms"]
    ],
    title="System Health"
)

# Trees for hierarchical data
root = ASCIIColors.tree("📁 project")
root.add("📁 src").add("📄 main.py")
root.add("📁 tests")
ASCIIColors.rich_print(root)

# Syntax highlighting for code
code = "def hello(): print('world')"
ASCIIColors.syntax(code, language="python", line_numbers=True)

# Live displays for progress
with ASCIIColors.live("Starting...") as live:
    for i in range(10):
        live.update(f"Progress: {i+1}/10")
        time.sleep(0.5)
```

---

## ✨ Complete Feature Guide

### 🎨 Colors & Styles

#### Direct Color Methods

```python
from ascii_colors import ASCIIColors

# Standard foreground colors
ASCIIColors.black("Black text")
ASCIIColors.red("Red text")
ASCIIColors.green("Green text")
ASCIIColors.yellow("Yellow text")
ASCIIColors.blue("Blue text")
ASCIIColors.magenta("Magenta text")
ASCIIColors.cyan("Cyan text")
ASCIIColors.white("White text")
ASCIIColors.orange("Orange text (256-color)")

# Style modifiers (combine with colors)
ASCIIColors.bold("Bold text")
ASCIIColors.dim("Dim text")
ASCIIColors.italic("Italic text")
ASCIIColors.underline("Underlined text")
ASCIIColors.blink("Blinking text")
ASCIIColors.reverse("Reversed video")
ASCIIColors.hidden("Hidden text (password mask)")
ASCIIColors.strikethrough("Strikethrough text")

# Full control with .print()
ASCIIColors.print(
    "Complex styling",
    color=ASCIIColors.color_cyan,
    background=ASCIIColors.color_bg_black,
    style=ASCIIColors.style_bold + ASCIIColors.style_italic
)
```

#### Rich Markup Syntax

Use Rich-style markup for inline styling anywhere:

```python
from ascii_colors import ASCIIColors

# Basic colors
ASCIIColors.rich_print("[red]Error[/red] [green]Success[/green] [blue]Info[/blue]")
ASCIIColors.rich_print("[yellow]Warning[/yellow] [magenta]Accent[/magenta] [cyan]Highlight[/cyan]")

# Styles
ASCIIColors.rich_print("[bold]Bold[/bold] [italic]Italic[/italic] [underline]Underlined[/underline]")
ASCIIColors.rich_print("[dim]Dimmed[/dim] [blink]Blink[/blink]")

# Bright colors
ASCIIColors.rich_print("[bright_red]Bright red[/bright_red] [bright_green]Bright green[/bright_green]")

# Backgrounds
ASCIIColors.rich_print("[on red]White on red[/on red]")
ASCIIColors.rich_print("[bold white on blue]Bold white on blue[/bold white on blue]")

# Semantic tags
ASCIIColors.rich_print("[success]Operation completed[/success]")
ASCIIColors.rich_print("[error]An error occurred[/error]")
ASCIIColors.rich_print("[warning]Warning message[/warning]")
ASCIIColors.rich_print("[info]Information[/info]")
ASCIIColors.rich_print("[danger]Critical issue[/danger]")

# Method alias on ASCIIColors
ASCIIColors.rich_print("[bold green]Hello World[/bold green]")
```

---

### 🖥️ Rich Components (UI Elements)

ASCIIColors includes a complete **Rich-compatible** rendering layer — no external dependencies needed!

#### Panels

```python
from ascii_colors import ASCIIColors

# Simple panel
ASCIIColors.panel("Hello, World!", title="Greeting")

# Styled panel with markup
ASCIIColors.panel(
    "[bold red]This is a warning message with important information.[/bold red]",
    title="[bold yellow]⚠ Warning[/bold yellow]",
    border_style="bold yellow",
    box="round",           # "square", "round", "double", "minimal"
    padding=(1, 2)         # (vertical, horizontal)
)

# Using rich compatible module for more control
from ascii_colors import Panel, BoxStyle

panel = Panel(
    "Content with [bold]markup[/bold] support",
    title="[bold]Title[/bold]",
    border_style="bold cyan",
    box=BoxStyle.ROUND,
    padding=(2, 4),
    width=60
)
ASCIIColors.rich_print(panel)
```

#### Tables

```python
from ascii_colors import ASCIIColors

# Simple table
ASCIIColors.table(
    "Name", "Role", "Status",
    rows=[
        ["Alice", "Admin", "[green]Active[/green]"],
        ["Bob", "User", "[green]Active[/green]"],
        ["Carol", "Guest", "[yellow]Pending[/yellow]"]
    ]
)

# With title and styling
ASCIIColors.table(
    "Package", "Version", "Status",
    rows=[
        ["numpy", "1.24.0", "[green]✓ up to date[/green]"],
        ["pandas", "2.0.0", "[yellow]⚠ update available[/yellow]"],
        ["requests", "2.28.0", "[red]✗ security fix needed[/red]"]
    ],
    title="[bold]Installed Packages[/bold]",
    header_style="bold cyan",
    show_lines=True,
    box="round"
)
```

#### Trees

```python
from ascii_colors import ASCIIColors

# Build a file tree
root = ASCIIColors.tree("📁 project", style="bold")
src = root.add_node("📁 src")
src.add("📄 __init__.py")
src.add("📄 main.py")
utils = src.add_node("📁 utils")
utils.add("📄 helpers.py")

tests = root.add_node("📁 tests")
tests.add("📄 test_main.py")

root.add("📄 README.md")
root.add("📄 pyproject.toml")

ASCIIColors.rich_print(root)
```

#### Syntax Highlighting

```python
from ascii_colors import ASCIIColors

# Python code
python_code = '''
def fibonacci(n):
    """Generate Fibonacci sequence."""
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b
'''

ASCIIColors.syntax(python_code, language="python", line_numbers=True)

# JSON
json_code = '''{
    "name": "ascii_colors",
    "version": "1.0.0",
    "features": ["colors", "logging", "progress", "panels"]
}'''

ASCIIColors.syntax(json_code, language="json")

# Other languages: javascript, bash, yaml, sql, text
```

#### Markdown Rendering

```python
from ascii_colors import ASCIIColors

markdown_text = """# ASCII Colors

A **powerful** library for terminal output.

## Features

- *Colors* and styles
- **Bold** and __underlined__ text
- `inline code` support

> This is a blockquote with important information.

| Feature | Status |
|---------|--------|
| Panels | ✓ |
| Tables | ✓ |
| Trees | ✓ |
"""

ASCIIColors.markdown(markdown_text)
```

#### Columns Layout

```python
from ascii_colors import ASCIIColors

items = [
    "Feature 1: Colors",
    "Feature 2: Styles", 
    "Feature 3: Panels",
    "Feature 4: Tables",
    "Feature 5: Trees",
    "Feature 6: Syntax"
]

ASCIIColors.columns(*items, equal=True, width=30)
```

#### Rules (Dividers)

```python
from ascii_colors import ASCIIColors

# Simple rule
ASCIIColors.rule()

# With title
ASCIIColors.rule("Section Title", style="cyan")

# Alignment options
ASCIIColors.rule("Centered", style="bold magenta")     # default
ASCIIColors.rule("Left", align="left", style="yellow")
ASCIIColors.rule("Right", align="right", style="green")

# Custom characters
ASCIIColors.rule("Double", characters="═", style="blue")
```

#### Live Displays

```python
from ascii_colors import ASCIIColors
from ascii_colors import Text
import time

# Progress with live update
with ASCIIColors.live("Starting...", refresh_per_second=4) as live:
    for i in range(10):
        time.sleep(0.5)
        bar = "█" * (i + 1) + "░" * (9 - i)
        live.update(Text(f"Progress: [{bar}] {i+1}/10"))
    
    time.sleep(0.3)
    live.update(Text("[bold green]✓ Complete![/bold green]"))
```

#### Status Spinners

```python
from ascii_colors import ASCIIColors
import time

# Default dots spinner
with ASCIIColors.status("Loading data...") as status:
    time.sleep(3)

# Different spinner styles
spinners = ["dots", "line", "arrow", "pulse", "star", "moon"]
for spinner in spinners:
    with ASCIIColors.status(
        f"Testing {spinner}...",
        spinner=spinner,
        spinner_style="cyan"
    ) as status:
        time.sleep(2)

# With status updates
with ASCIIColors.status("Connecting...") as status:
    time.sleep(1)
    status.update("Authenticating...")
    time.sleep(1)
    status.update("Fetching data...")
```

---

### 🔄 Advanced Rich Patterns

#### Combining Live with Panels and Tables

Create professional dashboards that update in real-time:

```python
from ascii_colors import ASCIIColors
from ascii_colors import Panel, Table, Text, Columns
import time
import random

def create_dashboard(status, progress, logs):
    """Build a multi-panel dashboard layout."""
    # Status panel
    status_panel = Panel(
        f"[bold cyan]{status}[/bold cyan]",
        title="[bold]System Status[/bold]",
        border_style="green" if "healthy" in status.lower() else "yellow",
        width=40
    )
    
    # Progress panel with bar
    bar = "█" * (progress // 5) + "░" * (20 - progress // 5)
    progress_panel = Panel(
        f"[bold]{bar}[/bold] {progress}%",
        title="[bold]Progress[/bold]",
        border_style="cyan",
        width=40
    )
    
    # Recent logs panel
    log_text = "\n".join([f"[dim]{i+1}.[/dim] {log}" for i, log in enumerate(logs[-5:])])
    logs_panel = Panel(
        log_text or "[dim]No recent activity...[/dim]",
        title="[bold]Recent Logs[/bold]",
        border_style="magenta",
        height=10
    )
    
    # Metrics table
    metrics = Table("Metric", "Value", "Trend", box="minimal")
    metrics.add_row("CPU", f"{random.randint(20,80)}%", "[green]▼[/green]" if random.random() > 0.5 else "[red]▲[/red]")
    metrics.add_row("Memory", f"{random.randint(40,90)}%", "[green]▼[/green]" if random.random() > 0.5 else "[red]▲[/red]")
    metrics.add_row("Disk", f"{random.randint(50,95)}%", "[yellow]−[/yellow]")
    
    # Combine in columns
    top_row = Columns([status_panel, progress_panel], equal=True)
    
    return Text.assemble(
        top_row, "\n",
        logs_panel, "\n",
        metrics
    )

# Simulate live dashboard
logs = []
with ASCIIColors.live(create_dashboard("Initializing...", 0, logs), refresh_per_second=4) as live:
    for i in range(101):
        # Simulate work
        if i % 10 == 0:
            logs.append(f"Completed milestone {i//10}")
        
        status = "Healthy" if i < 80 else "Degraded" if i < 95 else "Critical"
        dashboard = create_dashboard(status, i, logs)
        live.update(dashboard)
        time.sleep(0.05)
    
    # Final state
    logs.append("Process completed successfully")
    live.update(create_dashboard("Complete", 100, logs))
    time.sleep(1)
```

#### Nested Live Updates with Tables Inside Panels

```python
from ascii_colors import ASCIIColors
from ascii_colors import Panel, Table, Text, Tree
import time

# File processing with live updates
files = ["data_001.csv", "data_002.csv", "data_003.csv", "report.pdf", "summary.json"]

with ASCIIColors.live("Preparing...", refresh_per_second=2) as live:
    for i, filename in enumerate(files):
        # Build processing table
        table = Table("File", "Status", "Progress", "Size")
        
        for j, f in enumerate(files):
            if j < i:
                status = "[green]✓ Complete[/green]"
                progress = "[green]100%[/green]"
                size = f"{random.randint(100, 5000)} KB"
            elif j == i:
                status = "[yellow]⏳ Processing...[/yellow]"
                prog_val = random.randint(10, 90)
                bar = "█" * (prog_val // 10) + "░" * (10 - prog_val // 10)
                progress = f"[yellow]{bar} {prog_val}%[/yellow]"
                size = "..."
            else:
                status = "[dim]⏸ Pending[/dim]"
                progress = "[dim]0%[/dim]"
                size = "-"
            
            table.add_row(f, status, progress, size)
        
        # Wrap in panel with dynamic title
        panel = Panel(
            table,
            title=f"[bold]Batch Processing ({i+1}/{len(files)})[/bold]",
            border_style="cyan"
        )
        
        live.update(panel)
        time.sleep(1.5)
    
    # Final success panel
    final_table = Table("File", "Status", "Size")
    for f in files:
        final_table.add_row(f, "[green]✓ Complete[/green]", f"{random.randint(100, 5000)} KB")
    
    success_panel = Panel(
        final_table,
        title="[bold green]✓ All Files Processed[/bold green]",
        border_style="green"
    )
    live.update(success_panel)
    time.sleep(2)
```

#### Custom Console Instances

Create multiple consoles with different configurations:

```python
from ascii_colors import ASCOIIColors
from ascii_colors import Console, Panel, Table

# Main console with full features
main_console = Console()

# Compact console for side panels
compact_console = Console(width=50, no_color=False)

# Log console (records output)
log_console = Console(record=True)

# Use different consoles
main_console.print(Panel("Main Application", title="App"))
compact_console.print(Panel("Side Info", title="Compact"))

# Log and export
log_console.log("Event 1")
log_console.log("Event 2")
log_content = log_console.export_text()  # Capture for file/email

# Jupyter-friendly console
jupyter_console = Console(force_jupyter=True)
jupyter_console.print("[blue]Notebook output[/blue]")
```

#### Status Spinner with Nested Live Display

Combine background status with foreground live updates:

```python
from ascii_colors import ASCIIColors
from ascii_colors import Text
import time

# Long-running operation with status and detailed progress
with ASCIIColors.status("Analyzing dataset...", spinner="dots") as status:
    # Simulate initial phase
    time.sleep(2)
    status.update("Loading data into memory...")
    
    # Switch to live display for detailed progress
    with ASCIIColors.live(Text("[dim]Preparing analysis...[/dim]"), refresh_per_second=2) as live:
        for phase, duration in [("Cleaning", 2), ("Transforming", 3), ("Computing", 4)]:
            for i in range(duration * 2):
                progress = (i / (duration * 2)) * 100
                bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
                live.update(Text(
                    f"[bold cyan]{phase}:[/bold cyan] [{bar}] {progress:.0f}%\n"
                    f"[dim]Processing records...[/dim]"
                ))
                time.sleep(0.5)
            
            status.update(f"Completed {phase.lower()}")
        
        live.update(Text("[bold green]✓ Analysis Complete[/bold green]"))
        time.sleep(1)
    
    status.update("Saving results...")
    time.sleep(1)
```

#### Rich Print with Conditional Formatting

```python
from ascii_colors import ASCIIColors

# Simulate API responses
responses = [
    {"status": 200, "time": 45},
    {"status": 404, "time": 120},
    {"status": 500, "time": 30},
    {"status": 200, "time": 25},
]

for resp in responses:
    # Dynamic coloring based on status
    color = "green" if resp["status"] == 200 else "yellow" if resp["status"] < 500 else "red"
    status_icon = "✓" if resp["status"] == 200 else "⚠" if resp["status"] < 500 else "✗"
    
    ASCIIColors.rich_print(
        f"[{color}]{status_icon}[/{color}] "
        f"Status: [bold]{resp['status']}[/bold] "
        f"([{color}]{resp['time']}ms[/{color}])"
    )
```

#### Panel with Internal Table and Tree

```python
from ascii_colors import ASCIIColors
from ascii_colors import Panel, Table, Tree

# Build complex nested layout
tree = Tree("[bold]Project Structure[/bold]")
src = tree.add_node("[blue]src/[/blue]")
src.add("[green]__init__.py[/green]")
src.add("[green]main.py[/green]")
tests = tree.add_node("[blue]tests/[/blue]")
tests.add("[green]test_main.py[/green]")

stats_table = Table("Metric", "Value", box="minimal")
stats_table.add_row("Files", "12")
stats_table.add_row("Lines", "1,247")
stats_table.add_row("Coverage", "[green]87%[/green]")

# Combine in a single panel with tree and table
combined_content = f"{tree}\n\n{stats_table}"
dashboard_panel = Panel(
    combined_content,
    title="[bold cyan]📊 Project Dashboard[/bold cyan]",
    border_style="cyan",
    padding=(1, 2)
)

ASCIIColors.rich_print(dashboard_panel)
```

---

### 🪵 Logging System

#### Basic Configuration

```python
import sys
import ascii_colors as logging

# Quick start
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# With multiple outputs
logger = logging.getLogger("MyApp")

# Console: colorful output
console = logging.ConsoleHandler(stream=sys.stdout, level=logging.INFO)
console.setFormatter(logging.Formatter(
    "{level_name:>8} | {message}",
    style='{'
))

# File: detailed logs
file_handler = logging.FileHandler("debug.log", level=logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
    include_source=True
))

# JSON: structured for aggregation
json_handler = logging.FileHandler("events.jsonl", level=logging.WARNING)
json_handler.setFormatter(logging.JSONFormatter(
    include_fields=["timestamp", "levelname", "name", "message", "pathname", "lineno"]
))

logging.getLogger().addHandler(console)
logging.getLogger().addHandler(file_handler)
logging.getLogger().addHandler(json_handler)

# Usage
logger.debug("Debug info")      # To file only
logger.info("Service started")  # To console and file
logger.warning("Disk full")     # To all handlers
logger.error("Database error")  # To all handlers
```

#### Contextual Logging

```python
from ascii_colors import ASCIIColors, logging

# Persistent context (all subsequent logs)
ASCIIColors.set_context(
    app_name="MyService",
    app_version="1.2.3",
    environment="production"
)

# Temporary context (auto-cleanup)
with ASCIIColors.context(
    request_id="req-abc-123",
    user_id="user-456"
):
    logger.info("Processing request")  # Includes context
    # ... do work ...
    logger.info("Done")  # Includes context

# After block: context automatically removed
logger.info("Cleanup")  # Without request context
```

#### 📜 File Rotation with `basicConfig`

For long-running services that need size-based log rotation, `basicConfig` now exposes `maxBytes` and `backupCount` directly — no need to wire up a `RotatingFileHandler` manually:

```python
import ascii_colors as logging

logging.basicConfig(
    filename="app.log",
    filemode="a",
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    file_maxBytes=10_000_000,   # Rotate when file reaches 10 MB
    file_backupCount=5,         # Keep 5 backup files
)

logger = logging.getLogger("MyService")
logger.info("This goes to app.log")
```

When `app.log` reaches 10 MB the file is rotated automatically:

```
app.log     ← current file (newly created)
app.log.1   ← previous run
app.log.2
app.log.3
app.log.4
app.log.5   ← oldest, deleted on next rotation
```

| Parameter | Default | Description |
|:---|:---|:---|
| `file_maxBytes` | `0` (no rotation) | Max size in bytes before rotating. Set to a positive value to enable rolling behavior. |
| `file_backupCount` | `0` | Number of backup files to keep. When `0`, the oldest file is deleted on each rotation. |

Setting `file_maxBytes=0` (the default) preserves the previous behavior of a plain append-only `FileHandler`. If you need time-based rotation, custom naming, or per-logger file routing, use `RotatingFileHandler` or `FolderRouterHandler` directly.

#### 🔍 Per-Logger File Routing — Built for LoLLMs VSCoder

When debugging complex applications with multiple components, scrolling through a single monolithic log file is painful and slow. **ASCII Colors** solves this with the `FolderRouterHandler`, which automatically routes each logger's output to its own dedicated file based on the logger's name.

**Why this is a game-changer for VSCoder AI agents:** When using the [LoLLMs VSCoder](https://github.com/ParisNeo/lollms-vscoder) extension, you can simply add the relevant log file(s) to your AI's context. The agent sees *only* the output from the module you're debugging — no noise, no scrolling, no confusion. Just focused, isolated diagnostics that lead to faster, more accurate fixes.

```python
import ascii_colors as logging

# Configure once at startup: route each logger to its own file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)-8s] %(message)s',
    log_folder="./logs",              # Output directory
    log_folder_mode="timestamp",      # New file per run (or "rolling" / "overwrite")
)

# Use named loggers throughout your codebase
auth_logger = logging.getLogger("auth")
db_logger = logging.getLogger("database")
api_logger = logging.getLogger("api")

auth_logger.info("User logged in")
db_logger.error("Connection pool exhausted")
api_logger.debug("Request received: /users/42")
```

**What gets created automatically:**

```
logs/
├── auth_20251006_184523.log
├── database_20251006_184523.log
└── api_20251006_184523.log
```

**The VSCoder workflow:**

1. An error occurs in your `database` module
2. Open VSCoder and start a chat
3. Click **Add Files to Context** and select `logs/database_20251006_184523.log`
4. Ask: *"Why is my database connection failing?"*
5. The AI sees the exact log file and provides a focused diagnosis — without wading through every other module's output

**Three routing modes for every workflow:**

| Mode | Behavior | Best For |
|:---|:---|:---|
| `rolling` | Rotates by size, keeps N backups | Long-running production services |
| `overwrite` | Single file per logger, truncated each run | Quick dev iteration, fresh start every run |
| `timestamp` | New file per run with timestamp in name | Preserving history, debugging specific runs |

**Manual setup (for fine-grained control):**

```python
from ascii_colors import ASCIIColors, FolderRouterHandler, Formatter
import ascii_colors as logging

handler = FolderRouterHandler(
    folder_path="./project_logs",
    mode="rolling",
    maxBytes=10_000_000,      # 10MB per file before rotation
    backupCount=5,            # Keep 5 backup files
    level=logging.DEBUG,
)
handler.setFormatter(Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
ASCIIColors.add_handler(handler)
```

**Pro tip:** Use descriptive, hierarchical logger names like `"app.auth.oauth"`, `"app.db.postgres"`, or `"app.api.v2.users"`. They're automatically sanitized into valid filenames (slashes and special characters become underscores), and you can correlate them directly with your module structure for instant context isolation when debugging.

---

### 🏗️ Multi-Module Project Best Practices

ASCII Colors is designed to make multi-module logging trivially clean. Follow this canonical pattern in your application:

#### The "configure-first" pattern

```python
# main.py — the entry point of your application
import ascii_colors as logging

# 1. Configure logging ONCE, at the top of your entry point
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_folder="./logs",                # Per-module file routing
    log_folder_mode="rolling",
    log_folder_maxBytes=10_000_000,
    log_folder_backupCount=5,
    force=True,                         # Safe in entry points: deterministic
)

# 2. NOW import your application modules
from myapp import auth, api, database

# 3. Run
auth.start()
api.serve()
```

In every other file of your project, this is **all you need**:

```python
# myapp/auth.py
import ascii_colors as logging
logger = logging.getLogger(__name__)   # → "myapp.auth"

def login(user, pwd):
    logger.info("Login attempt: %s", user)
    # → automatically routed to logs/myapp.auth.log
```

#### Why this works

| Concern | How it's handled |
|:---|:---|
| Logger created *before* `basicConfig`? | Falls back to a default console handler; picks up the configured handlers on the next emit. No crash. |
| Multiple files share the same config? | All read from the global `ASCIIColors._handlers` list — zero duplication. |
| Memory cost per module? | Negligible: loggers are cached by name in `_logger_cache`. |
| Re-importing the same module? | Same cached adapter, no handler leaks. |
| Per-logger file routing? | `__name__` becomes the filename stem → VSCoder-friendly isolation. |

#### Key rules

1. **Configure once, at the top of `main.py` (or your entry point).**
2. **Configure *before* importing your own modules** — this captures any import-time log messages cleanly.
3. **Use `force=True` at the entry point, `force=False` inside libraries** to avoid clobbering host applications.
4. **Every other file just does `logger = logging.getLogger(__name__)`** — never call `basicConfig` from a library module.
5. **Never hardcode a `filename=` per-module** — let `FolderRouterHandler` route by name.

#### Decision matrix: which configuration to use

| Scenario | Configuration |
|:---|:---|
| One log file for the whole app | `filename="app.log"` + `file_maxBytes` + `file_backupCount` |
| One file per module (VSCoder debugging) | `log_folder="./logs"` + `log_folder_mode` |
| Both (file + folder fallback) | Use a `handlers=[...]` list in `basicConfig` |
| Library code | Only `getLogger(__name__)` — never `basicConfig` |

#### Testing

Configure logging once in `conftest.py` to a temp directory — every test then gets automatic per-logger isolation:

```python
# tests/conftest.py
import tempfile
import ascii_colors as logging
import pytest

@pytest.fixture(autouse=True)
def isolated_logging():
    tmp = tempfile.mkdtemp()
    logging.basicConfig(
        log_folder=tmp,
        log_folder_mode="overwrite",  # Clean state per test
        force=True,
    )
    yield
    logging.shutdown()
```

---

### 📊 Progress Bars

```python
from ascii_colors import ProgressBar, ASCIIColors
import time

# Basic usage
for item in ProgressBar(range(100), desc="Processing"):
    time.sleep(0.01)

# Custom styling
for item in ProgressBar(
    range(1000),
    desc="Uploading",
    color=ASCIIColors.color_cyan,
    bar_style="fill",      # "fill", "line", "blocks", "emoji"
    progress_char="█",
    empty_char="░"
):
    process(item)

# Emoji style
for item in ProgressBar(
    range(100),
    desc="Building",
    bar_style="emoji",
    progress_char="🚀",
    empty_char="⬛"
):
    build_step()

# Manual control
with ProgressBar(total=1024*1024, desc="Uploading", unit="B") as pbar:
    while chunk := read_chunk():
        pbar.update(len(chunk))
```

---

### 🖱️ Interactive Menus

```python
from ascii_colors import Menu, ASCIIColors

# Return mode — select and return value
menu = Menu("Choose format", mode='return')
menu.add_choice("JSON", value="json")
menu.add_choice("YAML", value="yaml")
menu.add_choice("XML", value="xml")

format_choice = menu.run()  # Returns "json", "yaml", or "xml"

# Execute mode — run actions
def show_status():
    ASCIIColors.green("All systems operational")

menu = Menu("System Manager", mode='execute')
menu.add_action("Show Status", show_status)
menu.add_action("Restart", restart_service)
menu.run()

# Checkbox mode — multi-select
menu = Menu("Select features", mode='checkbox')
menu.add_checkbox("Auth", value="auth", checked=True)
menu.add_checkbox("Cache", value="cache")
selected = menu.run()  # Returns list like ["auth"]

# With filtering
menu = Menu("Select user", mode='return', enable_filtering=True)
menu.add_choices([
    ("Alice Anderson", "alice"),
    ("Bob Baker", "bob"),
    ("Charlie Chen", "charlie"),
])
```

---

### ❓ Smart Prompts (Questionary-Compatible)

Complete drop-in replacement for the `questionary` library:

```python
from ascii_colors import questionary

# Text input
name = questionary.text("What's your name?", default="Anonymous").ask()

# Password (hidden, with confirmation)
password = questionary.password(
    "Set password",
    confirm=True
).ask()

# Yes/No confirmation
if questionary.confirm("Continue?", default=True).ask():
    proceed()

# Single selection
color = questionary.select(
    "Favorite color?",
    choices=["Red", "Green", "Blue"]
).ask()

# With display names and values
format_choice = questionary.select(
    "Export format",
    choices=[
        {"name": "JSON (recommended)", "value": "json"},
        {"name": "YAML", "value": "yaml", "disabled": True},
        {"name": "CSV", "value": "csv"}
    ]
).ask()  # Returns "json", "yaml", or "csv"

# Multi-selection (checkbox)
features = questionary.checkbox(
    "Select features",
    choices=[
        {"name": "Authentication", "value": "auth", "checked": True},
        {"name": "Logging", "value": "logging"},
        {"name": "Caching", "value": "cache"}
    ]
).ask()  # Returns list of selected values

# Autocomplete
city = questionary.autocomplete(
    "Enter city",
    choices=["New York", "London", "Tokyo", "Paris"],
    ignore_case=True,
    match_middle=True
).ask()

# Forms (multiple questions)
answers = questionary.form(
    questionary.text("First name"),
    questionary.text("Last name"),
    questionary.confirm("Subscribe?", default=False)
).ask()
# Returns: {"First name": "...", "Last name": "...", "Subscribe?": True/False}

# Validation
from ascii_colors.questionary import Validator, ValidationError

class EmailValidator(Validator):
    def validate(self, document):
        if "@" not in document:
            raise ValidationError("Email must contain @")

email = questionary.text("Email:", validate=EmailValidator()).ask()

# Conditional questions
is_company = questionary.confirm("Company account?").ask()
company_name = questionary.text("Company name").skip_if(
    not is_company, default="N/A"
).ask()
```

---

### 🛠️ Utility Functions

```python
from ascii_colors import ASCIIColors, get_trace_exception

# Execute with spinner animation
def long_task():
    time.sleep(3)
    return "result"

result = ASCIIColors.execute_with_animation(
    "Processing...",
    long_task,
    color=ASCIIColors.color_yellow
)

# Enhanced exception display
try:
    risky_operation()
except Exception as e:
    # Beautiful traceback with local variables
    formatted = get_trace_exception(e, enhanced=True)
    print(formatted)
    
    # Or log it
    ASCIIColors.trace_exception(e, enhanced=True)

# Multicolor text
ASCIIColors.multicolor(
    ["Status: ", "ACTIVE", " | Load: ", "85%"],
    [
        ASCIIColors.color_white,
        ASCIIColors.color_green,
        ASCIIColors.color_white,
        ASCIIColors.color_yellow
    ]
)

# Highlight patterns
ASCIIColors.highlight(
    "ERROR: File not found",
    subtext=["ERROR", "not found"],
    highlight_color=ASCIIColors.color_bright_red
)
```

---

## 🎨 Complete Color & Style Reference

### Reset
| Constant | Effect |
|:---|:---|
| `color_reset` | Reset all colors and styles |

### Text Styles
| Constant | ANSI Code | Effect |
|:---|:---|:---|
| `style_bold` | `\u001b[1m` | Bold/Bright |
| `style_dim` | `\u001b[2m` | Dim/Faint |
| `style_italic` | `\u001b[3m` | Italic |
| `style_underline` | `\u001b[4m` | Underline |
| `style_blink` | `\u001b[5m` | Slow blink |
| `style_blink_fast` | `\u001b[6m` | Rapid blink |
| `style_reverse` | `\u001b[7m` | Reverse video |
| `style_hidden` | `\u001b[8m` | Hidden/Concealed |
| `style_strikethrough` | `\u001b[9m` | Strikethrough |

### Foreground Colors
| Constant | Code | Constant | Code |
|:---|:---|:---|:---|
| `color_black` | 30 | `color_bright_black` | 90 |
| `color_red` | 31 | `color_bright_red` | 91 |
| `color_green` | 32 | `color_bright_green` | 92 |
| `color_yellow` | 33 | `color_bright_yellow` | 93 |
| `color_blue` | 34 | `color_bright_blue` | 94 |
| `color_magenta` | 35 | `color_bright_magenta` | 95 |
| `color_cyan` | 36 | `color_bright_cyan` | 96 |
| `color_white` | 37 | `color_bright_white` | 97 |
| `color_orange` | 38;5;208 | — | — |

### Background Colors
| Constant | Code | Constant | Code |
|:---|:---|:---|:---|
| `color_bg_black` | 40 | `color_bg_bright_black` | 100 |
| `color_bg_red` | 41 | `color_bg_bright_red` | 101 |
| `color_bg_green` | 42 | `color_bg_bright_green` | 102 |
| `color_bg_yellow` | 43 | `color_bg_bright_yellow` | 103 |
| `color_bg_blue` | 44 | `color_bg_bright_blue` | 104 |
| `color_bg_magenta` | 45 | `color_bg_bright_magenta` | 105 |
| `color_bg_cyan` | 46 | `color_bg_bright_cyan` | 106 |
| `color_bg_white` | 47 | `color_bg_bright_white` | 107 |
| `color_bg_orange` | 48;5;208 | — | — |

---

## 🔄 Migration Guides

### From Standard `logging` Module

```python
# Before (standard logging)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("myapp")

# After (ascii_colors) — identical API!
import ascii_colors as logging  # Just change the import!
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("myapp")

# Plus: colorful output, JSON formatters, contextual logging, etc.
```

### From `colorama`

```python
# Before (colorama)
from colorama import init, Fore, Back, Style
init()
print(Fore.RED + "Error" + Style.RESET_ALL)

# After (ascii_colors)
from ascii_colors import ASCIIColors
ASCIIColors.red("Error")  # Auto-reset, more intuitive

# Plus: backgrounds, styles, bright colors, logging, progress bars, etc.
```

### From `tqdm`

```python
# Before (tqdm)
from tqdm import tqdm
for i in tqdm(range(100)):
    pass

# After (ascii_colors)
from ascii_colors import ProgressBar
for i in ProgressBar(range(100), color=ASCIIColors.color_cyan):
    pass

# Plus: custom chars, colors, styles, thread-safe, manual control
```

### From `questionary`

```python
# Before (questionary)
import questionary
name = questionary.text("Name?").ask()

# After (ascii_colors) — drop-in replacement!
from ascii_colors import questionary  # Just change the import!
name = questionary.text("Name?").ask()

# Plus: enhanced styling, no dependencies, built-in integration
```

### From `rich`

```python
# Before (rich)
from rich import print
from rich.panel import Panel
from rich.table import Table

print(Panel("Hello"))

# After (ascii_colors) — familiar API, no dependency!
from ascii_colors import rich

ASCIIColors.rich_print(rich.Panel("Hello"))

# Or use convenience methods
from ascii_colors import ASCIIColors
ASCIIColors.panel("Hello")

# Plus: zero dependencies, lighter weight, integrates with logging
```

---

## 📚 Documentation & Resources

- **[Full Documentation](https://parisneo.github.io/ascii_colors/)** — Complete guides, API reference, and examples
- **[PyPI Package](https://pypi.org/project/ascii-colors/)** — Release history and installation
- **[GitHub Repository](https://github.com/ParisNeo/ascii_colors)** — Source code and contributions
- **[Changelog](CHANGELOG.md)** — Version history and migration notes

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development setup instructions
- Code style guidelines (we use Black)
- Testing requirements
- Pull request process

Quick start for contributors:

```bash
git clone https://github.com/ParisNeo/ascii_colors.git
cd ascii_colors
pip install -e ".[dev]"
pytest tests/  # Run the test suite
```

---

## 🐛 Troubleshooting

### Colors not showing in Windows
- Windows 10 version 1511+ supports ANSI colors natively
- For older systems, use Windows Terminal or VS Code terminal
- Legacy CMD may need `colorama`: `pip install colorama`

### Progress bar width issues with wide characters
```bash
pip install wcwidth
```

### Logging not appearing
- Check global level: `ASCIIColors.set_log_level(LogLevel.DEBUG)`
- Check handler level: `handler.setLevel(LogLevel.DEBUG)`
- Ensure handler is added: `ASCIIColors.add_handler(handler)`

---

## 📜 License

Apache License 2.0 — see [LICENSE](LICENSE) for full details.

---

**Ready to make your CLI applications shine?**

```bash
pip install ascii_colors
```

Start building beautiful, powerful terminal applications today! 🚀