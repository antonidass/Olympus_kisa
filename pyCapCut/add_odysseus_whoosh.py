from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DRAFT_DIR = (
    Path(os.environ["LOCALAPPDATA"])
    / "CapCut"
    / "User Data"
    / "Projects"
    / "com.lveditor.draft"
    / "Одиссей и Пенелопа"
)
DRAFT_FILE = DRAFT_DIR / "draft_content.json"
WHOOSH_FILE = PROJECT_ROOT / "assets" / "audio" / "WHOOSH.mp3"

WHOOSH_DUR_US = 600_000
WHOOSH_VOLUME = 0.70

# Punchy/non-dissolve transitions in enrich_odysseus.py.
WHOOSH_SCENE_IDS = {
    "002",
    "004",
    "006",
    "008",
    "009",
    "010",
    "011",
    "012",
    "015",
    "016",
    "017",
    "018",
    "019",
    "020",
    "022",
}


def gen_id() -> str:
    return uuid.uuid4().hex


def make_audio_material() -> dict:
    mid = gen_id()
    return {
        "app_id": 0,
        "category_id": "",
        "category_name": "local",
        "check_flag": 3,
        "copyright_limit_type": "none",
        "duration": WHOOSH_DUR_US,
        "effect_id": "",
        "formula_id": "",
        "id": mid,
        "local_material_id": mid,
        "music_id": mid,
        "name": "WHOOSH.mp3",
        "path": str(WHOOSH_FILE),
        "source_platform": 0,
        "type": "extract_music",
        "wave_points": [],
    }


def make_segment(material_id: str, start_us: int) -> dict:
    return {
        "enable_adjust": True,
        "enable_color_correct_adjust": False,
        "enable_color_curves": True,
        "enable_color_match_adjust": False,
        "enable_color_wheels": True,
        "enable_lut": True,
        "enable_smart_color_adjust": False,
        "last_nonzero_volume": 1.0,
        "reverse": False,
        "track_attribute": 0,
        "track_render_index": 0,
        "visible": True,
        "id": gen_id(),
        "material_id": material_id,
        "target_timerange": {"start": int(start_us), "duration": WHOOSH_DUR_US},
        "common_keyframes": [],
        "keyframe_refs": [],
        "source_timerange": {"start": 0, "duration": WHOOSH_DUR_US},
        "speed": 1.0,
        "volume": WHOOSH_VOLUME,
        "extra_material_refs": [],
        "clip": None,
        "hdr_settings": None,
        "render_index": 0,
    }


def main() -> int:
    if not DRAFT_FILE.is_file():
        raise SystemExit(f"Draft not found: {DRAFT_FILE}")
    if not WHOOSH_FILE.is_file():
        raise SystemExit(f"WHOOSH not found: {WHOOSH_FILE}")

    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))
    main_track = next(
        t for t in draft["tracks"] if t.get("type") == "video" and t.get("name") == "main"
    )

    # Remove previous local WHOOSH pass, if any.
    old_audio_ids = {
        a["id"]
        for a in draft["materials"].get("audios", [])
        if a.get("name") == "WHOOSH.mp3"
    }
    draft["materials"]["audios"] = [
        a for a in draft["materials"].get("audios", []) if a.get("id") not in old_audio_ids
    ]
    draft["tracks"] = [
        t
        for t in draft["tracks"]
        if not (t.get("type") == "audio" and t.get("name") == "sfx")
    ]

    material = make_audio_material()
    draft["materials"]["audios"].append(material)

    sfx_track = {
        "attribute": 0,
        "flag": 0,
        "id": gen_id(),
        "is_default_name": True,
        "name": "sfx",
        "segments": [],
        "type": "audio",
    }

    placed = 0
    for index, seg in enumerate(main_track.get("segments", []), start=1):
        sid = f"{index:03d}"
        if sid not in WHOOSH_SCENE_IDS:
            continue
        end_us = seg["target_timerange"]["start"] + seg["target_timerange"]["duration"]
        start_us = max(0, end_us - WHOOSH_DUR_US // 2)
        sfx_track["segments"].append(make_segment(material["id"], start_us))
        placed += 1

    sfx_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])
    draft["tracks"].append(sfx_track)

    backup = DRAFT_FILE.with_suffix(".json.whoosh-backup")
    shutil.copy2(DRAFT_FILE, backup)
    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for name in ("template-2.tmp", "draft_content.json.bak"):
        shutil.copy2(DRAFT_FILE, DRAFT_DIR / name)

    print(f"WHOOSH inserted: {placed} segments, backup: {backup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
