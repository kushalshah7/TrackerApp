# Repository Guidelines

## Project Structure & Module Organization

This repository contains a two-tier internal reporting application:

- `frontend/`: Vite, React, and TypeScript UI. Application code lives in `frontend/src/`; `App.tsx` composes the interface, `api.ts` handles backend calls, and `styles.css` contains shared styling.
- `backend/app/`: FastAPI service. `main.py` defines HTTP endpoints, `models.py` contains request/response models, and `excel_service.py` owns workbook reads, writes, locking, validation, and backups.
- `backend/tests/`: pytest tests, currently focused on Excel persistence and status updates.
- `backend/data/`: local workbook, template, lock, and backup files. These runtime artifacts are intentionally gitignored.

Keep workbook rules in the backend; frontend clients must not construct sheet names, cell references, or filesystem paths.

## Build, Test, and Development Commands

Run the backend from `backend/`:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
.venv\Scripts\python.exe -m pytest -q
```

The API is served at `http://localhost:8000`; pytest uses disposable workbooks and must never target the live file.

Run the frontend from `frontend/`:

```powershell
npm install
npm run dev
npm run build
npm run preview
```

`npm run build` performs TypeScript checking before producing the Vite bundle.

## Coding Style & Naming Conventions

Use four spaces for Python and two spaces for TypeScript/TSX. Follow PEP 8 conventions: `snake_case` for Python functions and variables, `PascalCase` for classes. In React, use `PascalCase` components, `camelCase` functions and values, and explicit shared types in `src/types.ts`. Prefer small, focused functions and keep API configuration centralized in `src/config.ts`. No formatter or linter is configured, so match nearby code and keep imports organized.

## Testing Guidelines

Name Python tests `test_*.py` and test functions `test_<behavior>`. Use pytest fixtures and `tmp_path` for workbook tests. Verify persistence by reopening generated files, and cover locking, backups, serial generation, and status changes when modifying `ExcelService`. Run `pytest -q` and `npm run build` before submitting changes.

## Commit & Pull Request Guidelines

Git history is unavailable in this checkout. Use concise, imperative commit subjects, optionally with a Conventional Commit prefix, for example `fix: preserve workbook summary rows`. Keep commits scoped to one concern. Pull requests should explain the user-visible change, list validation commands, link the relevant issue, and include screenshots for UI changes. Call out workbook schema, configuration, or deployment impacts explicitly.

## Security & Configuration

Never commit `.xlsx` files, backups, locks, secrets, or virtual environments. Keep `FRONTEND_ORIGIN` restricted in deployed environments. Use persistent storage for `backend/data/`; ephemeral serverless filesystems can lose submissions and backups.
