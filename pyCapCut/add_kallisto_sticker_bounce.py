"""
Циклическая качка стикеров на всю длительность сцены + растягивание
стикеров до длительности сцены — для драфта «Каллисто и Аркас».

ВАЖНО (правило обновлено 2026-05-21 на Каллисто, см. CAPCUT.md §4.3):
  - Стикер растягивается на ВСЮ свою сцену
    (target.start = scene.start, target.duration = scene.duration).
  - Качка y → y+0.07 → y → y+0.07 → ... тоже идёт ВСЮ длительность,
    keyframes на каждые 300 мс (полупериод), плюс финальный возврат
    к base_y на конце сцены. Один keyframe-блок KFTypePositionY с
    14-20 кадрами вместо старых трёх (0/300/600 ms).
  - Скрипт запускается ПОСЛЕ ручных правок пользователя в CapCut
    (третий проход в трёх-проходном пайплайне стикеров). Скрипт читает
    текущие clip.transform.y, удаляет лишние стикеры пользователя не
    касается (их просто нет в треке).
  - Идемпотентность: при повторном прогоне старые KFTypePositionY
    перетираются новой циклической качкой на новую длительность сцены.

Запуск (CapCut должен быть закрыт):
    python pyCapCut/add_kallisto_sticker_bounce.py
    python pyCapCut/add_kallisto_sticker_bounce.py --dry-run
    python pyCapCut/add_kallisto_sticker_bounce.py --name "Каллисто v2"
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
DRAFTS_ROOT = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
DEFAULT_PROJECT_NAME = "Каллисто и Аркас"


# ─────────────────────────────────────────────────────────────────────
# Параметры подпрыгивания — циклическая качка на всю длительность сцены.
# CAPCUT.md §4.3 (обновлено 2026-05-21).
# ─────────────────────────────────────────────────────────────────────

BOUNCE_OFFSET = 0.07              # амплитуда: y → y+0.07 → y
BOUNCE_HALF_PERIOD_US = 300_000   # 300 ms на половину цикла (полный период = 600 ms)


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


def make_looped_bounce_keyframes(base_y: float, duration_us: int) -> dict:
    """Циклическая качка y → y+0.07 → y → y+0.07 → ... до конца duration_us.
    Кадры через BOUNCE_HALF_PERIOD_US (=300 ms). Чётные индексы — base_y,
    нечётные — base_y+offset. Финальный кадр на ровно duration_us возвращает
    к base_y (мягкое приземление в конце сцены)."""
    keyframes = []
    t = 0
    i = 0
    while t < duration_us:
        y = base_y + (BOUNCE_OFFSET if (i % 2 == 1) else 0.0)
        keyframes.append(make_position_y_keyframe(t, y))
        t += BOUNCE_HALF_PERIOD_US
        i += 1
    keyframes.append(make_position_y_keyframe(duration_us, base_y))
    return {
        "id": gen_id_hex(),
        "material_id": "",
        "property_type": "KFTypePositionY",
        "keyframe_list": keyframes,
    }


# ─────────────────────────────────────────────────────────────────────
# Применение
# ─────────────────────────────────────────────────────────────────────

def apply_sticker_bounce(draft: dict) -> List[str]:
    """Растягивает каждый стикер на ВСЮ длительность своей сцены (по
    пересечению start с main-треком) и кладёт циклическую качку y±0.07
    с keyframes каждые 300ms на всю эту длительность. Идемпотентно:
    старые KFTypePositionY перетираются новой качкой."""
    log: List[str] = []
    stickers_track = next(
        (t for t in draft["tracks"]
         if t.get("name") == "stickers" or t.get("type") == "sticker"),
        None,
    )
    if not stickers_track:
        log.append("WARN трек 'stickers' не найден — качка пропущена")
        return log

    main = next((t for t in draft["tracks"]
                 if t["type"] == "video" and t.get("name") == "main"), None)
    if main is None:
        log.append("WARN трек 'main' не найден — качка пропущена")
        return log

    # Карта сцен main-трека: [(start_us, dur_us)]
    main_scenes = [(int(s["target_timerange"]["start"]),
                    int(s["target_timerange"]["duration"]))
                   for s in main.get("segments", [])]

    processed = 0
    for i, seg in enumerate(stickers_track.get("segments", [])):
        clip = seg.get("clip") or {}
        tr = clip.get("transform") or {}
        y = tr.get("y")
        if y is None:
            log.append(f"  seg{i:>2}: нет clip.transform.y — пропуск")
            continue

        # Найти сцену по пересечению start стикера
        old_start = int(seg["target_timerange"]["start"])
        scene = next(((st, du) for (st, du) in main_scenes if st <= old_start < st + du), None)
        if scene is None:
            log.append(f"  seg{i:>2}: не нашёл сцену для стикера на {old_start/1e6:.3f}s — пропуск")
            continue
        scene_start, scene_dur = scene

        # Растягиваем стикер на всю сцену — И target, И source.
        # КРИТИЧНО: source_timerange.duration должен совпадать с
        # target_timerange.duration. Иначе CapCut анимирует "рамку"
        # сегмента на target, а PNG показывается только source — после
        # source-длительности картинка "замирает", но common_keyframes
        # KFTypePositionY продолжают двигать сегмент. Визуально это
        # выглядит как "трясущаяся рамка вокруг неподвижного стикера".
        # Для статичного PNG source-длительность не имеет смысла —
        # один кадр всё равно.
        seg["target_timerange"]["start"] = scene_start
        seg["target_timerange"]["duration"] = scene_dur
        seg.setdefault("source_timerange", {"start": 0, "duration": 0})
        seg["source_timerange"]["start"] = 0
        seg["source_timerange"]["duration"] = scene_dur
        seg["speed"] = 1.0  # явно, чтобы не было таймстретча

        # Перетираем старые KFTypePositionY новой циклической качкой
        existing = seg.get("common_keyframes") or []
        existing_clean = [b for b in existing if b.get("property_type") != "KFTypePositionY"]
        block = make_looped_bounce_keyframes(float(y), scene_dur)
        seg["common_keyframes"] = existing_clean + [block]

        n_kf = len(block["keyframe_list"])
        log.append(f"  seg{i:>2}: dur={scene_dur/1e6:.3f}s, y={y:.4f}±{BOUNCE_OFFSET:.2f}, "
                   f"{n_kf} keyframes (every {BOUNCE_HALF_PERIOD_US//1000}ms)")
        processed += 1

    log.append(f"OK обработано стикеров: {processed}")
    return log


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--name", default=DEFAULT_PROJECT_NAME, help="Имя проекта в CapCut.")
    p.add_argument("--dry-run", action="store_true", help="Только показать план, не писать драфт.")
    args = p.parse_args()

    draft_dir = DRAFTS_ROOT / args.name
    draft_file = draft_dir / "draft_content.json"

    if not draft_file.is_file():
        print(f"Не нашёл драфт: {draft_file}")
        print("Сначала запусти: python pyCapCut/build_kallisto.py")
        return 1

    if not args.dry_run and not check_capcut_closed():
        print("WARN CapCut запущен. Закрой его полностью (включая трей) и перезапусти скрипт.")
        return 1

    print(f"Читаю драфт: {draft_file}")
    draft = json.load(open(draft_file, encoding="utf-8"))

    print()
    print("Подпрыгивание стикеров:")
    for line in apply_sticker_bounce(draft):
        print(line)

    if args.dry_run:
        print("\n--dry-run: драфт не трогаю.")
        return 0

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = draft_dir / f"draft_content.json.bounce-backup-{ts}"
    shutil.copy2(draft_file, backup)
    print(f"\nБэкап: {backup.name}")

    json.dump(draft, open(draft_file, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = draft_dir / tgt_name
        try:
            shutil.copy2(draft_file, tgt)
        except Exception as ex:
            print(f"  WARN не удалось синхронизировать {tgt_name}: {ex}")

    print("\nOK Готово. Открой CapCut -> Drafts -> «Каллисто и Аркас» -> проверь качку стикеров.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
