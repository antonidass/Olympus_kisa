"""
Карточка-объяснялка про Гермеса в драфт «Цирцея и Одиссей».

Берёт за основу свиток из живого драфта «Персефона и Аид» (см. CAPCUT.md § 4.6,
эталон карточки-объяснялки) и клонирует его в Цирцею на момент, когда в
sentence_010 произносится имя «Гермес» (сцена 9).

Тайминг (по _karaoke_cache_circe.json):
  sentence_010 стартует на 29.900с, длина 6.283с.
  Слово «гермез» внутри фразы: 1.38–1.82с.
  Свиток ставится на 1.38с от начала фразы → 31.280с в таймлайне (квантуется
  вниз до границы кадра 60fps). Длительность 3.78с (канон § 4.6), эффектный
  конец на 35.06с — сцена 9 кончается на 36.18с, есть запас.

НИЧЕГО, кроме новых 4-х треков, не трогает. Существующие правки пользователя
в CapCut сохраняются полностью.

Запуск (CapCut должен быть полностью закрыт):
    python add_circe_hermes_scroll.py
"""

from __future__ import annotations

import copy
import io
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFTS = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
SOURCE_PROJECT = "Персефона и Аид"
TARGET_PROJECT = "Цирцея и Одиссей"
SOURCE_FILE = DRAFTS / SOURCE_PROJECT / "draft_content.json"
TARGET_DIR = DRAFTS / TARGET_PROJECT
TARGET_FILE = TARGET_DIR / "draft_content.json"

SCROLL_TRACK = "hermes_scroll"
LOGO_TRACK = "hermes_scroll_logo"
TEXT_TRACK = "hermes_scroll_text"
SFX_TRACK = "hermes_scroll_sfx"

US = 1_000_000
FPS = 60


def floor_to_frame_us(us: int) -> int:
    frames = (us * FPS) // US
    return (frames * US) // FPS


# sentence_010 (sid=009) стартует на 29_900_000 µs.
# Слово «Гермес» начинается на 1.38с внутри фразы.
SENTENCE_010_START_US = 29_900_000
HERMES_OFFSET_US = 1_380_000
SCENE_START_US = floor_to_frame_us(SENTENCE_010_START_US + HERMES_OFFSET_US)
SCENE_DURATION_US = 3_783_334
SCENE_END_US = SCENE_START_US + SCENE_DURATION_US

# Старт исходной карточки в Персефоне (см. add_graiae_scroll / kallisto).
SOURCE_START_US = 15_150_000

SOURCE_SCROLL_SEG_ID = "4FAEA63F-EC31-4939-9F39-EC6CE680BB05"
SOURCE_LOGO_SEG_ID = "A1AF07AF-6A2C-452b-A393-61713F991701"
SOURCE_TEXT_SEG_ID = "28FF51E0-688C-45f0-9D25-2AB8EA0D3961"
SOURCE_SPARKLE_SEG_ID = "AF9C6831-B757-4bd4-9D8E-C7A047979E9B"
SOURCE_TYPING_SEG_ID = "DDBC1002-62F0-45f5-9118-B2BA0994ADCB"

CALLOUT_TEXT = "ГЕРМЕС — БОГ-ВЕСТНИК\nОЛИМПА И ПОСРЕДНИК\nМЕЖДУ БОГАМИ И ЛЮДЬМИ"
CALLOUT_NAME_LEN = len("ГЕРМЕС")

# Логотип канала — версия с прозрачным фоном (см. memory
# feedback_scroll_logo_transparent). channelLogo.png со сплошным
# фоном даёт светлую рамку вокруг мордочки кота на свитке.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGO_TRANSPARENT_PATH = PROJECT_ROOT / "assets" / "additional" / "channelLogoWithoutBackground.png"
LOGO_TRANSPARENT_NAME = "channelLogoWithoutBackground.png"


def check_capcut_closed() -> bool:
    try:
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
        text = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        return "CapCut.exe" not in text and "JianyingPro" not in text
    except Exception:
        return True


