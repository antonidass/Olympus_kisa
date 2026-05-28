"""
replace_compound_with_mp4.py - заменяет сборный клип в CapCut-проекте на
обычное video-материал, ссылающийся на готовый MP4 (тот, что лежит в final/).

Зачем: после make_compound_oh_02.py + предобработки в CapCut + harvest_compound_mp4.py
у нас есть финальный MP4 (рендер всей сборки). Чтобы можно было дальше нажать
«Экспорт» в CapCut без перерендера компаунда, мы подменяем сегмент-компаунд
на сегмент-видео, указывающий на этот MP4. Проект становится «лёгким»:
один трек, один сегмент, один MP4 на диске.

Что делает скрипт:
  1. Читает текущий draft_content.json (должен быть в compound-состоянии).
  2. Из materials.videos[0] забирает шаблон video-материала и переписывает:
       path → абсолютный путь к final MP4
       category_name → "local"
       material_name → имя файла
  3. Чистит materials.drafts (компаунд больше не нужен).
  4. На сегменте удаляет ссылку на drafts-материал из extra_material_refs.
  5. Опционально удаляет папку subdraft/<UUID>/ и Resources/combination/.

Использование:
    python replace_compound_with_mp4.py                       # дефолты для Ч.02
    python replace_compound_with_mp4.py --dry-run
    python replace_compound_with_mp4.py --keep-subdraft       # не удалять папку
    python replace_compound_with_mp4.py --mp4 "C:/path.mp4"
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
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
DEFAULT_MP4 = (
    Path(__file__).resolve().parent.parent
    / "content"
    / "От Хаоса до Олимпа"
    / "часть_02_Власть_Кроноса"
    / "final"
    / "От Хаоса до Олимпа Ч.02 Власть Кроноса.mp4"
)


def load_json(p: Path) -> dict:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(p: Path, data: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drafts", type=Path, default=DEFAULT_DRAFTS_ROOT)
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--mp4", type=Path, default=DEFAULT_MP4,
                        help="Путь к финальному MP4")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-subdraft", action="store_true",
                        help="Не удалять папку subdraft/<UUID>/")
    parser.add_argument("--keep-combination-cache", action="store_true",
                        help="Не удалять Resources/combination/*.mp4")
    args = parser.parse_args()

    project_dir = args.drafts / args.project
    draft_path = project_dir / "draft_content.json"
    if not draft_path.exists():
        print(f"[ОШИБКА] Нет {draft_path}", file=sys.stderr)
        return 2
    if not args.mp4.exists():
        print(f"[ОШИБКА] Нет MP4: {args.mp4}", file=sys.stderr)
        return 2

    draft = load_json(draft_path)

    # Проверка: должен быть compound-вид (есть materials.drafts с combination)
    drafts_mat = draft.get("materials", {}).get("drafts", [])
    if not drafts_mat:
        print("[ОШИБКА] В draft_content.json нет materials.drafts. "
              "Похоже, сборного клипа здесь уже нет.", file=sys.stderr)
        return 2
    combo_mat = drafts_mat[0]
    if combo_mat.get("type") != "combination":
        print(f"[ОШИБКА] materials.drafts[0].type = {combo_mat.get('type')}, ожидаю 'combination'",
              file=sys.stderr)
        return 2

    if len(draft.get("tracks", [])) != 1 or len(draft["tracks"][0].get("segments", [])) != 1:
        print("[ВНИМАНИЕ] Ожидаю ровно 1 трек с 1 сегментом (compound-вид). "
              "Текущее: tracks=%d, segs=%d" % (
                  len(draft.get("tracks", [])),
                  sum(len(t.get("segments", [])) for t in draft.get("tracks", []))),
              file=sys.stderr)
        return 2

    # Берём текущий video-материал как шаблон, переписываем поля под обычный MP4
    new_video = copy.deepcopy(draft["materials"]["videos"][0])
    mp4_size = args.mp4.stat().st_size
    new_video["path"] = str(args.mp4)
    new_video["material_name"] = args.mp4.name
    new_video["category_name"] = "local"
    # Длительность и размеры в драфте уже соответствуют MP4 (CapCut рендерил его
    # из текущей канвы и текущей длины), так что не трогаем.

    # Сегмент: удаляем ссылку на drafts из extra_material_refs
    seg = draft["tracks"][0]["segments"][0]
    drafts_id = combo_mat["id"]
    new_refs = [r for r in seg.get("extra_material_refs", []) if r != drafts_id]
    seg["extra_material_refs"] = new_refs
    # material_id остаётся прежним (мы переписали тот же объект)

    # materials.drafts → пусто
    draft["materials"]["drafts"] = []
    # Заменяем materials.videos[0] на наш new_video
    draft["materials"]["videos"] = [new_video]

    # Путь к папке subdraft из combo_mat
    sub_id = None
    dfp = combo_mat.get("draft_file_path", "")
    for part in dfp.replace("\\", "/").split("/"):
        if part and len(part) == 36 and part.count("-") == 4:
            sub_id = part
            break
    sub_dir = project_dir / "subdraft" / sub_id if sub_id else None
    combo_id = combo_mat.get("combination_id")
    combo_cache_dir = project_dir / "Resources" / "combination"

    print(f"[i] Проект:       {project_dir.name}")
    print(f"[i] MP4:          {args.mp4} ({mp4_size/1_048_576:.1f} MiB)")
    print(f"[i] Длина драфта: {draft['duration']/1_000_000:.2f} с")
    print(f"[i] Канва:        {draft['canvas_config']['width']}×{draft['canvas_config']['height']}")
    print(f"[i] subdraft/<id>: {sub_id or '(не найден)'}")
    print(f"[i] combination_id: {combo_id}")
    print(f"[i] segments итог: 1, tracks итог: 1")

    if args.dry_run:
        print("\n[dry-run] Ничего не записал.")
        return 0

    # Бэкап текущего (compound) состояния
    backup_path = project_dir / "draft_content.json.pre-replace-backup"
    if not backup_path.exists():
        shutil.copy2(draft_path, backup_path)
        print(f"[бэкап] {backup_path.name}")
    else:
        print(f"[бэкап] уже есть, не перезаписываю: {backup_path.name}")

    save_json(draft_path, draft)
    print(f"[write] {draft_path.name}")

    # Удаляем subdraft-папку
    if sub_dir and sub_dir.exists() and not args.keep_subdraft:
        shutil.rmtree(sub_dir)
        print(f"[clean] удалил subdraft/{sub_id}/")
    elif args.keep_subdraft and sub_dir and sub_dir.exists():
        print(f"[skip ] subdraft/{sub_id}/ оставлена")

    # Удаляем кэш предобработки в Resources/combination
    if combo_cache_dir.exists() and not args.keep_combination_cache:
        removed = 0
        for f in combo_cache_dir.iterdir():
            if f.is_file() and (combo_id and combo_id in f.name):
                f.unlink()
                removed += 1
        if removed:
            print(f"[clean] удалил {removed} файл(ов) из Resources/combination/")
    elif args.keep_combination_cache:
        print(f"[skip ] Resources/combination/ оставлена")

    print("\n[готово] Открой проект в CapCut - должен быть 1 видео-сегмент с MP4.")
    print("         Откат: переименуй .pre-replace-backup → draft_content.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
