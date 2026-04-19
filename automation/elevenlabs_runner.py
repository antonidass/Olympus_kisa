"""
ElevenLabs Runner — автоматизация озвучки voiceover.md через ElevenLabs TTS.

Читает voiceover.md, разбивает текст на ПРЕДЛОЖЕНИЯ (не на части!), по очереди
вставляет каждое в поле ввода на elevenlabs.io/app/speech-synthesis, жмёт
Generate, ждёт генерации и скачивает mp3. Каждое предложение озвучивается
целиком — чтобы интонация не ломалась посередине фразы.

Использование:
    python automation/elevenlabs_runner.py content/сизиф/prompts/voiceover.md
    python automation/elevenlabs_runner.py content/сизиф/prompts/voiceover.md --from 3
    python automation/elevenlabs_runner.py content/сизиф/prompts/voiceover.md --sentences 1,2,5

Куда сохраняется:
    content/<миф>/voiceover/audio/sentence_001.mp3
    content/<миф>/voiceover/audio/sentence_002.mp3
    ...

После окончания файлы нужно ВРУЧНУЮ пересопоставить со сценами и
переименовать в scene_NN.mp3 / scene_NN_XX.mp3.

Первый запуск:
    - Откроется браузер с elevenlabs.io → залогинься.
    - Сессия сохранится в automation/.browser_profile (общая с imagefx_runner).
    - В следующие разы логиниться не нужно.
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

# Импорт playwright откладываем — чтобы --dry-run работал без установленного пакета.
try:
    from playwright.sync_api import Page, sync_playwright  # type: ignore
except ImportError:
    Page = None  # type: ignore
    sync_playwright = None  # type: ignore

# Таймштамп перед каждой строкой лога.
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


ELEVENLABS_URL = "https://elevenlabs.io/app/speech-synthesis/text-to-speech"
PROFILE_DIR = Path(__file__).parent / ".browser_profile"
CONTENT_ROOT = Path(__file__).parent.parent / "content"

PAGE_LOAD_TIMEOUT = 60_000
GENERATION_TIMEOUT = 180  # сек — у ElevenLabs обычно 5-30 сек на фразу

# Селекторы — могут меняться, если ElevenLabs обновит UI.
# Текстовое поле — на ElevenLabs это textarea.
TEXT_INPUT_SELECTORS = [
    'textarea[data-testid*="input"]',
    'textarea[placeholder*="Start typing"]',
    'textarea[placeholder*="text"]',
    'div[contenteditable="true"][role="textbox"]',
    "textarea",
]
# Главная кнопка действия — одна и та же: сначала "Generate speech",
# после первой генерации "Regenerate speech". Ищем по обоим текстам.
ACTION_BUTTON_SELECTORS = [
    'button:has-text("Regenerate speech")',
    'button:has-text("Generate speech")',
    'button:has-text("Generate")',
]
# Кнопка скачивания — иконка-стрелка рядом со счётчиком символов.
# ElevenLabs использует SVG без явной aria-label, поэтому ищем по разным признакам.
DOWNLOAD_BUTTON_SELECTORS = [
    'button[aria-label*="Download" i]',
    'button[aria-label*="Скачать" i]',
    'button[data-testid*="download" i]',
    'button:has(svg[data-lucide="download"])',
    # Fallback: кнопка-иконка рядом с "Regenerate speech" — обычно это download.
    'button:near(:text("Regenerate speech"))',
]

# Сколько вариантов озвучки на одно предложение (включая первую генерацию).
# У ElevenLabs 3 варианта бесплатно, 4-й платный.
VARIANTS_PER_SENTENCE = 3

# Stealth — убираем признаки автоматизации.
STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en-US', 'en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
window.chrome = window.chrome || { runtime: {} };
"""


@dataclass
class Sentence:
    index: int
    text: str


