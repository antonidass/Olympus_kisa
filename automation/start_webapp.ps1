# Запуск webapp на порту 5000.
# Если на 5000 уже что-то висит (старый webapp / зомби-процесс) — убивает.
# После старта открывает Chrome на http://localhost:5000/

$ErrorActionPreference = "Stop"
# Скрипт лежит в BOGI AI/automation/, project root — на уровень выше.
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Port = 5000
# IPv4 явно: на Win11 'localhost' резолвится сначала в ::1, и если Flask
# слушает только 127.0.0.1 — Invoke-WebRequest залипает на IPv6-таймауте.
$Url = "http://127.0.0.1:$Port/"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " BOGI AI — webapp launcher" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# 1) Найти и убить процесс, занимающий порт 5000.
Write-Host "[1/3] Проверяю порт $Port..." -ForegroundColor Yellow
$conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($conns) {
    foreach ($c in $conns) {
        $procId = $c.OwningProcess
        try {
            $proc = Get-Process -Id $procId -ErrorAction Stop
            Write-Host "      Убиваю старый процесс: PID=$procId  ($($proc.ProcessName))" -ForegroundColor DarkYellow
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host "      Не удалось остановить PID=$procId — пропускаю." -ForegroundColor Red
        }
    }
    Start-Sleep -Milliseconds 500
} else {
    Write-Host "      Порт $Port свободен." -ForegroundColor Green
}

# 2) Запуск webapp в фоне без окна (через pythonw.exe). PowerShell-родитель
#    может закрыться — webapp продолжит работать, т.к. процесс отвязан.
Write-Host ""
Write-Host "[2/3] Запускаю webapp в фоне на порту $Port..." -ForegroundColor Yellow

# Ищем python, в котором установлен Flask. Просто `Get-Command python` не годится:
# на Win11 первой идёт C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\python.exe
# — это App Execution Alias-stub из Microsoft Store. Stub не имеет flask и при
# любом аргументе тихо выходит с ExitCode=9009/0/2. Поэтому собираем кандидатов
# из стандартных мест, отбрасываем WindowsApps stub и проверяем каждого
# через `import flask`. Первый рабочий — наш.
$pyCandidates = New-Object System.Collections.Generic.List[string]
foreach ($cmd in (Get-Command python -All -ErrorAction SilentlyContinue)) {
    if ($cmd.Source -and $cmd.Source -notmatch '\\WindowsApps\\') {
        $pyCandidates.Add($cmd.Source) | Out-Null
    }
}
foreach ($p in @(
    'C:\ProgramData\anaconda3\python.exe',
    'C:\ProgramData\miniconda3\python.exe',
    "$env:USERPROFILE\anaconda3\python.exe",
    "$env:USERPROFILE\miniconda3\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    'C:\Python313\python.exe',
    'C:\Python312\python.exe',
    'C:\Python311\python.exe'
)) {
    if ((Test-Path $p) -and ($pyCandidates -notcontains $p)) {
        $pyCandidates.Add($p) | Out-Null
    }
}

$python = $null
foreach ($cand in $pyCandidates) {
    & $cand -c "import flask" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $python = $cand
        break
    }
}

if (-not $python) {
    Write-Host "      ОШИБКА: не нашёл python с установленным flask." -ForegroundColor Red
    Write-Host "      Проверял:" -ForegroundColor DarkYellow
    foreach ($c in $pyCandidates) { Write-Host "        $c" -ForegroundColor DarkGray }
    Write-Host "      Установи flask: <python> -m pip install flask" -ForegroundColor Yellow
    Read-Host "Нажми Enter чтобы выйти"
    exit 1
}
Write-Host "      Использую python: $python" -ForegroundColor DarkGray

