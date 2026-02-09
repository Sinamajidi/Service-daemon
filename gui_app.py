"""
Desktop GUI Application (Tkinter)
Provides a corporative, tabbed interface for settings, database, and operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv
import json
import platform
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from uuid import uuid4

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.data_access_layer import get_dal
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
        self._show_toast(message)

    def _show_toast(self, message: str) -> None:
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

        self.connection_status_var = tk.StringVar(value="Connection not tested")
        self.connection_status_label = tk.Label(
            container,
            textvariable=self.connection_status_var,
            fg="#7c2d12",
            bg="#f3f5f8",
        )
        self.connection_status_label.grid(row=6, column=0, sticky="w", pady=(8, 2))

        button_frame = ttk.Frame(container)
        button_frame.grid(row=6, column=1, sticky="e", pady=10)
        ttk.Button(button_frame, text="Save Settings", command=self._save).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(button_frame, text="Reload", command=self._reload).grid(
            row=0, column=1, padx=4
        )
        ttk.Button(
            button_frame,
            text="Test Connection",
            command=self._test_connection,
        ).grid(row=0, column=2, padx=4)

        service_frame = ttk.LabelFrame(container, text="PostgreSQL Service")
        service_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        service_frame.grid_columnconfigure(1, weight=1)

        self.service_status_var = tk.StringVar(value="Service status: Off")
        service_status = ttk.Label(service_frame, textvariable=self.service_status_var)
        service_status.grid(row=0, column=0, sticky="w", padx=8, pady=6)

        service_buttons = ttk.Frame(service_frame)
        service_buttons.grid(row=0, column=1, sticky="e", padx=8, pady=6)
        ttk.Button(service_buttons, text="Start", command=self._start_postgres).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(service_buttons, text="Stop", command=self._stop_postgres).grid(
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
        self._test_connection()

    def _reload(self) -> None:
        self.app.settings.load()
        self.host_var.set(self.app.settings.db_host)
        self.port_var.set(str(self.app.settings.db_port))
        self.name_var.set(self.app.settings.db_name)
        self.user_var.set(self.app.settings.db_user)
        self.password_var.set(self.app.settings.db_password)
        self.refresh_var.set(str(self.app.settings.refresh_interval_seconds))
        self.app.notifications.notify("Settings reloaded.")
        self._test_connection()

    def _test_connection(self) -> None:
        import psycopg2

        try:
            psycopg2.connect(
                host=self.host_var.get().strip(),
                port=int(self.port_var.get().strip()),
                dbname=self.name_var.get().strip(),
                user=self.user_var.get().strip(),
                password=self.password_var.get().strip(),
                connect_timeout=4,
            ).close()
        except Exception as exc:  # pragma: no cover - UI status
            self.connection_status_var.set(f"Connection failed: {exc}")
            self.connection_status_label.configure(fg="#b91c1c")
            self.app.notifications.notify("Database connection failed.")
            return
        self.connection_status_var.set("Connection OK")
        self.connection_status_label.configure(fg="#15803d")
        self.app.notifications.notify("Database connection OK.")

    def _start_postgres(self) -> None:
        self._run_service_command("start")

    def _stop_postgres(self) -> None:
        self._run_service_command("stop")

    def _run_service_command(self, action: str) -> None:
        commands: list[list[str]] = []
        system = platform.system().lower()
        if system == "windows":
            commands.append(["sc", action, "postgresql"])
        elif system == "darwin":
            commands.append(["brew", "services", action, "postgresql"])
        else:
            commands.append(["systemctl", action, "postgresql"])
            commands.append(["service", "postgresql", action])

        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                self.service_status_var.set(
                    f"Service status: {action.capitalize()} OK"
                )
                self.app.notifications.notify(
                    result.stdout.strip() or f"PostgreSQL {action} command executed."
                )
                return
            except (OSError, subprocess.CalledProcessError):
                continue

        self.service_status_var.set(f"Service status: {action.capitalize()} failed")
        self.app.notifications.notify(
            f"Unable to {action} PostgreSQL service. Check system permissions."
        )


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
        ttk.Button(toolbar, text="Add Entry", command=self._add_entry).grid(
            row=0, column=4, padx=6
        )
        ttk.Button(toolbar, text="Delete Selected", command=self._delete_selected).grid(
            row=0, column=5, padx=6
        )
        ttk.Button(toolbar, text="Import CSV", command=self._import_csv).grid(
            row=0, column=6, padx=6
        )
        ttk.Button(toolbar, text="Edit Selected", command=self._edit_selected).grid(
            row=0, column=7, padx=6
        )

        self.tree = ttk.Treeview(self, show="headings", selectmode="extended")
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

    def _add_entry(self) -> None:
        if not self.columns:
            self.app.notifications.notify("Load a table before adding entries.")
            return
        AddRecordDialog(
            self,
            self.app,
            f"Add {self.table_var.get()} record",
            self.columns,
            on_save=self._insert_record,
        )

    def _insert_record(self, data: dict[str, str | None]) -> None:
        cleaned = {key: value for key, value in data.items() if value not in (None, "")}
        try:
            get_dal().insert_record(self.table_var.get(), cleaned)
        except Exception as exc:
            self.app.notifications.notify(f"Insert failed: {exc}")
            return
        self.app.notifications.notify("Record added successfully.")
        self.refresh()

    def _delete_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            self.app.notifications.notify("Select one or more rows to delete.")
            return
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete {len(selection)} selected record(s)?",
        ):
            return
        table = self.table_var.get()
        deleted = 0
        for item_id in selection:
            values = self.tree.item(item_id, "values")
            data = dict(zip(self.columns, values))
            record_id = data.get("id")
            if not record_id:
                continue
            try:
                if get_dal().delete_record(table, record_id):
                    deleted += 1
            except Exception as exc:
                self.app.notifications.notify(f"Delete failed: {exc}")
                return
        self.app.notifications.notify(f"Deleted {deleted} record(s).")
        self.refresh()

    def _import_csv(self) -> None:
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not filename:
            return
        try:
            with open(filename, newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    self.app.notifications.notify("CSV file has no header row.")
                    return
                missing = [
                    col for col in self.columns if col not in reader.fieldnames
                ]
                if missing:
                    self.app.notifications.notify(
                        f"CSV missing columns: {', '.join(missing)}"
                    )
                    return
                count = 0
                for row in reader:
                    payload = {
                        key: (value if value != "" else None)
                        for key, value in row.items()
                        if key in self.columns
                    }
                    get_dal().insert_record(self.table_var.get(), payload)
                    count += 1
        except Exception as exc:
            self.app.notifications.notify(f"CSV import failed: {exc}")
            return
        self.app.notifications.notify(f"Imported {count} record(s).")
        self.refresh()


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


class AddRecordDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Widget,
        app: "ServiceDaemonApp",
        title: str,
        columns: list[str],
        on_save,
    ) -> None:
        super().__init__(parent)
        self.app = app
        self.columns = columns
        self.on_save = on_save
        self.entries: dict[str, tk.Entry] = {}
        self.title(title)
        self._build()

    def _build(self) -> None:
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        for idx, key in enumerate(self.columns):
            ttk.Label(container, text=key).grid(row=idx, column=0, sticky="w")
            entry = ttk.Entry(container)
            entry.grid(row=idx, column=1, sticky="ew", padx=6, pady=2)
            self.entries[key] = entry

        button_frame = ttk.Frame(container)
        button_frame.grid(row=len(self.columns), column=1, sticky="e", pady=8)
        ttk.Button(button_frame, text="Add", command=self._save).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(button_frame, text="Cancel", command=self.destroy).grid(
            row=0, column=1, padx=4
        )

    def _save(self) -> None:
        payload = {key: entry.get().strip() or None for key, entry in self.entries.items()}
        self.on_save(payload)
        self.destroy()


class JsonStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text())
        except json.JSONDecodeError:
            return []

    def save(self, records: list[dict]) -> None:
        self.path.write_text(json.dumps(records, indent=2) + "\n")


class JsonRecordDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Widget,
        app: "ServiceDaemonApp",
        title: str,
        field_specs: list[dict],
        on_save,
    ) -> None:
        super().__init__(parent)
        self.app = app
        self.field_specs = field_specs
        self.on_save = on_save
        self.inputs: dict[str, tk.Widget] = {}
        self.title(title)
        self._build()

    def _build(self) -> None:
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        for idx, field in enumerate(self.field_specs):
            ttk.Label(container, text=field["label"]).grid(row=idx, column=0, sticky="w")
            if field.get("widget") == "text":
                widget = tk.Text(container, height=3, width=40)
                widget.grid(row=idx, column=1, sticky="ew", padx=6, pady=2)
            else:
                widget = ttk.Entry(container)
                widget.grid(row=idx, column=1, sticky="ew", padx=6, pady=2)
            self.inputs[field["name"]] = widget

        button_frame = ttk.Frame(container)
        button_frame.grid(row=len(self.field_specs), column=1, sticky="e", pady=8)
        ttk.Button(button_frame, text="Add", command=self._save).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(button_frame, text="Cancel", command=self.destroy).grid(
            row=0, column=1, padx=4
        )

    def _save(self) -> None:
        payload: dict[str, object] = {}
        for field in self.field_specs:
            widget = self.inputs[field["name"]]
            if isinstance(widget, tk.Text):
                value = widget.get("1.0", "end").strip()
            else:
                value = widget.get().strip()

            if field.get("required") and not value:
                self.app.notifications.notify(
                    f"Field '{field['label']}' is required."
                )
                return

            if field.get("json") and value:
                try:
                    payload[field["name"]] = json.loads(value)
                except json.JSONDecodeError:
                    self.app.notifications.notify(
                        f"Field '{field['label']}' must be valid JSON."
                    )
                    return
            else:
                payload[field["name"]] = value or None

        self.on_save(payload)
        self.destroy()


class TasksTab(BaseTab):
    def __init__(self, parent: ttk.Notebook, app: "ServiceDaemonApp") -> None:
        super().__init__(parent, app)
        self.store = JsonStore(PROJECT_ROOT / "task_instances.json")
        self.records: list[dict] = []
        self._build()
        self.refresh()

    def _build(self) -> None:
        header = ttk.Label(self, text="Tasks", style="Header.TLabel")
        header.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        toolbar = ttk.Frame(self)
        toolbar.grid(row=1, column=0, sticky="ew", padx=12)
        toolbar.grid_columnconfigure(6, weight=1)

        ttk.Button(toolbar, text="Refresh", command=self.refresh).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(toolbar, text="Add Task", command=self._add_task).grid(
            row=0, column=1, padx=4
        )
        ttk.Button(toolbar, text="Delete Selected", command=self._delete_selected).grid(
            row=0, column=2, padx=4
        )
        ttk.Button(toolbar, text="Import CSV", command=self._import_csv).grid(
            row=0, column=3, padx=4
        )

        self.tree = ttk.Treeview(
            self,
            columns=(
                "instance_id",
                "template_id",
                "target_entity_id",
                "scheduled_time",
                "status",
                "assignee_ids",
            ),
            show="headings",
            selectmode="extended",
        )
        self.tree.grid(row=2, column=0, sticky="nsew", padx=12, pady=12)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="w")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.records = self.store.load()
        for record in self.records:
            self.tree.insert(
                "",
                "end",
                values=(
                    record.get("instance_id"),
                    record.get("template_id"),
                    record.get("target_entity_id"),
                    record.get("scheduled_time"),
                    record.get("status"),
                    self._format_cell(record.get("assignee_ids")),
                ),
            )
        self.app.notifications.notify(f"Loaded {len(self.records)} tasks.")

    def _format_cell(self, value: object) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return "" if value is None else str(value)

    def _add_task(self) -> None:
        JsonRecordDialog(
            self,
            self.app,
            "Add Task",
            TASK_INSTANCE_FIELDS,
            self._save_task,
        )

    def _save_task(self, data: dict[str, object]) -> None:
        if not data.get("instance_id"):
            data["instance_id"] = str(uuid4())
        self.records.append(data)
        self.store.save(self.records)
        self.app.notifications.notify("Task added successfully.")
        self.refresh()

    def _delete_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            self.app.notifications.notify("Select one or more tasks to delete.")
            return
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete {len(selection)} selected task(s)?",
        ):
            return
        ids_to_remove = {self.tree.item(item, "values")[0] for item in selection}
        self.records = [
            record
            for record in self.records
            if record.get("instance_id") not in ids_to_remove
        ]
        self.store.save(self.records)
        self.app.notifications.notify("Tasks deleted.")
        self.refresh()

    def _import_csv(self) -> None:
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not filename:
            return
        try:
            with open(filename, newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    self.app.notifications.notify("CSV file has no header row.")
                    return
                missing = [
                    field["name"]
                    for field in TASK_INSTANCE_FIELDS
                    if field["name"] not in reader.fieldnames
                ]
                if missing:
                    self.app.notifications.notify(
                        f"CSV missing columns: {', '.join(missing)}"
                    )
                    return
                count = 0
                for row in reader:
                    payload = self._parse_csv_row(row, TASK_INSTANCE_FIELDS)
                    if not payload.get("instance_id"):
                        payload["instance_id"] = str(uuid4())
                    self.records.append(payload)
                    count += 1
        except Exception as exc:
            self.app.notifications.notify(f"CSV import failed: {exc}")
            return
        self.store.save(self.records)
        self.app.notifications.notify(f"Imported {count} task(s).")
        self.refresh()

    def _parse_csv_row(self, row: dict[str, str], fields: list[dict]) -> dict:
        payload: dict[str, object] = {}
        field_map = {field["name"]: field for field in fields}
        for key, value in row.items():
            field = field_map.get(key)
            if not field:
                continue
            cleaned = value.strip()
            if field.get("json") and cleaned:
                payload[key] = json.loads(cleaned)
            else:
                payload[key] = cleaned or None
        for field in fields:
            if field.get("required") and not payload.get(field["name"]):
                raise ValueError(f"Missing required field {field['name']}")
        return payload


class TaskTemplatesTab(BaseTab):
    def __init__(self, parent: ttk.Notebook, app: "ServiceDaemonApp") -> None:
        super().__init__(parent, app)
        self.store = JsonStore(PROJECT_ROOT / "task_templates.json")
        self.records: list[dict] = []
        self._build()
        self.refresh()

    def _build(self) -> None:
        header = ttk.Label(self, text="Task Templates", style="Header.TLabel")
        header.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        toolbar = ttk.Frame(self)
        toolbar.grid(row=1, column=0, sticky="ew", padx=12)
        toolbar.grid_columnconfigure(6, weight=1)

        ttk.Button(toolbar, text="Refresh", command=self.refresh).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(toolbar, text="Add Template", command=self._add_template).grid(
            row=0, column=1, padx=4
        )
        ttk.Button(toolbar, text="Delete Selected", command=self._delete_selected).grid(
            row=0, column=2, padx=4
        )
        ttk.Button(toolbar, text="Import CSV", command=self._import_csv).grid(
            row=0, column=3, padx=4
        )

        self.tree = ttk.Treeview(
            self,
            columns=(
                "id",
                "title",
                "category",
                "description",
                "safety_level",
                "visibility",
            ),
            show="headings",
            selectmode="extended",
        )
        self.tree.grid(row=2, column=0, sticky="nsew", padx=12, pady=12)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=160, anchor="w")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.records = self.store.load()
        for record in self.records:
            self.tree.insert(
                "",
                "end",
                values=(
                    record.get("id"),
                    record.get("title"),
                    record.get("category"),
                    record.get("description"),
                    record.get("safety_level"),
                    self._format_cell(record.get("visibility")),
                ),
            )
        self.app.notifications.notify(
            f"Loaded {len(self.records)} task templates."
        )

    def _format_cell(self, value: object) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return "" if value is None else str(value)

    def _add_template(self) -> None:
        JsonRecordDialog(
            self,
            self.app,
            "Add Task Template",
            TASK_TEMPLATE_FIELDS,
            self._save_template,
        )

    def _save_template(self, data: dict[str, object]) -> None:
        if not data.get("id"):
            data["id"] = str(uuid4())
        self.records.append(data)
        self.store.save(self.records)
        self.app.notifications.notify("Task template added successfully.")
        self.refresh()

    def _delete_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            self.app.notifications.notify("Select templates to delete.")
            return
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete {len(selection)} selected template(s)?",
        ):
            return
        ids_to_remove = {self.tree.item(item, "values")[0] for item in selection}
        self.records = [
            record for record in self.records if record.get("id") not in ids_to_remove
        ]
        self.store.save(self.records)
        self.app.notifications.notify("Templates deleted.")
        self.refresh()

    def _import_csv(self) -> None:
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not filename:
            return
        try:
            with open(filename, newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    self.app.notifications.notify("CSV file has no header row.")
                    return
                missing = [
                    field["name"]
                    for field in TASK_TEMPLATE_FIELDS
                    if field["name"] not in reader.fieldnames
                ]
                if missing:
                    self.app.notifications.notify(
                        f"CSV missing columns: {', '.join(missing)}"
                    )
                    return
                count = 0
                for row in reader:
                    payload = self._parse_csv_row(row, TASK_TEMPLATE_FIELDS)
                    if not payload.get("id"):
                        payload["id"] = str(uuid4())
                    self.records.append(payload)
                    count += 1
        except Exception as exc:
            self.app.notifications.notify(f"CSV import failed: {exc}")
            return
        self.store.save(self.records)
        self.app.notifications.notify(f"Imported {count} template(s).")
        self.refresh()

    def _parse_csv_row(self, row: dict[str, str], fields: list[dict]) -> dict:
        payload: dict[str, object] = {}
        field_map = {field["name"]: field for field in fields}
        for key, value in row.items():
            field = field_map.get(key)
            if not field:
                continue
            cleaned = value.strip()
            if field.get("json") and cleaned:
                payload[key] = json.loads(cleaned)
            else:
                payload[key] = cleaned or None
        for field in fields:
            if field.get("required") and not payload.get(field["name"]):
                raise ValueError(f"Missing required field {field['name']}")
        return payload


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
        self.operations_tab = TasksTab(notebook, self)
        self.task_templates_tab = TaskTemplatesTab(notebook, self)

        notebook.add(self.settings_tab, text="Settings")
        notebook.add(self.database_tab, text="Database")
        notebook.add(self.operations_tab, text="Tasks")
        notebook.add(self.task_templates_tab, text="Task Templates")

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
        self.task_templates_tab.refresh()
        self.notifications.notify("All tabs refreshed.")


TASK_TEMPLATE_FIELDS = [
    {"name": "id", "label": "Template ID"},
    {"name": "title", "label": "Title", "required": True},
    {"name": "category", "label": "Category", "required": True},
    {"name": "description", "label": "Description", "required": True, "widget": "text"},
    {
        "name": "classification",
        "label": "Classification Tags (JSON)",
        "json": True,
        "required": True,
    },
    {
        "name": "scheduling_options",
        "label": "Scheduling Options (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {
        "name": "allowed_frequencies",
        "label": "Allowed Frequencies (JSON)",
        "json": True,
        "required": True,
    },
    {
        "name": "parameters",
        "label": "Parameters (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {
        "name": "preconditions",
        "label": "Preconditions (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {
        "name": "postconditions",
        "label": "Postconditions (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {
        "name": "resources_required",
        "label": "Resources Required (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {
        "name": "time_estimate",
        "label": "Time Estimate (JSON)",
        "json": True,
        "required": True,
    },
    {
        "name": "cost_model",
        "label": "Cost Model (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {"name": "safety_level", "label": "Safety Level", "required": True},
    {
        "name": "output_schema",
        "label": "Output Schema (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {
        "name": "quality_checks",
        "label": "Quality Checks (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {
        "name": "retry_policy",
        "label": "Retry Policy (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {
        "name": "concurrency_limits",
        "label": "Concurrency Limits (JSON)",
        "json": True,
        "required": True,
    },
    {
        "name": "visibility",
        "label": "Visibility (JSON)",
        "json": True,
        "required": True,
    },
    {
        "name": "virtual_effects",
        "label": "Virtual Effects (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {
        "name": "audit_fields_required",
        "label": "Audit Fields Required (JSON)",
        "json": True,
        "required": True,
    },
]

TASK_INSTANCE_FIELDS = [
    {"name": "instance_id", "label": "Instance ID"},
    {"name": "template_id", "label": "Template ID", "required": True},
    {"name": "target_entity_id", "label": "Target Entity ID", "required": True},
    {"name": "creator_id", "label": "Creator ID", "required": True},
    {
        "name": "assignee_ids",
        "label": "Assignee IDs (JSON)",
        "json": True,
        "required": True,
    },
    {"name": "scheduled_time", "label": "Scheduled Time", "required": True},
    {
        "name": "parameters",
        "label": "Parameters (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {"name": "status", "label": "Status", "required": True},
    {"name": "attempts", "label": "Attempts", "required": True},
    {
        "name": "result",
        "label": "Result (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {"name": "created_at", "label": "Created At", "required": True},
    {"name": "updated_at", "label": "Updated At", "required": True},
    {
        "name": "logs",
        "label": "Logs (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {
        "name": "attached_files",
        "label": "Attached Files (JSON)",
        "json": True,
        "required": True,
        "widget": "text",
    },
    {"name": "idempotency_key", "label": "Idempotency Key", "required": True},
]


if __name__ == "__main__":
    app = ServiceDaemonApp()
    app.mainloop()
