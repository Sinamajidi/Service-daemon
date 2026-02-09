"""Tab implementations for the Service Daemon GUI."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from uuid import uuid4

import psycopg2

from database.data_access_layer import get_dal
from database.db_connection import get_db
from .dialogs import AddRecordDialog, JsonRecordDialog, RecordEditorDialog
from .utils import (
    INFO_CONFIG_PATH,
    SQL_EXECUTION_DIR,
    is_valid_uuid,
    logger,
)


class BaseTab(ttk.Frame):
    """Base class for tab content frames."""

    def __init__(self, parent: ttk.Notebook, app) -> None:
        super().__init__(parent)
        self.app = app


class SettingsTab(BaseTab):
    """Tab for database and GUI settings."""

    def __init__(self, parent: ttk.Notebook, app) -> None:
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
            fg="#6b7280",
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

        self.after(200, self._test_connection)

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
                logger.exception("Database connection failed", exc_info=exc)
            return
        self.connection_status_var.set("Connection OK")
        self.connection_status_label.configure(fg="#15803d")
        self.app.notifications.notify("Database connection OK.")


class DatabaseTab(BaseTab):
    """Tab for browsing and editing database tables."""

    def __init__(self, parent: ttk.Notebook, app) -> None:
        super().__init__(parent, app)
        self.dal = get_dal()
        self.columns: list[str] = []
        self.column_types: dict[str, str] = {}
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
        results = self.app.run_db_action(
            lambda: self.dal.execute_custom_query(query, fetch="all"),
            "Unable to load tables",
        )
        if results is None:
            return []
        return [row["table_name"] for row in results] if results else []

    def _get_columns(self, table: str) -> list[str]:
        query = """
            SELECT column_name, data_type
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
        self.column_types = {
            row["column_name"]: row["data_type"] for row in results if row
        }
        return [row["column_name"] for row in results] if results else []

    def refresh(self) -> None:
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
        selection = self.tree.selection()
        if not selection:
            self.app.notifications.notify("Select a row to edit.")
            return
        values = self.tree.item(selection[0], "values")
        data = dict(zip(self.columns, values))
        if "id" not in data:
            self.app.notifications.notify("Selected table lacks an 'id' column.")
            return
        field_specs = self._build_field_specs(self.table_var.get(), self.columns)
        RecordEditorDialog(
            self,
            self.app,
            self.table_var.get(),
            data,
            field_specs,
            self.refresh,
        )

    def _add_entry(self) -> None:
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
        cleaned = {key: value for key, value in data.items() if value not in (None, "")}
        if not self._validate_uuid_fields(cleaned):
            return
        try:
            get_dal().insert_record(self.table_var.get(), cleaned)
        except Exception as exc:
            if not self.app.handle_db_exception(exc):
                self.app.notifications.notify(f"Insert failed: {exc}")
                logger.exception("Insert failed", exc_info=exc)
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
                if not self.app.handle_db_exception(exc):
                    self.app.notifications.notify(f"Delete failed: {exc}")
                    logger.exception("Delete failed", exc_info=exc)
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
                    if not self._validate_uuid_fields(payload):
                        return
                    get_dal().insert_record(self.table_var.get(), payload)
                    count += 1
        except Exception as exc:
            if not self.app.handle_db_exception(exc):
                self.app.notifications.notify(f"CSV import failed: {exc}")
                logger.exception("CSV import failed", exc_info=exc)
            return
        self.app.notifications.notify(f"Imported {count} record(s).")
        self.refresh()

    def _build_field_specs(self, table: str, columns: list[str]) -> list[dict]:
        enum_options = {
            "role": ["tenant", "manager", "provider_staff", "admin"],
            "status": [
                "requested",
                "scheduled",
                "assigned",
                "in_progress",
                "completed",
                "cancelled",
            ],
            "priority": ["low", "normal", "high", "emergency"],
            "safety_level": ["low", "medium", "high"],
        }
        field_specs = []
        for column in columns:
            field = {"name": column, "label": column}
            data_type = self.column_types.get(column)
            if column in {"id", "created_at", "updated_at"}:
                field["auto"] = True
            if data_type in {"timestamp with time zone", "timestamp without time zone"}:
                field["label"] = f"{column} (YYYY-MM-DD HH:MM:SS+00)"
                field["placeholder"] = "YYYY-MM-DD HH:MM:SS+00"
            elif data_type == "date":
                field["label"] = f"{column} (YYYY-MM-DD)"
                field["placeholder"] = "YYYY-MM-DD"
            elif data_type == "time without time zone":
                field["label"] = f"{column} (HH:MM:SS)"
                field["placeholder"] = "HH:MM:SS"
            if data_type == "boolean":
                field["options"] = ["true", "false"]
            if column in enum_options:
                field["options"] = enum_options[column]
            if table == "users" and column == "password_hash":
                field["label"] = "password"
                field["secret"] = True
            field_specs.append(field)
        return field_specs

    def _validate_uuid_fields(self, payload: dict[str, object]) -> bool:
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


