"""CLI: раскатать папочную структуру и шаблоны промптов для нового мифа.

Используется на шаге 2 пайплайна (см. CONTEXT.md → «Пайплайн создания
ролика»). Один источник правды с webapp — оба зовут одну функцию из
`automation/scenario_scaffold.py`.

Использование:

    python automation/create_scenario.py "Персефона и Аид"

Если имя не передано аргументом — попросит ввести интерактивно.

Имя папки = точное название мифа на русском, с заглавных букв, через
пробел, без подчёркиваний. То же имя пойдёт в финальный файл
`content/<Имя>/final/<Имя>.mp4`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Добавляем корень репозитория в sys.path чтобы импорт работал из любой папки
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from automation.scenario_scaffold import (
    ScenarioExistsError,
    create_scenario,
    validate_scenario_name,
)

CONTENT_DIR = ROOT / "content"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Раскатать структуру нового сценария в content/<Имя>/",
    )
    parser.add_argument(
        "name",
        nargs="?",
        help='Точное русское название мифа, например "Персефона и Аид". '
        "Если опущено — попросит ввести интерактивно.",
    )
    args = parser.parse_args()

    name = args.name
    if not name:
        try:
            name = input("Название мифа (например, «Персефона и Аид»): ").strip()
        except EOFError:
            print("ERROR: имя не передано", file=sys.stderr)
            return 2

    ok, err = validate_scenario_name(name)
    if not ok:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2

    name = name.strip()

    try:
        created = create_scenario(name, CONTENT_DIR, root=ROOT)
    except ScenarioExistsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print(
            f"       Если хотите перезалить шаблоны — сначала удалите\n"
            f"       папку content/{name}/ или переименуйте её.",
            file=sys.stderr,
        )
        return 1

    print(f"Сценарий «{name}» создан: {len(created)} путей")
    for p in created:
        print(f"  {p}")
    print()
    print("Дальше по пайплайну:")
    print(f"  1. Написать сценарий в content/{name}/prompts/voiceover.md")
    print(f"     (хук → титул → основной текст; см. CONTEXT.md)")
    print(f"  2. Разбить на предложения в content/{name}/voiceover/texts/sentence_NNN.txt")
    print(f"  3. Запустить генерацию озвучки через webapp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
