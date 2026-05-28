from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "Одиссей и Пенелопа"
MYTH_ROOT = PROJECT_ROOT / "content" / PROJECT_NAME
STICKERS_DIR = MYTH_ROOT / "images" / "stickers"
DRAFT_DIR = (
    Path(os.environ["LOCALAPPDATA"])
    / "CapCut"
    / "User Data"
    / "Projects"
    / "com.lveditor.draft"
    / PROJECT_NAME
)
DRAFT_FILE = DRAFT_DIR / "draft_content.json"

US = 1_000_000


STICKER_PLAN = [
    # scene, sticker image, x, y, scale
    (2, "scene_02_boarding_pass_troy.jpeg", 0.52, 0.38, 0.245),
    (3, "scene_03_undelivered_parcel_stamp.jpeg", -0.52, 0.38, 0.245),
    (4, "scene_04_cracked_hourglass_still_waiting.jpeg", 0.52, 0.38, 0.245),
    (5, "scene_05_bronze_doorbell_108.jpeg", -0.52, 0.38, 0.245),
    (9, "scene_09_golden_best_wife_medal.jpeg", 0.52, 0.39, 0.245),
    (10, "scene_10_ctrl_z_keyboard_key.jpeg", -0.52, 0.39, 0.245),
    (13, "scene_13_retro_handheld_gps.jpeg", 0.52, 0.39, 0.245),
    (16, "scene_16_rpg_quest_scroll.jpeg", -0.52, 0.38, 0.245),
    (17, "scene_17_legendary_magic_bow.jpeg", 0.50, 0.38, 0.265),
    (20, "scene_20_five_gold_stars_perfect.jpeg", -0.50, 0.38, 0.265),
    (21, "scene_21_golden_padlock_verifying.jpeg", 0.52, 0.38, 0.245),
    (23, "scene_23_crimson_wax_verified_seal.jpeg", -0.50, 0.38, 0.255),
    (24, "scene_24_smartphone_tinder_match.jpeg", 0.0, 0.36, 0.265),
]


def gen_id() -> str:
    return str(uuid.uuid4()).upper()


def image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image

        with Image.open(path) as img:
            return img.size
    except Exception:
        return 1024, 1024


def make_photo_material(path: Path) -> dict:
    mid = gen_id()
    width, height = image_size(path)
    name = path.name
    return {
        "id": mid,
        "unique_id": "",
        "type": "photo",
        "duration": 10_800_000_000,
        "path": str(path),
        "media_path": "",
        "local_id": "",
        "has_audio": False,
        "reverse_path": "",
        "intensifies_path": "",
        "reverse_intensifies_path": "",
        "intensifies_audio_path": "",
        "cartoon_path": "",
        "width": width,
        "height": height,
        "category_id": "",
        "category_name": "local",
        "material_id": "",
        "material_name": name,
        "material_url": "",
        "crop": {
            "upper_left_x": 0.0,
            "upper_left_y": 0.0,
            "upper_right_x": 1.0,
            "upper_right_y": 0.0,
            "lower_left_x": 0.0,
            "lower_left_y": 1.0,
            "lower_right_x": 1.0,
            "lower_right_y": 1.0,
        },
        "crop_ratio": "free",
        "audio_fade": None,
        "crop_scale": 1.0,
        "extra_type_option": 0,
        "stable": {"stable_level": 0, "matrix_path": "", "time_range": {"start": 0, "duration": 0}},
        "matting": {
            "flag": 0,
            "path": "",
            "interactiveTime": [],
            "has_use_quick_brush": False,
            "strokes": [],
            "has_use_quick_eraser": False,
            "expansion": 0,
            "feather": 0,
            "reverse": False,
            "custom_matting_id": "",
            "enable_matting_stroke": False,
        },
        "source": 0,
        "source_platform": 0,
        "formula_id": "",
        "check_flag": 62978047,
        "video_algorithm": {
            "algorithms": [],
            "time_range": {"start": 0, "duration": 0},
            "path": "",
            "gameplay_configs": [],
            "ai_in_painting_config": [],
            "complement_frame_config": None,
            "motion_blur_config": None,
            "deflicker": None,
            "noise_reduction": None,
            "quality_enhance": None,
            "super_resolution": None,
            "ai_background_configs": [],
            "smart_complement_frame": None,
            "aigc_generate": None,
            "aigc_generate_list": [],
            "mouth_shape_driver": None,
            "ai_expression_driven": None,
            "ai_motion_driven": None,
            "image_interpretation": None,
            "story_video_modify_video_config": {
                "task_id": "",
                "is_overwrite_last_video": False,
                "tracker_task_id": "",
            },
            "skip_algorithm_index": [],
        },
        "is_unified_beauty_mode": False,
        "object_locked": None,
        "smart_motion": None,
        "multi_camera_info": None,
        "freeze": None,
        "picture_from": "none",
        "picture_set_category_id": "",
        "picture_set_category_name": "",
        "team_id": "",
        "local_material_id": "",
        "origin_material_id": "",
        "request_id": "",
        "has_sound_separated": False,
        "is_text_edit_overdub": False,
        "is_ai_generate_content": False,
        "aigc_type": "none",
        "is_copyright": False,
        "aigc_history_id": "",
        "aigc_item_id": "",
        "local_material_from": "",
        "smart_match_info": None,
        "beauty_face_preset_infos": [],
        "beauty_body_preset_id": "",
        "beauty_face_auto_preset": {"preset_id": "", "name": "", "rate_map": "", "scene": ""},
        "beauty_face_auto_preset_infos": [],
        "beauty_body_auto_preset": None,
        "live_photo_timestamp": -1,
        "live_photo_cover_path": "",
        "content_feature_info": None,
        "corner_pin": None,
        "surface_trackings": [],
        "video_mask_stroke": {
            "resource_id": "",
            "path": "",
            "type": "",
            "color": "",
            "size": 0.0,
            "alpha": 0.0,
            "distance": 0.0,
            "texture": 0.0,
            "horizontal_shift": 0.0,
            "vertical_shift": 0.0,
        },
        "video_mask_shadow": {
            "resource_id": "",
            "path": "",
            "color": "",
            "alpha": 0.0,
            "blur": 0.0,
            "distance": 0.0,
            "angle": 0.0,
        },
    }


