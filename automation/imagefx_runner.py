"""
Flow Runner — автоматизация генерации изображений в Google Flow (Nano Banana).

Читает markdown-файл со сценами, цепляется по CDP к уже запущенному Chrome
пользователя (тому, в котором открыт Flow-проект), по очереди вставляет
промпты, ждёт генерации и скачивает картинки через перехват сетевых ответов.

Предварительный шаг — пользователь запускает `automation/launch_chrome_debug.bat`
и логинится в Google в открывшемся окне. Скрипт НЕ запускает Chrome сам —
Playwright-запущенный браузер Google отлавливает как automation. CDP-attach
к обычному user-launched Chrome даёт чистейший fingerprint: navigator.webdriver
равен false, нет --enable-automation, и вся работа идёт внутри настоящей
Google-сессии пользователя.

Использование:
    python automation/imagefx_runner.py content/<миф>/prompts/images.md
    python automation/imagefx_runner.py <md> --scenes 1,2,3
    python automation/imagefx_runner.py <md> --from 3

Шаги workflow:
    1. Запусти automation/launch_chrome_debug.bat — откроется Chrome с портом 9222
    2. В этом Chrome залогинься в Google и открой Flow-проект нужного мифа
    3. Оставь окно Chrome открытым
    4. Запусти этот скрипт (или кнопку «Сгенерировать все картинки» в webapp)

Если Google всё равно блокирует:
    - Подожди 15-30 минут
    - Запускай батчами по 2-3 сцены: --scenes 1,2,3 ... --scenes 4,5,6
"""

from __future__ import annotations

import argparse
import builtins
import os
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from flow_projects import resolve_flow_url

# Переопределяем print так, чтобы каждое сообщение в консоли начиналось с [ЧЧ:ММ].
# Многострочные сообщения получают префикс только на первой строке — остальные
# строки выравниваются пробелами, чтобы читалось как блок.
_original_print = builtins.print


def print(*args, **kwargs):  # type: ignore[override]
    stamp = datetime.now().strftime("[%H:%M]")
    sep = kwargs.get("sep", " ")
    msg = sep.join(str(a) for a in args)
    if msg == "":
        _original_print(stamp, **kwargs)
        return
    lines = msg.split("\n")
    pad = " " * (len(stamp) + 1)
    lines[0] = f"{stamp} {lines[0]}"
    for i in range(1, len(lines)):
        lines[i] = pad + lines[i]
    kwargs.pop("sep", None)
    _original_print("\n".join(lines), **kwargs)

PROFILE_DIR = Path(__file__).parent / ".browser_profile"
CONTENT_ROOT = Path(__file__).parent.parent / "content"

# Служебные/известные папки, которые точно не являются именем сценария
_NON_SCENARIO_FOLDERS = {
    "prompts", "video", "images", "voiceover", "music", "final",
    "content", "automation", "scripts", "output",
}


def resolve_scenario_folder(markdown_path: Path) -> str:
    """Имя папки сценария по пути к markdown-файлу (сохраняем оригинальный регистр).

    Пример: scripts/икар_и_дедал/images.md → 'икар_и_дедал'.
    """
    for parent in markdown_path.resolve().parents:
        name = parent.name
        if not name:
            continue
        if name.lower() in _NON_SCENARIO_FOLDERS:
            continue
        return name
    raise ValueError(f"Не удалось определить имя сценария из пути: {markdown_path}")

PAGE_LOAD_TIMEOUT = 60_000
GENERATION_TIMEOUT = 300  # сек — на всякий случай побольше
STABLE_WAIT_SEC = 10       # сколько ждать стабилизации после появления картинки

PROMPT_SELECTOR = '[contenteditable="true"][role="textbox"]'
GENERATE_BUTTON_SELECTOR = 'button:has-text("arrow_forward"):has-text("Создать")'

# Паттерны URL сгенерированных картинок. Flow в конце 2025 перешёл на
# свой CDN flow-content.google — без этого паттерна сетевой listener
# отклонял ВСЕ ответы генерации как «не картинки Flow» и сохранить не получалось.
IMAGE_URL_PATTERNS = [
    "flow-content.google",
    "googleusercontent.com",
    "lh3.google",
    "lh4.google",
    "lh5.google",
    "lh6.google",
    "storage.googleapis.com",
    "aistudio.google.com",
    "labs.google",
]

# Минимальный размер файла.
# Flow отдаёт размытые PNG-плейсхолдеры ~100 КБ перед финальными картинками (~600-800 КБ).
# 300 КБ — безопасный порог, чтобы отсечь плейсхолдеры но не обрезать настоящие картинки.
MIN_IMAGE_BYTES = 300_000

# CDP-attach: подключаемся к user-launched Chrome, запущенному через
# automation/launch_chrome_debug.bat (порт 9222). Не запускаем свой браузер —
# это главный слой анти-детекта: Google видит обычную Google-сессию без
# следов Playwright/automation.
CDP_URL = "http://127.0.0.1:9222"
CDP_HOST = "127.0.0.1"
CDP_PORT = 9222
LAUNCH_CHROME_BAT = Path(__file__).parent / "launch_chrome_debug.bat"

# Профиль debug-Chrome — должен совпадать с PROFILE в launch_chrome_debug.bat.
# Чистится перед каждым запуском (если включён --clean-session), чтобы Flow
# видел свежую сессию. Имя профиля настраивается env BOGI_CHROME_PROFILE —
# при бане аккаунта меняем имя (BogiAiChromeDebug2/3/...) для чистого
# fingerprint без следов старого аккаунта.
CHROME_DEBUG_PROFILE = Path(os.environ.get("LOCALAPPDATA", "")) / os.environ.get(
    "BOGI_CHROME_PROFILE", "BogiAiChromeDebug2"
)


def _cdp_reachable(timeout_sec: float = 1.5) -> bool:
    """Быстрая проверка: слушает ли кто-то CDP-порт 9222."""
    import socket  # noqa: PLC0415
    try:
        sock = socket.create_connection((CDP_HOST, CDP_PORT), timeout=timeout_sec)
        sock.close()
        return True
    except Exception:
        return False


