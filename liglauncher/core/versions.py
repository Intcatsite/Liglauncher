"""Version listing and metadata helpers.

The full version list comes from (in order):
  1. Mojang's version manifest,
  2. the BMCLAPI mirror (bmclapi2.bangbang93.com) when Mojang is
     unreachable — some ISPs/regions block or fail to resolve
     launchermeta.mojang.com,
  3. a manifest snapshot bundled with the launcher (assets/versions.json),
     so the picker is fully populated even with no network at all.

New Minecraft versions appear automatically whenever either remote source
is reachable; the bundled snapshot is only the worst-case floor.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import minecraft_launcher_lib as mll
import requests

from ..paths import assets_dir

log = logging.getLogger(__name__)


VERSION_TYPES = ("release", "snapshot", "old_beta", "old_alpha")
LOADER_TYPES = ("forge", "fabric", "quilt")

MANIFEST_URLS = (
    "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json",
    "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json",
    "https://bmclapi2.bangbang93.com/mc/game/version_manifest_v2.json",  # mirror
)


@dataclass(frozen=True)
class VersionEntry:
    id: str
    type: str
    installed: bool


def list_remote_versions() -> list[dict]:
    """Full Mojang version manifest. Network required."""
    return mll.utils.get_version_list()


def bundled_versions() -> list[dict]:
    path = assets_dir() / "versions.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("versions", [])
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("Bundled version snapshot unavailable: %s", exc)
        return []


def fetch_all_versions(timeout: float = 10.0) -> tuple[list[dict], bool]:
    """Return (versions, from_network).

    Tries each manifest URL in turn; falls back to the bundled snapshot.
    Each version dict has at least 'id' and 'type'.
    """
    for url in MANIFEST_URLS:
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            versions = resp.json().get("versions", [])
            if versions:
                return versions, True
        except (requests.RequestException, ValueError) as exc:
            log.info("Version manifest %s failed: %s", url, exc)
    return bundled_versions(), False


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