def split_sentences(text: str) -> list[str]:
    """Разбивает сырой текст на предложения.

    Правила:
    - Разбиваем по терминальной пунктуации (. ! ? …) — но СОХРАНЯЕМ знак в предложении.
    - Кавычки «ёлочки» и прямая речь остаются внутри предложения.
    """
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    pattern = re.compile(r".+?[.!?…]+[»\"')\]]*(?:\s+|$)", re.DOTALL)
    raw = [m.group(0).strip() for m in pattern.finditer(text)]
    matched_total = sum(len(s) for s in raw) + len(raw)
    if matched_total < len(text):
        tail = text[matched_total:].strip()
        if tail:
            raw.append(tail)
    return [s for s in raw if s]


def parse_voiceover(path: Path) -> list[Sentence]:
    """Парсит voiceover.md в список предложений для озвучки.

    Особенность: ПЕРВАЯ строка файла (например, «Сизи́ф. Миф за минуту.»)
    считается титульной и озвучивается ОДНИМ запросом, даже если содержит
    несколько предложений с точками. Это исключение из правила «одно
    предложение = один mp3» — интро читается слитно, как единая фраза.
    """
    content = path.read_text(encoding="utf-8")
    # Отсекаем markdown-заголовки `# Название` — они не читаются.
    content = re.sub(r"^#.*$", "", content, flags=re.MULTILINE)

    # Первая непустая строка — интро. Берём её целиком.
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    if not lines:
        return []
    intro = lines[0]
    rest = "\n".join(lines[1:])

    sentences: list[str] = [intro]
    sentences.extend(split_sentences(rest))
    return [Sentence(index=i, text=s) for i, s in enumerate(sentences, start=1)]


def human_sleep(min_s: float, max_s: float):
    time.sleep(random.uniform(min_s, max_s))


def human_type(page: Page, text: str):
    """Человеческая скорость печати, но чуть быстрее чем в imagefx."""
    for ch in text:
        page.keyboard.type(ch)
        if ch == " " and random.random() < 0.1:
            time.sleep(random.uniform(0.1, 0.25))
        else:
            time.sleep(random.uniform(0.02, 0.06))


def first_visible(page: Page, selectors: list[str], timeout: float = 10_000):
    """Возвращает первый видимый локатор из списка вариантов."""
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        for sel in selectors:
            loc = page.locator(sel).first
            try:
                if loc.is_visible(timeout=500):
                    return loc
            except Exception:
                continue
        time.sleep(0.2)
    raise TimeoutError(f"Ни один из селекторов не стал видимым: {selectors}")


def fill_text(page: Page, text: str):
    field = first_visible(page, TEXT_INPUT_SELECTORS, timeout=15_000)
    field.click()
    human_sleep(0.3, 0.7)
    # Очищаем поле полностью.
    page.keyboard.press("Control+A")
    human_sleep(0.1, 0.3)
    page.keyboard.press("Delete")
    human_sleep(0.2, 0.5)
    human_type(page, text)
    human_sleep(0.5, 1.0)


def find_action_button(page: Page):
    """Возвращает главную кнопку действия (Generate/Regenerate speech)."""
    return first_visible(page, ACTION_BUTTON_SELECTORS, timeout=15_000)


def click_action(page: Page):
    btn = find_action_button(page)
    for _ in range(15):
        if btn.is_enabled():
            break
        time.sleep(0.3)
    btn.click()


def wait_for_generation_complete(page: Page, timeout_sec: int):
    """Ждёт завершения генерации.

    Логика: после клика кнопка "Regenerate speech" на короткое время становится
    disabled / меняет текст. Когда она снова enabled и содержит "speech" —
    генерация завершена.

    Сначала ждём пока она войдёт в loading-состояние (disabled), потом ждём
    пока выйдет из него.
    """
    btn = find_action_button(page)

    # 1. Ждём пока кнопка войдёт в loading (disabled) — даём 3 сек.
    loading_deadline = time.time() + 3
    while time.time() < loading_deadline:
        try:
            if not btn.is_enabled():
                break
        except Exception:
            pass
        time.sleep(0.15)

    # 2. Ждём пока кнопка снова станет enabled.
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            # Пересоздаём локатор — UI мог перерисоваться.
            btn = find_action_button(page)
            if btn.is_enabled():
                # Короткая задержка чтобы audio успел подгрузиться.
                time.sleep(1.2)
                return
        except Exception:
            pass
        time.sleep(0.4)
    raise TimeoutError("Генерация не завершилась за отведённое время")