def kill_debug_chrome(wait_sec: int = 12) -> bool:
    """Закрывает ТОЛЬКО Chrome, запущенный с --remote-debugging-port=9222.

    Не трогает остальные окна Chrome пользователя — фильтр идёт по точной
    подстроке в командной строке процесса. После убийства ждёт пока порт
    9222 освободится (иначе ensure_debug_chrome решит, что Chrome ещё жив).
    """
    if not _cdp_reachable():
        return True  # уже мёртв — чисто

    if sys.platform != "win32":
        print("  ⚠ kill_debug_chrome поддерживает только Windows")
        return False

    print(f"  🪦 Закрываю Chrome с debug-портом {CDP_PORT}…")
    ps_cmd = (
        "Get-CimInstance Win32_Process -Filter \"Name = 'chrome.exe'\" "
        "| Where-Object { $_.CommandLine -like '*remote-debugging-port=" + str(CDP_PORT) + "*' } "
        "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, timeout=20,
        )
    except Exception as e:
        print(f"  ⚠ powershell завершился ошибкой: {e}")

    # Ждём освобождения порта
    for _ in range(wait_sec * 2):
        if not _cdp_reachable():
            return True
        time.sleep(0.5)
    print(f"  ⚠ Порт {CDP_PORT} ещё отвечает спустя {wait_sec}с — Chrome не закрылся")
    return False


def clean_flow_session() -> None:
    """Чистит google-куки и storage в debug-профиле перед каждым запуском.

    Зачем: Google Flow по сумме (cookies + LocalStorage + IndexedDB +
    Cache + ServiceWorker) выставляет «trust score» сессии. Когда score
    падает — выскакивает «We noticed unusual activity», и дальше идти
    бесполезно. Полная чистка между прогонами возвращает фингерпринт в
    «как первый заход с этого устройства» состояние.

    Что делает:
      1. Закрывает Chrome 9222 (если запущен) — иначе файлы залочены.
      2. Удаляет из Network/Cookies все строки с google-доменами.
      3. Сносит Local Storage / Session Storage / Cache / Code Cache /
         GPUCache / Service Worker — целиком (профиль используется только
         для labs.google, ничего ценного там нет).
      4. Удаляет IndexedDB-папки labs.google.

    Не трогает: bookmarks, расширения, fingerprint железа, Login Data,
    Preferences. Только сессионное состояние Google.
    """
    profile = CHROME_DEBUG_PROFILE
    if not profile.exists():
        # Первый запуск — чистить нечего, ensure_debug_chrome создаст профиль.
        return

    print("\n🧹 Чищу профиль Chrome перед запуском (cookies + storage + cache)…")

    # 1. Закрыть Chrome — иначе SQLite/LevelDB файлы залочены
    if not kill_debug_chrome():
        print("  ⚠ Продолжаю несмотря на не-закрытый Chrome — чистка может частично провалиться")

    default = profile / "Default"

    # 2. Cookies (SQLite в новой раскладке Chrome — Default/Network/Cookies)
    cookies = default / "Network" / "Cookies"
    if cookies.exists():
        try:
            db = sqlite3.connect(str(cookies))
            cur = db.cursor()
            cur.execute(
                "DELETE FROM cookies WHERE host_key LIKE '%google%' "
                "OR host_key LIKE '%.google.%' OR host_key LIKE '%gstatic%' "
                "OR host_key LIKE '%youtube%'"
            )
            removed = cur.rowcount
            db.commit()
            db.close()
            print(f"  🍪 Удалено google-куков: {removed}")
        except Exception as e:
            print(f"  ⚠ Cookies: {e}")

    # 3. Storage и кеш — рекурсивные удаления (Chrome пересоздаст пустые)
    storage_targets = [
        ("Local Storage",   default / "Local Storage"),
        ("Session Storage", default / "Session Storage"),
        ("Cache",           default / "Cache"),
        ("Code Cache",      default / "Code Cache"),
        ("GPUCache",        default / "GPUCache"),
        ("Service Worker",  default / "Service Worker"),
    ]
    for label, path in storage_targets:
        if path.exists():
            try:
                shutil.rmtree(path)
                print(f"  🧹 {label}: снесено")
            except Exception as e:
                print(f"  ⚠ {label}: {e}")

    # 4. IndexedDB — только labs.google (остальные сайты не трогаем,
    # их там и так не должно быть в этом профиле, но подстрахуемся)
    idb = default / "IndexedDB"
    if idb.exists():
        for sub in idb.iterdir():
            if sub.is_dir() and "labs.google" in sub.name.lower():
                try:
                    shutil.rmtree(sub)
                    print(f"  🧹 IndexedDB/{sub.name}: снесено")
                except Exception as e:
                    print(f"  ⚠ IndexedDB/{sub.name}: {e}")

    print("✓ Профиль очищен — нужно будет залогиниться в Google заново\n")


def ensure_debug_chrome(max_wait_sec: int = 60) -> bool:
    """Убеждается, что debug-Chrome запущен. Если нет — поднимает .bat и ждёт.

    Возвращает True если порт CDP стал отвечать (Chrome готов), False если
    за отведённое время не стартанул.
    """
    if _cdp_reachable():
        print(f"✓ Chrome с debug-портом {CDP_PORT} уже запущен")
        return True

    if not LAUNCH_CHROME_BAT.exists():
        print(f"❌ Не найден {LAUNCH_CHROME_BAT}")
        return False

    print(f"🚀 Chrome-debug не запущен — поднимаю {LAUNCH_CHROME_BAT.name}")
    # CREATE_NEW_CONSOLE — Chrome получает свою консоль, наш cmd не блокируется.
    # Bat запускает Chrome через `start ""` — это сам по себе детач, т.е.
    # subprocess завершится сразу, а Chrome продолжит жить независимо.
    flags = subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, "CREATE_NEW_CONSOLE") else 0
    try:
        subprocess.Popen(
            [str(LAUNCH_CHROME_BAT)],
            cwd=str(LAUNCH_CHROME_BAT.parent),
            creationflags=flags,
        )
    except Exception as e:
        print(f"❌ Не удалось запустить bat: {e}")
        return False

    print(f"⏳ Жду открытия порта {CDP_PORT} (до {max_wait_sec} сек)…")
    for i in range(max_wait_sec):
        if _cdp_reachable():
            print(f"✓ CDP-порт ответил через {i+1}с")
            time.sleep(2)  # ещё 2 сек — дать Chrome докрутить UI
            return True
        time.sleep(1)

    print(f"❌ За {max_wait_sec}с Chrome не открыл CDP-порт")
    return False


