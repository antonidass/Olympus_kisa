@echo off
rem Открывает тот же профиль Chrome что и launch_chrome_debug.bat,
rem но БЕЗ --remote-debugging-port. Нужно для первичного логина в Google:
rem с debug-портом Google блокирует sign-in (анти-фишинг защита, видит CDP-
rem подключение и думает что это попытка украсть куки).
rem
rem Сценарий использования при заведении нового аккаунта:
rem   1. Двойной клик по login_chrome.bat
rem   2. Залогиниться в Google в открывшемся окне
rem   3. (опционально) открыть https://labs.google/fx/ru/tools/flow/
rem      и создать нужные Flow-проекты, скопировать flow_id
rem   4. ЗАКРЫТЬ это окно Chrome полностью
rem   5. Запустить launch_chrome_debug.bat для работы раннеров
rem      (куки сохранятся в профиле, повторный логин не нужен)
title chrome_login_no_debug

if "%BOGI_CHROME_PROFILE%"=="" set BOGI_CHROME_PROFILE=BogiAiChromeDebug2
set PROFILE=%LOCALAPPDATA%\%BOGI_CHROME_PROFILE%
if not exist "%PROFILE%" mkdir "%PROFILE%"

set CHROME="C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist %CHROME% set CHROME="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not exist %CHROME% set CHROME="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

echo Открываю Chrome БЕЗ debug-порта для логина в Google.
echo Profile: %PROFILE%
echo.
echo 1. Залогинься в Google
echo 2. (опционально) создай Flow-проект на labs.google/fx/ru/tools/flow/
echo 3. ЗАКРОЙ это окно Chrome полностью
echo 4. Запусти launch_chrome_debug.bat для работы раннеров
echo.
start "" %CHROME% --user-data-dir="%PROFILE%" "https://accounts.google.com/signin"
