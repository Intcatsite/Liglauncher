"""Offline multi-account manager: create as many accounts as you want (bulk
creation up to 1000+ in one go), rename, delete, and set a per-version skin
for each one."""
from __future__ import annotations

import logging

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...core.accounts import AccountManager, DuplicateAccountError, AccountLimitError
from ...core.skins import InvalidSkinError, SkinStore
from ..imaging import pil_to_pixmap

log = logging.getLogger(__name__)

COMMON_VERSIONS = ["_default", "1.21.1", "1.20.4", "1.19.4", "1.18.2", "1.16.5", "1.12.2", "1.8.9"]


class AccountsPage(QWidget):
    def __init__(self, accounts: AccountManager, on_changed=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.accounts = accounts
        self.skins = SkinStore()
        self._on_changed = on_changed
        self._icon_cache: dict[str, QIcon] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(14)

        title = QLabel("Аккаунты")
        title.setObjectName("PageTitle")
        outer.addWidget(title)

        body = QHBoxLayout()
        body.setSpacing(18)
        outer.addLayout(body, 1)

        # -- left: list + create controls -----------------------------------
        left = QVBoxLayout()
        body.addLayout(left, 1)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по нику…")
        self.search.textChanged.connect(self._refresh_list)
        left.addWidget(self.search)

        self.list = QListWidget()
        self.list.setIconSize(QSize(32, 32))
        self.list.currentItemChanged.connect(self._on_selection_changed)
        left.addWidget(self.list, 1)

        add_row = QHBoxLayout()
        self.new_name = QLineEdit()
        self.new_name.setPlaceholderText("Ник (3-16 симв.)")
        add_row.addWidget(self.new_name, 1)
        add_btn = QPushButton("+ Добавить")
        add_btn.setObjectName("Secondary")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_account)
        add_row.addWidget(add_btn)
        left.addLayout(add_row)

        bulk_row = QHBoxLayout()
        self.bulk_prefix = QLineEdit("Player")
        self.bulk_prefix.setPlaceholderText("Префикс")
        bulk_row.addWidget(self.bulk_prefix, 1)
        self.bulk_count = QSpinBox()
        self.bulk_count.setRange(1, 1000)
        self.bulk_count.setValue(100)
        bulk_row.addWidget(self.bulk_count)
        bulk_btn = QPushButton("Создать пачкой")
        bulk_btn.setObjectName("Secondary")
        bulk_btn.setCursor(Qt.PointingHandCursor)
        bulk_btn.clicked.connect(self._add_bulk)
        bulk_row.addWidget(bulk_btn)
        left.addLayout(bulk_row)

        self.count_label = QLabel()
        self.count_label.setObjectName("Muted")
        left.addWidget(self.count_label)

        # -- right: selected account details ---------------------------------
        right = QWidget()
        right.setObjectName("Card")
        right.setFixedWidth(340)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(12)
        body.addWidget(right)

        self.detail_avatar = QLabel()
        self.detail_avatar.setFixedSize(72, 72)
        self.detail_avatar.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.detail_avatar, 0, Qt.AlignHCenter)

        self.detail_name = QLabel("—")
        self.detail_name.setAlignment(Qt.AlignCenter)
        self.detail_name.setObjectName("PageTitle")
        right_layout.addWidget(self.detail_name)

        rename_row = QHBoxLayout()
        self.rename_field = QLineEdit()
        rename_row.addWidget(self.rename_field, 1)
        rename_btn = QPushButton("Переим.")
        rename_btn.setObjectName("Secondary")
        rename_btn.clicked.connect(self._rename_selected)
        rename_row.addWidget(rename_btn)
        right_layout.addLayout(rename_row)

        right_layout.addWidget(QLabel("Скин для версии:"))
        self.skin_version = QComboBox()
        self.skin_version.addItems(COMMON_VERSIONS)
        self.skin_version.currentIndexChanged.connect(self._refresh_detail_avatar)
        right_layout.addWidget(self.skin_version)

        skin_btn = QPushButton("Загрузить PNG/JPG…")
        skin_btn.setObjectName("Secondary")
        skin_btn.setCursor(Qt.PointingHandCursor)
        skin_btn.clicked.connect(self._upload_skin)
        right_layout.addWidget(skin_btn)

        hint = QLabel("64×64 (или старый 64×32). «_default» применяется, если для версии свой скин не задан.")
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        right_layout.addWidget(hint)

        right_layout.addStretch(1)

        delete_btn = QPushButton("Удалить аккаунт")
        delete_btn.setObjectName("Secondary")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(self._delete_selected)
        right_layout.addWidget(delete_btn)

        self._refresh_list()

    # -- helpers -------------------------------------------------------------

    def _icon_for(self, uid: str, version: str | None) -> QIcon:
        key = f"{uid}:{version or ''}"
        if key not in self._icon_cache:
            head = self.skins.head_icon(uid, version, size=32)
            self._icon_cache[key] = QIcon(pil_to_pixmap(head))
        return self._icon_cache[key]

    def _refresh_list(self) -> None:
        self.list.clear()
        query = self.search.text()
        accs = self.accounts.search(query) if query else self.accounts.list()
        for acc in accs:
            item = QListWidgetItem(self._icon_for(acc.uuid, None), acc.name)
            item.setData(Qt.UserRole, acc.uuid)
            self.list.addItem(item)
        self.count_label.setText(f"Всего аккаунтов: {len(self.accounts)}")

    def _selected_uuid(self) -> str | None:
        item = self.list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _on_selection_changed(self) -> None:
        uid = self._selected_uuid()
        if not uid:
            self.detail_name.setText("—")
            self.detail_avatar.clear()
            return
        acc = self.accounts.get(uid)
        if acc is None:
            return
        self.detail_name.setText(acc.name)
        self.rename_field.setText(acc.name)
        self._refresh_detail_avatar()

    def _refresh_detail_avatar(self) -> None:
        uid = self._selected_uuid()
        if not uid:
            return
        version = self.skin_version.currentText()
        version = None if version == "_default" else version
        head = self.skins.head_icon(uid, version, size=72)
        self.detail_avatar.setPixmap(pil_to_pixmap(head))

    def _notify_changed(self) -> None:
        self._icon_cache.clear()
        if self._on_changed:
            self._on_changed()

    # -- actions ---------------------------------------------------------

    def _add_account(self) -> None:
        name = self.new_name.text().strip()
        try:
            self.accounts.create(name)
        except (ValueError, DuplicateAccountError, AccountLimitError) as exc:
            QMessageBox.warning(self, "Не удалось создать аккаунт", str(exc))
            return
        self.new_name.clear()
        self._refresh_list()
        self._notify_changed()

    def _add_bulk(self) -> None:
        prefix = self.bulk_prefix.text().strip() or "Player"
        count = self.bulk_count.value()
        names = [f"{prefix}{i}" for i in range(1, count + 1)]
        created, errors = self.accounts.create_bulk(names)
        self._refresh_list()
        self._notify_changed()
        msg = f"Создано аккаунтов: {len(created)}."
        if errors:
            msg += f"\nПропущено (уже существуют/ошибка): {len(errors)}."
        QMessageBox.information(self, "Массовое создание", msg)

    def _rename_selected(self) -> None:
        uid = self._selected_uuid()
        if not uid:
            return
        try:
            self.accounts.rename(uid, self.rename_field.text())
        except (ValueError, DuplicateAccountError, KeyError) as exc:
            QMessageBox.warning(self, "Не удалось переименовать", str(exc))
            return
        self._refresh_list()
        self._notify_changed()

    def _delete_selected(self) -> None:
        uid = self._selected_uuid()
        if not uid:
            return
        acc = self.accounts.get(uid)
        if acc and QMessageBox.question(
            self, "Удалить аккаунт", f"Удалить «{acc.name}»? Скины аккаунта тоже будут удалены."
        ) == QMessageBox.Yes:
            self.skins.delete_all_for_account(uid)
            self.accounts.delete(uid)
            self._refresh_list()
            self._notify_changed()

    def _upload_skin(self) -> None:
        uid = self._selected_uuid()
        if not uid:
            QMessageBox.information(self, "Выберите аккаунт", "Сначала выберите аккаунт слева.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Выберите скин", "", "Изображения (*.png *.jpg *.jpeg)")
        if not path:
            return
        version = self.skin_version.currentText()
        version = None if version == "_default" else version
        try:
            self.skins.set_skin(uid, path, version)
        except InvalidSkinError as exc:
            QMessageBox.warning(self, "Неверный скин", str(exc))
            return
        self._refresh_detail_avatar()
        self._notify_changed()
        self._refresh_list()
