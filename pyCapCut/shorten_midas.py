"""
Создаёт копию проекта CapCut «Мидас и золотое прикосновение» под именем
«Мидас и золотое прикосновение ОБРЕЗАННЫЙ» и вырезает из неё набор сцен,
чтобы итоговая длина получилась < 60 секунд (для YouTube Shorts).

Что удаляется:
  04, 05, 07, 12, 14, 17, 20, 23  —  декоративные сцены, не двигающие сюжет.

Алгоритм (ripple-delete):
  1. Копируем папку проекта.
  2. По именам файлов видео (scene_NN_v1.mp4) находим target_timerange
     удаляемых сцен на main-видео-треке.
  3. На каждой дорожке:
       - сегмент ПОЛНОСТЬЮ внутри cut-интервала → удаляем
       - сегмент ПОЛНОСТЬЮ после cut-интервала  → сдвигаем start влево
         на сумму всех cut-интервалов до него
       - сегмент ПЕРЕСЕКАЕТСЯ с cut-интервалом (музыка) → укорачиваем,
         подгоняем keyframes
  4. Сохраняем в новый draft_content.json + синхронизируем кэши.

CapCut сам подхватит новый проект в списке при следующем запуске.
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ────────────────────────────────────────────────────────────
PROJECTS_ROOT = Path(os.environ["LOCALAPPDATA"]) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
SRC_NAME = "Мидас и золотое прикосновение"
DST_NAME = "Мидас и золотое прикосновение ОБРЕЗАННЫЙ"
SRC = PROJECTS_ROOT / SRC_NAME
DST = PROJECTS_ROOT / DST_NAME

CUT_SCENES = {"04", "05", "07", "12", "14", "17", "20", "23"}


# ────────────────────────────────────────────────────────────
# 1. Копируем папку проекта
# ────────────────────────────────────────────────────────────

if DST.exists():
    print(f"Папка {DST.name} уже существует — удаляю.")
    shutil.rmtree(DST)
print(f"Копирую {SRC.name} → {DST.name}...")
shutil.copytree(SRC, DST)


# ────────────────────────────────────────────────────────────
# 2. Загружаем draft_content.json копии
# ────────────────────────────────────────────────────────────

draft_path = DST / "draft_content.json"
d = json.load(open(draft_path, encoding="utf-8"))


# ────────────────────────────────────────────────────────────
# 3. Находим cut-интервалы по именам видеофайлов
# ────────────────────────────────────────────────────────────

videos_by_id = {v["id"]: v for v in d["materials"]["videos"]}
cut_intervals: list[tuple[int, int]] = []

for tr in d["tracks"]:
    if tr.get("type") != "video" or tr.get("name") != "main":
        continue
    for s in tr["segments"]:
        vid = videos_by_id.get(s["material_id"], {})
        fname = os.path.basename(vid.get("path", ""))
        m = re.match(r"scene_(\d+)", fname)
        if m and m.group(1) in CUT_SCENES:
            start = s["target_timerange"]["start"]
            dur = s["target_timerange"]["duration"]
            cut_intervals.append((start, start + dur))

cut_intervals.sort()
total_cut_us = sum(e - s for s, e in cut_intervals)
print(f"Вырезаем {len(cut_intervals)} сцен, суммарно {total_cut_us/1_000_000:.2f} с.")
for s, e in cut_intervals:
    print(f"  {s/1_000_000:6.2f} – {e/1_000_000:6.2f} с  ({(e-s)/1_000_000:.2f})")


# ────────────────────────────────────────────────────────────
# 4. Хелперы для ripple-delete
# ────────────────────────────────────────────────────────────

def cut_before(t_us: int) -> int:
    """Сумма всех cut-интервалов, которые полностью ДО позиции t_us."""
    total = 0
    for cs, ce in cut_intervals:
        if t_us >= ce:
            total += ce - cs
    return total


def overlap_inside(start_us: int, end_us: int) -> int:
    """Сумма cut-интервалов, попадающих ВНУТРЬ [start, end)."""
    total = 0
    for cs, ce in cut_intervals:
        a = max(cs, start_us)
        b = min(ce, end_us)
        if b > a:
            total += b - a
    return total


def is_fully_inside_cut(start_us: int, end_us: int) -> bool:
    for cs, ce in cut_intervals:
        if start_us >= cs and end_us <= ce:
            return True
    return False


def shift_kfs_within(segment, start_us_old: int, end_us_old: int):
    """Сдвигает keyframes внутри сегмента при сжатии. keyframes заданы
    относительно segment start."""
    new_start = segment["target_timerange"]["start"]
    new_dur = segment["target_timerange"]["duration"]

    for kf_block in segment.get("common_keyframes", []):
        new_list = []
        for k in kf_block.get("keyframe_list", []):
            # абсолютное время этого keyframe на ОРИГИНАЛЬНОЙ шкале
            kf_abs = start_us_old + k["time_offset"]
            # если keyframe внутри какой-то вырезанной зоны — дропаем
            inside_cut = False
            cuts_before_kf = 0
            for cs, ce in cut_intervals:
                if cs <= kf_abs < ce:
                    inside_cut = True
                    break
                if kf_abs >= ce:
                    cuts_before_kf += ce - cs
            if inside_cut:
                continue
            # новое абсолютное время
            kf_abs_new = kf_abs - cuts_before_kf
            kf_rel_new = kf_abs_new - new_start
            if kf_rel_new < 0 or kf_rel_new > new_dur:
                continue
            k["time_offset"] = int(kf_rel_new)
            new_list.append(k)
        kf_block["keyframe_list"] = new_list


# ────────────────────────────────────────────────────────────
# 5. Ripple-delete по каждой дорожке
# ────────────────────────────────────────────────────────────

total_removed = 0
total_shifted = 0
total_trimmed = 0

for tr in d["tracks"]:
    new_segs = []
    for s in tr.get("segments", []):
        start = s["target_timerange"]["start"]
        dur = s["target_timerange"]["duration"]
        end = start + dur

        if is_fully_inside_cut(start, end):
            total_removed += 1
            continue

        ov = overlap_inside(start, end)
        if ov > 0:
            # сегмент длинный и пересекает cut'ы (обычно — музыка).
            # Новый старт = old_start - cut_before(old_start).
            # Новая длительность = old_dur - overlap_inside.
            old_start = start
            old_end = end
            new_start = start - cut_before(start)
            new_dur = dur - ov
            s["target_timerange"]["start"] = int(new_start)
            s["target_timerange"]["duration"] = int(new_dur)
            if s.get("source_timerange"):
                s["source_timerange"]["duration"] = int(new_dur)
            shift_kfs_within(s, old_start, old_end)
            total_trimmed += 1
        else:
            # сегмент полностью до/после cut'ов — просто shift
            shift = cut_before(start)
            if shift > 0:
                s["target_timerange"]["start"] = int(start - shift)
                total_shifted += 1

        new_segs.append(s)
    tr["segments"] = new_segs

print(f"\nОбработано:")
print(f"  удалено сегментов:  {total_removed}")
print(f"  сдвинуто:           {total_shifted}")
print(f"  укорочено (muzika): {total_trimmed}")


# ────────────────────────────────────────────────────────────
# 6. Считаем новую длину
# ────────────────────────────────────────────────────────────

video_end_us = 0
for tr in d["tracks"]:
    if tr.get("type") == "video":
        for s in tr["segments"]:
            end = s["target_timerange"]["start"] + s["target_timerange"]["duration"]
            if end > video_end_us:
                video_end_us = end
print(f"\nНовая длина видео: {video_end_us/1_000_000:.2f} с")


# ────────────────────────────────────────────────────────────
# 7. Обновляем draft_meta_info.json (новый ID + имя)
# ────────────────────────────────────────────────────────────

meta_path = DST / "draft_meta_info.json"
meta = json.load(open(meta_path, encoding="utf-8"))
new_id = str(uuid.uuid4()).upper()
meta["draft_id"] = new_id
meta["draft_name"] = DST_NAME
meta["draft_fold_path"] = str(DST).replace("\\", "/")
if "draft_timeline_materials_size_" in meta:
    # размер считаем по файлу позже, сейчас оставим как есть
    pass
json.dump(meta, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
print(f"✓ draft_meta_info.json обновлён (новый id={new_id[:8]}...)")


# ────────────────────────────────────────────────────────────
# 8. Сохраняем draft_content.json + синхронизируем кэши
# ────────────────────────────────────────────────────────────

json.dump(d, open(draft_path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
for cache_name in ("template-2.tmp", "draft_content.json.bak"):
    tgt = DST / cache_name
    if tgt.exists():
        shutil.copy2(draft_path, tgt)
print("✓ draft_content.json + кэши сохранены.")


# ────────────────────────────────────────────────────────────
# 9. Обновляем root_meta_info.json — добавляем запись о новом драфте
# ────────────────────────────────────────────────────────────

root_meta_path = PROJECTS_ROOT / "root_meta_info.json"
root_meta = json.load(open(root_meta_path, encoding="utf-8"))
store = root_meta.get("all_draft_store", [])

# берём шаблон из существующей записи про Мидаса
template_entry = None
for e in store:
    if e.get("draft_name") == SRC_NAME:
        template_entry = dict(e)
        break

if template_entry:
    # удаляем уже существующую запись ОБРЕЗАННЫЙ (если была)
    store[:] = [e for e in store if e.get("draft_name") != DST_NAME]

    new_entry = dict(template_entry)
    new_entry["draft_id"] = new_id
    new_entry["draft_name"] = DST_NAME
    new_entry["draft_fold_path"] = str(DST).replace("\\", "/")
    if "draft_cover" in new_entry:
        new_entry["draft_cover"] = str(DST / "draft_cover.jpg").replace("\\", "/")
    store.insert(0, new_entry)
    root_meta["all_draft_store"] = store
    json.dump(root_meta, open(root_meta_path, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"✓ root_meta_info.json обновлён — новый проект добавлен в список.")
else:
    print("⚠ Не нашёл запись-шаблон в root_meta_info.json — CapCut должен всё равно подхватить папку.")

print(f"\n✅ Готово. Новый проект: {DST_NAME}")
print(f"   Папка: {DST}")
print(f"   Длина: {video_end_us/1_000_000:.2f} с")