def make_video_segment(material_id: str, start_us: int, duration_us: int, x: float, y: float, scale: float) -> dict:
    return {
        "id": gen_id(),
        "source_timerange": {"start": 0, "duration": int(duration_us)},
        "target_timerange": {"start": int(start_us), "duration": int(duration_us)},
        "render_timerange": {"start": 0, "duration": 0},
        "desc": "",
        "state": 0,
        "speed": 1.0,
        "is_loop": False,
        "is_tone_modify": False,
        "reverse": False,
        "intensifies_audio": False,
        "cartoon": False,
        "volume": 0.0,
        "last_nonzero_volume": 1.0,
        "clip": {
            "scale": {"x": float(scale), "y": float(scale)},
            "rotation": 0.0,
            "transform": {"x": float(x), "y": float(y)},
            "flip": {"vertical": False, "horizontal": False},
            "alpha": 1.0,
        },
        "uniform_scale": {"on": True, "value": 1.0},
        "material_id": material_id,
        "extra_material_refs": [],
        "render_index": 1,
        "keyframe_refs": [],
        "enable_lut": True,
        "enable_adjust": True,
        "enable_hsl": False,
        "visible": True,
        "group_id": "",
        "enable_color_curves": True,
        "enable_hsl_curves": True,
        "track_render_index": 0,
        "hdr_settings": {"mode": 1, "intensity": 1.0, "nits": 1000},
        "enable_color_wheels": True,
        "track_attribute": 0,
        "is_placeholder": False,
        "template_id": "",
        "enable_smart_color_adjust": False,
        "template_scene": "default",
        "common_keyframes": [],
        "caption_info": None,
        "responsive_layout": {
            "enable": False,
            "target_follow": "",
            "size_layout": 0,
            "horizontal_pos_layout": 0,
            "vertical_pos_layout": 0,
        },
        "enable_color_match_adjust": False,
        "enable_color_correct_adjust": False,
        "enable_adjust_mask": False,
        "raw_segment_id": "",
        "lyric_keyframes": None,
        "enable_video_mask": True,
        "digital_human_template_group_id": "",
        "color_correct_alg_result": "",
        "source": "segmentsourcenormal",
        "enable_mask_stroke": False,
        "enable_mask_shadow": False,
        "enable_color_adjust_pro": False,
    }


def remove_existing_sticker_pass(draft: dict) -> int:
    old_video_ids: set[str] = set()
    removed_segments = 0
    kept_tracks = []
    for track in draft["tracks"]:
        if track.get("type") == "video" and track.get("name") == "stickers":
            removed_segments += len(track.get("segments", []))
            old_video_ids.update(seg.get("material_id", "") for seg in track.get("segments", []))
            continue
        kept_tracks.append(track)
    draft["tracks"] = kept_tracks
    if old_video_ids:
        draft["materials"]["videos"] = [
            v for v in draft["materials"].get("videos", []) if v.get("id") not in old_video_ids
        ]
    return removed_segments


def main() -> int:
    if not DRAFT_FILE.is_file():
        raise SystemExit(f"Draft not found: {DRAFT_FILE}")

    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))
    main_track = next(
        t for t in draft["tracks"] if t.get("type") == "video" and t.get("name") == "main"
    )

    removed = remove_existing_sticker_pass(draft)
    sticker_track = {
        "attribute": 0,
        "flag": 0,
        "id": gen_id(),
        "is_default_name": True,
        "name": "stickers",
        "segments": [],
        "type": "video",
    }

    placed = 0
    for scene_number, file_name, x, y, scale in STICKER_PLAN:
        sticker_path = STICKERS_DIR / file_name
        if not sticker_path.is_file():
            print(f"missing sticker: {sticker_path}")
            continue
        segment_index = scene_number - 1
        if segment_index < 0 or segment_index >= len(main_track.get("segments", [])):
            print(f"missing scene segment: scene_{scene_number:02d}")
            continue

        scene_segment = main_track["segments"][segment_index]
        scene_start = int(scene_segment["target_timerange"]["start"])
        scene_duration = int(scene_segment["target_timerange"]["duration"])
        duration = min(int(1.5 * US), max(int(0.75 * US), scene_duration - int(0.1 * US)))
        start = scene_start + min(int(0.25 * US), max(0, scene_duration - duration))

        material = make_photo_material(sticker_path)
        draft["materials"].setdefault("videos", []).append(material)
        sticker_track["segments"].append(
            make_video_segment(material["id"], start, duration, x, y, scale)
        )
        placed += 1

    sticker_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])

    # Keep the sticker layer directly above the main video and under text tracks.
    insert_at = 1
    draft["tracks"].insert(insert_at, sticker_track)

    backup = DRAFT_FILE.with_suffix(".json.stickers-backup")
    shutil.copy2(DRAFT_FILE, backup)
    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for name in ("template-2.tmp", "draft_content.json.bak"):
        shutil.copy2(DRAFT_FILE, DRAFT_DIR / name)

    print(f"stickers inserted: {placed}; previous removed: {removed}; backup: {backup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
