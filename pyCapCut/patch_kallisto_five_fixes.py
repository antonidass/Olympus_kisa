"""
Точечный патч для драфта «Каллисто и Аркас» — 5 правок без пересборки.
Музыка и всё остальное (которое пользователь добавил руками) НЕ трогается.

Правки:
  1. Halftone «Зеленые точки» на отдельный effect-трек поверх sent_002 (титул).
     Параметры 37/74/40/100 — канон из enrich_dionysus.py.
  2. Перенос энциклопедии Артемиды (4 трека artemis_scroll*) со сцены 2 на сцену 3
     (+scene_2_duration). Так же сдвигается parallel intro-keyboard-SFX
     (безымянный аудио-трек, начинающийся в один тайм со scroll).
  3. Cap длительности INTRO «Realistic sound effects for typing on keyboards»
     до 1.666s (длительность typewriter-анимации). Чтобы SFX заканчивался
     одновременно с окончанием стрелочки-печати.
  4. Между scene 23 и 24 (sid 021→022) — переход «Бумажный шар» +
     crumpled_paper.mp3 (за 0.333с до старта 24-й сцены, dur 0.866с, vol 1.0).
  5. Между scene 13 и 14 (sid 012→013) — переход «Взмах лапки».

CapCut должен быть полностью закрыт.
"""

from __future__ import annotations

import copy
import datetime
import io
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ─────────────────────────────────────────────────────────────────────
# Пути
# ─────────────────────────────────────────────────────────────────────

LOCALAPPDATA = Path(os.environ["LOCALAPPDATA"])
DRAFTS = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
KALLISTO_DIR = DRAFTS / "Каллисто и Аркас"
DRAFT_FILE = KALLISTO_DIR / "draft_content.json"
# Шаблоны переходов берём из существующих драфтов — там transition
# materials уже валидные, с path к CapCut Cache.
MIDAS_FILE = DRAFTS / "Мидас и золотое прикосновение" / "draft_content.json"
ORION_FILE = DRAFTS / "Орион и Артемида" / "draft_content.json"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CRUMPLED_PAPER_FILE = PROJECT_ROOT / "assets" / "sfx" / "crumpled_paper.mp3"


# ─────────────────────────────────────────────────────────────────────
# Константы
# ─────────────────────────────────────────────────────────────────────

# Item 1 — halftone «Зеленые точки»
HALFTONE_EFFECT_ID = "7399468802095795462"
HALFTONE_EFFECT_NAME = "Зеленые точки"
HALFTONE_EFFECT_MD5 = "87e58ba33f7dc96c4e108cd67c67e2a4"
HALFTONE_EFFECT_PATH = (
    LOCALAPPDATA / "CapCut" / "User Data" / "Cache" / "effect"
    / HALFTONE_EFFECT_ID / HALFTONE_EFFECT_MD5
)
HALFTONE_TITLE_AUDIO_NAME = "sentence_002_v13.mp3"  # титул в Каллисто

# Item 2 — энциклопедия Артемиды: список треков для сдвига
ARTEMIS_TRACK_NAMES = ("artemis_scroll", "artemis_scroll_logo", "artemis_scroll_text", "artemis_scroll_sfx")
ARTEMIS_TARGET_SID = "002"   # текущее место (sid сцены 2 на таймлайне)
ARTEMIS_NEW_SID = "003"      # куда переносим (sid сцены 3)

# Item 3 — cap длительности INTRO typing SFX
INTRO_TYPING_SFX_NAME = "Realistic sound effects for typing on keyboards"
TYPEWRITER_ANIMATION_DUR_US = 1_666_666

# Item 4 — Бумажный шар + crumpled SFX
PAPER_BAG_TRANSITION_ID = "7249296835204878850"
PAPER_BAG_TRANSITION_NAME = "Бумажный шар"
PAPER_BAG_SID = "021"        # переход после sid 021 (= scene 23 → scene 24)
PAPER_BAG_DUR_US = 1_270_000   # 1.27с (как в эталоне Персефоны)
CRUMPLED_PAPER_LEN_US = 866_667
CRUMPLED_PAPER_LEAD_US = 333_334
CRUMPLED_PAPER_VOLUME = 1.0

