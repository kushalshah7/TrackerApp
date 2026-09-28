from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response

from .config import MODULES
from .models import EntryPayload
from .tracker_store import TrackerStore

app = FastAPI(title="Presales Weekly Tracker API", version="2.1.0")
store = TrackerStore()
VISIBLE_MODULES = {"weekly-review", "weekly-meeting"}


def check_module(module: str):
    if module not in VISIBLE_MODULES:
        raise HTTPException(404, "Unknown tracker")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/names")
def names():
    return store.names()


@app.get("/api/entries/{module}")
def entries(module: str, limit: int = Query(5000, ge=1, le=5000)):
    check_module(module)
    return store.entries(module, limit)


@app.post("/api/entries/{module}", status_code=201)
def add_entry(module: str, payload: EntryPayload):
    check_module(module)
    try:
        return store.add(module, payload.data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.patch("/api/entries/{module}/{record_id}")
def update_entry(module: str, record_id: int, payload: EntryPayload):
    check_module(module)
    try:
        return store.update(module, record_id, payload.data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.delete("/api/entries/{module}/{record_id}")
def delete_entry(module: str, record_id: int):
    check_module(module)
    try:
        return store.delete(module, record_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/workbook/download")
def download():
    content = store.workbook_bytes()
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return Response(
        content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="Presales_Weekly_Tracker_{stamp}.xlsx"',
                 "Cache-Control": "no-store"},
    )
