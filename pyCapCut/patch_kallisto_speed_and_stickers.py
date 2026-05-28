"""
Точечный патч для драфта «Каллисто и Аркас»:

  1. seg 9 (scene_10_v2.mp4 — изгнание Каллисто) — speed=0.6, источник
     обрезается до 2.4с (target.dur 4.0с * speed 0.6). Slow-motion,
     видео не показывается до конца.

  2. Для всех оставшихся стикеров в треке "stickers" (после ручных
     правок пользователя):
       - target_timerange растягивается на ВСЮ длительность своей сцены
         (start = scene.start, duration = scene.duration);
       - common_keyframes пересобираются: KFTypePositionY с циклической
         качкой y → y+0.07 → y с периодом 600ms на всю длительность.
     Музыка, voice, sticker_sfx, артемида-карточка, halftone и любые
     другие треки НЕ трогаются.

CapCut должен быть полностью закрыт.
"""

from __future__ import annotations

import datetime
import io
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


LOCALAPPDATA = Path(os.environ["LOCALAPPDATA"])
DRAFTS = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
KALLISTO_DIR = DRAFTS / "Каллисто и Аркас"
DRAFT_FILE = KALLISTO_DIR / "draft_content.json"

# Item 1 — скорость на сцене 10
SCENE_10_FILE = "scene_10_v2.mp4"
SCENE_10_SPEED = 0.6

# Item 2 — параметры качки стикеров (канон CAPCUT.md §4.3 / эталон Одиссея)
BOUNCE_OFFSET = 0.07
BOUNCE_HALF_PERIOD_US = 300_000   # y → y+0.07 за 300ms, y+0.07 → y за 300ms (полный цикл 600ms)


def gen_id_hex() -> str:
    return uuid.uuid4().hex


def check_capcut_closed() -> bool:
    try:
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
        text = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        if "CapCut.exe" in text or "JianyingPro" in text:
            return False
    except Exception:
        pass
    return True


def make_position_y_keyframe(time_us: int, y: float) -> dict:
    return {
        "id": gen_id_hex(),
        "curveType": "Line",
        "time_offset": int(time_us),
        "left_control": {"x": 0.0, "y": 0.0},
        "right_control": {"x": 0.0, "y": 0.0},
        "values": [float(y)],
        "string_value": "",
        "graphID": "",
    }


def make_looped_bounce_keyframes(base_y: float, duration_us: int) -> dict:
    """Циклическая качка y → y+0.07 → y → y+0.07 → ... до конца duration.
    Кадры через каждые 300ms (=BOUNCE_HALF_PERIOD_US). Чётные индексы — base_y,
    нечётные — base_y+offset. Закрываем последним кадром на ровно duration_us."""
    keyframes = []
    t = 0
    i = 0
    while t < duration_us:
        y = base_y + (BOUNCE_OFFSET if (i % 2 == 1) else 0.0)
        keyframes.append(make_position_y_keyframe(t, y))
        t += BOUNCE_HALF_PERIOD_US
        i += 1
    # Финальный кадр на конце — возвращаем к base_y (мягкое приземление)
    keyframes.append(make_position_y_keyframe(duration_us, base_y))
    return {
        "id": gen_id_hex(),
        "material_id": "",
        "property_type": "KFTypePositionY",
        "keyframe_list": keyframes,
    }


def apply_scene10_speed(draft: dict) -> str:
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    videos_by_id = {v["id"]: v for v in draft["materials"]["videos"]}
    for i, seg in enumerate(main["segments"]):
        mat = videos_by_id.get(seg["material_id"], {})
        fname = Path(mat.get("path", "")).name
        if fname != SCENE_10_FILE:
            continue
        target_dur = int(seg["target_timerange"]["duration"])
        new_src_dur = int(target_dur * SCENE_10_SPEED)
        # Обновляем source_timerange и speed
        seg.setdefault("source_timerange", {"start": 0, "duration": 0})
        seg["source_timerange"]["start"] = 0
        seg["source_timerange"]["duration"] = new_src_dur
        seg["speed"] = SCENE_10_SPEED
        return (f"  OK seg{i} {fname}: speed={SCENE_10_SPEED}, "
                f"source.dur={new_src_dur/1e6:.3f}s "
                f"(из {target_dur/1e6:.3f}s target), показывается {new_src_dur/1e6:.3f}s из {mat.get('duration',0)/1e6:.3f}s исходника")
    return f"  WARN: {SCENE_10_FILE} не найден в main треке"


