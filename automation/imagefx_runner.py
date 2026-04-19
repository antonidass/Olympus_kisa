"""
Flow Runner — автоматизация генерации изображений в Google Flow (Nano Banana).

Читает markdown-файл со сценами, открывает Flow-проект в браузере с
сохранённым профилем, по очереди вставляет промпт, ждёт генерации и
скачивает картинки через перехват сетевых ответов.

Использование:
    python automation/imagefx_runner.py scripts/pandora.md
    python automation/imagefx_runner.py scripts/pandora.md --scenes 1,2,3
    python automation/imagefx_runner.py scripts/pandora.md --from 3

Анти-детект:
    - Убран признак navigator.webdriver
    - Текст промпта вставляется через буфер обмена (Ctrl+V)
    - Случайные паузы 10-20 сек между сценами
    - Случайные движения мыши

Если Google всё равно блокирует:
    - Подожди 15-30 минут
    - Запускай батчами по 2-3 сцены: --scenes 1,2,3 ... --scenes 4,5,6
"""

from __future__ import annotations

import argparse
import builtins
import random
import re
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

# Паттерны URL сгенерированных картинок
IMAGE_URL_PATTERNS = [
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

# Скрипт анти-детекта — убирает navigator.webdriver и т.п.
STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en-US', 'en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
window.chrome = window.chrome || { runtime: {} };
"""


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

    scene_blocks = re.split(r"^##\s+Сцена\s+\d+\s*$", content, flags=re.MULTILINE)[1:]
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


def paste_text(page: Page, text: str):
    """Мгновенная вставка текста в активный contenteditable —
    имитация Ctrl+C/Ctrl+V через clipboard API страницы.

    Используем navigator.clipboard.writeText(...) и отправляем Ctrl+V клавиатурой.
    Для Chrome в persistent-контексте разрешения на clipboard обычно уже даны;
    если нет — делаем fallback через execCommand('insertText').
    """
    try:
        page.evaluate("(t) => navigator.clipboard.writeText(t)", text)
        page.keyboard.press("Control+V")
        return
    except Exception:
        pass
    # Fallback: вставка через execCommand прямо в активный элемент
    try:
        page.evaluate(
            """(t) => {
                const el = document.activeElement;
                if (el && (el.isContentEditable || el.tagName === 'TEXTAREA' || el.tagName === 'INPUT')) {
                    document.execCommand('insertText', false, t);
                }
            }""",
            text,
        )
    except Exception:
        # Последний fallback — Playwright insertText (моментальный, без посимвольных пауз)
        page.keyboard.insert_text(text)


def random_mouse_wander(page: Page):
    """Небольшие случайные движения мыши — имитируем живого юзера."""
    for _ in range(random.randint(2, 4)):
        x = random.randint(200, 1200)
        y = random.randint(200, 700)
        page.mouse.move(x, y, steps=random.randint(8, 20))
        time.sleep(random.uniform(0.1, 0.3))


def fill_prompt(page: Page, prompt: str):
    field = page.locator(PROMPT_SELECTOR).first
    field.wait_for(state="visible", timeout=10_000)
    random_mouse_wander(page)
    field.click()
    human_sleep(0.5, 1.2)
    page.keyboard.press("Control+A")
    human_sleep(0.2, 0.4)
    page.keyboard.press("Delete")
    human_sleep(0.3, 0.6)
    paste_text(page, prompt)
    human_sleep(0.8, 1.5)


def click_generate(page: Page):
    btn = page.locator(GENERATE_BUTTON_SELECTOR).first
    btn.wait_for(state="visible", timeout=5_000)
    for _ in range(10):
        if btn.is_enabled():
            break
        time.sleep(0.3)
    random_mouse_wander(page)
    btn.click()


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

    # Заранее заполняем поле промпта (пока принимать картинки нельзя)
    state["accepting"] = False
    captured.clear()
    fill_prompt(page, scene.prompt)

    # Снимок URL всех картинок, которые уже есть на странице до клика
    existing = snapshot_existing_img_urls(page)
    print(f"  📋 До клика в DOM было {len(existing)} img")
    state["existing_urls"] = existing
    state["accepting"] = True  # теперь listener принимает новые

    click_generate(page)
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


def run(markdown_path: Path, scenes_filter: set[int] | None, start_from: int, headless: bool = False):
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

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    # Буфер для перехваченных image-ответов текущей сцены
    captured: list[dict] = []
    # Per-scene состояние listener'а
    state: dict = {"accepting": False, "existing_urls": set()}

    with sync_playwright() as p:
        # channel="chrome" — используем установленный Google Chrome вместо
        # Playwright-Chromium "для тестирования". Общий persistent-профиль
        # хранит Google-авторизацию и может падать/ломаться в тестовой сборке.
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            channel="chrome",
            headless=headless,
            viewport={"width": 1400, "height": 900},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        context.add_init_script(STEALTH_INIT_SCRIPT)
        try:
            context.grant_permissions(
                ["clipboard-read", "clipboard-write"],
                origin="https://labs.google",
            )
        except Exception as e:
            print(f"⚠ Не удалось выдать clipboard-разрешения: {e}")

        page = context.pages[0] if context.pages else context.new_page()

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

        print("\n🌐 Открываю Flow-проект")
        page.goto(flow_url, timeout=PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")

        print("\n⏸  Дождись полной загрузки проекта (поле ввода должно быть видно).")
        print("   Если недавно была ошибка 'unusual activity' — подожди 15-30 мин перед запуском.")
        input("   Нажми Enter для старта генерации... ")

        for i, scene in enumerate(scenes):
            try:
                generate_scene(page, scene, output_dir, captured, state)
            except Exception as e:
                print(f"  ✗ Ошибка на сцене {scene.index}: {e}")
            finally:
                state["accepting"] = False

            # Пауза между сценами кроме последней
            if i < len(scenes) - 1:
                pause = random.uniform(10, 20)
                print(f"  💤 Пауза {int(pause)} сек перед следующей сценой...")
                time.sleep(pause)
                random_mouse_wander(page)

        print(f"\n✅ Готово. Результаты в: {output_dir}")
        input("Нажми Enter для закрытия браузера... ")
        context.close()


def parse_scenes_arg(value: str) -> set[int]:
    return {int(x.strip()) for x in value.split(",") if x.strip()}


def main():
    parser = argparse.ArgumentParser(description="Генерация изображений в Google Flow по сценам из markdown.")
    parser.add_argument("markdown", type=Path, help="Путь к .md файлу со сценами")
    parser.add_argument("--scenes", type=str, default=None, help="Номера сцен через запятую, напр. 1,2,3")
    parser.add_argument("--from", dest="start_from", type=int, default=0, help="Начать с сцены N")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    if not args.markdown.exists():
        print(f"❌ Файл не найден: {args.markdown}")
        sys.exit(1)

    scenes_filter = parse_scenes_arg(args.scenes) if args.scenes else None
    run(args.markdown, scenes_filter, args.start_from, headless=args.headless)


if __name__ == "__main__":
    main()
