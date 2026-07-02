"""Create Server: spins up a local vanilla server and, once it's online,
tunnels it publicly through CraftIP so you get a real `xxxx.craftip.net`
address to hand out to friends."""
from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...config import LauncherConfig
from ...core import craftip, server as server_core
from ...core.errors import friendly_message
from .. import dialogs
from ..workers import Worker

log = logging.getLogger(__name__)


class _Bridge(QObject):
    line = Signal(str)
    address = Signal(str)
    ready = Signal()


class ServersPage(QWidget):
    def __init__(self, cfg: LauncherConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self._managed: server_core.ManagedServer | None = None
        self._tunnel: craftip.Tunnel | None = None
        self._bridge = _Bridge()
        self._bridge.line.connect(self._append_log)
        self._bridge.address.connect(self._on_address)
        self._bridge.ready.connect(self._on_server_ready)
        self._create_worker: Worker | None = None
        self._build_worker: Worker | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(14)

        title = QLabel("Создать сервер")
        title.setObjectName("PageTitle")
        outer.addWidget(title)

        card = QWidget()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(10)
        outer.addWidget(card)

        row1 = QHBoxLayout()
        self.name_field = QLineEdit("MyServer")
        row1.addWidget(QLabel("Имя:"))
        row1.addWidget(self.name_field, 1)
        self.version_combo = QComboBox()
        self.version_combo.addItems(["1.21.1", "1.20.4", "1.19.4", "1.18.2", "1.16.5", "1.12.2"])
        row1.addWidget(QLabel("Версия:"))
        row1.addWidget(self.version_combo)
        card_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(25565)
        row2.addWidget(QLabel("Порт:"))
        row2.addWidget(self.port_spin)
        self.ram_spin = QSpinBox()
        self.ram_spin.setRange(512, 16384)
        self.ram_spin.setSingleStep(512)
        self.ram_spin.setValue(2048)
        row2.addWidget(QLabel("RAM (MB):"))
        row2.addWidget(self.ram_spin)
        row2.addStretch(1)
        self.create_btn = QPushButton("Создать сервер")
        self.create_btn.setObjectName("Primary")
        self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.clicked.connect(self._on_create)
        row2.addWidget(self.create_btn)
        card_layout.addLayout(row2)

        addr_row = QHBoxLayout()
        self.address_label = QLabel("Адрес появится здесь после запуска сервера…")
        self.address_label.setObjectName("Muted")
        addr_row.addWidget(self.address_label, 1)
        self.copy_btn = QPushButton("Копировать")
        self.copy_btn.setObjectName("Secondary")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self._copy_address)
        addr_row.addWidget(self.copy_btn)
        card_layout.addLayout(addr_row)

        craftip_row = QHBoxLayout()
        self.craftip_status = QLabel()
        self.craftip_status.setObjectName("Muted")
        craftip_row.addWidget(self.craftip_status, 1)
        self.build_craftip_btn = QPushButton("Собрать CraftIP")
        self.build_craftip_btn.setObjectName("Secondary")
        self.build_craftip_btn.clicked.connect(self._on_build_craftip)
        craftip_row.addWidget(self.build_craftip_btn)
        card_layout.addLayout(craftip_row)
        self._refresh_craftip_status()

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(220)
        outer.addWidget(self.log_view, 1)

    # -- craftip status -------------------------------------------------

    def _refresh_craftip_status(self) -> None:
        if craftip.is_available():
            self.craftip_status.setText("CraftIP: клиент готов ✓")
            self.build_craftip_btn.setVisible(False)
        else:
            missing = craftip.build_prerequisites_missing()
            if missing:
                self.craftip_status.setText(
                    "CraftIP ещё не собран. Не хватает: " + ", ".join(missing)
                )
                self.build_craftip_btn.setEnabled(False)
            else:
                self.craftip_status.setText("CraftIP ещё не собран.")
                self.build_craftip_btn.setEnabled(True)
            self.build_craftip_btn.setVisible(True)

    def _on_build_craftip(self) -> None:
        self.build_craftip_btn.setEnabled(False)
        self._append_log("Сборка CraftIP-клиента из исходников (codeberg.org/craftip/craftip)…")
        self._build_worker = Worker(craftip.build_client, on_line=self._bridge.line.emit)
        self._build_worker.finished_ok.connect(lambda _p: self._refresh_craftip_status())
        self._build_worker.failed.connect(
            lambda msg: dialogs.warning(self, self.cfg, "Сборка не удалась", friendly_message(msg))
        )
        self._build_worker.finished_ok.connect(lambda _p: self.build_craftip_btn.setEnabled(True))
        self._build_worker.failed.connect(lambda _m: self.build_craftip_btn.setEnabled(True))
        self._build_worker.start()

    # -- create + start ---------------------------------------------------

    def _on_create(self) -> None:
        self.create_btn.setEnabled(False)
        self.log_view.clear()
        name = self.name_field.text().strip() or "server"
        mc_version = self.version_combo.currentText()
        port = self.port_spin.value()

        def work():
            srv = server_core.create_server(name, mc_version, port, progress=self._bridge.line.emit)
            server_core.start_server(
                srv,
                ram_mb=self.ram_spin.value(),
                java_path=self.cfg.java_path or "java",
                on_line=self._bridge.line.emit,
                on_ready=self._bridge.ready.emit,
            )
            return srv

        self._create_worker = Worker(work)
        self._create_worker.finished_ok.connect(self._on_server_created)
        self._create_worker.failed.connect(self._on_create_failed)
        self._create_worker.start()

    def _on_server_created(self, srv: server_core.ManagedServer) -> None:
        self._managed = srv
        self.create_btn.setEnabled(True)
        self.create_btn.setText("Сервер запускается…")
        self.create_btn.setEnabled(False)

    def _on_create_failed(self, message: str) -> None:
        self.create_btn.setEnabled(True)
        dialogs.critical(self, self.cfg, "Не удалось создать сервер", friendly_message(message))

    def _on_server_ready(self) -> None:
        self._append_log("Сервер запущен и готов принимать игроков.")
        if not craftip.is_available():
            self.address_label.setText(
                f"Локально: localhost:{self._managed.port if self._managed else self.port_spin.value()} "
                "(соберите CraftIP выше, чтобы получить публичный адрес)"
            )
            return
        try:
            self._tunnel = craftip.start_tunnel(
                self._managed.port,
                on_line=self._bridge.line.emit,
                on_address=self._bridge.address.emit,
            )
            self.address_label.setText("Открываем туннель CraftIP…")
        except craftip.CraftIpUnavailable as exc:
            self.address_label.setText(str(exc))

    def _on_address(self, address: str) -> None:
        self.address_label.setText(f"Публичный адрес: {address}")
        self.copy_btn.setEnabled(True)
        self._last_address = address

    def _copy_address(self) -> None:
        if getattr(self, "_last_address", None):
            QApplication.clipboard().setText(self._last_address)

    def _append_log(self, text: str) -> None:
        self.log_view.appendPlainText(text)
