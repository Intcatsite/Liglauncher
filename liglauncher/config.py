"""Persistent launcher configuration: game settings + UI theme."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .paths import config_path, minecraft_dir

log = logging.getLogger(__name__)


@dataclass
class ThemeConfig:
    accent_color: str = "#7c5cff"       # primary accent used across the whole UI
    text_color: str = "#f5f5f7"
    font_family: str = "Segoe UI"
    font_size: int = 10
    background_path: str = ""           # empty = built-in gradient
    background_blur: bool = True
    window_opacity: float = 0.90        # 0.4..1.0, how see-through the window is
    window_mode: str = "windowed"       # "windowed" | "fullscreen"
    window_width: int = 1180
    window_height: int = 740


@dataclass
class LauncherConfig:
    active_account_uuid: str = ""
    version_id: str = ""
    version_type: str = "release"  # release | snapshot | old_beta | old_alpha | forge | fabric | quilt
    ram_mb: int = 2048
    java_path: str = ""
    game_dir: str = ""
    show_snapshots: bool = False
    show_old: bool = False
    jvm_args: list[str] = field(default_factory=list)
    theme: ThemeConfig = field(default_factory=ThemeConfig)

    def resolved_game_dir(self) -> Path:
        return Path(self.game_dir) if self.game_dir else minecraft_dir()


def load_config() -> LauncherConfig:
    path = config_path()
    if not path.exists():
        return LauncherConfig()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        theme_data = data.pop("theme", {}) or {}
        valid = {f for f in LauncherConfig.__dataclass_fields__}
        clean = {k: v for k, v in data.items() if k in valid and k != "theme"}
        theme_valid = {f for f in ThemeConfig.__dataclass_fields__}
        theme_clean = {k: v for k, v in theme_data.items() if k in theme_valid}
        return LauncherConfig(theme=ThemeConfig(**theme_clean), **clean)
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        log.warning("Failed to load config (%s); using defaults", exc)
        return LauncherConfig()


def save_config(cfg: LauncherConfig) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(asdict(cfg), indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        log.error("Failed to save config: %s", exc)