def open_flow_tab(browser, flow_url: str):
    """Открывает (или переиспользует) вкладку с нужным Flow-проектом.

    1. Если есть вкладка с labs.google/fx/tools/flow/ (listing projects или
       другой проект) — НАВИГИРУЕМ её на flow_url вместо создания новой.
       Так пользователь не получает две Flow-вкладки (listing от bat +
       project от runner).
    2. Если вообще никакой Flow-вкладки нет — создаём новую.
    """
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()

    reuse_candidate = None
    for pg in ctx.pages:
        try:
            if pg.is_closed():
                continue
            if "labs.google" in pg.url and "/flow" in pg.url:
                reuse_candidate = pg
                break
        except Exception:
            continue

    if reuse_candidate is not None:
        page = reuse_candidate
        print(f"  ↻ Переиспользую существующую Flow-вкладку: {page.url[:60]}…")
        try:
            page.goto(flow_url, timeout=60_000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"  ⚠ Не получилось навигировать ({e}) — открываю новую вкладку")
            page = ctx.new_page()
            page.goto(flow_url, timeout=60_000, wait_until="domcontentloaded")
    else:
        page = ctx.new_page()
        page.goto(flow_url, timeout=60_000, wait_until="domcontentloaded")

    page.bring_to_front()
    return page


def _flow_project_id_from_url(url: str) -> "str | None":
    """Извлекает flow_id из URL вкладки. Нужно чтобы не перепутать проекты —
    bat открывает Chrome на hardcoded URL Дедала, а сцены мы генерим для
    другого мифа. Без сравнения ID скрипт работал бы на чужом проекте.
    """
    m = re.search(r"/flow/project/([0-9a-f-]{8,})", url)
    return m.group(1) if m else None


def find_flow_page(context, target_project_id: "str | None" = None) -> "Page | None":
    """Находит открытую вкладку Flow.

    Если target_project_id задан — ТОЛЬКО точное совпадение. Иначе любая
    вкладка с flow/project. В режиме target=None используется для initial
    attach, когда мы ещё не знаем какой проект нужен.
    """
    for pg in context.pages:
        try:
            if pg.is_closed():
                continue
            page_pid = _flow_project_id_from_url(pg.url)
            if target_project_id:
                if page_pid == target_project_id:
                    return pg
            else:
                if "flow/project" in pg.url:
                    return pg
        except Exception:
            continue
    return None


def attach_and_find(p, target_project_id: "str | None" = None, verbose: bool = True):
    """Подключается к Chrome по CDP и ищет вкладку Flow.

    Возвращает (browser, page).
      - (None, None)     — CDP недоступен
      - (browser, None)  — Chrome запущен, но нужной вкладки нет
      - (browser, page)  — всё нашли

    target_project_id: конкретный flow_id, которого мы ищем. Без этого
    параметра можно наткнуться на чужой проект (например, Дедала из bat).
    """
    try:
        browser = p.chromium.connect_over_cdp(CDP_URL, timeout=5_000)
    except Exception as e:
        if verbose:
            print(f"  ⚠ Не подключиться к Chrome на {CDP_URL}: {e}")
        return None, None

    if not browser.contexts:
        if verbose:
            print("  ⚠ В Chrome нет открытых контекстов")
        return browser, None

    for ctx in browser.contexts:
        pg = find_flow_page(ctx, target_project_id=target_project_id)
        if pg is not None:
            return browser, pg

    if verbose:
        if target_project_id:
            print(f"  ⚠ Не нашёл вкладку проекта {target_project_id[:8]}… ни в одном контексте")
        else:
            print("  ⚠ Не нашёл вкладку Flow ни в одном контексте")
    return browser, None


def ensure_page_alive(p, page, target_project_id: "str | None" = None):
    """Проверяет что вкладка Flow жива, при необходимости переподключается.

    target_project_id: тот же flow_id, что мы использовали в initial attach.
    Передача обязательна, чтобы reconnect не уехал на чужую flow-вкладку
    после срыва связи.
    """
    if page is not None:
        try:
            if not page.is_closed():
                page.evaluate("() => 1")
                return page
        except Exception:
            pass
    print("  🔄 Вкладка Flow потеряна, переподключаюсь через CDP...")
    _, new_page = attach_and_find(p, target_project_id=target_project_id, verbose=False)
    if new_page is not None:
        new_page.bring_to_front()
        print(f"  ✓ Переподключился: {new_page.url[:80]}...")
        return new_page
    print("\n  ❌ Flow-проект закрыт. Открой его в Chrome и жми Enter.")
    input("     ")
    _, new_page = attach_and_find(p, target_project_id=target_project_id)
    if new_page is not None:
        new_page.bring_to_front()
        return new_page
    return None


@dataclass
class Scene:
    index: int
    text: str
    prompt: str


def parse_markdown(path: Path) -> tuple[str, list[Scene]]:
    content = path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if not title_match:
        raise ValueError(f"Не найден заголовок `# Название` в {path}")
    title = title_match.group(1).strip()

    # Допускаем хвост после номера — например, «## Сцена 1 (sent_001)».
    scene_blocks = re.split(r"^##\s+Сцена\s+\d+[^\n]*$", content, flags=re.MULTILINE)[1:]
    if not scene_blocks:
        raise ValueError(f"Не найдено ни одной `## Сцена N` в {path}")

    scenes: list[Scene] = []
    for i, block in enumerate(scene_blocks, start=1):
        text_match = re.search(r"\*\*Текст:\*\*\s*(.+?)(?=\n\n|\*\*Промпт:\*\*)", block, re.DOTALL)
        prompt_match = re.search(r"\*\*Промпт:\*\*\s*(.+?)(?=\n##|\Z)", block, re.DOTALL)
        if not prompt_match:
            print(f"⚠ Сцена {i}: не найден промпт, пропускаю")
            continue
        scenes.append(
            Scene(
                index=i,
                text=(text_match.group(1).strip() if text_match else ""),
                prompt=prompt_match.group(1).strip(),
            )
        )
    return title, scenes


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s]+", "_", text)
    return text or "untitled"


def human_sleep(min_s: float, max_s: float):
    time.sleep(random.uniform(min_s, max_s))


