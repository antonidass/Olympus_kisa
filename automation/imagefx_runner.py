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
    - Человеческая скорость печати (50-120 мс/символ)
    - Случайные паузы 30-60 сек между сценами
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

FLOW_URL = "https://labs.google/fx/ru/tools/flow/project/7bd82873-3936-4fc2-8687-f4284b363c1f"
PROFILE_DIR = Path(__file__).parent / ".browser_profile"
OUTPUT_ROOT = Path(__file__).parent.parent / "output"

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


def human_type(page: Page, text: str):
    """Печать с человеческой скоростью и иногда с паузами между словами."""
    for ch in text:
        page.keyboard.type(ch)
        if ch == " " and random.random() < 0.15:
            time.sleep(random.uniform(0.15, 0.4))
        else:
            time.sleep(random.uniform(0.04, 0.12))


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
    human_type(page, prompt)
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

    if not captured:
        print("  ⚠ Сетевой перехват пуст. Пробую fallback через DOM...")
        dom_imgs = fallback_dom_download(page, output_dir, scene.index, state.get("existing_urls", set()))
        if not dom_imgs:
            print("  ⚠ И DOM пустой. Сохраняю скриншот для диагностики.")
            shot = output_dir / f"scene_{scene.index:02d}_fallback.png"
            page.screenshot(path=str(shot), full_page=True)
            print(f"  📸 Скриншот: {shot.name}")
        return

    print(f"  📥 Сохраняю {len(captured)} картинок...")
    for variant_i, item in enumerate(captured, start=1):
        ext = item["ext"]
        out_path = output_dir / f"scene_{scene.index:02d}_v{variant_i}.{ext}"
        try:
            out_path.write_bytes(item["body"])
            print(f"    ✓ {out_path.name}  ({len(item['body'])//1024} КБ)")
        except Exception as e:
            print(f"    ✗ {out_path.name}: {e}")


def fallback_dom_download(page: Page, output_dir: Path, scene_index: int, existing_urls: set[str]) -> int:
    """Забирает новые большие <img> с страницы через fetch() внутри контекста страницы.

    Пропускает картинки, URL которых был в existing_urls до клика «Создать».
    """
    try:
        srcs: list[str] = page.evaluate(
            """() => {
                const out = [];
                document.querySelectorAll('img').forEach(el => {
                    const r = el.getBoundingClientRect();
                    if (r.width < 200 || r.height < 200) return;
                    if (!el.src) return;
                    out.push(el.src);
                });
                return out;
            }"""
        )
    except Exception as e:
        print(f"    ! fallback DOM eval ошибка: {e}")
        return 0

    new_srcs = [s for s in srcs if s not in existing_urls]
    print(f"    📋 DOM: всего {len(srcs)} img, новых (не было до клика) {len(new_srcs)}")

    saved = 0
    for i, src in enumerate(new_srcs, start=1):
        try:
            data = page.evaluate(
                """async (url) => {
                    const r = await fetch(url);
                    if (!r.ok) throw new Error('HTTP ' + r.status);
                    const buf = await r.arrayBuffer();
                    return Array.from(new Uint8Array(buf));
                }""",
                src,
            )
            body = bytes(data)
            if len(body) < MIN_IMAGE_BYTES:
                print(f"    ~ пропущен ({len(body)//1024}КБ, плейсхолдер?) {src[:60]}")
                continue
            out_path = output_dir / f"scene_{scene_index:02d}_dom_v{i}.png"
            out_path.write_bytes(body)
            print(f"    ✓ (DOM) {out_path.name}  ({len(body)//1024} КБ)")
            saved += 1
        except Exception as e:
            print(f"    ✗ fallback fetch {src[:60]}: {e}")
    return saved


def run(markdown_path: Path, scenes_filter: set[int] | None, start_from: int, headless: bool = False):
    title, scenes = parse_markdown(markdown_path)

    if scenes_filter:
        scenes = [s for s in scenes if s.index in scenes_filter]
    if start_from:
        scenes = [s for s in scenes if s.index >= start_from]

    print(f"📖 Миф: {title}")
    print(f"📑 Будет обработано сцен: {len(scenes)} (номера: {[s.index for s in scenes]})")

    output_dir = OUTPUT_ROOT / slugify(title)
    output_dir.mkdir(parents=True, exist_ok=True)

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    # Буфер для перехваченных image-ответов текущей сцены
    captured: list[dict] = []
    # Per-scene состояние listener'а
    state: dict = {"accepting": False, "existing_urls": set()}

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
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
        page.goto(FLOW_URL, timeout=PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")

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

            # Длинная пауза между сценами кроме последней
            if i < len(scenes) - 1:
                pause = random.uniform(30, 60)
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
