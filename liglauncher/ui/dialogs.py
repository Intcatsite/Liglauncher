"""Themed replacement for QMessageBox — matches the app's frameless, rounded,
accent-colored look instead of the native OS dialog chrome."""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config import LauncherConfig
from .theme import Palette

_BADGE_COLORS = {
    "info": ("#2f7bf6", "i"),
    "warning": ("#f59e0b", "!"),
    "error": ("#ef4444", "×"),
    "question": ("#8b5cf6", "?"),
}


class ThemedDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        cfg: LauncherConfig,
        title: str,
        text: str,
        kind: str = "info",
        buttons: tuple[tuple[str, bool], ...] = (("OK", True),),
    ) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self.result_text: str | None = None
        self.setObjectName("ThemedDialog")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(380)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 22, 24, 20)
        outer.setSpacing(14)

        top = QHBoxLayout()
        top.setSpacing(12)
        color, glyph = _BADGE_COLORS.get(kind, _BADGE_COLORS["info"])
        badge = QLabel(glyph)
        badge.setFixedSize(34, 34)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f"background: {color}; color: white; border-radius: 17px; font-weight: 700; font-size: 14pt;"
        )
        top.addWidget(badge, 0, Qt.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("PageTitle")
        title_lbl.setStyleSheet("font-size: 12pt; font-weight: 700;")
        title_lbl.setWordWrap(True)
        text_col.addWidget(title_lbl)

        body_lbl = QLabel(text)
        body_lbl.setWordWrap(True)
        body_lbl.setObjectName("Muted")
        text_col.addWidget(body_lbl)
        top.addLayout(text_col, 1)

        outer.addLayout(top)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        for label, is_primary in buttons:
            btn = QPushButton(label)
            btn.setObjectName("Primary" if is_primary else "Secondary")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, t=label: self._choose(t))
            btn_row.addWidget(btn)
        outer.addLayout(btn_row)

    def _choose(self, text: str) -> None:
        self.result_text = text
        self.accept()

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

    def exec(self) -> str | None:  # noqa: A003
        self._center_on_parent()
        super().exec()
        return self.result_text


def info(parent: QWidget, cfg: LauncherConfig, title: str, text: str) -> None:
    ThemedDialog(parent, cfg, title, text, kind="info").exec()


def warning(parent: QWidget, cfg: LauncherConfig, title: str, text: str) -> None:
    ThemedDialog(parent, cfg, title, text, kind="warning").exec()


def critical(parent: QWidget, cfg: LauncherConfig, title: str, text: str) -> None:
    ThemedDialog(parent, cfg, title, text, kind="error").exec()


def question(parent: QWidget, cfg: LauncherConfig, title: str, text: str) -> bool:
    result = ThemedDialog(
        parent,
        cfg,
        title,
        text,
        kind="question",
        buttons=(("Отмена", False), ("Да", True)),
    ).exec()
    return result == "Да"
