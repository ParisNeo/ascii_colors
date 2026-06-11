# -*- coding: utf-8 -*-
"""
vscoder_logging_demo.py
========================

Demonstrates ASCII Colors' per-logger file routing feature
(`FolderRouterHandler`) — built for the LoLLMs VSCoder workflow.

Why this matters for VSCoder AI agents
--------------------------------------
When debugging complex applications, scrolling through a single monolithic
log file is painful. ASCII Colors solves this with the `FolderRouterHandler`,
which automatically routes each logger's output to its own dedicated file
based on the logger's name.

With the LoLLMs VSCoder extension, you can then **add that single log
file to your AI agent's context** instead of dumping your entire log
corpus. The agent sees ONLY the output from the module you're debugging —
no noise, no scrolling, no confusion. Focused, isolated diagnostics lead
to faster, more accurate fixes.

The VSCoder workflow
--------------------
1. An error occurs in one of your modules (e.g. `database`).
2. You open VSCoder and start a chat.
3. You click "Add Files to Context" and select the relevant log file,
   e.g. `logs/database_20251006_184523.log`.
4. You ask: *"Why is my database connection failing?"*
5. The AI agent sees the exact log file and provides a focused diagnosis
   — without wading through every other module's output.

Run modes
---------
    python examples/vscoder_logging_demo.py             # default: rolling
    python examples/vscoder_logging_demo.py rolling     # size-based rotation
    python examples/vscoder_logging_demo.py overwrite   # fresh start each run
    python examples/vscoder_logging_demo.py timestamp   # new file per run

After the script finishes, inspect the `logs/` directory next to where
you ran it and add any single file to VSCoder to experience the workflow.
"""

from __future__ import annotations

import os
import sys
import shutil
import time
import random
from pathlib import Path
from datetime import datetime

import ascii_colors as logging
from ascii_colors import ASCIIColors


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOG_FOLDER = Path("./logs").resolve()
VALID_MODES = ("rolling", "overwrite", "timestamp")


def banner() -> None:
    """Print a friendly intro banner so the demo is self-explanatory."""
    ASCIIColors.rule("🔍 ASCII Colors — Per-Logger File Routing Demo", style="cyan")
    ASCIIColors.print(
        "[bold cyan]Goal:[/bold cyan] show how each named logger gets its "
        "own file, so you can hand a single file to your VSCoder AI agent.",
        color=ASCIIColors.color_white,
    )
    print()


def get_mode() -> str:
    """Pick a routing mode from CLI arg, env var, or default."""
    mode = "rolling"
    if len(sys.argv) > 1 and sys.argv[1] in VALID_MODES:
        mode = sys.argv[1]
    elif os.environ.get("ASCII_COLORS_LOG_MODE") in VALID_MODES:
        mode = os.environ["ASCII_COLORS_LOG_MODE"]
    return mode


def reset_log_folder() -> None:
    """Wipe the logs/ folder so each run is clean and predictable."""
    if LOG_FOLDER.exists():
        shutil.rmtree(LOG_FOLDER)


# ---------------------------------------------------------------------------
# Simulated application components
# ---------------------------------------------------------------------------
# Each function uses a different named logger, so FolderRouterHandler will
# write its output to a separate file. In a real codebase these would be
# different modules / packages.


def simulate_auth(logger) -> None:
    """Simulate user authentication events."""
    user_id = random.randint(1000, 9999)
    logger.info("Authenticating user_id=%d", user_id)
    time.sleep(0.05)
    if random.random() < 0.15:
        logger.warning(
            "Failed login attempt for user_id=%d (bad password)", user_id
        )
    else:
        logger.info("Login successful for user_id=%d", user_id)


