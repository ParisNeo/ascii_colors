# ASCIIColors: Colorful Logging & Terminal Utilities Made Simple 🎨

[![PyPI version](https://img.shields.io/pypi/v/ascii_colors.svg)](https://pypi.org/project/ascii-colors/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/ascii_colors.svg)](https://pypi.org/project/ascii-colors/)
[![PyPI license](https://img.shields.io/pypi/l/ascii_colors.svg)](https://github.com/ParisNeo/ascii_colors/blob/main/LICENSE)
[![PyPI downloads](https://img.shields.io/pypi/dm/ascii_colors.svg)](https://pypi.org/project/ascii-colors/)
<!-- Optional: Add build status if you set up CI -->
<!-- [![Build Status](https://github.com/ParisNeo/ascii_colors/actions/workflows/your-ci-workflow.yml/badge.svg)](https://github.com/ParisNeo/ascii_colors/actions/workflows/your-ci-workflow.yml) -->
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation Status](https://readthedocs.org/projects/ascii_colors/badge/?version=latest)](https://parisneo.github.io/ascii_colors/) 

Tired of bland terminal output? Need powerful logging without the boilerplate? **ASCIIColors** is your solution!

It combines beautiful, effortless **color printing** with a **flexible, modern logging system**. Now featuring a compatibility layer mimicking Python's standard `logging` module, it makes transitioning or integrating easier than ever. Plus, it includes handy **terminal utilities** like spinners and highlighting.

---

## 🤔 Why Choose ASCIIColors?

*   **🎨 Dual Approach:** Offers both simple, direct color printing *and* a structured logging system.
*   **✨ Easy Logging:** Get colored, leveled logging to the console (`stderr` by default) with minimal setup using `basicConfig`.
*   **🐍 `logging` Compatibility:** Use familiar functions like `getLogger()`, `basicConfig()`, level constants (`INFO`, `WARNING`), and handlers (`StreamHandler`, `FileHandler`, `RotatingFileHandler`) for a smooth transition or integration.
*   **💪 Flexible & Powerful:** Configure multiple handlers (console, file, rotating), custom formats (including JSON), thread-local context, and fine-grained level control.
*   **🌈 Rich Styling:** Provides a wide range of ANSI color and style constants for direct printing.
*   **🛠️ Utilities Included:** Comes with `execute_with_animation` spinner, `highlight` utility, and easy exception tracing.
*   **✅ Backward Compatible:** Existing code using direct `ASCIIColors.red()`, `ASCIIColors.print()` etc. continues to work as direct terminal output, separate from the logging system.

---

## ✨ Features

*   🌈 **Direct Colored Output:** Print text directly to the terminal in various foreground/background colors and styles (`bold`, `underline`, `italic`, etc.) using simple static methods.
*   🪵 **Robust Logging System:**
    *   Standard Levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
    *   `logging`-like API: Use `getLogger()`, `basicConfig()`, `logger.info()`, etc.
    *   Multiple Handlers: Log to console (`StreamHandler`), files (`FileHandler`), rotating files (`RotatingFileHandler`). Add custom handlers inheriting from `Handler`.
    *   Customizable Formatters: Control log layout using `%` or `{` style formats. Includes timestamps, levels, source info (file/line/func), logger names, thread info, and custom context. Built-in `JSONFormatter`.
    *   Global & Handler Levels: Filter messages globally and per-handler.
*   🧠 **Thread-Local Context:** Easily add contextual information (e.g., request ID, user ID) to logs within a specific thread using `ASCIIColors.set_context` or `ASCIIColors.context()`.
*   📄 **File Logging & Rotation:** Built-in `FileHandler` and `RotatingFileHandler` (in `ascii_colors.handlers`) with standard options (`mode`, `maxBytes`, `backupCount`).
*   📜 **JSON Logging:** Output structured logs with the `JSONFormatter` for easy machine parsing.
*   🛠️ **Console Utilities:**
    *   `execute_with_animation`: Display a spinner while a function runs.
    *   `highlight`: Emphasize keywords or lines in direct output.
    *   `multicolor`: Print text segments with different colors on one line directly.
    *   `trace_exception`: Easily log formatted exception tracebacks via the logging system.
*   🤝 **Two Ways to Log:** Use the familiar `getLogger()` API *or* the original `ASCIIColors.info()`, etc. methods. Both feed into the same underlying handler/formatter system managed globally by `ASCIIColors`.

---

## 🚀 Installation

```bash
pip install ascii_colors
```

---

## 🏁 Quick Start

**Option 1: Logging (Recommended for structured logs)**

```python
# Use ascii_colors with a logging-like interface
import ascii_colors as logging # Use alias for familiarity
from pathlib import Path

# Configure logging (only runs once unless force=True)
log_file = Path("my_app.log")
logging.basicConfig(
    level=logging.DEBUG, # Set the root level
    # Use standard %-style formatting
    format='%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    # Log to both console (stderr by default) and a file
    # basicConfig handles one handler; add file handler manually or use handlers=[]
    # Let's add file handler manually for this example:
    # handlers=[logging.StreamHandler(), logging.FileHandler(log_file)] # Alternative
)
# Add file handler separately if not using handlers=[]
file_handler = logging.FileHandler(log_file, mode='w')
file_handler.setFormatter(logging.Formatter('%(asctime)s|%(levelname)s|%(message)s')) # Different format for file
logging.getLogger().addHandler(file_handler) # Add to root logger

# Get a logger instance
logger = logging.getLogger("MyApp")

# Log messages
logger.info("Application starting...")
logger.debug("Configuration loaded.")
logger.warning("Settings value missing, using default.")
user = "Alice"
logger.info("User '%s' logged in.", user) # Use %-args

try:
    result = 10 / 0
except ZeroDivisionError:
    logger.error("Calculation failed!", exc_info=True) # Log error with traceback

print(f"\nCheck console output (stderr) and '{log_file}'")
```

**Option 2: Direct Printing (For simple, immediate styled output)**

```python
from ascii_colors import ASCIIColors

# These print directly to stdout and bypass the logging system
ASCIIColors.red("This is an urgent error message.")
ASCIIColors.green("Operation completed successfully!")
ASCIIColors.yellow("Warning: Disk space low.")
ASCIIColors.bold("This is important!", color=ASCIIColors.color_bright_white)
ASCIIColors.underline("Underlined text.", color=ASCIIColors.color_cyan)
ASCIIColors.print_with_bg(
    " Black text on Orange background ",
    color=ASCIIColors.color_black,
    background=ASCIIColors.bg_orange
)
```

---

## 📚 Core Concepts: Direct Print vs Logging

`ascii_colors` provides two distinct ways to output styled text:

1.  **Direct Print Methods (`ASCIIColors.red`, `print`, `bold`, `bg_red`, etc.):**
    *   These methods print **directly** to the console (`sys.stdout` by default, or a specified stream) using `builtins.print`.
    *   They **bypass the logging system** entirely (no handlers, formatters, levels, context involved).
    *   Color and style are applied directly as specified in the method call.
    *   Use these for simple, immediate, styled terminal output when logging features aren't needed (e.g., user prompts, status indicators, decorative output).

2.  **Logging System (`basicConfig`, `getLogger`, `logger.info`, `ASCIIColors.info`, Handlers, Formatters):**
    *   This provides structured, leveled logging.
    *   Messages are processed by **Handlers** (e.g., `StreamHandler`, `FileHandler`) which direct output to destinations (console, files).
    *   Output format is controlled by **Formatters** (e.g., `Formatter`, `JSONFormatter`), allowing timestamps, levels, source info, context variables, etc.
    *   Messages are filtered by **global and handler levels**.
    *   Console output color is typically determined by the **log level** (via `ConsoleHandler` using `_level_colors`).
    *   You can interact with the logging system via:
        *   **`logging`-like API:** `import ascii_colors as logging`, `logging.getLogger()`, `logging.basicConfig()`. Recommended for new projects or easy integration.
        *   **`ASCIIColors` Class Methods:** `ASCIIColors.info()`, `ASCIIColors.warning()`, `ASCIIColors.add_handler()`. Provided for backward compatibility.
    *   Both logging APIs control the *same underlying global logging state* (handlers, level) managed by the `ASCIIColors` class.

**Utilities** like `highlight`, `multicolor`, and `execute_with_animation` use **direct printing**. The `trace_exception` utility uses the **logging system** (`ASCIIColors.error`).

---

## 🛠️ Usage & Examples

### 1. Direct Printing

```python
from ascii_colors import ASCIIColors

# Simple colors
ASCIIColors.red("Error!")
ASCIIColors.green("Success!")
ASCIIColors.blue("Information")

# Styles
ASCIIColors.bold("Bold Text")
ASCIIColors.underline("Underlined Text", color=ASCIIColors.color_yellow)
ASCIIColors.italic("Italic Magenta", color=ASCIIColors.color_magenta)
ASCIIColors.strikethrough("Strike")

# Backgrounds
ASCIIColors.bg_yellow("Black text on Yellow", color=ASCIIColors.color_black)
ASCIIColors.print_with_bg(
    " White text on Red BG ",
    color=ASCIIColors.color_white,
    background=ASCIIColors.bg_red
)

# Combine styles and colors
ASCIIColors.print(
    " Bold, Underlined, Bright Red ",
    color=ASCIIColors.color_bright_red,
    style=ASCIIColors.style_bold + ASCIIColors.style_underline
)

# Multicolor
ASCIIColors.multicolor(
    ["File: ", "config.yaml", " | Status: ", "LOADED"],
    [ASCIIColors.color_white, ASCIIColors.color_cyan, ASCIIColors.color_white, ASCIIColors.color_green]
)

# Highlight
log_line = "INFO: User 'test' logged out."
ASCIIColors.highlight(log_line, ["INFO", "test", "logged out"],
                      highlight_color=ASCIIColors.color_bright_yellow)
```

### 2. Logging System Setup

**a) Using `basicConfig()` (Simple Setup)**

```python
import ascii_colors as logging # Alias for familiarity
from pathlib import Path

# Log INFO and above to stderr with default format
# logging.basicConfig(level=logging.INFO)

# Log DEBUG and above to a file, with custom format
log_file = Path("app_basic.log")
logging.basicConfig(
    level=logging.DEBUG,
    filename=log_file,
    filemode='w', # Overwrite
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("MySimpleApp")
logger.debug("This goes to the file.")
# Need to add a StreamHandler manually if you want console output too
# logger.addHandler(logging.StreamHandler(level=logging.INFO, stream=sys.stdout))
# logger.info("This now goes to file and stdout.")
```

**b) Manual Setup (More Control)**

```python
from ascii_colors import (
    ASCIIColors, LogLevel, ConsoleHandler, FileHandler,
    RotatingFileHandler, JSONFormatter, Formatter, handlers
)
import sys
from pathlib import Path

# Reset global state if needed (e.g., in tests or re-configuration)
ASCIIColors.clear_handlers()
ASCIIColors._basicConfig_called = False # If mixing with basicConfig

# Set global level (filters messages *before* handlers see them)
ASCIIColors.set_log_level(LogLevel.DEBUG)

# 1. Console Handler (Colored, Simple Format, INFO+) -> stdout
console_fmt = Formatter("[{levelname}] {message}", style='{')
console_handler = ConsoleHandler(level=LogLevel.INFO, stream=sys.stdout, formatter=console_fmt)
ASCIIColors.add_handler(console_handler)

# 2. File Handler (Detailed Format, DEBUG+) -> app_manual.log
log_file = Path("app_manual.log")
if log_file.exists(): log_file.unlink() # Clear previous
file_fmt = Formatter(
    fmt="%(asctime)s|%(levelname)-8s|%(name)s:%(lineno)d|%(message)s",
    datefmt="%H:%M:%S",
    style='%',
    include_source=True # Adds overhead but includes line number
)
file_handler = FileHandler(log_file, level=LogLevel.DEBUG, formatter=file_fmt)
ASCIIColors.add_handler(file_handler)

# 3. Rotating File Handler (JSON Format, WARNING+) -> service.log
service_log = Path("service.log")
json_fmt = JSONFormatter(include_fields=["timestamp", "levelname", "name", "message", "custom_data"])
# Use handlers namespace for clarity
rotating_handler = handlers.RotatingFileHandler(
    service_log,
    maxBytes=1024 * 100, # 100 KB
    backupCount=3,
    level=LogLevel.WARNING,
    formatter=json_fmt
)
ASCIIColors.add_handler(rotating_handler)

# --- Now log messages ---
logger = getLogger("ManualSetup") # Use getLogger

logger.debug("This goes only to app_manual.log")
logger.info("This goes to console and app_manual.log")
logger.warning("This goes to console, app_manual.log, and service.log (as JSON)", extra={'custom_data': 123})
ASCIIColors.error("Error via ASCIIColors API - goes to all handlers >= ERROR") # Use direct API too
```

### 3. Logging Messages

```python
import ascii_colors as logging

logging.basicConfig(level=logging.DEBUG) # Basic setup for demo
logger = logging.getLogger("App")

# Simple messages
logger.debug("Debugging connection...")
logger.info("User logged in.")
logger.warning("Configuration value not found.")
logger.error("Failed to process data.")
logger.critical("System shutting down!")

# Messages with %-style arguments
user_id = 123
file_path = "data.csv"
logger.info("Processing file '%s' for user %d", file_path, user_id)

# Logging exceptions
try:
    x = {}
    y = x['key']
except KeyError:
    logger.error("Missing key in dictionary", exc_info=True) # Option 1: exc_info=True
    # logger.exception("Missing key in dictionary") # Option 2: logger.exception()

# Using trace_exception utility
from ascii_colors import trace_exception
try:
    z = 1 / 0
except ZeroDivisionError as e:
    trace_exception(e) # Logs error with traceback using ASCIIColors.error

# Using ASCIIColors direct logging methods (feeds into same handlers)
from ascii_colors import ASCIIColors
ASCIIColors.info("This info message uses the direct API.")
```

### 4. Context Management

Add thread-local context to logs automatically.

```python
from ascii_colors import ASCIIColors, ConsoleHandler, Formatter, getLogger
import threading
import time
import sys

# Setup a handler that uses context variables
fmt = Formatter("[{asctime}] ({name}) (Req:{request_id}|User:{user}) {message}", style='{', datefmt='%H:%M:%S')
handler = ConsoleHandler(formatter=fmt, stream=sys.stdout)
ASCIIColors.clear_handlers() # Start clean
ASCIIColors.add_handler(handler)
ASCIIColors.set_log_level(DEBUG)

logger = getLogger("WebApp")

def process_request(req_id, user):
    # Use context manager to set context for this thread/task
    with ASCIIColors.context(request_id=req_id, user=user):
        logger.info("Processing started.")
        time.sleep(0.1)
        if user == "admin":
            logger.warning("Admin request detected.")
        logger.info("Processing finished.")

# Simulate concurrent requests
t1 = threading.Thread(target=process_request, args=("req-001", "alice"))
t2 = threading.Thread(target=process_request, args=("req-002", "admin"))

t1.start(); t2.start()
t1.join(); t2.join()

# Example Output:
# [10:30:01] (WebApp) (Req:req-001|User:alice) Processing started.
# [10:30:01] (WebApp) (Req:req-002|User:admin) Processing started.
# [10:30:01] (WebApp) (Req:req-002|User:admin) Admin request detected.
# [10:30:01] (WebApp) (Req:req-001|User:alice) Processing finished.
# [10:30:01] (WebApp) (Req:req-002|User:admin) Processing finished.
```

### 5. Utilities

```python
import time
from ascii_colors import ASCIIColors

# --- Animation ---
def simulate_work(duration):
    # Logs within the task will use the global logging config
    ASCIIColors.info(f">> Starting task (will take {duration}s)...")
    time.sleep(duration)
    # raise ValueError("Failed!") # Uncomment to see failure case
    return "Data processed!"

try:
    result = ASCIIColors.execute_with_animation(
        "Processing data...", simulate_work, 1.5, color=ASCIIColors.color_cyan
    )
    # The execute_with_animation uses DIRECT PRINT for the spinner/status line
    # Use direct print (like success/fail) for its result
    ASCIIColors.success(f"Work result: {result}")
except Exception as e:
    ASCIIColors.fail(f"Work failed: {e}")

# --- Highlighting (Direct Print) ---
log_line = "ERROR: Connection failed to host 192.168.1.100"
ASCIIColors.highlight(log_line, ["ERROR", "192.168.1.100"],
                      color=ASCIIColors.color_white,
                      highlight_color=ASCIIColors.bg_red) # Highlight with background
```

---

## 🌈 Available Colors and Styles

Use these constants with `ASCIIColors.print()`, style methods (`bold()`, `bg_red()`, etc.), or `multicolor()`.

*   **Reset:** `ASCIIColors.color_reset`
*   **Styles:** `style_bold`, `style_dim`, `style_italic`, `style_underline`, `style_blink`, `style_reverse`, `style_hidden`, `style_strikethrough`
*   **Foreground (Regular):** `color_black`, `color_red`, `color_green`, `color_yellow`, `color_blue`, `color_magenta`, `color_cyan`, `color_white`, `color_orange`
*   **Foreground (Bright):** `color_bright_black`, `color_bright_red`, `color_bright_green`, `color_bright_yellow`, `color_bright_blue`, `color_bright_magenta`, `color_bright_cyan`, `color_bright_white`
*   **Background (Regular):** `bg_black`, `bg_red`, `bg_green`, `bg_yellow`, `bg_blue`, `bg_magenta`, `bg_cyan`, `bg_white`, `bg_orange`
*   **Background (Bright):** `bg_bright_black`, `bg_bright_red`, `bg_bright_green`, `bg_bright_yellow`, `bg_bright_blue`, `bg_bright_magenta`, `bg_bright_cyan`, `bg_bright_white`

---

## 💡 Use Cases

`ascii_colors` is great for:

*   **CLI Applications:** Clear, colorful status updates, progress, errors.
*   **Web Service Backends:** Structured logging (JSON), request tracing with context, readable debug logs.
*   **Scripts & Automation:** Simple setup for logging progress, results, errors to console/files.
*   **Development & Debugging:** Quickly add detailed, leveled logs without complex setup.
*   **Any application where readable, informative, and visually distinct output improves developer productivity or user experience.**

---

## 🤝 Contributing

Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines.

---

## 📜 License

ASCIIColors is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.