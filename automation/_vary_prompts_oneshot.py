"""Одноразовая утилита: раскидывает варианты стилевого каркаса по
сценам внутри prompts/images.md. Меняет только обёртку (первая фраза и
последняя фраза каждого промпта), содержательную часть не трогает.

Запуск: python automation/_vary_prompts_oneshot.py "<путь к images.md>"

Можно безопасно запускать несколько раз — детектит уже-варьированные
промпты и пропускает.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

OPENING_DEFAULT = "highly detailed pixel art, 9:16 vertical,"
CLOSING_DEFAULT = ", modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement"

OPENING_VARIANTS = [
    "highly detailed pixel art, 9:16 vertical,",
    "9:16 vertical pixel art frame, richly detailed,",
    "richly detailed pixel art in 9:16 vertical composition,",
    "cinematic 9:16 vertical pixel art, finely detailed,",
    "finely detailed pixel art, vertical 9:16 frame,",
    "9:16 vertical composition rendered in highly detailed pixel art,",
]

CLOSING_VARIANTS = [
    ", modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement",
    ", rendered in modern detailed pixel art with warm cinematic light, no letters or text visible, no camera movement",
    ", warm cinematic lighting and modern detailed pixel art treatment, no text or letters, no camera movement",
    ", modern pixel art finish with warm cinematic glow, no letters, no text on screen, no camera movement",
    ", crisp modern pixel art rendering with warm cinematic light, no text, no letters, no camera motion",
    ", warm cinematic light in a modern detailed pixel art style, no letters, no text, no camera movement",
]

# Замаппено вручную — каждая сцена получает уникальную пару (opening, closing).
# Соседние сцены не должны иметь одинаковую пару, чтобы не было локального
# паттерна. Цикл с шагом 7 для openings и 11 для closings даёт максимальный
# разброс на 21 сцене.
def assignment_for(scene_num: int) -> tuple[int, int]:
    o = (scene_num * 7 + 3) % len(OPENING_VARIANTS)
    c = (scene_num * 11 + 5) % len(CLOSING_VARIANTS)
    return o, c


SCENE_BLOCK_RE = re.compile(
    r"^(##\s+Сцена\s+(\d+)[^\n]*\n.*?)(?=^##\s+Сцена\s+\d+|\Z)",
    re.MULTILINE | re.DOTALL,
)
PROMPT_LINE_RE = re.compile(r"(\*\*Промпт:\*\*\s*)(.+)$", re.MULTILINE)


def vary_one_prompt(prompt_text: str, opening_idx: int, closing_idx: int) -> tuple[str, bool]:
    """Возвращает (новая_строка_промпта, было_изменение)."""
    text = prompt_text.rstrip()

    new_opening = OPENING_VARIANTS[opening_idx]
    new_closing = CLOSING_VARIANTS[closing_idx]

    changed = False

    # 1. Меняем открытие если оно — дефолтное
    if text.startswith(OPENING_DEFAULT):
        text = new_opening + text[len(OPENING_DEFAULT):]
        changed = True
    else:
        # Уже варьировано — проверим, что начало совпадает с одним из
        # вариантов; если нет — оставляем как есть, чтобы не сломать
        # ручные правки.
        if not any(text.startswith(v) for v in OPENING_VARIANTS):
            print(f"    ⚠ открытие не распознано — пропускаю: {text[:60]}…")

    # 2. Меняем закрытие если оно — дефолтное
    if text.endswith(CLOSING_DEFAULT):
        text = text[:-len(CLOSING_DEFAULT)] + new_closing
        changed = True
    else:
        if not any(text.endswith(v) for v in CLOSING_VARIANTS):
            print(f"    ⚠ закрытие не распознано — пропускаю: …{text[-60:]}")

    return text, changed


def process(md_path: Path) -> None:
    src = md_path.read_text(encoding="utf-8")

    changes = 0
    untouched = 0

    def repl_block(m: re.Match) -> str:
        nonlocal changes, untouched
        block = m.group(1)
        scene_num = int(m.group(2))
        opening_idx, closing_idx = assignment_for(scene_num)

        def repl_prompt(pm: re.Match) -> str:
            nonlocal changes, untouched
            prefix = pm.group(1)
            current = pm.group(2)
            new_text, was_changed = vary_one_prompt(current, opening_idx, closing_idx)
            if was_changed:
                changes += 1
                print(f"  ✓ Сцена {scene_num:2d}: opening V{opening_idx + 1}, closing C{closing_idx + 1}")
            else:
                untouched += 1
            return prefix + new_text

        new_block = PROMPT_LINE_RE.sub(repl_prompt, block, count=1)
        return new_block

    new_src = SCENE_BLOCK_RE.sub(repl_block, src)

    if new_src == src:
        print("  Нет изменений (возможно, файл уже варьирован).")
        return

    md_path.write_text(new_src, encoding="utf-8")
    print(f"\n✅ Готово: {changes} промптов варьировано, {untouched} нетронуто.")
    print(f"   Файл перезаписан: {md_path}")


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python _vary_prompts_oneshot.py <path/to/images.md>")
        sys.exit(2)
    md = Path(sys.argv[1])
    if not md.exists():
        print(f"❌ Файл не найден: {md}")
        sys.exit(1)
    process(md)


if __name__ == "__main__":
    main()