def simulate_api(logger) -> None:
    """Simulate API request handling."""
    endpoint = random.choice(["/users", "/orders", "/products", "/health"])
    status = random.choices(
        [200, 201, 400, 404, 500], weights=[70, 10, 8, 7, 5]
    )[0]
    duration_ms = random.randint(5, 250)

    logger.info("Request %s -> %d (%d ms)", endpoint, status, duration_ms)

    if status == 500:
        logger.error(
            "Unhandled exception while processing %s "
            "(see database logs for upstream cause)",
            endpoint,
        )


def simulate_cache(logger) -> None:
    """Simulate cache hits and misses."""
    if random.random() < 0.7:
        logger.debug("Cache HIT for key=user:%d", random.randint(1, 1000))
    else:
        logger.warning("Cache MISS for key=user:%d (falling back to DB)")


def simulate_database(logger) -> None:
    """Simulate database activity — including a planted bug for debugging.

    The bug at the bottom of this function is intentionally left in. After
    running the demo, add `logs/database_*.log` (or `logs/database.log`
    in rolling/overwrite mode) to your VSCoder agent's context and ask it
    to diagnose the issue. This is exactly the workflow the feature enables.
    """
    query = random.choice(
        ["SELECT * FROM users", "SELECT * FROM orders", "SELECT * FROM products"]
    )
    rows = random.randint(1, 500)
    duration_ms = random.randint(1, 80)

    logger.debug("Executing query: %s", query)
    logger.info(
        "Query returned %d rows in %d ms: %s", rows, duration_ms, query
    )

    # Simulate connection pool exhaustion on a few unlucky runs
    if random.random() < 0.10:
        logger.error(
            "psycopg2.OperationalError: connection pool exhausted "
            "(active=10/10, waiting=4, timeout=2.0s)"
        )
        logger.error(
            "Failed to acquire connection within 2.0s for query: %s", query
        )
        return

    # >>> PLANTED BUG: negative row count should never happen <<<
    if rows < 0:
        # This is a bug — assert so it ends up loud in the log file
        logger.critical(
            "INTEGRITY ERROR: negative row count (%d) returned by %s. "
            "Aborting transaction.",
            rows,
            query,
        )
        logger.critical(
            "Upstream caller: simulate_api() at request /orders. "
            "Suspect bad LIMIT clause or unhandled NULL.",
        )


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------


def run_demo(mode: str) -> None:
    """Run the multi-logger simulation under the given routing mode."""
    reset_log_folder()

    # Configure once at startup: route each logger to its own file.
    # NOTE: passing `log_folder` switches the default handler from a
    # ConsoleHandler to a FolderRouterHandler.
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_folder=str(LOG_FOLDER),
        log_folder_mode=mode,
        # Only used in `rolling` mode:
        log_folder_maxBytes=10_000_000,
        log_folder_backupCount=3,
        force=True,
    )

    ASCIIColors.print(
        f"[bold]Routing mode:[/bold] [magenta]{mode}[/magenta]   "
        f"[bold]Output folder:[/bold] [cyan]{LOG_FOLDER}[/cyan]",
        color=ASCIIColors.color_white,
    )
    print()

    # Each component gets its own named logger. That name becomes the
    # filename stem after sanitization.
    auth_logger = logging.getLogger("auth")
    api_logger = logging.getLogger("api")
    cache_logger = logging.getLogger("cache")
    db_logger = logging.getLogger("database")

    # Simulate a burst of realistic activity. In a real app these would
    # run concurrently; here we just interleave them.
    total_events = 40
    ASCIIColors.print(
        f"Simulating {total_events} cross-component events...\n",
        color=ASCIIColors.color_white,
    )

    for i in range(total_events):
        choice = random.choices(
            ["auth", "api", "cache", "db"],
            weights=[25, 35, 20, 20],
        )[0]

        if choice == "auth":
            simulate_auth(auth_logger)
        elif choice == "api":
            simulate_api(api_logger)
        elif choice == "cache":
            simulate_cache(cache_logger)
        else:
            simulate_database(db_logger)

        # Tiny sleep so timestamps differ visibly in the files
        time.sleep(0.01)

    # Make sure every handler's buffer is flushed to disk
    logging.shutdown()

    print()
    show_results(mode)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def show_results(mode: str) -> None:
    """Print the resulting log file tree and a sample of the database log."""
    files = sorted(LOG_FOLDER.glob("*.log"))
    if not files:
        ASCIIColors.warning("No log files were created — something went wrong.")
        return

    ASCIIColors.rule("📁 Resulting Log Folder", style="green")
    ASCIIColors.print(
        f"{LOG_FOLDER}/", color=ASCIIColors.color_cyan, style=ASCIIColors.style_bold
    )
    for f in files:
        size_kb = f.stat().st_size / 1024
        ASCIIColors.print(
            f"  └─ [cyan]{f.name}[/cyan]   [dim]({size_kb:.1f} KB)[/dim]",
            color=ASCIIColors.color_white,
            markup=True,
        )
    print()

    # Highlight the database log — this is what you'd hand to VSCoder.
    db_files = [f for f in files if f.name.startswith("database")]
    if db_files:
        sample = db_files[0].read_text(encoding="utf-8")
        line_count = sample.count("\n")

        ASCIIColors.rule("📄 Sample of logs/database_*.log (for VSCoder)", style="magenta")
        ASCIIColors.print(
            f"[dim]Showing the first lines of {db_files[0].name} "
            f"({line_count} lines total)[/dim]\n",
            color=ASCIIColors.color_white,
        )
        # Show the first 15 lines so the user can see what the AI would see
        for line in sample.splitlines()[:15]:
            print(f"  {line}")
        if line_count > 15:
            ASCIIColors.print(
                f"\n  [dim]... and {line_count - 15} more lines[/dim]",
                color=ASCIIColors.color_white,
            )

    print()
    show_vscoder_workflow(mode)