# Item 5 — Взмах лапки
PAW_WAVE_TRANSITION_ID = "7561440477262761277"
PAW_WAVE_TRANSITION_NAME = "Взмах лапки"
PAW_WAVE_SID = "012"         # переход после sid 012 (= scene 13 → scene 14)
PAW_WAVE_DUR_US = 1_000_000   # 1.0с — короткий комический переход

# SCENE_LAYOUT — должен совпадать с scene_structure_kallisto.py
SCENE_LAYOUT = [
    ("001", 1), ("002", 1), ("003", 1), ("004", 1), ("005", 1),
    ("006", 2), ("007", 1), ("008", 1), ("009", 1), ("010", 1),
    ("011", 1), ("012", 1), ("013", 1), ("014", 1), ("015", 1),
    ("016", 1), ("017", 1), ("018", 1), ("019", 2), ("020", 1),
    ("021", 1), ("022", 1),
]


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


def build_segment_to_sid_map() -> list[str]:
    out: list[str] = []
    for sid, n in SCENE_LAYOUT:
        out.extend([sid] * n)
    return out


def last_shot_index_per_sid() -> dict[str, int]:
    out: dict[str, int] = {}
    for i, sid in enumerate(build_segment_to_sid_map()):
        out[sid] = i
    return out


def first_shot_index_per_sid() -> dict[str, int]:
    out: dict[str, int] = {}
    for i, sid in enumerate(build_segment_to_sid_map()):
        out.setdefault(sid, i)
    return out


def scene_start_and_duration(draft: dict, sid: str) -> tuple[int, int]:
    """Считает start/duration сцены sid по сегментам main-трека."""
    seg_to_sid = build_segment_to_sid_map()
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    start = None
    dur = 0
    for i, seg in enumerate(main["segments"]):
        if i < len(seg_to_sid) and seg_to_sid[i] == sid:
            if start is None:
                start = int(seg["target_timerange"]["start"])
            dur += int(seg["target_timerange"]["duration"])
    return start or 0, dur


def find_transition_template(eff_id: str) -> Optional[dict]:
    """Ищет transition material с нужным effect_id в Midas или Орионе."""
    for path in (MIDAS_FILE, ORION_FILE):
        if not path.is_file():
            continue
        d = json.load(open(path, encoding="utf-8"))
        for t in d["materials"].get("transitions", []):
            if str(t.get("effect_id", "")) == eff_id:
                return t
    return None


def clone_transition(template: dict, duration_us: int) -> dict:
    m = copy.deepcopy(template)
    m["id"] = gen_id_hex()
    m["duration"] = int(duration_us)
    return m


def make_global_video_effect_halftone() -> dict:
    """Halftone «Зеленые точки» — те же 37/74/40/100 что в enrich_dionysus.py."""
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
        "algorithm_artifact_path": "", "apply_target_type": 2, "apply_time_range": None,
        "bind_segment_id": "", "category_id": "", "category_name": "",
        "common_keyframes": [], "covering_relation_change": 0,
        "disable_effect_faces": [], "effect_mask": [],
        "effect_id": HALFTONE_EFFECT_ID,
        "enable_mask": True, "enable_video_mask_shadow": True, "enable_video_mask_stroke": True,
        "formula_id": "", "id": gen_id_upper(), "item_effect_type": 0,
        "name": HALFTONE_EFFECT_NAME,
        "path": str(HALFTONE_EFFECT_PATH).replace("\\", "/"),
        "platform": "all", "render_index": 11000,
        "request_id": "20260521HALFTONE",
        "resource_id": HALFTONE_EFFECT_ID,
        "source_platform": 1, "sub_type": 0, "transparent_params": "",
        "time_range": None, "track_render_index": 0, "type": "video_effect",
        "value": 1.0, "version": "",
    }


