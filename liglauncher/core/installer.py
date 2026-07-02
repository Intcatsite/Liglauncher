"""Install Minecraft versions (vanilla / Forge / Fabric / Quilt)."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import minecraft_launcher_lib as mll

log = logging.getLogger(__name__)

ProgressFn = Callable[[str, int, int], None]

# The Forge installer runs installer.jar as a subprocess and then tries to
# clean up its temp dir; on Windows the JVM process (or an antivirus scan of
# the freshly-downloaded jar) can still hold a handle to that file for a
# moment, raising "WinError 32: file in use" even though the install itself
# succeeded. This is transient, so retry a few times before giving up.
_LOCK_RETRIES = 4
_LOCK_RETRY_DELAY_S = 1.5


def _retry_on_file_lock(fn: Callable[[], None]) -> None:
    for attempt in range(1, _LOCK_RETRIES + 1):
        try:
            fn()
            return
        except PermissionError:
            if attempt == _LOCK_RETRIES:
                raise
            log.warning(
                "Install file locked by another process, retrying (%d/%d)…",
                attempt,
                _LOCK_RETRIES,
            )
            time.sleep(_LOCK_RETRY_DELAY_S)


@dataclass
class InstallTarget:
    mc_version: str
    loader: str = "vanilla"  # vanilla | forge | fabric | quilt
    loader_version: Optional[str] = None  # only used for Forge


def _make_callback(progress: Optional[ProgressFn]) -> dict:
    state = {"status": "", "current": 0, "total": 0}

    def set_status(text: str) -> None:
        state["status"] = text
        if progress:
            progress(state["status"], state["current"], state["total"])

    def set_progress(value: int) -> None:
        state["current"] = value
        if progress:
            progress(state["status"], state["current"], state["total"])

    def set_max(value: int) -> None:
        state["total"] = value
        if progress:
            progress(state["status"], state["current"], state["total"])

    return {"setStatus": set_status, "setProgress": set_progress, "setMax": set_max}


def install_vanilla(version_id: str, game_dir: Path, progress: Optional[ProgressFn] = None) -> None:
    log.info("Installing vanilla %s into %s", version_id, game_dir)
    mll.install.install_minecraft_version(version_id, str(game_dir), callback=_make_callback(progress))


def install_fabric(
    mc_version: str, game_dir: Path, loader_version: Optional[str] = None, progress: Optional[ProgressFn] = None
) -> str:
    log.info("Installing Fabric for %s", mc_version)
    mll.fabric.install_fabric(mc_version, str(game_dir), loader_version=loader_version, callback=_make_callback(progress))
    loader_ver = loader_version or mll.fabric.get_latest_loader_version()
    return f"fabric-loader-{loader_ver}-{mc_version}"


def install_quilt(
    mc_version: str, game_dir: Path, loader_version: Optional[str] = None, progress: Optional[ProgressFn] = None
) -> str:
    log.info("Installing Quilt for %s", mc_version)
    mll.quilt.install_quilt(mc_version, str(game_dir), loader_version=loader_version, callback=_make_callback(progress))
    loader_ver = loader_version or mll.quilt.get_latest_loader_version()
    return f"quilt-loader-{loader_ver}-{mc_version}"


def install_forge(
    mc_version: str, game_dir: Path, forge_version: Optional[str] = None, progress: Optional[ProgressFn] = None
) -> str:
    fv = forge_version or mll.forge.find_forge_version(mc_version)
    if not fv:
        raise RuntimeError(f"No Forge build found for Minecraft {mc_version}")
    if not mll.forge.supports_automatic_install(fv):
        raise RuntimeError(
            f"Forge {fv} cannot be installed automatically (legacy installer). "
            "Run the official Forge installer manually for this version."
        )
    log.info("Installing Forge %s", fv)
    _retry_on_file_lock(
        lambda: mll.forge.install_forge_version(fv, str(game_dir), callback=_make_callback(progress))
    )
    return mll.forge.forge_to_installed_version(fv)


def install_target(target: InstallTarget, game_dir: Path, progress: Optional[ProgressFn] = None) -> str:
    """Install the target and return the resolved installed version id."""
    game_dir.mkdir(parents=True, exist_ok=True)

    if target.loader == "vanilla":
        install_vanilla(target.mc_version, game_dir, progress)
        return target.mc_version
    if target.loader == "fabric":
        return install_fabric(target.mc_version, game_dir, progress=progress)
    if target.loader == "quilt":
        return install_quilt(target.mc_version, game_dir, progress=progress)
    if target.loader == "forge":
        return install_forge(target.mc_version, game_dir, target.loader_version, progress=progress)
    raise ValueError(f"Unknown loader: {target.loader!r}")
