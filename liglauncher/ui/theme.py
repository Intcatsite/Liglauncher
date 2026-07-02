"""Turns a ThemeConfig into a Qt stylesheet + derived colors."""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor

from ..config import ThemeConfig


def _mix(c1: QColor, c2: QColor, t: float) -> QColor:
    return QColor(
        int(c1.red() + (c2.red() - c1.red()) * t),
        int(c1.green() + (c2.green() - c1.green()) * t),
        int(c1.blue() + (c2.blue() - c1.blue()) * t),
    )


@dataclass
class Palette:
    accent: QColor
    accent_hover: QColor
    accent_pressed: QColor
    text: QColor
    text_dim: QColor
    panel: QColor
    panel_alt: QColor
    border: QColor

    @classmethod
    def from_theme(cls, theme: ThemeConfig) -> "Palette":
        accent = QColor(theme.accent_color)
        text = QColor(theme.text_color)
        white = QColor("#ffffff")
        black = QColor("#000000")
        return cls(
            accent=accent,
            accent_hover=_mix(accent, white, 0.15),
            accent_pressed=_mix(accent, black, 0.20),
            text=text,
            text_dim=_mix(text, QColor("#0b0b10"), 0.35),
            panel=QColor(18, 18, 24, 190),
            panel_alt=QColor(28, 28, 36, 200),
            border=QColor(255, 255, 255, 25),
        )


def build_stylesheet(theme: ThemeConfig) -> str:
    p = Palette.from_theme(theme)
    font = theme.font_family
    size = theme.font_size

    return f"""
    * {{
        font-family: "{font}";
        font-size: {size}pt;
        color: {p.text.name()};
        outline: none;
    }}

    #RootSurface {{
        background: transparent;
    }}

    #TitleBar {{
        background: transparent;
        border-top-left-radius: 14px;
        border-top-right-radius: 14px;
    }}
    #TitleBar QLabel {{
        color: {p.text.name()};
        font-weight: 600;
    }}

    #TitleButton {{
        background: transparent;
        border: none;
        border-radius: 6px;
        color: {p.text.name()};
        min-width: 34px;
        min-height: 28px;
    }}
    #TitleButton:hover {{ background: rgba(255,255,255,25); }}
    #TitleButton[close="true"]:hover {{ background: #e74c4c; color: white; }}

    #NavBar {{
        background: rgba(14,14,18,150);
        border-right: 1px solid {p.border.name(QColor.HexArgb)};
    }}

    QPushButton#NavItem {{
        text-align: left;
        padding: 10px 14px;
        border-radius: 10px;
        background: transparent;
        border: none;
        color: {p.text_dim.name()};
        font-weight: 500;
    }}
    QPushButton#NavItem:hover {{
        background: rgba(255,255,255,18);
        color: {p.text.name()};
    }}
    QPushButton#NavItem:checked {{
        background: {p.accent.name()};
        color: white;
    }}

    QWidget#Card {{
        background: rgba(255,255,255,14);
        border: 1px solid {p.border.name(QColor.HexArgb)};
        border-radius: 16px;
    }}

    QPushButton#Primary {{
        background: {p.accent.name()};
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 22px;
        font-weight: 600;
    }}
    QPushButton#Primary:hover {{ background: {p.accent_hover.name()}; }}
    QPushButton#Primary:pressed {{ background: {p.accent_pressed.name()}; }}
    QPushButton#Primary:disabled {{ background: rgba(255,255,255,30); color: rgba(255,255,255,90); }}

    QPushButton#Secondary {{
        background: rgba(255,255,255,20);
        color: {p.text.name()};
        border: 1px solid {p.border.name(QColor.HexArgb)};
        border-radius: 10px;
        padding: 9px 18px;
    }}
    QPushButton#Secondary:hover {{ background: rgba(255,255,255,32); }}

    QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {{
        background: rgba(0,0,0,90);
        border: 1px solid {p.border.name(QColor.HexArgb)};
        border-radius: 8px;
        padding: 8px 10px;
        color: {p.text.name()};
        selection-background-color: {p.accent.name()};
    }}
    QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{ border: 1px solid {p.accent.name()}; }}

    QSlider::groove:horizontal {{
        height: 4px;
        background: rgba(255,255,255,30);
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        height: 4px;
        background: {p.accent.name()};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 16px;
        height: 16px;
        margin: -6px 0;
        border-radius: 8px;
        background: {p.text.name()};
    }}

    QListWidget {{
        background: transparent;
        border: none;
    }}
    QListWidget::item {{
        border-radius: 12px;
        padding: 6px;
        margin: 3px 0;
    }}
    QListWidget::item:selected {{
        background: rgba(255,255,255,22);
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255,255,255,60);
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

    QProgressBar {{
        background: rgba(0,0,0,90);
        border: none;
        border-radius: 6px;
        text-align: center;
        color: {p.text.name()};
    }}
    QProgressBar::chunk {{
        background: {p.accent.name()};
        border-radius: 6px;
    }}

    QLabel#PageTitle {{
        font-size: {size + 6}pt;
        font-weight: 700;
    }}
    QLabel#Muted {{
        color: {p.text_dim.name()};
    }}
    """
