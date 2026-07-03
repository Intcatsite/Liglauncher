"""Automatic download mirror for networks where Mojang is unreachable.

Some ISPs/regions fail to resolve or block *.mojang.com — installs then die
with DNS errors even though the internet "works". BMCLAPI
(bmclapi2.bangbang93.com) is a long-running public mirror of Mojang's
version manifests, client/server jars, assets and libraries, plus the
Forge/Fabric mavens.

`ensure_checked()` probes Mojang once per launcher run; if Mojang is down
but the mirror answers, it monkeypatches minecraft-launcher-lib's two
download entry points (`_helper.download_file` and
`_helper.get_requests_response_cache`) to rewrite Mojang URLs to their
mirror equivalents. Everything else (install logic, hashes, layouts) stays
untouched — the mirror serves byte-identical files, and sha1 checks in mll
still run against Mojang's own hashes from the (mirrored) manifests.
"""
from __future__ import annotations

import logging
import threading

import requests

log = logging.getLogger(__name__)

MIRROR_HOST = "https://bmclapi2.bangbang93.com"

_URL_MAP: tuple[tuple[str, str], ...] = (
    ("https://launchermeta.mojang.com", MIRROR_HOST),
    ("https://piston-meta.mojang.com", MIRROR_HOST),
    ("https://piston-data.mojang.com", MIRROR_HOST),
    ("https://launcher.mojang.com", MIRROR_HOST),
    ("https://resources.download.minecraft.net", MIRROR_HOST + "/assets"),
    ("https://libraries.minecraft.net", MIRROR_HOST + "/maven"),
    ("https://files.minecraftforge.net/maven", MIRROR_HOST + "/maven"),
    ("https://maven.minecraftforge.net", MIRROR_HOST + "/maven"),
    ("https://meta.fabricmc.net", MIRROR_HOST + "/fabric-meta"),
    ("https://maven.fabricmc.net", MIRROR_HOST + "/maven"),
)

_PROBE_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
_MIRROR_PROBE_URL = MIRROR_HOST + "/mc/game/version_manifest_v2.json"

_lock = threading.Lock()
_checked = False
_enabled = False


def rewrite(url: str) -> str:
    for prefix, replacement in _URL_MAP:
        if url.startswith(prefix):
            return replacement + url[len(prefix):]
    return url


def is_enabled() -> bool:
    return _enabled


def rewrite_if_enabled(url: str) -> str:
    return rewrite(url) if _enabled else url


def _reachable(url: str, timeout: float) -> bool:
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        return resp.status_code < 500
    except requests.RequestException:
        return False


def _patch_mll() -> None:
    import minecraft_launcher_lib._helper as helper

    original_download = helper.download_file
    original_cache_get = helper.get_requests_response_cache

    def patched_download(url: str, *args, **kwargs):  # noqa: ANN002, ANN003
        return original_download(rewrite(url), *args, **kwargs)

    def patched_cache_get(url: str):
        return original_cache_get(rewrite(url))

    helper.download_file = patched_download
    helper.get_requests_response_cache = patched_cache_get

    # Other mll modules import these names directly (`from ._helper import
    # download_file`), so patch those references too.
    import minecraft_launcher_lib as mll

    for module_name in dir(mll):
        module = getattr(mll, module_name, None)
        if module is None or not hasattr(module, "__file__"):
            continue
        if getattr(module, "download_file", None) is original_download:
            module.download_file = patched_download
        if getattr(module, "get_requests_response_cache", None) is original_cache_get:
            module.get_requests_response_cache = patched_cache_get


def ensure_checked(timeout: float = 6.0) -> bool:
    """Probe Mojang once; enable the mirror if it's down. Returns is_enabled()."""
    global _checked, _enabled
    with _lock:
        if _checked:
            return _enabled
        _checked = True
        if _reachable(_PROBE_URL, timeout):
            log.info("Mojang reachable; mirror not needed")
            return False
        if not _reachable(_MIRROR_PROBE_URL, timeout):
            log.warning("Neither Mojang nor the BMCLAPI mirror is reachable")
            return False
        try:
            _patch_mll()
            _enabled = True
            log.warning("Mojang unreachable — switched downloads to BMCLAPI mirror")
        except Exception as exc:  # noqa: BLE001
            log.error("Failed to enable mirror: %s", exc)
        return _enabled


def reset_for_tests() -> None:
    global _checked, _enabled
    _checked = False
    _enabled = False
