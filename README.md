# ASCIIColors: Colorful Logging & Terminal Utilities Made Simple 🎨

[![PyPI version](https://img.shields.io/pypi/v/ascii_colors.svg)](https://pypi.org/project/ascii-colors/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/ascii_colors.svg)](https://pypi.org/project/ascii-colors/)
[![PyPI license](https://img.shields.io/pypi/l/ascii_colors.svg)](https://github.com/ParisNeo/ascii_colors/blob/main/LICENSE)
[![PyPI downloads](https://img.shields.io/pypi/dm/ascii_colors.svg)](https://pypi.org/project/ascii-colors/)
<!-- Optional: Add build status if you set up CI -->
<!-- [![Build Status](https://github.com/ParisNeo/ascii_colors/actions/workflows/your-ci-workflow.yml/badge.svg)](https://github.com/ParisNeo/ascii_colors/actions/workflows/your-ci-workflow.yml) -->
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Tired of bland terminal output? Need powerful logging without the boilerplate? **ASCIIColors** is your solution!

It combines beautiful, effortless **color printing** with a **flexible, modern logging system** inspired by standard `logging` but designed for simplicity and developer experience. Plus, it includes handy **terminal utilities** like spinners and highlighting.

---

## 🤔 Why Choose ASCIIColors Over Standard `logging`?

Python's built-in `logging` is powerful but can feel verbose for many common tasks, especially when you want easy, colorful console output. ASCIIColors aims to be the sweet spot:

*   **✨ Dead Simple Start:** Get colorful, leveled logging to the console *immediately* with zero configuration.
*   **🎨 Color First:** Beautiful, configurable ANSI colors are a core feature, not an afterthought requiring complex setup.
*   **🔧 Modern & Intuitive:** Features like thread-local context management feel more Pythonic and less boilerplatey than standard `logging`'s `extra` dictionary.
*   **🔌 Batteries Included:** Comes with useful utilities like `execute_with_animation` and `highlight` that you won't find in the standard library.
*   **💪 Flexible Power:** Scales gracefully. Need file logging, JSON output, log rotation, or custom formats? ASCIIColors provides the familiar Handler/Formatter pattern without the initial complexity overload.
*   **🕊️ Smooth Transition:** Still offers simple `print`, `red`, `green` methods for quick output or backward compatibility, now smartly integrated into the logging system.

**In short: Get the power you need, with the simplicity and beauty you want.**

---

## ✨ Features

*   🌈 **Effortless Colored Output:** Print text in various colors and styles with simple static methods.
*   🪵 **Robust Logging System:**
    *   Standard Levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`.
    *   Multiple Handlers: Log to console (`stdout`/`stderr`), files, rotating files. Add as many as you need!
    *   Customizable Formatters: Control log message layout, including timestamps, source info (file/line/func), and custom data. Built-in JSON formatter!
    *   Global & Handler Levels: Filter messages globally and per-handler.
*   🧠 **Thread-Local Context:** Easily add contextual information (e.g., request ID, user ID) to all subsequent logs within a thread using `set_context` or a `with` statement.
*   📄 **File Logging & Rotation:** Built-in `FileHandler` and `RotatingFileHandler` for persistent logs.
*   📜 **JSON Logging:** Output structured logs with the `JSONFormatter` for easy machine parsing.
*   🛠️ **Console Utilities:**
    *   `execute_with_animation`: Display a spinner while a function runs.
    *   `highlight`: Emphasize keywords or lines in output.
    *   `multicolor`: Print text segments with different colors on one line.
    *   `trace_exception`: Easily log formatted exception tracebacks.
*    Backward Compatibility: Original simple print methods (`print`, `red`, etc.) still work, integrated with the new logging core.

---

## 🚀 Installation

```bash
pip install ascii_colors
```

---

## 🏁 Quick Start: Instant Colorful Logging

```python
from ascii_colors import ASCIIColors, LogLevel

# Logs INFO and above to console by default with colors!
ASCIIColors.info("Processing started...")
ASCIIColors.warning("Configuration value missing, using default.")
ASCIIColors.debug("This won't show by default (level is INFO).")

# Set level to see more
ASCIIColors.set_log_level(LogLevel.DEBUG)
ASCIIColors.debug("Detailed step: Loaded module X.")

# Log errors, optionally with extra context
try:
    data = {}
    val = data['required']
except KeyError as e:
    # Log error message and include formatted traceback
    ASCIIColors.error("Missing required key in data", exc_info=True, data_keys=list(data.keys()))
    # Output (Example):
    # [ERROR][2023-10-28 10:30:00] Missing required key in data {'data_keys': []}
    # Traceback (most recent call last):
    #   File "...", line X, in <module>
    #     val = data['required']
    # KeyError: 'required'
```

---

## 📚 Advanced Usage & Examples

### 1. Multiple Handlers (Console & File)

Log everything to console, but only INFO and above to a file with a different format.

```python
from ascii_colors import ASCIIColors, LogLevel, ConsoleHandler, FileHandler, Formatter
import sys

# Start fresh if needed
ASCIIColors.clear_handlers()
ASCIIColors.set_log_level(LogLevel.DEBUG) # Allow all levels globally

# Console Handler (Default Colors, Simple Format)
console_handler = ConsoleHandler(stream=sys.stdout, level=LogLevel.DEBUG)
console_handler.set_formatter(Formatter("{level_name}: {message}")) # Simple format
ASCIIColors.add_handler(console_handler)

# File Handler (Detailed Format, No Colors)
file_formatter = Formatter(
    fmt="[{datetime}] {level_name:<8} [{func_name}] - {message}",
    datefmt="%Y-%m-%d %H:%M:%S",
    include_source=True # Include function name
)
file_handler = FileHandler("app.log", level=LogLevel.INFO, formatter=file_formatter)
ASCIIColors.add_handler(file_handler)

# --- Logging ---
ASCIIColors.debug("Connecting to database...") # Console only
ASCIIColors.info("User 'alice' logged in.")   # Console & File
ASCIIColors.error("Failed to process record 123.", record_id=123) # Console & File
```

### 2. Rotating Log Files

Keep log files from growing indefinitely.

```python
from ascii_colors import ASCIIColors, LogLevel, RotatingFileHandler, Formatter

# Rotate log file when it reaches 2MB, keep 3 backup files
rotating_handler = RotatingFileHandler(
    filename="service.log",
    maxBytes=2 * 1024 * 1024, # 2 MB
    backupCount=3,
    level=LogLevel.INFO,
    formatter=Formatter("[{datetime}] {level_name}: {message}") # Simple file format
)
ASCIIColors.add_handler(rotating_handler) # Add alongside console handler

# ... log many messages ...
for i in range(50000):
     ASCIIColors.info(f"Processing item {i}")
# service.log will rotate into service.log.1, .2, .3 etc.
```

### 3. JSON Logging for Analysis

Output structured logs, perfect for log aggregation systems.

```python
from ascii_colors import ASCIIColors, LogLevel, FileHandler, JSONFormatter

json_formatter = JSONFormatter(
    # Define fields to include (or None for all standard + context + kwargs)
    include_fields=["datetime", "level_name", "message", "request_id", "user", "duration_ms"],
    datefmt="iso" # Use ISO8601 timestamps
)
json_handler = FileHandler("events.jsonl", level=LogLevel.INFO, formatter=json_formatter)
ASCIIColors.add_handler(json_handler)

# Log events with custom data
ASCIIColors.info(
    "API Request Received",
    request_id="xyz-789",
    user="bob",
    endpoint="/api/data"
)
ASCIIColors.info(
    "API Request Completed",
    request_id="xyz-789",
    user="bob",
    endpoint="/api/data",
    status_code=200,
    duration_ms=150
)

# Example line in events.jsonl:
# {"datetime": "2023-10-28T11:00:01.123456", "level_name": "INFO", "message": "API Request Completed", "request_id": "xyz-789", "user": "bob", "duration_ms": 150}
```

### 4. Context Management for Richer Logs

Automatically add context to logs within a specific scope (e.g., a web request).

```python
from ascii_colors import ASCIIColors, Formatter

# Assume console handler uses this formatter
formatter = Formatter("[{datetime:%H:%M:%S}] {level_name} (Req:{request_id}|User:{user_id}) - {message}")
# Apply formatter to handler (e.g., the default console handler)
if ASCIIColors._handlers:
    ASCIIColors._handlers[0].set_formatter(formatter)

def handle_request(request_id, user_id):
    # Set context for this request thread
    with ASCIIColors.context(request_id=request_id, user_id=user_id):
        ASCIIColors.info("Request processing started.")
        # ... do work ...
        if user_id == "admin":
            ASCIIColors.warning("Admin action performed.")
        # ... more work ...
        ASCIIColors.info("Request processing finished.")
    # Context is automatically cleared outside the 'with' block

# Simulate handling requests
handle_request("req-001", "alice")
handle_request("req-002", "admin")

# Example Console Output:
# [11:15:30] INFO (Req:req-001|User:alice) - Request processing started.
# [11:15:30] INFO (Req:req-001|User:alice) - Request processing finished.
# [11:15:30] INFO (Req:req-002|User:admin) - Request processing started.
# [11:15:30] WARNING (Req:req-002|User:admin) - Admin action performed.
# [11:15:30] INFO (Req:req-002|User:admin) - Request processing finished.
```

### 5. Easy Exception Tracing

Log exceptions with full tracebacks effortlessly.

```python
from ascii_colors import trace_exception, ASCIIColors

try:
    x = 1 / 0
except Exception as e:
    # Option 1: Use the utility function (logs via ASCIIColors.error)
    trace_exception(e)

    # Option 2: Log manually with exc_info=True or exc_info=e
    # ASCIIColors.error("An error occurred during calculation", exc_info=e)
```

### 6. Legacy Color Printing (Integrated)

Still need quick, direct color output? The original methods work, now logging at INFO level.

```python
from ascii_colors import ASCIIColors

ASCIIColors.red("This is an urgent message.") # Logs as INFO, colored red on console
ASCIIColors.green("Task completed successfully.") # Logs as INFO, colored green
ASCIIColors.bold("Important Title", color=ASCIIColors.color_yellow) # Logs as INFO, bold yellow
```

### 7. Console Utilities

Go beyond logging with built-in helpers:

```python
import time
from ascii_colors import ASCIIColors

# --- Animation ---
def simulate_work(duration):
    time.sleep(duration)
    # raise ValueError("Failed!") # Uncomment to see failure case
    return "Data processed!"

result = ASCIIColors.execute_with_animation(
    "Processing...", simulate_work, 2, color=ASCIIColors.color_cyan
)
ASCIIColors.success(f"Work result: {result}") # Prints success message


# --- Highlighting ---
log_line = "INFO: User 'testuser' logged in from 192.168.1.100"
ASCIIColors.highlight(log_line, ["INFO", "testuser", "192.168.1.100"],
                      color=ASCIIColors.color_white,
                      highlight_color=ASCIIColors.color_bright_yellow)


# --- Multicolor ---
ASCIIColors.multicolor(
    ["Status: ", "RUNNING", " | Progress: ", "75%"],
    [ASCIIColors.color_white, ASCIIColors.color_green, ASCIIColors.color_white, ASCIIColors.color_cyan]
)
```

---

## 🌈 Available Colors and Styles

Use these constants with `ASCIIColors.print()`, `ASCIIColors.bold()`, etc., or directly with formatters if needed.

```python
# --- Reset ---
ASCIIColors.color_reset

# --- Regular Colors ---
ASCIIColors.color_black, ASCIIColors.color_red, ASCIIColors.color_green,
ASCIIColors.color_yellow, ASCIIColors.color_blue, ASCIIColors.color_magenta,
ASCIIColors.color_cyan, ASCIIColors.color_white, ASCIIColors.color_orange

# --- Bright Colors ---
ASCIIColors.color_bright_black, ASCIIColors.color_bright_red, ASCIIColors.color_bright_green,
ASCIIColors.color_bright_yellow, ASCIIColors.color_bright_blue, ASCIIColors.color_bright_magenta,
ASCIIColors.color_bright_cyan, ASCIIColors.color_bright_white, ASCIIColors.color_bright_orange

# --- Styles ---
ASCIIColors.style_bold, ASCIIColors.style_underline
```

---

## 💡 Use Cases

ASCIIColors is great for:

*   **CLI Applications:** Providing clear, colorful status updates, progress, and error messages.
*   **Web Service Backends:** Logging requests with context (request ID, user), outputting structured logs (JSON) for analysis, and human-readable logs for debugging.
*   **Scripts & Automation:** Simple setup for logging script progress, results, and errors to console and/or files.
*   **Development & Debugging:** Quickly adding detailed, leveled logs with context without complex setup.
*   **Any application where readable, informative, and visually distinct logs improve developer productivity or user experience.**

---

## Key Concepts: Logging vs. Direct Printing

ASCIIColors now clearly separates its functionality:

1.  **Logging Methods (`debug`, `info`, `warning`, `error`):**
    *   These methods use the **logging system**.
    *   Output is processed by **Handlers** (Console, File, RotatingFile, etc.).
    *   Message format is controlled by **Formatters** (including timestamps, levels, source info, context).
    *   Messages are filtered by **global and handler levels**.
    *   Console output color is determined by the **log level** (via `ConsoleHandler`).
    *   Use these for structured, configurable logging.

2.  **Direct Print Methods (`red`, `green`, `blue`, `bold`, `underline`, `print`, `success`, `fail`, etc.):**
    *   These methods print **directly to the console** (or specified stream) using `builtins.print`.
    *   They **bypass the logging system** entirely (no handlers, formatters, levels, context involved).
    *   Color and style are applied directly as specified in the method call.
    *   Use these for simple, immediate, styled terminal output where logging features aren't needed.

**Utilities** like `highlight`, `multicolor`, and `execute_with_animation` also use **direct printing**. The `trace_exception` utility uses the **logging system** (`ASCIIColors.error`).

---

## 🤝 Contributing

Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on setting up the development environment, coding style, running tests, and submitting pull requests.

---

## 📜 License

ASCIIColors is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.