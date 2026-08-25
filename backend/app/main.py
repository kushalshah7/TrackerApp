import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from .config import MODULES, WORKBOOK_PATH
from .excel_service import ExcelService, WorkbookUnavailable
from .models import EntryPayload, StatusPayload

app = FastAPI(title="Presales Weekly Tracker API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")], allow_credentials=True, allow_methods=["GET", "POST", "PATCH"], allow_headers=["*"])
if os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL"):
    from .postgres_service import PostgresService

    service = PostgresService()
else:
    service = ExcelService()

@app.exception_handler(WorkbookUnavailable)
async def workbook_missing(_, exc): return __import__("fastapi").responses.JSONResponse(status_code=503, content={"detail": str(exc)})

@app.get("/api/health")
def health():
    return {"status": "ok", "workbook_ready": True if hasattr(service, "workbook_bytes") else WORKBOOK_PATH.exists()}

@app.get("/api/users")
def users(): return service.users()

@app.get("/api/dashboard")
def dashboard(presales: str): return service.dashboard(presales)

@app.get("/api/entries/{module}")
def entries(module: str, presales: str | None = None, month: str | None = None, limit: int = Query(50, ge=1, le=5000)):
    if module not in MODULES: raise HTTPException(404, "Unknown module")
    return service.read_entries(module, presales, month, limit)

@app.post("/api/entries/{module}", status_code=201)
def add_entry(module: str, payload: EntryPayload):
    if module not in MODULES: raise HTTPException(404, "Unknown module")
    try: return service.append_entry(module, payload.data)
    except ValueError as exc: raise HTTPException(422, str(exc))

@app.patch("/api/entries/{module}/{row}")
def update_entry(module: str, row: int, payload: EntryPayload):
    if module not in MODULES: raise HTTPException(404, "Unknown module")
    try: return service.update_entry(module, row, payload.data)
    except ValueError as exc: raise HTTPException(422, str(exc))

@app.get("/api/status")
def status(): return service.status()

@app.patch("/api/status/{presales}/{module}")
def update_status(presales: str, module: str, payload: StatusPayload):
    if module not in {k for k in MODULES if k != "win-lost"}: raise HTTPException(404, "Unknown status module")
    try: return service.update_status(presales, module, payload.status, payload.up_to)
    except ValueError as exc: raise HTTPException(404, str(exc))

@app.get("/api/client-manager-targets")
def targets(): return service.raw_sheet("Client Managers Target")

@app.get("/api/column-guide")
def guide(): return service.raw_sheet("Column Guide")

@app.get("/api/workbook/download")
def download():
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    if hasattr(service, "workbook_bytes"):
        return Response(
            service.workbook_bytes(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="Presales_Weekly_Tracker_{stamp}.xlsx"'},
        )
    service._ensure()
    return FileResponse(WORKBOOK_PATH, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=f"Presales_Weekly_Tracker_{stamp}.xlsx")

