"""
Video Flow Runner — автоматизация генерации видео в Google Flow (Veo 3.1).

Читает video.md со сценами, открывает Flow-проект в браузере,
автоматически загружает картинку-источник из проекта, заполняет промпт,
запускает генерацию и скачивает видео.

Использование:
    python automation/video_runner.py scripts/икар_и_дедал/video.md
    python automation/video_runner.py scripts/икар_и_дедал/video.md --scenes 1,2,3
    python automation/video_runner.py scripts/икар_и_дедал/video.md --from 3

Workflow на каждую сцену:
    1. Скрипт загружает картинку сцены автоматически
    2. Ты в браузере: выбираешь модель и формат
    3. Жмёшь Enter в терминале
    4. Скрипт: вставляет промпт → кликает «Создать» → ждёт → скачивает видео
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

# Раньше использовался patchright (stealth-форк Playwright), но для CDP-attach
# к user-launched Chrome stealth-патчи не нужны — Chrome запущен пользователем,
# Playwright только подключается. Обычный playwright + CDP равноценен
# patchright + CDP, зато работает в любом Python без доп. установки.
from playwright.sync_api import Page, sync_playwright

from flow_projects import resolve_flow_url

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


# ──────────────────────────────────────────────────────────────────
# Маппинг «сценарий → flow_id» хранится в automation/flow_projects.json.
# При первом запуске для нового сценария resolve_flow_url() сам спросит
# flow_id и сохранит его в JSON.
# ──────────────────────────────────────────────────────────────────

PROFILE_DIR = Path(__file__).parent / ".browser_profile"
PATCHRIGHT_PROFILE_DIR = Path(__file__).parent / ".patchright_profile"
PROJECT_ROOT = Path(__file__).parent.parent
CONTENT_ROOT = PROJECT_ROOT / "content"

# Режим attach: скрипт подключается к уже запущенному Chrome через CDP.
# Chrome должен быть запущен пользователем (через launch_chrome_debug.bat)
# с флагом --remote-debugging-port=9222. Для Flow это твоя легитимная
# сессия — `navigator.webdriver`=false, нет `--enable-automation`.
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

    Возвращает True если CDP-порт начал отвечать, False если за отведённое
    время не стартанул. Функция продублирована из imagefx_runner — идея
    одинаковая: single-click UX, пользователь жмёт кнопку «запустить видео»,
    всё поднимается само.
    """
    import subprocess as _sp  # noqa: PLC0415
    if _cdp_reachable():
        print(f"✓ Chrome с debug-портом {CDP_PORT} уже запущен")
        return True
    if not LAUNCH_CHROME_BAT.exists():
        print(f"❌ Не найден {LAUNCH_CHROME_BAT}")
        return False
    print(f"🚀 Chrome-debug не запущен — поднимаю {LAUNCH_CHROME_BAT.name}")
    flags = _sp.CREATE_NEW_CONSOLE if hasattr(_sp, "CREATE_NEW_CONSOLE") else 0
    try:
        _sp.Popen(
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
            print(f"✓ CDP-порт ответил через {i+1}с — жду 2 сек на прогрев UI")
            time.sleep(2)
            return True
        time.sleep(1)
    print(f"❌ За {max_wait_sec}с Chrome не открыл CDP-порт")
    return False


def find_flow_page(context) -> Page | None:
    """Находит открытую вкладку с Flow-проектом среди всех вкладок контекста."""
    for pg in context.pages:
        try:
            if pg.is_closed():
                continue
            if "flow/project" in pg.url:
                return pg
        except Exception:
            continue
    return None


def attach_and_find(p, verbose: bool = True) -> tuple[object, Page] | tuple[None, None]:
    """Подключается к Chrome по CDP и находит вкладку Flow.

    Возвращает (browser, page) или (None, None) при неудаче.
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
        return None, None

    for ctx in browser.contexts:
        pg = find_flow_page(ctx)
        if pg is not None:
            return browser, pg

    if verbose:
        print("  ⚠ Не нашёл вкладку Flow ни в одном контексте")
    return None, None


def ensure_page_alive(p, page: Page | None) -> Page | None:
    """Проверяет что вкладка Flow жива, при необходимости переподключается."""
    # Быстрая проверка текущего page
    if page is not None:
        try:
            if not page.is_closed():
                # Доп. проверка через evaluate — page может считаться открытым,
                # но DevTools-сессия уже порвана (Chrome сам перезагрузил вкладку).
                page.evaluate("() => 1")
                return page
        except Exception:
            pass

    # page мёртв — пробуем переподключиться
    print("  🔄 Вкладка Flow потеряна, переподключаюсь через CDP...")
    _, new_page = attach_and_find(p, verbose=False)
    if new_page is not None:
        new_page.bring_to_front()
        print(f"  ✓ Переподключился: {new_page.url[:80]}...")
        return new_page

    # Не смогли найти — просим пользователя
    print("\n  ❌ Flow-проект закрыт. Открой его в Chrome и жми Enter.")
    input("     ")
    _, new_page = attach_and_find(p)
    if new_page is not None:
        new_page.bring_to_front()
        return new_page
    return None

# Папки, которые не могут быть именем сценария (служебные)
_NON_SCENARIO_FOLDERS = {
    "prompts", "video", "images", "voiceover", "music", "final",
    "content", "automation", "scripts", "output",
}


def resolve_scenario_folder(markdown_path: Path) -> str:
    """Имя папки сценария по пути к markdown-файлу.

    Пример: content/Сизифов Труд/prompts/video.md → 'Сизифов Труд'.
    """
    for parent in markdown_path.resolve().parents:
        name = parent.name
        if not name:
            continue
        if name.lower() in _NON_SCENARIO_FOLDERS:
            continue
        return name
    raise ValueError(f"Не удалось определить имя сценария из пути: {markdown_path}")


APPROVED_IMG_RE = re.compile(r"^scene_(\d+)_(v\d+)$")
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def load_approved_images_map(scenario_folder: str) -> dict[int, Path]:
    """Читает content/<миф>/images/approved_images/ и возвращает {scene_index: Path}.

    Позволяет узнать, какой именно вариант (v1/v2/v3/v4) пользователь отобрал
    для конкретной сцены после финализации. Нужно чтобы в Flow-пикере выбрать
    именно тот же кадр визуально — через pHash сравнение с thumbnail'ами.
    """
    approved_dir = CONTENT_ROOT / scenario_folder / "images" / "approved_images"
    if not approved_dir.exists():
        return {}
    result: dict[int, Path] = {}
    for img in approved_dir.iterdir():
        if img.suffix.lower() not in _IMAGE_EXTS:
            continue
        m = APPROVED_IMG_RE.match(img.stem)
        if not m:
            continue
        result[int(m.group(1))] = img
    return result

PAGE_LOAD_TIMEOUT = 60_000

PROMPT_SELECTOR = '[contenteditable="true"][role="textbox"]'
GENERATE_BUTTON_SELECTOR = 'button:has-text("arrow_forward"):has-text("Создать")'

STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en-US', 'en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
window.chrome = window.chrome || { runtime: {} };
"""


@dataclass
class VideoScene:
    index: int
    image_path: str
    prompt: str
    sounds: str


def parse_video_markdown(path: Path) -> tuple[str, list[VideoScene]]:
    content = path.read_text(encoding="utf-8")

    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if not title_match:
        raise ValueError(f"Не найден заголовок `# Название` в {path}")
    raw_title = title_match.group(1).strip()
    # Убираем суффикс " — видео (Veo 3.1)" и подобные
    title = re.sub(r"\s*[—–-]\s*видео.*$", "", raw_title, flags=re.IGNORECASE).strip()

    scene_blocks = re.split(r"^##\s+Сцена\s+\d+\s*$", content, flags=re.MULTILINE)[1:]
    if not scene_blocks:
        raise ValueError(f"Не найдено ни одной `## Сцена N` в {path}")

    scenes: list[VideoScene] = []
    for i, block in enumerate(scene_blocks, start=1):
        image_match = re.search(r"\*\*Изображение:\*\*\s*(.+?)(?=\n)", block)
        prompt_match = re.search(r"\*\*Промпт:\*\*\s*(.+?)(?=\n\*\*Звуки|\n##|\Z)", block, re.DOTALL)
        sounds_match = re.search(r"\*\*Звуки:\*\*\s*(.+?)(?=\n##|\Z)", block, re.DOTALL)

        if not prompt_match:
            print(f"⚠ Сцена {i}: не найден промпт, пропускаю")
            continue

        scenes.append(
            VideoScene(
                index=i,
                image_path=(image_match.group(1).strip() if image_match else ""),
                prompt=prompt_match.group(1).strip(),
                sounds=(sounds_match.group(1).strip() if sounds_match else ""),
            )
        )
    return title, scenes


def build_full_prompt(scene: VideoScene) -> str:
    """Собирает полный промпт: действие + звуки в одну строку.

    ВАЖНО: нельзя использовать \\n — Enter в contenteditable запускает генерацию.
    """
    parts = [scene.prompt]
    if scene.sounds:
        parts.append(f"Sounds: {scene.sounds}")
    return " ".join(parts)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s]+", "_", text)
    return text or "untitled"


