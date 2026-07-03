"""Self-update: check GitHub Releases for a newer LigLauncher.exe and,
when running as the packaged .exe, download it and swap it in for the
currently running one.

This only ever finds something to update to once a real tagged GitHub
Release exists (created by pushing a `vX.Y.Z` tag, which the repo's
`.github/workflows/release.yml` turns into a Release with `LigLauncher.exe`
attached) — plain CI build artifacts from workflow_dispatch runs don't
count, since only tagged Releases show up in the GitHub Releases API.
"""
from __future__ import annotations

import logging
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import requests

from .. import __version__

log = logging.getLogger(__name__)

RELEASES_API = "https://api.github.com/repos/Intcatsite/Liglauncher/releases/latest"
ASSET_NAME = "LigLauncher.exe"
ProgressFn = Callable[[int, int], None]


@dataclass
class UpdateInfo:
    version: str
    download_url: str
    notes: str


def _parse_version(v: str) -> tuple[int, ...]:
    v = v.strip().lstrip("vV")
    parts = []
    for chunk in v.split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def is_frozen() -> bool:
    """True when running as the PyInstaller-built .exe (self-update only works there)."""
    return hasattr(sys, "_MEIPASS")


def check_for_update(timeout: float = 10.0) -> Optional[UpdateInfo]:
    """Return update info if the latest GitHub Release is newer than this build, else None.

    Network/parse errors propagate so callers can tell "checked, nothing new"
    apart from "couldn't check at all".
    """
    resp = requests.get(RELEASES_API, timeout=timeout, headers={"Accept": "application/vnd.github+json"})
    resp.raise_for_status()
    data = resp.json()

    tag = data.get("tag_name") or ""
    if not tag or _parse_version(tag) <= _parse_version(__version__):
        return None

    asset = next((a for a in data.get("assets", []) if a.get("name") == ASSET_NAME), None)
    if asset is None:
        log.info("Release %s has no %s asset yet", tag, ASSET_NAME)
        return None

    return UpdateInfo(
        version=tag.lstrip("vV"),
        download_url=asset["browser_download_url"],
        notes=(data.get("body") or "").strip(),
    )


def download_update(info: UpdateInfo, on_progress: Optional[ProgressFn] = None) -> Path:
    """Download the new exe next to the running one (or into a temp dir in dev mode)."""
    if is_frozen():
        dest_dir = Path(sys.executable).parent
    else:
        dest_dir = Path(tempfile.gettempdir())
    dest = dest_dir / "LigLauncher.update.exe"

    with requests.get(info.download_url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        done = 0
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                fh.write(chunk)
                done += len(chunk)
                if on_progress:
                    on_progress(done, total)
    return dest


def apply_update(new_exe: Path) -> None:
    """Spawn a detached helper that waits for us to exit, replaces the exe, and relaunches it.

    Windows allows deleting/renaming a running executable's file (just not
    overwriting its bytes while mapped), so the helper polls with `del` until
    that succeeds, then moves the new build into place and starts it. The
    caller is responsible for quitting the app right after calling this.
    """
    if not is_frozen():
        raise RuntimeError("Self-update only works in the packaged .exe, not `python -m liglauncher`.")

    current = Path(sys.executable)
    script = current.parent / "_liglauncher_update.bat"
    script.write_text(
        "@echo off\r\n"
        "timeout /t 1 /nobreak > NUL\r\n"
        ":wait\r\n"
        f'del /f /q "{current}" 2>NUL\r\n'
        f'if exist "{current}" goto wait\r\n'
        f'move /y "{new_exe}" "{current}" > NUL\r\n'
        f'start "" "{current}"\r\n'
        f'del /f /q "%~f0"\r\n',
        encoding="utf-8",
    )
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen(["cmd", "/c", str(script)], creationflags=flags, close_fds=True)
