"""
Продлевает стикеры до конца их сцены (main-сегмента) и добавляет
непрерывное вертикальное подпрыгивание `y → y+0.07 → y` каждые 600 мс
на всю новую длительность.

Драфт: «От Хаоса до Олимпа Ч.02 Власть Кроноса» (НЕ «(новый)»).

Логика:
  1. Для каждого стикера ищем main-сегмент, чей `target_timerange`
     содержит начало стикера. Новая длительность стикера =
     (конец main-сегмента) − (старт стикера).
  2. Удаляем существующий KFTypePositionY-блок (если был от старого
     одиночного бауса) и кладём новый: keyframes на 0/300/600/900/...
     каждые 300 мс, чередуя y и y+0.07, заканчивая на y в конце
     последнего полного 600-мс цикла. После последнего keyframe
     стикер «оседает» в y до окончания сцены.

Идемпотентен: повторный прогон производит тот же результат
(пересоздаёт keyframes от текущего y).

Запуск (CapCut должен быть закрыт):
    python pyCapCut/add_oh_02_sticker_extend_and_bounce.py
    python pyCapCut/add_oh_02_sticker_extend_and_bounce.py --dry-run
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
import uuid
from pathlib import Path
from typing import List, Optional

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFT_DIR = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft" / "От Хаоса до Олимпа Ч.02 Власть Кроноса"
DRAFT_FILE = DRAFT_DIR / "draft_content.json"

BOUNCE_OFFSET = 0.07
HALF_PERIOD_US = 300_000  # 300 ms; полный цикл = 600 ms


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


def make_continuous_bounce_block(duration_us: int, y: float) -> Optional[dict]:
    """Цепочка keyframes y/y+off/y/y+off/... каждые 300 мс до duration_us.
    Заканчивается на y в конце последнего полного 600-мс цикла, чтобы
    стикер «оседал» к финалу, а не застывал в верхней точке."""
    period_us = 2 * HALF_PERIOD_US
    n_cycles = duration_us // period_us
    if n_cycles == 0:
        # Сцена короче полного цикла — обойдёмся одной точкой y
        kfs = [make_position_y_keyframe(0, y)]
    else:
        kfs = []
        for cycle in range(n_cycles):
            start = cycle * period_us
            kfs.append(make_position_y_keyframe(start, y))
            kfs.append(make_position_y_keyframe(start + HALF_PERIOD_US, y + BOUNCE_OFFSET))
        # финальный «осад» в y в конце последнего полного цикла
        kfs.append(make_position_y_keyframe(n_cycles * period_us, y))
    return {
        "id": gen_id_hex(),
        "material_id": "",
        "property_type": "KFTypePositionY",
        "keyframe_list": kfs,
    }


def find_main_shot_end_us(main_segments: list, start_us: int) -> Optional[int]:
    """Конец main-сегмента, чьё target_timerange содержит start_us."""
    for seg in main_segments:
        t = seg["target_timerange"]
        seg_start = t["start"]
        seg_end = seg_start + t["duration"]
        if seg_start <= start_us < seg_end:
            return seg_end
    return None


def apply(draft: dict) -> List[str]:
    log: List[str] = []
    main_track = next(t for t in draft["tracks"] if t.get("name") == "main")
    sticker_track = next(
        (t for t in draft["tracks"] if t.get("name") == "stickers" or t.get("type") == "sticker"),
        None,
    )
    if sticker_track is None:
        log.append("⚠ трек 'stickers' не найден — нечего делать")
        return log

    mat_name = {v["id"]: v.get("material_name", "") for v in draft["materials"]["videos"]}
    main_segs = main_track["segments"]

    for i, seg in enumerate(sticker_track["segments"]):
        tr_range = seg["target_timerange"]
        start_us = tr_range["start"]
        old_dur_us = tr_range["duration"]

        shot_end = find_main_shot_end_us(main_segs, start_us)
        if shot_end is None:
            log.append(f"  seg{i:>2}: не нашёл main-сцену для start={start_us/1e6:.2f}s — пропуск")
            continue

        new_dur_us = shot_end - start_us
        if new_dur_us <= 0:
            log.append(f"  seg{i:>2}: new_dur_us<=0 (start уже после конца) — пропуск")
            continue

        # Расширить target_timerange.
        # ВАЖНО: для photo source_timerange.duration тоже надо растянуть,
        # иначе CapCut показывает картинку только source-длительность,
        # а оставшееся время в сегменте отображается «пустой рамкой»
        # (которая всё ещё двигается от наших keyframes).
        tr_range["duration"] = new_dur_us
        src_range = seg.get("source_timerange") or {}
        if src_range:
            src_range["duration"] = new_dur_us

        # Получить текущий y
        clip = seg.get("clip") or {}
        transform = clip.get("transform") or {}
        y = transform.get("y")
        if y is None:
            log.append(f"  seg{i:>2}: нет clip.transform.y — расширил длительность, баус пропустил")
            continue

        # Снести старый KFTypePositionY-блок и положить новый
        existing = seg.get("common_keyframes", []) or []
        cleaned = [b for b in existing if b.get("property_type") != "KFTypePositionY"]
        block = make_continuous_bounce_block(new_dur_us, float(y))
        if block is not None:
            cleaned.append(block)
        seg["common_keyframes"] = cleaned

        name = mat_name.get(seg["material_id"], "?")[:48]
        kf_count = len(block["keyframe_list"]) if block else 0
        log.append(
            f"  seg{i:>2}: {name:<48}  "
            f"start={start_us/1e6:6.2f}s  "
            f"dur {old_dur_us/1e6:.2f}s → {new_dur_us/1e6:.2f}s  "
            f"bounce kf={kf_count} (y={y:.3f}, +{BOUNCE_OFFSET:.2f})"
        )

    return log


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Только показать план, не писать драфт.")
    args = p.parse_args()

    if not DRAFT_FILE.is_file():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1

    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой его полностью (включая трей) и перезапусти.")
        return 1

    print(f"Читаю драфт: {DRAFT_FILE}")
    with open(DRAFT_FILE, encoding="utf-8") as f:
        draft = json.load(f)

    print()
    print("Стикеры: расширение до конца сцены + непрерывный bounce:")
    for line in apply(draft):
        print(line)

    if args.dry_run:
        print("\n--dry-run: драфт не трогаю.")
        return 0

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DRAFT_DIR / f"draft_content.json.bounce-backup-{ts}"
    shutil.copy2(DRAFT_FILE, backup)
    print(f"\nБэкап: {backup.name}")

    with open(DRAFT_FILE, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = DRAFT_DIR / tgt_name
        try:
            shutil.copy2(DRAFT_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    print("\n✓ Готово. Открой CapCut → проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