def find_download_button(page: Page):
    """Ищет кнопку скачивания (иконка-стрелка рядом со счётчиком символов).

    На ElevenLabs кнопка обычно без явной aria-label, поэтому ищем по разным
    признакам. Возвращает первую видимую.
    """
    for sel in DOWNLOAD_BUTTON_SELECTORS:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=500):
                return loc
        except Exception:
            continue
    # Fallback: ищем любую кнопку с SVG и классом, содержащим "download".
    try:
        fallback = page.locator('button:has(svg)').filter(
            has=page.locator('[class*="download" i], [data-lucide="download"]')
        ).first
        if fallback.is_visible(timeout=500):
            return fallback
    except Exception:
        pass
    raise TimeoutError("Не нашёл кнопку Download")


def download_current_audio(page: Page, out_path: Path):
    """Кликает Download и сохраняет mp3 в out_path."""
    btn = find_download_button(page)
    with page.expect_download(timeout=30_000) as dl_info:
        btn.click()
    dl_info.value.save_as(str(out_path))
    print(f"    ✓ {out_path.name}  ({out_path.stat().st_size // 1024} КБ)")


def generate_three_variants(page: Page, sentence: Sentence, output_dir: Path) -> None:
    """Генерирует 3 варианта озвучки одного предложения.

    Шаги:
    1. Вставить текст, кликнуть Generate/Regenerate speech → ждать завершения → скачать v1.
    2. Ещё раз кликнуть Regenerate speech → скачать v2.
    3. Ещё раз → скачать v3.
    4-й раз не делаем — у ElevenLabs платный.

    Каждое предложение получает свою папку:
        <audio>/sentence_001/sentence_001_v1.mp3
        <audio>/sentence_001/sentence_001_v2.mp3
        <audio>/sentence_001/sentence_001_v3.mp3

    Завершение детектим по состоянию главной кнопки (enabled/disabled),
    а не по новым кнопкам Download — в ElevenLabs один плеер и одна
    кнопка download, которая всегда скачивает последнюю озвучку.
    """
    sentence_dir = output_dir / f"sentence_{sentence.index:03d}"
    sentence_dir.mkdir(parents=True, exist_ok=True)

    # ——— Вариант 1 ———
    fill_text(page, sentence.text)
    click_action(page)
    print(f"  ⏳ Вариант 1: жду завершения (до {GENERATION_TIMEOUT} сек)...")
    try:
        wait_for_generation_complete(page, GENERATION_TIMEOUT)
    except TimeoutError:
        print("  ⚠ Первая генерация не завершилась — пропускаю это предложение.")
        return
    try:
        download_current_audio(page, sentence_dir / f"sentence_{sentence.index:03d}_v1.mp3")
    except Exception as e:
        print(f"  ⚠ Не удалось скачать вариант 1: {e}")

    # ——— Варианты 2 и 3 ———
    for variant in (2, 3):
        human_sleep(1.0, 2.0)
        try:
            click_action(page)
        except Exception as e:
            print(f"  ⚠ Не нашёл кнопку для варианта {variant}: {e}")
            break
        print(f"  ⏳ Вариант {variant}: жду завершения (до {GENERATION_TIMEOUT} сек)...")
        try:
            wait_for_generation_complete(page, GENERATION_TIMEOUT)
        except TimeoutError:
            print(f"  ⚠ Вариант {variant} не завершился — останавливаюсь.")
            break
        try:
            download_current_audio(page, sentence_dir / f"sentence_{sentence.index:03d}_v{variant}.mp3")
        except Exception as e:
            print(f"  ⚠ Не удалось скачать вариант {variant}: {e}")


