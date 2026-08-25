# Presales Weekly Tracker

A React + FastAPI internal reporting app that treats the existing Excel workbook as its only source of truth. It includes every editable reporting module, submission status, recent activity, read-only references, and complete workbook download.

## 1. Add the workbook

Copy the supplied workbook into `backend/data/` twice:

```text
backend/data/Workbook.xlsx
backend/data/Workbook_TEMPLATE.xlsx
```

The `_TEMPLATE` file is the untouched recovery master. The app writes only to `Workbook.xlsx`. Workbook files are gitignored intentionally.

## 2. Start the backend

PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

API docs are available at `http://localhost:8000/docs`. `GET /api/health` reports whether the workbook is ready.

## 3. Start the frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Workbook safety

Every mutation acquires both a process lock and file lock, reloads the latest workbook, creates a timestamped backup, writes to a temporary `.xlsx`, reopens it for validation, then atomically replaces the active workbook. The latest 10 automatic backups are retained in `backend/data/backups/`.

To recover:

1. Stop the backend.
2. Move the damaged active workbook out of `backend/data/` for investigation.
3. Copy the newest valid file from `backend/data/backups/` to `backend/data/Workbook.xlsx`.
4. Open it in Excel to verify it, then restart the backend.

If no backup is suitable, restore from `Workbook_TEMPLATE.xlsx`; this loses submissions made after the template was created.

## Validation and tests

Run backend tests from `backend/`:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

The automated suite creates a disposable workbook with the original sheet/header layout, writes one row through every editable module, reopens the result, checks serial generation/status updates, and confirms backups exist. Before production rollout, repeat the test against a copy of the actual supplied workbook; never point tests at the live active file.

Build the frontend:

```powershell
cd frontend
npm run build
```

## Deployment

Use a company VM, internal server, Docker host, or another environment with a persistent mounted filesystem. The workbook and backups must survive process and host restarts. Do not deploy this backend to ephemeral serverless storage. Restrict `FRONTEND_ORIGIN` to the deployed frontend origin, put the internal service behind your company network/reverse proxy, and back up `backend/data/` independently.

## Notes

- Presales users are read from the `Status` sheet; the UI uses the supplied fallback list only while the workbook is unavailable.
- Sheet names and allowed field names are mapped on the backend. Clients cannot supply sheet names, row numbers, cell references, or file paths.
- New values are normalized by the form controls; historical workbook data is never mass-edited.
- Win/Lost inserts before the first summary/formula row so the summary region is preserved.
