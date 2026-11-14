# pen

A minimalist terminal text editor with live syntax highlighting, built on the
[`ascii_colors`](https://pypi.org/project/ascii_colors/) TUI framework.

Designed as a friendly `nano` replacement on Windows (and everywhere else):
system clipboard copy/paste, Save As, undo/redo, find, go-to-line, and
detection of external file changes.

## Install

```bash
pip install ascii-pen
```

Or, from a checkout of this directory:

```bash
pip install -e .
```

## Usage

```bash
pen                     # start with an empty untitled document
pen path/to/file.py     # open an existing file, or create a new one
pen notes.md            # any text file works — not just Python
```

## Controls

| Key                               | Action                                        |
| --------------------------------- | --------------------------------------------- |
| Arrows, Home, End, PgUp, PgDn     | Move the cursor                               |
| Shift + arrows                    | Extend the selection                          |
| Ctrl+A / Ctrl+B                   | Select all / toggle the selection mark        |
| Ctrl+C / Ctrl+X / Ctrl+V          | Copy / cut / paste (uses the OS clipboard)    |
| Ctrl+Z / Ctrl+Y                   | Undo / redo                                   |
| Enter, Backspace, Delete, Tab     | Edit                                          |
| Ctrl+S                            | Save (prompts for a path if untitled)         |
| F2                                | Save As…                                      |
| Ctrl+O                            | Open another file                             |
| Ctrl+N                            | New buffer                                    |
| F5                                | Reload from disk                              |
| Ctrl+F / Ctrl+G                   | Find / go to line                             |
| F1                                | Shortcut help                                 |
| Ctrl+Q                            | Quit (asks before discarding changes)         |

`Tab` inserts an indent using the file's own convention (tabs if the file
already uses tabs, otherwise spaces).

## Features

- **Not Python-only.** Highlighting is chosen from the file extension —
  Python, JavaScript/TypeScript, C/C++/C#/Java/Go/Rust, JSON, shell,
  TOML/INI/YAML — and falls back to plain text for anything else.
- **Real copy/paste.** Uses the Windows clipboard (via `ctypes`), `pbcopy` /
  `pbpaste` on macOS, and `xclip` / `xsel` on Linux, with an in-process
  fallback when none is available.
- **External change detection.** The buffer watches its file; if another
  program rewrites it, the status line warns, saving asks for confirmation,
  and `F5` reloads.
- **Unsaved-change protection.** Quitting, opening and creating buffers all
  ask before throwing work away.
- Line-number gutter with the current line highlighted.
- Vertical and horizontal scrolling driven by the cursor.
- Wide-character aware rendering.

## License

MIT