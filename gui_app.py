"""! @file gui_app.py
@brief Desktop GUI application (Tkinter) for the service daemon.

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
from uuid import UUID, uuid4

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import psycopg2

from database.data_access_layer import get_dal
from database.db_connection import get_db
from config import DB_CONFIG


SQL_EXECUTION_DIR = PROJECT_ROOT / "manual_sql"


@dataclass
class AppSettings:
    """! @brief Persisted GUI and database connection settings."""
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
        """! @brief Build settings using defaults and config overrides."""
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
        """! @brief Load settings from the environment and GUI settings files."""
        if self.env_path.exists():
            self._load_env_file()
        if self.gui_settings_path.exists():
            self._load_gui_settings()

    def save(self) -> None:
        """! @brief Persist settings to disk."""
        self._save_env_file()
        self._save_gui_settings()

    def _load_env_file(self) -> None:
        """! @brief Load DB settings from the .env file."""
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
        """! @brief Write DB settings to the .env file."""
        content = [
            f"DB_HOST={self.db_host}",
            f"DB_PORT={self.db_port}",
            f"DB_NAME={self.db_name}",
            f"DB_USER={self.db_user}",
            f"DB_PASSWORD={self.db_password}",
        ]
        self.env_path.write_text("\n".join(content) + "\n")

    def _load_gui_settings(self) -> None:
        """! @brief Load GUI-only settings from the settings JSON file."""
        try:
            data = json.loads(self.gui_settings_path.read_text())
        except (json.JSONDecodeError, OSError):
            return
        self.refresh_interval_seconds = self._safe_int(
            data.get("refresh_interval_seconds"),
            self.refresh_interval_seconds,
        )

    def _save_gui_settings(self) -> None:
        """! @brief Persist GUI-only settings to the settings JSON file."""
        data = {
            "refresh_interval_seconds": self.refresh_interval_seconds,
        }
        self.gui_settings_path.write_text(json.dumps(data, indent=2) + "\n")

    @staticmethod
    def _safe_int(value: str | int | None, default: int) -> int:
        """! @brief Convert a value to int, falling back to a default."""
        try:
            return int(value) if value is not None else default
        except (TypeError, ValueError):
            return default


class NotificationCenter:
    """! @brief Displays status notifications and transient toasts."""
    def __init__(self, parent: tk.Widget) -> None:
        """! @brief Create the notification widget container."""
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
        """! @brief Update the status message and show a toast."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_var.set(f"[{timestamp}] {message}")
        self._show_toast(message)

    def _show_toast(self, message: str) -> None:
        """! @brief Display a transient toast notification."""
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
    """! @brief Apply consistent corporate styling for widgets."""
    def __init__(self, root: tk.Tk) -> None:
        """! @brief Build the style configuration for the UI."""
        self.style = ttk.Style(root)
        self.root = root
        self._configure()

    def _configure(self) -> None:
        """! @brief Configure style rules for the application."""
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
    """! @brief Validate that a string is a valid UUID."""
    try:
        UUID(str(value))
        return True
    except (ValueError, TypeError):
        return False


class PostgresServiceManager:
    """! @brief Cross-platform PostgreSQL service helper."""
    def run(self, action: str) -> tuple[bool, str]:
        """! @brief Run the service command and return status."""
        commands: list[list[str]] = []
        system = platform.system().lower()
        if system == "windows":
            commands.append(["sc", action, "postgresql"])
        elif system == "darwin":
            commands.append(["brew", "services", action, "postgresql"])
        else:
            commands.append(["systemctl", action, "postgresql"])
            commands.append(["service", "postgresql", action])

        errors: list[str] = []
        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                message = result.stdout.strip() or f"PostgreSQL {action} command executed."
                return True, message
            except (OSError, subprocess.CalledProcessError) as exc:
                detail = getattr(exc, "stderr", None) or str(exc)
                errors.append(detail.strip())

        error_summary = "; ".join(error for error in errors if error)
        message = (
            error_summary
            or f"Unable to {action} PostgreSQL service. Check system permissions."
        )
        return False, message

    def start(self) -> tuple[bool, str]:
        """! @brief Start PostgreSQL service."""
        return self.run("start")

    def stop(self) -> tuple[bool, str]:
        """! @brief Stop PostgreSQL service."""
        return self.run("stop")


