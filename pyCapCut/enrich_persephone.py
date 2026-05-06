"""
Обогащает уже собранный CapCut-драфт «Персефона и Аид» переходами,
видео-эффектами, фейдом музыки, громкостями и whoosh-SFX. Полная
копия enrich_orpheus.py с подменой карты SCENE_LAYOUT, PLAN под
24 сцены Персефоны и без CTA-аутро (финальный круг на сцене 024).

Подход тот же: тянем готовые transition / video_effect шаблоны из
живого драфта Мидаса (где пользователь уже расставил их вручную).
Это гарантирует, что все effect_id уже скачаны в CapCut Cache и
схема полей точно та, что CapCut ожидает.

Запуск (CapCut должен быть полностью закрыт, включая трей):
    python enrich_persephone.py
    python enrich_persephone.py --dry-run   # только показать план
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
PERSEPHONE_DIR = DRAFTS / "Персефона и Аид"
PERSEPHONE_FILE = PERSEPHONE_DIR / "draft_content.json"
MIDAS_FILE = DRAFTS / "Мидас и золотое прикосновение" / "draft_content.json"


# ─────────────────────────────────────────────────────────────────────
# Карта sid сцены → число шотов в треке.
# Должна совпадать со scene_structure_persephone.py:
#   24 сцены с озвучкой, 28 mp4-шотов (2-шотные: 004/006/013/020).
# ─────────────────────────────────────────────────────────────────────

SCENE_LAYOUT: List[Tuple[str, int]] = [
    ("001", 1), ("002", 1), ("003", 1), ("004", 2), ("005", 1),
    ("006", 2), ("007", 1), ("008", 1), ("009", 1), ("010", 1),
    ("011", 1), ("012", 1), ("013", 2), ("014", 1), ("015", 1),
    ("016", 1), ("017", 1), ("018", 1), ("019", 1), ("020", 2),
    ("021", 1), ("022", 1), ("023", 1), ("024", 1),
]
# Сумма: 28 ✓


# ─────────────────────────────────────────────────────────────────────
# План переходов под контекст мифа Персефоны:
#   001 крючок «украл» — резкий зум с тряской
#   002 интро-карточка → плавный диссолв
#   003 идиллия → плавный
#   004 трещина + колесница → драматичный зум
#   005 Аид крупно → камера-шейк
#   006 хватание + унеслись → пастельные блики (контраст «над/под землёй»)
#   007 трон тёмный → диссолв
#   008 Деметра ищет → диссолв
#   009 девять дней с факелом → размытие шар
#   010 Гелиос шепнул → полутоновая вспышка
#   011 «Зевс в курсе» → глитч-вспышка
#   012 Деметра в горе → размытие шар
#   013 поля высохли + лёд → диссолв
#   014 голод → диссолв
#   015 Зевс в панике → переход-зум
#   016 Гермес летит → свист
#   017 Персефона-царица → диссолв
#   018 зерно граната → зум с тряской
#   019 связь навсегда → полутоновая вспышка
#   020 треть года / остальное → растяжение влево (split-сцена)
#   021 весна → пастельные блики
#   022 зима → разделение рваной бумагой
#   023 «зима — это не погода» → растяжение влево
#   (024 — последняя, переход не нужен)
# ─────────────────────────────────────────────────────────────────────

PLAN: List[Tuple[str, str, float, str]] = [
    ("001", "7340177833508999681", 1.20, "Зум с тряской 2"),
    ("002", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("003", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("004", "7340177833508999681", 1.20, "Зум с тряской 2"),
    ("005", "7262258307128103425", 1.00, "Зум с тряской"),
    ("006", "7550260993348177213", 1.10, "Пастельные блики"),
    ("007", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("008", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("009", "7159450506648097281", 1.20, "Размытие (шар)"),
    ("010", "7609529907026119941", 1.20, "Полутоновая вспышка"),
    ("011", "7234817586234397186", 0.70, "Глитч-вспышка"),
    ("012", "7159450506648097281", 1.20, "Размытие (шар)"),
    ("013", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("014", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("015", "7464433696658001213", 1.20, "Переход-зум"),
    ("016", "6724239584663704071", 1.00, "Свист"),
    ("017", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("018", "7340177833508999681", 1.20, "Зум с тряской 2"),
    ("019", "7609529907026119941", 1.20, "Полутоновая вспышка"),
    ("020", "7620344224734629138", 1.20, "Растяжение влево"),
    ("021", "7550260993348177213", 1.10, "Пастельные блики"),
    ("022", "7604808025253137682", 1.40, "Разделение рваной бумагой"),
    ("023", "7620344224734629138", 1.20, "Растяжение влево"),
    # 024 — последняя сцена, переход не нужен
]

WHOOSH_TRANSITION_EFFECT_IDS = {
    "6724227717195108867",  # Влево
    "6724227330190873100",  # Вниз
    "6724227090872275463",  # Вверх
    "7327547930728993282",  # Поворот и изменение
    "6724227965965435396",  # Вправо
}
WHOOSH_TRANSITION_LABELS = {"Влево", "Вправо", "Вверх", "Вниз", "Поворот и изменение"}


# ─────────────────────────────────────────────────────────────────────
# Видео-эффекты как у Мидаса: «Ожоги на пленке» на интро,
# «Финальный круг» на последнюю сцену.
# Персефона без CTA-аутро, поэтому финальный эффект ставим на 024.
# ─────────────────────────────────────────────────────────────────────

EFFECT_PLAN: List[Tuple[str, str, str]] = [
    ("002", "7563294314475080965", "Ожоги на пленке"),
    ("024", "7613711779025358087", "Финальный круг"),
]


# Длительность fade_out на фоновой музыке.
MUSIC_FADE_OUT_US = int(MUSIC_FADE_OUT_SECONDS * 1_000_000)

MAX_TRANSITION_RATIO = 0.45
MIN_TRANSITION_US = 200_000

# Громкости — по эталону template_theseus.py.
VOLUME_VOICE = VOLUMES["voice"]
VOLUME_VIDEO = VOLUMES["video"]
VOLUME_MUSIC = VOLUMES["music"]
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


def make_audio_fade(fade_in_us: int, fade_out_us: int) -> dict:
    return {
        "fade_in_duration": int(fade_in_us),
        "fade_out_duration": int(fade_out_us),
        "fade_type": 0,
        "id": str(uuid.uuid4()).upper(),
        "type": "audio_fade",
    }


# ─────────────────────────────────────────────────────────────────────
# Применение к драфту Персефоны
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
        ve_mat["time_range"] = {
            "start": 0,
            "duration": int(seg["target_timerange"]["duration"]),
        }
        log.append(f"  ★ {sid:<4} {label}  (на сегмент #{seg_idx})")
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
               f"{n_sfx_segs} whoosh-сегментов")
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

    if not PERSEPHONE_FILE.is_file():
        print(f"Не нашёл драфт Персефоны: {PERSEPHONE_FILE}")
        print("Сначала запусти: python build_persephone.py")
        return 1
    if not MIDAS_FILE.is_file():
        print(f"Не нашёл драфт Мидаса для забора шаблонов: {MIDAS_FILE}")
        return 1

    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой его полностью (включая трей) и запусти скрипт ещё раз.")
        return 1

    print(f"Читаю Персефону: {PERSEPHONE_FILE}")
    draft = json.load(open(PERSEPHONE_FILE, encoding="utf-8"))

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

    bkp = PERSEPHONE_FILE.with_suffix(".json.enrich-backup")
    shutil.copy2(PERSEPHONE_FILE, bkp)
    print(f"\nБэкап: {bkp.name}")

    json.dump(draft, open(PERSEPHONE_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = PERSEPHONE_DIR / tgt_name
        try:
            shutil.copy2(PERSEPHONE_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    mats = draft["materials"]
    sfx_count = sum(len(t.get("segments", [])) for t in draft["tracks"]
                    if t["type"] == "audio" and t.get("name") == "sfx")
    print(f"\n✓ Готово. transitions={len(mats['transitions'])}, "
          f"video_effects={len(mats['video_effects'])}, "
          f"audio_fades={len(mats['audio_fades'])}, "
          f"whoosh-сегментов={sfx_count}.")
    print("Открой CapCut → проект «Персефона и Аид» → проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
