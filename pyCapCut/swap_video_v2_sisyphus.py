"""
Подмена видеоматериалов сцен 9 / 11 / 12 / 14 на свежие v2-версии,
лежащие в `content/Сизифов Труд/video/scene_NN_v2.mp4`.

Что делает:
  1. Открывает draft_content.json «Сизифов труд».
  2. Для каждого video-материала с именем scene_09.mp4 / 11 / 12 / 14
     меняет path на абсолютный к .._v2.mp4 и обновляет duration через
     pymediainfo. Имя самого материала (`material_name`/`name`) тоже
     приводим к виду scene_NN_v2.mp4 — иначе CapCut в превью покажет
     старое имя и может не пересчитать thumbnail.
  3. Сохраняет драфт + синхронизирует .bak / template-2.tmp.

Запуск (CapCut должен быть закрыт):
    python pyCapCut/swap_video_v2_sisyphus.py
    python pyCapCut/swap_video_v2_sisyphus.py --dry-run
"""

from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFT_DIR = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft" / "Сизифов труд"
DRAFT_FILE = DRAFT_DIR / "draft_content.json"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
V2_DIR = PROJECT_ROOT / "content" / "Сизифов Труд" / "video"

# scene name → новое имя файла v2
SWAPS = {
    "scene_09.mp4": "scene_09_v2.mp4",
    "scene_11.mp4": "scene_11_v2.mp4",
    "scene_12.mp4": "scene_12_v2.mp4",
    "scene_14.mp4": "scene_14_v2.mp4",
}


def video_duration_us(path: Path) -> int:
    from pymediainfo import MediaInfo
    mi = MediaInfo.parse(str(path))
    for t in mi.tracks:
        if t.track_type == "Video" and t.duration is not None:
            return int(float(t.duration) * 1000)
    raise RuntimeError(f"Не нашёл video-дорожку в {path}")


def check_capcut_closed() -> bool:
    try:
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
        text = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        if "CapCut.exe" in text or "JianyingPro" in text:
            return False
    except Exception:
        pass
    return True


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not DRAFT_FILE.is_file():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1

    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой его полностью (включая трей) и запусти снова.")
        return 1

    # Проверяем v2-файлы
    missing = [old for old, new in SWAPS.items() if not (V2_DIR / new).is_file()]
    if missing:
        print("Не нашёл v2-файлы:")
        for m in missing:
            print(f"  - {V2_DIR / SWAPS[m]}")
        return 1

    print(f"Читаю драфт: {DRAFT_FILE}")
    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))

    plan = []
    for vmat in draft["materials"]["videos"]:
        old_name = Path(vmat["path"]).name
        if old_name not in SWAPS:
            continue
        new_name = SWAPS[old_name]
        new_path = V2_DIR / new_name
        new_dur = video_duration_us(new_path)
        plan.append({
            "id": vmat["id"],
            "old_name": old_name,
            "new_name": new_name,
            "new_path": new_path,
            "new_dur": new_dur,
            "old_path": vmat["path"],
            "old_dur": vmat.get("duration", 0),
        })

    print()
    print(f"{'Старый файл':<18} → {'Новый v2-файл':<22} {'Длит.':>8}")
    print("-" * 60)
    for p_ in plan:
        print(f"  {p_['old_name']:<16} → {p_['new_name']:<22} {p_['new_dur']/1_000_000:>6.2f}s")

    if args.dry_run:
        print("\n--dry-run: ничего не меняю.")
        return 0

    # Бэкап
    bkp = DRAFT_FILE.with_suffix(".json.swapv2-backup")
    shutil.copy2(DRAFT_FILE, bkp)
    print(f"\nБэкап: {bkp.name}")

    # Применяем
    swapped = 0
    for vmat in draft["materials"]["videos"]:
        old_name = Path(vmat["path"]).name
        if old_name not in SWAPS:
            continue
        item = next(x for x in plan if x["id"] == vmat["id"])
        new_abs = str(item["new_path"]).replace("/", "\\")
        vmat["path"] = new_abs
        vmat["duration"] = item["new_dur"]
        # name / material_name — для отображения в Media Bin
        if "material_name" in vmat:
            vmat["material_name"] = item["new_name"]
        if "name" in vmat:
            vmat["name"] = item["new_name"]
        swapped += 1

    # Сохраняем + синхронизируем .bak / template-2.tmp
    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = DRAFT_DIR / tgt_name
        try:
            shutil.copy2(DRAFT_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    print(f"\n✓ Подменено материалов: {swapped}.")
    print("Открой CapCut → проект «Сизифов труд» → проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
