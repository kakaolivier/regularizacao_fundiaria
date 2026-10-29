@echo off
setlocal
cd /d "%~dp0"
echo Configurando Territorio Python nesta pasta...
if exist ".venv\Scripts\python.exe" goto install
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m venv .venv
if errorlevel 1 goto error
goto install
:use_python
python -m venv .venv
if errorlevel 1 goto error
:install
".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m pip install --only-binary=:all: -r requirements.txt
if errorlevel 1 goto error
echo.
echo Configuracao concluida. Execute iniciar.bat para abrir o sistema.
pause
exit /b 0
:error
echo.
echo Configuracao nao concluida. Confira a mensagem acima.
echo Requer Python 3.10 ou superior. Recomendado: Python 3.12 de 64 bits.
echo Se o download dos pacotes for bloqueado, consulte a TI sobre o acesso ao PyPI.
pause
exit /b 1
