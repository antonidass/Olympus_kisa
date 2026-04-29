@echo off
rem Launches regular Google Chrome with remote-debugging-port so video_runner
rem can attach via CDP. Chrome is user-launched — no automation flags leak.
title chrome_debug_9222

rem Имя профиля настраивается через env BOGI_CHROME_PROFILE. Если первый
rem аккаунт забанили — меняем имя (BogiAiChromeDebug2/3/...) и получаем
rem полностью чистый fingerprint без следов старого аккаунта. ASCII-путь
rem (без кириллицы) — иначе Chrome ругается на profile-lock.
if "%BOGI_CHROME_PROFILE%"=="" set BOGI_CHROME_PROFILE=BogiAiChromeDebug2
set PROFILE=%LOCALAPPDATA%\%BOGI_CHROME_PROFILE%
if not exist "%PROFILE%" mkdir "%PROFILE%"

rem Try standard Chrome install paths
set CHROME="C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist %CHROME% set CHROME="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not exist %CHROME% set CHROME="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

echo Launching Chrome with debug port 9222...
echo Profile: %PROFILE%
echo.
echo 1. Sign in to Google in the window that opens (first time only)
echo 2. Runners (video / imagefx) сами откроют нужный Flow-проект
echo 3. Оставь Chrome открытым
echo.
rem URL — нейтральный projects-listing, а не конкретный проект. Иначе
rem при каждом старте debug-Chrome открывал hardcoded проект Дедала, и
rem runner'ы сверху открывали вторую вкладку правильного мифа → пользователь
rem видел две Flow-вкладки. Сейчас всегда одна вкладка от runner'а.
start "" %CHROME% --remote-debugging-port=9222 --user-data-dir="%PROFILE%" "https://labs.google/fx/ru/tools/flow/"
