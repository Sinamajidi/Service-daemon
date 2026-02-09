"""
Desktop GUI Application (Tkinter)
Provides a corporative, tabbed interface for settings, database, and operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import sys
import tkinter as tk
from tkinter import ttk

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.data_access_layer import get_dal
from database.entity_access import get_booking_access
from config import DB_CONFIG


@dataclass
class AppSettings:
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
        if self.env_path.exists():
            self._load_env_file()
        if self.gui_settings_path.exists():
            self._load_gui_settings()

    def save(self) -> None:
        self._save_env_file()
        self._save_gui_settings()

    def _load_env_file(self) -> None:
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
        content = [
            f"DB_HOST={self.db_host}",
            f"DB_PORT={self.db_port}",
            f"DB_NAME={self.db_name}",
            f"DB_USER={self.db_user}",
            f"DB_PASSWORD={self.db_password}",
        ]
        self.env_path.write_text("\n".join(content) + "\n")

    def _load_gui_settings(self) -> None:
        try:
            data = json.loads(self.gui_settings_path.read_text())
        except (json.JSONDecodeError, OSError):
            return
        self.refresh_interval_seconds = self._safe_int(
            data.get("refresh_interval_seconds"),
            self.refresh_interval_seconds,
        )

    def _save_gui_settings(self) -> None:
        data = {
            "refresh_interval_seconds": self.refresh_interval_seconds,
        }
        self.gui_settings_path.write_text(json.dumps(data, indent=2) + "\n")

    @staticmethod
    def _safe_int(value: str | int | None, default: int) -> int:
        try:
            return int(value) if value is not None else default
        except (TypeError, ValueError):
            return default


class NotificationCenter:
    def __init__(self, parent: tk.Widget) -> None:
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
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_var.set(f"[{timestamp}] {message}")


class CorporateStyle:
    def __init__(self, root: tk.Tk) -> None:
        self.style = ttk.Style(root)
        self.root = root
        self._configure()

    def _configure(self) -> None:
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


class BaseTab(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, app: "ServiceDaemonApp") -> None:
        super().__init__(parent)
        self.app = app


class SettingsTab(BaseTab):
    def __init__(self, parent: ttk.Notebook, app: "ServiceDaemonApp") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        header = ttk.Label(self, text="Settings", style="Header.TLabel")
        header.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        container = ttk.Frame(self)
        container.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        container.grid_columnconfigure(1, weight=1)

        ttk.Label(container, text="Database Host").grid(row=0, column=0, sticky="w")
        ttk.Label(container, text="Database Port").grid(row=1, column=0, sticky="w")
        ttk.Label(container, text="Database Name").grid(row=2, column=0, sticky="w")
        ttk.Label(container, text="Database User").grid(row=3, column=0, sticky="w")
        ttk.Label(container, text="Database Password").grid(row=4, column=0, sticky="w")
        ttk.Label(container, text="Refresh Interval (sec)").grid(
            row=5, column=0, sticky="w"
        )

        self.host_var = tk.StringVar(value=self.app.settings.db_host)
        self.port_var = tk.StringVar(value=str(self.app.settings.db_port))
        self.name_var = tk.StringVar(value=self.app.settings.db_name)
        self.user_var = tk.StringVar(value=self.app.settings.db_user)
        self.password_var = tk.StringVar(value=self.app.settings.db_password)
        self.refresh_var = tk.StringVar(
            value=str(self.app.settings.refresh_interval_seconds)
        )

        ttk.Entry(container, textvariable=self.host_var).grid(
            row=0, column=1, sticky="ew", padx=6, pady=4
        )
        ttk.Entry(container, textvariable=self.port_var).grid(
            row=1, column=1, sticky="ew", padx=6, pady=4
        )
        ttk.Entry(container, textvariable=self.name_var).grid(
            row=2, column=1, sticky="ew", padx=6, pady=4
        )
        ttk.Entry(container, textvariable=self.user_var).grid(
            row=3, column=1, sticky="ew", padx=6, pady=4
        )
        ttk.Entry(container, textvariable=self.password_var, show="•").grid(
            row=4, column=1, sticky="ew", padx=6, pady=4
        )
        ttk.Entry(container, textvariable=self.refresh_var).grid(
            row=5, column=1, sticky="ew", padx=6, pady=4
        )

        button_frame = ttk.Frame(container)
        button_frame.grid(row=6, column=1, sticky="e", pady=10)
        ttk.Button(button_frame, text="Save Settings", command=self._save).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(button_frame, text="Reload", command=self._reload).grid(
            row=0, column=1, padx=4
        )

    def _save(self) -> None:
        self.app.settings.db_host = self.host_var.get().strip()
        try:
            self.app.settings.db_port = int(self.port_var.get().strip())
        except ValueError:
            self.app.notifications.notify("Database port must be a number.")
            return
        self.app.settings.db_name = self.name_var.get().strip()
        self.app.settings.db_user = self.user_var.get().strip()
        self.app.settings.db_password = self.password_var.get().strip()
        try:
            refresh_interval = int(self.refresh_var.get().strip())
        except ValueError:
            self.app.notifications.notify("Refresh interval must be a number.")
            return
        self.app.settings.refresh_interval_seconds = max(5, refresh_interval)
        self.app.settings.save()
        self.app.notifications.notify("Settings saved. Restart to apply DB changes.")
        self.app.operations_tab.update_refresh_interval()

    def _reload(self) -> None:
        self.app.settings.load()
        self.host_var.set(self.app.settings.db_host)
        self.port_var.set(str(self.app.settings.db_port))
        self.name_var.set(self.app.settings.db_name)
        self.user_var.set(self.app.settings.db_user)
        self.password_var.set(self.app.settings.db_password)
        self.refresh_var.set(str(self.app.settings.refresh_interval_seconds))
        self.app.notifications.notify("Settings reloaded.")


class DatabaseTab(BaseTab):
    def __init__(self, parent: ttk.Notebook, app: "ServiceDaemonApp") -> None:
        super().__init__(parent, app)
        self.dal = get_dal()
        self.columns: list[str] = []
        self._build()

    def _build(self) -> None:
        header = ttk.Label(self, text="Database", style="Header.TLabel")
        header.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        toolbar = ttk.Frame(self)
        toolbar.grid(row=1, column=0, sticky="ew", padx=12)
        toolbar.grid_columnconfigure(2, weight=1)

        ttk.Label(toolbar, text="Table").grid(row=0, column=0, sticky="w")
        self.table_var = tk.StringVar(value="users")
        self.table_select = ttk.Combobox(
            toolbar,
            textvariable=self.table_var,
            values=self._get_table_names(),
            state="readonly",
            width=24,
        )
        self.table_select.grid(row=0, column=1, sticky="w", padx=6)
        self.table_select.bind("<<ComboboxSelected>>", lambda _: self.refresh())

        ttk.Button(toolbar, text="Refresh", command=self.refresh).grid(
            row=0, column=3, padx=6
        )
        ttk.Button(toolbar, text="Edit Selected", command=self._edit_selected).grid(
            row=0, column=4, padx=6
        )

        self.tree = ttk.Treeview(self, show="headings")
        self.tree.grid(row=2, column=0, sticky="nsew", padx=12, pady=12)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.refresh()

    def _get_table_names(self) -> list[str]:
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        try:
            results = self.dal.execute_custom_query(query, fetch="all")
        except Exception as exc:
            self.app.notifications.notify(f"Unable to load tables: {exc}")
            return []
        return [row["table_name"] for row in results] if results else []

    def _get_columns(self, table: str) -> list[str]:
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """
        try:
            results = self.dal.execute_custom_query(query, (table,), fetch="all")
        except Exception as exc:
            self.app.notifications.notify(f"Unable to load columns: {exc}")
            return []
        return [row["column_name"] for row in results] if results else []

    def refresh(self) -> None:
        table = self.table_var.get()
        try:
            self.columns = self._get_columns(table)
            self.tree.configure(columns=self.columns)
            for col in self.columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=140, anchor="w")
            for item in self.tree.get_children():
                self.tree.delete(item)
            rows = self.dal.get_filtered_records(table, "1=1", (), limit=200)
            for row in rows:
                values = [row.get(col) for col in self.columns]
                self.tree.insert("", "end", values=values)
            self.app.notifications.notify(f"Loaded {len(rows)} rows from {table}.")
        except Exception as exc:
            self.app.notifications.notify(f"Database load failed: {exc}")

    def _edit_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            self.app.notifications.notify("Select a row to edit.")
            return
        values = self.tree.item(selection[0], "values")
        data = dict(zip(self.columns, values))
        if "id" not in data:
            self.app.notifications.notify("Selected table lacks an 'id' column.")
            return
        RecordEditorDialog(self, self.app, self.table_var.get(), data, self.refresh)


class RecordEditorDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Widget,
        app: "ServiceDaemonApp",
        table: str,
        data: dict,
        on_save,
    ) -> None:
        super().__init__(parent)
        self.app = app
        self.table = table
        self.data = data
        self.on_save = on_save
        self.entries: dict[str, tk.Entry] = {}
        self.title(f"Edit {table} record")
        self._build()

    def _build(self) -> None:
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        for idx, (key, value) in enumerate(self.data.items()):
            ttk.Label(container, text=key).grid(row=idx, column=0, sticky="w")
            entry = ttk.Entry(container)
            entry.insert(0, "" if value is None else str(value))
            entry.grid(row=idx, column=1, sticky="ew", padx=6, pady=2)
            if key == "id":
                entry.configure(state="disabled")
            self.entries[key] = entry

        button_frame = ttk.Frame(container)
        button_frame.grid(row=len(self.data), column=1, sticky="e", pady=8)
        ttk.Button(button_frame, text="Save", command=self._save).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(button_frame, text="Cancel", command=self.destroy).grid(
            row=0, column=1, padx=4
        )

    def _save(self) -> None:
        updated = {}
        for key, entry in self.entries.items():
            if key == "id":
                continue
            updated[key] = entry.get() or None
        record_id = self.data.get("id")
        try:
            success = get_dal().update_record(self.table, record_id, updated)
            if success:
                self.app.notifications.notify("Record updated successfully.")
                self.on_save()
                self.destroy()
            else:
                self.app.notifications.notify("No changes were saved.")
        except Exception as exc:
            self.app.notifications.notify(f"Update failed: {exc}")


