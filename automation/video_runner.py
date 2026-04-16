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
import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

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
# Flow-проекты: имя_сценария → flow_id
# Перед запуском нового проекта — добавь строку с его flow_id.
# flow_id берётся из URL: labs.google/fx/.../flow/project/<flow_id>
# ──────────────────────────────────────────────────────────────────
FLOW_PROJECTS: dict[str, str] = {
    "икар_и_дедал": "7bd82873-3936-4fc2-8687-f4284b363c1f",
    # "новый_сценарий": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
}

FLOW_BASE_URL = "https://labs.google/fx/ru/tools/flow/project"
PROFILE_DIR = Path(__file__).parent / ".browser_profile"
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_ROOT = PROJECT_ROOT / "output"

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


def random_mouse_wander(page: Page):
    for _ in range(random.randint(2, 4)):
        x = random.randint(200, 1200)
        y = random.randint(200, 700)
        page.mouse.move(x, y, steps=random.randint(8, 20))
        time.sleep(random.uniform(0.1, 0.3))


GALLERY_IMG_SELECTOR = 'img[alt="Сгенерированное изображение"]'
# Слот «Первый кадр» — div 50x50 cursor:pointer в видео-панели
FIRST_FRAME_SLOT_TEXT = "Первый кадр"


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
    """Собирает URL всех изображений из главной галереи (до открытия пикера)."""
    return page.evaluate("""
        () => Array.from(document.querySelectorAll('img[alt="Сгенерированное изображение"]'))
            .map(img => img.src)
    """)


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


def download_video_via_ui(page: Page, output_dir: Path, scene_index: int) -> bool:
    """Скачивает видео из открытого превью: Скачать → 1080p."""

    # Кликаем «Скачать»
    dl_btn = page.locator('button:has-text("Скачать")')
    try:
        dl_btn.first.wait_for(state="visible", timeout=5_000)
        dl_btn.first.click()
        human_sleep(0.5, 1.0)
        print("  ↳ Кликнул «Скачать»")
    except Exception as e:
        print(f"  ⚠ Кнопка «Скачать» не найдена: {e}")
        return False

    # Кликаем «1080p» и ловим скачивание
    try:
        with page.expect_download(timeout=120_000) as download_info:
            q_btn = page.get_by_text("1080p")
            q_btn.first.wait_for(state="visible", timeout=5_000)
            q_btn.first.click()
            print("  ↳ Кликнул «1080p», жду скачивания...")

        download = download_info.value
        out_path = output_dir / f"scene_{scene_index:02d}_v1.mp4"
        download.save_as(str(out_path))
        size_mb = out_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ Скачано: {out_path.name} ({size_mb:.1f} МБ)")
        return True
    except Exception as e:
        print(f"  ⚠ Ошибка скачивания: {e}")
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
                         first_scene: bool = False):
    full_prompt = build_full_prompt(scene)

    print(f"\n{'='*60}")
    print(f"→ Сцена {scene.index}")
    print(f"  Картинка: {scene.image_path}")
    print(f"  Промпт: {scene.prompt[:80]}...")
    if scene.sounds:
        print(f"  Звуки: {scene.sounds[:80]}...")
    print(f"{'='*60}")

    # ШАГ 1: собираем URL изображений из галереи (до открытия пикера)
    gallery_urls = get_gallery_image_urls(page)
    total_images = len(gallery_urls)
    print(f"  📋 В галерее {total_images} изображений")

    if total_images == 0:
        print("  ⚠ Галерея пуста — выбери изображение вручную.")
        input("     Нажми Enter когда готово... ")
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

    # Считаем видео ДО генерации
    videos_before = count_video_items(page)
    print(f"  📊 Видео в галерее до генерации: {videos_before}")

    # Заполняем промпт и запускаем генерацию
    fill_prompt(page, full_prompt)
    click_generate(page)

    print(f"  ⏳ Генерируется видео... (автоматически жду появления)")

    # Автоматически ждём появления нового видео
    appeared = wait_for_video_generation(page, videos_before)
    if not appeared:
        print(f"  ⚠ Видео не появилось автоматически.")
        input("     Когда видео появилось — нажми Enter... ")

    # Кликаем на видео → открываем превью
    human_sleep(1.0, 2.0)
    opened = open_generated_video(page)
    if not opened:
        print(f"  👆 Кликни на сгенерированное видео вручную.")
        input("     Когда превью открыто (видишь кнопку «Скачать») — нажми Enter... ")

    # Скачиваем: Скачать → 1080p
    success = download_video_via_ui(page, output_dir, scene.index)
    if not success:
        print(f"  ⚠ Скачай видео сцены {scene.index} вручную в {output_dir}")
        input("     Нажми Enter когда скачал... ")

    # Возвращаемся в галерею для следующей сцены
    go_back_to_gallery(page)


def resolve_flow_url(markdown_path: Path) -> str:
    """Определяет Flow URL по имени папки сценария или через ввод пользователя."""
    # Имя папки сценария (напр. "икар_и_дедал")
    project_key = markdown_path.parent.name.lower()
    if project_key in FLOW_PROJECTS:
        flow_id = FLOW_PROJECTS[project_key]
        print(f"🔗 Flow-проект: {project_key} → {flow_id}")
        return f"{FLOW_BASE_URL}/{flow_id}"

    # Неизвестный проект — просим ввести flow_id
    print(f"⚠ Проект «{project_key}» не найден в FLOW_PROJECTS.")
    print("  Добавь его в словарь FLOW_PROJECTS в начале video_runner.py")
    print("  или введи flow_id сейчас (из URL Flow-проекта):")
    flow_id = input("  flow_id: ").strip()
    if not flow_id:
        raise ValueError("flow_id не указан — невозможно продолжить")
    return f"{FLOW_BASE_URL}/{flow_id}"


def run(markdown_path: Path, scenes_filter: set[int] | None, start_from: int, headless: bool = False):
    title, scenes = parse_video_markdown(markdown_path)

    if scenes_filter:
        scenes = [s for s in scenes if s.index in scenes_filter]
    if start_from:
        scenes = [s for s in scenes if s.index >= start_from]

    print(f"🎬 Миф: {title}")
    print(f"📑 Будет обработано сцен: {len(scenes)} (номера: {[s.index for s in scenes]})")

    slug = slugify(title)
    output_dir = OUTPUT_ROOT / slug / "video"
    output_dir.mkdir(parents=True, exist_ok=True)

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            accept_downloads=True,
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

        flow_url = resolve_flow_url(markdown_path)
        print("\n🌐 Открываю Flow-проект")
        page.goto(flow_url, timeout=PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")

        print("\n⏸  Дождись полной загрузки проекта.")
        input("   Нажми Enter для старта... ")

        for i, scene in enumerate(scenes):
            try:
                generate_video_scene(page, scene, output_dir, first_scene=(i == 0))
            except Exception as e:
                print(f"  ✗ Ошибка на сцене {scene.index}: {e}")

            if i < len(scenes) - 1:
                pause = random.uniform(30, 60)
                print(f"  💤 Пауза {int(pause)} сек перед следующей сценой...")
                time.sleep(pause)
                random_mouse_wander(page)

        print(f"\n✅ Готово. Видео в: {output_dir}")
        input("Нажми Enter для закрытия браузера... ")
        context.close()


def parse_scenes_arg(value: str) -> set[int]:
    return {int(x.strip()) for x in value.split(",") if x.strip()}


def main():
    parser = argparse.ArgumentParser(description="Генерация видео в Google Flow по сценам из video.md.")
    parser.add_argument("markdown", type=Path, help="Путь к video.md файлу со сценами")
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
