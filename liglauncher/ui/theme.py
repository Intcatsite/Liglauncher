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


def contrast_text(bg: QColor, dark: str = "#0f172a", light: str = "#ffffff") -> QColor:
    """Pick a readable text color for content drawn on top of ``bg``."""
    brightness = (bg.red() * 299 + bg.green() * 587 + bg.blue() * 114) / 1000
    return QColor(dark if brightness > 150 else light)


@dataclass
class Palette:
    accent: QColor
    accent_hover: QColor
    accent_pressed: QColor
    accent_text: QColor
    text: QColor
    text_dim: QColor
    panel: QColor
    border: QColor
    field_bg: QColor
    hover_tint: str
    faint_tint: str

    @classmethod
    def from_theme(cls, theme: ThemeConfig) -> "Palette":
        accent = QColor(theme.accent_color)
        text = QColor(theme.text_color)
        white = QColor("#ffffff")
        black = QColor("#000000")
        return cls(
            accent=accent,
            accent_hover=_mix(accent, white, 0.15),
            accent_pressed=_mix(accent, black, 0.12),
            accent_text=contrast_text(accent, dark=theme.text_color),
            text=text,
            text_dim=_mix(text, QColor("#94a3b8"), 0.55),
            panel=QColor(255, 255, 255, 214),
            border=QColor(15, 23, 42, 22),
            field_bg=QColor(15, 23, 42, 10),
            hover_tint="rgba(15,23,42,16)",
            faint_tint="rgba(15,23,42,8)",
        )


def build_stylesheet(theme: ThemeConfig) -> str:
    p = Palette.from_theme(theme)
    font = theme.font_family
    size = theme.font_size
    r = theme.corner_radius
    r_sm = max(4, r - 6)
    r_lg = r + 2
    bw = theme.border_width
    border = f"{bw}px solid {p.border.name(QColor.HexArgb)}"

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
        border-top-left-radius: {r}px;
        border-top-right-radius: {r}px;
    }}
    #TitleBar QLabel {{
        color: {p.text.name()};
        font-weight: 600;
    }}

    #TitleButton {{
        background: transparent;
        border: none;
        border-radius: {r_sm}px;
        color: {p.text.name()};
        min-width: 34px;
        min-height: 28px;
    }}
    #TitleButton:hover {{ background: {p.hover_tint}; }}
    #TitleButton[close="true"]:hover {{ background: #ef4444; color: white; }}

    #NavBar {{
        background: rgba(255,255,255,120);
        border-right: {border};
    }}

    QPushButton#NavItem {{
        text-align: left;
        padding: 10px 14px;
        border-radius: {r_sm}px;
        background: transparent;
        border: none;
        color: {p.text_dim.name()};
        font-weight: 500;
    }}
    QPushButton#NavItem:hover {{
        background: {p.hover_tint};
        color: {p.text.name()};
    }}
    QPushButton#NavItem:checked {{
        background: {p.accent.name()};
        color: {p.accent_text.name()};
    }}

    QWidget#Card {{
        background: {p.panel.name(QColor.HexArgb)};
        border: {border};
        border-radius: {r_lg}px;
    }}

    QPushButton#Primary {{
        background: {p.accent.name()};
        color: {p.accent_text.name()};
        border: none;
        border-radius: {r_sm}px;
        padding: 10px 22px;
        font-weight: 600;
    }}
    QPushButton#Primary:hover {{ background: {p.accent_hover.name()}; }}
    QPushButton#Primary:pressed {{ background: {p.accent_pressed.name()}; }}
    QPushButton#Primary:disabled {{ background: rgba(15,23,42,25); color: rgba(15,23,42,90); }}

    QPushButton#Secondary {{
        background: {p.faint_tint};
        color: {p.text.name()};
        border: {border};
        border-radius: {r_sm}px;
        padding: 9px 18px;
    }}
    QPushButton#Secondary:hover {{ background: {p.hover_tint}; }}

    QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {{
        background: {p.field_bg.name(QColor.HexArgb)};
        border: {border};
        border-radius: {r_sm}px;
        padding: 8px 10px;
        color: {p.text.name()};
        selection-background-color: {p.accent.name()};
        selection-color: {p.accent_text.name()};
    }}
    QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{ border: {bw}px solid {p.accent.name()}; }}

    QComboBox QAbstractItemView {{
        background: white;
        border: 1px solid {p.border.name(QColor.HexArgb)};
        border-radius: {r_sm}px;
        color: {p.text.name()};
        selection-background-color: {p.accent.name()};
        selection-color: {p.accent_text.name()};
        outline: none;
    }}

    QSlider::groove:horizontal {{
        height: 4px;
        background: {p.faint_tint};
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
        background: {p.accent.name()};
        border: 2px solid white;
    }}

    QListWidget {{
        background: transparent;
        border: none;
    }}
    QListWidget::item {{
        border-radius: {r_sm}px;
        padding: 6px;
        margin: 3px 0;
    }}
    QListWidget::item:selected {{
        background: {p.hover_tint};
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(15,23,42,50);
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

    QProgressBar {{
        background: {p.field_bg.name(QColor.HexArgb)};
        border: none;
        border-radius: {r_sm - 2}px;
        text-align: center;
        color: {p.text.name()};
    }}
    QProgressBar::chunk {{
        background: {p.accent.name()};
        border-radius: {r_sm - 2}px;
    }}

    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: {bw if bw else 1}px solid {p.border.name(QColor.HexArgb)};
        border-radius: 4px;
        background: {p.field_bg.name(QColor.HexArgb)};
    }}
    QCheckBox::indicator:checked {{
        background: {p.accent.name()};
        border-color: {p.accent.name()};
    }}

    QLabel#PageTitle {{
        font-size: {size + 6}pt;
        font-weight: 700;
    }}
    QLabel#Muted {{
        color: {p.text_dim.name()};
    }}

    QDialog#ThemedDialog {{
        background: {p.panel.name(QColor.HexArgb)};
        border: {border};
        border-radius: {r_lg}px;
    }}
    """
