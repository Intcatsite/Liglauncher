"""Full UI customization: accent color, font, background, transparency and
window mode — plus the underlying game settings (RAM, Java, game folder)."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFontComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QColorDialog,
)

from ...config import LauncherConfig, save_config
from ...paths import backgrounds_dir


class SettingsPage(QWidget):
    def __init__(self, cfg: LauncherConfig, on_theme_changed: Callable[[], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self.on_theme_changed = on_theme_changed

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(16)

        title = QLabel("Настройки")
        title.setObjectName("PageTitle")
        outer.addWidget(title)

        outer.addWidget(self._theme_card())
        outer.addWidget(self._game_card())
        outer.addStretch(1)

    # -- theme card ---------------------------------------------------------

    def _theme_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(QLabel("Оформление"))

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Акцентный цвет:"))
        self.color_swatch = QPushButton()
        self.color_swatch.setFixedSize(32, 24)
        self._update_swatch()
        self.color_swatch.clicked.connect(self._pick_color)
        color_row.addWidget(self.color_swatch)
        color_row.addStretch(1)
        layout.addLayout(color_row)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Шрифт:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self.cfg.theme.font_family))
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        font_row.addWidget(self.font_combo, 1)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 18)
        self.font_size.setValue(self.cfg.theme.font_size)
        self.font_size.valueChanged.connect(self._on_font_size_changed)
        font_row.addWidget(self.font_size)
        layout.addLayout(font_row)

        bg_row = QHBoxLayout()
        bg_btn = QPushButton("Выбрать фон…")
        bg_btn.setObjectName("Secondary")
        bg_btn.setCursor(Qt.PointingHandCursor)
        bg_btn.clicked.connect(self._pick_background)
        bg_row.addWidget(bg_btn)
        clear_btn = QPushButton("Сбросить фон")
        clear_btn.setObjectName("Secondary")
        clear_btn.clicked.connect(self._clear_background)
        bg_row.addWidget(clear_btn)
        bg_row.addStretch(1)
        layout.addLayout(bg_row)

        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Прозрачность окна:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(40, 100)
        self.opacity_slider.setValue(int(self.cfg.theme.window_opacity * 100))
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_row.addWidget(self.opacity_slider, 1)
        layout.addLayout(opacity_row)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Режим окна:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Окно", "windowed")
        self.mode_combo.addItem("Полный экран", "fullscreen")
        idx = self.mode_combo.findData(self.cfg.theme.window_mode)
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch(1)
        layout.addLayout(mode_row)

        return card

    def _update_swatch(self) -> None:
        self.color_swatch.setStyleSheet(
            f"background: {self.cfg.theme.accent_color}; border-radius: 6px; border: 1px solid rgba(255,255,255,60);"
        )

    def _pick_color(self) -> None:
        from PySide6.QtGui import QColor

        color = QColorDialog.getColor(QColor(self.cfg.theme.accent_color), self, "Акцентный цвет")
        if color.isValid():
            self.cfg.theme.accent_color = color.name()
            self._update_swatch()
            self._commit()

    def _on_font_changed(self, font: QFont) -> None:
        self.cfg.theme.font_family = font.family()
        self._commit()

    def _on_font_size_changed(self, value: int) -> None:
        self.cfg.theme.font_size = value
        self._commit()

    def _pick_background(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Выберите фон", "", "Изображения (*.png *.jpg *.jpeg *.webp)")
        if not path:
            return
        backgrounds_dir().mkdir(parents=True, exist_ok=True)
        dest = backgrounds_dir() / Path(path).name
        try:
            shutil.copyfile(path, dest)
        except OSError:
            dest = Path(path)  # fall back to using it in place
        self.cfg.theme.background_path = str(dest)
        self._commit()

    def _clear_background(self) -> None:
        self.cfg.theme.background_path = ""
        self._commit()

    def _on_opacity_changed(self, value: int) -> None:
        self.cfg.theme.window_opacity = value / 100.0
        self._commit()

    def _on_mode_changed(self) -> None:
        self.cfg.theme.window_mode = self.mode_combo.currentData()
        self._commit()

    def _commit(self) -> None:
        save_config(self.cfg)
        self.on_theme_changed()

    # -- game settings card -------------------------------------------------

    def _game_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(QLabel("Игра"))

        ram_row = QHBoxLayout()
        ram_row.addWidget(QLabel("RAM по умолчанию (MB):"))
        ram_spin = QSpinBox()
        ram_spin.setRange(512, 32768)
        ram_spin.setSingleStep(512)
        ram_spin.setValue(self.cfg.ram_mb)
        ram_spin.valueChanged.connect(self._on_ram_changed)
        ram_row.addWidget(ram_spin)
        ram_row.addStretch(1)
        layout.addLayout(ram_row)

        java_row = QHBoxLayout()
        java_row.addWidget(QLabel("Путь к Java (пусто = авто):"))
        self.java_field = QLineEdit(self.cfg.java_path)
        self.java_field.editingFinished.connect(self._on_java_changed)
        java_row.addWidget(self.java_field, 1)
        java_btn = QPushButton("…")
        java_btn.setObjectName("Secondary")
        java_btn.setFixedWidth(36)
        java_btn.clicked.connect(self._pick_java)
        java_row.addWidget(java_btn)
        layout.addLayout(java_row)

        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("Папка игры (пусто = по умолчанию):"))
        self.dir_field = QLineEdit(self.cfg.game_dir)
        self.dir_field.editingFinished.connect(self._on_dir_changed)
        dir_row.addWidget(self.dir_field, 1)
        dir_btn = QPushButton("…")
        dir_btn.setObjectName("Secondary")
        dir_btn.setFixedWidth(36)
        dir_btn.clicked.connect(self._pick_dir)
        dir_row.addWidget(dir_btn)
        layout.addLayout(dir_row)

        return card

    def _on_ram_changed(self, value: int) -> None:
        self.cfg.ram_mb = value
        save_config(self.cfg)

    def _on_java_changed(self) -> None:
        self.cfg.java_path = self.java_field.text().strip()
        save_config(self.cfg)

    def _pick_java(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Выберите java")
        if path:
            self.java_field.setText(path)
            self._on_java_changed()

    def _on_dir_changed(self) -> None:
        self.cfg.game_dir = self.dir_field.text().strip()
        save_config(self.cfg)

    def _pick_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Выберите папку игры")
        if path:
            self.dir_field.setText(path)
            self._on_dir_changed()
