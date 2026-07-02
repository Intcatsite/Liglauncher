"""Small self-contained SVG icon set (no external assets/network needed).

Icons are Material-style outline/solid glyphs rasterized on demand and
tinted to match the current theme, replacing plain unicode characters in
the nav bar and title bar.
"""
from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_PATHS: dict[str, str] = {
    "play": "M8 5v14l11-7z",
    "person": (
        "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c"
        "-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"
    ),
    "globe": (
        "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm"
        "-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1"
        ".9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1"
        "-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06"
        " 5 7.41 0 2.08-.8 3.97-2.1 5.39z"
    ),
    "settings": (
        "M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c"
        ".18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c"
        "-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c"
        "-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c"
        "-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c"
        "-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61"
        "l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54"
        "c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24"
        " 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22"
        ".07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62"
        "-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"
    ),
    "minimize": "M5 11h14v2H5z",
    "fullscreen": (
        "M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2"
        "h3v3h2V5h-5z"
    ),
    "fullscreen_exit": (
        "M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h"
        "-2v5h5V8h-3z"
    ),
    "close": (
        "M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19"
        " 12 13.41 17.59 19 19 17.59 13.41 12z"
    ),
    "check": "M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z",
    "trash": (
        "M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1"
        " 1H5v2h14V4z"
    ),
    "upload": "M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z",
    "copy": (
        "M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0"
        " 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"
    ),
}

_cache: dict[tuple[str, str, int], QIcon] = {}


def _render(svg: bytes, size: int) -> QPixmap:
    renderer = QSvgRenderer(QByteArray(svg))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    return pixmap


def icon(name: str, color: str, size: int = 20) -> QIcon:
    """Return a themed QIcon for ``name`` (see _PATHS), cached per color/size."""
    key = (name, color, size)
    cached = _cache.get(key)
    if cached is not None:
        return cached
    d = _PATHS[name]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        f'<path d="{d}" fill="{color}"/></svg>'
    ).encode("utf-8")
    result = QIcon(_render(svg, size))
    _cache[key] = result
    return result


def clear_cache() -> None:
    _cache.clear()


def toggle_icon(name: str, off_color: str, on_color: str, size: int = 20) -> QIcon:
    """Two-state icon: off_color when unchecked, on_color when a checkable button is checked."""
    d = _PATHS[name]

    def _pixmap(color: str) -> QPixmap:
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            f'<path d="{d}" fill="{color}"/></svg>'
        ).encode("utf-8")
        return _render(svg, size)

    result = QIcon()
    result.addPixmap(_pixmap(off_color), QIcon.Normal, QIcon.Off)
    result.addPixmap(_pixmap(on_color), QIcon.Normal, QIcon.On)
    return result