def make_halftone_effect_track_segment(material_id: str, start_us: int, duration_us: int) -> dict:
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
        "extra_material_refs": [], "group_id": "", "hdr_settings": None,
        "id": gen_id_upper(), "intensifies_audio": False,
        "is_loop": False, "is_placeholder": False, "is_tone_modify": False,
        "keyframe_refs": [], "last_nonzero_volume": 1.0, "lyric_keyframes": None,
        "material_id": material_id, "raw_segment_id": "",
        "render_index": 11000, "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {"enable": False, "horizontal_pos_layout": 0,
                              "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0},
        "reverse": False, "source": "segmentsourcenormal",
        "source_timerange": None, "speed": 1.0, "state": 0,
        "target_timerange": {"duration": int(duration_us), "start": int(start_us)},
        "template_id": "", "template_scene": "default",
        "track_attribute": 0, "track_render_index": 0, "uniform_scale": None,
        "visible": True, "volume": 1.0,
    }


def make_effect_track(name: str, segment: dict) -> dict:
    return {
        "attribute": 0, "flag": 0, "id": gen_id_upper(),
        "is_default_name": False, "name": name,
        "segments": [segment], "type": "effect",
    }


def mp3_duration_us(path: Path) -> int:
    try:
        from mutagen.mp3 import MP3
        return int(MP3(str(path)).info.length * 1_000_000)
    except Exception:
        return CRUMPLED_PAPER_LEN_US + 200_000


def make_crumpled_paper_material(path: Path, full_dur_us: int) -> dict:
    mid = gen_id_hex()
    return {
        "ai_music_enter_from": "", "ai_music_generate_scene": 0, "ai_music_type": 0,
        "aigc_history_id": "", "aigc_item_id": "", "app_id": 0,
        "category_id": "", "category_name": "local",
        "check_flag": 3, "cloned_model_type": "", "copyright_limit_type": "none",
        "duration": int(full_dur_us),
        "effect_id": "7350583934167552513",
        "formula_id": "", "id": mid, "intensifies_path": "",
        "is_ai_clone_tone": False, "is_ai_clone_tone_post": False,
        "is_text_edit_overdub": False, "is_ugc": False,
        "local_material_id": mid, "lyric_type": 0,
        "mock_tone_speaker": "", "moyin_emotion": "",
        "music_id": mid, "music_source": "",
        "name": "Crumpled paper",
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
        "type": "sound", "video_id": "", "wave_points": [],
    }


def make_crumpled_segment(material_id: str, start_us: int, dur_us: int) -> dict:
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
        "material_id": material_id, "raw_segment_id": "",
        "render_index": 0, "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {"enable": False, "horizontal_pos_layout": 0,
                              "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0},
        "reverse": False, "source_timerange": {"duration": int(dur_us), "start": 0},
        "speed": 1.0, "state": 0, "stretch_alg": "",
        "target_timerange": {"duration": int(dur_us), "start": int(start_us)},
        "template_id": "", "template_scene": "default",
        "track_attribute": 0, "track_render_index": 0, "uniform_scale": None,
        "visible": True, "volume": CRUMPLED_PAPER_VOLUME,
    }


# ─────────────────────────────────────────────────────────────────────
# Item 1 — Halftone «Зеленые точки» поверх sentence_002
# ─────────────────────────────────────────────────────────────────────