def human_sleep(min_s: float, max_s: float):
    time.sleep(random.uniform(min_s, max_s))


def human_type(page: Page, text: str):
    for ch in text:
        page.keyboard.type(ch)
        if ch == " " and random.random() < 0.15:
            time.sleep(random.uniform(0.15, 0.4))
        else:
            time.sleep(random.uniform(0.04, 0.12))


def random_mouse_wander(page: Page, intensity: str = "normal"):
    """Имитирует праздное движение мыши.

    intensity:
      'light'  — 1-2 движения, короткие паузы (быстрый жест между кликами)
      'normal' — 2-4 движения (по умолчанию)
      'heavy'  — 4-8 движений с долгими паузами (во время «чтения» или ожидания)
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
        page.mouse.move(x, y, steps=random.randint(15, 35))
        time.sleep(random.uniform(*pause))


def idle_like_human(page: Page, seconds: float):
    """Ждёт `seconds` секунд, периодически шевеля мышью — как человек
    смотрит в экран и иногда двигает курсор.
    """
    elapsed = 0.0
    while elapsed < seconds:
        chunk = random.uniform(3.5, 9.0)
        if elapsed + chunk > seconds:
            chunk = seconds - elapsed
        time.sleep(chunk)
        elapsed += chunk
        # 60% шанс что-то подвинуть, 40% просто сидеть
        if random.random() < 0.6 and elapsed < seconds - 0.5:
            random_mouse_wander(page, intensity=random.choice(["light", "normal"]))
            # random_mouse_wander сам потратил ~0.5-2 сек — учитываем
            elapsed += random.uniform(0.5, 1.5)


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


GALLERY_IMG_SELECTOR = 'img[alt="Сгенерированное изображение"]'
# Слот «Первый кадр» — div 50x50 cursor:pointer в видео-панели
FIRST_FRAME_SLOT_TEXT = "Первый кадр"


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
                    || text.includes('помощи') && text.includes('help center')
                    || text.includes('we noticed some');
            }
            """
        ))
    except Exception:
        return False


def pause_for_abuse_resolution(context: str = ""):
    """Останавливает скрипт, ждёт пока пользователь разблокирует Flow вручную."""
    print("\n" + "🚨" * 30)
    print(f"  Flow показал «подозрительная активность»{' (' + context + ')' if context else ''}.")
    print("  1) В окне браузера — кликни на предупреждение, пройди все шаги")
    print("     (restore, continue, или подожди несколько минут).")
    print("  2) Когда Flow снова работает — нажми Enter здесь для продолжения.")
    print("🚨" * 30)
    input("\n     Жду разблокировки → Enter... ")
    # Дать странице стабилизироваться после разблокировки
    time.sleep(random.uniform(2, 4))


# ── Детект rate-limit тоста («Вы слишком быстро отправляете запросы») ──────
#
# Это другой сигнал, чем abuse-диалог: тост появляется на 5-7 сек в
# нижнем-левом углу и сам исчезает. Если его не поймать — раннер
# простоит весь wait_for_video_generation таймаут впустую.

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


# ── Perceptual hash (pHash) для автовыбора картинки из пикера ───────────────
#
# Flow-пикер показывает thumbnail'ы и превью описаний, но без привязки к тому,
# какой именно scene_XX_vN.jpg мы выбрали при финализации — UUID во Flow не
# совпадают с именами файлов в approved_images/. Поэтому сопоставляем визуально:
# считаем pHash каждого thumbnail и сравниваем с pHash approved-картинки.
#
# Метод: grayscale + resize 8×8 → bit per pixel относительно среднего.
# Это устойчиво к разнице разрешений (thumbnail vs original) и небольшому
# шуму от JPEG-сжатия.

def phash_bytes(data: bytes, size: int = 8) -> int:
    """Перцептуальный хэш картинки (64 бита для size=8)."""
    from PIL import Image
    from io import BytesIO
    img = Image.open(BytesIO(data)).convert("L").resize((size, size), Image.LANCZOS)
    pixels = list(img.getdata())
    avg = sum(pixels) / len(pixels)
    h = 0
    for p in pixels:
        h = (h << 1) | (1 if p > avg else 0)
    return h


