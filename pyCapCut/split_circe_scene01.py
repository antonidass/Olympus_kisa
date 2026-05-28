"""
Подменяет один шот scene_01_v2.mp4 в драфте «Цирцея и Одиссей» на
ДВА шота встык:
  - scene_01_a_v2.mp4 (банкет + Цирцея сзади) — 0.000–3.333с
  - scene_01_b_v2.mp4 (свинарник + Цирцея + титр-караоке)  — 3.333–6.650с

Точка раскола 3.333с (200 кадров @ 60fps) выбрана так, чтобы зрительский
переход банкет→свинарник упал на слово «хрюкали» — это самый сильный
комический разворот фразы.

Ничего другого не меняет:
  - аудио (voice, music, sticker_sfx, sfx, hermes_scroll_sfx)
  - переход «Влево» между сценой 1 и сценой 2 — переезжает на сегмент b
  - стикеры, halftone-эффект, hermes-карточка, караоке-титр
  - громкости, геометрия, fade-out музыки

Запуск (CapCut должен быть полностью закрыт):
    python split_circe_scene01.py
    python split_circe_scene01.py --dry-run
"""

from __future__ import annotations

import argparse
import copy
import datetime
import io
import json
import os
import shutil
import subprocess
import sys
import uuid
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
A_FILE = VIDEO_DIR / "scene_01_a_v2.mp4"
B_FILE = VIDEO_DIR / "scene_01_b_v2.mp4"

US = 1_000_000
FPS = 60


def floor_to_frame_us(us: int) -> int:
    frames = (us * FPS) // US
    return (frames * US) // FPS


# Точка раскола внутри scene_01: 3.333с (200 кадров @ 60fps).
# Перед: банкет, аудио "Двенадцать моряков сели за её стол, а к рассвету все".
# После: свинарник, аудио "хрюкали в свинарнике" + sent_002 титр.
SPLIT_US = floor_to_frame_us(3_333_333)
TOTAL_US = 6_650_000   # длина scene_01 на таймлайне (sent_001 + sent_002)
A_DUR_US = SPLIT_US                     # 3.333с
B_DUR_US = TOTAL_US - SPLIT_US          # 3.317с


def gen_id_hex() -> str:
    return uuid.uuid4().hex


def video_duration_us(path: Path) -> int:
    from pymediainfo import MediaInfo
    mi = MediaInfo.parse(str(path))
    for t in mi.tracks:
        if t.track_type == "Video" and t.duration is not None:
            return floor_to_frame_us(int(float(t.duration) * 1000))
    raise RuntimeError(f"видео-дорожка не найдена в {path}")


def check_capcut_closed() -> bool:
    try:
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
        text = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        return "CapCut.exe" not in text and "JianyingPro" not in text
    except Exception:
        return True


