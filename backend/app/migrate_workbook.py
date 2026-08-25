from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import openpyxl
from psycopg.types.json import Jsonb

from .config import MODULES
from .excel_service import ExcelService
from .postgres_service import PostgresService, json_value
from .workbook_export import editable_rows


def migrate(path: Path, replace: bool) -> None:
    service = PostgresService()
    service.initialize_schema()
    template = path.read_bytes()
    workbook = openpyxl.load_workbook(path, data_only=False)
    excel = ExcelService(path)
    with service._connect() as connection:
        existing = connection.execute("select count(*) as count from tracker_entries").fetchone()["count"]
        if existing and not replace:
            raise RuntimeError("Database already contains entries; use --replace only after verifying the target")
        if replace:
            connection.execute("truncate tracker_entries restart identity")
            connection.execute("truncate tracker_status")
            connection.execute("truncate tracker_reference_sheets")
        for module, cfg in MODULES.items():
            ws = workbook[cfg["sheet"]]
            for row in editable_rows(ws, cfg):
                data = {field: json_value(ws.cell(row, cfg["start_col"] + index).value) for index, field in enumerate(cfg["fields"])}
                data["_source_row"] = row
                connection.execute("insert into tracker_entries(module, data) values (%s, %s)", (module, Jsonb(data)))
        for status in excel.status():
            connection.execute(
                "insert into tracker_status(presales, data) values (%s, %s) on conflict (presales) do update set data = excluded.data, updated_at = now()",
                (str(status["Presales Name"]), Jsonb({key: json_value(value) for key, value in status.items()})),
            )
        for name in ("Client Managers Target", "Column Guide"):
            connection.execute(
                "insert into tracker_reference_sheets(name, data) values (%s, %s) on conflict (name) do update set data = excluded.data, updated_at = now()",
                (name, Jsonb(excel.raw_sheet(name))),
            )
        connection.execute(
            "insert into tracker_workbook_template(singleton, content, sha256) values (true, %s, %s) on conflict (singleton) do update set content = excluded.content, sha256 = excluded.sha256, updated_at = now()",
            (template, hashlib.sha256(template).hexdigest()),
        )
    workbook.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import the workbook into PostgreSQL/Supabase")
    parser.add_argument("path", type=Path)
    parser.add_argument("--replace", action="store_true")
    arguments = parser.parse_args()
    migrate(arguments.path, arguments.replace)

