"""Main application entrypoint for the Service Daemon GUI."""

from __future__ import annotations

import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import psycopg2

if __package__ is None:  # pragma: no cover - support running as a script
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(PROJECT_ROOT))

from gui_app.tabs import (  # noqa: E402
    DatabaseTab,
    InfoTab,
    SettingsTab,
    SQLQueryTab,
    TaskTemplatesTab,
    TasksTab,
)
from gui_app.utils import (  # noqa: E402
    AppSettings,
    CorporateStyle,
    NotificationCenter,
    PROJECT_ROOT,
    configure_logging,
    logger,
)


class ServiceDaemonApp(tk.Tk):
    """Main Tkinter application for Service Daemon."""

    def __init__(self) -> None:
        super().__init__()
        configure_logging()
        self.project_root = PROJECT_ROOT
        self.title("Service Daemon Console")
        self.geometry("1200x720")
        self.minsize(980, 640)
        CorporateStyle(self)

        self.settings = AppSettings.from_defaults()
        self.settings.load()

        self._build_layout()

    def handle_db_exception(self, exc: Exception, notify: bool = True) -> bool:
        """Handle database connectivity errors gracefully."""
        connection_error = isinstance(
            exc, (psycopg2.OperationalError, psycopg2.InterfaceError)
        ) or "connection" in str(exc).lower()
        if not connection_error:
            return False
        if notify:
            self.notifications.notify(
                "Database connection error detected. Start PostgreSQL and retry."
            )
        logger.exception("Database connection error", exc_info=exc)
        return True

    def run_db_action(self, action, failure_message: str):
        """Execute a DB action with error handling."""
        try:
            return action()
        except Exception as exc:
            if not self.handle_db_exception(exc):
                self.notifications.notify(f"{failure_message}: {exc}")
                logger.exception(failure_message, exc_info=exc)
            return None

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
        self.sql_query_tab = SQLQueryTab(notebook, self)
        self.info_tab = InfoTab(notebook, self)

        notebook.add(self.settings_tab, text="Settings")
        notebook.add(self.database_tab, text="Database")
        notebook.add(self.operations_tab, text="Tasks")
        notebook.add(self.task_templates_tab, text="Task Templates")
        notebook.add(self.sql_query_tab, text="SQL Query Execution")
        notebook.add(self.info_tab, text="Info")

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


def main() -> None:
    app = ServiceDaemonApp()
    app.mainloop()


if __name__ == "__main__":
    main()
