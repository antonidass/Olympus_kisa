"""
Одноразовая доводка драфта «Одиссей и Пенелопа» под CAPCUT.md.

Что делает:
1. Добавляет интро-спецэффект «Зеленые точки» (effect_id 7399468802095795462)
   отдельным `effect`-треком `halftone_green_dots`. Тайминг = тайминг
   аудио-сегмента `sentence_002_v1.mp3` (на нём звучит «Одиссей и
   Пенелопа. Миф за минуту»). Параметры: текстура 0.37, фильтры 0.74,
   цвет 0.4, размер 1.0 — как у Персефоны/Диониса.

2. Каждому стикеру в треке `stickers` добавляет лёгкую вертикальную
   качку через `common_keyframes` → KFTypePositionY:
       t=0     → y
       t=300ms → y + 0.07
       t=600ms → y
   Ручные координаты пользователя НЕ перетираются — берётся текущее
   `clip.transform.y` сегмента и от него считаются ключи.

Запуск (CapCut обязательно закрыт):
    python pyCapCut/add_odysseus_halftone_and_bounce.py
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
DRAFTS = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
DRAFT_DIR = DRAFTS / "Одиссей и Пенелопа"
DRAFT_FILE = DRAFT_DIR / "draft_content.json"

HALFTONE_EFFECT_ID = "7399468802095795462"
HALFTONE_EFFECT_NAME = "Зеленые точки"
HALFTONE_EFFECT_MD5 = "87e58ba33f7dc96c4e108cd67c67e2a4"
HALFTONE_EFFECT_PATH = (
    LOCALAPPDATA / "CapCut" / "User Data" / "Cache" / "effect"
    / HALFTONE_EFFECT_ID / HALFTONE_EFFECT_MD5
)

# Озвучка названия мифа. У Одиссея sentence_001 = хук, sentence_002 = титул.
HALFTONE_AUDIO_NAME_PREFIX = "sentence_002"

# Качка стикеров.
BOUNCE_OFFSET = 0.07       # y → y+0.07 → y (по CAPCUT.md §4.3)
BOUNCE_TIMES_US = (0, 300_000, 600_000)


# ─────────────────────────────────────────────────────────────────────
# Утилиты
# ─────────────────────────────────────────────────────────────────────

def gen_id_hex() -> str:
    return uuid.uuid4().hex


def gen_id_upper() -> str:
    return str(uuid.uuid4()).upper()


def check_capcut_closed() -> bool:
    try:
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
        text = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        if "CapCut.exe" in text or "JianyingPro" in text:
            return False
    except Exception:
        pass
    return True


# ─────────────────────────────────────────────────────────────────────
# Halftone
# ─────────────────────────────────────────────────────────────────────

def make_halftone_material() -> dict:
    return {
        "adjust_params": [
            {
                "default_value": 0.6,
                "max_value": 1.0,
                "min_value": 0.0,
                "name": "effects_adjust_texture",
                "parameterIndex": 0,
                "portIndex": 0,
                "value": 0.37,
            },
            {
                "default_value": 1.0,
                "max_value": 1.0,
                "min_value": 0.0,
                "name": "effects_adjust_filter",
                "parameterIndex": 1,
                "portIndex": 0,
                "value": 0.74,
            },
            {
                "default_value": 0.5,
                "max_value": 1.0,
                "min_value": 0.0,
                "name": "effects_adjust_color",
                "parameterIndex": 2,
                "portIndex": 0,
                "value": 0.4,
            },
            {
                "default_value": 0.5,
                "max_value": 1.0,
                "min_value": 0.0,
                "name": "effects_adjust_size",
                "parameterIndex": 3,
                "portIndex": 0,
                "value": 1.0,
            },
        ],
        "algorithm_artifact_path": "",
        "apply_target_type": 2,
        "apply_time_range": None,
        "bind_segment_id": "",
        "category_id": "",
        "category_name": "",
        "common_keyframes": [],
        "covering_relation_change": 0,
        "disable_effect_faces": [],
        "effect_mask": [],
        "effect_id": HALFTONE_EFFECT_ID,
        "enable_mask": True,
        "enable_video_mask_shadow": True,
        "enable_video_mask_stroke": True,
        "formula_id": "",
        "id": gen_id_upper(),
        "item_effect_type": 0,
        "name": HALFTONE_EFFECT_NAME,
        "path": str(HALFTONE_EFFECT_PATH).replace("\\", "/"),
        "platform": "all",
        "render_index": 11000,
        "request_id": "20260516HALFTONEODY",
        "resource_id": HALFTONE_EFFECT_ID,
        "source_platform": 1,
        "sub_type": 0,
        "transparent_params": "",
        "time_range": None,
        "track_render_index": 0,
        "type": "video_effect",
        "value": 1.0,
        "version": "",
    }


def make_halftone_segment(material_id: str, start_us: int, duration_us: int) -> dict:
    return {
        "caption_info": None,
        "cartoon": False,
        "clip": None,
        "color_correct_alg_result": "",
        "common_keyframes": [],
        "desc": "",
        "digital_human_template_group_id": "",
        "enable_adjust": False,
        "enable_adjust_mask": False,
        "enable_color_adjust_pro": False,
        "enable_color_correct_adjust": False,
        "enable_color_curves": True,
        "enable_color_match_adjust": False,
        "enable_color_wheels": True,
        "enable_hsl": False,
        "enable_hsl_curves": True,
        "enable_lut": False,
        "enable_mask_shadow": False,
        "enable_mask_stroke": False,
        "enable_smart_color_adjust": False,
        "enable_video_mask": True,
        "extra_material_refs": [],
        "group_id": "",
        "hdr_settings": None,
        "id": gen_id_upper(),
        "intensifies_audio": False,
        "is_loop": False,
        "is_placeholder": False,
        "is_tone_modify": False,
        "keyframe_refs": [],
        "last_nonzero_volume": 1.0,
        "lyric_keyframes": None,
        "material_id": material_id,
        "raw_segment_id": "",
        "render_index": 11000,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False,
            "horizontal_pos_layout": 0,
            "size_layout": 0,
            "target_follow": "",
            "vertical_pos_layout": 0,
        },
        "reverse": False,
        "source": "segmentsourcenormal",
        "source_timerange": None,
        "speed": 1.0,
        "state": 0,
        "target_timerange": {"duration": int(duration_us), "start": int(start_us)},
        "template_id": "",
        "template_scene": "default",
        "track_attribute": 0,
        "track_render_index": 0,
        "uniform_scale": None,
        "visible": True,
        "volume": 1.0,
    }


def make_halftone_track(segment: dict) -> dict:
    return {
        "attribute": 0,
        "flag": 0,
        "id": gen_id_upper(),
        "is_default_name": False,
        "name": "halftone_green_dots",
        "segments": [segment],
        "type": "effect",
    }


def find_title_voice_segment(draft: dict) -> dict | None:
    audios_by_id = {a["id"]: a for a in draft["materials"].get("audios", [])}
    voice = next(
        (t for t in draft["tracks"] if t.get("type") == "audio" and t.get("name") == "voice"),
        None,
    )
    if not voice:
        return None
    for seg in voice.get("segments", []):
        mat = audios_by_id.get(seg.get("material_id"), {})
        if (mat.get("name") or "").startswith(HALFTONE_AUDIO_NAME_PREFIX):
            return seg
    return None


def apply_halftone(draft: dict) -> str:
    # Если halftone уже есть — не дублируем.
    for t in draft["tracks"]:
        if t.get("type") == "effect" and t.get("name") == "halftone_green_dots":
            return "halftone уже добавлен — пропуск"

    title_seg = find_title_voice_segment(draft)
    if title_seg is None:
        return f"⚠ не нашёл voice-сегмент с именем {HALFTONE_AUDIO_NAME_PREFIX}*.mp3 — halftone пропущен"

    start_us = int(title_seg["target_timerange"]["start"])
    duration_us = int(title_seg["target_timerange"]["duration"])

    mat = make_halftone_material()
    draft["materials"]["video_effects"].append(mat)
    seg = make_halftone_segment(mat["id"], start_us, duration_us)
    draft["tracks"].append(make_halftone_track(seg))
    return (
        f"✓ halftone_green_dots: {start_us / 1e6:.2f}s → "
        f"{(start_us + duration_us) / 1e6:.2f}s "
        f"({duration_us / 1e6:.2f}s)"
    )


# ─────────────────────────────────────────────────────────────────────
# Качка стикеров
# ─────────────────────────────────────────────────────────────────────

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


def apply_sticker_bounce(draft: dict) -> list[str]:
    log: list[str] = []
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
        # Сохраняем чужие property_type если вдруг есть.
        seg["common_keyframes"] = list(existing) + [block]
        added += 1
        log.append(f"  seg{i:>2}: y={y:.4f} → +{BOUNCE_OFFSET:.2f} → y  (0/300/600 ms)")

    log.append(f"✓ качка стикеров: добавлено {added}, пропущено {skipped}")
    return log


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    if not DRAFT_FILE.exists():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1

    if not check_capcut_closed():
        print("⛔ CapCut запущен — закрой его и запусти скрипт снова.")
        return 1

    with open(DRAFT_FILE, "r", encoding="utf-8") as f:
        draft = json.load(f)

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DRAFT_DIR / f"draft_content.json.halftone-bounce-{ts}"
    shutil.copy(DRAFT_FILE, backup)
    print(f"Бекап: {backup.name}")

    print()
    print("Halftone:")
    print(f"  {apply_halftone(draft)}")

    print()
    print("Bounce stickers:")
    for line in apply_sticker_bounce(draft):
        print(line)

    with open(DRAFT_FILE, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False)

    print()
    print("✓ готово. Открой CapCut и проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
