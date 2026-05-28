"""
Подмена видео-шотов scene_09 и scene_15 в драфте «Цирцея и Одиссей»
на v2 без замедления.

Старое поведение build_circe.py: если видео-материал короче target_dur
(длина озвучки), сегменту назначается speed = src/target < 1.0 —
видео замедляется. Пользователь сделал v2 подлиннее (6.0с вместо 4.0с),
но scene_09 всё ещё чуть короче своей озвучки 6.28с. Чтобы не было
замедления:
  - scene_09 (target 6.28с, src v2 6.0с): speed=1.0, source_duration=6.0с,
    target_duration оставляем 6.28с — последние 0.28с CapCut удержит
    последний кадр (freeze frame), но скорость нормальная.
  - scene_15 (target 4.72с, src v2 6.0с): speed=1.0, source_duration=4.72с
    (тримминг хвоста), target_duration без изменений.

Запуск (CapCut должен быть полностью закрыт):
    python swap_video_v2_circe.py
    python swap_video_v2_circe.py --dry-run
"""

from __future__ import annotations

import argparse
import datetime
import io
import json
import os
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


LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFT_DIR = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft" / "Цирцея и Одиссей"
DRAFT_FILE = DRAFT_DIR / "draft_content.json"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIDEO_DIR = PROJECT_ROOT / "content" / "Цирцея и Одиссей" / "video"

US = 1_000_000
FPS = 60

# Старое имя → новое имя
SWAPS = {
    "scene_09_v1.mp4": "scene_09_v2.mp4",
    "scene_15_v1.mp4": "scene_15_v2.mp4",
}


def floor_to_frame_us(us: int) -> int:
    frames = (us * FPS) // US
    return (frames * US) // FPS


def video_duration_us(path: Path) -> int:
    from pymediainfo import MediaInfo
    mi = MediaInfo.parse(str(path))
    for t in mi.tracks:
        if t.track_type == "Video" and t.duration is not None:
            return floor_to_frame_us(int(float(t.duration) * 1000))
    raise RuntimeError(f"Не нашёл видео-дорожку в {path}")


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
    p.add_argument("--dry-run", action="store_true", help="Только показать план.")
    args = p.parse_args()

    if not DRAFT_FILE.is_file():
        print(f"Нет драфта: {DRAFT_FILE}")
        return 1
    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой полностью (включая трей).")
        return 1

    for old, new in SWAPS.items():
        np = VIDEO_DIR / new
        if not np.is_file():
            print(f"Нет файла {np}")
            return 1

    print(f"Читаю драфт: {DRAFT_FILE}")
    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))

    videos_by_id = {v["id"]: v for v in draft["materials"]["videos"]}
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")

    # Найти сегменты с подменяемыми именами и обновить
    changes = []
    for seg in main["segments"]:
        mat = videos_by_id.get(seg.get("material_id"))
        if not mat:
            continue
        old_name = os.path.basename(mat.get("path", ""))
        if old_name not in SWAPS:
            continue
        new_name = SWAPS[old_name]
        new_path = VIDEO_DIR / new_name
        new_dur_us = video_duration_us(new_path)

        old_path = mat["path"]
        old_dur = mat.get("duration", 0)

        # Обновляем материал
        mat["path"] = str(new_path).replace("/", "\\")
        mat["material_name"] = new_name
        mat["duration"] = new_dur_us

        # Сегмент: speed=1.0, source = min(video_dur, target_dur)
        tgt_dur = int(seg["target_timerange"]["duration"])
        src_dur = min(new_dur_us, tgt_dur)
        seg["source_timerange"] = {"start": 0, "duration": src_dur}
        seg["speed"] = 1.0
        # Сбросить ускорение/замедление в speeds-материале если ссылается
        for ref in seg.get("extra_material_refs", []):
            for sp in draft["materials"].get("speeds", []):
                if sp.get("id") == ref:
                    sp["speed"] = 1.0
                    sp["mode"] = 0
                    sp.setdefault("curve_speed", None)

        changes.append({
            "old": old_name, "new": new_name,
            "old_dur": old_dur, "new_dur": new_dur_us,
            "tgt": tgt_dur, "src": src_dur,
            "freeze_tail": max(0, tgt_dur - src_dur),
        })

    print()
    for c in changes:
        freeze = c["freeze_tail"] / US
        freeze_note = f"  (freeze last frame {freeze:.3f}s)" if freeze > 0.001 else ""
        print(f"  {c['old']} -> {c['new']}  src={c['src']/US:.3f}s "
              f"tgt={c['tgt']/US:.3f}s speed=1.000{freeze_note}")

    if args.dry_run:
        print("\n--dry-run: драфт не трогаю.")
        return 0

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bkp = DRAFT_DIR / f"draft_content.json.swap-v2-{ts}"
    shutil.copy2(DRAFT_FILE, bkp)
    print(f"\nБэкап: {bkp.name}")

    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = DRAFT_DIR / tgt_name
        try:
            shutil.copy2(DRAFT_FILE, tgt)
        except Exception:
            pass

    print(f"\n✓ Готово. Подменено {len(changes)} видео-сегмента.")
    print("Открой CapCut -> проект «Цирцея и Одиссей» -> проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