def apply_stickers_stretch_and_bounce(draft: dict) -> list[str]:
    log: list[str] = []
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    stickers = next((t for t in draft["tracks"]
                     if t["type"] == "video" and t.get("name") == "stickers"), None)
    if stickers is None:
        return ["  WARN: трек stickers не найден"]

    videos_by_id = {v["id"]: v for v in draft["materials"]["videos"]}
    scene_segments = []
    for i, seg in enumerate(main["segments"]):
        mat = videos_by_id.get(seg["material_id"], {})
        fname = Path(mat.get("path", "")).name
        scene_segments.append((i, fname, seg["target_timerange"]["start"], seg["target_timerange"]["duration"]))

    for s_i, s_seg in enumerate(stickers["segments"]):
        mat = videos_by_id.get(s_seg["material_id"], {})
        fname = Path(mat.get("path", "")).name
        old_ttr = s_seg["target_timerange"]
        # Найти сцену в main, к которой стикер привязан (по пересечению start)
        scene = None
        for (idx, fn, st, du) in scene_segments:
            if st <= old_ttr["start"] < st + du:
                scene = (idx, fn, st, du)
                break
        if scene is None:
            log.append(f"  WARN sticker{s_i} {fname}: не нашёл сцену по start={old_ttr['start']/1e6:.3f}s")
            continue
        scene_idx, scene_name, scene_start, scene_dur = scene

        # Растягиваем стикер на всю сцену
        s_seg["target_timerange"]["start"] = int(scene_start)
        s_seg["target_timerange"]["duration"] = int(scene_dur)

        # Текущая позиция Y (после ручных правок пользователя)
        clip = s_seg.get("clip") or {}
        transform = clip.get("transform") or {}
        base_y = float(transform.get("y", 0.39))

        # Снимаем старые KFTypePositionY (если были) и ставим новые на всю длительность
        existing = s_seg.get("common_keyframes") or []
        existing_without_y = [b for b in existing if b.get("property_type") != "KFTypePositionY"]
        bounce_block = make_looped_bounce_keyframes(base_y, int(scene_dur))
        s_seg["common_keyframes"] = existing_without_y + [bounce_block]

        n_keyframes = len(bounce_block["keyframe_list"])
        log.append(
            f"  sticker{s_i:>2} {fname[:50]}: "
            f"start {old_ttr['start']/1e6:.3f}s→{scene_start/1e6:.3f}s, "
            f"dur {old_ttr['duration']/1e6:.3f}s→{scene_dur/1e6:.3f}s "
            f"(сцена {scene_name}), bounce y={base_y:.3f}±{BOUNCE_OFFSET} x{n_keyframes} кадров"
        )
    return log


def main() -> int:
    if not DRAFT_FILE.is_file():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1
    if not check_capcut_closed():
        print("WARN CapCut запущен. Закрой полностью (включая трей) и перезапусти.")
        return 1

    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = KALLISTO_DIR / f"draft_content.json.speed-stickers-backup-{ts}"
    shutil.copy2(DRAFT_FILE, backup)
    print(f"Бэкап: {backup.name}")
    print()

    print(f"Item 1 — speed {SCENE_10_SPEED} на {SCENE_10_FILE}:")
    print(apply_scene10_speed(draft))
    print()

    print("Item 2 — растянуть стикеры на всю сцену + циклическая качка:")
    for line in apply_stickers_stretch_and_bounce(draft):
        print(line)
    print()

    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = KALLISTO_DIR / tgt_name
        try:
            shutil.copy2(DRAFT_FILE, tgt)
        except Exception as ex:
            print(f"  WARN не удалось синхронизировать {tgt_name}: {ex}")

    print("OK Готово. Музыка, voice, sticker_sfx, артемида-карточка и halftone не тронуты.")
    print("Открой CapCut → проверь сцену 10 (slow-mo) и стикеры (тянутся всю сцену, качаются).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
