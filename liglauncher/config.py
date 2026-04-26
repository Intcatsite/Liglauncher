"""Persistent launcher configuration."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .paths import config_path, minecraft_dir

log = logging.getLogger(__name__)


@dataclass
class LauncherConfig:
    username: str = "Player"
    version_id: str = ""
    version_type: str = "release"  # release | snapshot | old_beta | old_alpha | forge | fabric | quilt
    ram_mb: int = 2048
    java_path: str = ""  # empty = let JVM be auto-detected by minecraft-launcher-lib
    game_dir: str = ""  # empty = use default minecraft_dir()
    show_snapshots: bool = False
    show_old: bool = False
    jvm_args: list[str] = field(default_factory=list)

    def resolved_game_dir(self) -> Path:
        return Path(self.game_dir) if self.game_dir else minecraft_dir()


def load_config() -> LauncherConfig:
    path = config_path()
    if not path.exists():
        return LauncherConfig()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # Ignore unknown keys to stay forward-compatible.
        valid = {f for f in LauncherConfig.__dataclass_fields__}
        clean = {k: v for k, v in data.items() if k in valid}
        return LauncherConfig(**clean)
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        log.warning("Failed to load config (%s); using defaults", exc)
        return LauncherConfig()


def save_config(cfg: LauncherConfig) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
    except OSError as exc:
        log.error("Failed to save config: %s", exc)