class OperationsTab(BaseTab):
    def __init__(self, parent: ttk.Notebook, app: "ServiceDaemonApp") -> None:
        super().__init__(parent, app)
        self.booking_access = get_booking_access()
        self.refresh_job: str | None = None
        self._build()
        self.schedule_refresh()

    def _build(self) -> None:
        header = ttk.Label(self, text="Operations", style="Header.TLabel")
        header.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        toolbar = ttk.Frame(self)
        toolbar.grid(row=1, column=0, sticky="ew", padx=12)
        toolbar.grid_columnconfigure(5, weight=1)

        ttk.Button(toolbar, text="Refresh", command=self.refresh).grid(
            row=0, column=0, padx=4
        )

        ttk.Label(toolbar, text="Status").grid(row=0, column=1, padx=4)
        self.status_var = tk.StringVar(value="scheduled")
        self.status_combo = ttk.Combobox(
            toolbar,
            textvariable=self.status_var,
            values=["requested", "scheduled", "assigned", "in_progress", "completed", "cancelled"],
            width=16,
            state="readonly",
        )
        self.status_combo.grid(row=0, column=2, padx=4)

        ttk.Button(toolbar, text="Update Status", command=self.update_status).grid(
            row=0, column=3, padx=4
        )

        ttk.Button(toolbar, text="Schedule", command=self.schedule_booking).grid(
            row=0, column=4, padx=4
        )

        schedule_frame = ttk.Frame(self)
        schedule_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))
        schedule_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(schedule_frame, text="Start (YYYY-MM-DD HH:MM)").grid(
            row=0, column=0, sticky="w"
        )
        self.start_var = tk.StringVar()
        ttk.Entry(schedule_frame, textvariable=self.start_var).grid(
            row=0, column=1, sticky="ew", padx=6
        )

        ttk.Label(schedule_frame, text="End (YYYY-MM-DD HH:MM)").grid(
            row=1, column=0, sticky="w"
        )
        self.end_var = tk.StringVar()
        ttk.Entry(schedule_frame, textvariable=self.end_var).grid(
            row=1, column=1, sticky="ew", padx=6
        )

        self.tree = ttk.Treeview(
            self,
            columns=(
                "id",
                "status",
                "priority",
                "unit_id",
                "scheduled_start",
                "scheduled_end",
            ),
            show="headings",
        )
        self.tree.grid(row=3, column=0, sticky="nsew", padx=12, pady=12)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="w")

        self.tree.bind("<<TreeviewSelect>>", self._populate_schedule_fields)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=3, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def update_refresh_interval(self) -> None:
        if self.refresh_job:
            self.after_cancel(self.refresh_job)
        self.schedule_refresh()

    def schedule_refresh(self) -> None:
        interval_ms = self.app.settings.refresh_interval_seconds * 1000
        self.refresh_job = self.after(interval_ms, self._auto_refresh)

    def _auto_refresh(self) -> None:
        self.refresh()
        self.schedule_refresh()

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            bookings = get_dal().get_filtered_records("bookings", "1=1", (), limit=200)
            for booking in bookings:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        booking.get("id"),
                        booking.get("status"),
                        booking.get("priority"),
                        booking.get("unit_id"),
                        booking.get("scheduled_start"),
                        booking.get("scheduled_end"),
                    ),
                )
            self.app.notifications.notify(f"Loaded {len(bookings)} bookings.")
        except Exception as exc:
            self.app.notifications.notify(f"Booking refresh failed: {exc}")

    def _selected_booking_id(self) -> str | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return self.tree.item(selection[0], "values")[0]

    def _populate_schedule_fields(self, _event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        self.start_var.set(values[4] or "")
        self.end_var.set(values[5] or "")

    def update_status(self) -> None:
        booking_id = self._selected_booking_id()
        if not booking_id:
            self.app.notifications.notify("Select a booking first.")
            return
        try:
            success = self.booking_access.update_booking_status(
                booking_id, self.status_var.get()
            )
            if success:
                self.app.notifications.notify("Booking status updated.")
                self.refresh()
            else:
                self.app.notifications.notify("Status update failed.")
        except Exception as exc:
            self.app.notifications.notify(f"Status update error: {exc}")

    def schedule_booking(self) -> None:
        booking_id = self._selected_booking_id()
        if not booking_id:
            self.app.notifications.notify("Select a booking first.")
            return
        try:
            start = self._parse_datetime(self.start_var.get())
            end = self._parse_datetime(self.end_var.get())
            success = self.booking_access.update_booking(
                booking_id,
                scheduled_start=start,
                scheduled_end=end,
            )
            if success:
                self.app.notifications.notify("Booking scheduled.")
                self.refresh()
            else:
                self.app.notifications.notify("Scheduling failed.")
        except Exception as exc:
            self.app.notifications.notify(f"Schedule error: {exc}")

    def _parse_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        cleaned = value.strip()
        return datetime.fromisoformat(cleaned)


class ServiceDaemonApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Service Daemon Console")
        self.geometry("1200x720")
        self.minsize(980, 640)
        CorporateStyle(self)

        self.settings = AppSettings.from_defaults()
        self.settings.load()

        self._build_layout()

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        content = ttk.Frame(self)
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        notebook = ttk.Notebook(content)
        notebook.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.notifications = NotificationCenter(content)
        self.notifications.frame.grid(row=1, column=0, sticky="ew")

        self.settings_tab = SettingsTab(notebook, self)
        self.database_tab = DatabaseTab(notebook, self)
        self.operations_tab = OperationsTab(notebook, self)

        notebook.add(self.settings_tab, text="Settings")
        notebook.add(self.database_tab, text="Database")
        notebook.add(self.operations_tab, text="Operations")

        self.applications_menu = tk.Menu(self)
        self.config(menu=self.applications_menu)
        file_menu = tk.Menu(self.applications_menu, tearoff=0)
        file_menu.add_command(label="Refresh", command=self._refresh_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        self.applications_menu.add_cascade(label="File", menu=file_menu)

    def _refresh_all(self) -> None:
        self.database_tab.refresh()
        self.operations_tab.refresh()
        self.notifications.notify("All tabs refreshed.")


if __name__ == "__main__":
    app = ServiceDaemonApp()
    app.mainloop()
