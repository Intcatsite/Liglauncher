"""Cross-platform paths used by the launcher."""
from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "LigLauncher"


def app_data_dir() -> Path:
    """Per-user data directory (game files, config, logs)."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    # Linux / other Unix
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / APP_NAME


def minecraft_dir() -> Path:
    """Game directory used by minecraft-launcher-lib."""
    return app_data_dir() / "minecraft"


def config_path() -> Path:
    return app_data_dir() / "config.json"


def logs_dir() -> Path:
    return app_data_dir() / "logs"
