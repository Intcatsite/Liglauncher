"""Version listing and metadata helpers."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import minecraft_launcher_lib as mll

log = logging.getLogger(__name__)


VERSION_TYPES = ("release", "snapshot", "old_beta", "old_alpha")
LOADER_TYPES = ("forge", "fabric", "quilt")


@dataclass(frozen=True)
class VersionEntry:
    id: str
    type: str  # one of VERSION_TYPES + LOADER_TYPES
    installed: bool


def list_remote_versions() -> list[dict]:
    """Full Mojang version manifest. Network required."""
    return mll.utils.get_version_list()


def list_installed_versions(game_dir: Path) -> list[dict]:
    return mll.utils.get_installed_versions(str(game_dir))


def filter_vanilla(
    versions: Iterable[dict],
    *,
    show_snapshots: bool,
    show_old: bool,
) -> list[dict]:
    allowed = {"release"}
    if show_snapshots:
        allowed.add("snapshot")
    if show_old:
        allowed.add("old_beta")
        allowed.add("old_alpha")
    return [v for v in versions if v.get("type") in allowed]


def installed_ids(game_dir: Path) -> set[str]:
    try:
        return {v["id"] for v in list_installed_versions(game_dir)}
    except Exception as exc:  # noqa: BLE001
        log.warning("Failed to read installed versions: %s", exc)
        return set()


# --- Loader-specific helpers ---------------------------------------------------

def fabric_supported(mc_version: str) -> bool:
    try:
        return mll.fabric.is_minecraft_version_supported(mc_version)
    except Exception as exc:  # noqa: BLE001
        log.warning("Fabric availability check failed: %s", exc)
        return False


def quilt_supported(mc_version: str) -> bool:
    try:
        return mll.quilt.is_minecraft_version_supported(mc_version)
    except Exception as exc:  # noqa: BLE001
        log.warning("Quilt availability check failed: %s", exc)
        return False


def forge_supported(mc_version: str) -> bool:
    try:
        return mll.forge.find_forge_version(mc_version) is not None
    except Exception as exc:  # noqa: BLE001
        log.warning("Forge availability check failed: %s", exc)
        return False
