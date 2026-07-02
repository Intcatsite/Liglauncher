"""Custom, borderless title bar that visually blends into the window background."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from .. import icons
from ...paths import assets_dir


class TitleBar(QWidget):
    minimize_clicked = Signal()
    toggle_fullscreen_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(44)
        self._is_fullscreen = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 8, 0)
        layout.setSpacing(6)

        self.icon_label = QLabel()
        icon_path = assets_dir() / "icon.png"
        if icon_path.exists():
            self.icon_label.setPixmap(
                QPixmap(str(icon_path)).scaled(
                    20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        layout.addWidget(self.icon_label)

        self.title_label = QLabel(title)
        layout.addWidget(self.title_label)
        layout.addStretch(1)

        self.btn_min = QPushButton()
        self.btn_min.setObjectName("TitleButton")
        self.btn_min.setCursor(Qt.PointingHandCursor)
        self.btn_min.clicked.connect(self.minimize_clicked.emit)

        self.btn_fullscreen = QPushButton()
        self.btn_fullscreen.setObjectName("TitleButton")
        self.btn_fullscreen.setCursor(Qt.PointingHandCursor)
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen_clicked.emit)

        self.btn_close = QPushButton()
        self.btn_close.setObjectName("TitleButton")
        self.btn_close.setProperty("close", True)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.close_clicked.emit)

        for b in (self.btn_min, self.btn_fullscreen, self.btn_close):
            layout.addWidget(b)

        self.apply_icon_colors("#0f172a")

    # -- theming -----------------------------------------------------------

    def apply_icon_colors(self, color: str, close_hover_color: str = "#ffffff") -> None:
        self.btn_min.setIcon(icons.icon("minimize", color, size=16))
        self._fs_color = color
        self._set_fullscreen_icon()
        self.btn_close.setIcon(icons.icon("close", color, size=16))
        self._close_hover_color = close_hover_color

    def set_fullscreen(self, is_fullscreen: bool) -> None:
        self._is_fullscreen = is_fullscreen
        self._set_fullscreen_icon()

    def _set_fullscreen_icon(self) -> None:
        name = "fullscreen_exit" if self._is_fullscreen else "fullscreen"
        self.btn_fullscreen.setIcon(icons.icon(name, self._fs_color, size=16))

    # -- window dragging -------------------------------------------------

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemMove()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self.toggle_fullscreen_clicked.emit()
        super().mouseDoubleClickEvent(event)