def clone_video_material(template: dict, new_path: Path, new_dur_us: int) -> dict:
    m = copy.deepcopy(template)
    m["id"] = gen_id_hex()
    m["local_material_id"] = gen_id_hex()
    new_str = str(new_path).replace("/", "\\")
    m["path"] = new_str
    m["media_path"] = new_str
    m["material_name"] = new_path.name
    m["duration"] = int(new_dur_us)
    return m


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    for f in (A_FILE, B_FILE):
        if not f.is_file():
            print(f"Нет файла: {f}")
            return 1
    if not DRAFT_FILE.is_file():
        print(f"Нет драфта: {DRAFT_FILE}")
        return 1
    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен — закрой полностью.")
        return 1

    a_full_us = video_duration_us(A_FILE)
    b_full_us = video_duration_us(B_FILE)
    print(f"scene_01_a_v2.mp4: {a_full_us/US:.3f}s, scene_01_b_v2.mp4: {b_full_us/US:.3f}s")
    print(f"split point: {SPLIT_US/US:.3f}s")
    print(f"  segment a: target [0, {A_DUR_US/US:.3f}s], source [0, {A_DUR_US/US:.3f}s]")
    print(f"  segment b: target [{SPLIT_US/US:.3f}s, {B_DUR_US/US:.3f}s], source [0, {B_DUR_US/US:.3f}s]")

    if A_DUR_US > a_full_us:
        print(f"⚠ A_DUR_US > scene_01_a duration — обрезаю до {a_full_us/US:.3f}s")
        a_use = a_full_us
    else:
        a_use = A_DUR_US

    if B_DUR_US > b_full_us:
        print(f"⚠ B_DUR_US > scene_01_b duration — обрезаю до {b_full_us/US:.3f}s")
        b_use = b_full_us
    else:
        b_use = B_DUR_US

    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))
    vids = {v["id"]: v for v in draft["materials"]["videos"]}
    main = next(t for t in draft["tracks"]
                if t["type"] == "video" and t.get("name") == "main")
    seg0 = main["segments"][0]
    old_mat = vids.get(seg0["material_id"])
    if old_mat is None:
        print("⚠ не нашёл материал scene_01 в draft")
        return 1

    # Определяем какой из refs — переход (его перенесём на segment b)
    trans_ids = {t["id"] for t in draft["materials"]["transitions"]}
    seg0_refs = list(seg0.get("extra_material_refs", []))
    transition_refs = [r for r in seg0_refs if r in trans_ids]
    nontransition_refs = [r for r in seg0_refs if r not in trans_ids]
    print(f"  transition refs (переедут на segment b): {len(transition_refs)}")
    print(f"  служебные refs (на оба сегмента): {len(nontransition_refs)}")

    # Создаём новые видео-материалы
    mat_a = clone_video_material(old_mat, A_FILE, a_full_us)
    mat_b = clone_video_material(old_mat, B_FILE, b_full_us)
    draft["materials"]["videos"].append(mat_a)
    draft["materials"]["videos"].append(mat_b)

    # Клонируем seg0 как seg_a и seg_b, выставляем нужные поля
    seg_a = copy.deepcopy(seg0)
    seg_a["id"] = gen_id_hex()
    seg_a["material_id"] = mat_a["id"]
    seg_a["source_timerange"] = {"start": 0, "duration": int(a_use)}
    seg_a["target_timerange"] = {"start": 0, "duration": int(A_DUR_US)}
    seg_a["speed"] = 1.0
    seg_a["extra_material_refs"] = list(nontransition_refs)  # без перехода

    seg_b = copy.deepcopy(seg0)
    seg_b["id"] = gen_id_hex()
    seg_b["material_id"] = mat_b["id"]
    seg_b["source_timerange"] = {"start": 0, "duration": int(b_use)}
    seg_b["target_timerange"] = {"start": int(SPLIT_US), "duration": int(B_DUR_US)}
    seg_b["speed"] = 1.0
    seg_b["extra_material_refs"] = list(nontransition_refs) + list(transition_refs)

    # Подменяем seg0 на [seg_a, seg_b]
    main["segments"] = [seg_a, seg_b] + main["segments"][1:]

    if args.dry_run:
        print("\n--dry-run: не сохраняю.")
        return 0

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bkp = DRAFT_DIR / f"draft_content.json.scene01-split-{ts}"
    shutil.copy2(DRAFT_FILE, bkp)
    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt in ("template-2.tmp", "draft_content.json.bak"):
        try:
            shutil.copy2(DRAFT_FILE, DRAFT_DIR / tgt)
        except Exception:
            pass

    print(f"\n✓ Готово. scene_01 разбит на два шота.")
    print(f"  segment a: 0.000–{SPLIT_US/US:.3f}s  ({A_FILE.name})")
    print(f"  segment b: {SPLIT_US/US:.3f}–{TOTAL_US/US:.3f}s  ({B_FILE.name})")
    print(f"  переход «Влево» (и др.) переехал на segment b")
    print(f"Бэкап: {bkp.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
