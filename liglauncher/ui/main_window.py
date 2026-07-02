"""Frameless, translucent main window with a custom title bar that blends
into the background, a side nav, and a stacked set of pages."""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QPushButton,
    QSizeGrip,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..config import LauncherConfig, save_config
from .theme import Palette, build_stylesheet
from .widgets.titlebar import TitleBar

log = logging.getLogger(__name__)

CORNER_RADIUS = 16


class MainWindow(QWidget):
    def __init__(self, cfg: LauncherConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self._background_pixmap: QPixmap | None = None
        self._resize_edge = None
        self._resize_start_geo = None
        self._resize_start_pos = None

        self.setWindowTitle("LigLauncher")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(920, 600)
        self.resize(cfg.theme.window_width, cfg.theme.window_height)
        self.setMouseTracking(True)

        self._build_ui()
        self.apply_theme()

        if cfg.theme.window_mode == "fullscreen":
            self.showFullScreen()

    # -- UI construction ---------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        self.title_bar = TitleBar("LigLauncher — Black Edition")
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.toggle_fullscreen_clicked.connect(self.toggle_fullscreen)
        self.title_bar.close_clicked.connect(self.close)
        root.addWidget(self.title_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root.addLayout(body, 1)

        self.nav = QWidget()
        self.nav.setObjectName("NavBar")
        self.nav.setFixedWidth(210)
        nav_layout = QVBoxLayout(self.nav)
        nav_layout.setContentsMargins(14, 20, 14, 14)
        nav_layout.setSpacing(6)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self._nav_buttons: dict[str, QPushButton] = {}

        for key, label in (
            ("play", "▶  Играть"),
            ("accounts", "👤  Аккаунты"),
            ("servers", "🌐  Серверы"),
            ("settings", "⚙  Настройки"),
        ):
            btn = QPushButton(label)
            btn.setObjectName("NavItem")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            nav_layout.addWidget(btn)
            self.nav_group.addButton(btn)
            self._nav_buttons[key] = btn

        nav_layout.addStretch(1)
        version_lbl = QPushButton(f"v{__version__}")
        version_lbl.setObjectName("NavItem")
        version_lbl.setEnabled(False)
        nav_layout.addWidget(version_lbl)

        body.addWidget(self.nav)

        self.pages = QStackedWidget()
        self.pages.setContentsMargins(0, 0, 0, 0)
        body.addWidget(self.pages, 1)

        grip_row = QHBoxLayout()
        grip_row.addStretch(1)
        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)
        grip_row.addWidget(grip)
        root.addLayout(grip_row)

    def register_page(self, key: str, widget: QWidget) -> None:
        index = self.pages.addWidget(widget)
        btn = self._nav_buttons.get(key)
        if btn is not None:
            btn.clicked.connect(lambda: self.pages.setCurrentIndex(index))
            if self.pages.count() == 1:
                btn.setChecked(True)

    # -- theming ---------------------------------------------------------

    def apply_theme(self) -> None:
        self.setStyleSheet(build_stylesheet(self.cfg.theme))
        self._background_pixmap = None
        if self.cfg.theme.background_path and Path(self.cfg.theme.background_path).exists():
            self._background_pixmap = QPixmap(self.cfg.theme.background_path)
        self.update()

    # -- painting: rounded, translucent, blended background -------------

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        radius = 0 if self.isFullScreen() else CORNER_RADIUS
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(path)

        if self._background_pixmap and not self._background_pixmap.isNull():
            scaled = self._background_pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            overlay = QColor(10, 10, 14)
            overlay.setAlphaF(1.0 - self.cfg.theme.window_opacity)
            painter.fillRect(rect, overlay)
        else:
            grad = QLinearGradient(0, 0, self.width(), self.height())
            accent = QColor(self.cfg.theme.accent_color)
            grad.setColorAt(0.0, QColor(12, 12, 18, int(255 * self.cfg.theme.window_opacity)))
            grad.setColorAt(1.0, QColor(accent.red() // 4, accent.green() // 4, accent.blue() // 4, int(255 * self.cfg.theme.window_opacity)))
            painter.fillRect(rect, grad)

        painter.setPen(Palette.from_theme(self.cfg.theme).border)
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
        super().paintEvent(event)

    # -- window mode -------------------------------------------------------

    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
            self.cfg.theme.window_mode = "windowed"
        else:
            self.showFullScreen()
            self.cfg.theme.window_mode = "fullscreen"
        save_config(self.cfg)
        self.update()

    def closeEvent(self, event) -> None:  # noqa: N802
        if not self.isFullScreen():
            self.cfg.theme.window_width = self.width()
            self.cfg.theme.window_height = self.height()
        save_config(self.cfg)
        super().closeEvent(event)
