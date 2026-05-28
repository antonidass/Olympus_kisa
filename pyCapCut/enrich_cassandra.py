"""
Обогащает уже собранный CapCut-драфт «Аполлон и Кассандра» переходами,
видео-эффектами, фейдом музыки, громкостями и whoosh-SFX.

Переходы повторяют ручную раскладку пользователя в живом драфте
«Цирцея и Одиссей»: те же 11 переходов в той же последовательности по
индексам сегментов 0..19. Шаблоны переходов и интро-halftone берутся из
живого draft_content.json Цирцеи (там уже скачаны нужные CapCut-online
ассеты).

EFFECT_PLAN пуст («Финальный круг» запрещён каноном).

Запуск (CapCut должен быть полностью закрыт):
    python enrich_cassandra.py
    python enrich_cassandra.py --dry-run
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
CASSANDRA_DIR = DRAFTS / "Аполлон и Кассандра"
CASSANDRA_FILE = CASSANDRA_DIR / "draft_content.json"
# Шаблоны переходов тянем из живого черновика Цирцеи (там вручную
# разложены все 7 уникальных переходов с уже подгруженными ассетами).
CIRCE_FILE = DRAFTS / "Цирцея и Одиссей" / "draft_content.json"


# ─────────────────────────────────────────────────────────────────────
# Карта sid → число шотов в треке: 15 sid, 20 шотов суммарно.
# (См. scene_structure_cassandra.py.)
# ─────────────────────────────────────────────────────────────────────

SCENE_LAYOUT: List[Tuple[str, int]] = [
    ("001", 1), ("002", 1), ("003", 1), ("004", 1), ("005", 1),
    ("006", 2), ("007", 1), ("008", 1), ("009", 2), ("010", 1),
    ("011", 2), ("012", 2), ("013", 1), ("014", 1), ("015", 2),
]


# ─────────────────────────────────────────────────────────────────────
# План переходов — точная копия живой раскладки Цирцеи по индексам
# сегментов на main-треке. Переход на сегменте N означает: между
# сегментом N и N+1.
#
# Drama: Влево/Вытягивание/Вверх на сюжетных сдвигах локации,
# Резкий зум на эмоциональных всплесках, Взмах лапки на введении
# героя, Скольжение воспоминаний на видениях/пророчествах, Бумажный
# шар на финальном «зажигании Трои». Запрещённые переходы
# (Полутоновая вспышка, Пастельные блики, Зум с тряской 1/2) НЕ
# используются.
# ─────────────────────────────────────────────────────────────────────

TRANSITION_PLAN: List[Tuple[int, str, int, str]] = [
    # (segment_index, effect_id, duration_us, label)
    (1,  "6724227717195108867", 800_000, "Влево"),
    (2,  "7574908666210471221", 966_666, "Резкий зум"),
    (3,  "7561440477262761277", 566_666, "Взмах лапки"),
    (4,  "6724226338418332167", 500_000, "Вытягивание"),
    (6,  "7309740200605782530", 700_000, "Скольжение воспоминаний II"),
    (7,  "6724227717195108867", 700_000, "Влево"),
    (9,  "7574908666210471221", 566_666, "Резкий зум"),
    (11, "7309740200605782530", 433_333, "Скольжение воспоминаний II"),
    (13, "6724227090872275463", 500_000, "Вверх"),
    (14, "6724226338418332167", 500_000, "Вытягивание"),
    (17, "7249296835204878850", 666_666, "Бумажный шар"),
]

# WHOOSH.mp3 на стыки направленных переходов — повторяем живую
# раскладку Цирцеи (там WHOOSH стоит только на seg[7] Влево и
# seg[13] Вверх). На зум/взмах/скольжение/Бумажный шар отдельный
# whoosh в Циркее не клался.
WHOOSH_SEG_INDICES: List[int] = [7, 13]

# Crumpled paper на Бумажный шар (канон § 3.3.1: 1.00 vol, 0.866 с,
# за 0.333 с до старта следующей сцены).
CRUMPLED_SEG_INDEX = 17


# ─────────────────────────────────────────────────────────────────────
# Видео-эффекты: только интро-halftone «Зеленые точки» поверх sent_002.
# ─────────────────────────────────────────────────────────────────────

EFFECT_PLAN: List[Tuple[str, str, str]] = []

HALFTONE_SCENE = "001"
HALFTONE_EFFECT_ID = "7399468802095795462"
HALFTONE_EFFECT_NAME = "Зеленые точки"
HALFTONE_EFFECT_MD5 = "87e58ba33f7dc96c4e108cd67c67e2a4"
HALFTONE_EFFECT_PATH = (
    LOCALAPPDATA / "CapCut" / "User Data" / "Cache" / "effect"
    / HALFTONE_EFFECT_ID / HALFTONE_EFFECT_MD5
)
HALFTONE_AUDIO_NAME = "sentence_002_v4.mp3"

MUSIC_FADE_OUT_US = int(MUSIC_FADE_OUT_SECONDS * 1_000_000)

VOLUME_VOICE = VOLUMES["voice"]
VOLUME_VIDEO = VOLUMES["video"]
VOLUME_MUSIC = 0.1348
VOLUME_WHOOSH = 0.7
VOLUME_CRUMPLED = 1.0

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WHOOSH_FILE = PROJECT_ROOT / "assets" / "audio" / "WHOOSH.mp3"
CRUMPLED_FILE = PROJECT_ROOT / "assets" / "sfx" / "crumpled_paper.mp3"
WHOOSH_LEN_US = 600_000
CRUMPLED_LEN_US = 866_667
CRUMPLED_LEAD_US = 333_334  # за 0.333 с до конца текущего сегмента


def mp3_duration_us(path: Path) -> int:
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


def build_template_library(donor_draft: dict) -> dict:
    mats = donor_draft["materials"]
    transitions: Dict[str, dict] = {}
    for t in mats.get("transitions", []):
        eid = str(t["effect_id"])
        if eid not in transitions:
            transitions[eid] = t
    video_effects: Dict[str, dict] = {}
    for e in mats.get("video_effects", []):
        eid = str(e["effect_id"])
        if eid not in video_effects:
            video_effects[eid] = e
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
            {"default_value": 0.6, "max_value": 1.0, "min_value": 0.0,
             "name": "effects_adjust_texture", "parameterIndex": 0, "portIndex": 0, "value": 0.37},
            {"default_value": 1.0, "max_value": 1.0, "min_value": 0.0,
             "name": "effects_adjust_filter", "parameterIndex": 1, "portIndex": 0, "value": 0.74},
            {"default_value": 0.5, "max_value": 1.0, "min_value": 0.0,
             "name": "effects_adjust_color", "parameterIndex": 2, "portIndex": 0, "value": 0.4},
            {"default_value": 0.5, "max_value": 1.0, "min_value": 0.0,
             "name": "effects_adjust_size", "parameterIndex": 3, "portIndex": 0, "value": 1.0},
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
        "request_id": "20260526HALFTONECASSANDRA",
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
        "caption_info": None, "cartoon": False, "clip": None,
        "color_correct_alg_result": "", "common_keyframes": [], "desc": "",
        "digital_human_template_group_id": "",
        "enable_adjust": False, "enable_adjust_mask": False,
        "enable_color_adjust_pro": False, "enable_color_correct_adjust": False,
        "enable_color_curves": True, "enable_color_match_adjust": False,
        "enable_color_wheels": True, "enable_hsl": False, "enable_hsl_curves": True,
        "enable_lut": False, "enable_mask_shadow": False, "enable_mask_stroke": False,
        "enable_smart_color_adjust": False, "enable_video_mask": True,
        "extra_material_refs": [], "group_id": "", "hdr_settings": None,
        "id": str(uuid.uuid4()).upper(),
        "intensifies_audio": False, "is_loop": False, "is_placeholder": False,
        "is_tone_modify": False, "keyframe_refs": [], "last_nonzero_volume": 1.0,
        "lyric_keyframes": None,
        "material_id": material_id,
        "raw_segment_id": "", "render_index": 11000,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {"enable": False, "horizontal_pos_layout": 0, "size_layout": 0,
                              "target_follow": "", "vertical_pos_layout": 0},
        "reverse": False, "source": "segmentsourcenormal",
        "source_timerange": None, "speed": 1.0, "state": 0,
        "target_timerange": {"duration": int(duration_us), "start": int(start_us)},
        "template_id": "", "template_scene": "default",
        "track_attribute": 0, "track_render_index": 0, "uniform_scale": None,
        "visible": True, "volume": 1.0,
    }


def make_effect_track(name: str, segment: dict) -> dict:
    return {
        "attribute": 0, "flag": 0,
        "id": str(uuid.uuid4()).upper(),
        "is_default_name": False, "name": name,
        "segments": [segment], "type": "effect",
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


def apply_transitions(draft: dict, library: dict) -> List[str]:
    """Раскладывает переходы по индексам сегментов (TRANSITION_PLAN)."""
    log: List[str] = []
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    n_segs = len(main["segments"])

    for seg_idx, eff_id, dur_us, label in TRANSITION_PLAN:
        if seg_idx >= n_segs - 1:
            log.append(f"  ⚠ seg_idx {seg_idx}: вне диапазона (всего {n_segs}), пропуск")
            continue
        template = library["transitions"].get(eff_id)
        if template is None:
            log.append(f"  ⚠ effect_id {eff_id} ({label}) не нашёлся в Цирцее — пропуск")
            continue

        tr_mat = clone_transition(template, dur_us)
        draft["materials"]["transitions"].append(tr_mat)

        seg = main["segments"][seg_idx]
        refs = seg.setdefault("extra_material_refs", [])
        refs.append(tr_mat["id"])

        log.append(f"  → seg[{seg_idx:02d}] → seg[{seg_idx + 1:02d}]  {label:<28} {dur_us/1_000_000:.2f}s")
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
    seg["volume"] = VOLUME_MUSIC

    dur = int(seg["target_timerange"]["duration"])
    seg["common_keyframes"] = [{
        "id": gen_id_hex(),
        "material_id": "",
        "property_type": "KFTypeVolume",
        "keyframe_list": [
            {"id": gen_id_hex(), "curveType": "Line",
             "time_offset": max(0, dur - MUSIC_FADE_OUT_US),
             "left_control": {"x": 0.0, "y": 0.0},
             "right_control": {"x": 0.0, "y": 0.0},
             "values": [VOLUME_MUSIC], "string_value": "", "graphID": ""},
            {"id": gen_id_hex(), "curveType": "Line", "time_offset": dur,
             "left_control": {"x": 0.0, "y": 0.0},
             "right_control": {"x": 0.0, "y": 0.0},
             "values": [0.0], "string_value": "", "graphID": ""},
        ],
    }]
    log.append(f"  ♪ музыка: fade_out {MUSIC_FADE_OUT_US/1_000_000:.1f}s")
    return log


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


def apply_video_geometry(draft: dict) -> List[str]:
    log: List[str] = []
    main = next((t for t in draft["tracks"]
                 if t["type"] == "video" and t.get("name") == "main"), None)
    if main is None:
        log.append("  ⚠ video.main не найден — геометрию пропускаю")
        return log
    for seg in main.get("segments", []):
        clip = seg.setdefault("clip", {})
        clip["scale"] = {"x": 1.0, "y": 1.0}
        transform = clip.setdefault("transform", {"x": 0.0, "y": 0.0})
        transform["x"] = 0.0
        transform["y"] = 0.0
        uniform = seg.setdefault("uniform_scale", {"on": True, "value": 1.0})
        uniform["on"] = True
        uniform["value"] = 1.0
    log.append(
        f"  video.main: scale=1.0, transform=0,0 ({len(main.get('segments', []))} сегм.)"
    )
    return log


def make_local_audio_material(path: Path, full_dur_us: int) -> dict:
    mid = gen_id_hex()
    return {
        "ai_music_enter_from": "", "ai_music_generate_scene": 0, "ai_music_type": 0,
        "aigc_history_id": "", "aigc_item_id": "", "app_id": 0,
        "category_id": "", "category_name": "local",
        "check_flag": 3, "cloned_model_type": "", "copyright_limit_type": "none",
        "duration": int(full_dur_us),
        "effect_id": "", "formula_id": "",
        "id": mid, "intensifies_path": "",
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


def make_audio_segment(material_id: str, start_us: int, dur_us: int, volume: float) -> dict:
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
        "extra_material_refs": [], "group_id": "",
        "id": gen_id_hex(),
        "intensifies_audio": False, "is_loop": False, "is_placeholder": False,
        "is_tone_modify": False, "keyframe_refs": [],
        "last_nonzero_volume": 1.0, "lyric_keyframes": None,
        "material_id": material_id,
        "raw_segment_id": "",
        "render_index": 0, "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {"enable": False, "horizontal_pos_layout": 0,
                              "size_layout": 0, "target_follow": "",
                              "vertical_pos_layout": 0},
        "reverse": False, "source_timerange": {"duration": int(dur_us), "start": 0},
        "speed": 1.0, "state": 0, "stretch_alg": "",
        "target_timerange": {"duration": int(dur_us), "start": int(start_us)},
        "template_id": "", "template_scene": "default",
        "track_attribute": 0, "track_render_index": 0, "uniform_scale": None,
        "visible": True, "volume": float(volume),
    }


def apply_sfx(draft: dict) -> List[str]:
    log: List[str] = []
    main = next(t for t in draft["tracks"]
                if t["type"] == "video" and t.get("name") == "main")
    n_segs = len(main["segments"])

    sfx_track = {
        "attribute": 0, "flag": 0, "id": gen_id_hex(),
        "is_default_name": True, "name": "sfx",
        "segments": [], "type": "audio",
    }
    draft["tracks"].append(sfx_track)

    # WHOOSH на seg[7] и seg[13]
    if WHOOSH_FILE.is_file():
        whoosh_full = mp3_duration_us(WHOOSH_FILE)
        whoosh_dur = min(WHOOSH_LEN_US, whoosh_full)
        whoosh_mat = make_local_audio_material(WHOOSH_FILE, whoosh_full)
        draft["materials"]["audios"].append(whoosh_mat)
        for seg_idx in WHOOSH_SEG_INDICES:
            if seg_idx >= n_segs:
                continue
            seg = main["segments"][seg_idx]
            end_us = seg["target_timerange"]["start"] + seg["target_timerange"]["duration"]
            start_us = max(0, end_us - whoosh_dur // 2)
            wseg = make_audio_segment(whoosh_mat["id"], start_us, whoosh_dur, VOLUME_WHOOSH)
            sfx_track["segments"].append(wseg)
            log.append(f"  ♨ WHOOSH seg[{seg_idx:02d}] @{start_us/1e6:.2f}s vol={VOLUME_WHOOSH}")
    else:
        log.append(f"  ⚠ нет файла {WHOOSH_FILE} — WHOOSH пропускаю")

    # Crumpled paper на Бумажный шар (seg[17])
    if CRUMPLED_FILE.is_file() and CRUMPLED_SEG_INDEX < n_segs:
        crumpled_full = mp3_duration_us(CRUMPLED_FILE)
        crumpled_dur = min(CRUMPLED_LEN_US, crumpled_full)
        crumpled_mat = make_local_audio_material(CRUMPLED_FILE, crumpled_full)
        draft["materials"]["audios"].append(crumpled_mat)
        seg = main["segments"][CRUMPLED_SEG_INDEX]
        end_us = seg["target_timerange"]["start"] + seg["target_timerange"]["duration"]
        start_us = max(0, end_us - CRUMPLED_LEAD_US)
        cseg = make_audio_segment(crumpled_mat["id"], start_us, crumpled_dur, VOLUME_CRUMPLED)
        sfx_track["segments"].append(cseg)
        log.append(f"  📜 Crumpled seg[{CRUMPLED_SEG_INDEX:02d}] @{start_us/1e6:.2f}s vol={VOLUME_CRUMPLED}")
    elif not CRUMPLED_FILE.is_file():
        log.append(f"  ⚠ нет файла {CRUMPLED_FILE} — Crumpled пропускаю")

    sfx_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])
    return log


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Только показать план.")
    args = p.parse_args()

    if not CASSANDRA_FILE.is_file():
        print(f"Не нашёл драфт Кассандры: {CASSANDRA_FILE}")
        print("Сначала запусти: python build_cassandra.py")
        return 1
    if not CIRCE_FILE.is_file():
        print(f"Не нашёл драфт Цирцеи для забора шаблонов переходов: {CIRCE_FILE}")
        return 1

    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой его полностью (включая трей).")
        return 1

    print(f"Читаю Кассандру: {CASSANDRA_FILE}")
    draft = json.load(open(CASSANDRA_FILE, encoding="utf-8"))

    print(f"Читаю шаблоны Цирцеи: {CIRCE_FILE}")
    donor = json.load(open(CIRCE_FILE, encoding="utf-8"))
    library = build_template_library(donor)
    print(f"  transitions: {len(library['transitions'])}, "
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
    print("План переходов (по живой раскладке Цирцеи):")
    for line in apply_transitions(draft, library):
        print(line)

    print()
    print("Спецэффект intro-halftone:")
    for line in apply_halftone_effect(draft):
        print(line)

    print()
    print("Музыка:")
    for line in apply_music_fade(draft):
        print(line)

    print()
    print("SFX (WHOOSH + crumpled):")
    for line in apply_sfx(draft):
        print(line)

    if args.dry_run:
        print("\n--dry-run: драфт не трогаю.")
        return 0

    bkp = CASSANDRA_FILE.with_suffix(".json.enrich-backup")
    shutil.copy2(CASSANDRA_FILE, bkp)
    print(f"\nБэкап: {bkp.name}")

    json.dump(draft, open(CASSANDRA_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = CASSANDRA_DIR / tgt_name
        try:
            shutil.copy2(CASSANDRA_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    mats = draft["materials"]
    sfx_count = sum(len(t.get("segments", [])) for t in draft["tracks"]
                    if t["type"] == "audio" and t.get("name") == "sfx")
    print(f"\n✓ Готово. transitions={len(mats['transitions'])}, "
          f"video_effects={len(mats['video_effects'])}, "
          f"audio_fades={len(mats['audio_fades'])}, "
          f"sfx-сегментов={sfx_count}.")
    print("Открой CapCut -> проект «Аполлон и Кассандра» -> проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
