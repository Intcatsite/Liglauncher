"""Build a single-file Windows .exe with PyInstaller.

Usage:
    pip install -r requirements.txt pyinstaller
    python build.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
SPEC = ROOT / "LigLauncher.spec"


def main() -> int:
    for path in (DIST, BUILD):
        if path.exists():
            shutil.rmtree(path)
    if SPEC.exists():
        SPEC.unlink()

    icon = ROOT / "assets" / "icon.ico"
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "LigLauncher",
    ]
    if icon.exists():
        args += ["--icon", str(icon)]
    args += [str(ROOT / "liglauncher" / "__main__.py")]

    print(">>>", " ".join(args))
    return subprocess.call(args)


if __name__ == "__main__":
    sys.exit(main())
