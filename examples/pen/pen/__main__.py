# -*- coding: utf-8 -*-
"""Entry point for ``python -m pen``."""

import sys

from pen.cli import main

if __name__ == "__main__":
    sys.exit(main())