def hamming_distance(h1: int, h2: int) -> int:
    """Число отличающихся бит между двумя хэшами."""
    return bin(h1 ^ h2).count("1")


def fetch_image_bytes(page: Page, url: str) -> bytes:
    """Загружает картинку по URL через fetch() внутри страницы → bytes.

    Делается из контекста Flow (same-origin), поэтому работает с приватными
    thumbnail'ами, которые напрямую Playwright не скачает.
    """
    import base64
    data_url = page.evaluate(
        """
        async (url) => {
            const r = await fetch(url);
            if (!r.ok) throw new Error('HTTP ' + r.status);
            const blob = await r.blob();
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            });
        }
        """,
        url,
    )
    _, b64 = data_url.split(",", 1)
    return base64.b64decode(b64)


def click_first_frame_slot(page: Page) -> bool:
    """Кликает на слот «Первый кадр» в видео-панели для открытия режима выбора."""
    # Playwright text selector — точное совпадение
    slot = page.get_by_text(FIRST_FRAME_SLOT_TEXT, exact=True)
    if slot.count() > 0 and slot.first.is_visible():
        slot.first.click()
        human_sleep(1.0, 1.5)
        print("  ✓ Кликнул на «Первый кадр» — режим выбора открыт")
        return True

    # Fallback: ищем div с текстом «Первый кадр» размером ~50x50
    clicked = page.evaluate("""
        () => {
            const divs = document.querySelectorAll('div');
            for (const d of divs) {
                const text = (d.innerText || '').trim();
                if (text === 'Первый кадр') {
                    const rect = d.getBoundingClientRect();
                    if (rect.width > 30 && rect.width < 100) {
                        d.click();
                        return 'ok:' + Math.round(rect.width) + 'x' + Math.round(rect.height);
                    }
                }
            }
            return null;
        }
    """)
    if clicked:
        human_sleep(1.0, 1.5)
        print(f"  ✓ Кликнул на «Первый кадр» (JS fallback: {clicked})")
        return True

    print("  ⚠ Слот «Первый кадр» не найден")
    return False


def get_gallery_image_urls(page: Page) -> list[str]:
    """Собирает URL всех изображений из главной галереи (до открытия пикера).

    С retry: Flow — SPA, может делать навигацию прямо во время evaluate
    (особенно при первом запуске сцены — страница ещё дорендеривается).
    """
    last_err = None
    for attempt in range(5):
        try:
            # Ждём пока DOM стабилизируется — необязательно до networkidle,
            # достаточно "domcontentloaded" плюс небольшая пауза
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5_000)
            except Exception:
                pass
            return page.evaluate("""
                () => Array.from(document.querySelectorAll('img[alt="Сгенерированное изображение"]'))
                    .map(img => img.src)
            """)
        except Exception as e:
            last_err = e
            msg = str(e)
            if "Execution context was destroyed" in msg or "navigation" in msg.lower():
                print(f"  ⚠ Страница ещё навигирует, жду 3 сек (попытка {attempt + 1}/5)...")
                time.sleep(3)
                continue
            raise
    raise last_err if last_err else RuntimeError("get_gallery_image_urls failed")


def extract_media_id(url: str) -> str:
    """Извлекает media ID (UUID) из URL изображения Flow."""
    m = re.search(r'name=([a-f0-9-]+)', url)
    return m.group(1) if m else ""


def _search_picker_for_id(page: Page, target_media_id: str) -> dict:
    """JS: ищет строку с UUID в пикере, возвращает координаты или информацию об ошибке."""
    return page.evaluate("""
        (mediaId) => {
            const dialog = document.querySelector('div[role="dialog"]');
            if (!dialog) return {ok: false, reason: 'no_dialog'};

            // Собираем все строки пикера: div ~257x56, cursor:pointer, содержит img
            const rows = [];
            dialog.querySelectorAll('div').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 200 && rect.width < 350
                    && rect.height > 40 && rect.height < 70
                    && el.querySelector('img')
                    && window.getComputedStyle(el).cursor === 'pointer') {
                    rows.push(el);
                }
            });

            if (rows.length === 0) return {ok: false, reason: 'no_rows'};

            // Ищем строку с совпадением UUID в thumbnail src
            for (let i = 0; i < rows.length; i++) {
                const img = rows[i].querySelector('img');
                if (img && img.src && img.src.includes(mediaId)) {
                    rows[i].scrollIntoView({block: 'center'});
                    const rect = rows[i].getBoundingClientRect();
                    return {
                        ok: true,
                        text: (rows[i].innerText || '').trim().slice(0, 60),
                        index: i,
                        total: rows.length,
                        x: rect.x + rect.width / 2,
                        y: rect.y + rect.height / 2,
                    };
                }
            }

            // Не нашли — вернуть количество
            return {ok: false, reason: 'no_match', total: rows.length};
        }
    """, target_media_id)


def _scroll_picker(page: Page, direction: str = "down") -> bool:
    """Скроллит контейнер списка внутри диалога пикера. Возвращает True если скролл произошёл."""
    delta = 300 if direction == "down" else -300
    return page.evaluate("""
        (delta) => {
            const dialog = document.querySelector('div[role="dialog"]');
            if (!dialog) return false;

            // Ищем скроллируемый контейнер внутри диалога
            const containers = dialog.querySelectorAll('div');
            for (const c of containers) {
                if (c.scrollHeight > c.clientHeight + 10 && c.clientHeight > 100) {
                    const before = c.scrollTop;
                    c.scrollTop += delta;
                    return Math.abs(c.scrollTop - before) > 5;
                }
            }
            return false;
        }
    """, delta)


