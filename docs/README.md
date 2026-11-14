# ascii_colors Documentation

This directory contains the [Sphinx](https://www.sphinx-doc.org/) sources and
build helpers for the [ascii_colors](https://github.com/ParisNeo/ascii_colors)
documentation.

## Layout

| Path | Purpose |
|------|---------|
| `source/` | Sphinx sources (RST pages and `conf.py`) |
| `source/_static/` | Static assets (kept via `.gitkeep`) |
| `source/_templates/` | Custom Sphinx templates (kept via `.gitkeep`) |
| `build/` | Generated HTML output (should stay out of version control) |

## Prerequisites

Install the documentation dependencies:

```bash
pip install -r docs/requirements.txt
```

Or install the package itself with its `dev` extras (which include the doc
toolchain plus testing/linting tools):

```bash
pip install -e ".[dev]"
```

## Building Locally

Using the Makefile (Linux / macOS / WSL):

```bash
make -C docs html
```

On Windows, use the bundled batch file from the repository root:

```bat
docs\make.bat html
```

Or invoke Sphinx directly:

```bash
sphinx-build -b html docs/source docs/build/html
```

The rendered site is written to `docs/build/html/index.html`. Open it in a
browser:

```bash
# Linux
xdg-open docs/build/html/index.html
# macOS
open docs/build/html/index.html
# Windows
start docs\build\html\index.html
```

## Live Reload

For rapid iteration, use `sphinx-autobuild` (part of the `dev` extras):

```bash
sphinx-autobuild docs/source docs/build/html --open-browser
```

The browser will refresh automatically whenever a source file changes.

## Publishing

The documentation is published to GitHub Pages automatically by
[`.github/workflows/docs.yaml`](../.github/workflows/docs.yaml) whenever a
commit is pushed to `main`. The deployment target is the `docs/build/html`
directory built from `docs/source`.

Live site: <https://parisneo.github.io/ascii_colors/>

## Conventions

- Keep each guide page focused on a single topic (installation, quickstart,
  logging, rich components, prompts, TUI).
- Prefer `.. automodule::` / `.. autoclass::` directives over hand-written
  signatures so API reference stays in sync with the source.
- Do not delete `conf.py`, `index.rst`, `api.rst`, or any guide page — the
  suite is already deployed; augment it instead of recreating it.