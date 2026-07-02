"""Generic background-thread worker so long operations (downloads, server
boot, tunnel build) never block the UI thread."""
from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    line = Signal(str)
    progress = Signal(str, int, int)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.finished_ok.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
