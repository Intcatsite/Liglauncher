"""Integration with CraftIP (https://craftip.net) — tunnels a local Minecraft
server so it's reachable from the internet at `xxxx.craftip.net`.

CraftIP is a real, independent open-source project (Rust, GPL, developed at
https://codeberg.org/craftip/craftip). It ships no pre-built binaries, so
this module builds the CLI client from source once (needs `git` + Rust's
`cargo` on PATH — both one-time, user-triggered installs) and caches the
resulting executable under paths.tools_dir(). We do not reimplement or proxy
their tunnel protocol ourselves: we just run their real client as a
subprocess and read the public address it reports on stdout.
"""
from __future__ import annotations

import logging
import platform
import re
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional

from ..paths import tools_dir

log = logging.getLogger(__name__)

REPO_URL = "https://codeberg.org/craftip/craftip.git"
ADDRESS_RE = re.compile(r"[a-zA-Z0-9-]+\.craftip\.net(?::\d+)?")
LogFn = Callable[[str], None]


class CraftIpUnavailable(Exception):
    pass


def _binary_name() -> str:
    return "client.exe" if platform.system() == "Windows" else "client"


def cached_client_path() -> Path:
    return tools_dir() / _binary_name()


def is_available() -> bool:
    return cached_client_path().exists()


def build_prerequisites_missing() -> list[str]:
    """Tools required to build the CraftIP client from source, that aren't on PATH."""
    missing = []
    if shutil.which("git") is None:
        missing.append("git")
    if shutil.which("cargo") is None:
        missing.append("cargo (Rust toolchain, https://rustup.rs)")
    return missing


def build_client(on_line: Optional[LogFn] = None) -> Path:
    """Clone craftip and `cargo build --release --bin client`; cache the binary."""
    missing = build_prerequisites_missing()
    if missing:
        raise CraftIpUnavailable(
            "Для сборки CraftIP не хватает: " + ", ".join(missing)
        )

    tools_dir().mkdir(parents=True, exist_ok=True)
    src_dir = tools_dir() / "craftip-src"

    def _run(cmd: list[str], cwd: Optional[Path] = None) -> None:
        if on_line:
            on_line("$ " + " ".join(cmd))
        proc = subprocess.Popen(
            cmd, cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            if on_line:
                on_line(line.rstrip("\n"))
        code = proc.wait()
        if code != 0:
            raise CraftIpUnavailable(f"Команда завершилась с ошибкой ({code}): {' '.join(cmd)}")

    if src_dir.exists():
        _run(["git", "-C", str(src_dir), "pull", "--ff-only"])
    else:
        _run(["git", "clone", "--depth", "1", REPO_URL, str(src_dir)])

    _run(["cargo", "build", "--release", "--bin", "client"], cwd=src_dir)

    built = src_dir / "target" / "release" / _binary_name()
    if not built.exists():
        raise CraftIpUnavailable("Сборка завершилась, но исполняемый файл клиента не найден.")

    dest = cached_client_path()
    shutil.copyfile(built, dest)
    dest.chmod(0o755)
    return dest


class Tunnel:
    def __init__(self) -> None:
        self.process: Optional[subprocess.Popen] = None
        self.address: Optional[str] = None

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def stop(self) -> None:
        if self.process and self.is_running():
            self.process.terminate()


def start_tunnel(
    local_port: int,
    on_line: Optional[LogFn] = None,
    on_address: Optional[Callable[[str], None]] = None,
) -> Tunnel:
    client = cached_client_path()
    if not client.exists():
        raise CraftIpUnavailable(
            "CraftIP-клиент ещё не собран. Нажмите «Собрать CraftIP» в настройках."
        )

    tunnel = Tunnel()
    proc = subprocess.Popen(
        [str(client), f"localhost:{local_port}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    tunnel.process = proc

    def _pump() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip("\n")
            if on_line:
                on_line(line)
            if tunnel.address is None:
                m = ADDRESS_RE.search(line)
                if m:
                    tunnel.address = m.group(0)
                    if on_address:
                        on_address(tunnel.address)

    threading.Thread(target=_pump, daemon=True).start()
    return tunnel
