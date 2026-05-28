"""
Добавляет лёгкую вертикальную «качку» (bounce) каждому стикеру в треке
`stickers` драфта «От Хаоса до Олимпа Ч.01 Хаос».

Запускать ПОСЛЕ того, как пользователь руками поправил позиции стикеров
в CapCut: скрипт читает текущие `clip.transform.y` из draft_content.json
(а не из STICKER_PLAN), и добавляет к ним KFTypePositionY-keyframes
`y → y+0.07 → y` на временах `0 / 300 / 600 ms` — как в CAPCUT.md §4.3
и эталоне Одиссея/Диониса.

Идемпотентность: если у сегмента уже есть KFTypePositionY-блок (повторный
прогон), скрипт его не трогает. Чтобы перегенерировать — вручную удалить
существующие keyframes в CapCut.

Запуск (CapCut должен быть закрыт):
    python pyCapCut/add_oh_01_sticker_bounce.py
    python pyCapCut/add_oh_01_sticker_bounce.py --dry-run
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
from typing import List

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ─────────────────────────────────────────────────────────────────────
# Пути
# ─────────────────────────────────────────────────────────────────────

LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFT_DIR = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft" / "От Хаоса до Олимпа Ч.01 Хаос"
DRAFT_FILE = DRAFT_DIR / "draft_content.json"


# ─────────────────────────────────────────────────────────────────────
# Параметры подпрыгивания — по CAPCUT.md §4.3 и эталону Одиссея.
# ─────────────────────────────────────────────────────────────────────

BOUNCE_OFFSET = 0.07           # y → y+0.07 → y (полная амплитуда)
BOUNCE_TIMES_US = (0, 300_000, 600_000)


# ─────────────────────────────────────────────────────────────────────
# Утилиты
# ─────────────────────────────────────────────────────────────────────

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


def make_bounce_keyframes(y: float) -> dict:
    t0, t1, t2 = BOUNCE_TIMES_US
    return {
        "id": gen_id_hex(),
        "material_id": "",
        "property_type": "KFTypePositionY",
        "keyframe_list": [
            make_position_y_keyframe(t0, y),
            make_position_y_keyframe(t1, y + BOUNCE_OFFSET),
            make_position_y_keyframe(t2, y),
        ],
    }


# ─────────────────────────────────────────────────────────────────────
# Применение
# ─────────────────────────────────────────────────────────────────────

def apply_sticker_bounce(draft: dict) -> List[str]:
    log: List[str] = []
    stickers_track = next(
        (t for t in draft["tracks"]
         if t.get("name") == "stickers" or t.get("type") == "sticker"),
        None,
    )
    if not stickers_track:
        log.append("⚠ трек 'stickers' не найден — качка пропущена")
        return log

    added = 0
    skipped = 0
    for i, seg in enumerate(stickers_track.get("segments", [])):
        # Если у стикера уже есть KFTypePositionY — не трогаем (повторный прогон).
        existing = seg.get("common_keyframes", []) or []
        has_y = any(b.get("property_type") == "KFTypePositionY" for b in existing)
        if has_y:
            skipped += 1
            log.append(f"  seg{i:>2}: уже есть KFTypePositionY — пропуск")
            continue

        clip = seg.get("clip") or {}
        tr = clip.get("transform") or {}
        y = tr.get("y")
        if y is None:
            log.append(f"  seg{i:>2}: нет clip.transform.y — пропуск")
            skipped += 1
            continue

        block = make_bounce_keyframes(float(y))
        seg["common_keyframes"] = list(existing) + [block]
        added += 1
        log.append(f"  seg{i:>2}: y={y:.4f} → +{BOUNCE_OFFSET:.2f} → y  (0/300/600 ms)")

    log.append(f"✓ качка стикеров: добавлено {added}, пропущено {skipped}")
    return log


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Только показать план, не писать драфт.")
    args = p.parse_args()

    if not DRAFT_FILE.is_file():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1

    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой его полностью (включая трей) и перезапусти скрипт.")
        return 1

    print(f"Читаю драфт: {DRAFT_FILE}")
    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))

    print()
    print("Подпрыгивание стикеров:")
    for line in apply_sticker_bounce(draft):
        print(line)

    if args.dry_run:
        print("\n--dry-run: драфт не трогаю.")
        return 0

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DRAFT_DIR / f"draft_content.json.bounce-backup-{ts}"
    shutil.copy2(DRAFT_FILE, backup)
    print(f"\nБэкап: {backup.name}")

    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = DRAFT_DIR / tgt_name
        try:
            shutil.copy2(DRAFT_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    print("\n✓ Готово. Открой CapCut → проверь подпрыгивание стикеров.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
