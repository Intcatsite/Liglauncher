"""Wires the config, accounts and pages into the main window and runs the app."""
from __future__ import annotations

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from ..config import load_config
from ..core import updater
from ..core.accounts import AccountManager
from .main_window import MainWindow
from .pages.accounts_page import AccountsPage
from .pages.play_page import PlayPage
from .pages.servers_page import ServersPage
from .pages.settings_page import SettingsPage
from .update_dialog import check_and_offer_update


def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("LigLauncher")

    cfg = load_config()
    accounts = AccountManager()

    window = MainWindow(cfg)

    play_page = PlayPage(cfg, accounts)
    accounts_page = AccountsPage(cfg, accounts, on_changed=play_page.refresh_accounts)
    servers_page = ServersPage(cfg)
    settings_page = SettingsPage(
        cfg,
        on_theme_changed=window.apply_theme,
        on_versions_changed=play_page.refresh_versions,
    )

    window.register_page("play", play_page)
    window.register_page("accounts", accounts_page)
    window.register_page("servers", servers_page)
    window.register_page("settings", settings_page)

    window.show()

    if updater.is_frozen():
        QTimer.singleShot(2000, lambda: check_and_offer_update(window, cfg, silent=True))

    sys.exit(app.exec())
