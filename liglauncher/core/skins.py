"""Per-account, per-version skin storage.

Each account can have a custom skin (uploaded as .png or .jpg) stored under
    <skins_dir>/<account_uuid>/<version_id>/skin.png
so different Minecraft versions can use different skins for the same
account. A skin stored under the special "_default" version is used as a
fallback whenever a version-specific skin hasn't been set.

Because vanilla offline-mode Minecraft never asks Mojang for a skin (the
account isn't real), the texture only shows up in-game through a local skin
mod such as CustomSkinLoader (see core/skinloader.py) — the files written
here are exactly the layout that mod expects. In the launcher UI itself the
skin is always shown via the rendered head icon below.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PIL import Image

from ..paths import skins_dir

log = logging.getLogger(__name__)

DEFAULT_SLOT = "_default"
VALID_SKIN_SIZES = {(64, 64), (64, 32)}


class InvalidSkinError(Exception):
    pass


def _slot_dir(account_uuid: str, version_id: Optional[str]) -> Path:
    return skins_dir() / account_uuid / (version_id or DEFAULT_SLOT)


def _load_and_validate(source: Path) -> Image.Image:
    try:
        img = Image.open(source)
        img.load()
    except Exception as exc:  # noqa: BLE001
        raise InvalidSkinError(f"Не удалось открыть изображение: {exc}") from exc

    if img.size not in VALID_SKIN_SIZES:
        raise InvalidSkinError(
            f"Неверный размер скина {img.size[0]}x{img.size[1]}. "
            "Нужен PNG/JPG размером 64x64 (или старый формат 64x32)."
        )
    return img.convert("RGBA")


def _normalize(img: Image.Image) -> Image.Image:
    """Upgrade legacy 64x32 skins to a full 64x64 canvas (transparent 2nd layer)."""
    if img.size == (64, 64):
        return img
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    canvas.paste(img, (0, 0))
    return canvas


class SkinStore:
    def set_skin(
        self, account_uuid: str, source_path: Path, version_id: Optional[str] = None
    ) -> Path:
        """Validate + store a skin for an account (optionally scoped to a version)."""
        img = _normalize(_load_and_validate(Path(source_path)))
        dest_dir = _slot_dir(account_uuid, version_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "skin.png"
        img.save(dest, format="PNG")
        log.info("Stored skin for %s (%s) -> %s", account_uuid, version_id or "default", dest)
        return dest

    def get_skin(self, account_uuid: str, version_id: Optional[str] = None) -> Optional[Path]:
        """Resolve the skin to use: version-specific first, then the account default."""
        if version_id:
            candidate = _slot_dir(account_uuid, version_id) / "skin.png"
            if candidate.exists():
                return candidate
        default = _slot_dir(account_uuid, None) / "skin.png"
        return default if default.exists() else None

    def delete_skin(self, account_uuid: str, version_id: Optional[str] = None) -> None:
        candidate = _slot_dir(account_uuid, version_id) / "skin.png"
        if candidate.exists():
            candidate.unlink()

    def delete_all_for_account(self, account_uuid: str) -> None:
        import shutil

        d = skins_dir() / account_uuid
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)

    def versions_with_custom_skin(self, account_uuid: str) -> list[str]:
        base = skins_dir() / account_uuid
        if not base.exists():
            return []
        return sorted(
            p.name for p in base.iterdir()
            if p.is_dir() and p.name != DEFAULT_SLOT and (p / "skin.png").exists()
        )

    def head_icon(
        self, account_uuid: str, version_id: Optional[str] = None, size: int = 64
    ) -> Image.Image:
        """Composited front-facing head (base layer + hat overlay), nearest-neighbor scaled."""
        skin_path = self.get_skin(account_uuid, version_id)
        if skin_path is None:
            return _placeholder_head(size)
        try:
            img = Image.open(skin_path).convert("RGBA")
        except Exception as exc:  # noqa: BLE001
            log.warning("Failed to render head icon for %s: %s", account_uuid, exc)
            return _placeholder_head(size)

        base = img.crop((8, 8, 16, 16))
        head = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        head.paste(base, (0, 0))
        if img.size == (64, 64):
            hat = img.crop((40, 8, 48, 16))
            head.alpha_composite(hat)
        return head.resize((size, size), Image.NEAREST)


def _placeholder_head(size: int) -> Image.Image:
    """Flat Steve-ish grey head used when no skin has been set."""
    img = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    skin_tone = (152, 113, 89, 255)
    for y in range(8):
        for x in range(8):
            img.putpixel((x, y), skin_tone)
    return img.resize((size, size), Image.NEAREST)
