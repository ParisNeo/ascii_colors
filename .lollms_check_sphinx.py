
# -*- coding: utf-8 -*-
"""One-shot verification that the docs toolchain is importable."""
import importlib
import sys

PACKAGES = [
    ("sphinx", "__version__"),
    ("furo", None),
    ("myst_parser", None),
    ("sphinx_copybutton", None),
    ("sphinx_autodoc_typehints", None),
    ("toml", None),
]

failed = []
for name, version_attr in PACKAGES:
    try:
        module = importlib.import_module(name)
    except ImportError as exc:
        failed.append(f"{name}: {exc}")
        continue
    version = getattr(module, version_attr, "ok") if version_attr else "ok"
    print(f"{name} -> {version}")

if failed:
    print("MISSING:", ", ".join(failed), file=sys.stderr)
    sys.exit(1)
print("ALL_DOC_DEPS_OK")