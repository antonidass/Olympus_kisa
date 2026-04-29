@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0.."
python automation\video_runner.py "content\Мидас и золотое прикосновение\prompts\video.md" %*
echo.
echo =====================================================
echo  Runner finished (exit=%ERRORLEVEL%). Close window manually.
echo =====================================================
pause