$appPath = Join-Path $ProjectRoot "webapp\app.py"
if (-not (Test-Path $appPath)) {
    Write-Host "      ОШИБКА: не найден $appPath" -ForegroundColor Red
    Read-Host "Нажми Enter чтобы выйти"
    exit 1
}
# Запускаем python напрямую через Start-Process — без cmd-прослойки.
# Старый вариант (cmd /c start "title" "python" "app.py") молча падал на
# машинах с кириллицей в пути ($env:USERPROFILE = C:\Users\Антон\...): cmd
# токенизирует аргументы в текущей ANSI-кодовой странице, и путь до app.py
# приходил битым — python тихо завершался, окно было WindowStyle=Hidden,
# юзер видел только Chrome без webapp.
#
# Start-Process передаёт args в CreateProcessW как UTF-16, поэтому кириллица
# в путях доходит корректно. Для python.exe (консольное приложение) Windows
# сам выделит видимое окно консоли. PYTHONIOENCODING форсит UTF-8 на stdout/stderr,
# чтобы логи Flask не превращались в кракозябры (видели "C:\Users\?????\..." в выводе).
# Если рядом с найденным python есть pythonw.exe — запускаем через него,
# чтобы НЕ открывалось окно консоли вообще. pythonw.exe = тот же интерпретатор,
# но без аллокации консоли (stdout/stderr идут в NUL). Webapp работает в фоне,
# и его не нужно держать открытым — если не отвечает, юзер запустит вручную
# `python webapp/app.py` и увидит traceback.
$pythonw = Join-Path (Split-Path -Parent $python) 'pythonw.exe'
$launchExe = if (Test-Path $pythonw) { $pythonw } else { $python }

$prevEnc = $env:PYTHONIOENCODING
$env:PYTHONIOENCODING = 'utf-8'
try {
    # Цитируем путь явно: в "BOGI AI" пробел, без кавычек python получит
    # два аргумента ("BOGI" и "AI\webapp\app.py") и упадёт с ExitCode=2.
    # WindowStyle Hidden — страховка, если используется python.exe без pythonw.
    Start-Process -FilePath $launchExe -ArgumentList ('"' + $appPath + '"') `
                  -WorkingDirectory $ProjectRoot -WindowStyle Hidden
} finally {
    $env:PYTHONIOENCODING = $prevEnc
}
Write-Host "      webapp стартует в фоне (без окна консоли)." -ForegroundColor Green

# 3) Ждём через быстрый TCP-чек (по IPv4). HTTP-поллер на Win11 капризный:
#    Invoke-WebRequest с 'localhost' иногда залипает на IPv6 ::1 даже с таймаутом.
Write-Host ""
Write-Host "[3/3] Жду пока порт $Port начнёт слушать и открываю Chrome..." -ForegroundColor Yellow
$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 250
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $iar = $tcp.BeginConnect("127.0.0.1", $Port, $null, $null)
        $ok = $iar.AsyncWaitHandle.WaitOne(200, $false)
        if ($ok -and $tcp.Connected) { $tcp.EndConnect($iar); $tcp.Close(); $ready = $true; break }
        $tcp.Close()
    } catch {
        # порт ещё не слушает
    }
}

if (-not $ready) {
    Write-Host "      WARNING: порт не отвечает за 10 сек, всё равно открываю Chrome." -ForegroundColor DarkYellow
} else {
    Write-Host "      OK: webapp слушает на :$Port" -ForegroundColor Green
}

# Ищем chrome в стандартных местах.
$chromeCandidates = @(
    "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "${env:LOCALAPPDATA}\Google\Chrome\Application\chrome.exe"
)
$chrome = $chromeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($chrome) {
    Start-Process -FilePath $chrome -ArgumentList $Url
    Write-Host "      Chrome открыт: $Url" -ForegroundColor Green
} else {
    Write-Host "      Chrome не найден — открываю в браузере по умолчанию." -ForegroundColor DarkYellow
    Start-Process $Url
}

Write-Host ""
Write-Host "Готово. Webapp работает в фоне — это окно можно закрывать." -ForegroundColor Green
Write-Host "Чтобы остановить: запусти этот скрипт ещё раз (он убьёт старый процесс)" -ForegroundColor DarkGray
Write-Host "или останови процесс pythonw.exe в Диспетчере задач." -ForegroundColor DarkGray
Write-Host ""
