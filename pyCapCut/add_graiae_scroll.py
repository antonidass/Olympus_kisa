"""
Add the Persephone-style scroll callout to the Graiae scene in
the "Персей и Медуза" CapCut draft.

The source callout is copied from the live "Персефона и Аид" draft:
scroll image + channel-logo seal + styled text + the same two SFX.
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
TARGET_PROJECT = "Персей и Медуза"
SOURCE_FILE = DRAFTS / SOURCE_PROJECT / "draft_content.json"
TARGET_DIR = DRAFTS / TARGET_PROJECT
TARGET_FILE = TARGET_DIR / "draft_content.json"

SCROLL_TRACK = "graiae_scroll"
LOGO_TRACK = "graiae_scroll_logo"
TEXT_TRACK = "graiae_scroll_text"
SFX_TRACK = "graiae_scroll_sfx"

SCENE_011_START_US = 31_416_666
SCENE_011_END_US = 35_200_000
SCENE_011_DURATION_US = SCENE_011_END_US - SCENE_011_START_US

SOURCE_START_US = 15_150_000

SOURCE_SCROLL_SEG_ID = "4FAEA63F-EC31-4939-9F39-EC6CE680BB05"
SOURCE_LOGO_SEG_ID = "A1AF07AF-6A2C-452b-A393-61713F991701"
SOURCE_TEXT_SEG_ID = "28FF51E0-688C-45f0-9D25-2AB8EA0D3961"
SOURCE_SPARKLE_SEG_ID = "AF9C6831-B757-4bd4-9D8E-C7A047979E9B"
SOURCE_TYPING_SEG_ID = "DDBC1002-62F0-45f5-9118-B2BA0994ADCB"

CALLOUT_TEXT = "ГРАЙИ — ТРИ СЕСТРЫ,\nКОТОРЫЕ ОЛИЦЕТВОРЯЛИ СТАРОСТЬ"


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
    split_at = len("ГРАЙИ")
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

    for old_id in material_ids:
        cat, mat = source_index[old_id]
        target.setdefault("materials", {}).setdefault(cat, [])
        cloned = clone_material(mat, old_id, id_map[old_id], id_map)
        if old_id == find_segment(source, SOURCE_TEXT_SEG_ID)["material_id"]:
            update_callout_text_material(cloned)
        target["materials"][cat].append(cloned)

    for seg in source_segments:
        offset = seg["target_timerange"]["start"] - SOURCE_START_US
        source_dur = seg["target_timerange"]["duration"]
        if seg["id"] in (SOURCE_SCROLL_SEG_ID, SOURCE_LOGO_SEG_ID, SOURCE_TEXT_SEG_ID):
            duration = SCENE_011_DURATION_US
        elif seg["id"] == SOURCE_TYPING_SEG_ID:
            duration = min(source_dur, SCENE_011_DURATION_US)
        else:
            duration = source_dur
        cloned_segments.append(
            clone_segment(seg, id_map, SCENE_011_START_US + offset, duration)
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
        print(f"Не найден драфт Персея: {TARGET_FILE}")
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

    backup = TARGET_FILE.with_suffix(".json.graiae-scroll-backup")
    shutil.copy2(TARGET_FILE, backup)
    json.dump(target, open(TARGET_FILE, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for extra_name in ("template-2.tmp", "draft_content.json.bak"):
        dst = TARGET_DIR / extra_name
        shutil.copy2(TARGET_FILE, dst)

    print(f"Готово: добавлен свиток Грайи на {SCENE_011_START_US / 1_000_000:.3f}-{SCENE_011_END_US / 1_000_000:.3f}s")
    print(f"Бэкап: {backup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
