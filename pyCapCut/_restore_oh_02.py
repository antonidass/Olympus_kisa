"""
Одноразовое восстановление проекта 'От Хаоса до Олимпа Ч.02 Власть Кроноса'
из .recycle_bin/<...> (1)/ с откатом на .compound-backup (11 треков).
"""
import json
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

ROOT = r"C:\Users\Антон\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft"
SRC_FOLDER = os.path.join(ROOT, ".recycle_bin", "От Хаоса до Олимпа Ч.02 Власть Кроноса (1)")
DST_FOLDER = os.path.join(ROOT, "От Хаоса до Олимпа Ч.02 Власть Кроноса")
RECYCLE_META = os.path.join(ROOT, ".recycle_bin", "root_meta_info.json")
MAIN_META = os.path.join(ROOT, "root_meta_info.json")
RESTORED_NAME = "От Хаоса до Олимпа Ч.02 Власть Кроноса"
RECYCLED_NAME = "От Хаоса до Олимпа Ч.02 Власть Кроноса (1)"


def main() -> int:
    if not os.path.exists(SRC_FOLDER):
        print(f"[ОШИБКА] нет {SRC_FOLDER}")
        return 1
    if os.path.exists(DST_FOLDER):
        print(f"[ОШИБКА] {DST_FOLDER} уже существует")
        return 1

    print(f"[move] {SRC_FOLDER}")
    print(f"   →   {DST_FOLDER}")
    shutil.move(SRC_FOLDER, DST_FOLDER)

    backup = os.path.join(DST_FOLDER, "draft_content.json.compound-backup")
    target = os.path.join(DST_FOLDER, "draft_content.json")
    if not os.path.exists(backup):
        print(f"[ОШИБКА] нет {backup}")
        return 1
    shutil.copy2(backup, target)
    print("[restore] draft_content.json ← .compound-backup")

    with open(target, "r", encoding="utf-8") as f:
        d = json.load(f)
    tracks = d.get("tracks", [])
    segs = sum(len(t.get("segments", [])) for t in tracks)
    print(f"[check] tracks={len(tracks)}, segs={segs}, "
          f"duration={d.get('duration', 0) / 1_000_000:.1f}с")

    with open(RECYCLE_META, "r", encoding="utf-8") as f:
        rmeta = json.load(f)
    with open(MAIN_META, "r", encoding="utf-8") as f:
        mmeta = json.load(f)

    entry = None
    for i, e in enumerate(rmeta.get("all_draft_store", [])):
        if e.get("draft_name") == RECYCLED_NAME:
            entry = rmeta["all_draft_store"].pop(i)
            break

    if entry is None:
        print("[warn] запись в recycle meta не найдена, пропускаю обновление meta")
    else:
        fold_unix = DST_FOLDER.replace(os.sep, "/")
        entry["draft_name"] = RESTORED_NAME
        entry["draft_fold_path"] = fold_unix
        sep = "\\"  # CapCut в этих полях использует обратные слэши
        entry["draft_cover"] = fold_unix + sep + "draft_cover.jpg"
        entry["draft_json_file"] = fold_unix + sep + "draft_content.json"
        entry["tm_draft_removed"] = 0
        entry["tm_duration"] = int(d.get("duration", 0))
        mmeta["all_draft_store"].append(entry)
        print(f"[meta] entry перенесена в main (draft_id={entry['draft_id']})")

    with open(RECYCLE_META, "w", encoding="utf-8") as f:
        json.dump(rmeta, f, ensure_ascii=False, separators=(",", ":"))
    with open(MAIN_META, "w", encoding="utf-8") as f:
        json.dump(mmeta, f, ensure_ascii=False, separators=(",", ":"))
    print("[meta] обе root_meta_info.json сохранены")
    print()
    print("[готово] CapCut должен показать проект с 11 треками")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