class BaseTab(ttk.Frame):
    """! @brief Base class for tab content frames."""
    def __init__(self, parent: ttk.Notebook, app: "ServiceDaemonApp") -> None:
        """! @brief Initialize the tab with a parent notebook and app context."""
        super().__init__(parent)
        self.app = app


class SettingsTab(BaseTab):
    """! @brief Tab for database and GUI settings."""
    def __init__(self, parent: ttk.Notebook, app: "ServiceDaemonApp") -> None:
        """! @brief Build the settings tab UI."""
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        """! @brief Construct the settings form layout."""
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
        """! @brief Persist settings and refresh the application state."""
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
        """! @brief Reload settings from disk and refresh the form."""
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
        """! @brief Attempt a direct database connection with current settings."""
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
            handled = self.app.handle_db_exception(exc, notify=False)
            self.connection_status_var.set(f"Connection failed: {exc}")
            self.connection_status_label.configure(fg="#b91c1c")
            if not handled:
                self.app.notifications.notify("Database connection failed.")
            return
        self.connection_status_var.set("Connection OK")
        self.connection_status_label.configure(fg="#15803d")
        self.app.notifications.notify("Database connection OK.")

    def _start_postgres(self) -> None:
        """! @brief Start the PostgreSQL service."""
        self._run_service_command("start")

    def _stop_postgres(self) -> None:
        """! @brief Stop the PostgreSQL service."""
        self._run_service_command("stop")

    def _run_service_command(self, action: str) -> None:
        """! @brief Run a platform-appropriate service command."""
        success, message = self.app.service_manager.run(action)
        if success:
            self.service_status_var.set(f"Service status: {action.capitalize()} OK")
        else:
            self.service_status_var.set(f"Service status: {action.capitalize()} failed")
        self.app.notifications.notify(message)


