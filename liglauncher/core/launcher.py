"""Build and execute the Minecraft launch command."""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import minecraft_launcher_lib as mll

from .. import __version__
from .auth import OfflineAccount
from . import skinloader
from .skins import SkinStore

log = logging.getLogger(__name__)


@dataclass
class LaunchOptions:
    account: OfflineAccount
    version_id: str  # resolved/installed version id (e.g. fabric-loader-...)
    mc_version: str  # base Minecraft version (e.g. "1.20.4")
    loader: str = "vanilla"  # vanilla | forge | fabric | quilt
    game_dir: Path = None  # type: ignore[assignment]
    ram_mb: int = 2048
    java_path: str = ""
    extra_jvm_args: Optional[Iterable[str]] = None
    apply_skin: bool = True


def _resolve_java(java_path: str, game_dir: Path) -> Optional[str]:
    if java_path:
        return java_path
    try:
        runtimes = mll.runtime.get_installed_jvm_runtimes(str(game_dir))
        if runtimes:
            return mll.runtime.get_executable_path(runtimes[0], str(game_dir))
    except Exception as exc:  # noqa: BLE001
        log.debug("No bundled JVM runtime found: %s", exc)
    return None


def _sync_skin(opts: LaunchOptions) -> None:
    """Best-effort: install CustomSkinLoader + drop the account's skin into place."""
    if not opts.apply_skin:
        return
    store = SkinStore()
    skin_path = store.get_skin(opts.account.uuid, opts.mc_version)
    if skin_path is None:
        return
    try:
        skinloader.ensure_installed(opts.game_dir, opts.mc_version, opts.loader)
        skinloader.sync_local_skin(opts.game_dir, opts.account.name, skin_path)
    except Exception as exc:  # noqa: BLE001
        log.warning("Skin sync failed (game will still launch): %s", exc)


def build_command(opts: LaunchOptions) -> list[str]:
    jvm_args = [f"-Xmx{opts.ram_mb}M", f"-Xms{min(opts.ram_mb, 1024)}M"]
    if opts.extra_jvm_args:
        jvm_args.extend(opts.extra_jvm_args)

    options = {
        **opts.account.as_options(),
        "jvmArguments": jvm_args,
        "launcherName": "LigLauncher",
        "launcherVersion": __version__,
        "gameDirectory": str(opts.game_dir),
    }

    java_exe = _resolve_java(opts.java_path, opts.game_dir)
    if java_exe:
        options["executablePath"] = java_exe

    return mll.command.get_minecraft_command(opts.version_id, str(opts.game_dir), options)


def launch(opts: LaunchOptions) -> subprocess.Popen:
    _sync_skin(opts)
    cmd = build_command(opts)
    log.info("Launching: %s", " ".join(cmd))

    creationflags = 0
    if sys.platform.startswith("win"):
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    return subprocess.Popen(
        cmd,
        cwd=str(opts.game_dir),
        env=os.environ.copy(),
        creationflags=creationflags,
    )
