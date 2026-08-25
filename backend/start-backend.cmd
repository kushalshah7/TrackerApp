@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Backend environment not found. Run: python -m venv .venv
  exit /b 1
)

".venv\Scripts\python.exe" -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
  echo Backend dependencies are missing. Run: .venv\Scripts\python.exe -m pip install -r requirements.txt
  exit /b 1
)

".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
