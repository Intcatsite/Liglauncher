"""Create and run a local vanilla Minecraft server (for the "Create Server" button)."""
from __future__ import annotations

import logging
import re
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import requests
import minecraft_launcher_lib as mll

from ..paths import servers_dir

log = logging.getLogger(__name__)

LogFn = Callable[[str], None]


class ServerInstallError(Exception):
    pass


@dataclass
class ManagedServer:
    name: str
    mc_version: str
    directory: Path
    port: int = 25565
    process: Optional[subprocess.Popen] = None
    ready: bool = False
    _log_lines: list[str] = field(default_factory=list)

    @property
    def jar_path(self) -> Path:
        return self.directory / "server.jar"

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def stop(self) -> None:
        if self.process and self.is_running():
            try:
                if self.process.stdin:
                    self.process.stdin.write("stop\n")
                    self.process.stdin.flush()
                self.process.wait(timeout=20)
            except Exception:  # noqa: BLE001
                self.process.terminate()


def _find_server_download(mc_version: str) -> tuple[str, Optional[str]]:
    """Return (download_url, sha1) for the vanilla server jar of mc_version."""
    manifest = mll.utils.get_version_list()
    entry = next((v for v in manifest if v.get("id") == mc_version), None)
    if entry is None:
        raise ServerInstallError(f"Версия {mc_version} не найдена в манифесте Mojang.")

    resp = requests.get(entry["url"], timeout=20)
    resp.raise_for_status()
    version_json = resp.json()
    server = version_json.get("downloads", {}).get("server")
    if not server:
        raise ServerInstallError(
            f"Для версии {mc_version} нет серверного jar (слишком старая версия?)."
        )
    return server["url"], server.get("sha1")


def create_server(
    name: str,
    mc_version: str,
    port: int = 25565,
    progress: Optional[LogFn] = None,
) -> ManagedServer:
    """Download the vanilla server jar and lay out a ready-to-run server directory."""
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", name.strip()) or "server"
    directory = servers_dir() / safe_name
    directory.mkdir(parents=True, exist_ok=True)

    srv = ManagedServer(name=safe_name, mc_version=mc_version, directory=directory, port=port)

    if not srv.jar_path.exists():
        if progress:
            progress(f"Скачивание server.jar для {mc_version}…")
        url, _sha1 = _find_server_download(mc_version)
        with requests.get(url, stream=True, timeout=120) as dl:
            dl.raise_for_status()
            with open(srv.jar_path, "wb") as fh:
                for chunk in dl.iter_content(chunk_size=1 << 16):
                    fh.write(chunk)

    (directory / "eula.txt").write_text("eula=true\n", encoding="utf-8")

    props_path = directory / "server.properties"
    if not props_path.exists():
        props_path.write_text(
            f"server-port={port}\nonline-mode=false\nmotd=LigLauncher server\n",
            encoding="utf-8",
        )

    if progress:
        progress("Сервер готов.")
    return srv


def start_server(
    srv: ManagedServer,
    ram_mb: int = 2048,
    java_path: str = "java",
    on_line: Optional[LogFn] = None,
    on_ready: Optional[Callable[[], None]] = None,
) -> subprocess.Popen:
    cmd = [java_path, f"-Xmx{ram_mb}M", f"-Xms{min(ram_mb, 1024)}M", "-jar", str(srv.jar_path), "nogui"]
    log.info("Starting server: %s", " ".join(cmd))

    proc = subprocess.Popen(
        cmd,
        cwd=str(srv.directory),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    srv.process = proc

    def _pump() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip("\n")
            srv._log_lines.append(line)
            if on_line:
                on_line(line)
            if not srv.ready and re.search(r'Done \(.*\)!.*For help', line):
                srv.ready = True
                if on_ready:
                    on_ready()

    threading.Thread(target=_pump, daemon=True).start()
    return proc
