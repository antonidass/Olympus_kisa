@echo off
REM BOGI AI — webapp launcher (двойной клик).
REM Просто вызывает start_webapp.ps1 с обходом ExecutionPolicy.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_webapp.ps1"
