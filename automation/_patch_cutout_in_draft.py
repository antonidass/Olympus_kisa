"""
One-shot: подменить ссылки на стикеры в живом CapCut-драфте с
`images/stickers/scene_NN_*.jpg` на `images/stickers/cutout/scene_NN_*.png`
после прохода automation/cutout_stickers.py.

Используется когда драфт уже собран и в нём есть ручные правки —
полная пересборка build/enrich/karaoke их затрёт.

Делает:
  1. бэкап draft_content.json → draft_content.json.cutout-backup (если ещё нет)
  2. для каждой ссылки <stem>.jpg ищет в материалах и заменяет:
     - path:           ...\\images\\stickers\\<stem>.jpg
                    →  ...\\images\\stickers\\cutout\\<stem>.png
     - material_name:  <stem>.jpg → <stem>.png
  3. сохраняет JSON обратно.

Использование:
    python automation/_patch_cutout_in_draft.py "<draft_dir>"
    python automation/_patch_cutout_in_draft.py "%LOCALAPPDATA%\\CapCut\\User Data\\Projects\\com.lveditor.draft\\<имя драфта>"

CapCut должен быть закрыт.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

SEP = "\\"  # CapCut на Windows пишет пути с обратным слэшем


def patch_draft(draft_dir: Path) -> int:
    draft = draft_dir / "draft_content.json"
    if not draft.is_file():
        print(f"ERROR: не найден {draft}", file=sys.stderr)
        return 2

    backup = draft_dir / "draft_content.json.cutout-backup"
    if not backup.exists():
        shutil.copy2(draft, backup)
        print(f"Backup: {backup.name}")
    else:
        print(f"Backup exists: {backup.name} (keep)")

    data = json.loads(draft.read_text(encoding="utf-8"))

    materials = data.get("materials", {})
    videos = materials.get("videos", []) or []

    patched: list[str] = []
    skipped_already_png: list[str] = []
    skipped_no_cutout: list[str] = []

    for v in videos:
        name = v.get("material_name") or ""
        path = v.get("path") or ""

        # Интересны только стикеры — file matches scene_NN_*.jpg в папке stickers
        if not name.lower().endswith(".jpg"):
            continue
        if not name.lower().startswith("scene_"):
            continue
        path_lower = path.replace("/", SEP).lower()
        if f"{SEP}images{SEP}stickers{SEP}" not in path_lower:
            continue
        # Уже после cutout/ — пропустить
        if f"{SEP}cutout{SEP}" in path_lower:
            skipped_already_png.append(name)
            continue

        # Построить целевой путь: ...\images\stickers\cutout\<stem>.png
        head, tail = path.rsplit(SEP + "stickers" + SEP, 1)
        # tail = <stem>.jpg
        new_name = tail[:-4] + ".png"
        new_path = head + SEP + "stickers" + SEP + "cutout" + SEP + new_name

        # Проверим что cutout/<...>.png реально существует на диске
        if not Path(new_path).exists():
            print(f"  SKIP {name}: cutout PNG не существует → {new_path}")
            skipped_no_cutout.append(name)
            continue

        v["path"] = new_path
        v["material_name"] = new_name
        patched.append(name)
        print(f"  OK   {name} -> stickers\\cutout\\{new_name}")

    if not patched:
        print("Ничего не пропатчено.")
    else:
        draft.write_text(
            # CapCut пишет компактно (без пробелов после `,` и `:`) —
            # сохраняем тот же стиль, иначе draft_content.json пухнет.
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        print(f"\nЗаписано: {draft}")

    print()
    print(f"Итого: {len(patched)} пропатчено, "
          f"{len(skipped_already_png)} уже PNG/cutout, "
          f"{len(skipped_no_cutout)} без cutout-файла.")
    return 0 if not skipped_no_cutout else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Подменить ссылки stickers/*.jpg на stickers/cutout/*.png в CapCut-драфте."
    )
    parser.add_argument("draft_dir", help="Папка драфта в %LOCALAPPDATA%\\CapCut\\User Data\\Projects\\com.lveditor.draft\\<имя>")
    args = parser.parse_args()

    draft_dir = Path(os.path.expandvars(args.draft_dir)).expanduser()
    if not draft_dir.is_dir():
        print(f"ERROR: {draft_dir} не папка", file=sys.stderr)
        return 2

    return patch_draft(draft_dir)


if __name__ == "__main__":
    raise SystemExit(main())