def select_from_picker(page: Page, target_media_id: str) -> bool:
    """Находит и кликает элемент в открытом пикере (div[role='dialog']) по UUID.

    Пикер показывает список с текстовыми описаниями и превью.
    Каждый элемент — div ~257x56px, cursor:pointer, содержит img с thumbnail.
    Порядок непредсказуем — поэтому ищем по UUID в src thumbnail.

    Список виртуализирован: только ~16 элементов рендерятся одновременно.
    Если UUID не найден — скроллим вниз порциями, загружая новые элементы.
    """
    # Ждём появления диалога
    try:
        page.locator('div[role="dialog"]').wait_for(state="visible", timeout=5_000)
    except Exception:
        print("  ⚠ Диалог пикера не появился")
        return False

    human_sleep(0.5, 1.0)

    # Сначала скроллим в начало списка
    _scroll_picker(page, "up")
    _scroll_picker(page, "up")
    _scroll_picker(page, "up")
    human_sleep(0.3, 0.5)

    # Ищем элемент, скролля вниз при необходимости (до 15 попыток)
    max_scroll_attempts = 15
    for attempt in range(max_scroll_attempts + 1):
        result = _search_picker_for_id(page, target_media_id)

        if result.get("ok"):
            # Нашли — кликаем по координатам (Playwright — настоящая эмуляция мыши)
            human_sleep(0.3, 0.6)
            page.mouse.click(result["x"], result["y"])
            human_sleep(1.5, 2.5)
            print(f"  ✓ Выбрано из пикера: '{result['text']}' [{result['index']}/{result['total']}]"
                  + (f" (после {attempt} скроллов)" if attempt > 0 else ""))
            return True

        if result.get("reason") in ("no_dialog", "no_rows"):
            print(f"  ⚠ Пикер: {result.get('reason')}")
            return False

        # Не нашли — скроллим вниз
        if attempt < max_scroll_attempts:
            scrolled = _scroll_picker(page, "down")
            if not scrolled:
                # Дошли до конца списка
                print(f"  ⚠ Достигнут конец списка пикера (после {attempt + 1} скроллов), UUID не найден")
                break
            human_sleep(0.3, 0.5)

    print(f"  ⚠ Не нашёл в пикере: UUID {target_media_id[:12]}... "
          f"(прокрутил {max_scroll_attempts} раз)")
    return False


def _list_picker_rows(page: Page) -> list[dict]:
    """Возвращает видимые ряды пикера с координатами и URL миниатюр."""
    return page.evaluate(
        """
        () => {
            const dialog = document.querySelector('div[role="dialog"]');
            if (!dialog) return [];
            const out = [];
            dialog.querySelectorAll('div').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 200 && rect.width < 350
                    && rect.height > 40 && rect.height < 70
                    && el.querySelector('img')
                    && window.getComputedStyle(el).cursor === 'pointer') {
                    const img = el.querySelector('img');
                    out.push({
                        src: img.src,
                        x: rect.x + rect.width / 2,
                        y: rect.y + rect.height / 2,
                    });
                }
            });
            return out;
        }
        """
    )


# Порог совпадения pHash. Типичные значения:
#   distance 0-5    — почти точное совпадение (считаем "нашёл")
#   distance 5-12   — похожее изображение
#   distance 12-20  — сомнительно, но ещё можно
#   distance 20+    — разные картинки
PHASH_MATCH_THRESHOLD = 14


def select_from_picker_by_image(page: Page, approved_path: Path) -> bool:
    """Находит в открытом пикере картинку, визуально совпадающую с approved_path.

    Алгоритм:
      1. Считаем pHash approved-кадра
      2. Скроллим пикер сверху вниз, на каждом шаге хэшируем новые thumbnail'ы
      3. Находим ряд с минимальной hamming distance
      4. Если ниже порога — кликаем, иначе возвращаем False (ручной fallback)
    """
    try:
        page.locator('div[role="dialog"]').wait_for(state="visible", timeout=5_000)
    except Exception:
        print("  ⚠ Диалог пикера не появился")
        return False

    target_hash = phash_bytes(approved_path.read_bytes())
    print(f"  🔢 pHash approved: {target_hash:016x}")

    human_sleep(0.4, 0.7)
    # Скроллим в начало списка
    for _ in range(3):
        _scroll_picker(page, "up")
    human_sleep(0.3, 0.5)

    best = {"distance": 999, "src": None, "x": 0, "y": 0}
    seen_srcs: set[str] = set()
    max_scrolls = 50

    for scroll_i in range(max_scrolls):
        rows = _list_picker_rows(page)
        new_in_batch = 0
        for row in rows:
            src = row.get("src")
            if not src or src in seen_srcs:
                continue
            seen_srcs.add(src)
            new_in_batch += 1
            try:
                thumb_bytes = fetch_image_bytes(page, src)
                row_hash = phash_bytes(thumb_bytes)
                d = hamming_distance(row_hash, target_hash)
                if d < best["distance"]:
                    best = {"distance": d, "src": src, "x": row["x"], "y": row["y"]}
                    if d <= 2:
                        # Очень уверенное совпадение — можно не продолжать
                        print(f"  ⚡ Почти идеальное совпадение (distance={d}), остановка")
                        break
            except Exception as e:
                # Thumbnail мог ещё грузиться — пропускаем
                continue

        if best["distance"] <= 2:
            break

        if new_in_batch == 0:
            # Ничего нового не появилось — скорее всего, достигли конца
            break

        scrolled = _scroll_picker(page, "down")
        if not scrolled:
            break
        time.sleep(0.35)

    print(f"  📏 Лучшее совпадение: distance={best['distance']}, "
          f"просканировано {len(seen_srcs)} картинок")

    if best["distance"] > PHASH_MATCH_THRESHOLD:
        print(f"  ⚠ Слабое совпадение (>{PHASH_MATCH_THRESHOLD}) — выбор ненадёжен")
        return False

    # Прокручиваем к найденному ряду и кликаем
    clicked = page.evaluate(
        """
        (src) => {
            const dialog = document.querySelector('div[role="dialog"]');
            if (!dialog) return false;
            const rows = Array.from(dialog.querySelectorAll('div'));
            for (const el of rows) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 200 && rect.width < 350
                    && rect.height > 40 && rect.height < 70
                    && el.querySelector('img')
                    && window.getComputedStyle(el).cursor === 'pointer') {
                    const img = el.querySelector('img');
                    if (img && img.src === src) {
                        el.scrollIntoView({block: 'center'});
                        return true;
                    }
                }
            }
            return false;
        }
        """,
        best["src"],
    )
    if not clicked:
        print("  ⚠ Ряд с лучшим совпадением исчез после скролла")
        return False

    time.sleep(0.4)
    # Перечитываем координаты после scrollIntoView
    rows = _list_picker_rows(page)
    for row in rows:
        if row.get("src") == best["src"]:
            page.mouse.click(row["x"], row["y"])
            human_sleep(1.2, 1.8)
            print(f"  ✓ Автовыбор по pHash (distance={best['distance']})")
            return True

    # Fallback — клик по последним известным координатам
    page.mouse.click(best["x"], best["y"])
    human_sleep(1.2, 1.8)
    print(f"  ✓ Автовыбор по pHash (distance={best['distance']}, исходные координаты)")
    return True


