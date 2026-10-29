@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Execute configurar.bat uma vez antes de iniciar.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" app.py --open
if errorlevel 1 pause
