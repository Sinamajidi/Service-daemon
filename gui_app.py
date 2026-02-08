"""
Desktop GUI application for the Service-daemon project.
Provides a corporate-themed Tkinter interface for database operations,
settings management, and operational scheduling.
"""

from __future__ import annotations

import json
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from tkinter import ttk, messagebox

from config import BOOKING_STATUSES
from database.data_access_layer import get_dal
from database.entity_access import get_booking_access
from database.db_connection import DatabaseConnection


BASE_DIR = Path(__file__).parent
SETTINGS_FILE = BASE_DIR / "app_settings.json"


@dataclass
class AppSettings:
    """Application settings stored in a local JSON file."""

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "apartment_mgmt"
    db_user: str = "postgres"
    db_password: str = "postgres"
    operations_refresh_seconds: int = 15
    operations_default_status: str = "requested"
    notifications_max: int = 20
    theme_primary: str = "#1F4E79"
    theme_secondary: str = "#2F75B5"

    @classmethod
    def load(cls, path: Path) -> "AppSettings":
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(**data)
        return cls()

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.__dict__, indent=2), encoding="utf-8")


class NotificationCenter:
    """In-app notification center with a status bar and message list."""

    def __init__(self, container: ttk.Frame, max_items: int = 20) -> None:
        self.max_items = max_items
        self.frame = ttk.LabelFrame(container, text="Notifications")
        self.frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(self.frame, height=6)
        self.listbox.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.status_var = tk.StringVar(value="Ready.")
        self.status_label = ttk.Label(self.frame, textvariable=self.status_var, anchor="w")
        self.status_label.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

    def notify(self, message: str, popup: bool = False) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.listbox.insert(0, entry)
        self.status_var.set(message)
        while self.listbox.size() > self.max_items:
            self.listbox.delete(tk.END)
        if popup:
            messagebox.showinfo("Notification", message)


class BaseTab(ttk.Frame):
    """Base class for tabs with access to the main app."""

    def __init__(self, master: ttk.Notebook, app: "MainApplication") -> None:
        super().__init__(master)
        self.app = app


class DashboardTab(BaseTab):
    """Summary dashboard with key metrics."""

    def __init__(self, master: ttk.Notebook, app: "MainApplication") -> None:
        super().__init__(master, app)
        self.configure(padding=16)
        self.metrics_frame = ttk.Frame(self)
        self.metrics_frame.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)

        self.cards: Dict[str, tk.StringVar] = {}
        self._build_cards()
        self.refresh_metrics()

    def _build_cards(self) -> None:
        labels = [
            ("Total Users", "users"),
            ("Active Tenants", "tenants"),
            ("Units", "units"),
            ("Open Bookings", "bookings"),
        ]
        for index, (title, key) in enumerate(labels):
            card = ttk.LabelFrame(self.metrics_frame, text=title)
            card.grid(row=0, column=index, padx=8, pady=8, sticky="nsew")
            self.metrics_frame.columnconfigure(index, weight=1)
            value_var = tk.StringVar(value="-")
            ttk.Label(card, textvariable=value_var, font=("Segoe UI", 20, "bold")).pack(
                padx=12, pady=16
            )
            self.cards[key] = value_var

        refresh_button = ttk.Button(self, text="Refresh Metrics", command=self.refresh_metrics)
        refresh_button.grid(row=1, column=0, sticky="w", pady=(12, 0))

    def refresh_metrics(self) -> None:
        dal = get_dal()
        self.cards["users"].set(str(dal.count_records("users")))
        self.cards["tenants"].set(str(dal.count_records("tenants")))
        self.cards["units"].set(str(dal.count_records("units")))
        open_count = dal.count_records("bookings", "status != 'completed'", ())
        self.cards["bookings"].set(str(open_count))
        self.app.notifications.notify("Dashboard metrics refreshed.")