def fill_prompt(page: Page, prompt: str):
    """Живой ввод промпта — тот же паттерн, что в imagefx_runner.

    Paste через буфер — один из явных bot-сигналов Google. Печатаем
    посимвольно с вариативным ритмом 25-65 симв/сек, кликаем по полю
    с человекоподобной траекторией мыши, очищаем одним из трёх
    случайных способов.
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

        # Прогрессивный backoff: 60-120, 120-240, 180-360 сек.
        # Veo и так медленный, дополнительная минута-две не критична.
        cooldown = random.uniform(60, 120) * attempt
        print(f"  ⏳ Rate-limit (попытка {attempt}/{max_retries}): пауза {int(cooldown)} сек перед retry…")
        deadline = time.time() + cooldown
        while time.time() < deadline:
            time.sleep(min(5.0, deadline - time.time()))
        # Дожидаемся пока тост точно исчез — иначе следующий клик
        # может попасть на ещё видимый toast и быть проигнорирован Flow.
        for _ in range(15):
            if not detect_rate_limit_toast(page):
                break
            time.sleep(2.0)
    return False


def snapshot_video_ids(page: Page) -> list[str]:
    """Снимок «какие видео сейчас есть в галерее».

    Признак каждого видео — src <video> + его позиция. Пока видео не
    перемешиваются внутри сессии, эти id стабильны. Используем для того,
    чтобы потом отличить «наше» новое видео от других, которые могли
    появиться параллельно (например, если пользователь сам генерирует).
    """
    return page.evaluate(
        """
        () => {
            const out = [];
            document.querySelectorAll('div[role="button"][tabindex="0"]').forEach(item => {
                const rect = item.getBoundingClientRect();
                if (rect.width < 80 || rect.height < 80 || rect.y < 0) return;
                let hasPlay = false;
                item.querySelectorAll('i, span').forEach(icon => {
                    const t = (icon.textContent || '').trim().toLowerCase();
                    if (t.includes('play_arrow') || t.includes('play_circle')) hasPlay = true;
                });
                if (!hasPlay) hasPlay = !!item.querySelector('video');
                if (!hasPlay) return;
                const vid = item.querySelector('video');
                const src = vid ? vid.src : '';
                out.push(src + '|' + Math.round(rect.x) + ',' + Math.round(rect.y)
                         + ',' + Math.round(rect.width) + 'x' + Math.round(rect.height));
            });
            return out;
        }
        """
    )


def open_specific_video(page: Page, before_ids: list[str]) -> bool:
    """Находит и кликает на НОВОЕ видео, появившееся после последнего снимка.

    Работает даже если параллельно появились другие видео — ищет ровно те,
    которых не было в `before_ids`. Если новых несколько — берёт первое
    (то которое сверху = обычно самое свежее).
    """
    new_coords = page.evaluate(
        """
        (beforeList) => {
            const before = new Set(beforeList);
            const items = document.querySelectorAll('div[role="button"][tabindex="0"]');
            for (const item of items) {
                const rect = item.getBoundingClientRect();
                if (rect.width < 80 || rect.height < 80 || rect.y < 0) continue;
                let hasPlay = false;
                item.querySelectorAll('i, span').forEach(icon => {
                    const t = (icon.textContent || '').trim().toLowerCase();
                    if (t.includes('play_arrow') || t.includes('play_circle')) hasPlay = true;
                });
                if (!hasPlay) hasPlay = !!item.querySelector('video');
                if (!hasPlay) continue;
                const vid = item.querySelector('video');
                const src = vid ? vid.src : '';
                const id = src + '|' + Math.round(rect.x) + ',' + Math.round(rect.y)
                           + ',' + Math.round(rect.width) + 'x' + Math.round(rect.height);
                if (!before.has(id)) {
                    return {
                        x: Math.round(rect.x + rect.width / 2),
                        y: Math.round(rect.y + rect.height / 2),
                        w: Math.round(rect.width),
                        h: Math.round(rect.height),
                    };
                }
            }
            return null;
        }
        """,
        before_ids,
    )

    if new_coords:
        print(f"  📹 Нашёл НОВОЕ видео ({new_coords['w']}x{new_coords['h']})")
        page.mouse.click(new_coords["x"], new_coords["y"])
        human_sleep(2.0, 3.0)
        dl_btn = page.locator('button:has-text("Скачать")')
        if dl_btn.count() > 0 and dl_btn.first.is_visible():
            print("  ✓ Превью видео открыто")
            return True

    print("  ⚠ Не нашёл новое видео — пробую запасной вариант (первое в галерее)")
    return open_generated_video(page)


def open_generated_video(page: Page) -> bool:
    """Находит и кликает на сгенерированное ВИДЕО (не картинку) в галерее.

    Видео отличается от изображений наличием иконки play (▶) внутри карточки.
    Кликаем на первый (самый новый) видео-элемент.
    """
    # Ищем карточки галереи, содержащие иконку play (= видео, а не картинка)
    video_coords = page.evaluate("""
        () => {
            const items = document.querySelectorAll('div[role="button"][tabindex="0"]');
            for (const item of items) {
                const rect = item.getBoundingClientRect();
                if (rect.width < 80 || rect.height < 80 || rect.y < 0) continue;

                // Ищем иконку play внутри карточки (Material Icons: <i>play_arrow</i>)
                let hasPlay = false;
                item.querySelectorAll('i, span').forEach(icon => {
                    const t = (icon.textContent || '').trim().toLowerCase();
                    if (t.includes('play_arrow') || t.includes('play_circle')
                        || t === 'play_arrow' || t === 'play_circle_filled') {
                        hasPlay = true;
                    }
                });
                // Также проверяем наличие <video> элемента
                if (!hasPlay) hasPlay = !!item.querySelector('video');

                if (hasPlay) {
                    return {
                        x: Math.round(rect.x + rect.width / 2),
                        y: Math.round(rect.y + rect.height / 2),
                        w: Math.round(rect.width),
                        h: Math.round(rect.height),
                    };
                }
            }
            return null;
        }
    """)

    if video_coords:
        print(f"  📹 Нашёл видео в галерее ({video_coords['w']}x{video_coords['h']})")
        page.mouse.click(video_coords["x"], video_coords["y"])
        human_sleep(2.0, 3.0)

        # Проверяем что превью открылось
        dl_btn = page.locator('button:has-text("Скачать")')
        if dl_btn.count() > 0 and dl_btn.first.is_visible():
            print("  ✓ Превью видео открыто")
            return True

    print("  ⚠ Видео не найдено автоматически (нет иконки play в галерее)")
    return False


# Качество скачиваемого видео из Flow. У Veo 3.1 в меню «Скачать» доступны
# «720p» и «1080p». Контент канала — пиксель-арт, у которого нет высоко-
# частотных деталей, на которых 1080p выигрывает; YouTube Shorts/TikTok
# всё равно ререндерят клип в свой кодек. 720p в ~2× легче по весу,
# скачивается заметно быстрее, экономит диск и трафик. Дефолт — 720p,
# через --quality 1080p можно поднять для архива/мастера.
DOWNLOAD_QUALITY = "720p"
DOWNLOAD_TIMEOUT_MS = 240_000  # 4 минуты — даже 720p может качаться долго при медленном Flow

QUALITY_CHOICES = ("720p", "1080p")


def _do_download_flow(page: Page, output_dir: Path, scene_index: int,
                      attempt_label: str = "") -> bool:
    """Однократная попытка скачать текущее видео через UI: Скачать → {DOWNLOAD_QUALITY}.

    Ключевые моменты:
    - ждём что меню качеств ДЕЙСТВИТЕЛЬНО появилось после клика «Скачать»
    - таймаут скачивания 4 мин (на медленном Flow даже 720p качается не мгновенно)
    - перед кликом на пункт качества убеждаемся что элемент видим и enabled
    """
    label = f" [{attempt_label}]" if attempt_label else ""

    dl_btn = page.locator('button:has-text("Скачать")')
    try:
        dl_btn.first.wait_for(state="visible", timeout=5_000)
        dl_btn.first.click()
        human_sleep(0.8, 1.5)
        print(f"  ↳ Кликнул «Скачать»{label}")
    except Exception as e:
        print(f"  ⚠ Кнопка «Скачать» не найдена: {e}")
        return False

    # Ждём, пока реально появится пункт {DOWNLOAD_QUALITY} (меню качеств открылось).
    # Если меню не развернулось — клик на текст уйдёт в никуда.
    q_btn = page.get_by_text(DOWNLOAD_QUALITY)
    try:
        q_btn.first.wait_for(state="visible", timeout=10_000)
    except Exception:
        print(f"  ⚠ Меню качеств не появилось — ещё раз жмём «Скачать»")
        try:
            dl_btn.first.click()
            human_sleep(0.8, 1.5)
            q_btn.first.wait_for(state="visible", timeout=10_000)
        except Exception as e:
            print(f"  ⚠ Меню всё равно не открылось: {e}")
            return False

    # Ловим скачивание
    try:
        with page.expect_download(timeout=DOWNLOAD_TIMEOUT_MS) as download_info:
            q_btn.first.click()
            print(f"  ↳ Кликнул «{DOWNLOAD_QUALITY}», жду скачивания (до {DOWNLOAD_TIMEOUT_MS // 60_000} мин)...")

        download = download_info.value
        out_path = output_dir / f"scene_{scene_index:02d}_v1.mp4"
        download.save_as(str(out_path))
        size_mb = out_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ Скачано{label}: {out_path.name} ({size_mb:.1f} МБ, {DOWNLOAD_QUALITY})")
        return True
    except Exception as e:
        print(f"  ⚠ Ошибка скачивания{label}: {e}")
        return False


def download_video_via_ui(page: Page, output_dir: Path, scene_index: int,
                          state: dict | None = None) -> bool:
    """Скачивает видео из открытого превью с retry и обнаружением блокировок."""

    # Первая попытка
    if _do_download_flow(page, output_dir, scene_index):
        return True

    # Диагностика: что видно на экране после таймаута?
    try:
        visible_buttons = page.evaluate(
            """
            () => {
                const out = [];
                document.querySelectorAll('button').forEach(b => {
                    if (b.offsetWidth > 0 && b.offsetHeight > 0) {
                        const t = (b.innerText || '').trim();
                        if (t && t.length < 40) out.push(t);
                    }
                });
                return out.slice(0, 20);
            }
            """
        )
        print(f"  🔍 Видимые кнопки на странице: {visible_buttons}")
    except Exception:
        pass

    # Проверяем abuse-диалог
    if detect_abuse_dialog(page):
        if state is not None:
            state["abuse_count"] = state.get("abuse_count", 0) + 1
        pause_for_abuse_resolution(context=f"при скачивании сцены {scene_index}")
        time.sleep(random.uniform(1.5, 3.0))
        # Повтор после разблокировки
        if _do_download_flow(page, output_dir, scene_index, attempt_label="после разблокировки"):
            return True

    # Ещё одна попытка — иногда после таймаута меню просто закрылось,
    # и достаточно ещё раз пройти весь флоу.
    print("  🔄 Ещё одна попытка...")
    time.sleep(random.uniform(2, 4))
    if _do_download_flow(page, output_dir, scene_index, attempt_label="retry"):
        return True

    return False


def count_video_items(page: Page) -> int:
    """Считает количество видео (не изображений) в галерее по иконке play."""
    return page.evaluate("""
        () => {
            let count = 0;
            const items = document.querySelectorAll('div[role="button"][tabindex="0"]');
            for (const item of items) {
                const rect = item.getBoundingClientRect();
                if (rect.width < 80 || rect.height < 80 || rect.y < 0) continue;

                let hasPlay = false;
                item.querySelectorAll('i, span').forEach(icon => {
                    const t = (icon.textContent || '').trim().toLowerCase();
                    if (t.includes('play_arrow') || t.includes('play_circle')
                        || t === 'play_arrow' || t === 'play_circle_filled') {
                        hasPlay = true;
                    }
                });
                if (!hasPlay) hasPlay = !!item.querySelector('video');
                if (hasPlay) count++;
            }
            return count;
        }
    """)


def get_video_progress(page: Page) -> str | None:
    """Проверяет, есть ли видео в процессе генерации (с процентом прогресса).

    Возвращает текст прогресса (напр. '28%') или None если все видео готовы.
    """
    return page.evaluate("""
        () => {
            const items = document.querySelectorAll('div[role="button"][tabindex="0"]');
            for (const item of items) {
                const rect = item.getBoundingClientRect();
                if (rect.width < 80 || rect.height < 80 || rect.y < 0) continue;

                // Ищем текст с процентом внутри карточки
                const text = (item.innerText || '').trim();
                const match = text.match(/(\\d+)\\s*%/);
                if (match) return match[0];
            }
            return null;
        }
    """)


def wait_for_video_generation(page: Page, initial_video_count: int,
                               timeout_s: int = 600, poll_s: int = 8) -> bool:
    """Ждёт появления нового видео в галерее И завершения его генерации.

    Два этапа:
    1. Ждём пока count видео увеличится (превью появилось)
    2. Ждём пока исчезнет индикатор прогресса (XX%) — видео готово
    """
    elapsed = 0
    video_appeared = False

    while elapsed < timeout_s:
        time.sleep(poll_s)
        elapsed += poll_s
        mins = elapsed // 60
        secs = elapsed % 60

        current = count_video_items(page)

        if not video_appeared:
            print(f"  ⏳ [{mins}:{secs:02d}] Видео в галерее: {current} (было: {initial_video_count})")
            if current > initial_video_count:
                video_appeared = True
                print(f"  ↳ Превью появилось, жду завершения генерации...")

        if video_appeared:
            progress = get_video_progress(page)
            if progress:
                print(f"  ⏳ [{mins}:{secs:02d}] Генерация: {progress}")
            else:
                print(f"  ✓ Видео готово! (заняло ~{mins} мин {secs} сек)")
                return True

    print(f"  ⚠ Таймаут ({timeout_s // 60} мин) — видео не готово")
    return False


def go_back_to_gallery(page: Page):
    """Возвращается из превью в галерею (кнопка «Назад» или Escape)."""
    back_btn = page.locator('button:has-text("Назад")')
    if back_btn.count() > 0 and back_btn.first.is_visible():
        back_btn.first.click()
        human_sleep(1.5, 2.5)
        print("  ↳ Вернулся в галерею")
        return
    # Fallback: Escape
    page.keyboard.press("Escape")
    human_sleep(1.5, 2.5)


def generate_video_scene(page: Page, scene: VideoScene, output_dir: Path,
                         approved_map: dict[int, Path], state: dict,
                         first_scene: bool = False):
    full_prompt = build_full_prompt(scene)

    approved_path = approved_map.get(scene.index)
    approved_name = approved_path.name if approved_path else None

    print(f"\n{'='*60}")
    print(f"→ Сцена {scene.index}")
    if approved_name:
        print(f"  ★ Выбранный кадр: {approved_name}")
    print(f"  Картинка: {scene.image_path}")
    print(f"  Промпт: {scene.prompt[:80]}...")
    if scene.sounds:
        print(f"  Звуки: {scene.sounds[:80]}...")
    print(f"{'='*60}")

    # Превентивная проверка: не висит ли abuse-диалог от прошлых шагов?
    if detect_abuse_dialog(page):
        state["abuse_count"] = state.get("abuse_count", 0) + 1
        pause_for_abuse_resolution(context=f"перед сценой {scene.index}")

    # ШАГ 1: собираем URL изображений из галереи (до открытия пикера)
    gallery_urls = get_gallery_image_urls(page)
    total_images = len(gallery_urls)
    print(f"  📋 В галерее {total_images} изображений")

    if total_images == 0:
        print("  ⚠ Галерея пуста — выбери изображение вручную.")
        input("     Нажми Enter когда готово... ")
    elif approved_path:
        # Режим approved_images: открываем пикер и автоматически находим
        # визуально совпадающий кадр через pHash.
        print(f"  🖼 Открываю пикер «Первый кадр»...")
        frame_opened = click_first_frame_slot(page)
        if not frame_opened:
            print(f"  👆 Кликни на «Первый кадр» вручную.")
            input("     Когда пикер открылся — нажми Enter... ")
        print(f"  🔍 Автопоиск по pHash (approved: {approved_name})...")
        selected = select_from_picker_by_image(page, approved_path)
        if not selected:
            print(f"  ⚠ Не нашёл автоматически — выбери '{approved_name}' вручную.")
            input(f"     Когда кадр выбран — нажми Enter... ")
    else:
        # Определяем UUID целевого изображения (галерея: newest first, сцена N = total-N)
        target_idx = max(0, min(total_images - scene.index, total_images - 1))
        target_url = gallery_urls[target_idx]
        target_media_id = extract_media_id(target_url)
        print(f"  🎯 Сцена {scene.index} → gallery[{target_idx}] → ID: {target_media_id[:12]}...")

        # ШАГ 2: кликаем «Первый кадр» для открытия пикера
        print(f"  🖼 Открываю пикер «Первый кадр»...")
        frame_opened = click_first_frame_slot(page)
        if not frame_opened:
            print(f"  👆 Кликни на «Первый кадр» вручную.")
            input("     Когда пикер открылся — нажми Enter... ")

        # ШАГ 3: выбираем в пикере по UUID
        selected = select_from_picker(page, target_media_id)
        if not selected:
            print(f"  ⚠ Не удалось выбрать автоматически — выбери картинку сцены {scene.index} вручную.")
            input("     Когда изображение выбрано — нажми Enter... ")

    # ШАГ 4: подтверждение модели (только для первой сцены в батче)
    if first_scene:
        print(f"\n  👆 Убедись что выбрана модель Veo 3.1 и формат 9:16.")
        input("     Нажми Enter когда готово... ")

    # Снимок видео ДО генерации — чтобы потом точно найти НАШЕ новое,
    # даже если параллельно появятся другие (напр., если пользователь
    # тоже что-то генерирует вручную в этой же вкладке).
    videos_before_ids = snapshot_video_ids(page)
    videos_before = len(videos_before_ids)
    print(f"  📊 Видео в галерее до генерации: {videos_before}")

    # Заполняем промпт и запускаем генерацию.
    # click_generate_with_rate_limit_retry ловит транзиентный тост
    # «Вы слишком быстро отправляете запросы» и автоматически повторяет
    # клик после прогрессивного backoff. Если retry исчерпан — пропуск.
    fill_prompt(page, full_prompt)
    if not click_generate_with_rate_limit_retry(page, state):
        print(f"  ⏭  Сцена {scene.index} пропущена из-за rate-limit.")
        return

    print(f"  ⏳ Генерируется видео... (автоматически жду появления)")

    # Автоматически ждём появления нового видео
    appeared = wait_for_video_generation(page, videos_before)
    if not appeared:
        print(f"  ⚠ Видео не появилось автоматически.")
        input("     Когда видео появилось — нажми Enter... ")

    # Кликаем на НАШЕ новое видео (которого не было в snapshot)
    human_sleep(1.0, 2.0)
    opened = open_specific_video(page, videos_before_ids)
    if not opened:
        print(f"  👆 Кликни на сгенерированное видео вручную.")
        input("     Когда превью открыто (видишь кнопку «Скачать») — нажми Enter... ")

    # Скачиваем: Скачать → {DOWNLOAD_QUALITY} (по умолчанию 720p, см. константу выше)
    success = download_video_via_ui(page, output_dir, scene.index, state=state)
    if not success:
        print(f"  ⚠ Скачай видео сцены {scene.index} вручную в {output_dir}")
        input("     Нажми Enter когда скачал... ")

    # Возвращаемся в галерею для следующей сцены
    go_back_to_gallery(page)


def run(markdown_path: Path, scenes_filter: set[int] | None, start_from: int, headless: bool = False, clean_session: bool = False, quality: str = "720p"):
    # quality пишем в модульную глобал, чтобы _do_download_flow читал актуальное
    # значение (он использует DOWNLOAD_QUALITY как module-level константу).
    if quality not in QUALITY_CHOICES:
        print(f"⚠ Неизвестное качество {quality!r}, использую 720p")
        quality = "720p"
    globals()["DOWNLOAD_QUALITY"] = quality
    print(f"🎞  Качество скачивания: {quality}")
    # `headless` оставлен в сигнатуре для обратной совместимости с лаунчерами;
    # в attach-режиме мы не запускаем браузер сами, поэтому флаг не используется.
    del headless
    title, scenes = parse_video_markdown(markdown_path)

    if scenes_filter:
        scenes = [s for s in scenes if s.index in scenes_filter]
    if start_from:
        scenes = [s for s in scenes if s.index >= start_from]

    print(f"🎬 Миф: {title}")
    print(f"📑 Будет обработано сцен: {len(scenes)} (номера: {[s.index for s in scenes]})")

    # Резолвим Flow-проект ДО запуска браузера: если сценарий новый,
    # пользователя спросят flow_id сразу, без лишнего запуска Chromium.
    flow_url = resolve_flow_url(markdown_path)

    scenario_folder = resolve_scenario_folder(markdown_path)
    output_dir = CONTENT_ROOT / scenario_folder / "video"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📂 Видео будут сохраняться в: {output_dir}")

    # Подтягиваем карту финализированных картинок:
    # {1: 'scene_01_v3.jpg', 2: 'scene_02_v2.png', ...}
    # Пользователь увидит в консоли какой именно вариант выбирать в Flow-пикере.
    approved_map = load_approved_images_map(scenario_folder)
    if approved_map:
        print(f"✅ Найдено {len(approved_map)} отобранных кадров в approved_images/")
    else:
        print(f"⚠ approved_images/ пуста — выбор картинок будет по индексу галереи")

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    # Per-run state. Сейчас используется только для счётчика abuse-хитов:
    # после первого срабатывания «unusual activity» все паузы между сценами
    # удваиваются — единственный честный сигнал «я человек» в этом режиме
    # резко снизить cadence до конца прогона.
    state: dict = {"abuse_count": 0}

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
        # Attach-режим: подключаемся к Chrome который пользователь запустил
        # сам через launch_chrome_debug.bat. Chrome user-launched — значит
        # navigator.webdriver=false, нет --enable-automation, чистый
        # fingerprint. Скрипт не управляет запуском браузера, только
        # действиями внутри него.
        #
        # Если Chrome-debug ещё не поднят — сами запустим launch_chrome_debug.bat
        # и подождём CDP-порта. Single-click UX такой же как у imagefx.
        if not ensure_debug_chrome(max_wait_sec=60):
            print("\n❌ Chrome-debug не стартовал за 60 сек.")
            print("   Попробуй запустить automation/launch_chrome_debug.bat вручную.")
            sys.exit(1)

        browser, page = None, None
        for attempt in range(10):
            browser, page = attach_and_find(p, verbose=False)
            if browser is not None:
                break
            time.sleep(1)

        if page is None:
            print(f"\n❌ Не удалось найти вкладку Flow после CDP-attach.")
            print("\n🛠  Залогинься в Google в открывшемся Chrome и открой Flow-проект:")
            print(f"      {flow_url}")
            print("   Потом запусти скрипт ещё раз.\n")
            sys.exit(1)
        # После успешного attach flow_url больше не используется —
        # скрипт работает с той вкладкой которая уже открыта.
        del flow_url

        print(f"🔗 Подключён к Chrome, вкладка Flow найдена:")
        print(f"   {page.url[:80]}...")
        page.bring_to_front()

        print("\n⏸  Убедись что проект полностью загрузился, галерея видна.")
        input("   Нажми Enter для старта... ")

        # Сразу после Enter — на всякий случай убеждаемся что вкладка
        # всё ещё жива (юзер мог что-то закрыть пока логинился/ждал).
        page = ensure_page_alive(p, page)
        if page is None:
            print("❌ Не смог привязаться к вкладке Flow. Закрываю.")
            sys.exit(1)

        # Стабилизация после возможной навигации
        print("⏱  Жду 3 сек стабилизации страницы...")
        time.sleep(3)
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass

        for i, scene in enumerate(scenes):
            # Перед каждой сценой проверяем что вкладка жива.
            # Flow может сам закрыть/перегрузить вкладку при abuse-лимите
            # или при длинной неактивности — тогда переподключаемся.
            page = ensure_page_alive(p, page)
            if page is None:
                print("❌ Flow-вкладка окончательно потеряна. Выход.")
                break

            try:
                generate_video_scene(page, scene, output_dir, approved_map,
                                     state, first_scene=(i == 0))
            except Exception as e:
                print(f"  ✗ Ошибка на сцене {scene.index}: {e}")

            if i < len(scenes) - 1:
                # Между генерацией и паузой — «посмотреть, что получилось»
                look_at_results(page)

                # Обычная пауза 90-180 сек. После первого abuse-хита
                # ИЛИ rate-limit-тоста всё удваиваем — Flow явно
                # подозревает сессию, и единственный честный способ
                # отбиться — резко снизить cadence.
                bumped = state.get("abuse_count", 0) > 0 or state.get("rate_limit_count", 0) > 0
                multiplier = 2.0 if bumped else 1.0
                pause = random.uniform(90, 180) * multiplier
                note = " (×2 после abuse/rate-limit)" if multiplier > 1 else ""
                print(f"  💤 Пауза {int(pause)} сек перед следующей сценой{note}...")
                idle_like_human(page, pause)

        print(f"\n✅ Готово. Видео в: {output_dir}")
        # Не закрываем Chrome — это процесс пользователя, запущенный
        # через launch_chrome_debug.bat. Пусть остаётся для следующего
        # запуска (не надо заново логиниться).
        print("   Chrome оставлен открытым — можно запустить скрипт снова.")


def parse_scenes_arg(value: str) -> set[int]:
    return {int(x.strip()) for x in value.split(",") if x.strip()}


def main():
    parser = argparse.ArgumentParser(description="Генерация видео в Google Flow по сценам из video.md.")
    parser.add_argument("markdown", type=Path, help="Путь к video.md файлу со сценами")
    parser.add_argument("--scenes", type=str, default=None, help="Номера сцен через запятую, напр. 1,2,3")
    parser.add_argument("--from", dest="start_from", type=int, default=0, help="Начать с сцены N")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--clean-session",
        action="store_true",
        help="Очистить cookies/Local Storage/Cache Google перед запуском (придётся логиниться заново)",
    )
    parser.add_argument(
        "--quality",
        choices=QUALITY_CHOICES,
        default="720p",
        help="Качество скачиваемого mp4 из Flow (720p или 1080p, дефолт 720p)",
    )
    args = parser.parse_args()

    if not args.markdown.exists():
        print(f"❌ Файл не найден: {args.markdown}")
        sys.exit(1)

    scenes_filter = parse_scenes_arg(args.scenes) if args.scenes else None
    run(
        args.markdown,
        scenes_filter,
        args.start_from,
        headless=args.headless,
        clean_session=args.clean_session,
        quality=args.quality,
    )


if __name__ == "__main__":
    main()
