"""Main launcher window."""
from __future__ import annotations

import logging
import os
import threading
import tkinter as tk
import tkinter.messagebox as messagebox
import customtkinter as ctk

from .. import __version__
from ..config import LauncherConfig, load_config, save_config
from ..core import installer, launcher, versions
from ..core.auth import OfflineAccount, is_valid_username
from ..paths import minecraft_dir
from . import theme

log = logging.getLogger(__name__)


LOADER_LABELS = {
    "vanilla": "Vanilla",
    "fabric": "Fabric",
    "quilt": "Quilt",
    "forge": "Forge",
}


class LigLauncherApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        theme.apply_theme()
        self.configure(fg_color=theme.BG)

        self.title(f"LigLauncher v{__version__} — Black Edition")
        self.geometry("780x560")
        self.minsize(720, 520)

        self.cfg: LauncherConfig = load_config()
        self._busy = False
        self._all_versions: list[dict] = []

        self._build_ui()
        self._populate_initial()

    # ---- UI construction -------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, **theme.frame_kwargs())
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="LIGLAUNCHER",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=theme.TEXT,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 0))
        ctk.CTkLabel(
            header,
            text="Offline Minecraft launcher · Black Edition",
            text_color=theme.TEXT_DIM,
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        # Main form
        form = ctk.CTkFrame(self, **theme.frame_kwargs())
        form.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        form.grid_columnconfigure(1, weight=1)

        row = 0

        # Username
        ctk.CTkLabel(form, text="Никнейм", text_color=theme.TEXT_DIM).grid(
            row=row, column=0, sticky="w", padx=(16, 8), pady=(16, 4)
        )
        self.username_var = tk.StringVar(value=self.cfg.username)
        self.username_entry = ctk.CTkEntry(
            form, textvariable=self.username_var, **theme.entry_kwargs()
        )
        self.username_entry.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=(16, 4))
        row += 1

        # Loader
        ctk.CTkLabel(form, text="Лоадер", text_color=theme.TEXT_DIM).grid(
            row=row, column=0, sticky="w", padx=(16, 8), pady=4
        )
        self.loader_var = tk.StringVar(value=LOADER_LABELS.get(self.cfg.version_type, "Vanilla"))
        self.loader_menu = ctk.CTkOptionMenu(
            form,
            variable=self.loader_var,
            values=list(LOADER_LABELS.values()),
            command=lambda _v: self._refresh_versions(),
            fg_color=theme.BG_INPUT,
            button_color=theme.BORDER,
            button_hover_color=theme.BG_INPUT,
            text_color=theme.TEXT,
            dropdown_fg_color=theme.BG_ELEV,
            dropdown_text_color=theme.TEXT,
            corner_radius=8,
            height=36,
        )
        self.loader_menu.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=4)
        row += 1

        # Version
        ctk.CTkLabel(form, text="Версия", text_color=theme.TEXT_DIM).grid(
            row=row, column=0, sticky="w", padx=(16, 8), pady=4
        )
        self.version_var = tk.StringVar(value=self.cfg.version_id)
        self.version_menu = ctk.CTkOptionMenu(
            form,
            variable=self.version_var,
            values=["(загрузка...)"],
            fg_color=theme.BG_INPUT,
            button_color=theme.BORDER,
            button_hover_color=theme.BG_INPUT,
            text_color=theme.TEXT,
            dropdown_fg_color=theme.BG_ELEV,
            dropdown_text_color=theme.TEXT,
            corner_radius=8,
            height=36,
        )
        self.version_menu.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=4)
        row += 1

        # Toggles
        toggles = ctk.CTkFrame(form, fg_color="transparent")
        toggles.grid(row=row, column=0, columnspan=2, sticky="ew", padx=16, pady=4)
        self.snap_var = tk.BooleanVar(value=self.cfg.show_snapshots)
        self.old_var = tk.BooleanVar(value=self.cfg.show_old)
        ctk.CTkCheckBox(
            toggles,
            text="Снапшоты",
            variable=self.snap_var,
            command=self._refresh_versions,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT,
            border_color=theme.BORDER,
        ).pack(side="left", padx=(0, 16))
        ctk.CTkCheckBox(
            toggles,
            text="Старые (alpha/beta)",
            variable=self.old_var,
            command=self._refresh_versions,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT,
            border_color=theme.BORDER,
        ).pack(side="left")
        row += 1

        # RAM
        ctk.CTkLabel(form, text="RAM (MB)", text_color=theme.TEXT_DIM).grid(
            row=row, column=0, sticky="w", padx=(16, 8), pady=4
        )
        ram_row = ctk.CTkFrame(form, fg_color="transparent")
        ram_row.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=4)
        ram_row.grid_columnconfigure(0, weight=1)
        self.ram_var = tk.IntVar(value=self.cfg.ram_mb)
        self.ram_label = ctk.CTkLabel(
            ram_row, text=f"{self.cfg.ram_mb} MB", text_color=theme.TEXT, width=80
        )
        self.ram_slider = ctk.CTkSlider(
            ram_row,
            from_=1024,
            to=max(2048, _system_max_ram_mb()),
            number_of_steps=max(1, (_system_max_ram_mb() - 1024) // 256),
            command=self._on_ram_change,
            progress_color=theme.ACCENT,
            button_color=theme.ACCENT,
            button_hover_color=theme.ACCENT_HOVER,
            fg_color=theme.BG_INPUT,
        )
        self.ram_slider.set(self.cfg.ram_mb)
        self.ram_slider.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.ram_label.grid(row=0, column=1)
        row += 1

        # Java path
        ctk.CTkLabel(form, text="Java (необязательно)", text_color=theme.TEXT_DIM).grid(
            row=row, column=0, sticky="w", padx=(16, 8), pady=4
        )
        self.java_var = tk.StringVar(value=self.cfg.java_path)
        ctk.CTkEntry(
            form,
            textvariable=self.java_var,
            placeholder_text="auto-detect",
            **theme.entry_kwargs(),
        ).grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=4)
        row += 1

        # Game directory (read-only, informational)
        ctk.CTkLabel(form, text="Папка игры", text_color=theme.TEXT_DIM).grid(
            row=row, column=0, sticky="w", padx=(16, 8), pady=4
        )
        self.game_dir_var = tk.StringVar(value=self.cfg.game_dir or str(minecraft_dir()))
        ctk.CTkEntry(
            form, textvariable=self.game_dir_var, **theme.entry_kwargs()
        ).grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=(4, 16))
        row += 1

        # Status / progress
        status = ctk.CTkFrame(self, fg_color="transparent")
        status.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))
        status.grid_columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value="Готов.")
        ctk.CTkLabel(
            status,
            textvariable=self.status_var,
            text_color=theme.TEXT_DIM,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        self.progress = ctk.CTkProgressBar(
            status,
            progress_color=theme.ACCENT,
            fg_color=theme.BG_INPUT,
            height=6,
        )
        self.progress.set(0)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        # Action bar
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))
        actions.grid_columnconfigure(0, weight=1)
        self.play_btn = ctk.CTkButton(
            actions,
            text="ИГРАТЬ",
            command=self._on_play,
            **theme.button_kwargs(primary=True),
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.play_btn.grid(row=0, column=0, sticky="ew")

    # ---- Helpers ---------------------------------------------------------

    def _on_ram_change(self, value: float) -> None:
        # Snap to 256 MB increments.
        mb = int(round(value / 256.0)) * 256
        self.ram_var.set(mb)
        self.ram_label.configure(text=f"{mb} MB")

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)
        self.update_idletasks()

    def _set_progress(self, current: int, total: int) -> None:
        if total > 0:
            self.progress.set(min(1.0, current / total))
        else:
            self.progress.set(0)
        self.update_idletasks()

    def _populate_initial(self) -> None:
        self._set_status("Загрузка списка версий...")
        threading.Thread(target=self._load_versions_async, daemon=True).start()

    def _safe_after(self, *args, **kwargs) -> None:
        """Like ``self.after`` but silently ignores a destroyed window."""
        try:
            self.after(*args, **kwargs)
        except (tk.TclError, RuntimeError):
            pass

    def _load_versions_async(self) -> None:
        try:
            self._all_versions = versions.list_remote_versions()
        except Exception as exc:  # noqa: BLE001
            log.exception("Failed to fetch version list")
            msg = f"Не удалось получить версии: {exc}"
            self._safe_after(0, lambda m=msg: self._set_status(m))
            return
        self._safe_after(0, self._refresh_versions)
        self._safe_after(0, lambda: self._set_status("Готов."))

    def _selected_loader(self) -> str:
        label = self.loader_var.get()
        for key, val in LOADER_LABELS.items():
            if val == label:
                return key
        return "vanilla"

    def _refresh_versions(self) -> None:
        if not self._all_versions:
            return
        filtered = versions.filter_vanilla(
            self._all_versions,
            show_snapshots=self.snap_var.get(),
            show_old=self.old_var.get(),
        )
        ids = [v["id"] for v in filtered]
        if not ids:
            ids = ["(нет версий)"]
        self.version_menu.configure(values=ids)
        # Preserve current selection if still present.
        current = self.version_var.get()
        if current not in ids:
            self.version_var.set(ids[0])

    # ---- Launch flow -----------------------------------------------------

    def _on_play(self) -> None:
        if self._busy:
            return
        username = self.username_var.get().strip()
        if not is_valid_username(username):
            messagebox.showerror(
                "Никнейм",
                "Никнейм должен быть 3–16 символов: A-Z, a-z, 0-9, _",
            )
            return
        version = self.version_var.get()
        if not version or version.startswith("("):
            messagebox.showerror("Версия", "Сначала выбери версию Minecraft.")
            return

        loader = self._selected_loader()

        # Persist config before launching.
        self.cfg.username = username
        self.cfg.version_id = version
        self.cfg.version_type = loader
        self.cfg.ram_mb = int(self.ram_var.get())
        self.cfg.java_path = self.java_var.get().strip()
        self.cfg.game_dir = self.game_dir_var.get().strip()
        self.cfg.show_snapshots = self.snap_var.get()
        self.cfg.show_old = self.old_var.get()
        save_config(self.cfg)

        self._busy = True
        self.play_btn.configure(state="disabled", text="ЗАПУСК...")
        threading.Thread(
            target=self._install_and_launch_async,
            args=(username, version, loader),
            daemon=True,
        ).start()

    def _install_and_launch_async(self, username: str, mc_version: str, loader: str) -> None:
        try:
            game_dir = self.cfg.resolved_game_dir()
            game_dir.mkdir(parents=True, exist_ok=True)

            def progress_cb(status: str, current: int, total: int) -> None:
                self._safe_after(0, self._set_status, status or "Загрузка...")
                self._safe_after(0, self._set_progress, current, total)

            target = installer.InstallTarget(mc_version=mc_version, loader=loader)
            self._safe_after(0, self._set_status, "Подготовка установки...")
            installed_id = installer.install_target(target, game_dir, progress_cb)

            self._safe_after(0, self._set_status, "Сборка команды запуска...")
            account = OfflineAccount.from_username(username)
            opts = launcher.LaunchOptions(
                account=account,
                version_id=installed_id,
                game_dir=game_dir,
                ram_mb=int(self.ram_var.get()),
                java_path=self.java_var.get().strip(),
                extra_jvm_args=self.cfg.jvm_args or None,
            )
            self._safe_after(0, self._set_status, f"Запуск {installed_id}...")
            proc = launcher.launch(opts)
            self._safe_after(0, self._set_status, f"Minecraft запущен (PID {proc.pid}).")
        except Exception as exc:  # noqa: BLE001
            log.exception("Launch failed")
            err = str(exc)
            self._safe_after(0, self._set_status, f"Ошибка: {err}")
            self._safe_after(0, lambda e=err: messagebox.showerror("Ошибка запуска", e))
        finally:
            self._safe_after(0, lambda: self._set_progress(0, 1))
            self._safe_after(0, lambda: self.play_btn.configure(state="normal", text="ИГРАТЬ"))
            self._busy = False


def _system_max_ram_mb() -> int:
    """Best-effort total RAM detection; fall back to 8192 MB."""
    try:
        if hasattr(os, "sysconf") and "SC_PAGE_SIZE" in os.sysconf_names and "SC_PHYS_PAGES" in os.sysconf_names:
            total = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
            return max(2048, int(total / 1024 / 1024 * 0.75))
    except (ValueError, OSError):
        pass
    if os.name == "nt":
        try:
            import ctypes

            class MEMSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return max(2048, int(stat.ullTotalPhys / 1024 / 1024 * 0.75))
        except Exception:  # noqa: BLE001
            pass
    return 8192


def run() -> None:
    app = LigLauncherApp()
    app.mainloop()