class DatabaseTab(BaseTab):
    """Database browser tab for viewing and editing tables."""

    def __init__(self, master: ttk.Notebook, app: "MainApplication") -> None:
        super().__init__(master, app)
        self.configure(padding=12)
        self.dal = get_dal()
        self.table_list = tk.Listbox(self, height=14)
        self.table_list.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        self.table_list.bind("<<ListboxSelect>>", self._on_table_select)

        right_frame = ttk.Frame(self)
        right_frame.grid(row=0, column=1, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)

        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=0, column=0, sticky="ew")

        ttk.Button(button_frame, text="Refresh Tables", command=self.load_tables).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(button_frame, text="Edit Selected", command=self.edit_selected).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_selected).pack(
            side=tk.LEFT, padx=(0, 8)
        )

        self.table_label = ttk.Label(right_frame, text="Select a table to view data")
        self.table_label.grid(row=1, column=0, sticky="w", pady=(8, 4))

        self.tree = ttk.Treeview(right_frame, show="headings")
        self.tree.grid(row=2, column=0, sticky="nsew")
        right_frame.rowconfigure(2, weight=1)

        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.current_table: Optional[str] = None
        self.current_rows: Dict[str, Dict[str, Any]] = {}
        self.load_tables()

    def load_tables(self) -> None:
        self.table_list.delete(0, tk.END)
        tables = self.dal.execute_custom_query(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
            """,
            fetch="all",
        )
        for row in tables:
            self.table_list.insert(tk.END, row["table_name"])
        self.app.notifications.notify("Database tables loaded.")

    def _on_table_select(self, event: tk.Event) -> None:
        selection = self.table_list.curselection()
        if not selection:
            return
        self.current_table = self.table_list.get(selection[0])
        self.load_table_data(self.current_table)

    def load_table_data(self, table: str) -> None:
        self.table_label.configure(text=f"Table: {table}")
        columns = self.dal.execute_custom_query(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table,),
            fetch="all",
        )
        column_names = [col["column_name"] for col in columns]
        self.tree.configure(columns=column_names)
        self.tree.delete(*self.tree.get_children())
        for col in column_names:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="w")

        order_column = "created_at" if "created_at" in column_names else "id"
        rows = self.dal.execute_custom_query(
            f"SELECT * FROM {table} ORDER BY {order_column} DESC LIMIT 200", fetch="all"
        )
        self.current_rows = {}
        for row in rows or []:
            row_id = str(row.get("id", ""))
            self.current_rows[row_id] = row
            values = [self._format_cell(row.get(col)) for col in column_names]
            self.tree.insert("", tk.END, iid=row_id, values=values)

        self.app.notifications.notify(f"Loaded {len(rows or [])} records from {table}.")

    def _format_cell(self, value: Any) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        if value is None:
            return ""
        return str(value)

    def edit_selected(self) -> None:
        if not self.current_table:
            self.app.notifications.notify("Select a table first.", popup=True)
            return
        selected = self.tree.selection()
        if not selected:
            self.app.notifications.notify("Select a record to edit.", popup=True)
            return
        record_id = selected[0]
        record = self.current_rows.get(record_id)
        if not record:
            self.app.notifications.notify("Record data not available.", popup=True)
            return
        RecordEditor(self, self.current_table, record, self._on_record_updated)

    def delete_selected(self) -> None:
        if not self.current_table:
            self.app.notifications.notify("Select a table first.", popup=True)
            return
        selected = self.tree.selection()
        if not selected:
            self.app.notifications.notify("Select a record to delete.", popup=True)
            return
        record_id = selected[0]
        confirm = messagebox.askyesno("Confirm Delete", "Delete the selected record?")
        if not confirm:
            return
        success = self.dal.delete_record(self.current_table, record_id)
        if success:
            self.app.notifications.notify("Record deleted.")
            self.load_table_data(self.current_table)
        else:
            self.app.notifications.notify("Delete failed.", popup=True)

    def _on_record_updated(self) -> None:
        if self.current_table:
            self.load_table_data(self.current_table)


class RecordEditor(tk.Toplevel):
    """Modal dialog to edit a single database record."""

    def __init__(
        self,
        parent: DatabaseTab,
        table: str,
        record: Dict[str, Any],
        on_saved,
    ) -> None:
        super().__init__(parent)
        self.parent_tab = parent
        self.table = table
        self.record = record
        self.on_saved = on_saved

        self.title(f"Edit Record - {table}")
        self.resizable(False, False)

        self.entries: Dict[str, tk.Entry] = {}
        frame = ttk.Frame(self, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")

        row_index = 0
        for key, value in record.items():
            ttk.Label(frame, text=key).grid(row=row_index, column=0, sticky="w", pady=4)
            entry = ttk.Entry(frame, width=48)
            entry.grid(row=row_index, column=1, sticky="ew", pady=4)
            entry.insert(0, "" if value is None else str(value))
            if key == "id":
                entry.configure(state="disabled")
            self.entries[key] = entry
            row_index += 1

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row_index, column=0, columnspan=2, pady=(12, 0), sticky="e")
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.RIGHT, padx=4)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=4)

    def save(self) -> None:
        updates = {}
        for key, entry in self.entries.items():
            if key == "id":
                continue
            value = entry.get()
            updates[key] = value if value != "" else None
        record_id = self.record.get("id")
        success = self.parent_tab.dal.update_record(self.table, record_id, updates)
        if success:
            self.parent_tab.app.notifications.notify("Record updated successfully.")
            self.on_saved()
            self.destroy()
        else:
            self.parent_tab.app.notifications.notify("Update failed.", popup=True)


class OperationsTab(BaseTab):
    """Operations tab for managing bookings."""

    def __init__(self, master: ttk.Notebook, app: "MainApplication") -> None:
        super().__init__(master, app)
        self.configure(padding=12)
        self.booking_access = get_booking_access()
        self.dal = get_dal()

        control_frame = ttk.Frame(self)
        control_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.columnconfigure(0, weight=1)

        ttk.Label(control_frame, text="Status Filter:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value=self.app.settings.operations_default_status)
        status_menu = ttk.Combobox(
            control_frame, textvariable=self.status_var, values=["all"] + BOOKING_STATUSES
        )
        status_menu.pack(side=tk.LEFT, padx=8)
        ttk.Button(control_frame, text="Refresh", command=self.refresh_bookings).pack(
            side=tk.LEFT, padx=8
        )

        self.tree = ttk.Treeview(
            self,
            columns=("status", "priority", "unit", "tenant", "service", "scheduled"),
            show="headings",
        )
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=1)

        for col, label, width in [
            ("status", "Status", 100),
            ("priority", "Priority", 90),
            ("unit", "Unit", 90),
            ("tenant", "Tenant", 180),
            ("service", "Service", 160),
            ("scheduled", "Scheduled", 200),
        ]:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, anchor="w")

        detail_frame = ttk.LabelFrame(self, text="Operation Details", padding=12)
        detail_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        detail_frame.columnconfigure(1, weight=1)

        self.selected_booking_id: Optional[str] = None
        self.detail_vars = {
            "status": tk.StringVar(),
            "priority": tk.StringVar(),
            "notes": tk.StringVar(),
            "scheduled_start": tk.StringVar(),
            "scheduled_end": tk.StringVar(),
        }

        ttk.Label(detail_frame, text="Status:").grid(row=0, column=0, sticky="w")
        self.status_combo = ttk.Combobox(
            detail_frame, textvariable=self.detail_vars["status"], values=BOOKING_STATUSES
        )
        self.status_combo.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(detail_frame, text="Priority:").grid(row=1, column=0, sticky="w")
        ttk.Entry(detail_frame, textvariable=self.detail_vars["priority"]).grid(
            row=1, column=1, sticky="ew", pady=4
        )

        ttk.Label(detail_frame, text="Notes:").grid(row=2, column=0, sticky="w")
        ttk.Entry(detail_frame, textvariable=self.detail_vars["notes"]).grid(
            row=2, column=1, sticky="ew", pady=4
        )

        ttk.Label(detail_frame, text="Scheduled Start (YYYY-MM-DD HH:MM):").grid(
            row=3, column=0, sticky="w"
        )
        ttk.Entry(detail_frame, textvariable=self.detail_vars["scheduled_start"]).grid(
            row=3, column=1, sticky="ew", pady=4
        )

        ttk.Label(detail_frame, text="Scheduled End (YYYY-MM-DD HH:MM):").grid(
            row=4, column=0, sticky="w"
        )
        ttk.Entry(detail_frame, textvariable=self.detail_vars["scheduled_end"]).grid(
            row=4, column=1, sticky="ew", pady=4
        )

        ttk.Button(detail_frame, text="Save Changes", command=self.save_booking).grid(
            row=5, column=1, sticky="e", pady=(8, 0)
        )

        self.tree.bind("<<TreeviewSelect>>", self._on_booking_select)
        self.refresh_bookings()
        self._schedule_refresh()

    def refresh_bookings(self) -> None:
        status_filter = self.status_var.get()
        query = """
            SELECT b.id,
                   b.status,
                   b.priority,
                   b.notes,
                   b.scheduled_start,
                   b.scheduled_end,
                   un.unit_number,
                   u.full_name as tenant_name,
                   st.name as service_name
            FROM bookings b
            LEFT JOIN tenants t ON b.tenant_id = t.id
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN units un ON b.unit_id = un.id
            LEFT JOIN service_types st ON b.service_type_id = st.id
        """
        params: List[Any] = []
        if status_filter and status_filter != "all":
            query += " WHERE b.status = %s"
            params.append(status_filter)
        query += " ORDER BY b.created_at DESC"

        records = self.dal.execute_custom_query(query, tuple(params), fetch="all")
        self.tree.delete(*self.tree.get_children())
        for record in records or []:
            scheduled = self._format_schedule(record.get("scheduled_start"), record.get("scheduled_end"))
            self.tree.insert(
                "",
                tk.END,
                iid=str(record["id"]),
                values=(
                    record.get("status"),
                    record.get("priority"),
                    record.get("unit_number") or "-",
                    record.get("tenant_name") or "-",
                    record.get("service_name") or "-",
                    scheduled,
                ),
            )
        self.app.notifications.notify("Operations list refreshed.")

    def _format_schedule(self, start: Optional[datetime], end: Optional[datetime]) -> str:
        if not start and not end:
            return "Not scheduled"
        start_text = start.strftime("%Y-%m-%d %H:%M") if isinstance(start, datetime) else str(start)
        end_text = end.strftime("%Y-%m-%d %H:%M") if isinstance(end, datetime) else str(end)
        return f"{start_text} → {end_text}"

    def _on_booking_select(self, event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        booking_id = selection[0]
        data = self.booking_access.get_booking_data(booking_id)
        if not data:
            self.app.notifications.notify("Booking details unavailable.", popup=True)
            return
        self.selected_booking_id = booking_id
        self.detail_vars["status"].set(data.get("status", ""))
        self.detail_vars["priority"].set(data.get("priority", ""))
        self.detail_vars["notes"].set(data.get("notes", ""))
        self.detail_vars["scheduled_start"].set(self._format_datetime_entry(data.get("scheduled_start")))
        self.detail_vars["scheduled_end"].set(self._format_datetime_entry(data.get("scheduled_end")))

    def _format_datetime_entry(self, value: Optional[datetime]) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        return "" if value is None else str(value)

    def save_booking(self) -> None:
        if not self.selected_booking_id:
            self.app.notifications.notify("Select an operation first.", popup=True)
            return
        updates: Dict[str, Any] = {
            "status": self.detail_vars["status"].get(),
            "priority": self.detail_vars["priority"].get(),
            "notes": self.detail_vars["notes"].get(),
        }
        schedule_updates = self._parse_schedule_fields()
        if schedule_updates is None:
            return
        updates.update(schedule_updates)
        success = self.booking_access.update_booking(self.selected_booking_id, **updates)
        if success:
            self.app.notifications.notify("Operation updated successfully.")
            self.refresh_bookings()
        else:
            self.app.notifications.notify("Failed to update operation.", popup=True)

    def _parse_schedule_fields(self) -> Optional[Dict[str, Any]]:
        start_text = self.detail_vars["scheduled_start"].get().strip()
        end_text = self.detail_vars["scheduled_end"].get().strip()
        updates: Dict[str, Any] = {}
        try:
            updates["scheduled_start"] = (
                datetime.strptime(start_text, "%Y-%m-%d %H:%M") if start_text else None
            )
            updates["scheduled_end"] = (
                datetime.strptime(end_text, "%Y-%m-%d %H:%M") if end_text else None
            )
        except ValueError:
            self.app.notifications.notify(
                "Invalid date format. Use YYYY-MM-DD HH:MM.", popup=True
            )
            return None
        return updates

    def _schedule_refresh(self) -> None:
        refresh_ms = max(5, self.app.settings.operations_refresh_seconds) * 1000
        self.after(refresh_ms, self._auto_refresh)

    def _auto_refresh(self) -> None:
        self.refresh_bookings()
        self._schedule_refresh()


class SettingsTab(BaseTab):
    """Settings tab for database and operations configuration."""

    def __init__(self, master: ttk.Notebook, app: "MainApplication") -> None:
        super().__init__(master, app)
        self.configure(padding=16)

        db_frame = ttk.LabelFrame(self, text="Database Settings", padding=12)
        db_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        db_frame.columnconfigure(1, weight=1)

        self.db_vars = {
            "db_host": tk.StringVar(value=app.settings.db_host),
            "db_port": tk.StringVar(value=str(app.settings.db_port)),
            "db_name": tk.StringVar(value=app.settings.db_name),
            "db_user": tk.StringVar(value=app.settings.db_user),
            "db_password": tk.StringVar(value=app.settings.db_password),
        }

        self._add_entry(db_frame, "Host", 0, self.db_vars["db_host"])
        self._add_entry(db_frame, "Port", 1, self.db_vars["db_port"])
        self._add_entry(db_frame, "Database", 2, self.db_vars["db_name"])
        self._add_entry(db_frame, "User", 3, self.db_vars["db_user"])
        self._add_entry(db_frame, "Password", 4, self.db_vars["db_password"], show="*")

        ttk.Button(db_frame, text="Test Connection", command=self.test_connection).grid(
            row=5, column=1, sticky="e", pady=(8, 0)
        )

        ops_frame = ttk.LabelFrame(self, text="Operations Settings", padding=12)
        ops_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        ops_frame.columnconfigure(1, weight=1)

        self.ops_vars = {
            "operations_refresh_seconds": tk.StringVar(
                value=str(app.settings.operations_refresh_seconds)
            ),
            "operations_default_status": tk.StringVar(
                value=app.settings.operations_default_status
            ),
            "notifications_max": tk.StringVar(value=str(app.settings.notifications_max)),
        }

        self._add_entry(
            ops_frame,
            "Refresh Interval (seconds)",
            0,
            self.ops_vars["operations_refresh_seconds"],
        )
        ttk.Label(ops_frame, text="Default Status Filter").grid(
            row=1, column=0, sticky="w", pady=4
        )
        ttk.Combobox(
            ops_frame,
            textvariable=self.ops_vars["operations_default_status"],
            values=["all"] + BOOKING_STATUSES,
        ).grid(row=1, column=1, sticky="ew", pady=4)
        self._add_entry(ops_frame, "Max Notifications", 2, self.ops_vars["notifications_max"])

        action_frame = ttk.Frame(self)
        action_frame.grid(row=2, column=0, sticky="e")
        ttk.Button(action_frame, text="Save Settings", command=self.save_settings).pack(
            side=tk.RIGHT, padx=8
        )

    def _add_entry(
        self,
        frame: ttk.LabelFrame,
        label: str,
        row: int,
        variable: tk.StringVar,
        show: Optional[str] = None,
    ) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=variable, show=show).grid(
            row=row, column=1, sticky="ew", pady=4
        )

    def test_connection(self) -> None:
        settings = self._collect_settings()
        db = DatabaseConnection()
        db._initialize_pool(
            host=settings.db_host,
            port=int(settings.db_port),
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
        )
        db.execute_query("SELECT 1", fetch="one")
        db.close_all_connections()
        self.app.notifications.notify("Connection test succeeded.", popup=True)

    def save_settings(self) -> None:
        settings = self._collect_settings()
        self.app.settings = settings
        settings.save(SETTINGS_FILE)
        self.app.notifications.max_items = settings.notifications_max
        self.app.notifications.notify("Settings saved. Restart app to apply DB changes.", popup=True)

    def _collect_settings(self) -> AppSettings:
        return AppSettings(
            db_host=self.db_vars["db_host"].get(),
            db_port=int(self.db_vars["db_port"].get()),
            db_name=self.db_vars["db_name"].get(),
            db_user=self.db_vars["db_user"].get(),
            db_password=self.db_vars["db_password"].get(),
            operations_refresh_seconds=int(self.ops_vars["operations_refresh_seconds"].get()),
            operations_default_status=self.ops_vars["operations_default_status"].get(),
            notifications_max=int(self.ops_vars["notifications_max"].get()),
            theme_primary=self.app.settings.theme_primary,
            theme_secondary=self.app.settings.theme_secondary,
        )


class MainApplication(tk.Tk):
    """Main Tkinter application."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = AppSettings.load(SETTINGS_FILE)

        self.title("Service-daemon Control Center")
        self.geometry("1200x760")
        self.minsize(1024, 640)

        self._configure_theme()

        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(container)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.notifications = NotificationCenter(container, self.settings.notifications_max)

        self._create_tabs()

    def _configure_theme(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "TFrame",
            background="#F5F7FA",
        )
        style.configure(
            "TLabel",
            background="#F5F7FA",
            foreground="#1E2B3C",
        )
        style.configure(
            "TNotebook",
            background="#F5F7FA",
            tabmargins=(8, 8, 8, 0),
        )
        style.configure(
            "TNotebook.Tab",
            background="#D9E2EF",
            padding=(14, 6),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.settings.theme_primary)],
            foreground=[("selected", "#FFFFFF")],
        )
        style.configure("TButton", padding=(10, 6))
        style.configure(
            "TLabelframe",
            background="#F5F7FA",
            foreground="#1E2B3C",
        )
        style.configure(
            "TLabelframe.Label",
            background="#F5F7FA",
            foreground="#1E2B3C",
        )

    def _create_tabs(self) -> None:
        tabs = [
            ("Dashboard", DashboardTab),
            ("Database", DatabaseTab),
            ("Operations", OperationsTab),
            ("Settings", SettingsTab),
        ]
        for title, tab_class in tabs:
            tab = tab_class(self.notebook, self)
            self.notebook.add(tab, text=title)


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