def human_type_prompt(page: Page, text: str):
    """Быстрая посимвольная печать с лёгкой рандомизацией ритма.

    Google Flow палит clipboard-paste (Ctrl+V) как bot-сигнал, поэтому
    paste отброшен. Опечатки + Backspace, «персонаж сессии» и
    «усталость» убраны — на abuse-детектор Flow они не повлияли.

    Базовый темп ~25-65 симв/сек (быстрый, но не моментальный). Редкие
    короткие паузы на пунктуации остаются — без них вообще линия,
    поэтому смысла их убирать нет, времени почти не отъедают.
    """
    for ch in text:
        page.keyboard.type(ch)
        # Короткая пауза после знака препинания — встречается редко в
        # промптах, общую длительность почти не двигает.
        if ch in ".,;!?" and random.random() < 0.5:
            time.sleep(random.uniform(0.05, 0.18))
            continue
        # Базовый ритм 0.015-0.040 сек/симв (~25-65 симв/сек)
        time.sleep(random.uniform(0.015, 0.040))


def random_mouse_wander(page: Page, intensity: str = "normal"):
    """Праздные движения мыши. Три уровня интенсивности:

      'light'  — 1-2 быстрых жеста (между кликами)
      'normal' — 2-4 движения (по умолчанию)
      'heavy'  — 4-8 движений с долгими паузами (во время ожидания)
    """
    if intensity == "light":
        moves = random.randint(1, 2)
        pause = (0.08, 0.22)
    elif intensity == "heavy":
        moves = random.randint(4, 8)
        pause = (0.4, 1.1)
    else:
        moves = random.randint(2, 4)
        pause = (0.15, 0.45)
    for _ in range(moves):
        x = random.randint(200, 1200)
        y = random.randint(200, 700)
        try:
            page.mouse.move(x, y, steps=random.randint(15, 35))
        except Exception:
            return
        time.sleep(random.uniform(*pause))


def idle_like_human(page: Page, seconds: float):
    """Ждём `seconds` секунд, периодически шевеля мышью — «смотрим в экран,
    иногда двигаем курсор». Используется во время ожидания генерации
    вместо голого time.sleep (голое бездействие тоже bot-сигнал).
    """
    elapsed = 0.0
    while elapsed < seconds:
        chunk = random.uniform(3.5, 9.0)
        if elapsed + chunk > seconds:
            chunk = seconds - elapsed
        time.sleep(chunk)
        elapsed += chunk
        if random.random() < 0.6 and elapsed < seconds - 0.5:
            random_mouse_wander(page, intensity=random.choice(["light", "normal"]))
            elapsed += random.uniform(0.5, 1.5)


# ── Обнаружение блокировки Flow («подозрительная активность») ──────────────

def detect_abuse_dialog(page: Page) -> bool:
    """Ищет в DOM признаки предупреждения «We noticed some unusual activity»."""
    try:
        return bool(page.evaluate(
            """
            () => {
                const text = (document.body.innerText || '').toLowerCase();
                return text.includes('unusual activity')
                    || text.includes('подозрительн')
                    || (text.includes('помощи') && text.includes('help center'))
                    || text.includes('we noticed some');
            }
            """
        ))
    except Exception:
        return False


def pause_for_abuse_resolution(context: str = ""):
    """Останавливает скрипт, ждёт пока пользователь разблокирует Flow."""
    print("\n" + "🚨" * 30)
    print(f"  Flow показал «подозрительная активность»{' (' + context + ')' if context else ''}.")
    print("  1) В окне Chrome — пройди все шаги (restore / continue / подожди).")
    print("  2) Когда Flow снова работает — нажми Enter для продолжения.")
    print("🚨" * 30)
    input("\n     Жду разблокировки → Enter... ")
    time.sleep(random.uniform(2, 4))


# ── Детект rate-limit тоста («Вы слишком быстро отправляете запросы») ──────
#
# Это другой сигнал, чем abuse-диалог: тост появляется на 5-7 сек в
# нижнем-левом углу и сам исчезает. Если его не поймать — раннер
# простоит весь GENERATION_TIMEOUT впустую, а сцена окажется без картинок.

RATE_LIMIT_MARKERS = [
    "слишком быстро",
    "повторите попытку через",
    "too many requests",
    "try again in a few",
    "rate limit",
]


def detect_rate_limit_toast(page: Page) -> bool:
    """Ищет в DOM транзиентный тост «слишком быстро отправляете»."""
    try:
        return bool(page.evaluate(
            """
            (markers) => {
                const text = (document.body.innerText || '').toLowerCase();
                return markers.some(m => text.includes(m));
            }
            """,
            RATE_LIMIT_MARKERS,
        ))
    except Exception:
        return False


def click_generate_with_rate_limit_retry(page: Page, state: dict, max_retries: int = 3) -> bool:
    """Кликает «Создать» с авто-retry при rate-limit тосте.

    Алгоритм:
      1. click_generate → ждём 2 сек, проверяем тост
      2. Если тост есть — фиксируем rate_limit_count, ждём 60-120 сек × attempt
         (прогрессивный backoff), проверяем что тост ушёл, повторяем клик
      3. После max_retries возвращаем False — вызывающий пропускает сцену

    Returns:
        True если генерация запустилась чисто, False если retry исчерпан.
    """
    for attempt in range(1, max_retries + 1):
        click_generate(page)
        # Тост появляется в течение 1-2 сек после клика
        time.sleep(2.0)
        if not detect_rate_limit_toast(page):
            return True

        state["rate_limit_count"] = state.get("rate_limit_count", 0) + 1
        if attempt >= max_retries:
            print(f"  ⚠ Rate-limit не ушёл после {max_retries} попыток — пропускаю сцену.")
            return False

        # Прогрессивный backoff: 60-120, 120-240, 180-360 сек
        cooldown = random.uniform(60, 120) * attempt
        print(f"  ⏳ Rate-limit (попытка {attempt}/{max_retries}): пауза {int(cooldown)} сек перед retry…")
        deadline = time.time() + cooldown
        # В процессе ожидания периодически проверяем что тост уже исчез —
        # без этого следующий клик может попасть на ещё видимый тост.
        while time.time() < deadline:
            time.sleep(min(5.0, deadline - time.time()))
        # Финальная проверка перед retry
        for _ in range(15):
            if not detect_rate_limit_toast(page):
                break
            time.sleep(2.0)
    return False