class DatabaseTab(BaseTab):
    """! @brief Tab for browsing and editing database tables."""
    def __init__(self, parent: ttk.Notebook, app: "ServiceDaemonApp") -> None:
        """! @brief Initialize the database tab and load table metadata."""
        super().__init__(parent, app)
        self.dal = get_dal()
        self.columns: list[str] = []
        self._build()

    def _build(self) -> None:
        """! @brief Build the database browsing layout."""
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
        """! @brief Fetch available table names from the database."""
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        results = self.app.run_db_action(
            lambda: self.dal.execute_custom_query(query, fetch="all"),
            "Unable to load tables",
        )
        if results is None:
            return []
        return [row["table_name"] for row in results] if results else []

    def _get_columns(self, table: str) -> list[str]:
        """! @brief Fetch column names for a selected table."""
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """
        results = self.app.run_db_action(
            lambda: self.dal.execute_custom_query(query, (table,), fetch="all"),
            "Unable to load columns",
        )
        if results is None:
            return []
        return [row["column_name"] for row in results] if results else []

    def refresh(self) -> None:
        """! @brief Refresh the table listing and data view."""
        table = self.table_var.get()
        def load_rows():
            self.columns = self._get_columns(table)
            self.tree.configure(columns=self.columns)
            for col in self.columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=140, anchor="w")
            for item in self.tree.get_children():
                self.tree.delete(item)
            return self.dal.get_filtered_records(table, "1=1", (), limit=200)

        rows = self.app.run_db_action(load_rows, "Database load failed")
        if rows is None:
            return
        for row in rows:
            values = [row.get(col) for col in self.columns]
            self.tree.insert("", "end", values=values)
        self.app.notifications.notify(f"Loaded {len(rows)} rows from {table}.")

    def _edit_selected(self) -> None:
        """! @brief Open an editor for the selected row."""
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
        """! @brief Open a dialog to add a new record."""
        if not self.columns:
            self.app.notifications.notify("Load a table before adding entries.")
            return
        field_specs = self._build_field_specs(self.table_var.get(), self.columns)
        AddRecordDialog(
            self,
            self.app,
            f"Add {self.table_var.get()} record",
            field_specs,
            on_save=self._insert_record,
        )

    def _insert_record(self, data: dict[str, str | None]) -> None:
        """! @brief Insert a new record and refresh the view."""
        cleaned = {key: value for key, value in data.items() if value not in (None, "")}
        if not self._validate_uuid_fields(cleaned):
            return
        try:
            get_dal().insert_record(self.table_var.get(), cleaned)
        except Exception as exc:
            if not self.app.handle_db_exception(exc):
                self.app.notifications.notify(f"Insert failed: {exc}")
            return
        self.app.notifications.notify("Record added successfully.")
        self.refresh()

    def _delete_selected(self) -> None:
        """! @brief Delete the selected record(s) from the table."""
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
                if not self.app.handle_db_exception(exc):
                    self.app.notifications.notify(f"Delete failed: {exc}")
                return
        self.app.notifications.notify(f"Deleted {deleted} record(s).")
        self.refresh()

    def _import_csv(self) -> None:
        """! @brief Import records from a CSV file into the selected table."""
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
                    if not self._validate_uuid_fields(payload):
                        return
                    get_dal().insert_record(self.table_var.get(), payload)
                    count += 1
        except Exception as exc:
            if not self.app.handle_db_exception(exc):
                self.app.notifications.notify(f"CSV import failed: {exc}")
            return
        self.app.notifications.notify(f"Imported {count} record(s).")
        self.refresh()

    def _build_field_specs(self, table: str, columns: list[str]) -> list[dict]:
        """! @brief Build field specifications for record dialogs."""
        field_specs = []
        for column in columns:
            field = {"name": column, "label": column}
            if column == "id":
                field["auto"] = True
            if table == "users" and column == "password_hash":
                field["label"] = "password"
                field["secret"] = True
            field_specs.append(field)
        return field_specs

    def _validate_uuid_fields(self, payload: dict[str, object]) -> bool:
        """! @brief Ensure UUID fields contain valid UUIDs."""
        for key, value in payload.items():
            if value in (None, ""):
                continue
            if key == "id" or key.endswith("_id"):
                if not is_valid_uuid(str(value)):
                    self.app.notifications.notify(
                        f"{key} must be a valid UUID value."
                    )
                    return False
        return True


class RecordEditorDialog(tk.Toplevel):
    """! @brief Dialog for editing a single database record."""
    def __init__(
        self,
        parent: tk.Widget,
        app: "ServiceDaemonApp",
        table: str,
        data: dict,
        on_save,
    ) -> None:
        """! @brief Initialize the record editor dialog."""
        super().__init__(parent)
        self.app = app
        self.table = table
        self.data = data
        self.on_save = on_save
        self.entries: dict[str, tk.Entry] = {}
        self.title(f"Edit {table} record")
        self._build()

    def _build(self) -> None:
        """! @brief Build the form inputs for editing."""
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        for idx, (key, value) in enumerate(self.data.items()):
            label = "password" if self.table == "users" and key == "password_hash" else key
            ttk.Label(container, text=label).grid(row=idx, column=0, sticky="w")
            entry_kwargs = {}
            if self.table == "users" and key == "password_hash":
                entry_kwargs["show"] = "•"
            entry = ttk.Entry(container, **entry_kwargs)
            if not (self.table == "users" and key == "password_hash"):
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
        """! @brief Persist edits back to the database."""
        updated = {}
        for key, entry in self.entries.items():
            if key == "id":
                continue
            value = entry.get() or None
            if self.table == "users" and key == "password_hash":
                if not value:
                    continue
                updated[key] = value
            else:
                updated[key] = value
        if not self.app.database_tab._validate_uuid_fields(updated):
            return
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
    """! @brief Dialog for adding a new database record."""
    def __init__(
        self,
        parent: tk.Widget,
        app: "ServiceDaemonApp",
        title: str,
        field_specs: list[dict],
        on_save,
    ) -> None:
        """! @brief Initialize the add-record dialog."""
        super().__init__(parent)
        self.app = app
        self.field_specs = field_specs
        self.on_save = on_save
        self.entries: dict[str, tk.Entry] = {}
        self.title(title)
        self._build()

    def _build(self) -> None:
        """! @brief Build the form inputs for a new record."""
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        for idx, field in enumerate(self.field_specs):
            name = field["name"]
            label = field.get("label", name)
            ttk.Label(container, text=label).grid(row=idx, column=0, sticky="w")
            entry_kwargs = {}
            if field.get("secret"):
                entry_kwargs["show"] = "•"
            entry = ttk.Entry(container, **entry_kwargs)
            if field.get("auto"):
                entry.insert(0, "Auto-generated")
                entry.configure(state="disabled")
            entry.grid(row=idx, column=1, sticky="ew", padx=6, pady=2)
            self.entries[name] = entry

        button_frame = ttk.Frame(container)
        button_frame.grid(row=len(self.field_specs), column=1, sticky="e", pady=8)
        ttk.Button(button_frame, text="Add", command=self._save).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(button_frame, text="Cancel", command=self.destroy).grid(
            row=0, column=1, padx=4
        )

    def _save(self) -> None:
        """! @brief Submit the new record payload."""
        payload = {}
        for field in self.field_specs:
            name = field["name"]
            if field.get("auto"):
                continue
            value = self.entries[name].get().strip() or None
            payload[name] = value
        self.on_save(payload)
        self.destroy()


class JsonStore:
    """! @brief Simple JSON file storage for task data."""
    def __init__(self, path: Path) -> None:
        """! @brief Initialize the JSON store with a backing file path."""
        self.path = path

    def load(self) -> list[dict]:
        """! @brief Load records from disk, returning an empty list on failure."""
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text())
        except json.JSONDecodeError:
            return []

    def save(self, records: list[dict]) -> None:
        """! @brief Persist records to disk as JSON."""
        self.path.write_text(json.dumps(records, indent=2) + "\n")


class JsonRecordDialog(tk.Toplevel):
    """! @brief Dialog for creating JSON-backed task records."""
    def __init__(
        self,
        parent: tk.Widget,
        app: "ServiceDaemonApp",
        title: str,
        field_specs: list[dict],
        on_save,
    ) -> None:
        """! @brief Initialize the JSON record dialog."""
        super().__init__(parent)
        self.app = app
        self.field_specs = field_specs
        self.on_save = on_save
        self.inputs: dict[str, tk.Widget] = {}
        self.title(title)
        self._build()

    def _build(self) -> None:
        """! @brief Build the form inputs for JSON-backed fields."""
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
            if field.get("auto"):
                widget.insert(0, "Auto-generated")
                widget.configure(state="disabled")
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
        """! @brief Validate and submit the JSON record."""
        payload: dict[str, object] = {}
        for field in self.field_specs:
            if field.get("auto"):
                continue
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
    """! @brief Tab for managing task instances stored in JSON."""
    def __init__(self, parent: ttk.Notebook, app: "ServiceDaemonApp") -> None:
        """! @brief Initialize the tasks tab and load records."""
        super().__init__(parent, app)
        self.store = JsonStore(PROJECT_ROOT / "task_instances.json")
        self.records: list[dict] = []
        self._build()
        self.refresh()

    def _build(self) -> None:
        """! @brief Build the tasks table layout."""
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
        """! @brief Reload task instances from disk and render them."""
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
        """! @brief Format list/dict values for display in the table."""
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return "" if value is None else str(value)

    def _add_task(self) -> None:
        """! @brief Open the dialog to create a new task."""
        JsonRecordDialog(
            self,
            self.app,
            "Add Task",
            TASK_INSTANCE_FIELDS,
            self._save_task,
        )

    def _save_task(self, data: dict[str, object]) -> None:
        """! @brief Persist a new task record."""
        if not data.get("instance_id"):
            data["instance_id"] = str(uuid4())
        self.records.append(data)
        self.store.save(self.records)
        self.app.notifications.notify("Task added successfully.")
        self.refresh()

    def _delete_selected(self) -> None:
        """! @brief Delete selected task instances."""
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
        """! @brief Import task instances from a CSV file."""
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
        """! @brief Parse a CSV row into a task payload."""
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
    """! @brief Tab for managing task templates stored in JSON."""
    def __init__(self, parent: ttk.Notebook, app: "ServiceDaemonApp") -> None:
        """! @brief Initialize the task templates tab."""
        super().__init__(parent, app)
        self.store = JsonStore(PROJECT_ROOT / "task_templates.json")
        self.records: list[dict] = []
        self._build()
        self.refresh()

    def _build(self) -> None:
        """! @brief Build the task templates table layout."""
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
        """! @brief Reload task templates from disk and render them."""
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
        """! @brief Format list/dict values for display in the table."""
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return "" if value is None else str(value)

    def _add_template(self) -> None:
        """! @brief Open the dialog to create a new task template."""
        JsonRecordDialog(
            self,
            self.app,
            "Add Task Template",
            TASK_TEMPLATE_FIELDS,
            self._save_template,
        )

    def _save_template(self, data: dict[str, object]) -> None:
        """! @brief Persist a new task template record."""
        if not data.get("id"):
            data["id"] = str(uuid4())
        self.records.append(data)
        self.store.save(self.records)
        self.app.notifications.notify("Task template added successfully.")
        self.refresh()

    def _delete_selected(self) -> None:
        """! @brief Delete selected task templates."""
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
        """! @brief Import task templates from a CSV file."""
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
        """! @brief Parse a CSV row into a task template payload."""
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


class SQLQueryTab(BaseTab):
    """! @brief Tab for executing ad-hoc SQL queries."""
    def __init__(self, parent: ttk.Notebook, app: "ServiceDaemonApp") -> None:
        super().__init__(parent, app)
        self.loaded_sql_path: Path | None = None
        self._build()

    def _build(self) -> None:
        header = ttk.Label(self, text="SQL Query Execution", style="Header.TLabel")
        header.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        toolbar = ttk.Frame(self)
        toolbar.grid(row=1, column=0, sticky="ew", padx=12)
        toolbar.grid_columnconfigure(3, weight=1)

        ttk.Button(toolbar, text="Import SQL", command=self._import_sql).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(toolbar, text="Execute", command=self._execute_queries).grid(
            row=0, column=1, padx=4
        )
        ttk.Button(toolbar, text="Clear Logs", command=self._clear_logs).grid(
            row=0, column=2, padx=4
        )

        query_frame = ttk.LabelFrame(self, text="SQL Console")
        query_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=8)
        query_frame.grid_columnconfigure(0, weight=1)
        query_frame.grid_rowconfigure(0, weight=1)

        self.query_text = tk.Text(query_frame, height=10, wrap="word")
        self.query_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        log_frame = ttk.LabelFrame(self, text="Execution Logs")
        log_frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=8)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=12, wrap="word", state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.log_text.tag_configure("error", foreground="#b91c1c")

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _append_log(self, message: str, is_error: bool = False) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        tag = "error" if is_error else None
        self.log_text.insert("end", f"[{timestamp}] {message}\n", tag)
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def _clear_logs(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _import_sql(self) -> None:
        sql_files = sorted(SQL_EXECUTION_DIR.glob("*.sql")) if SQL_EXECUTION_DIR.exists() else []
        if not sql_files:
            self.app.notifications.notify("There are no SQL files to import.")
            return
        filename = filedialog.askopenfilename(
            title="Select SQL File",
            filetypes=[("SQL Files", "*.sql")],
            initialdir=str(SQL_EXECUTION_DIR),
        )
        if not filename:
            return
        selected_path = Path(filename)
        if SQL_EXECUTION_DIR not in selected_path.parents:
            self.app.notifications.notify(
                "Select a SQL file from the manual_sql folder."
            )
            return
        self.loaded_sql_path = selected_path
        self.query_text.delete("1.0", "end")
        self.query_text.insert("1.0", selected_path.read_text())
        self.app.notifications.notify(f"Loaded {selected_path.name}.")

    def _execute_queries(self) -> None:
        raw = self.query_text.get("1.0", "end").strip()
        if not raw:
            self.app.notifications.notify("Enter SQL before executing.")
            return
        statements = [stmt.strip() for stmt in raw.split(";") if stmt.strip()]
        for statement in statements:
            self._execute_statement(statement)
        if self.loaded_sql_path and messagebox.askyesno(
            "Delete SQL file?",
            f"Delete {self.loaded_sql_path.name} after execution?",
        ):
            try:
                self.loaded_sql_path.unlink()
                self.app.notifications.notify("SQL file deleted.")
            except OSError as exc:
                self._append_log(f"Delete failed: {exc}", is_error=True)
            self.loaded_sql_path = None

    def _execute_statement(self, statement: str) -> None:
        db = get_db()
        try:
            with db.get_cursor(dict_cursor=True) as cur:
                cur.execute(statement)
                if cur.description:
                    rows = cur.fetchall()
                    self._append_log(f"Query returned {len(rows)} row(s).")
                    if rows:
                        preview = json.dumps(rows[:5], indent=2, default=str)
                        self._append_log(preview)
                else:
                    self._append_log(f"Statement OK ({cur.rowcount} row(s) affected).")
        except Exception as exc:
            if self.app.handle_db_exception(exc):
                return
            self._append_log(f"{type(exc).__name__}: {exc}", is_error=True)


class ServiceDaemonApp(tk.Tk):
    """! @brief Main Tkinter application for Service Daemon."""
    def __init__(self) -> None:
        """! @brief Initialize the GUI application window."""
        super().__init__()
        self.title("Service Daemon Console")
        self.geometry("1200x720")
        self.minsize(980, 640)
        CorporateStyle(self)
        self.service_manager = PostgresServiceManager()

        self.settings = AppSettings.from_defaults()
        self.settings.load()

        self._build_layout()

    def handle_db_exception(self, exc: Exception, notify: bool = True) -> bool:
        """! @brief Handle database connectivity errors gracefully."""
        connection_error = isinstance(
            exc, (psycopg2.OperationalError, psycopg2.InterfaceError)
        ) or "connection" in str(exc).lower()
        if not connection_error:
            return False
        if notify:
            self.notifications.notify("Database connection error detected.")
        if messagebox.askyesno(
            "Database connection",
            "PostgreSQL appears to be stopped. Start the service now?",
        ):
            success, message = self.service_manager.start()
            self.notifications.notify(message)
        return True

    def run_db_action(self, action, failure_message: str):
        """! @brief Execute a DB action with error handling."""
        try:
            return action()
        except Exception as exc:
            if not self.handle_db_exception(exc):
                self.notifications.notify(f"{failure_message}: {exc}")
            return None

    def _build_layout(self) -> None:
        """! @brief Build the main application layout."""
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
        self.sql_query_tab = SQLQueryTab(notebook, self)

        notebook.add(self.settings_tab, text="Settings")
        notebook.add(self.database_tab, text="Database")
        notebook.add(self.operations_tab, text="Tasks")
        notebook.add(self.task_templates_tab, text="Task Templates")
        notebook.add(self.sql_query_tab, text="SQL Query Execution")

        self.applications_menu = tk.Menu(self)
        self.config(menu=self.applications_menu)
        file_menu = tk.Menu(self.applications_menu, tearoff=0)
        file_menu.add_command(label="Refresh", command=self._refresh_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        self.applications_menu.add_cascade(label="File", menu=file_menu)

    def _refresh_all(self) -> None:
        """! @brief Refresh all tabs and update status messaging."""
        self.database_tab.refresh()
        self.operations_tab.refresh()
        self.task_templates_tab.refresh()
        self.notifications.notify("All tabs refreshed.")


TASK_TEMPLATE_FIELDS = [
    {"name": "id", "label": "Template ID", "auto": True},
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
    {"name": "instance_id", "label": "Instance ID", "auto": True},
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
