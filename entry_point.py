"""PyInstaller entry point.

PyInstaller runs whatever script it's pointed at as a top-level module named
``__main__``, which breaks package-relative imports if pointed directly at
``liglauncher/__main__.py``. This tiny wrapper lives outside the package so
``liglauncher`` is imported normally (relative imports inside it keep
working) and only the wrapper itself is the PyInstaller entry script.
"""
from __future__ import annotations

import sys

from liglauncher.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