def human_click(page: Page, locator, *, padding: float = 0.2):
    """Кликает по элементу с человекоподобной траекторией мыши.

    Стандартный locator.click() бьёт ровно в boundingBox.center — это
    bot-сигнал, у людей попадание гуляет внутри элемента. Здесь:
      1. Берём bounding_box, выбираем случайную точку в центральной
         части (padding от краёв), чтобы не промахнуться по элементу
      2. Двигаем мышь к этой точке через серию шагов
      3. Кликаем по координатам, а не по селектору

    padding — доля от ширины/высоты с каждого края, в которую НЕ целимся
    (по умолчанию 20%, попадаем в центральные 60%).
    """
    box = locator.bounding_box()
    if not box or box["width"] < 4 or box["height"] < 4:
        # Деградируем до обычного клика — лучше так, чем падать
        locator.click()
        return
    x_lo = box["x"] + box["width"] * padding
    x_hi = box["x"] + box["width"] * (1.0 - padding)
    y_lo = box["y"] + box["height"] * padding
    y_hi = box["y"] + box["height"] * (1.0 - padding)
    target_x = random.uniform(x_lo, x_hi)
    target_y = random.uniform(y_lo, y_hi)
    try:
        page.mouse.move(target_x, target_y, steps=random.randint(20, 40))
    except Exception:
        pass
    time.sleep(random.uniform(0.08, 0.22))
    page.mouse.click(target_x, target_y)


def _clear_prompt_field(page: Page):
    """Очистка поля одним из трёх способов — варьируем, чтобы не было
    одинаковой Ctrl+A → Delete каждый раз. Реальные люди очищают
    по-разному."""
    method = random.choice(["select_all", "end_shift_home", "ctrl_backspace"])
    if method == "select_all":
        page.keyboard.press("Control+A")
        time.sleep(random.uniform(0.20, 0.45))
        page.keyboard.press(random.choice(["Delete", "Backspace"]))
    elif method == "end_shift_home":
        page.keyboard.press("End")
        time.sleep(random.uniform(0.10, 0.25))
        page.keyboard.press("Shift+Home")
        time.sleep(random.uniform(0.18, 0.40))
        page.keyboard.press("Backspace")
    else:  # ctrl_backspace — несколько раз стираем по слову
        for _ in range(random.randint(8, 14)):
            page.keyboard.press("Control+Backspace")
            time.sleep(random.uniform(0.04, 0.12))
        page.keyboard.press("Control+A")
        time.sleep(random.uniform(0.10, 0.20))
        page.keyboard.press("Delete")
    time.sleep(random.uniform(0.4, 0.8))


def fill_prompt(page: Page, prompt: str):
    """Живой ввод промпта — тот же паттерн, что в video_runner.

    Заменил старый clipboard-paste на посимвольную печать: paste через
    буфер — один из явных bot-сигналов Google. Медленнее (30-90 сек на
    промпт), но без блокировок.
    """
    field = page.locator(PROMPT_SELECTOR).first
    field.wait_for(state="visible", timeout=10_000)

    random_mouse_wander(page, intensity="light")
    human_click(page, field)
    time.sleep(random.uniform(0.6, 1.3))

    _clear_prompt_field(page)

    print(f"  ⌨  Печатаю промпт ({len(prompt)} симв.)...")
    human_type_prompt(page, prompt)

    # Короткая пауза «перед отправкой — ещё раз взглянул»
    time.sleep(random.uniform(1.5, 3.5))


def click_generate(page: Page):
    btn = page.locator(GENERATE_BUTTON_SELECTOR).first
    btn.wait_for(state="visible", timeout=5_000)
    for _ in range(10):
        if btn.is_enabled():
            break
        time.sleep(0.3)
    # Перед кликом — лёгкое движение мыши и пауза «на подумать»
    random_mouse_wander(page, intensity="normal")
    time.sleep(random.uniform(0.6, 1.4))
    human_click(page, btn)


def look_at_results(page: Page):
    """После генерации — «посмотреть на результат»: скролл вниз, пауза,
    лёгкое движение мыши над галереей, скролл назад. Боты сразу пишут
    следующий промпт; люди разглядывают то, что получилось."""
    try:
        page.mouse.wheel(0, random.randint(180, 420))
    except Exception:
        return
    time.sleep(random.uniform(2.0, 4.5))
    random_mouse_wander(page, intensity="normal")
    try:
        page.mouse.wheel(0, -random.randint(120, 320))
    except Exception:
        pass
    time.sleep(random.uniform(1.5, 3.5))


def snapshot_existing_img_urls(page: Page) -> set[str]:
    """Возвращает set всех img src, которые сейчас присутствуют на странице."""
    try:
        return set(
            page.evaluate(
                """() => Array.from(document.querySelectorAll('img'))
                    .map(e => e.src).filter(s => s && s.length > 0)"""
            )
        )
    except Exception:
        return set()


