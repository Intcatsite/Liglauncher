"""Account + version picker and the big Play button."""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...config import LauncherConfig, save_config
from ...core import installer, versions
from ...core.accounts import AccountManager
from ...core.auth import OfflineAccount
from ...core.errors import friendly_message
from ...core.installer import InstallTarget
from ...core.launcher import LaunchOptions, launch
from ...core.skins import SkinStore
from .. import dialogs
from ..imaging import pil_to_pixmap
from ..workers import Worker

log = logging.getLogger(__name__)


class PlayPage(QWidget):
    def __init__(self, cfg: LauncherConfig, accounts: AccountManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self.accounts = accounts
        self.skins = SkinStore()
        self._worker: Worker | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(18)

        title = QLabel("Играть")
        title.setObjectName("PageTitle")
        outer.addWidget(title)

        card = QWidget()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 22, 22, 22)
        card_layout.setSpacing(14)
        outer.addWidget(card)

        # Account row
        acc_row = QHBoxLayout()
        self.avatar = QLabel()
        self.avatar.setFixedSize(48, 48)
        acc_row.addWidget(self.avatar)

        self.account_combo = QComboBox()
        self.account_combo.currentIndexChanged.connect(self._on_account_changed)
        acc_row.addWidget(self.account_combo, 1)
        card_layout.addLayout(acc_row)

        # Version row
        ver_row = QHBoxLayout()
        self.loader_combo = QComboBox()
        self.loader_combo.addItems(["vanilla", "fabric", "forge", "quilt"])
        ver_row.addWidget(QLabel("Загрузчик:"))
        ver_row.addWidget(self.loader_combo)

        self.version_combo = QComboBox()
        ver_row.addWidget(QLabel("Версия:"))
        ver_row.addWidget(self.version_combo, 1)
        card_layout.addLayout(ver_row)

        self.skin_hint = QLabel()
        self.skin_hint.setObjectName("Muted")
        self.skin_hint.setWordWrap(True)
        card_layout.addWidget(self.skin_hint)

        self.status_label = QLabel("")
        self.status_label.setObjectName("Muted")
        card_layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        card_layout.addWidget(self.progress)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.play_btn = QPushButton("ИГРАТЬ")
        self.play_btn.setObjectName("Primary")
        self.play_btn.setMinimumWidth(180)
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.clicked.connect(self._on_play)
        btn_row.addWidget(self.play_btn)
        card_layout.addLayout(btn_row)

        outer.addStretch(1)

        self.refresh_accounts()
        self._load_versions()

    # -- data population --------------------------------------------------

    def refresh_accounts(self) -> None:
        self.account_combo.blockSignals(True)
        self.account_combo.clear()
        for acc in self.accounts.list():
            self.account_combo.addItem(acc.name, acc.uuid)
        if self.cfg.active_account_uuid:
            idx = self.account_combo.findData(self.cfg.active_account_uuid)
            if idx >= 0:
                self.account_combo.setCurrentIndex(idx)
        self.account_combo.blockSignals(False)
        self._on_account_changed()

    def _load_versions(self) -> None:
        try:
            game_dir = self.cfg.resolved_game_dir()
            installed = versions.installed_ids(game_dir)
            common = ["1.21.1", "1.20.4", "1.19.4", "1.18.2", "1.16.5", "1.12.2", "1.8.9"]
            for v in common:
                label = f"{v} ✓" if v in installed else v
                self.version_combo.addItem(label, v)
            if self.cfg.version_id:
                idx = self.version_combo.findData(self.cfg.version_id)
                if idx >= 0:
                    self.version_combo.setCurrentIndex(idx)
        except Exception as exc:  # noqa: BLE001
            log.warning("Failed to populate versions: %s", exc)
        self.version_combo.currentIndexChanged.connect(self._update_skin_hint)
        self.loader_combo.currentIndexChanged.connect(self._update_skin_hint)
        self._update_skin_hint()

    def _on_account_changed(self) -> None:
        uid = self.account_combo.currentData()
        if uid:
            head = self.skins.head_icon(uid, self._current_version(), size=48)
            self.avatar.setPixmap(pil_to_pixmap(head))
            self.cfg.active_account_uuid = uid
        else:
            self.avatar.clear()
        self._update_skin_hint()

    def _current_version(self) -> str | None:
        return self.version_combo.currentData()

    def _update_skin_hint(self) -> None:
        loader = self.loader_combo.currentText()
        uid = self.account_combo.currentData()
        has_skin = bool(uid and self.skins.get_skin(uid, self._current_version()))
        if not has_skin:
            self.skin_hint.setText("")
        elif loader == "vanilla":
            self.skin_hint.setText(
                "⚠ Скин загружен, но ванильный клиент не умеет показывать локальные скины офлайн-аккаунтов. "
                "Выберите Fabric или Forge — лаунчер сам поставит CustomSkinLoader."
            )
        else:
            self.skin_hint.setText("✓ При запуске скин будет установлен автоматически (CustomSkinLoader).")

    # -- play --------------------------------------------------------------

    def _on_play(self) -> None:
        uid = self.account_combo.currentData()
        if not uid:
            dialogs.warning(self, self.cfg, "Нет аккаунта", "Сначала создайте аккаунт на странице «Аккаунты».")
            return
        acc = self.accounts.get(uid)
        mc_version = self._current_version()
        if not mc_version:
            dialogs.warning(self, self.cfg, "Нет версии", "Выберите версию Minecraft.")
            return

        loader = self.loader_combo.currentText()
        self.cfg.version_id = mc_version
        self.cfg.active_account_uuid = uid
        save_config(self.cfg)

        self.play_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.status_label.setText("Установка…")

        target = InstallTarget(mc_version=mc_version, loader=loader)
        game_dir = self.cfg.resolved_game_dir()

        def work() -> str:
            def on_progress(status: str, cur: int, total: int) -> None:
                pass  # progress bar stays in indeterminate mode; status text below
            return installer.install_target(target, game_dir, progress=on_progress)

        self._worker = Worker(work)
        self._worker.finished_ok.connect(lambda resolved_id: self._do_launch(acc, mc_version, loader, resolved_id, game_dir))
        self._worker.failed.connect(self._on_install_failed)
        self._worker.start()

    def _do_launch(self, acc, mc_version: str, loader: str, resolved_id: str, game_dir: Path) -> None:
        self.status_label.setText("Запуск игры…")
        try:
            opts = LaunchOptions(
                account=OfflineAccount(name=acc.name, uuid=acc.uuid),
                version_id=resolved_id,
                mc_version=mc_version,
                loader=loader,
                game_dir=game_dir,
                ram_mb=self.cfg.ram_mb,
                java_path=self.cfg.java_path,
                extra_jvm_args=self.cfg.jvm_args,
            )
            launch(opts)
            self.status_label.setText("Игра запущена.")
        except Exception as exc:  # noqa: BLE001
            dialogs.critical(self, self.cfg, "Ошибка запуска", friendly_message(str(exc)))
            self.status_label.setText("Ошибка запуска.")
        finally:
            self.progress.setVisible(False)
            self.play_btn.setEnabled(True)

    def _on_install_failed(self, message: str) -> None:
        self.progress.setVisible(False)
        self.play_btn.setEnabled(True)
        self.status_label.setText("Ошибка установки.")
        dialogs.critical(self, self.cfg, "Ошибка установки", friendly_message(message))
