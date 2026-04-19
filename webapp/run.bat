@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM Показываем Flask'у, каким Python запускать CosyVoice 3 runner.
REM Отдельный venv в user-каталоге (conda-env в ProgramData без админа — read-only).
set "COSYVOICE_PYTHON=%USERPROFILE%\cosyvoice-venv\Scripts\python.exe"
if exist "%COSYVOICE_PYTHON%" (
  echo [webapp] CosyVoice Python: %COSYVOICE_PYTHON%
) else (
  echo [webapp] WARNING: CosyVoice venv не найден по пути %COSYVOICE_PYTHON%
  echo                   сначала запусти automation\setup_cosyvoice.bat
)

echo.
echo Запуск веб-приложения ревью озвучки...
echo.
python app.py
pause
