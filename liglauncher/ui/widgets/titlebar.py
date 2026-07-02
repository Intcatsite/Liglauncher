"""Custom, borderless title bar that visually blends into the window background."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class TitleBar(QWidget):
    minimize_clicked = Signal()
    toggle_fullscreen_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(44)
        self._drag_active = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 8, 0)
        layout.setSpacing(6)

        icon = QLabel("▣")  # simple glyph, no external asset needed
        icon.setStyleSheet("font-size: 14pt;")
        layout.addWidget(icon)

        self.title_label = QLabel(title)
        layout.addWidget(self.title_label)
        layout.addStretch(1)

        self.btn_min = QPushButton("–")
        self.btn_min.setObjectName("TitleButton")
        self.btn_min.setCursor(Qt.PointingHandCursor)
        self.btn_min.clicked.connect(self.minimize_clicked.emit)

        self.btn_fullscreen = QPushButton("⛶")
        self.btn_fullscreen.setObjectName("TitleButton")
        self.btn_fullscreen.setCursor(Qt.PointingHandCursor)
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen_clicked.emit)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("TitleButton")
        self.btn_close.setProperty("close", True)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.close_clicked.emit)

        for b in (self.btn_min, self.btn_fullscreen, self.btn_close):
            layout.addWidget(b)

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
