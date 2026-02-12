# ASCIIColors 🎨 Rich Terminal Output Made Simple

[![PyPI version](https://img.shields.io/pypi/v/ascii_colors.svg)](https://pypi.org/project/ascii-colors/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/ascii_colors.svg)](https://pypi.org/project/ascii-colors/)
[![PyPI license](https://img.shields.io/pypi/l/ascii_colors.svg)](https://github.com/ParisNeo/ascii_colors/blob/main/LICENSE)
[![PyPI downloads](https://img.shields.io/pypi/dm/ascii_colors.svg)](https://pypi.org/project/ascii-colors/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **One library. Colors. Logging. Progress. Menus. Prompts. Done.**

Stop wrestling with multiple CLI libraries. **ASCIIColors** unifies everything you need for modern terminal applications into a single, elegant toolkit — from quick colored output to production-grade logging, interactive menus, and smart prompts.

| 🎨 **Colors & Styles** | 🪵 **Logging System** | 📊 **Progress Bars** |
|:---|:---|:---|
| 256-color support, bright variants, backgrounds, bold/italic/underline/blink | Full `logging` compatibility with handlers, formatters, JSON output, rotation | `tqdm`-like bars with custom styles (fill, blocks, line, emoji), thread-safe |

| 🖱️ **Interactive Menus** | ❓ **Smart Prompts** | 🛠️ **Utilities** |
|:---|:---|:---|
| Arrow-key navigation, submenus, filtering, multi-select, checkbox mode | Drop-in `questionary` replacement: text, password, confirm, select, checkbox, autocomplete | Spinners, syntax highlighting, enhanced tracebacks with locals, multicolor text, confirm/prompt helpers |

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

ASCIIColors offers **two complementary approaches** that work seamlessly together:

| Approach | Best For | API Style | Key Methods |
|:---|:---|:---|:---|
| **Direct Print** | Immediate visual feedback, status messages, user interaction, spinners | `ASCIIColors.green("text")` | `print()`, `red()`, `green()`, `multicolor()`, `highlight()` |
| **Logging System** | Structured application logs, filtering, multiple outputs, production monitoring | `import ascii_colors as logging` | `basicConfig()`, `getLogger()`, `add_handler()` |

### Direct Print — Instant Visual Feedback

Perfect for CLI tools, status messages, and user-facing output:

```python
from ascii_colors import ASCIIColors

# Simple color methods — print immediately to terminal
ASCIIColors.red("Error: Connection failed")
ASCIIColors.green("✓ Success!")
ASCIIColors.yellow("Warning: Low memory", style=ASCIIColors.style_bold)
ASCIIColors.blue("Info: Processing item 42")

# Full control with .print() — combine colors, backgrounds, styles
ASCIIColors.print(
    " CRITICAL SYSTEM FAILURE ",
    color=ASCIIColors.color_black,
    background=ASCIIColors.color_bg_red,
    style=ASCIIColors.style_bold + ASCIIColors.style_blink
)

# Multicolor text — inline color changes without multiple print calls
ASCIIColors.multicolor(
    ["Status: ", "ACTIVE", " | Load: ", "85%", " | Memory: ", "OK"],
    [
        ASCIIColors.color_white,
        ASCIIColors.color_green,
        ASCIIColors.color_white,
        ASCIIColors.color_yellow,
        ASCIIColors.color_white,
        ASCIIColors.color_green
    ]
)

# Highlight patterns in text — great for log filtering
ASCIIColors.highlight(
    "ERROR: File not found in /path/to/file at line 42",
    subtext=["ERROR", "not found"],
    highlight_color=ASCIIColors.color_bright_red,
    color=ASCIIColors.color_white  # Non-matching text color
)

# Highlight entire lines containing pattern
log_output = """\
INFO: Server starting...
ERROR: Database connection failed
INFO: Retrying connection...
ERROR: Max retries exceeded
INFO: Shutting down...
"""
ASCIIColors.highlight(
    log_output,
    subtext="ERROR",
    whole_line=True,
    highlight_color=ASCIIColors.color_bg_bright_red + ASCIIColors.color_white
)
```

### Logging System — Production-Grade Structured Logging

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
# JSON file for log aggregation
json_handler = logging.FileHandler("app.jsonl", mode='a')
json_handler.setFormatter(logging.JSONFormatter(
    include_fields=["timestamp", "levelname", "name", "message", "pathname", "lineno"]
))
json_handler.setLevel(logging.WARNING)  # Only WARNING and above
logging.getLogger().addHandler(json_handler)

# Rotating file handler for long-running applications
rotate_handler = logging.handlers.RotatingFileHandler(
    "debug.log",
    maxBytes=10*1024*1024,  # 10 MB per file
    backupCount=5
)
rotate_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
))
rotate_handler.setLevel(logging.DEBUG)  # All debug info
logging.getLogger().addHandler(rotate_handler)

# Use throughout your application
logger = logging.getLogger("MyService")

logger.debug("Connection pool initialized with %d connections", 10)  # To debug.log only
logger.info("Service started on port %d", 8080)  # To console and debug.log
logger.warning("Disk usage at %d%%", 85)  # To all handlers
logger.error("Failed to connect to database")  # To all handlers
logger.critical("System out of memory!")  # To all handlers

# Exception logging with full tracebacks
try:
    risky_operation()
except Exception as e:
    logger.exception("Operation failed: %s", e)  # Automatically includes exc_info
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

# Combining styles and colors
ASCIIColors.print(
    "Important!",
    color=ASCIIColors.color_yellow,
    style=ASCIIColors.style_bold + ASCIIColors.style_underline
)

# Bright colors (high intensity)
ASCIIColors.print("Bright red", color=ASCIIColors.color_bright_red)
ASCIIColors.print("Bright green", color=ASCIIColors.color_bright_green)
ASCIIColors.print("Bright blue", color=ASCIIColors.color_bright_blue)
# ... and all other bright variants

# Background colors
ASCIIColors.print("Red background", background=ASCIIColors.color_bg_red)
ASCIIColors.print("Bright yellow background", background=ASCIIColors.color_bg_bright_yellow)

# Full control with .print()
ASCIIColors.print(
    "Complex styling",
    color=ASCIIColors.color_cyan,
    background=ASCIIColors.color_bg_black,
    style=ASCIIColors.style_bold + ASCIIColors.style_italic,
    end="\n\n",  # Custom line ending
    flush=True,   # Force immediate output
    file=sys.stderr  # Output stream
)
```

#### Advanced Printing Features

```python
# Compose effects by nesting (emit=False returns string without printing)
styled = ASCIIColors.green("Success: ", emit=False, end="")
styled += ASCIIColors.bold("Operation completed", emit=False)
print(styled)  # Print composed string

# Multiline colored blocks
ASCIIColors.print("""\
Line 1
Line 2
Line 3""", color=ASCIIColors.color_blue)

# Conditional coloring based on status
def print_status(message, is_error=False):
    color = ASCIIColors.color_red if is_error else ASCIIColors.color_green
    prefix = "✗" if is_error else "✓"
    ASCIIColors.print(f"{prefix} {message}", color=color, style=ASCIIColors.style_bold)

print_status("File saved")           # Green
print_status("Permission denied", True)  # Red
```

### 📊 Progress Bars

Customizable, thread-safe progress bars for any iterable or manual updates:

```python
from ascii_colors import ProgressBar, ASCIIColors
import time

# Basic usage — wrap any iterable
for item in ProgressBar(range(100), desc="Processing"):
    time.sleep(0.01)  # Your work here

# Custom styling
for item in ProgressBar(
    range(1000),
    desc="Uploading",
    unit="files",
    color=ASCIIColors.color_cyan,
    bar_style="fill",      # "fill" (default), "line", "blocks", "emoji"
    progress_char="█",
    empty_char="░"
):
    process_file(item)

# Emoji style
for item in ProgressBar(
    range(100),
    desc="Building",
    bar_style="emoji",
    progress_char="🚀",
    empty_char="⬛"
):
    build_step()

# Manual control with context manager
with ProgressBar(
    total=1024 * 1024,  # Total bytes to upload
    desc="Uploading",
    unit="B",
    unit_scale=True,    # Auto-convert to KB, MB, etc.
    unit_divisor=1024
) as pbar:
    while chunk := read_chunk():
        pbar.update(len(chunk))
        # Progress bar updates automatically

# Manual control without context manager
pbar = ProgressBar(total=100, desc="Custom")
pbar.update(10)   # Update by 10
pbar.update(20)   # Update by 20 (now at 30)
pbar.n = 50       # Set absolute position
pbar.refresh()    # Force redraw
pbar.close()      # Clean up (or use context manager)

# Thread-safe updates from multiple threads
import threading

pbar = ProgressBar(total=100, desc="Parallel")

def worker():
    for _ in range(25):
        pbar.update(1)
        time.sleep(0.01)

threads = [threading.Thread(target=worker) for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
pbar.close()

# Custom bar format
custom_format = "{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
for item in ProgressBar(
    range(100),
    desc="Custom",
    bar_format=custom_format
):
    time.sleep(0.01)
```

### 🖱️ Interactive Menus

Keyboard-navigable menus with multiple modes:

```python
from ascii_colors import Menu, ASCIIColors

# ============================================
# MODE 1: Return Mode — Select and return value
# ============================================

menu = Menu("Choose export format", mode='return')
menu.add_choice("JSON", value="json")
menu.add_choice("YAML", value="yaml")
menu.add_choice("XML", value="xml")
menu.add_choice("CSV", value="csv")

format_choice = menu.run()  # Returns "json", "yaml", "xml", or "csv"
print(f"Selected: {format_choice}")

# With filtering (type to filter choices)
menu = Menu("Select user", mode='return', enable_filtering=True)
menu.add_choices([
    ("Alice Anderson", "alice"),
    ("Bob Baker", "bob"),
    ("Charlie Chen", "charlie"),
    ("Diana Davis", "diana"),
])
user = menu.run()  # Type "al" to filter to "Alice Anderson"

# ============================================
# MODE 2: Execute Mode — Run actions
# ============================================

def show_status():
    ASCIIColors.green("All systems operational")

def restart_service():
    ASCIIColors.yellow("Restarting...")
    # Restart logic here
    ASCIIColors.green("Restarted!")

def quit_app():
    ASCIIColors.cyan("Goodbye!")
    exit(0)

main_menu = Menu("System Manager", mode='execute')
main_menu.add_action("Show Status", show_status)
main_menu.add_action("Restart Service", restart_service)
main_menu.add_action("Quit", quit_app)

main_menu.run()  # Menu loops until quit action selected

# ============================================
# MODE 3: Checkbox Mode — Multi-select
# ============================================

features_menu = Menu("Select features to install", mode='checkbox')
features_menu.add_checkbox("Authentication", value="auth", checked=True)
features_menu.add_checkbox("Logging", value="logging", checked=True)
features_menu.add_checkbox("Caching", value="cache", checked=False)
features_menu.add_checkbox("WebSocket", value="websocket", checked=False)
features_menu.add_checkbox("GraphQL API", value="graphql", checked=False)

selected = features_menu.run()  # Space to toggle, Enter to confirm
print(f"Installing: {selected}")  # e.g., ['auth', 'logging', 'cache']

# ============================================
# Advanced: Submenus and custom styling
# ============================================

# Create submenu
settings_menu = Menu("Settings", mode='execute')
settings_menu.add_action("General", lambda: print("General settings"))
settings_menu.add_action("Network", lambda: print("Network settings"))

# Create main menu with custom styling
main = Menu(
    "Application Menu",
    mode='execute',
    clear_screen_on_run=True,      # Clear screen before showing
    pointer="▶",                    # Custom pointer
    selected_icon="●",              # Custom selected indicator
    unselected_icon="○"
)

main.add_action("Start", lambda: print("Starting..."))
main.add_submenu("Settings", settings_menu)  # ↗ Enter submenu
main.add_input("Username", initial_value="admin")  # Text input field
main.add_action("Exit", lambda: exit(0))

main.run()
```

### ❓ Smart Prompts (Questionary-Compatible)

Complete drop-in replacement for the `questionary` library:

```python
from ascii_colors import questionary  # Module-like object
# Or import directly:
# from ascii_colors import text, password, confirm, select, checkbox, autocomplete, form

# ============================================
# Text Input
# ============================================

# Basic text
name = questionary.text("What's your name?").ask()

# With default value
name = questionary.text(
    "What's your name?",
    default="Anonymous"
).ask()

# Multiline text
description = questionary.text(
    "Enter description",
    multiline=True
).ask()

# With validation
def validate_email(text):
    return "@" in text and "." in text.split("@")[1]

email = questionary.text(
    "Enter email",
    validate=validate_email
).ask()

# Using Validator class
from ascii_colors.questionary import Validator, ValidationError

class NonEmptyValidator(Validator):
    def validate(self, document):
        if not document.strip():
            raise ValidationError("Please enter a value")

value = questionary.text("Required field", validate=NonEmptyValidator()).ask()

# ============================================
# Password Input
# ============================================

# Basic password (hidden input)
password = questionary.password("Enter password").ask()

# With confirmation (enter twice)
password = questionary.password(
    "Set password",
    confirm=True,
    confirm_message="Confirm password"
).ask()

# ============================================
# Confirmation (Yes/No)
# ============================================

if questionary.confirm("Do you want to continue?").ask():
    print("Continuing...")

# With default
proceed = questionary.confirm("Proceed?", default=True).ask()

# ============================================
# Single Select
# ============================================

# Simple list
color = questionary.select(
    "Favorite color?",
    choices=["Red", "Green", "Blue", "Yellow"]
).ask()

# With dictionary choices (name shown, value returned)
format_choice = questionary.select(
    "Export format",
    choices=[
        {"name": "JSON (recommended)", "value": "json"},
        {"name": "YAML", "value": "yaml"},
        {"name": "XML (legacy)", "value": "xml", "disabled": True}
    ],
    default="json"
).ask()  # Returns "json", "yaml", or "xml"

# ============================================
# Multi-Select (Checkbox)
# ============================================

features = questionary.checkbox(
    "Select features",
    choices=["Auth", "Logging", "Cache", "WebSocket"],
    default=["Auth", "Logging"]  # Pre-selected
).ask()  # Returns list like ["Auth", "Cache"]

# With custom styling
features = questionary.checkbox(
    "Select toppings",
    choices=[
        {"name": "Cheese", "value": "cheese", "checked": True},
        {"name": "Pepperoni", "value": "pepperoni"},
        {"name": "Mushrooms", "value": "mushrooms"},
        {"name": "Anchovies", "value": "anchovies", "disabled": True}
    ]
).ask()

# Minimum selection requirement
required = questionary.checkbox(
    "Select at least one",
    choices=["A", "B", "C"],
    min_selected=1
).ask()

# ============================================
# Autocomplete
# ============================================

city = questionary.autocomplete(
    "Enter city",
    choices=[
        "New York", "Los Angeles", "Chicago", "Houston", "Boston",
        "Seattle", "Denver", "Atlanta", "Miami", "San Francisco"
    ],
    ignore_case=True,      # Case-insensitive matching
    match_middle=True,     # Match "geles" to "Los Angeles"
    max_suggestions=5      # Show max 5 suggestions
).ask()

# ============================================
# Forms — Sequential Questions
# ============================================

user_info = questionary.form(
    questionary.text("First name"),
    questionary.text("Last name"),
    questionary.password("Password", confirm=True),
    questionary.confirm("Subscribe to newsletter?", default=False)
).ask()
# Returns: {
#     "First name": "...",
#     "Last name": "...",
#     "Password": "...",
#     "Subscribe to newsletter?": True/False
# }

# Conditional skipping
is_company = questionary.confirm("Is this a company account?").ask()

company_name = questionary.text(
    "Company name:"
).skip_if(not is_company, default="N/A").ask()

# ============================================
# Direct API Alternative
# ============================================

from ascii_colors.questionary import text, password, confirm, select, checkbox

# Same usage, slightly different import
name = text("Name?").ask()
proceed = confirm("Continue?").ask()
```

### 🛠️ Utility Functions

```python
from ascii_colors import ASCIIColors, execute_with_animation, confirm, prompt

# ============================================
# Execute with Animation (Spinner)
# ============================================

def long_running_task():
    import time
    time.sleep(3)
    return "Result data"

# Shows spinner while function runs
result = ASCIIColors.execute_with_animation(
    "Processing large dataset...",
    long_running_task,
    color=ASCIIColors.color_yellow  # Spinner color
)
# On success: ✓ appears, result returned
# On failure: ✗ appears, exception re-raised

# With custom success/failure messages
result = ASCIIColors.execute_with_animation(
    "Uploading file",
    upload_function,
    color=ASCIIColors.color_cyan
)

# ============================================
# Confirmation Prompt
# ============================================

# Simple yes/no
if ASCIIColors.confirm("Delete this file?"):
    delete_file()

# With default (yes/no)
if ASCIIColors.confirm("Overwrite existing?", default_yes=False):
    overwrite()

# Custom colors
if ASCIIColors.confirm(
    "Continue with dangerous operation?",
    default_yes=False,
    prompt_color=ASCIIColors.color_bright_red
):
    dangerous_op()

# ============================================
# Styled Prompt
# ============================================

# Basic prompt
name = ASCIIColors.prompt("Your name: ", color=ASCIIColors.color_green)

# Hidden input (password)
password = ASCIIColors.prompt(
    "Password: ",
    hide_input=True,
    color=ASCIIColors.color_magenta
)

# Styled prompt with underline
api_key = ASCIIColors.prompt(
    "API Key: ",
    color=ASCIIColors.color_cyan,
    style=ASCIIColors.style_underline
)

# ============================================
# Enhanced Exception Display
# ============================================

from ascii_colors import trace_exception, get_trace_exception

try:
    risky_operation()
except Exception as e:
    # Log with standard traceback
    trace_exception(e, enhanced=False)
    
    # Or display beautiful enhanced traceback
    formatted = get_trace_exception(e, enhanced=True, max_width=120)
    print(formatted)
    # Shows: Boxed frame with file paths, line numbers, source code,
    #        local variables in each frame, and formatted exception

# Direct enhanced display
try:
    1/0
except Exception as e:
    trace_exception(e, enhanced=True)  # Full visual traceback
```

---

## 🪵 Complete Logging Guide

### Basic Configuration

```python
import sys
from ascii_colors import (
    ASCIIColors, LogLevel, basicConfig, getLogger,
    ConsoleHandler, FileHandler, RotatingFileHandler,
    Formatter, JSONFormatter
)

# ============================================
# Quick Start with basicConfig
# ============================================

# Console-only, simple format
basicConfig(
    level=DEBUG,
    format='%(levelname)s: %(message)s'
)

# With timestamp and source location
basicConfig(
    level=INFO,
    format='%(asctime)s [%(levelname)-8s] %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stdout
)

# With file output
basicConfig(
    level=DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s',
    filename='app.log',
    filemode='a'  # 'a' append, 'w' overwrite
)

# Force reconfiguration (closes existing handlers)
basicConfig(
    level=WARNING,
    format='%(message)s',
    force=True
)

# ============================================
# Manual Configuration (Full Control)
# ============================================

# Clear any existing configuration
ASCIIColors.clear_handlers()

# Console handler: colorful, brief, INFO+
console = ConsoleHandler(stream=sys.stdout, level=LogLevel.INFO)
console.setFormatter(Formatter(
    "{level_name:>8} | {message}",  # Brace style format
    style='{'
))
ASCIIColors.add_handler(console)

# Debug file: detailed, all levels
debug_file = FileHandler("debug.log", mode='a', level=LogLevel.DEBUG)
debug_file.setFormatter(Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
    include_source=True  # Include file:line:function
))
ASCIIColors.add_handler(debug_file)

# Rotating file: auto-rotate when size exceeded
rotating = RotatingFileHandler(
    "app.log",
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5,          # Keep 5 backups: app.log, app.log.1, ..., app.log.5
    level=LogLevel.INFO
)
rotating.setFormatter(JSONFormatter(
    include_fields=["timestamp", "levelname", "name", "message", "pathname", "lineno"]
))
ASCIIColors.add_handler(rotating)

# Set global level
ASCIIColors.set_log_level(LogLevel.DEBUG)

# Usage
logger = getLogger("MyApp")
logger.info("Application started")  # Goes to all handlers
logger.debug("Debug info")          # Goes to debug_file only
```

### Context-Aware Logging

```python
from ascii_colors import ASCIIColors, Formatter

# ============================================
# Persistent Context
# ============================================

# Set once, included in all subsequent logs
ASCIIColors.set_context(
    app_name="MyService",
    app_version="1.2.3",
    environment="production"
)

# All logs now include these fields
formatter = Formatter(
    "[{asctime}] {app_name}/{app_version} [{levelname}] {message}",
    style='{'
)

# ============================================
# Temporary Context (Context Manager)
# ============================================

# Context automatically restored after block
with ASCIIColors.context(
    request_id="req-abc-123",
    user_id="user-456",
    trace_id="trace-xyz"
):
    # All logs in this block include request_id, user_id, trace_id
    # Plus the previously set app_name, app_version, environment
    ASCIIColors.info("Processing request")
    ASCIIColors.debug("Request details: ...")
    try:
        process()
    except Exception as e:
        ASCIIColors.error("Request failed: %s", e)

# After block: request_id, user_id, trace_id no longer included
# But app_name, app_version, environment still present
ASCIIColors.info("Cleanup complete")

# ============================================
# Thread-Local Context
# ============================================

import threading

def worker(thread_id):
    # Each thread has its own isolated context
    ASCIIColors.set_context(thread=thread_id, worker_type="background")
    ASCIIColors.info("Worker starting")  # Includes this thread's context
    
    with ASCIIColors.context(task_id=f"task-{thread_id}"):
        do_work()
        ASCIIColors.info("Task complete")  # Includes thread + task context
    
    ASCIIColors.info("Worker done")  # Back to thread context only

# Spawn workers
for i in range(5):
    threading.Thread(target=worker, args=(i,)).start()
```

### Formatters in Detail

```python
from ascii_colors import Formatter, JSONFormatter, LogLevel

# ============================================
# Formatter Styles
# ============================================

# Percent style (like standard logging)
percent_fmt = Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    style='%'
)

# Brace style (Python str.format)
brace_fmt = Formatter(
    "{asctime} [{level_name:>8}] {name}: {message}",
    datefmt="%H:%M:%S",
    style='{'
)

# With source information
source_fmt = Formatter(
    "[{func_name}:{lineno}] {message}",
    include_source=True,
    style='{'
)

# ============================================
# JSON Formatter
# ============================================

# All fields
json_all = JSONFormatter()  # Includes all standard fields

# Selected fields only
json_select = JSONFormatter(
    include_fields=[
        "timestamp", "levelname", "name", "message",
        "pathname", "lineno", "funcName", "thread", "process"
    ]
)

# Custom date format
json_iso = JSONFormatter(
    include_fields=["timestamp", "levelname", "message"],
    datefmt="iso"  # ISO 8601 format
)

# Pretty-printed (for development)
json_pretty = JSONFormatter(
    include_fields=["levelname", "name", "message"],
    json_indent=2
)
```

### Advanced Handler Configuration

```python
from ascii_colors import (
    ASCIIColors, LogLevel,
    ConsoleHandler, FileHandler, RotatingFileHandler,
    Formatter, JSONFormatter
)
import sys

# ============================================
# Handler-Specific Levels
# ============================================

# Console: only warnings and above
console = ConsoleHandler(stream=sys.stdout, level=LogLevel.WARNING)
console.setFormatter(Formatter(
    "{level_name}: {message}",
    style='{'
))

# Debug file: everything
debug_file = FileHandler("debug.log", level=LogLevel.DEBUG)
debug_file.setFormatter(Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
))

ASCIIColors.add_handler(console)
ASCIIColors.add_handler(debug_file)
ASCIIColors.set_log_level(LogLevel.DEBUG)  # Global level

# Result:
# logger.debug("msg")  # Only to debug.log
# logger.warning("msg")  # To both console and debug.log

# ============================================
# Multiple Formatters Example
# ============================================

# Human-readable console output
human = ConsoleHandler(sys.stdout, level=LogLevel.INFO)
human.setFormatter(Formatter(
    "{level_name:>8} | {message}",
    style='{'
))

# Structured JSON for log aggregation
machine = FileHandler("events.jsonl", level=LogLevel.INFO)
machine.setFormatter(JSONFormatter(
    include_fields=["timestamp", "level", "name", "message", "context"]
))

# Detailed debug log
detailed = FileHandler("verbose.log", level=LogLevel.DEBUG)
detailed.setFormatter(Formatter(
    "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
    datefmt="%H:%M:%S",
    include_source=True
))

ASCIIColors.add_handler(human)
ASCIIColors.add_handler(machine)
ASCIIColors.add_handler(detailed)
```

---

## 🎨 Complete Color & Style Reference

All constants available as `ASCIIColors.<name>` or direct import:

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
| `style_reverse` | `\u001b[7m` | Reverse video (swap fg/bg) |
| `style_hidden` | `\u001b[8m` | Hidden/Concealed |
| `style_strikethrough` | `\u001b[9m` | Strikethrough |

### Foreground Colors (Standard)
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

### Combining Styles

```python
from ascii_colors import ASCIIColors

# Multiple styles
alert = (
    ASCIIColors.style_bold +
    ASCIIColors.style_underline +
    ASCIIColors.color_bright_red
)
ASCIIColors.print("CRITICAL ALERT", color=alert)

# Full styling
ASCIIColors.print(
    " Success ",
    color=ASCIIColors.color_black,
    background=ASCIIColors.color_bg_bright_green,
    style=ASCIIColors.style_bold
)
```

---

## 🔄 Migration Guides

### From Standard `logging` Module

```python
# Before (standard logging)
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("myapp")

# After (ascii_colors) — identical API!
import ascii_colors as logging  # Just change the import!

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("myapp")

# Additional features available:
logger = logging.getLogger("myapp")
logger.addHandler(logging.FileHandler("app.jsonl"))  # Add file output
# etc.
```

### From `colorama`

```python
# Before (colorama)
from colorama import init, Fore, Back, Style
init()

print(Fore.RED + "Error" + Style.RESET_ALL)
print(Back.GREEN + Fore.BLACK + "Success" + Style.RESET_ALL)

# After (ascii_colors) — more intuitive, no init needed!
from ascii_colors import ASCIIColors

ASCIIColors.red("Error")  # Auto-reset
ASCIIColors.print(
    "Success",
    color=ASCIIColors.color_black,
    background=ASCIIColors.color_bg_green
)

# Plus: backgrounds, styles, bright colors, logging, progress bars, etc.
```

### From `tqdm`

```python
# Before (tqdm)
from tqdm import tqdm
import time

for i in tqdm(range(100), desc="Processing"):
    time.sleep(0.01)

# After (ascii_colors) — similar API, more styling!
from ascii_colors import ProgressBar
import time

for i in ProgressBar(range(100), desc="Processing", color=ASCIIColors.color_cyan):
    time.sleep(0.01)

# Additional: custom chars, colors, styles, thread-safe, manual control
```

### From `questionary`

```python
# Before (questionary)
import questionary

name = questionary.text("Name?").ask()
proceed = questionary.confirm("Continue?").ask()

# After (ascii_colors) — drop-in replacement!
from ascii_colors import questionary  # Just change the import!

name = questionary.text("Name?").ask()
proceed = questionary.confirm("Continue?").ask()

# Plus: enhanced styling, validation, forms, better error handling
```

---

## 📚 Documentation & Resources

- **[Full Documentation](https://parisneo.github.io/ascii_colors/)** — Complete API reference, guides, and examples
- **[PyPI Package](https://pypi.org/project/ascii-colors/)** — Release history, statistics, and installation
- **[GitHub Repository](https://github.com/ParisNeo/ascii_colors)** — Source code, issues, and contributions
- **[Changelog](CHANGELOG.md)** — Detailed version history and migration notes

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
- For older Windows, colors should still work in modern terminal emulators (Windows Terminal, VS Code terminal)
- Legacy CMD may require `colorama` installation: `pip install colorama`

### Progress bar width issues with wide characters
```bash
pip install wcwidth  # For accurate emoji/CJK character width detection
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