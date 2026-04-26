"""Black-edition color palette for CustomTkinter."""
from __future__ import annotations

import customtkinter as ctk

# Palette
BG = "#0A0A0A"
BG_ELEV = "#141414"
BG_INPUT = "#1C1C1C"
BORDER = "#2A2A2A"
TEXT = "#F2F2F2"
TEXT_DIM = "#9A9A9A"
ACCENT = "#FF4500"  # matches the README badge
ACCENT_HOVER = "#FF6A33"
DANGER = "#E5484D"


def apply_theme() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")  # baseline; we override per-widget


# Common widget kwargs
def button_kwargs(primary: bool = False) -> dict:
    if primary:
        return dict(
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#0A0A0A",
            corner_radius=8,
            height=42,
        )
    return dict(
        fg_color=BG_ELEV,
        hover_color=BG_INPUT,
        border_color=BORDER,
        border_width=1,
        text_color=TEXT,
        corner_radius=8,
        height=36,
    )


def entry_kwargs() -> dict:
    return dict(
        fg_color=BG_INPUT,
        border_color=BORDER,
        border_width=1,
        text_color=TEXT,
        corner_radius=8,
        height=36,
    )


def frame_kwargs() -> dict:
    return dict(fg_color=BG_ELEV, corner_radius=12, border_color=BORDER, border_width=1)
