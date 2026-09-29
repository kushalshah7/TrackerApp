from __future__ import annotations

import os
from datetime import date, datetime, timezone
from io import BytesIO
from typing import Any

import openpyxl
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .config import MODULES, validate_entry_data


SHEETS = {"weekly-review": ("Presales Review",), "weekly-meeting": ("Presales", "ISP Team")}
MEETING_HEADERS = MODULES["weekly-meeting"]["fields"]
PRESALES_NAMES = (
    "Aditya Potdar",
    "Ankesh Singh",
    "Arun M",
    "Ayush Rajput",
    "Irshad",
    "Kalim Ansari",
    "Suraj Raskar",
    "Surender Kumar",
)


def json_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    return value


def canonical_full_names(values: list[str]) -> list[str]:
    """Collapse case and short/full-name variants, preferring the common full name."""
    counts: dict[str, tuple[str, int]] = {}
    for value in values:
        name = value.strip()
        if not name:
            continue
        key = name.casefold()
        display, count = counts.get(key, (name, 0))
        counts[key] = (display, count + 1)

    by_first_name: dict[str, list[tuple[str, int]]] = {}
    for display, count in counts.values():
        first_name = display.split()[0].casefold()
        by_first_name.setdefault(first_name, []).append((display, count))

    result = []
    for variants in by_first_name.values():
        full_names = [(name, count) for name, count in variants if len(name.split()) > 1]
        if full_names:
            # Frequency resolves spelling variants; length makes the fallback deterministic.
            result.append(max(full_names, key=lambda item: (item[1], len(item[0])))[0])
        else:
            result.extend(name for name, _ in variants)
    return sorted(result, key=str.casefold)


class TrackerStore:
    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is required")

    def connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def initialize(self):
        with self.connect() as connection:
            connection.execute("""
                create table if not exists tracker_entries (
                    id bigint generated always as identity primary key,
                    module text not null,
                    data jsonb not null,
                    created_at timestamptz not null default now(),
                    updated_at timestamptz not null default now()
                );
                create index if not exists tracker_entries_module_id_idx on tracker_entries(module, id desc);
                create table if not exists tracker_workbook_template (
                    singleton boolean primary key default true check (singleton),
                    content bytea not null,
                    sha256 text not null,
                    updated_at timestamptz not null default now()
                );
                alter table tracker_entries add column if not exists last_edited_at timestamptz;
                alter table tracker_entries enable row level security;
                alter table tracker_workbook_template enable row level security;
            """)

    def entries(self, module: str, limit: int = 5000):
        with self.connect() as connection:
            rows = connection.execute(
                "select id, data, last_edited_at from tracker_entries where module = %s order by id desc limit %s",
                (module, limit),
            ).fetchall()
        return [{**row["data"], "_row": row["id"],
                 "_last_edited_at": row["last_edited_at"].isoformat() if row["last_edited_at"] else None}
                for row in rows]

    def names(self):
        with self.connect() as connection:
            rows = connection.execute(
                "select module, nullif(btrim(data->>'AM'), '') as am, "
                "nullif(btrim(data->>'Client Manager'), '') as client_manager "
                "from tracker_entries "
                "where module in ('weekly-meeting', 'weekly-review')"
            ).fetchall()
        account_managers = []
        for row in rows:
            field = "am" if row["module"] == "weekly-review" else "client_manager"
            value = row[field]
            if isinstance(value, str) and value.strip():
                account_managers.append(value)
        return {"am": canonical_full_names(account_managers),
                "presales": list(PRESALES_NAMES)}

    def _clean(self, module: str, data: dict[str, Any]):
        validate_entry_data(module, data)
        unknown = set(data) - set(MODULES[module]["fields"])
        if unknown:
            raise ValueError(f"Unsupported fields: {', '.join(sorted(unknown))}")
        return {key: json_value(value) for key, value in data.items()}

    def add(self, module: str, data: dict[str, Any]):
        clean = self._clean(module, data)
        with self.connect() as connection:
            connection.execute("select pg_advisory_xact_lock(hashtext(%s))", (module,))
            serial = MODULES[module]["serial"]
            if serial:
                maximum = connection.execute(
                    "select coalesce(max((data->>%s)::int), 0) as maximum from tracker_entries "
                    "where module = %s and data->>%s ~ '^[0-9]+$' and coalesce(data->>'_source_sheet', 'Presales') = 'Presales'",
                    (serial, module, serial),
                ).fetchone()["maximum"]
                clean[serial] = maximum + 1
            row = connection.execute(
                "insert into tracker_entries(module, data, last_edited_at) values (%s, %s, now()) returning id",
                (module, Jsonb(clean)),
            ).fetchone()
        return {"row": row["id"], "message": "Entry added successfully"}

    def update(self, module: str, record_id: int, data: dict[str, Any]):
        clean = self._clean(module, data)
        with self.connect() as connection:
            old = connection.execute(
                "select data from tracker_entries where id = %s and module = %s for update",
                (record_id, module),
            ).fetchone()
            if not old:
                raise ValueError("Entry was not found")
            for key in ("_source_row", "_source_sheet", MODULES[module]["serial"]):
                if key and key in old["data"]:
                    clean[key] = old["data"][key]
            connection.execute(
                "update tracker_entries set data = %s, updated_at = now(), last_edited_at = now() where id = %s",
                (Jsonb(clean), record_id),
            )
        return {"row": record_id, "message": "Entry updated successfully"}

    def delete(self, module: str, record_id: int):
        with self.connect() as connection:
            row = connection.execute(
                "delete from tracker_entries where module = %s and id = %s returning id",
                (module, record_id),
            ).fetchone()
            if not row:
                raise ValueError("Entry was not found")
        return {"row": record_id, "message": "Entry deleted successfully"}

    def workbook_bytes(self):
        with self.connect() as connection:
            template = connection.execute(
                "select content from tracker_workbook_template where singleton = true"
            ).fetchone()
        if not template:
            raise ValueError("Workbook has not been imported")
        workbook = openpyxl.load_workbook(BytesIO(bytes(template["content"])))
        for module, names in SHEETS.items():
            records = list(reversed(self.entries(module)))
            for sheet_name in names:
                sheet = workbook[sheet_name]
                fields = MODULES[module]["fields"]
                original_rows = [row for row in range(2, sheet.max_row + 1)
                                 if any(sheet.cell(row, col).value not in (None, "")
                                        for col in range(1, len(fields) + 1))]
                for row in original_rows:
                    for col in range(1, len(fields) + 1):
                        sheet.cell(row, col).value = None
                next_row = max(original_rows, default=1) + 1
                for record in records:
                    if record.get("_source_sheet", MODULES[module]["sheet"]) != sheet_name:
                        continue
                    target = record.get("_source_row") or next_row
                    if not record.get("_source_row"):
                        next_row += 1
                    for col, field in enumerate(fields, 1):
                        value = record.get(field)
                        if field in {"Date", "Date of Opportunity (MM/YY)", "Expected Month"} and isinstance(value, str):
                            try:
                                value = date.fromisoformat(value)
                            except ValueError:
                                pass
                        sheet.cell(target, col).value = value
        output = BytesIO()
        workbook.save(output)
        workbook.close()
        return output.getvalue()
