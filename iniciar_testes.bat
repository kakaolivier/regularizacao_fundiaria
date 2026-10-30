@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Execute configurar.bat antes de iniciar os testes.
  pause
  exit /b 1
)
echo Abrindo a base de testes em data-teste-manual, porta 3010.
echo Para usar sua base de trabalho habitual, utilize iniciar.bat.
".venv\Scripts\python.exe" app.py --data-dir data-teste-manual --port 3010 --open
if errorlevel 1 pause
