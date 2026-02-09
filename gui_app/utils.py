"""Shared utilities for the Service Daemon GUI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import logging
import tkinter as tk
from tkinter import ttk
from uuid import UUID

from config import DB_CONFIG

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_EXECUTION_DIR = PROJECT_ROOT / "manual_sql"
INFO_CONFIG_PATH = PROJECT_ROOT / "gui_app_info.json"


def configure_logging() -> logging.Logger:
    """Configure logging for GUI output."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    return logging.getLogger("service_daemon_gui")


logger = logging.getLogger("service_daemon_gui")


@dataclass
class AppSettings:
    """Persisted GUI and database connection settings."""

    env_path: Path
    gui_settings_path: Path
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    refresh_interval_seconds: int

    @classmethod
    def from_defaults(cls) -> "AppSettings":
        """Build settings using defaults and config overrides."""
        try:
            db_port = int(DB_CONFIG["DB_PORT"])
        except (TypeError, ValueError):
            db_port = 5432
        return cls(
            env_path=PROJECT_ROOT / ".env",
            gui_settings_path=PROJECT_ROOT / "gui_settings.json",
            db_host=DB_CONFIG["DB_HOST"],
            db_port=db_port,
            db_name=DB_CONFIG["DB_NAME"],
            db_user=DB_CONFIG["DB_USER"],
            db_password=DB_CONFIG["DB_PASSWORD"],
            refresh_interval_seconds=30,
        )

    def load(self) -> None:
        """Load settings from the environment and GUI settings files."""
        if self.env_path.exists():
            self._load_env_file()
        if self.gui_settings_path.exists():
            self._load_gui_settings()

    def save(self) -> None:
        """Persist settings to disk."""
        self._save_env_file()
        self._save_gui_settings()

    def _load_env_file(self) -> None:
        """Load DB settings from the .env file."""
        values = {}
        for line in self.env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
        self.db_host = values.get("DB_HOST", self.db_host)
        self.db_port = self._safe_int(values.get("DB_PORT"), self.db_port)
        self.db_name = values.get("DB_NAME", self.db_name)
        self.db_user = values.get("DB_USER", self.db_user)
        self.db_password = values.get("DB_PASSWORD", self.db_password)

    def _save_env_file(self) -> None:
        """Write DB settings to the .env file."""
        content = [
            f"DB_HOST={self.db_host}",
            f"DB_PORT={self.db_port}",
            f"DB_NAME={self.db_name}",
            f"DB_USER={self.db_user}",
            f"DB_PASSWORD={self.db_password}",
        ]
        self.env_path.write_text("\n".join(content) + "\n")

    def _load_gui_settings(self) -> None:
        """Load GUI-only settings from the settings JSON file."""
        try:
            data = json.loads(self.gui_settings_path.read_text())
        except (json.JSONDecodeError, OSError):
            return
        self.refresh_interval_seconds = self._safe_int(
            data.get("refresh_interval_seconds"),
            self.refresh_interval_seconds,
        )

    def _save_gui_settings(self) -> None:
        """Persist GUI-only settings to the settings JSON file."""
        data = {
            "refresh_interval_seconds": self.refresh_interval_seconds,
        }
        self.gui_settings_path.write_text(json.dumps(data, indent=2) + "\n")

    @staticmethod
    def _safe_int(value: str | int | None, default: int) -> int:
        """Convert a value to int, falling back to a default."""
        try:
            return int(value) if value is not None else default
        except (TypeError, ValueError):
            return default


class NotificationCenter:
    """Displays status notifications and transient toasts."""

    def __init__(self, parent: tk.Widget) -> None:
        """Create the notification widget container."""
        self.frame = ttk.Frame(parent)
        self.frame.grid_columnconfigure(0, weight=1)
        self.message_var = tk.StringVar(value="Ready.")
        self.message_label = ttk.Label(
            self.frame,
            textvariable=self.message_var,
            anchor="w",
            padding=(12, 6),
        )
        self.message_label.grid(row=0, column=0, sticky="ew")

    def notify(self, message: str) -> None:
        """Update the status message and show a toast."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_var.set(f"[{timestamp}] {message}")
        logger.info(message)
        self._show_toast(message)

    def _show_toast(self, message: str) -> None:
        """Display a transient toast notification."""
        toast = tk.Toplevel(self.frame)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg="#fef9c3")

        label = tk.Label(
            toast,
            text=message,
            bg="#fef9c3",
            fg="#1f2a44",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=8,
        )
        label.pack()

        toast.update_idletasks()
        x = toast.winfo_screenwidth() - toast.winfo_reqwidth() - 24
        y = toast.winfo_screenheight() - toast.winfo_reqheight() - 72
        toast.geometry(f"+{x}+{y}")
        toast.after(3200, toast.destroy)


class CorporateStyle:
    """Apply consistent corporate styling for widgets."""

    def __init__(self, root: tk.Tk) -> None:
        """Build the style configuration for the UI."""
        self.style = ttk.Style(root)
        self.root = root
        self._configure()

    def _configure(self) -> None:
        """Configure style rules for the application."""
        self.style.theme_use("clam")
        self.root.configure(bg="#f3f5f8")
        self.style.configure("TFrame", background="#f3f5f8")
        self.style.configure("TLabel", background="#f3f5f8", foreground="#1f2a44")
        self.style.configure(
            "Header.TLabel",
            font=("Segoe UI", 14, "bold"),
            foreground="#1f2a44",
        )
        self.style.configure(
            "TButton",
            font=("Segoe UI", 10, "bold"),
            background="#1f5aa6",
            foreground="white",
            padding=6,
        )
        self.style.map(
            "TButton",
            background=[("active", "#184b8a")],
            foreground=[("disabled", "#d0d0d0")],
        )
        self.style.configure(
            "TNotebook",
            background="#f3f5f8",
            tabmargins=(8, 4, 8, 0),
        )
        self.style.configure(
            "TNotebook.Tab",
            padding=(12, 6),
            font=("Segoe UI", 10, "bold"),
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", "#ffffff"), ("active", "#e0e6f0")],
            foreground=[("selected", "#1f2a44"), ("active", "#1f2a44")],
        )
        self.style.configure(
            "Treeview",
            background="white",
            fieldbackground="white",
            foreground="#1f2a44",
            rowheight=24,
            bordercolor="#d9dee7",
            borderwidth=1,
        )
        self.style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#d9dee7",
            foreground="#1f2a44",
        )
        self.style.map("Treeview", background=[("selected", "#c7d6f2")])


def is_valid_uuid(value: str) -> bool:
    """Validate that a string is a valid UUID."""
    try:
        UUID(str(value))
        return True
    except (ValueError, TypeError):
        return False