def generate_scene(page: Page, scene: Scene, output_dir: Path, captured: list[dict], state: dict):
    print(f"\n→ Сцена {scene.index}: {scene.prompt[:70]}...")

    # Детект блокировки ДО ввода промпта — если Flow уже показывает
    # «unusual activity», не фигачим сотню символов зря.
    if detect_abuse_dialog(page):
        pause_for_abuse_resolution(f"сцена {scene.index}: перед вводом промпта")

    # Заранее заполняем поле промпта (пока принимать картинки нельзя)
    state["accepting"] = False
    captured.clear()
    fill_prompt(page, scene.prompt)

    # Снимок URL всех картинок, которые уже есть на странице до клика
    existing = snapshot_existing_img_urls(page)
    print(f"  📋 До клика в DOM было {len(existing)} img")
    state["existing_urls"] = existing
    state["accepting"] = True  # теперь listener принимает новые

    # Кликаем «Создать» с автоматическим retry при rate-limit тосте
    # («Вы слишком быстро отправляете запросы»). Если все попытки
    # исчерпаны — пропускаем сцену, чтобы не висеть в GENERATION_TIMEOUT.
    if not click_generate_with_rate_limit_retry(page, state):
        state["accepting"] = False
        return

    # Детект блокировки СРАЗУ после клика — Flow иногда показывает
    # абьюз-диалог вместо генерации. Если поймали — ждём решения юзера
    # и идём на следующую сцену (текущую считаем провалом).
    time.sleep(1.5)  # дать странице отрисовать диалог если он есть
    if detect_abuse_dialog(page):
        # Считаем хиты — после первого все паузы в главном цикле умножаются.
        state["abuse_count"] = state.get("abuse_count", 0) + 1
        pause_for_abuse_resolution(f"сцена {scene.index}: после клика «Создать»")
        return

    print(f"  ⏳ Жду генерации (до {GENERATION_TIMEOUT} сек)...")

    # Ждём пока в captured ИЛИ в DOM появятся новые картинки,
    # затем даём им STABLE_WAIT_SEC сек на догрузку всех вариантов.
    deadline = time.time() + GENERATION_TIMEOUT
    last_total = 0
    stable_since = None
    existing = state.get("existing_urls", set())
    while time.time() < deadline:
        # Сколько новых больших img появилось в DOM
        try:
            dom_new = page.evaluate(
                """(existingList) => {
                    const exist = new Set(existingList);
                    return Array.from(document.querySelectorAll('img')).filter(el => {
                        if (!el.src || exist.has(el.src)) return false;
                        const r = el.getBoundingClientRect();
                        return r.width >= 200 && r.height >= 200;
                    }).length;
                }""",
                list(existing),
            )
        except Exception:
            dom_new = 0

        total_new = max(len(captured), dom_new)
        if total_new > 0:
            if total_new == last_total:
                if stable_since and (time.time() - stable_since) > STABLE_WAIT_SEC:
                    print(f"  ✓ Обнаружено {total_new} новых (captured={len(captured)}, dom={dom_new}), стабильно.")
                    break
                if stable_since is None:
                    stable_since = time.time()
                    print(f"  📸 Появились картинки (captured={len(captured)}, dom={dom_new}), жду стабилизации {STABLE_WAIT_SEC} сек...")
            else:
                last_total = total_new
                stable_since = None
        time.sleep(2)

    # Доп. проход: Flow часто отдаёт через сеть только 1 полноразмерный вариант
    # (тот, что в фокусе), а остальные 3 висят в DOM как превью <200px и не
    # загружаются браузером, пока на них не кликнут. Достаём их URL из DOM
    # (включая background-image) и подтягиваем через fetch() в контексте страницы.
    supplement_from_dom(page, captured, state.get("existing_urls", set()))

    if not captured:
        print("  ⚠ И сеть, и DOM пусты. Сохраняю скриншот для диагностики.")
        shot = output_dir / f"scene_{scene.index:02d}_fallback.png"
        page.screenshot(path=str(shot), full_page=True)
        print(f"  📸 Скриншот: {shot.name}")
        return

    print(f"  📥 Сохраняю {len(captured)} картинок...")
    scene_dir = output_dir / f"scene_{scene.index:02d}"
    scene_dir.mkdir(parents=True, exist_ok=True)
    for variant_i, item in enumerate(captured, start=1):
        ext = item["ext"]
        out_path = scene_dir / f"v{variant_i}.{ext}"
        try:
            out_path.write_bytes(item["body"])
            print(f"    ✓ {scene_dir.name}/{out_path.name}  ({len(item['body'])//1024} КБ)")
        except Exception as e:
            print(f"    ✗ {scene_dir.name}/{out_path.name}: {e}")


def supplement_from_dom(page: Page, captured: list[dict], existing_urls: set[str]) -> None:
    """Дотягивает варианты, которые Flow оставил лениво-загружаемыми.

    Сканирует:
      1. Все <img> (без фильтра размера) с URL из IMAGE_URL_PATTERNS
      2. background-image у всех элементов (Flow иногда рисует превью как bg)

    URL, которых не было в DOM до клика «Создать» и которых ещё нет в captured,
    тянет через fetch() внутри страницы и добавляет в captured.
    """
    captured_urls = {item["url"] for item in captured}

    try:
        dom_items = page.evaluate(
            """(patterns) => {
                const hit = (u) => u && patterns.some(p => u.includes(p));
                const out = [];
                // 1. <img> (любой размер)
                document.querySelectorAll('img').forEach(el => {
                    if (!hit(el.src)) return;
                    const r = el.getBoundingClientRect();
                    out.push({src: el.src, w: Math.round(r.width), h: Math.round(r.height), kind: 'img'});
                });
                // 2. background-image у всех элементов
                document.querySelectorAll('*').forEach(el => {
                    const bg = getComputedStyle(el).backgroundImage;
                    if (!bg || bg === 'none') return;
                    const m = bg.match(/url\\((?:"|')?([^"')]+)(?:"|')?\\)/);
                    if (!m) return;
                    const url = m[1];
                    if (!hit(url)) return;
                    const r = el.getBoundingClientRect();
                    out.push({src: url, w: Math.round(r.width), h: Math.round(r.height), kind: 'bg'});
                });
                return out;
            }""",
            IMAGE_URL_PATTERNS,
        )
    except Exception as e:
        print(f"    ! supplement DOM eval ошибка: {e}")
        return

    # Дедуп по src
    seen: set[str] = set()
    uniq: list[dict] = []
    for item in dom_items:
        if item["src"] in seen:
            continue
        seen.add(item["src"])
        uniq.append(item)

    candidates = [
        it for it in uniq
        if it["src"] not in existing_urls and it["src"] not in captured_urls
    ]
    if not candidates:
        return

    print(f"    🔁 В DOM {len(candidates)} URL мимо сети:")
    for it in candidates:
        print(f"       {it['kind']} {it['w']}x{it['h']}  {it['src'][:80]}")

    for it in candidates:
        src = it["src"]
        try:
            data = page.evaluate(
                """async (url) => {
                    const r = await fetch(url, {credentials: 'include'});
                    if (!r.ok) throw new Error('HTTP ' + r.status);
                    const buf = await r.arrayBuffer();
                    return Array.from(new Uint8Array(buf));
                }""",
                src,
            )
            body = bytes(data)
            if len(body) < MIN_IMAGE_BYTES:
                print(f"    ~ dom-fetch пропущен ({len(body)//1024}КБ плейсхолдер) {src[:60]}")
                continue
            # Определяем тип по сигнатуре файла
            if body[:3] == b"\xff\xd8\xff":
                ext = "jpg"
            elif body[:8] == b"\x89PNG\r\n\x1a\n":
                ext = "png"
            elif body[:6] in (b"GIF87a", b"GIF89a"):
                ext = "gif"
            elif body[:4] == b"RIFF" and body[8:12] == b"WEBP":
                ext = "webp"
            else:
                ext = "jpg"
            captured.append({"url": src, "ct": f"image/{ext}", "ext": ext, "body": body})
            print(f"    ✓ dom-fetch {len(body)//1024}КБ → v{len(captured)}  {src[:60]}")
        except Exception as e:
            print(f"    ✗ dom-fetch {src[:60]}: {e}")