def show_vscoder_workflow(mode: str) -> None:
    """Print a callout explaining the VSCoder workflow."""
    ASCIIColors.rule("🤖 VSCoder Workflow", style="yellow")
    ASCIIColors.print(
        "Now that you have isolated, per-module log files, you can use them\n"
        "with the LoLLMs VSCoder extension:\n",
        color=ASCIIColors.color_white,
    )
    steps = [
        ("1.", "Open VS Code with the LoLLMs VSCoder extension installed."),
        ("2.", "Start a new chat with the AI agent."),
        ("3.", "Click [bold]Add Files to Context[/bold] and select "
               "[cyan]logs/database_*.log[/cyan] (or any single component log)."),
        ("4.", "Ask: [italic]\"Why is my database connection failing?\"[/italic]"),
        ("5.", "The agent sees [bold]only[/bold] the database output — no noise "
               "from auth, cache, or api — and gives you a focused diagnosis."),
    ]
    for marker, text in steps:
        ASCIIColors.print(f"  [bold yellow]{marker}[/bold yellow] {text}", markup=True)

    print()
    ASCIIColors.print(
        f"💡 [bold]Tip:[/bold] rerun with "
        f"[magenta]python examples/vscoder_logging_demo.py {OTHER_MODES_FOR(mode)}[/magenta] "
        f"to see how the file naming changes between modes.",
        color=ASCIIColors.color_white,
    )
    print()
    ASCIIColors.print(
        f"📚 [dim]See README.md → "
        f"\"Per-Logger File Routing — Built for LoLLMs VSCoder\" "
        f"for the full reference.[/dim]",
        color=ASCIIColors.color_white,
    )


def OTHER_MODES_FOR(current: str) -> str:
    """Return a hint string showing the other two modes."""
    others = [m for m in VALID_MODES if m != current]
    return " or ".join(others)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    try:
        banner()
        mode = get_mode()
        run_demo(mode)
        return 0
    except KeyboardInterrupt:
        ASCIIColors.warning("\nInterrupted by user.")
        logging.shutdown()
        return 130


if __name__ == "__main__":
    sys.exit(main())
