@echo off
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
REM Clean inherited werkzeug FDs from parent webapp process - otherwise
REM Flask in this child tries socket.fromfd() and fails with WinError 10038.
set WERKZEUG_SERVER_FD=
set WERKZEUG_RUN_MAIN=

set "REPO_ROOT=%~dp0.."

echo [start] repo = %REPO_ROOT%

set "COSY_PY="
if defined COSYVOICE_PYTHON if exist "%COSYVOICE_PYTHON%" set "COSY_PY=%COSYVOICE_PYTHON%"
if not defined COSY_PY if exist "%USERPROFILE%\cosyvoice-venv\Scripts\python.exe" set "COSY_PY=%USERPROFILE%\cosyvoice-venv\Scripts\python.exe"

if not defined COSY_PY (
    echo [start] ERROR: cosyvoice python not found
    echo        Expected: %USERPROFILE%\cosyvoice-venv\Scripts\python.exe
    echo        Or set env COSYVOICE_PYTHON to absolute path
    pause
    exit /b 2
)

echo [start] python = %COSY_PY%

"%COSY_PY%" -c "import flask" 1>nul 2>nul
if errorlevel 1 (
    echo [start] flask not installed - installing...
    "%COSY_PY%" -m pip install flask
    if errorlevel 1 (
        echo [start] ERROR: pip install flask failed
        pause
        exit /b 3
    )
    echo [start] flask installed
)

echo [start] starting cosyvoice_server.py on 127.0.0.1:5001
echo [start] first start is slow - model loads in ~30 sec, do not close
echo.

cd /d "%REPO_ROOT%"
"%COSY_PY%" "%REPO_ROOT%\automation\cosyvoice_server.py" --host 127.0.0.1 --port 5001 %*

set RC=%ERRORLEVEL%
echo.
echo ========================================================
echo  CosyVoice server exited (code=%RC%)
echo  Window stays open - check errors above
echo ========================================================
pause