def run(markdown_path: Path, scenes_filter: set[int] | None, start_from: int, headless: bool = False, clean_session: bool = False):
    # `headless` оставлен в сигнатуре для обратной совместимости с CLI —
    # в CDP-режиме скрипт не запускает браузер сам, поэтому флаг игнорируется.
    del headless
    title, scenes = parse_markdown(markdown_path)

    if scenes_filter:
        scenes = [s for s in scenes if s.index in scenes_filter]
    if start_from:
        scenes = [s for s in scenes if s.index >= start_from]

    print(f"📖 Миф: {title}")
    print(f"📑 Будет обработано сцен: {len(scenes)} (номера: {[s.index for s in scenes]})")

    # Резолвим Flow-проект ДО запуска браузера: если сценарий новый,
    # пользователя спросят flow_id сразу, без лишнего запуска Chromium.
    flow_url = resolve_flow_url(markdown_path)

    scenario_folder = resolve_scenario_folder(markdown_path)
    output_dir = CONTENT_ROOT / scenario_folder / "images" / "review_images"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📂 Картинки будут сохраняться в: {output_dir}")

    # Буфер для перехваченных image-ответов текущей сцены
    captured: list[dict] = []
    # Per-scene состояние listener'а
    state: dict = {"accepting": False, "existing_urls": set()}

    # Чистка сессии перед прогоном: закрывает Chrome 9222 (если запущен),
    # сносит google-куки, Local/Session Storage, Cache, IndexedDB labs.google.
    # Даёт Flow «как первый заход» trust-score, что эмпирически снимает
    # «We noticed unusual activity». Цена — придётся залогиниться в Google
    # заново. По умолчанию выключено, включается флагом из вебаппа.
    if clean_session:
        clean_flow_session()
    else:
        print("ℹ Чистка сессии отключена — использую существующие cookies/storage Chrome")

    with sync_playwright() as p:
        # CDP-attach к user-launched Chrome вместо запуска своего —
        # это главный слой анти-детекта. Google Flow отлавливает
        # Playwright-launched Chrome (даже с stealth-патчами) и ставит
        # «unusual activity». Обычный Chrome, поднятый пользователем
        # через launch_chrome_debug.bat, — чистый fingerprint.
        #
        # Если Chrome-debug ещё не запущен — сами поднимаем его через
        # launch_chrome_debug.bat и ждём открытия CDP-порта. Это даёт
        # one-click UX из webapp: нажал кнопку — всё само.

        # Шаг 0: извлекаем target flow_id из resolved URL — именно по нему
        # ищем вкладку. Иначе скрипт натыкается на любую flow/project вкладку
        # (например, hardcoded Дедала из launch_chrome_debug.bat) и льёт
        # промпты в чужой проект.
        target_pid = _flow_project_id_from_url(flow_url)

        # Шаг 1: убеждаемся, что Chrome-debug слушает порт 9222
        if not ensure_debug_chrome(max_wait_sec=60):
            print("\n❌ Chrome-debug не стартовал за 60 сек.")
            print("   Попробуй запустить automation/launch_chrome_debug.bat вручную.")
            sys.exit(1)

        # Шаг 2: несколько попыток attach к CDP — Chrome после старта может
        # ещё не успеть инициализировать все контексты.
        browser, page = None, None
        for attempt in range(10):
            browser, page = attach_and_find(p, target_project_id=target_pid, verbose=False)
            if browser is not None:
                break
            time.sleep(1)

        if browser is None:
            print("\n❌ CDP-порт открыт, но connect_over_cdp не отвечает.")
            print(f"   Chrome работает? Проверь http://localhost:{CDP_PORT}/json/version")
            sys.exit(1)

        # Шаг 3: вкладки целевого проекта нет — открываем сами. Чужие вкладки
        # (другие flow-проекты) остаются без изменений, ничего не закрываем.
        if page is None:
            print(f"\n🌐 Вкладка проекта {target_pid or '?'} не найдена — открываю её сам:")
            print(f"   {flow_url}")
            try:
                page = open_flow_tab(browser, flow_url)
            except Exception as e:
                print(f"❌ Не удалось открыть Flow-проект: {e}")
                print(f"   Залогинься в Google вручную и открой: {flow_url}")
                sys.exit(1)
        del flow_url

        # Сохраняем target_pid на будущее — ensure_page_alive при обрыве
        # вкладки должен переподключаться к ТОЙ ЖЕ ЦЕЛЕВОЙ вкладке, а не к
        # первой попавшейся.
        state["target_pid"] = target_pid

        print(f"🔗 Подключён к Chrome, вкладка Flow готова:")
        print(f"   {page.url[:80]}...")
        page.bring_to_front()

        # Clipboard-разрешение для labs.google — на user-Chrome либо уже
        # выдано пользователем, либо Chrome сам спросит при первой вставке.
        # Пытаемся через CDP-контекст, молча падаем если что.
        try:
            page.context.grant_permissions(
                ["clipboard-read", "clipboard-write"],
                origin="https://labs.google",
            )
        except Exception as e:
            print(f"⚠ Не удалось выдать clipboard-разрешения (не критично): {e}")

        # Listener принимает картинки ТОЛЬКО когда state["accepting"]=True
        # (выставляется в generate_scene после клика «Создать»)
        # и только те URL, которых не было в DOM до клика.
        def on_response(resp):
            try:
                ct = (resp.headers or {}).get("content-type", "")
                if not ct.startswith("image/"):
                    return
                if not state.get("accepting"):
                    return
                url = resp.url

                # DEBUG: логируем все image/* ответы во время приёма
                print(f"    [net] {ct} {url[:100]}")

                if not any(pat in url for pat in IMAGE_URL_PATTERNS):
                    print(f"    [net] ↳ отклонён: URL не в IMAGE_URL_PATTERNS")
                    return
                if url in state.get("existing_urls", set()):
                    print(f"    [net] ↳ отклонён: был в DOM до клика")
                    return
                if any(item["url"] == url for item in captured):
                    return
                body = resp.body()
                size_kb = len(body) // 1024
                if len(body) < MIN_IMAGE_BYTES:
                    print(f"    [net] ↳ отклонён: {size_kb}КБ < {MIN_IMAGE_BYTES//1024}КБ (плейсхолдер)")
                    return
                ext = ct.split("/")[-1].split(";")[0].strip() or "png"
                if ext == "jpeg":
                    ext = "jpg"
                captured.append({"url": url, "ct": ct, "ext": ext, "body": body})
                print(f"    [net] ✓ перехвачено {size_kb}КБ")
            except Exception as e:
                print(f"    ! ошибка перехвата: {e}")

        page.on("response", on_response)

        # В CDP-режиме мы НЕ переходим на Flow URL — пользователь уже открыл
        # нужный проект в своём Chrome. page.goto(flow_url) инициировал бы
        # новую навигацию внутри его сессии, потенциально сбивая состояние.
        print(f"\n🌐 Работаю с уже открытой вкладкой Flow:")
        print(f"   {page.url[:100]}")

        print("\n⏸  Убедись что проект Flow полностью загрузился, поле ввода промпта видно.")
        print("   Если недавно была ошибка 'unusual activity' — подожди 15-30 мин перед запуском.")
        auto_mode = getattr(builtins, "_imagefx_auto", False)
        if auto_mode:
            print("   [auto] жду поля ввода промпта до 120 сек…")
            try:
                page.wait_for_selector("textarea, [contenteditable='true']", timeout=120_000)
                print("   [auto] поле ввода появилось — стартую через 3 сек")
                time.sleep(3)
            except Exception as e:
                print(f"   [auto] ⚠ не дождался поля ввода ({e}) — продолжаю всё равно")
        else:
            input("   Нажми Enter для старта генерации... ")

        # На всякий случай переподключаемся к вкладке — пользователь мог
        # что-то закрыть/переоткрыть пока нажимал Enter.
        page = ensure_page_alive(p, page, target_project_id=state.get("target_pid"))
        if page is None:
            print("❌ Не смог привязаться к вкладке Flow. Выхожу.")
            sys.exit(1)

        for i, scene in enumerate(scenes):
            # Перед каждой сценой проверяем что вкладка жива. Flow может
            # сам закрыть/перезагрузить её при abuse-лимите — тогда
            # переподключаемся к целевой вкладке через CDP.
            page = ensure_page_alive(p, page, target_project_id=state.get("target_pid"))
            if page is None:
                print("❌ Flow-вкладка окончательно потеряна. Выход.")
                break

            try:
                generate_scene(page, scene, output_dir, captured, state)
            except Exception as e:
                print(f"  ✗ Ошибка на сцене {scene.index}: {e}")
            finally:
                state["accepting"] = False

            # ВАЖНО: паузы копируют video_runner. Раньше было 12-22 сек
            # между сценами — Google палил это как автоматизацию (4 картинки
            # × 25 сцен за ~10 минут = ~100 картинок, человек так не делает).
            # Теперь: 90-180 сек между сценами. После первого abuse-хита
            # все паузы удваиваются — Flow в этом режиме очевидно
            # подозревает сессию, и единственный честный сигнал «я человек»
            # — резко снизить cadence до конца прогона.
            if i < len(scenes) - 1:
                # Между генерацией и паузой — «посмотреть, что получилось»
                look_at_results(page)

                # После abuse ИЛИ rate-limit увеличиваем паузы вдвое — это
                # самый честный сигнал «я человек, не торопящийся бот».
                bumped = state.get("abuse_count", 0) > 0 or state.get("rate_limit_count", 0) > 0
                multiplier = 2.0 if bumped else 1.0
                pause = random.uniform(90, 180) * multiplier
                note = " (×2 после abuse/rate-limit)" if multiplier > 1 else ""
                print(f"  💤 Пауза {int(pause)} сек перед следующей сценой{note}...")
                idle_like_human(page, pause)

        print(f"\n✅ Готово. Результаты в: {output_dir}")
        # В CDP-режиме Chrome принадлежит пользователю — НЕ закрываем.
        # Просто выходим из with sync_playwright(), CDP-соединение рвётся,
        # пользовательский Chrome остаётся жить со всеми вкладками.
        auto_mode = getattr(builtins, "_imagefx_auto", False)
        if not auto_mode:
            input("Нажми Enter для завершения скрипта... ")


