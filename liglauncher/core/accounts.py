"""Multi-account manager for offline profiles.

Supports creating as many offline accounts as the user wants (tested up to
several thousand) — each backed by the same deterministic offline UUID
scheme used by vanilla Minecraft, so no network/Microsoft account is ever
required.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from ..paths import accounts_path
from .auth import OfflineAccount, is_valid_username, offline_uuid

log = logging.getLogger(__name__)

# Generous upper bound so a runaway loop / corrupt import can't grow the
# accounts file without limit. Far above the "create 1000 accounts" ask.
MAX_ACCOUNTS = 5000


class DuplicateAccountError(Exception):
    pass


class AccountLimitError(Exception):
    pass


@dataclass
class Account:
    name: str
    uuid: str
    created_at: float = field(default_factory=time.time)

    def to_offline(self) -> OfflineAccount:
        return OfflineAccount(name=self.name, uuid=self.uuid)


class AccountManager:
    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = path or accounts_path()
        self._accounts: dict[str, Account] = {}
        self.load()

    # -- persistence ---------------------------------------------------

    def load(self) -> None:
        self._accounts = {}
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            for entry in raw:
                acc = Account(
                    name=entry["name"],
                    uuid=entry["uuid"],
                    created_at=entry.get("created_at", time.time()),
                )
                self._accounts[acc.uuid] = acc
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            log.warning("Failed to load accounts (%s); starting empty", exc)
            self._accounts = {}

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(a) for a in self.list()]
        try:
            self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            log.error("Failed to save accounts: %s", exc)

    # -- queries ---------------------------------------------------------

    def list(self) -> list[Account]:
        return sorted(self._accounts.values(), key=lambda a: a.created_at)

    def search(self, query: str) -> list[Account]:
        q = query.strip().lower()
        if not q:
            return self.list()
        return [a for a in self.list() if q in a.name.lower()]

    def get(self, uuid_: str) -> Optional[Account]:
        return self._accounts.get(uuid_)

    def get_by_name(self, name: str) -> Optional[Account]:
        return self._accounts.get(offline_uuid(name))

    def __len__(self) -> int:
        return len(self._accounts)

    # -- mutations ---------------------------------------------------------

    def create(self, name: str) -> Account:
        name = name.strip()
        if not is_valid_username(name):
            raise ValueError(
                "Никнейм должен быть 3-16 символов: латиница, цифры, подчёркивание."
            )
        if len(self._accounts) >= MAX_ACCOUNTS:
            raise AccountLimitError(f"Достигнут лимит в {MAX_ACCOUNTS} аккаунтов.")
        uid = offline_uuid(name)
        if uid in self._accounts:
            raise DuplicateAccountError(f"Аккаунт «{name}» уже существует.")
        acc = Account(name=name, uuid=uid)
        self._accounts[uid] = acc
        self.save()
        return acc

    def create_bulk(self, names: list[str]) -> tuple[list[Account], list[str]]:
        """Create many accounts at once (e.g. Player1..Player1000). Returns (created, errors)."""
        created: list[Account] = []
        errors: list[str] = []
        for name in names:
            try:
                created.append(self.create(name))
            except (ValueError, DuplicateAccountError, AccountLimitError) as exc:
                errors.append(f"{name}: {exc}")
        return created, errors

    def rename(self, uuid_: str, new_name: str) -> Account:
        new_name = new_name.strip()
        if not is_valid_username(new_name):
            raise ValueError(
                "Никнейм должен быть 3-16 символов: латиница, цифры, подчёркивание."
            )
        old = self._accounts.pop(uuid_, None)
        if old is None:
            raise KeyError(uuid_)
        new_uid = offline_uuid(new_name)
        if new_uid in self._accounts:
            self._accounts[uuid_] = old  # rollback
            raise DuplicateAccountError(f"Аккаунт «{new_name}» уже существует.")
        renamed = Account(name=new_name, uuid=new_uid, created_at=old.created_at)
        self._accounts[new_uid] = renamed
        self.save()
        return renamed

    def delete(self, uuid_: str) -> None:
        if self._accounts.pop(uuid_, None) is not None:
            self.save()

    def delete_all(self) -> None:
        self._accounts.clear()
        self.save()
