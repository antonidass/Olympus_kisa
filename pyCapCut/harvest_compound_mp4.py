"""
harvest_compound_mp4.py - забирает MP4, который CapCut генерирует при
«Предобработать сборный клип», и кладёт его в content/.../final/.

Логика:
  1. Из draft_content.json целевого проекта читаем combination_id.
  2. В папке Resources/combination/ ждём появления файла
     '<combination_id>_video.mp4' (без суффикса '_temp').
  3. Копируем (или перемещаем) в final-папку мифа.

Что делает CapCut при предсборе:
  - Сначала рендерит '<combination_id>_video.mp4_temp.mp4' (промежуточный).
  - По окончании переименовывает в '<combination_id>_video.mp4'.
  - Рядом лежит '*.alpha.mp4' - альфа-канал, не нужен.

Использование:
    python harvest_compound_mp4.py                        # дефолты для Ч.02
    python harvest_compound_mp4.py --wait 600             # ждать до 10 мин
    python harvest_compound_mp4.py --move                 # перемещать, не копировать
    python harvest_compound_mp4.py --project "Имя"  --final "C:/.../final/Х.mp4"
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except (AttributeError, OSError):
    pass


DEFAULT_DRAFTS_ROOT = (
    Path.home()
    / "AppData"
    / "Local"
    / "CapCut"
    / "User Data"
    / "Projects"
    / "com.lveditor.draft"
)

DEFAULT_PROJECT = "От Хаоса до Олимпа Ч.02 Власть Кроноса"
DEFAULT_FINAL = (
    Path(__file__).resolve().parent.parent
    / "content"
    / "От Хаоса до Олимпа"
    / "часть_02_Власть_Кроноса"
    / "final"
    / "От Хаоса до Олимпа Ч.02 Власть Кроноса.mp4"
)


def get_combination_id(project_dir: Path) -> str:
    """Читает combination_id из главного draft_content.json."""
    draft_path = project_dir / "draft_content.json"
    if not draft_path.exists():
        raise FileNotFoundError(f"Нет {draft_path}")
    with draft_path.open("r", encoding="utf-8") as f:
        d = json.load(f)
    drafts_mat = d.get("materials", {}).get("drafts", [])
    if not drafts_mat:
        raise ValueError(
            "В draft_content.json нет materials.drafts. "
            "Сначала сделай сборный клип (make_compound_oh_02.py)."
        )
    combo_id = drafts_mat[0].get("combination_id")
    if not combo_id:
        raise ValueError("В драфте есть materials.drafts[0], но без combination_id.")
    return combo_id


def wait_for_mp4(combo_dir: Path, combination_id: str, timeout_s: float) -> Path:
    """
    Возвращает путь к финальному MP4 предсбора. Падает с TimeoutError, если
    не появится за timeout_s.

    Финальный файл = '<combination_id>_video.mp4'. Если есть только '*_temp.mp4',
    значит CapCut ещё рендерит - ждём.
    """
    target = combo_dir / f"{combination_id}_video.mp4"
    temp = combo_dir / f"{combination_id}_video.mp4_temp.mp4"

    deadline = time.monotonic() + timeout_s
    last_size = -1
    last_report = 0.0
    print(f"[wait] жду {target.name}")
    while time.monotonic() < deadline:
        if target.exists() and target.stat().st_size > 0:
            # Убедимся, что файл «успокоился» - размер не растёт пару секунд
            size_now = target.stat().st_size
            time.sleep(1.5)
            if target.stat().st_size == size_now:
                return target
            continue
        # Прогресс по _temp
        if temp.exists():
            sz = temp.stat().st_size
            if sz != last_size and time.monotonic() - last_report > 2.0:
                print(f"  …рендер _temp.mp4: {sz/1_048_576:.1f} MiB")
                last_size = sz
                last_report = time.monotonic()
        time.sleep(1.0)
    raise TimeoutError(
        f"Не дождался {target.name} за {timeout_s:.0f} с. "
        f"Проверь, что в CapCut запущена 'Предобработать сборный клип'."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drafts", type=Path, default=DEFAULT_DRAFTS_ROOT,
                        help="Папка com.lveditor.draft с проектами CapCut")
    parser.add_argument("--project", default=DEFAULT_PROJECT,
                        help="Имя CapCut-проекта со сборным клипом")
    parser.add_argument("--final", type=Path, default=DEFAULT_FINAL,
                        help="Куда положить финальный MP4 (полный путь)")
    parser.add_argument("--wait", type=float, default=600.0,
                        help="Сколько секунд ждать появления MP4 (по умолчанию 600)")
    parser.add_argument("--move", action="store_true",
                        help="Перемещать, а не копировать (освобождает место в CapCut)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Перезаписать, если final-файл уже существует")
    args = parser.parse_args()

    project_dir = args.drafts / args.project
    if not project_dir.is_dir():
        print(f"[ОШИБКА] Нет проекта: {project_dir}", file=sys.stderr)
        return 2

    combo_id = get_combination_id(project_dir)
    combo_dir = project_dir / "Resources" / "combination"
    combo_dir.mkdir(parents=True, exist_ok=True)

    print(f"[i] Проект:         {project_dir.name}")
    print(f"[i] combination_id: {combo_id}")
    print(f"[i] Источник:       Resources/combination/{combo_id}_video.mp4")
    print(f"[i] Назначение:     {args.final}")
    print()

    src = wait_for_mp4(combo_dir, combo_id, args.wait)
    print(f"[ok] найден: {src} ({src.stat().st_size/1_048_576:.1f} MiB)")

    if args.final.exists() and not args.overwrite:
        print(f"[ОШИБКА] {args.final} уже существует. Используй --overwrite.", file=sys.stderr)
        return 3

    args.final.parent.mkdir(parents=True, exist_ok=True)
    if args.move:
        shutil.move(str(src), str(args.final))
        print(f"[move] → {args.final}")
    else:
        shutil.copy2(src, args.final)
        print(f"[copy] → {args.final}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
