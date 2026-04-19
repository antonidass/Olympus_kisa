@echo off
rem Pure ASCII bat — no Cyrillic inside to avoid cp866/UTF-8 conflict.
rem Russian path is stored inside run_video_sizif.py (UTF-8 source).
rem `title` must be ASCII — libuv (used by Playwright/Node) crashes on non-ASCII
rem window title when reading process title via WideCharToMultiByte.
title video_runner_sizif
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0.."
python -u automation\run_video_sizif.py
echo.
echo --- done, press any key to close ---
pause >nul