def apply_halftone(draft: dict) -> str:
    audios_by_id = {a["id"]: a for a in draft["materials"].get("audios", [])}
    voice = next((t for t in draft["tracks"] if t["type"] == "audio" and t.get("name") == "voice"), None)
    title_seg = None
    if voice:
        for s in voice.get("segments", []):
            mat = audios_by_id.get(s.get("material_id"), {})
            if mat.get("name") == HALFTONE_TITLE_AUDIO_NAME:
                title_seg = s
                break
    if title_seg is None:
        return f"  WARN: voice-сегмент {HALFTONE_TITLE_AUDIO_NAME} не найден, halftone пропущен"

    start_us = int(title_seg["target_timerange"]["start"])
    duration_us = int(title_seg["target_timerange"]["duration"])

    # Снимаем старый halftone-трек если был (идемпотентность)
    draft["tracks"] = [t for t in draft["tracks"] if t.get("name") != "halftone_green_dots"]
    # И связанный материал
    halftone_ids_old = {
        e["id"] for e in draft["materials"].get("video_effects", [])
        if str(e.get("effect_id", "")) == HALFTONE_EFFECT_ID
    }
    draft["materials"]["video_effects"] = [
        e for e in draft["materials"].get("video_effects", [])
        if e["id"] not in halftone_ids_old
    ]

    mat = make_global_video_effect_halftone()
    draft["materials"]["video_effects"].append(mat)
    seg = make_halftone_effect_track_segment(mat["id"], start_us, duration_us)
    draft["tracks"].append(make_effect_track("halftone_green_dots", seg))
    return f"  OK halftone «Зеленые точки» поверх {HALFTONE_TITLE_AUDIO_NAME}: {start_us/1e6:.2f}–{(start_us+duration_us)/1e6:.2f}s"


# ─────────────────────────────────────────────────────────────────────
# Item 2 — Перенос энциклопедии Артемиды со сцены 2 на сцену 3
# ─────────────────────────────────────────────────────────────────────

def apply_artemis_move(draft: dict) -> list[str]:
    log: list[str] = []
    _, scene2_dur = scene_start_and_duration(draft, ARTEMIS_TARGET_SID)
    if scene2_dur == 0:
        return [f"  WARN: не нашёл sid {ARTEMIS_TARGET_SID}, перенос отменён"]

    # Сдвигаем все треки artemis_scroll*
    for tname in ARTEMIS_TRACK_NAMES:
        track = next((t for t in draft["tracks"] if t.get("name") == tname), None)
        if not track:
            log.append(f"  WARN трек {tname} не найден — пропуск")
            continue
        for s in track.get("segments", []):
            before = s["target_timerange"]["start"]
            s["target_timerange"]["start"] = int(before + scene2_dur)
            log.append(f"  {tname}: {before/1e6:.3f}s -> {(before+scene2_dur)/1e6:.3f}s")

    # Дополнительно сдвигаем безымянный audio-track с keyboard SFX для энциклопедии:
    # это второй сегмент Realistic typing keyboard, который стартует в один тайм
    # с artemis_scroll (не путать с интро-typing над sent_002).
    audios_by_id = {a["id"]: a for a in draft["materials"].get("audios", [])}
    artemis_scroll = next((t for t in draft["tracks"] if t.get("name") == "artemis_scroll"), None)
    if artemis_scroll and artemis_scroll["segments"]:
        scroll_old_start = artemis_scroll["segments"][0]["target_timerange"]["start"] - scene2_dur
        for tr in draft["tracks"]:
            if tr["type"] != "audio" or tr.get("name"):
                continue  # только безымянные audio-треки
            for s in tr.get("segments", []):
                mat = audios_by_id.get(s.get("material_id"), {})
                if mat.get("name") != INTRO_TYPING_SFX_NAME:
                    continue
                # Это keyboard. Если он стартует в один тайм с artemis_scroll (старым) —
                # это keyboard энциклопедии, переносим.
                if abs(s["target_timerange"]["start"] - scroll_old_start) < 10_000:
                    before = s["target_timerange"]["start"]
                    s["target_timerange"]["start"] = int(before + scene2_dur)
                    log.append(f"  encyclopedia keyboard SFX: {before/1e6:.3f}s -> {(before+scene2_dur)/1e6:.3f}s")
    return log


# ─────────────────────────────────────────────────────────────────────
# Item 3 — Cap INTRO typing SFX duration до длительности typewriter-анимации
# ─────────────────────────────────────────────────────────────────────

