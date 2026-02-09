"""Dialog windows for record editing and creation."""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk

from database.data_access_layer import get_dal
from .utils import logger


class RecordEditorDialog(tk.Toplevel):
    """Dialog for editing a single database record."""

    def __init__(
        self,
        parent: tk.Widget,
        app,
        table: str,
        data: dict,
        field_specs: list[dict],
        on_save,
    ) -> None:
        super().__init__(parent)
        self.app = app
        self.table = table
        self.data = data
        self.field_specs = field_specs
        self.on_save = on_save
        self.entries: dict[str, tk.Entry] = {}
        self.title(f"Edit {table} record")
        self._build()

    def _build(self) -> None:
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        field_map = {field["name"]: field for field in self.field_specs}
        for idx, (key, value) in enumerate(self.data.items()):
            field = field_map.get(key, {"name": key, "label": key})
            label = "password" if self.table == "users" and key == "password_hash" else key
            label = field.get("label", label)
            ttk.Label(container, text=label).grid(row=idx, column=0, sticky="w")
            entry: tk.Widget
            if field.get("options"):
                entry = ttk.Combobox(
                    container,
                    values=field["options"],
                    state="readonly",
                )
            else:
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
            logger.exception("Update failed", exc_info=exc)


class AddRecordDialog(tk.Toplevel):
    """Dialog for adding a new database record."""

    def __init__(
        self,
        parent: tk.Widget,
        app,
        title: str,
        field_specs: list[dict],
        on_save,
    ) -> None:
        super().__init__(parent)
        self.app = app
        self.field_specs = field_specs
        self.on_save = on_save
        self.entries: dict[str, tk.Entry] = {}
        self.placeholders: dict[str, str] = {}
        self.title(title)
        self._build()

    def _build(self) -> None:
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        for idx, field in enumerate(self.field_specs):
            name = field["name"]
            label = field.get("label", name)
            ttk.Label(container, text=label).grid(row=idx, column=0, sticky="w")
            entry: tk.Widget
            if field.get("options"):
                entry = ttk.Combobox(
                    container,
                    values=field["options"],
                    state="readonly",
                )
            else:
                entry_kwargs = {}
                if field.get("secret"):
                    entry_kwargs["show"] = "•"
                entry = ttk.Entry(container, **entry_kwargs)
            if field.get("auto"):
                entry.insert(0, "Auto-generated")
                entry.configure(state="disabled")
            elif field.get("placeholder") and isinstance(entry, ttk.Entry):
                entry.insert(0, field["placeholder"])
                self.placeholders[name] = field["placeholder"]
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
        payload = {}
        for field in self.field_specs:
            name = field["name"]
            if field.get("auto"):
                continue
            raw_value = self.entries[name].get().strip()
            placeholder = self.placeholders.get(name)
            if placeholder and raw_value == placeholder:
                raw_value = ""
            value = raw_value or None
            payload[name] = value
        self.on_save(payload)
        self.destroy()


class JsonRecordDialog(tk.Toplevel):
    """Dialog for creating JSON-backed task records."""

    def __init__(
        self,
        parent: tk.Widget,
        app,
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
                parsed = self._parse_json_field(field, value)
                if parsed is None:
                    return
                payload[field["name"]] = parsed
            else:
                payload[field["name"]] = value or None

        self.on_save(payload)
        self.destroy()

    def _parse_json_field(self, field: dict, raw_value: str) -> object | None:
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            field_name = field.get("name", "field")
            if field_name.endswith("_ids"):
                entries = [item.strip() for item in raw_value.split(",") if item.strip()]
                if entries:
                    return entries
            example = '["id1","id2"]' if field_name.endswith("_ids") else '{"key":"value"}'
            self.app.notifications.notify(
                f"Field '{field.get('label', field_name)}' must be JSON. "
                f"Example: {example}"
            )
            return None