def gen_id() -> str:
    return uuid.uuid4().hex


def gen_uuid() -> str:
    return str(uuid.uuid4()).upper()


def build_material_index(draft: dict[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]:
    out: dict[str, tuple[str, dict[str, Any]]] = {}
    for cat, arr in draft.get("materials", {}).items():
        if isinstance(arr, list):
            for m in arr:
                mid = m.get("id")
                if mid:
                    out[mid] = (cat, m)
    return out


def find_segment(draft: dict[str, Any], seg_id: str) -> dict[str, Any]:
    for track in draft.get("tracks", []):
        for seg in track.get("segments", []):
            if seg.get("id") == seg_id:
                return seg
    raise RuntimeError(f"Source segment not found: {seg_id}")


def collect_segment_material_ids(seg: dict[str, Any]) -> set[str]:
    ids = {seg.get("material_id")}
    ids.update(seg.get("extra_material_refs") or [])
    for kf_group in seg.get("common_keyframes") or []:
        if kf_group.get("material_id"):
            ids.add(kf_group["material_id"])
    return {str(x) for x in ids if x}


def remap_value(value: Any, id_map: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {k: remap_value(v, id_map) for k, v in value.items()}
    if isinstance(value, list):
        return [remap_value(v, id_map) for v in value]
    if isinstance(value, str):
        return id_map.get(value, value)
    return value


def clone_material(
    source_mat: dict[str, Any],
    old_id: str,
    new_id: str,
    id_map: dict[str, str],
) -> dict[str, Any]:
    mat = remap_value(copy.deepcopy(source_mat), id_map)
    mat["id"] = new_id
    for key in ("local_id", "local_material_id", "material_id", "music_id"):
        if mat.get(key) == old_id:
            mat[key] = new_id
    return mat


def update_callout_text_material(mat: dict[str, Any]) -> None:
    content = json.loads(mat["content"])
    content["text"] = CALLOUT_TEXT
    split_at = CALLOUT_NAME_LEN
    total = len(CALLOUT_TEXT)
    for idx, style in enumerate(content.get("styles", [])):
        style["range"] = [0, split_at] if idx == 0 else [split_at, total]
        style["size"] = 11.5
        style["bold"] = True
    mat["content"] = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    mat["base_content"] = ""
    mat["words"] = {"start_time": [0], "end_time": [0], "text": [CALLOUT_TEXT]}


def clone_segment(
    source_seg: dict[str, Any],
    id_map: dict[str, str],
    start_us: int,
    duration_us: int,
) -> dict[str, Any]:
    seg = remap_value(copy.deepcopy(source_seg), id_map)
    seg["id"] = gen_uuid() if "-" in str(source_seg.get("id", "")) else gen_id()
    seg["target_timerange"] = {"start": int(start_us), "duration": int(duration_us)}
    seg.setdefault("source_timerange", {})
    source_range = source_seg.get("source_timerange") or {}
    if seg.get("source_timerange") is None:
        seg["source_timerange"] = {}
    seg["source_timerange"]["start"] = source_range.get("start", 0)
    seg["source_timerange"]["duration"] = int(duration_us)
    return seg


def clone_bundle(
    source: dict[str, Any],
    target: dict[str, Any],
    source_seg_ids: list[str],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    source_index = build_material_index(source)
    material_ids: set[str] = set()
    source_segments = [find_segment(source, seg_id) for seg_id in source_seg_ids]
    for seg in source_segments:
        material_ids.update(collect_segment_material_ids(seg))

    id_map = {old: gen_uuid() for old in material_ids}
    cloned_segments: list[dict[str, Any]] = []

    text_seg_material_id = find_segment(source, SOURCE_TEXT_SEG_ID)["material_id"]
    for old_id in material_ids:
        cat, mat = source_index[old_id]
        target.setdefault("materials", {}).setdefault(cat, [])
        cloned = clone_material(mat, old_id, id_map[old_id], id_map)
        if old_id == text_seg_material_id:
            update_callout_text_material(cloned)
        target["materials"][cat].append(cloned)

    for seg in source_segments:
        offset = seg["target_timerange"]["start"] - SOURCE_START_US
        source_dur = seg["target_timerange"]["duration"]
        if seg["id"] in (SOURCE_SCROLL_SEG_ID, SOURCE_LOGO_SEG_ID, SOURCE_TEXT_SEG_ID):
            duration = SCENE_DURATION_US
        elif seg["id"] == SOURCE_TYPING_SEG_ID:
            duration = min(source_dur, SCENE_DURATION_US)
        else:
            duration = source_dur
        cloned_segments.append(
            clone_segment(seg, id_map, SCENE_START_US + offset, duration)
        )
    return cloned_segments, id_map


def wipe_previous(target: dict[str, Any]) -> None:
    target["tracks"] = [
        t for t in target.get("tracks", [])
        if t.get("name") not in {SCROLL_TRACK, LOGO_TRACK, TEXT_TRACK, SFX_TRACK}
    ]


def add_track(target: dict[str, Any], track_type: str, name: str, segment: dict[str, Any]) -> None:
    target.setdefault("tracks", []).append({
        "attribute": 0,
        "flag": 0,
        "id": gen_id(),
        "is_default_name": False,
        "name": name,
        "segments": [segment],
        "type": track_type,
    })


def main() -> int:
    if not SOURCE_FILE.is_file():
        print(f"Не найден эталонный драфт: {SOURCE_FILE}")
        return 1
    if not TARGET_FILE.is_file():
        print(f"Не найден драфт Цирцеи: {TARGET_FILE}")
        return 1
    if not check_capcut_closed():
        print("CapCut сейчас открыт. Закрой его полностью и запусти скрипт ещё раз.")
        return 1

    source = json.load(open(SOURCE_FILE, encoding="utf-8"))
    target = json.load(open(TARGET_FILE, encoding="utf-8"))

    wipe_previous(target)
    segment_ids = [
        SOURCE_SCROLL_SEG_ID,
        SOURCE_LOGO_SEG_ID,
        SOURCE_TEXT_SEG_ID,
        SOURCE_SPARKLE_SEG_ID,
        SOURCE_TYPING_SEG_ID,
    ]
    scroll_seg, logo_seg, text_seg, sparkle_seg, typing_seg = clone_bundle(
        source, target, segment_ids
    )[0]

    # Подмена логотипа на версию без фона
    logo_mid = logo_seg["material_id"]
    for m in target["materials"]["videos"]:
        if m.get("id") == logo_mid:
            m["path"] = str(LOGO_TRANSPARENT_PATH)
            m["material_name"] = LOGO_TRANSPARENT_NAME
            if "name" in m:
                m["name"] = LOGO_TRANSPARENT_NAME
            break

    add_track(target, "video", SCROLL_TRACK, scroll_seg)
    add_track(target, "video", LOGO_TRACK, logo_seg)
    add_track(target, "text", TEXT_TRACK, text_seg)
    target.setdefault("tracks", []).append({
        "attribute": 0,
        "flag": 0,
        "id": gen_id(),
        "is_default_name": False,
        "name": SFX_TRACK,
        "segments": [sparkle_seg, typing_seg],
        "type": "audio",
    })

    backup = TARGET_FILE.with_suffix(".json.hermes-scroll-backup")
    shutil.copy2(TARGET_FILE, backup)
    json.dump(target, open(TARGET_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for extra_name in ("template-2.tmp", "draft_content.json.bak"):
        dst = TARGET_DIR / extra_name
        try:
            shutil.copy2(TARGET_FILE, dst)
        except Exception:
            pass

    print(f"Готово: карточка-объяснялка Гермес на "
          f"{SCENE_START_US / US:.3f}–{SCENE_END_US / US:.3f}s")
    print(f"Текст: {CALLOUT_TEXT!r}")
    print(f"Бэкап: {backup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