def apply_intro_typing_cap(draft: dict) -> str:
    """Находит keyboard-typing SFX, который стартует в начале sent_002, и
    обрезает его длительность до TYPEWRITER_ANIMATION_DUR_US (1.666s).
    Энциклопедийный keyboard остаётся как есть (он привязан к scroll-анимации)."""
    audios_by_id = {a["id"]: a for a in draft["materials"].get("audios", [])}

    # Находим start sentence_002 (титул)
    voice = next((t for t in draft["tracks"] if t["type"] == "audio" and t.get("name") == "voice"), None)
    intro_start = None
    if voice:
        for s in voice.get("segments", []):
            mat = audios_by_id.get(s.get("material_id"), {})
            if mat.get("name") == HALFTONE_TITLE_AUDIO_NAME:
                intro_start = int(s["target_timerange"]["start"])
                break
    if intro_start is None:
        return "  WARN: не нашёл sentence_002 для INTRO typing cap"

    capped = 0
    for tr in draft["tracks"]:
        if tr["type"] != "audio" or tr.get("name"):
            continue
        for s in tr.get("segments", []):
            mat = audios_by_id.get(s.get("material_id"), {})
            if mat.get("name") != INTRO_TYPING_SFX_NAME:
                continue
            # Только тот SFX, который стартует ровно у sentence_002 (intro)
            if abs(s["target_timerange"]["start"] - intro_start) > 50_000:
                continue
            old_dur = s["target_timerange"]["duration"]
            if old_dur <= TYPEWRITER_ANIMATION_DUR_US:
                return f"  intro typing SFX уже не длиннее 1.666s (dur={old_dur/1e6:.3f}s)"
            s["target_timerange"]["duration"] = TYPEWRITER_ANIMATION_DUR_US
            # source_timerange тоже укорачиваем, чтобы не было таймстретча
            if s.get("source_timerange") and "duration" in s["source_timerange"]:
                s["source_timerange"]["duration"] = TYPEWRITER_ANIMATION_DUR_US
            capped += 1
            return f"  OK intro typing SFX: dur {old_dur/1e6:.3f}s -> {TYPEWRITER_ANIMATION_DUR_US/1e6:.3f}s (заканчивается с анимацией)"
    return "  WARN: intro typing SFX не найден"


# ─────────────────────────────────────────────────────────────────────
# Items 4 & 5 — Замена Dissolve на нужный transition для конкретного sid
# ─────────────────────────────────────────────────────────────────────

def replace_transition(draft: dict, sid: str, new_eff_id: str, new_label: str, want_dur_us: int) -> str:
    template = find_transition_template(new_eff_id)
    if template is None:
        return f"  WARN transition {new_label} ({new_eff_id}) не найден в Midas/Орионе"

    last_idx = last_shot_index_per_sid()
    seg_idx = last_idx.get(sid)
    if seg_idx is None:
        return f"  WARN sid {sid} не найден"

    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    seg = main["segments"][seg_idx]
    refs = seg.setdefault("extra_material_refs", [])

    # Снимаем старые transition-материалы из refs этой сцены
    trans_ids = {t["id"] for t in draft["materials"].get("transitions", [])}
    refs_kept = [r for r in refs if r not in trans_ids]
    # И находим какие удалили
    refs_removed = [r for r in refs if r in trans_ids]
    seg["extra_material_refs"] = refs_kept
    # Удаляем сами материалы (только те, что были в refs этой сцены)
    draft["materials"]["transitions"] = [
        t for t in draft["materials"]["transitions"] if t["id"] not in refs_removed
    ]

    # Добавляем новый transition
    new_mat = clone_transition(template, want_dur_us)
    draft["materials"]["transitions"].append(new_mat)
    seg["extra_material_refs"].append(new_mat["id"])
    return f"  OK sid {sid} -> {new_label} (dur={want_dur_us/1e6:.2f}s)"