class JsonStore:
    """Simple JSON file storage for task data."""

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


class TasksTab(BaseTab):
    """Tab for managing task instances stored in JSON."""

    def __init__(self, parent: ttk.Notebook, app) -> None:
        super().__init__(parent, app)
        self.store = JsonStore(self.app.project_root / "task_instances.json")
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
            logger.exception("CSV import failed", exc_info=exc)
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
    """Tab for managing task templates stored in JSON."""

    def __init__(self, parent: ttk.Notebook, app) -> None:
        super().__init__(parent, app)
        self.store = JsonStore(self.app.project_root / "task_templates.json")
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
            logger.exception("CSV import failed", exc_info=exc)
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


def _split_sql_statements(raw: str) -> list[str]:
    statements = []
    current = []
    in_single = False
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "'":
            current.append(ch)
            if in_single and i + 1 < len(raw) and raw[i + 1] == "'":
                current.append("'")
                i += 1
            else:
                in_single = not in_single
        elif ch == ";" and not in_single:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(ch)
        i += 1
    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)
    return statements


class SQLQueryTab(BaseTab):
    """Tab for executing ad-hoc SQL queries."""

    def __init__(self, parent: ttk.Notebook, app) -> None:
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
        statements = _split_sql_statements(raw)
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
            logger.exception("SQL execution failed", exc_info=exc)


class InfoTab(BaseTab):
    """Tab for displaying application information."""

    def __init__(self, parent: ttk.Notebook, app) -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        header = ttk.Label(self, text="Info", style="Header.TLabel")
        header.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        container = ttk.Frame(self)
        container.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        container.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        info_text = tk.Text(container, wrap="word", height=18)
        info_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        info_text.configure(state="disabled")

        info = self._load_info()
        info_text.configure(state="normal")
        info_text.insert("1.0", self._format_info(info))
        info_text.configure(state="disabled")

    def _load_info(self) -> dict:
        if not INFO_CONFIG_PATH.exists():
            return {"title": "Service Daemon", "description": "Info file missing."}
        try:
            return json.loads(INFO_CONFIG_PATH.read_text())
        except json.JSONDecodeError:
            return {"title": "Service Daemon", "description": "Invalid info file."}

    def _format_info(self, info: dict) -> str:
        lines = []
        title = info.get("title")
        if title:
            lines.append(title)
            lines.append("=" * len(title))
        description = info.get("description")
        if description:
            lines.append(description)
            lines.append("")
        authors = info.get("authors")
        if authors:
            lines.append("Authors:")
            for author in authors:
                lines.append(f"- {author}")
            lines.append("")
        metadata = info.get("metadata")
        if isinstance(metadata, dict):
            lines.append("Details:")
            for key, value in metadata.items():
                lines.append(f"- {key}: {value}")
        return "\n".join(lines).strip() + "\n"


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
