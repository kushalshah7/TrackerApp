from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import Response

from .config import MODULES
from .auth.neon_auth import AuthenticatedUser, check_invite, current_user, redeem_invite, verified_identity
from .models import DeleteEntryPayload, EntryPayload, InviteCheckPayload, InvitePayload, UpdateEntryPayload
from .tracker_store import ConflictError, TrackerStore

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
def names(user: Annotated[AuthenticatedUser, Depends(current_user)]):
    return store.names(user.presales)


@app.get("/api/me")
def me(user: Annotated[AuthenticatedUser, Depends(current_user)]):
    return {"name": user.display_name, "email": user.email, "role": "admin" if user.is_admin else "presales",
            "presales": user.presales}


@app.post("/api/auth/enroll")
def enroll(payload: InvitePayload, user: Annotated[AuthenticatedUser, Depends(verified_identity)]):
    redeem_invite(user, payload.code)
    return {"message": "Tracker access activated"}


@app.post("/api/auth/check-invite")
def check_invitation(payload: InviteCheckPayload):
    check_invite(payload.email, payload.code)
    return {"valid": True}


@app.get("/api/entries/{module}")
def entries(module: str, user: Annotated[AuthenticatedUser, Depends(current_user)],
            limit: int = Query(5000, ge=1, le=5000), before_id: int | None = Query(None, ge=1)):
    check_module(module)
    return store.entries(module, limit, user.presales, before_id)


@app.post("/api/entries/{module}", status_code=201)
def add_entry(module: str, payload: EntryPayload,
              user: Annotated[AuthenticatedUser, Depends(current_user)]):
    check_module(module)
    try:
        return store.add(module, payload.data, user.presales)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.patch("/api/entries/{module}/{record_id}")
def update_entry(module: str, record_id: int, payload: UpdateEntryPayload,
                 user: Annotated[AuthenticatedUser, Depends(current_user)]):
    check_module(module)
    try:
        return store.update(module, record_id, payload.data, payload.expected_last_edited_at, user.presales)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.delete("/api/entries/{module}/{record_id}")
def delete_entry(module: str, record_id: int, payload: DeleteEntryPayload,
                 user: Annotated[AuthenticatedUser, Depends(current_user)]):
    check_module(module)
    try:
        return store.delete(module, record_id, payload.expected_last_edited_at, user.presales)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/workbook/download")
def download(user: Annotated[AuthenticatedUser, Depends(current_user)]):
    content = store.workbook_bytes(user.presales)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return Response(
        content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="Presales_Weekly_Tracker_{stamp}.xlsx"',
                 "Cache-Control": "no-store"},
    )
