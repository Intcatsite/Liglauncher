"""Cross-platform paths used by the launcher."""
from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "LigLauncher"


def assets_dir() -> Path:
    """Bundled read-only assets (icons, app icon) — inside the frozen exe or repo root."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent / "assets"


def app_data_dir() -> Path:
    """Per-user data directory (game files, config, logs, accounts, skins)."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / APP_NAME


def minecraft_dir() -> Path:
    """Game directory used by minecraft-launcher-lib."""
    return app_data_dir() / "minecraft"


def config_path() -> Path:
    return app_data_dir() / "config.json"


def accounts_path() -> Path:
    return app_data_dir() / "accounts.json"


def skins_dir() -> Path:
    """<skins>/<account_uuid>/<version_id>/skin.png"""
    return app_data_dir() / "skins"


def backgrounds_dir() -> Path:
    return app_data_dir() / "backgrounds"


def servers_dir() -> Path:
    return app_data_dir() / "servers"


def tools_dir() -> Path:
    """Bundled/downloaded third-party helper binaries (e.g. the CraftIP client)."""
    return app_data_dir() / "tools"


def logs_dir() -> Path:
    return app_data_dir() / "logs"
