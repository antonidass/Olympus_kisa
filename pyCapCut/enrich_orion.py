"""
Обогащает уже собранный CapCut-драфт «Орион и Артемида» переходами,
видео-эффектами, фейдом музыки, громкостями и whoosh-SFX. Полная
копия enrich_perseus.py с подменой карты SCENE_LAYOUT, PLAN под
23 сцены Ориона и без CTA-аутро (финальный круг на сцене 023).

Подход тот же: тянем готовые transition / video_effect шаблоны из
живого драфта Мидаса (где пользователь уже расставил их вручную).
Это гарантирует, что все effect_id уже скачаны в CapCut Cache и
схема полей точно та, что CapCut ожидает.

Запуск (CapCut должен быть полностью закрыт, включая трей):
    python enrich_orion.py
    python enrich_orion.py --dry-run   # только показать план
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from template_theseus import (
    MUSIC_FADE_OUT_SECONDS,
    VOLUMES,
    ZOOM_SCALE_X,
    ZOOM_SCALE_Y,
    ZOOM_TRANSFORM_Y,
    ZOOM_UI_Y,
)

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
ORION_DIR = DRAFTS / "Орион и Артемида"
ORION_FILE = ORION_DIR / "draft_content.json"
MIDAS_FILE = DRAFTS / "Мидас и золотое прикосновение" / "draft_content.json"


# ─────────────────────────────────────────────────────────────────────
# Карта sid сцены → число шотов в треке.
# Должна совпадать со scene_structure_orion.py:
#   23 сцены с озвучкой, 23 mp4-шота.
# ─────────────────────────────────────────────────────────────────────

SCENE_LAYOUT: List[Tuple[str, int]] = [
    ("001", 1), ("002", 1), ("003", 1), ("004", 1), ("005", 1),
    ("006", 1), ("007", 1), ("008", 1), ("009", 1), ("010", 1),
    ("011", 1), ("012", 1), ("013", 1), ("014", 1), ("015", 1),
    ("016", 1), ("017", 1), ("018", 1), ("019", 1), ("020", 1),
    ("021", 1), ("022", 1), ("023", 1),
]
# Сумма: 23


# ─────────────────────────────────────────────────────────────────────
# План переходов под контекст мифа Ориона:
# от героического вступления к лесной близости, затем к обману Аполлона
# и финальному подъему среди звезд.
# ─────────────────────────────────────────────────────────────────────

PLAN: List[Tuple[str, str, float, str]] = [
    ("001", "7340177833508999681", 1.20, "Зум с тряской 2"),
    ("002", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("003", "7550260993348177213", 1.00, "Пастельные блики"),
    ("004", "7234817586234397186", 0.70, "Глитч-вспышка"),
    ("005", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("006", "7550260993348177213", 1.00, "Пастельные блики"),
    ("007", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("008", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("009", "7609529907026119941", 1.00, "Полутоновая вспышка"),
    ("010", "7234817586234397186", 0.70, "Глитч-вспышка"),
    ("011", "7340177833508999681", 1.10, "Зум с тряской 2"),
    ("012", "7464433696658001213", 1.00, "Переход-зум"),
    ("013", "7159450506648097281", 1.00, "Размытие (шар)"),
    ("014", "7340177833508999681", 1.20, "Зум с тряской 2"),
    ("015", "6724239584663704071", 0.90, "Свист"),
    ("016", "7464433696658001213", 1.00, "Переход-зум"),
    ("017", "7234817586234397186", 0.70, "Глитч-вспышка"),
    ("018", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("019", "7159450506648097281", 1.00, "Размытие (шар)"),
    ("020", "7609529907026119941", 1.20, "Полутоновая вспышка"),
    ("021", "7550260993348177213", 1.00, "Пастельные блики"),
    ("022", "7620344224734629138", 1.20, "Растяжение влево"),
    # 023 — последняя сцена, переход не нужен
]

WHOOSH_TRANSITION_EFFECT_IDS = {
    "7340177833508999681",  # Зум с тряской 2
    "7234817586234397186",  # Глитч-вспышка
    "6724239584663704071",  # Свист
    "7620344224734629138",  # Растяжение влево
    "6724227717195108867",  # Влево
    "6724227330190873100",  # Вниз
    "6724227090872275463",  # Вверх
    "7327547930728993282",  # Поворот и изменение
    "6724227965965435396",  # Вправо
}
WHOOSH_TRANSITION_LABELS = {"Влево", "Вправо", "Вверх", "Вниз", "Поворот и изменение"}


# ─────────────────────────────────────────────────────────────────────
# Видео-эффекты: интро без старых film-burn эффектов, только финальный круг.
# Орион без CTA-аутро, поэтому финальный эффект ставим на 023.
# ─────────────────────────────────────────────────────────────────────

EFFECT_PLAN: List[Tuple[str, str, str]] = [
    ("023", "7613711779025358087", "Финальный круг"),
]

HALFTONE_SCENE = "001"
HALFTONE_EFFECT_ID = "7399468802095795462"
HALFTONE_EFFECT_NAME = "Зеленые точки"
HALFTONE_EFFECT_MD5 = "87e58ba33f7dc96c4e108cd67c67e2a4"
HALFTONE_EFFECT_PATH = (
    LOCALAPPDATA / "CapCut" / "User Data" / "Cache" / "effect"
    / HALFTONE_EFFECT_ID / HALFTONE_EFFECT_MD5
)
HALFTONE_AUDIO_NAME = "sentence_002_v1.mp3"
FINAL_EFFECT_DURATION_US = 1_500_000

# Длительность fade_out на фоновой музыке.
MUSIC_FADE_OUT_US = int(MUSIC_FADE_OUT_SECONDS * 1_000_000)

MAX_TRANSITION_RATIO = 0.45
MIN_TRANSITION_US = 200_000

# Громкости — по эталону template_theseus.py.
VOLUME_VOICE = VOLUMES["voice"]
VOLUME_VIDEO = VOLUMES["video"]
VOLUME_MUSIC = 0.1348
VOLUME_WHOOSH = 0.7

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WHOOSH_FILE = PROJECT_ROOT / "assets" / "audio" / "WHOOSH.mp3"
WHOOSH_LEN_US = 600_000


def mp3_duration_us(path: Path) -> int:
    """Длительность mp3 через pymediainfo."""
    try:
        from pymediainfo import MediaInfo
    except ImportError as e:
        raise SystemExit(
            "Не установлен pymediainfo. Поставь зависимости:\n"
            "  pip install -r requirements.txt"
        ) from e
    mi = MediaInfo.parse(str(path))
    for t in mi.tracks:
        if t.track_type == "Audio" and t.duration is not None:
            return int(float(t.duration) * 1000)
    raise RuntimeError(f"Не нашёл audio-дорожку в {path}")


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


def build_segment_to_sid_map() -> List[str]:
    """seg_index → sid сцены. Длина списка = сумма шотов всех сцен."""
    out: List[str] = []
    for sid, n in SCENE_LAYOUT:
        out.extend([sid] * n)
    return out


def last_shot_index_per_sid() -> Dict[str, int]:
    out: Dict[str, int] = {}
    seg_to_sid = build_segment_to_sid_map()
    for i, sid in enumerate(seg_to_sid):
        out[sid] = i
    return out


def first_shot_index_per_sid() -> Dict[str, int]:
    out: Dict[str, int] = {}
    seg_to_sid = build_segment_to_sid_map()
    for i, sid in enumerate(seg_to_sid):
        out.setdefault(sid, i)
    return out


def scene_duration_us(draft: dict, sid: str) -> int:
    """Сумма target_timerange.duration по всем шотам сцены."""
    seg_to_sid = build_segment_to_sid_map()
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    total = 0
    for i, seg in enumerate(main["segments"]):
        if i < len(seg_to_sid) and seg_to_sid[i] == sid:
            total += seg["target_timerange"]["duration"]
    return total


# ─────────────────────────────────────────────────────────────────────
# Сборка библиотеки шаблонов из Мидас-драфта
# ─────────────────────────────────────────────────────────────────────

def build_template_library(midas_draft: dict) -> dict:
    mats = midas_draft["materials"]
    transitions: Dict[str, dict] = {}
    for t in mats["transitions"]:
        transitions[str(t["effect_id"])] = t
    video_effects: Dict[str, dict] = {}
    for e in mats["video_effects"]:
        video_effects[str(e["effect_id"])] = e
    return {"transitions": transitions, "video_effects": video_effects}


def clone_transition(template: dict, duration_us: int) -> dict:
    m = copy.deepcopy(template)
    m["id"] = gen_id_hex()
    m["duration"] = int(duration_us)
    return m


def clone_video_effect(template: dict) -> dict:
    m = copy.deepcopy(template)
    m["id"] = str(uuid.uuid4()).upper()
    return m


def make_global_video_effect(effect_id: str, name: str) -> dict:
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
        "effect_id": effect_id,
        "enable_mask": True,
        "enable_video_mask_shadow": True,
        "enable_video_mask_stroke": True,
        "formula_id": "",
        "id": str(uuid.uuid4()).upper(),
        "item_effect_type": 0,
        "name": name,
        "path": str(HALFTONE_EFFECT_PATH).replace("\\", "/"),
        "platform": "all",
        "render_index": 11000,
        "request_id": "20260508210050HALFTONE",
        "resource_id": effect_id,
        "source_platform": 1,
        "sub_type": 0,
        "transparent_params": "",
        "time_range": None,
        "track_render_index": 0,
        "type": "video_effect",
        "value": 1.0,
        "version": "",
    }


def make_effect_track_segment(material_id: str, start_us: int, duration_us: int) -> dict:
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
        "id": str(uuid.uuid4()).upper(),
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


def make_effect_track(name: str, segment: dict) -> dict:
    return {
        "attribute": 0,
        "flag": 0,
        "id": str(uuid.uuid4()).upper(),
        "is_default_name": False,
        "name": name,
        "segments": [segment],
        "type": "effect",
    }


def voice_end_us(draft: dict) -> int:
    voice = next(
        (t for t in draft["tracks"] if t["type"] == "audio" and t.get("name") == "voice"),
        None,
    )
    if not voice or not voice.get("segments"):
        return int(draft.get("duration", 0) or 0)
    return max(
        int(s["target_timerange"]["start"]) + int(s["target_timerange"]["duration"])
        for s in voice["segments"]
    )


def trim_timeline_to_voice_end(draft: dict) -> List[str]:
    log: List[str] = []
    end_us = voice_end_us(draft)
    if end_us <= 0:
        log.append("  ⚠ voice_end не найден — обрезку пропускаю")
        return log

    trimmed = 0
    removed = 0
    for tr in draft.get("tracks", []):
        kept = []
        for seg in tr.get("segments", []):
            rng = seg.get("target_timerange")
            if not rng:
                kept.append(seg)
                continue
            start = int(rng.get("start", 0))
            dur = int(rng.get("duration", 0))
            seg_end = start + dur
            if start >= end_us:
                removed += 1
                continue
            if seg_end > end_us:
                new_dur = max(0, end_us - start)
                rng["duration"] = new_dur
                src = seg.get("source_timerange")
                if isinstance(src, dict) and int(src.get("duration", 0) or 0) > new_dur:
                    src["duration"] = new_dur
                trimmed += 1
            kept.append(seg)
        tr["segments"] = kept

    draft["duration"] = end_us
    for d in draft.get("materials", {}).get("drafts", []):
        if isinstance(d, dict) and "duration" in d:
            d["duration"] = end_us

    music = next(
        (t for t in draft["tracks"] if t["type"] == "audio" and t.get("name") == "music"),
        None,
    )
    if music and music.get("segments"):
        seg = music["segments"][0]
        dur = int(seg["target_timerange"]["duration"])
        seg["common_keyframes"] = [{
            "id": gen_id_hex(),
            "material_id": "",
            "property_type": "KFTypeVolume",
            "keyframe_list": [
                {
                    "id": gen_id_hex(),
                    "curveType": "Line",
                    "time_offset": max(0, dur - MUSIC_FADE_OUT_US),
                    "left_control": {"x": 0.0, "y": 0.0},
                    "right_control": {"x": 0.0, "y": 0.0},
                    "values": [VOLUME_MUSIC],
                    "string_value": "",
                    "graphID": "",
                },
                {
                    "id": gen_id_hex(),
                    "curveType": "Line",
                    "time_offset": dur,
                    "left_control": {"x": 0.0, "y": 0.0},
                    "right_control": {"x": 0.0, "y": 0.0},
                    "values": [0.0],
                    "string_value": "",
                    "graphID": "",
                },
            ],
        }]

    log.append(
        f"  ✂ конец по voice: {end_us/1_000_000:.2f}s "
        f"(укорочено {trimmed}, удалено {removed})"
    )
    return log


def make_audio_fade(fade_in_us: int, fade_out_us: int) -> dict:
    return {
        "fade_in_duration": int(fade_in_us),
        "fade_out_duration": int(fade_out_us),
        "fade_type": 0,
        "id": str(uuid.uuid4()).upper(),
        "type": "audio_fade",
    }


# ─────────────────────────────────────────────────────────────────────
# Применение к драфту Персея
# ─────────────────────────────────────────────────────────────────────

def apply_transitions(draft: dict, library: dict) -> List[str]:
    log: List[str] = []
    last_idx = last_shot_index_per_sid()
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    sids_in_order = [sid for sid, _ in SCENE_LAYOUT]

    durs_by_sid = {sid: scene_duration_us(draft, sid) for sid, _ in SCENE_LAYOUT}

    for plan_idx, (sid, eff_id, want_dur_s, label) in enumerate(PLAN):
        try:
            next_sid = sids_in_order[sids_in_order.index(sid) + 1]
        except (ValueError, IndexError):
            log.append(f"  ⚠ sid {sid}: нет следующей сцены, пропускаю")
            continue
        prev_dur = durs_by_sid.get(sid, 0)
        next_dur = durs_by_sid.get(next_sid, 0)
        cap = int(min(prev_dur, next_dur) * MAX_TRANSITION_RATIO)
        want_us = int(want_dur_s * 1_000_000)
        dur_us = max(MIN_TRANSITION_US, min(want_us, cap))

        template = library["transitions"].get(eff_id)
        if template is None:
            log.append(f"  ⚠ effect_id {eff_id} ({label}) не нашёлся в Мидас-материалах — пропуск")
            continue

        tr_mat = clone_transition(template, dur_us)
        draft["materials"]["transitions"].append(tr_mat)

        seg_idx = last_idx[sid]
        seg = main["segments"][seg_idx]
        refs = seg.setdefault("extra_material_refs", [])
        refs.append(tr_mat["id"])

        clamped = " (cap'd)" if want_us > cap else ""
        log.append(
            f"  → {sid:<4} → {next_sid:<4}  {label:<28} {dur_us/1_000_000:.2f}s{clamped}"
        )
    return log


def apply_video_effects(draft: dict, library: dict) -> List[str]:
    log: List[str] = []
    first_idx = first_shot_index_per_sid()
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    for sid, eff_id, label in EFFECT_PLAN:
        template = library["video_effects"].get(eff_id)
        if template is None:
            log.append(f"  ⚠ video_effect {eff_id} ({label}) не нашёлся в Мидасе — пропуск")
            continue
        ve_mat = clone_video_effect(template)
        draft["materials"]["video_effects"].append(ve_mat)

        seg_idx = first_idx.get(sid)
        if seg_idx is None:
            log.append(f"  ⚠ sid {sid} не найден в треке — пропуск")
            continue
        seg = main["segments"][seg_idx]
        refs = seg.setdefault("extra_material_refs", [])
        refs.append(ve_mat["id"])
        seg_dur = int(seg["target_timerange"]["duration"])
        ve_mat["time_range"] = {
            "start": max(0, seg_dur - FINAL_EFFECT_DURATION_US) if sid == "022" else 0,
            "duration": min(seg_dur, FINAL_EFFECT_DURATION_US) if sid == "022" else seg_dur,
        }
        log.append(f"  ★ {sid:<4} {label}  (на сегмент #{seg_idx})")
    return log


def apply_halftone_effect(draft: dict) -> List[str]:
    log: List[str] = []
    audios_by_id = {a["id"]: a for a in draft["materials"].get("audios", [])}
    voice = next(
        (t for t in draft["tracks"] if t["type"] == "audio" and t.get("name") == "voice"),
        None,
    )
    title_voice_seg = None
    if voice:
        for seg in voice.get("segments", []):
            mat = audios_by_id.get(seg.get("material_id"), {})
            if mat.get("name") == HALFTONE_AUDIO_NAME:
                title_voice_seg = seg
                break

    if title_voice_seg is None:
        log.append(f"  ⚠ не нашёл {HALFTONE_AUDIO_NAME} — {HALFTONE_EFFECT_NAME} пропущен")
        return log

    start_us = int(title_voice_seg["target_timerange"]["start"])
    duration_us = int(title_voice_seg["target_timerange"]["duration"])
    mat = make_global_video_effect(HALFTONE_EFFECT_ID, HALFTONE_EFFECT_NAME)
    draft["materials"]["video_effects"].append(mat)
    effect_seg = make_effect_track_segment(mat["id"], start_us, duration_us)
    draft["tracks"].append(make_effect_track("halftone_green_dots", effect_seg))
    log.append(
        f"  ◌ {HALFTONE_SCENE:<4} {HALFTONE_EFFECT_NAME} "
        f"{start_us/1_000_000:.2f}–{(start_us + duration_us)/1_000_000:.2f}s"
    )
    return log


def apply_music_fade(draft: dict) -> List[str]:
    log: List[str] = []
    music_track = next(
        (t for t in draft["tracks"] if t["type"] == "audio" and t.get("name") == "music"),
        None,
    )
    if music_track is None or not music_track.get("segments"):
        log.append("  ⚠ дорожки music нет, фейд пропускаю")
        return log
    fade_mat = make_audio_fade(0, MUSIC_FADE_OUT_US)
    draft["materials"]["audio_fades"].append(fade_mat)
    seg = music_track["segments"][0]
    refs = seg.setdefault("extra_material_refs", [])
    refs.append(fade_mat["id"])
    log.append(f"  ♪ музыка: fade_out {MUSIC_FADE_OUT_US/1_000_000:.1f}s")
    return log


# ─────────────────────────────────────────────────────────────────────
# Чистка прошлых правок (для идемпотентности)
# ─────────────────────────────────────────────────────────────────────

def wipe_previous_enrichment(draft: dict) -> List[str]:
    log: List[str] = []
    mats = draft["materials"]

    trans_ids = {t["id"] for t in mats["transitions"]}
    ve_ids = {e["id"] for e in mats["video_effects"]}
    fade_ids = {f["id"] for f in mats.get("audio_fades", [])}

    main = next((t for t in draft["tracks"]
                 if t["type"] == "video" and t.get("name") == "main"), None)
    if main:
        for seg in main["segments"]:
            seg["extra_material_refs"] = [
                r for r in seg.get("extra_material_refs", [])
                if r not in trans_ids and r not in ve_ids
            ]

    music = next((t for t in draft["tracks"]
                  if t["type"] == "audio" and t.get("name") == "music"), None)
    if music:
        for seg in music["segments"]:
            seg["extra_material_refs"] = [
                r for r in seg.get("extra_material_refs", [])
                if r not in fade_ids
            ]

    effect_tracks = [
        t for t in draft["tracks"]
        if t["type"] == "effect"
        and (
            t.get("name") == "halftone_green_dots"
            or any(s.get("material_id") in ve_ids for s in t.get("segments", []))
        )
    ]
    n_effect_segs = 0
    for tr in effect_tracks:
        n_effect_segs += len(tr.get("segments", []))
        draft["tracks"].remove(tr)

    n_t = len(mats["transitions"])
    n_v = len(mats["video_effects"])
    n_f = len(mats.get("audio_fades", []))
    mats["transitions"] = []
    mats["video_effects"] = []
    mats["audio_fades"] = []

    sfx_tracks = [t for t in draft["tracks"]
                  if t["type"] == "audio" and t.get("name") == "sfx"]
    n_sfx_segs = 0
    sfx_audio_ids: set[str] = set()
    for tr in sfx_tracks:
        n_sfx_segs += len(tr.get("segments", []))
        for s in tr.get("segments", []):
            sfx_audio_ids.add(s.get("material_id", ""))
        draft["tracks"].remove(tr)
    if sfx_audio_ids:
        used_elsewhere: set[str] = set()
        for tr in draft["tracks"]:
            if tr["type"] != "audio":
                continue
            for s in tr.get("segments", []):
                used_elsewhere.add(s.get("material_id", ""))
        mats["audios"] = [a for a in mats["audios"]
                          if a["id"] not in sfx_audio_ids or a["id"] in used_elsewhere]

    log.append(f"  снято: {n_t} transitions, {n_v} video_effects, {n_f} audio_fades, "
               f"{n_sfx_segs} whoosh-сегментов, {n_effect_segs} effect-сегментов")
    return log


# ─────────────────────────────────────────────────────────────────────
# Громкости (как у Мидаса)
# ─────────────────────────────────────────────────────────────────────

def apply_volumes(draft: dict) -> List[str]:
    log: List[str] = []
    for tr in draft["tracks"]:
        if tr["type"] == "video" and tr.get("name") == "main":
            for seg in tr["segments"]:
                seg["volume"] = VOLUME_VIDEO
            log.append(f"  video.main: {VOLUME_VIDEO}  ({len(tr['segments'])} сегм.)")
        elif tr["type"] == "audio" and tr.get("name") == "voice":
            for seg in tr["segments"]:
                seg["volume"] = VOLUME_VOICE
            log.append(f"  audio.voice: {VOLUME_VOICE}  ({len(tr['segments'])} сегм.)")
        elif tr["type"] == "audio" and tr.get("name") == "music":
            for seg in tr["segments"]:
                seg["volume"] = VOLUME_MUSIC
            log.append(f"  audio.music: {VOLUME_MUSIC}  ({len(tr['segments'])} сегм.)")
    return log


# ─────────────────────────────────────────────────────────────────────
# Геометрия видео: 104% и Y=-77 в UI CapCut для прижатия к верхнему краю.
# ─────────────────────────────────────────────────────────────────────

def apply_video_geometry(draft: dict) -> List[str]:
    log: List[str] = []
    main = next((t for t in draft["tracks"]
                 if t["type"] == "video" and t.get("name") == "main"), None)
    if main is None:
        log.append("  ⚠ video.main не найден — геометрию пропускаю")
        return log
    for seg in main.get("segments", []):
        clip = seg.setdefault("clip", {})
        clip["scale"] = {"x": ZOOM_SCALE_X, "y": ZOOM_SCALE_Y}
        transform = clip.setdefault("transform", {"x": 0.0, "y": 0.0})
        transform["x"] = 0.0
        transform["y"] = ZOOM_TRANSFORM_Y
        uniform = seg.setdefault("uniform_scale", {"on": True, "value": 1.0})
        uniform["on"] = True
        uniform["value"] = ZOOM_SCALE_X
    log.append(
        f"  video.main: scale={ZOOM_SCALE_X}, UI Y={ZOOM_UI_Y}, "
        f"transform.y={ZOOM_TRANSFORM_Y:.10f} ({len(main.get('segments', []))} сегм.)"
    )
    return log


# ─────────────────────────────────────────────────────────────────────
# Whoosh-SFX на каждом slide-переходе
# ─────────────────────────────────────────────────────────────────────

def make_whoosh_audio_material(path: Path, full_dur_us: int) -> dict:
    mid = gen_id_hex()
    return {
        "ai_music_enter_from": "", "ai_music_generate_scene": 0, "ai_music_type": 0,
        "aigc_history_id": "", "aigc_item_id": "", "app_id": 0,
        "category_id": "", "category_name": "local",
        "check_flag": 3, "cloned_model_type": "", "copyright_limit_type": "none",
        "duration": int(full_dur_us),
        "effect_id": "", "formula_id": "",
        "id": mid,
        "intensifies_path": "",
        "is_ai_clone_tone": False, "is_ai_clone_tone_post": False,
        "is_text_edit_overdub": False, "is_ugc": False,
        "local_material_id": mid,
        "lyric_type": 0, "mock_tone_speaker": "", "moyin_emotion": "",
        "music_id": mid, "music_source": "",
        "name": path.name,
        "path": str(path).replace("/", "\\"),
        "pgc_id": "", "pgc_name": "", "query": "", "request_id": "",
        "resource_id": "", "search_id": "",
        "similiar_music_info": {"original_song_id": "", "original_song_name": ""},
        "sound_separate_type": "", "source_from": "",
        "source_platform": 0, "team_id": "", "text_id": "", "third_resource_id": "",
        "tone_category_id": "", "tone_category_name": "",
        "tone_effect_id": "", "tone_effect_name": "", "tone_platform": "",
        "tone_second_category_id": "", "tone_second_category_name": "",
        "tone_speaker": "", "tone_type": "",
        "type": "extract_music",
        "video_id": "", "wave_points": [],
    }


def make_whoosh_segment(material_id: str, start_us: int, dur_us: int) -> dict:
    return {
        "caption_info": None, "cartoon": False, "clip": None,
        "color_correct_alg_result": "", "common_keyframes": [], "desc": "",
        "digital_human_template_group_id": "",
        "enable_adjust": False, "enable_adjust_mask": False,
        "enable_color_adjust_pro": False, "enable_color_correct_adjust": False,
        "enable_color_curves": True, "enable_color_match_adjust": False,
        "enable_color_wheels": True, "enable_hsl": False,
        "enable_hsl_curves": True, "enable_lut": False,
        "enable_mask_shadow": False, "enable_mask_stroke": False,
        "enable_smart_color_adjust": False, "enable_video_mask": True,
        "extra_material_refs": [],
        "group_id": "",
        "id": gen_id_hex(),
        "intensifies_audio": False, "is_loop": False, "is_placeholder": False,
        "is_tone_modify": False, "keyframe_refs": [],
        "last_nonzero_volume": 1.0,
        "lyric_keyframes": None,
        "material_id": material_id,
        "raw_segment_id": "",
        "render_index": 0, "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False, "horizontal_pos_layout": 0, "size_layout": 0,
            "target_follow": "", "vertical_pos_layout": 0,
        },
        "reverse": False, "source_timerange": {"duration": int(dur_us), "start": 0},
        "speed": 1.0,
        "state": 0, "stretch_alg": "",
        "target_timerange": {"duration": int(dur_us), "start": int(start_us)},
        "template_id": "", "template_scene": "default",
        "track_attribute": 0, "track_render_index": 0, "uniform_scale": None,
        "visible": True, "volume": VOLUME_WHOOSH,
    }


def apply_whoosh(draft: dict) -> List[str]:
    log: List[str] = []
    if not WHOOSH_FILE.is_file():
        log.append(f"  ⚠ нет файла {WHOOSH_FILE} — whoosh пропускаю")
        return log

    full_dur = mp3_duration_us(WHOOSH_FILE)
    use_dur = min(WHOOSH_LEN_US, full_dur)

    whoosh_mat = make_whoosh_audio_material(WHOOSH_FILE, full_dur)
    draft["materials"]["audios"].append(whoosh_mat)

    sfx_track = {
        "attribute": 0, "flag": 0, "id": gen_id_hex(),
        "is_default_name": True, "name": "sfx",
        "segments": [], "type": "audio",
    }
    draft["tracks"].append(sfx_track)

    last_idx = last_shot_index_per_sid()
    main = next(t for t in draft["tracks"]
                if t["type"] == "video" and t.get("name") == "main")
    trans_ids_to_dur: Dict[str, int] = {}
    for tmat in draft["materials"]["transitions"]:
        trans_ids_to_dur[tmat["id"]] = tmat["duration"]

    transition_by_id = {tmat["id"]: tmat for tmat in draft["materials"]["transitions"]}

    placed = 0
    for sid, eff_id, _want, label in PLAN:
        if eff_id not in WHOOSH_TRANSITION_EFFECT_IDS and label not in WHOOSH_TRANSITION_LABELS:
            continue
        seg_idx = last_idx[sid]
        seg = main["segments"][seg_idx]
        my_trans_dur = 0
        for r in seg.get("extra_material_refs", []):
            tmat = transition_by_id.get(r)
            if not tmat:
                continue
            actual_eff = str(tmat.get("effect_id", ""))
            if actual_eff in WHOOSH_TRANSITION_EFFECT_IDS:
                my_trans_dur = trans_ids_to_dur[r]
                break
        if my_trans_dur == 0:
            continue
        end_us = seg["target_timerange"]["start"] + seg["target_timerange"]["duration"]
        whoosh_start_us = max(0, end_us - use_dur // 2)
        wseg = make_whoosh_segment(whoosh_mat["id"], whoosh_start_us, use_dur)
        sfx_track["segments"].append(wseg)
        placed += 1

    sfx_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])
    log.append(f"  whoosh добавлен: {placed} вставок только на slide/turn переходах (vol={VOLUME_WHOOSH})")
    return log


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Только показать план, не писать драфт.")
    args = p.parse_args()

    if not ORION_FILE.is_file():
        print(f"Не нашёл драфт Ориона: {ORION_FILE}")
        print("Сначала запусти: python build_orion.py")
        return 1
    if not MIDAS_FILE.is_file():
        print(f"Не нашёл драфт Мидаса для забора шаблонов: {MIDAS_FILE}")
        return 1

    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой его полностью (включая трей) и запусти скрипт ещё раз.")
        return 1

    print(f"Читаю Ориона: {ORION_FILE}")
    draft = json.load(open(ORION_FILE, encoding="utf-8"))

    print(f"Читаю библиотеку шаблонов из Мидаса: {MIDAS_FILE}")
    midas = json.load(open(MIDAS_FILE, encoding="utf-8"))
    library = build_template_library(midas)
    print(f"  доступно transitions: {len(library['transitions'])}, "
          f"video_effects: {len(library['video_effects'])}")

    print()
    print("Чистка прошлых правок:")
    for line in wipe_previous_enrichment(draft):
        print(line)

    print()
    print("Громкости:")
    for line in apply_volumes(draft):
        print(line)

    print()
    print("Геометрия видео:")
    for line in apply_video_geometry(draft):
        print(line)

    print()
    print("Обрезка по озвучке:")
    for line in trim_timeline_to_voice_end(draft):
        print(line)

    print()
    print("План переходов:")
    log_tr = apply_transitions(draft, library)
    for line in log_tr:
        print(line)

    print()
    print("Видео-эффекты:")
    log_ve = apply_video_effects(draft, library)
    for line in log_ve:
        print(line)

    print()
    print("Спецэффект intro-halftone:")
    for line in apply_halftone_effect(draft):
        print(line)

    print()
    print("Музыка:")
    log_mu = apply_music_fade(draft)
    for line in log_mu:
        print(line)

    print()
    print("Whoosh-SFX:")
    log_wh = apply_whoosh(draft)
    for line in log_wh:
        print(line)

    if args.dry_run:
        print("\n--dry-run: драфт не трогаю.")
        return 0

    bkp = ORION_FILE.with_suffix(".json.enrich-backup")
    shutil.copy2(ORION_FILE, bkp)
    print(f"\nБэкап: {bkp.name}")

    json.dump(draft, open(ORION_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = ORION_DIR / tgt_name
        try:
            shutil.copy2(ORION_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    mats = draft["materials"]
    sfx_count = sum(len(t.get("segments", [])) for t in draft["tracks"]
                    if t["type"] == "audio" and t.get("name") == "sfx")
    print(f"\n✓ Готово. transitions={len(mats['transitions'])}, "
          f"video_effects={len(mats['video_effects'])}, "
          f"audio_fades={len(mats['audio_fades'])}, "
          f"whoosh-сегментов={sfx_count}.")
    print("Открой CapCut -> проект «Орион и Артемида» -> проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
