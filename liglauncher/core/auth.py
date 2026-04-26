"""Offline authentication.

Generates a deterministic offline-mode UUID from a username, the same way the
vanilla Minecraft server does for offline players (Java edition):

    uuid = UUID.nameUUIDFromBytes(("OfflinePlayer:" + username).getBytes())

This lets the launcher work fully offline, without any Microsoft account.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass


_VALID_NAME = re.compile(r"^[A-Za-z0-9_]{3,16}$")


def is_valid_username(name: str) -> bool:
    """Vanilla-compatible offline name: 3..16 chars, [A-Za-z0-9_]."""
    return bool(_VALID_NAME.match(name or ""))


def offline_uuid(username: str) -> str:
    """Replicate Java's UUID.nameUUIDFromBytes(("OfflinePlayer:"+name).getBytes())."""
    md5 = hashlib.md5(f"OfflinePlayer:{username}".encode("utf-8")).digest()
    b = bytearray(md5)
    # Set version to 3 (name-based MD5).
    b[6] = (b[6] & 0x0F) | 0x30
    # Set variant to IETF.
    b[8] = (b[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(b)))


@dataclass(frozen=True)
class OfflineAccount:
    name: str
    uuid: str
    token: str = "0"  # any non-empty token works for offline launches

    @classmethod
    def from_username(cls, username: str) -> "OfflineAccount":
        return cls(name=username, uuid=offline_uuid(username))

    def as_options(self) -> dict:
        """Options dict expected by minecraft_launcher_lib.command.get_minecraft_command."""
        return {
            "username": self.name,
            "uuid": self.uuid,
            "token": self.token,
        }
