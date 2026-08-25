from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .config import MODULES, STATUS_FIELDS
from .excel_service import WorkbookUnavailable
from .workbook_export import build_workbook


SCHEMA_SQL = """
create table if not exists tracker_entries (
  id bigint generated always as identity primary key,
  module text not null,
  data jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint tracker_entries_module_check check (module in (
    'weekly-review','weekly-meeting','training-attended','training-conducted',
    'poc','customer-workshop','win-lost'
  ))
);
create index if not exists tracker_entries_module_id_idx on tracker_entries(module, id desc);
create table if not exists tracker_status (
  presales text primary key,
  data jsonb not null,
  updated_at timestamptz not null default now()
);
create table if not exists tracker_reference_sheets (
  name text primary key,
  data jsonb not null,
  updated_at timestamptz not null default now()
);
create table if not exists tracker_workbook_template (
  singleton boolean primary key default true check (singleton),
  content bytea not null,
  sha256 text not null,
  updated_at timestamptz not null default now()
);
alter table tracker_entries enable row level security;
alter table tracker_status enable row level security;
alter table tracker_reference_sheets enable row level security;
alter table tracker_workbook_template enable row level security;
"""


def json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


class PostgresService:
    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL or POSTGRES_URL is required")

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(SCHEMA_SQL)

    def read_entries(self, module, presales=None, month=None, limit=50):
        cfg = MODULES[module]
        clauses, params = ["module = %s"], [module]
        if presales:
            clauses.append("lower(data->>%s) = lower(%s)")
            params.extend([cfg["presales"], presales])
        if month:
            clauses.append("lower(data->>'Month') = lower(%s)")
            params.append(month)
        params.append(min(limit, 5000))
        query = f"select id, data from tracker_entries where {' and '.join(clauses)} order by id desc limit %s"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [{**row["data"], "_row": row["id"]} for row in rows]

    def append_entry(self, module: str, data: dict[str, Any]):
        cfg = MODULES[module]
        unknown = set(data) - set(cfg["fields"])
        if unknown:
            raise ValueError(f"Unsupported fields: {', '.join(sorted(unknown))}")
        clean = {key: json_value(value) for key, value in data.items()}
        with self._connect() as connection:
            connection.execute("select pg_advisory_xact_lock(hashtext(%s))", (module,))
            if cfg["serial"]:
                serial = cfg["serial"]
                maximum = connection.execute(
                    "select coalesce(max(case when data->>%s ~ '^[0-9]+$' then (data->>%s)::bigint end), 0) as value from tracker_entries where module = %s",
                    (serial, serial, module),
                ).fetchone()["value"]
                clean[serial] = maximum + 1
            row = connection.execute(
                "insert into tracker_entries(module, data) values (%s, %s) returning id",
                (module, Jsonb(clean)),
            ).fetchone()
        return {"row": row["id"], "message": "Entry added successfully"}

    def update_entry(self, module: str, row: int, data: dict[str, Any]):
        cfg = MODULES[module]
        unknown = set(data) - set(cfg["fields"])
        if unknown:
            raise ValueError(f"Unsupported fields: {', '.join(sorted(unknown))}")
        clean = {key: json_value(value) for key, value in data.items()}
        with self._connect() as connection:
            current = connection.execute(
                "select data from tracker_entries where id = %s and module = %s for update", (row, module)
            ).fetchone()
            if not current:
                raise ValueError("Entry is not an editable data row")
            if current["data"].get("_source_row") is not None:
                clean["_source_row"] = current["data"]["_source_row"]
            if cfg["serial"]:
                clean[cfg["serial"]] = current["data"].get(cfg["serial"])
            connection.execute(
                "update tracker_entries set data = %s, updated_at = now() where id = %s",
                (Jsonb(clean), row),
            )
        return {"row": row, "message": "Entry updated successfully"}

    def status(self):
        with self._connect() as connection:
            rows = connection.execute("select data from tracker_status order by presales").fetchall()
        return [row["data"] for row in rows]

    def update_status(self, presales, module, status, up_to=None):
        label = STATUS_FIELDS[module]
        with self._connect() as connection:
            row = connection.execute(
                "select data from tracker_status where lower(presales) = lower(%s) for update", (presales,)
            ).fetchone()
            if not row:
                raise ValueError("Presales user not found")
            data = row["data"]
            data[label] = status
            if "Up to" in data:
                data["Up to"] = up_to or datetime.now().strftime("%d %b %Y")
            connection.execute(
                "update tracker_status set data = %s, updated_at = now() where lower(presales) = lower(%s)",
                (Jsonb(data), presales),
            )
        return {"message": f"{label} marked {status}"}

    def users(self):
        return [str(row["Presales Name"]) for row in self.status()]

    def raw_sheet(self, name, header_row=1):
        with self._connect() as connection:
            row = connection.execute("select data from tracker_reference_sheets where name = %s", (name,)).fetchone()
        return row["data"] if row else []

    def dashboard(self, presales):
        counts = {key: len(self.read_entries(key, presales, limit=100)) for key in MODULES}
        status = next((row for row in self.status() if str(row.get("Presales Name", "")).casefold() == presales.casefold()), {})
        recent = []
        for key in MODULES:
            for item in self.read_entries(key, presales, limit=3):
                recent.append({"module": key, **item})
        return {"counts": counts, "status": status, "recent": recent[:10]}

    def workbook_bytes(self) -> bytes:
        with self._connect() as connection:
            template = connection.execute("select content from tracker_workbook_template where singleton").fetchone()
        if not template:
            raise WorkbookUnavailable("Workbook template has not been imported")
        entries = {module: list(reversed(self.read_entries(module, limit=5000))) for module in MODULES}
        return build_workbook(bytes(template["content"]), entries, self.status())

