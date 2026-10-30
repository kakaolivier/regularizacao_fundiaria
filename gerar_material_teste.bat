@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Execute configurar.bat antes de gerar o material de teste.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\gerar_material_teste.py
if errorlevel 1 (
  pause
  exit /b 1
)
echo.
echo Consulte docs\MANUAL-DE-TESTES.md e execute iniciar_testes.bat.
pause
