"""Read-only release audit of the configured tracker database and Excel export."""

from __future__ import annotations

from collections import Counter
from datetime import date
from io import BytesIO

import openpyxl
from dotenv import dotenv_values

from app.config import MODULES, REQUIRED_FIELDS
from app.tracker_store import MONTH_YEAR_FIELDS, SHEETS, TrackerStore


def main() -> None:
    environment = dotenv_values("../.env.local")
    url = environment.get("DATABASE_URL_UNPOOLED") or environment.get("DATABASE_URL")
    if not url:
        raise RuntimeError("No local DATABASE_URL was found")
    store = TrackerStore(url)
    with store.connect() as connection:
        connection.execute("set transaction read only")
        duplicates = connection.execute(
            "select count(*) as total from ("
            "select module, data->>'_source_sheet', data->>'_source_row' "
            "from tracker_entries where data->>'_source_row' is not null "
            "group by 1, 2, 3 having count(*) > 1) duplicates"
        ).fetchone()["total"]
    if duplicates:
        raise AssertionError(f"Duplicate imported source rows: {duplicates}")

    expected = Counter()
    meeting_month_mismatches = []
    missing_required = Counter()
    missing_required_rows = []
    serials = Counter()
    for module, sheet_names in SHEETS.items():
        for record in store.entries(module, limit=None):
            sheet = record.get("_source_sheet", MODULES[module]["sheet"])
            if sheet not in sheet_names:
                raise AssertionError(f"Unexpected source sheet in {module}: {sheet}")
            expected[sheet] += 1
            for field in REQUIRED_FIELDS[module]:
                if record.get(field) in (None, ""):
                    missing_required[(module, field)] += 1
                    missing_required_rows.append((record["_row"], sheet, record.get("_source_row"), field))
            serial_field = MODULES[module]["serial"]
            if serial_field and sheet == "Presales" and record.get(serial_field) not in (None, ""):
                serials[str(record[serial_field])] += 1
            if module == "weekly-meeting" and record.get("Date"):
                try:
                    meeting_date = date.fromisoformat(str(record["Date"])[:10])
                except ValueError:
                    meeting_month_mismatches.append(("invalid date", record.get("Month")))
                else:
                    if str(record.get("Month") or "").casefold() != meeting_date.strftime("%B").casefold():
                        meeting_month_mismatches.append((str(meeting_date), record.get("Month")))

    workbook = openpyxl.load_workbook(BytesIO(store.workbook_bytes()), read_only=True)
    try:
        for module, sheet_names in SHEETS.items():
            fields = MODULES[module]["fields"]
            for sheet_name in sheet_names:
                sheet = workbook[sheet_name]
                count = 0
                for row in sheet.iter_rows(min_row=2, max_col=len(fields)):
                    if not any(cell.value not in (None, "") for cell in row):
                        continue
                    count += 1
                    for field in MONTH_YEAR_FIELDS.intersection(fields):
                        cell = row[fields.index(field)]
                        if cell.value not in (None, "") and cell.number_format != "mmm-yy":
                            raise AssertionError(f"Wrong date format in {sheet_name} {cell.coordinate}")
                if count != expected[sheet_name]:
                    raise AssertionError(
                        f"{sheet_name}: database has {expected[sheet_name]} records, export has {count}"
                    )
                print(f"{sheet_name}: {count} records, export count matches")
    finally:
        workbook.close()
    print("Source-row and export checks passed")
    print(f"Meeting rows with Month different from Date: {meeting_month_mismatches}")
    print(f"Imported rows missing current required fields: {dict(missing_required)}")
    print(f"Rows needing completion (record ID, sheet, source row, field): {missing_required_rows}")
    print(f"Duplicate Presales meeting serial numbers: {[key for key, count in serials.items() if count > 1][:10]}")


if __name__ == "__main__":
    main()
