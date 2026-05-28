"""
Один-разовый патч: убирает видео-сегмент scene_16 из main-video-трека
драфта «Баба-Яга» и расширяет scene_15 на освободившуюся длительность.

Voice / music / karaoke / sfx-треки НЕ трогаются — sentence_015 и
sentence_016 продолжают звучать как обычно, караоке-слова остаются на
своих абсолютных таймстампах. Просто визуально вместо двух разных
кадров (15 и 16) теперь идёт растянутый scene_15_v1.mp4.

CapCut должен быть полностью закрыт (включая трей).
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

# Имена материалов, по которым ищем сегменты на видео-треке.
KEEP_NAME = "scene_15_v1.mp4"
DROP_NAME = "scene_16_v1.mp4"

# Длительность mp4-материала scene_15_v1 в µs (ffprobe → 4.000s). Нужна,
# чтобы убедиться, что расширенный target не превысит длительность файла —
# иначе pycapcut/CapCut поднимут «截取的素材时间范围 ... 超出了素材时长».
SCENE_15_MATERIAL_DURATION_US = 4_000_000


def find_main_video_track(draft: dict) -> dict:
    for t in draft["tracks"]:
        if t.get("type") == "video" and t.get("name") == "main":
            return t
    raise RuntimeError("В драфте нет video-трека main.")


def find_segments(main: dict, vmats: dict, name: str) -> list[int]:
    """Возвращает индексы сегментов на main-треке, чей material имеет данное name."""
    idx = []
    for i, seg in enumerate(main["segments"]):
        mat = vmats.get(seg.get("material_id"), {})
        mname = mat.get("material_name") or mat.get("name")
        if mname == name:
            idx.append(i)
    return idx


def main() -> int:
    if not DRAFT_FILE.is_file():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1

    print(f"Читаю драфт: {DRAFT_FILE}")
    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))

    main = find_main_video_track(draft)
    vmats = {m["id"]: m for m in draft["materials"].get("videos", [])}

    keep_idxs = find_segments(main, vmats, KEEP_NAME)
    drop_idxs = find_segments(main, vmats, DROP_NAME)
    if len(keep_idxs) != 1 or len(drop_idxs) != 1:
        print(f"Ожидал ровно по одному сегменту {KEEP_NAME} и {DROP_NAME}, "
              f"нашёл keep={keep_idxs} drop={drop_idxs}")
        return 1

    keep_idx = keep_idxs[0]
    drop_idx = drop_idxs[0]
    if drop_idx != keep_idx + 1:
        print(f"Ожидал {DROP_NAME} сразу после {KEEP_NAME} "
              f"(keep_idx={keep_idx}, drop_idx={drop_idx}). Прерываю.")
        return 1

    keep_seg = main["segments"][keep_idx]
    drop_seg = main["segments"][drop_idx]

    keep_tt = keep_seg["target_timerange"]
    drop_tt = drop_seg["target_timerange"]

    # Расширяем target на длительность дропнутого сегмента.
    new_target_dur = int(keep_tt["duration"]) + int(drop_tt["duration"])

    # Source: pycapcut по умолчанию = [0, target_dur] при speed=1.
    # Расширяем source_timerange на ту же дельту, если он задан.
    keep_src = keep_seg.get("source_timerange") or None
    if keep_src is not None:
        # source.start не трогаем, дотягиваем дюрацию.
        new_src_dur = int(new_target_dur)  # speed=1.0
        if new_src_dur > SCENE_15_MATERIAL_DURATION_US:
            print(f"⚠ Расширенный source ({new_src_dur}µs) превышает длину файла "
                  f"scene_15_v1.mp4 ({SCENE_15_MATERIAL_DURATION_US}µs). Прерываю.")
            return 1
        keep_src["duration"] = new_src_dur

    keep_tt["duration"] = new_target_dur

    # Удаляем drop-сегмент из трека. Его transition material остаётся в
    # materials.transitions, но не на что не ссылается — безопасно
    # (CapCut просто не нарисует переход без сегмента-владельца).
    main["segments"].pop(drop_idx)

    print(f"  scene_15: target.duration {keep_tt['duration']/1e6:.3f}s "
          f"(+{drop_tt['duration']/1e6:.3f}s от scene_16)")
    print(f"  scene_16: удалён из main-видео-трека")
    print(f"  main-трек теперь содержит {len(main['segments'])} сегментов "
          f"(было 23, стало 22)")

    # Бэкап.
    bkp = DRAFT_FILE.with_suffix(".json.merge15-16-backup")
    shutil.copy2(DRAFT_FILE, bkp)
    print(f"  Бэкап: {bkp.name}")

    # Записываем + синхронизируем CapCut-кэши.
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
