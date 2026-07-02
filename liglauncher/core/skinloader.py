"""Bridge that makes uploaded skins actually show up in-game.

Vanilla offline Minecraft never shows custom skins: the client only ever
asks *Mojang* for a skin texture, and offline/pirate accounts don't exist
there. The standard workaround (used by essentially every offline launcher)
is the CustomSkinLoader mod, which reads skin PNGs from a local folder
instead. This module:

  1. Downloads + installs CustomSkinLoader into the instance's `mods/`
     folder from Modrinth, for Fabric/Forge/Quilt instances only (vanilla
     has no mod loader, so it's a hard engine limitation there).
  2. Copies the account's resolved skin into the folder CustomSkinLoader
     watches by default: `<game_dir>/CustomSkinLoader/LocalSkin/skins/<name>.png`.

CustomSkinLoader still needs its local-skin source enabled once from its
own in-game config screen (`/csl gui` in chat, or edit
`CustomSkinLoader/CustomSkinLoader.json`) — we intentionally don't overwrite
that file ourselves since its schema isn't stable across versions and a bad
guess would silently break skin loading entirely.
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Optional

import requests

log = logging.getLogger(__name__)

MODRINTH_PROJECT = "customskinloader"
MODRINTH_API = "https://api.modrinth.com/v2"
SUPPORTED_LOADERS = {"fabric", "forge", "quilt"}


class SkinLoaderUnavailable(Exception):
    pass


def _mods_dir(game_dir: Path) -> Path:
    d = game_dir / "mods"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _installed_jar(game_dir: Path) -> Optional[Path]:
    for jar in _mods_dir(game_dir).glob("CustomSkinLoader*.jar"):
        return jar
    return None


def ensure_installed(game_dir: Path, mc_version: str, loader: str) -> Optional[Path]:
    """Download+install CustomSkinLoader for (mc_version, loader) if missing.

    Returns the jar path, or None if the loader isn't supported (vanilla) or
    no matching build could be found (best-effort; launch continues either way).
    """
    loader = loader.lower()
    if loader not in SUPPORTED_LOADERS:
        return None

    existing = _installed_jar(game_dir)
    if existing is not None:
        return existing

    try:
        resp = requests.get(
            f"{MODRINTH_API}/project/{MODRINTH_PROJECT}/version",
            params={"loaders": f'["{loader}"]', "game_versions": f'["{mc_version}"]'},
            timeout=15,
        )
        resp.raise_for_status()
        versions = resp.json()
        if not versions:
            log.warning("No CustomSkinLoader build for %s/%s", loader, mc_version)
            return None

        files = versions[0].get("files", [])
        primary = next((f for f in files if f.get("primary")), files[0] if files else None)
        if primary is None:
            return None

        dest = _mods_dir(game_dir) / primary["filename"]
        with requests.get(primary["url"], stream=True, timeout=60) as dl:
            dl.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in dl.iter_content(chunk_size=1 << 16):
                    fh.write(chunk)
        log.info("Installed CustomSkinLoader -> %s", dest)
        return dest
    except (requests.RequestException, KeyError, IndexError, OSError) as exc:
        log.warning("Could not auto-install CustomSkinLoader: %s", exc)
        return None


def sync_local_skin(game_dir: Path, username: str, skin_path: Path) -> Path:
    """Copy the resolved skin into CustomSkinLoader's local-skin folder."""
    local_dir = game_dir / "CustomSkinLoader" / "LocalSkin" / "skins"
    local_dir.mkdir(parents=True, exist_ok=True)
    dest = local_dir / f"{username}.png"
    shutil.copyfile(skin_path, dest)
    return dest