def parse_scenes_arg(value: str) -> set[int]:
    return {int(x.strip()) for x in value.split(",") if x.strip()}


def main():
    parser = argparse.ArgumentParser(description="Генерация изображений в Google Flow по сценам из markdown.")
    parser.add_argument("markdown", type=Path, help="Путь к .md файлу со сценами")
    parser.add_argument("--scenes", type=str, default=None, help="Номера сцен через запятую, напр. 1,2,3")
    parser.add_argument("--from", dest="start_from", type=int, default=0, help="Начать с сцены N")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Неинтерактивный режим — не ждать Enter, стартовать сразу и закрыть браузер по окончании",
    )
    parser.add_argument(
        "--clean-session",
        action="store_true",
        help="Очистить cookies/Local Storage/Cache Google перед запуском (придётся логиниться заново)",
    )
    args = parser.parse_args()

    if not args.markdown.exists():
        print(f"❌ Файл не найден: {args.markdown}")
        sys.exit(1)

    # Флаг auto пробрасываем через глобал, чтобы в run() и generate_scene
    # не прокидывать его через все сигнатуры.
    builtins._imagefx_auto = bool(args.auto)  # type: ignore[attr-defined]

    scenes_filter = parse_scenes_arg(args.scenes) if args.scenes else None
    run(
        args.markdown,
        scenes_filter,
        args.start_from,
        headless=args.headless,
        clean_session=args.clean_session,
    )


if __name__ == "__main__":
    main()
