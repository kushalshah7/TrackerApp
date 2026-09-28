from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

import openpyxl
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

from .config import MODULES
from .tracker_store import SHEETS, TrackerStore, json_value


def migrate(path: Path, database_url: str | None = None) -> dict[str, int]:
    """Import the supplied workbook once; never replace live entries."""
    store = TrackerStore(database_url)
    store.initialize()
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    counts = {module: 0 for module in SHEETS}
    try:
        with store.connect() as connection:
            connection.execute("select pg_advisory_xact_lock(hashtext('tracker-workbook-import'))")
            existing = connection.execute("select count(*) as count from tracker_entries").fetchone()["count"]
            if existing:
                raise RuntimeError(f"Database already has {existing} entries; import cancelled")
            batch = []
            for module, sheet_names in SHEETS.items():
                fields = MODULES[module]["fields"]
                for sheet_name in sheet_names:
                    sheet = workbook[sheet_name]
                    headings = [cell.value for cell in next(sheet.iter_rows(min_row=1, max_row=1))]
                    expected = ["ISP Team" if sheet_name == "ISP Team" and field == "Presales" else field
                                for field in fields]
                    if headings[:len(fields)] != expected:
                        raise ValueError(f"Unexpected headers in {sheet_name}")
                    for row_number, cells in enumerate(sheet.iter_rows(min_row=2), 2):
                        values = [cell.value for cell in cells[:len(fields)]]
                        if not any(value not in (None, "") for value in values):
                            continue
                        data = {field: json_value(value) for field, value in zip(fields, values)}
                        data.update(_source_sheet=sheet_name, _source_row=row_number)
                        batch.append((module, Jsonb(data)))
                        counts[module] += 1
            with connection.cursor() as cursor:
                cursor.executemany(
                    "insert into tracker_entries(module, data) values (%s, %s)", batch
                )
            content = path.read_bytes()
            connection.execute(
                "insert into tracker_workbook_template(singleton, content, sha256) "
                "values (true, %s, %s) on conflict (singleton) do update "
                "set content = excluded.content, sha256 = excluded.sha256, updated_at = now()",
                (content, hashlib.sha256(content).hexdigest()),
            )
    finally:
        workbook.close()
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import the weekly tracker workbook")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    load_dotenv(".env.local")
    print(migrate(args.path, os.getenv("DATABASE_URL_UNPOOLED") or os.getenv("DATABASE_URL")))