def apply_crumpled_paper(draft: dict) -> str:
    """Кладёт crumpled_paper.mp3 за 0.333с до старта sid 022 (scene 24)."""
    if not CRUMPLED_PAPER_FILE.is_file():
        return f"  WARN не нашёл {CRUMPLED_PAPER_FILE} — crumpled SFX пропущен"

    # start сцены sid 022 = scene_24
    next_start, _ = scene_start_and_duration(draft, "022")
    full_dur = mp3_duration_us(CRUMPLED_PAPER_FILE)
    use_dur = min(CRUMPLED_PAPER_LEN_US, full_dur)
    start_us = max(0, next_start - CRUMPLED_PAPER_LEAD_US)

    # Снимаем старый crumpled (идемпотентность): из дорожки sfx удаляем
    # все сегменты, у которых material — Crumpled paper.
    audios_by_id = {a["id"]: a for a in draft["materials"].get("audios", [])}
    for tr in draft["tracks"]:
        if tr["type"] != "audio" or tr.get("name") != "sfx":
            continue
        tr["segments"] = [
            s for s in tr.get("segments", [])
            if audios_by_id.get(s.get("material_id"), {}).get("name") != "Crumpled paper"
        ]

    # Старые Crumpled paper материалы выкидываем
    draft["materials"]["audios"] = [
        a for a in draft["materials"].get("audios", []) if a.get("name") != "Crumpled paper"
    ]

    mat = make_crumpled_paper_material(CRUMPLED_PAPER_FILE, full_dur)
    draft["materials"]["audios"].append(mat)

    sfx_track = next((t for t in draft["tracks"] if t["type"] == "audio" and t.get("name") == "sfx"), None)
    if sfx_track is None:
        sfx_track = {
            "attribute": 0, "flag": 0, "id": gen_id_hex(),
            "is_default_name": True, "name": "sfx",
            "segments": [], "type": "audio",
        }
        draft["tracks"].append(sfx_track)

    sfx_track["segments"].append(make_crumpled_segment(mat["id"], start_us, use_dur))
    sfx_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])
    return f"  OK Crumpled paper SFX: {start_us/1e6:.2f}s dur={use_dur/1e6:.2f}s vol={CRUMPLED_PAPER_VOLUME}"


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    if not DRAFT_FILE.is_file():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1
    if not check_capcut_closed():
        print("WARN CapCut запущен. Закрой его полностью (включая трей) и запусти ещё раз.")
        return 1

    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = KALLISTO_DIR / f"draft_content.json.five-fixes-backup-{ts}"
    shutil.copy2(DRAFT_FILE, backup)
    print(f"Бэкап: {backup.name}")
    print()

    print("Item 1 — Halftone «Зеленые точки» поверх sent_002:")
    print(apply_halftone(draft))
    print()

    print("Item 2 — Перенос энциклопедии Артемиды со сцены 2 на сцену 3:")
    for line in apply_artemis_move(draft):
        print(line)
    print()

    print("Item 3 — Cap INTRO typing SFX до длительности typewriter-анимации:")
    print(apply_intro_typing_cap(draft))
    print()

    print("Item 4 — Бумажный шар между scene 23 и scene 24 (sid 021 -> 022):")
    print(replace_transition(draft, PAPER_BAG_SID, PAPER_BAG_TRANSITION_ID,
                              PAPER_BAG_TRANSITION_NAME, PAPER_BAG_DUR_US))
    print(apply_crumpled_paper(draft))
    print()

    print("Item 5 — Взмах лапки между scene 13 и scene 14 (sid 012 -> 013):")
    print(replace_transition(draft, PAW_WAVE_SID, PAW_WAVE_TRANSITION_ID,
                              PAW_WAVE_TRANSITION_NAME, PAW_WAVE_DUR_US))
    print()

    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = KALLISTO_DIR / tgt_name
        try:
            shutil.copy2(DRAFT_FILE, tgt)
        except Exception as ex:
            print(f"  WARN не удалось синхронизировать {tgt_name}: {ex}")

    print("OK Готово. Открой CapCut -> Drafts -> «Каллисто и Аркас» -> проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
