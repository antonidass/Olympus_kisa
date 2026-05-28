"""
Один-разовый патч: scene_07 на main-видео-треке драфта «Баба-Яга»
начинается с offset 1.2 секунды от начала клипа scene_07_v1.mp4.

Если после offset в клипе остаётся меньше длительности озвучки —
скрипт автоматически замедляет видео (speed<1.0), чтобы оставшаяся
часть покрыла всю target_duration. В текущем кейсе клип 4.0с,
offset 1.2с → остаток 2.8с, а target=2.567с — slow-mo не нужен.

Voice / music / karaoke / sfx НЕ трогаются — это правка только
source_timerange (и при необходимости speed) одного видео-сегмента.

CapCut должен быть полностью закрыт.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

DRAFTS = Path(os.environ["LOCALAPPDATA"]) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
YAGA_DIR = DRAFTS / "Баба-Яга"
DRAFT_FILE = YAGA_DIR / "draft_content.json"

SCENE_NAME = "scene_07_v1.mp4"
OFFSET_US = 1_200_000     # 1.2 секунды
MIN_SPEED = 0.5           # пороговое замедление — ниже артефакты тяжёлые


def find_main_video_track(draft: dict) -> dict:
    for t in draft["tracks"]:
        if t.get("type") == "video" and t.get("name") == "main":
            return t
    raise RuntimeError("В драфте нет video-трека main.")


def main() -> int:
    if not DRAFT_FILE.is_file():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1

    print(f"Читаю драфт: {DRAFT_FILE}")
    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))

    main_tr = find_main_video_track(draft)
    vmats = {m["id"]: m for m in draft["materials"].get("videos", [])}

    target_seg = None
    target_idx = -1
    target_mat = None
    for i, seg in enumerate(main_tr["segments"]):
        mat = vmats.get(seg.get("material_id"), {})
        name = mat.get("material_name") or mat.get("name")
        if name == SCENE_NAME:
            target_seg = seg
            target_idx = i
            target_mat = mat
            break

    if target_seg is None:
        print(f"Не нашёл {SCENE_NAME} на main-треке.")
        return 1

    material_dur = int(target_mat.get("duration") or 0)
    tt = target_seg["target_timerange"]
    target_dur = int(tt["duration"])

    # Сколько секунд клипа доступно от offset до конца материала.
    available_us = material_dur - OFFSET_US
    if available_us <= 0:
        print(f"⚠ offset {OFFSET_US/1e6:.2f}s ≥ длины материала "
              f"{material_dur/1e6:.2f}s — нечего показывать. Прерываю.")
        return 1

    if available_us >= target_dur:
        # Хватает без замедления.
        new_speed = 1.0
        new_src_dur = target_dur
        print(f"  scene_07: material={material_dur/1e6:.3f}s, offset={OFFSET_US/1e6:.2f}s, "
              f"available={available_us/1e6:.3f}s ≥ target={target_dur/1e6:.3f}s → speed=1.0")
    else:
        # Замедляем: чтобы available_us покрыл target_dur при speed<1.
        # speed = source_dur / target_dur (source_dur = available_us).
        new_speed = available_us / target_dur
        if new_speed < MIN_SPEED:
            print(f"⚠ Требуется speed={new_speed:.3f}, что ниже порога {MIN_SPEED}. "
                  f"Прерываю — артефакты будут заметны. Уменьши offset или укоротите аудио.")
            return 1
        new_src_dur = available_us
        print(f"  scene_07: material={material_dur/1e6:.3f}s, offset={OFFSET_US/1e6:.2f}s, "
              f"available={available_us/1e6:.3f}s < target={target_dur/1e6:.3f}s → "
              f"speed={new_speed:.3f} (slow-mo)")

    src = target_seg.setdefault("source_timerange", {"start": 0, "duration": target_dur})
    src["start"] = OFFSET_US
    src["duration"] = int(new_src_dur)
    target_seg["speed"] = new_speed

    # Бэкап.
    bkp = DRAFT_FILE.with_suffix(".json.offset07-backup")
    shutil.copy2(DRAFT_FILE, bkp)
    print(f"  Бэкап: {bkp.name}")

    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = YAGA_DIR / tgt_name
        try:
            shutil.copy2(DRAFT_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    print("✓ Готово. Открой CapCut → проект «Баба-Яга» → проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
