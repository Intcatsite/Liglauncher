"""Update-available dialog: shows the changelog, downloads the new build
with a progress bar, then hands off to the self-updater and quits."""
from __future__ import annotations

import logging

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..config import LauncherConfig
from ..core import updater
from ..core.errors import friendly_message
from ..core.updater import UpdateInfo
from . import dialogs
from .theme import Palette
from .workers import Worker

log = logging.getLogger(__name__)


def check_and_offer_update(parent: QWidget, cfg: LauncherConfig, *, silent: bool) -> None:
    """Check GitHub Releases for a newer build.

    ``silent`` controls behavior when there's nothing to report: True (used
    for the automatic startup check) stays quiet on "no update"/network
    errors; False (manual "Проверить обновления" click) always tells the
    user something.
    """
    worker = Worker(updater.check_for_update)

    def on_result(info: UpdateInfo | None) -> None:
        if info is None:
            if not silent:
                dialogs.info(parent, cfg, "Обновления", f"У вас последняя версия ({__version__}).")
            return
        if not updater.is_frozen():
            if not silent:
                dialogs.info(
                    parent,
                    cfg,
                    "Доступна новая версия",
                    f"Вышла версия {info.version}, но автообновление работает только в собранном "
                    ".exe, а не при запуске из исходников.",
                )
            return
        dlg = UpdateDialog(parent, cfg, info)
        dlg.restart_requested.connect(QApplication.instance().quit)
        dlg.show_centered()
        parent._update_dialog_ref = dlg  # keep alive

    def on_failed(message: str) -> None:
        log.info("Update check failed: %s", message)
        if not silent:
            dialogs.warning(
                parent,
                cfg,
                "Обновления",
                "Не удалось проверить обновления — либо нет интернет-соединения, "
                "либо на GitHub ещё не опубликовано ни одного релиза.",
            )

    worker.finished_ok.connect(on_result)
    worker.failed.connect(on_failed)
    parent._update_worker_ref = worker  # keep alive
    worker.start()


class UpdateDialog(QDialog):
    restart_requested = Signal()

    def __init__(self, parent: QWidget | None, cfg: LauncherConfig, info: UpdateInfo) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self.info = info
        self._worker: Worker | None = None

        self.setObjectName("ThemedDialog")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(420)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 22, 24, 20)
        outer.setSpacing(14)

        top = QHBoxLayout()
        top.setSpacing(12)
        badge = QLabel("↑")
        badge.setFixedSize(34, 34)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            "background: #2f7bf6; color: white; border-radius: 17px; font-weight: 700; font-size: 14pt;"
        )
        top.addWidget(badge, 0, Qt.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        title = QLabel(f"Доступна версия {info.version}")
        title.setStyleSheet("font-size: 12pt; font-weight: 700;")
        title.setWordWrap(True)
        text_col.addWidget(title)

        notes = info.notes[:500] or "Список изменений не указан."
        notes_lbl = QLabel(notes)
        notes_lbl.setWordWrap(True)
        notes_lbl.setObjectName("Muted")
        notes_lbl.setMaximumHeight(140)
        text_col.addWidget(notes_lbl)
        top.addLayout(text_col, 1)
        outer.addLayout(top)

        self.status_label = QLabel("")
        self.status_label.setObjectName("Muted")
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)
        outer.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        outer.addWidget(self.progress)

        self.btn_row = QHBoxLayout()
        self.btn_row.addStretch(1)
        self.later_btn = QPushButton("Позже")
        self.later_btn.setObjectName("Secondary")
        self.later_btn.setCursor(Qt.PointingHandCursor)
        self.later_btn.clicked.connect(self.reject)
        self.btn_row.addWidget(self.later_btn)

        self.update_btn = QPushButton("Обновить")
        self.update_btn.setObjectName("Primary")
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.clicked.connect(self._start_download)
        self.btn_row.addWidget(self.update_btn)
        outer.addLayout(self.btn_row)

    # -- download + apply --------------------------------------------------

    def _start_download(self) -> None:
        self.later_btn.setEnabled(False)
        self.update_btn.setEnabled(False)
        self.update_btn.setText("Загрузка…")
        self.status_label.setVisible(True)
        self.status_label.setText("Скачивание обновления…")
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)

        worker = Worker(self._download_and_apply)
        worker.progress.connect(self._on_progress)
        worker.finished_ok.connect(self._on_done)
        worker.failed.connect(self._on_failed)
        self._worker = worker
        worker.start()

    def _download_and_apply(self):
        worker = self._worker

        def on_progress(done: int, total: int) -> None:
            if worker is not None:
                worker.progress.emit("", done, total)

        path = updater.download_update(self.info, on_progress=on_progress)
        updater.apply_update(path)

    def _on_progress(self, _status: str, done: int, total: int) -> None:
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(done)
            mb_done = done / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.status_label.setText(f"Скачивание обновления… {mb_done:.1f} / {mb_total:.1f} МБ")

    def _on_done(self, _result) -> None:
        self.status_label.setText("Готово — перезапуск…")
        self.restart_requested.emit()
        self.accept()

    def _on_failed(self, message: str) -> None:
        self.status_label.setText(f"Не удалось обновить: {friendly_message(message)}")
        self.progress.setVisible(False)
        self.later_btn.setEnabled(True)
        self.update_btn.setEnabled(True)
        self.update_btn.setText("Обновить")

    # -- painting ------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        palette = Palette.from_theme(self.cfg.theme)
        radius = self.cfg.theme.corner_radius + 2
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(path)
        painter.fillRect(rect, QColor(255, 255, 255, 250))
        painter.setPen(palette.border)
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
        super().paintEvent(event)

    def _center_on_parent(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        top = parent.window()
        geo = top.geometry()
        self.adjustSize()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + (geo.height() - self.height()) // 2
        self.move(x, y)

    def show_centered(self) -> None:
        self._center_on_parent()
        self.show()