def run(
    voiceover_path: Path,
    sentences_filter: set[int] | None,
    start_from: int,
    headless: bool,
):
    sentences = parse_voiceover(voiceover_path)
    if not sentences:
        print(f"❌ Не нашёл ни одного предложения в {voiceover_path}")
        sys.exit(1)

    if sentences_filter:
        sentences = [s for s in sentences if s.index in sentences_filter]
    if start_from:
        sentences = [s for s in sentences if s.index >= start_from]

    # Папка: content/<миф>/voiceover/audio/
    myth_dir = voiceover_path.parent.parent  # .../<миф>/
    output_dir = myth_dir / "voiceover" / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📖 Voiceover: {voiceover_path}")
    print(f"📑 Будет озвучено предложений: {len(sentences)}")
    for s in sentences[:5]:
        print(f"   [{s.index:03d}] {s.text[:80]}{'...' if len(s.text) > 80 else ''}")
    if len(sentences) > 5:
        print(f"   ... и ещё {len(sentences) - 5}")
    print(f"📂 Папка сохранения: {output_dir}")

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        # channel="chrome" — используем установленный Google Chrome вместо
        # Playwright-Chromium «для тестирования». Google OAuth не работает
        # в тестовой сборке, поэтому для входа через Google нужен реальный Chrome.
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            channel="chrome",
            headless=headless,
            viewport={"width": 1400, "height": 900},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            accept_downloads=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        context.add_init_script(STEALTH_INIT_SCRIPT)

        page = context.pages[0] if context.pages else context.new_page()

        print("\n🌐 Открываю ElevenLabs TTS...")
        page.goto(ELEVENLABS_URL, timeout=PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")

        print("\n⏸  Проверь окно браузера:")
        print("   - Если нужен логин — залогинься (профиль сохранится).")
        print("   - Выбери нужный голос, модель и настройки стабильности.")
        print("   - Убедись что видно поле ввода и кнопку Generate.")
        input("   Нажми Enter для старта озвучки... ")

        for i, s in enumerate(sentences):
            print(f"\n→ Предложение {s.index}/{len(sentences)}: {s.text[:70]}{'...' if len(s.text) > 70 else ''}")
            try:
                generate_three_variants(page, s, output_dir)
            except Exception as e:
                print(f"  ✗ Ошибка на предложении {s.index}: {e}")
                shot = output_dir / f"sentence_{s.index:03d}_error.png"
                try:
                    page.screenshot(path=str(shot), full_page=True)
                    print(f"    📸 Скриншот: {shot.name}")
                except Exception:
                    pass

            # Пауза между предложениями — поменьше чем у ImageFX,
            # но не нулевая чтобы не выглядеть как бот.
            if i < len(sentences) - 1:
                pause = random.uniform(3, 7)
                print(f"  💤 Пауза {pause:.1f} сек...")
                time.sleep(pause)

        print(f"\n✅ Готово. Файлы в: {output_dir}")
        print("   Дальше вручную пересопоставь предложения со сценами и переименуй в scene_NN.mp3.")
        input("Нажми Enter для закрытия браузера... ")
        context.close()


def parse_sentences_arg(value: str) -> set[int]:
    return {int(x.strip()) for x in value.split(",") if x.strip()}


def main():
    parser = argparse.ArgumentParser(
        description="Озвучка voiceover.md через ElevenLabs TTS — по предложению на файл."
    )
    parser.add_argument("voiceover", type=Path, help="Путь к voiceover.md")
    parser.add_argument("--sentences", type=str, default=None, help="Номера через запятую, напр. 1,2,5")
    parser.add_argument("--from", dest="start_from", type=int, default=0, help="Начать с предложения N")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Только распечатать предложения, без браузера")
    args = parser.parse_args()

    if not args.voiceover.exists():
        print(f"❌ Файл не найден: {args.voiceover}")
        sys.exit(1)

    if args.dry_run:
        sentences = parse_voiceover(args.voiceover)
        print(f"📑 Всего предложений: {len(sentences)}\n")
        for s in sentences:
            print(f"[{s.index:03d}] {s.text}")
        return

    sentences_filter = parse_sentences_arg(args.sentences) if args.sentences else None
    run(args.voiceover, sentences_filter, args.start_from, headless=args.headless)


if __name__ == "__main__":
    main()
