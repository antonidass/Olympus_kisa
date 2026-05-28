"""CLI: разовый перенос уже опубликованных мифов в `content/архив/`.

Запускается один раз после внедрения архивного режима. Сканирует все
сценарии, у которых стоит флаг `published` (см. файлы
`webapp/selections/published_<имя>.json`), и физически переносит их
папки в `content/архив/<имя>/`. Selections-файлы переезжают вместе с
мифом (см. `archive_scenario` в `webapp/app.py`).

По умолчанию работает в режиме **dry-run** — печатает план без правок.
Чтобы фактически перенести, передай `--apply`.

Что пропускается:
  • уже архивированные мифы (имя начинается с `архив/`)
  • части сериалов (имя содержит `/` — discovery работает на 2 уровнях,
    архивация серий пока не поддерживается)

Использование:

    python automation/migrate_published_to_archive.py             # dry-run
    python automation/migrate_published_to_archive.py --apply     # фактический перенос
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Импорт из webapp.app — единый источник правды для логики переноса.
# Flask init при импорте дешёвый, listening не запускается.
from webapp.app import (  # noqa: E402
    ARCHIVE_FOLDER_NAME,
    CONTENT_DIR,
    archive_scenario,
    iter_scenarios_by_creation,
    load_published_state,
)


def _collect_candidates() -> tuple[list[str], list[tuple[str, str]]]:
    """Возвращает (для_переноса, пропущенные).

    Пропускаемые — это (имя, причина), чтобы можно было показать пользователю
    почему миф НЕ попал в план миграции."""
    to_move: list[str] = []
    skipped: list[tuple[str, str]] = []
    for entry in iter_scenarios_by_creation(CONTENT_DIR):
        pub = load_published_state(entry.name)
        if not pub.get("published"):
            continue
        if entry.name.startswith(f"{ARCHIVE_FOLDER_NAME}/"):
            skipped.append((entry.name, "уже в архиве"))
            continue
        if "/" in entry.name:
            skipped.append((entry.name, "часть сериала — пропускаем"))
            continue
        to_move.append(entry.name)
    return to_move, skipped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Разово перенести опубликованные мифы в content/архив/",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Фактический перенос. Без флага — только показывает план (dry-run).",
    )
    args = parser.parse_args()

    to_move, skipped = _collect_candidates()

    if not to_move and not skipped:
        print("Опубликованных мифов не найдено — нечего переносить.")
        return 0

    print(f"План миграции (CONTENT_DIR = {CONTENT_DIR}):")
    print(f"  опубликованных к переносу: {len(to_move)}")
    print(f"  пропущено:                  {len(skipped)}")
    print()

    if to_move:
        print("Будут перенесены в content/архив/:")
        for name in to_move:
            print(f"  • {name}")
        print()

    if skipped:
        print("Пропущены:")
        for name, reason in skipped:
            print(f"  • {name}  ({reason})")
        print()

    if not args.apply:
        print("Это dry-run. Запусти с --apply для фактического переноса.")
        return 0

    print("=== Выполняю перенос ===")
    moved_total = 0
    failed: list[tuple[str, str]] = []
    for name in to_move:
        try:
            new_name, moved = archive_scenario(name)
        except Exception as e:  # noqa: BLE001 — фактическое сообщение важно
            failed.append((name, str(e)))
            print(f"  ✗ {name}: {e}")
            continue
        moved_total += 1
        print(f"  ✓ {name} → {new_name}")
        for line in moved:
            print(f"      {line}")

    print()
    print(f"Готово: {moved_total} из {len(to_move)} перенесено.")
    if failed:
        print(f"Ошибки: {len(failed)}")
        for name, err in failed:
            print(f"  • {name}: {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
