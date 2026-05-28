"""
Обогащает уже собранный CapCut-драфт «Баба-Яга» переходами, фейдом музыки
и громкостями. Адаптация enrich_oh_01.py под 23 сцены Бабы-Яги:
  - 23 single-shot сцены, 22 стыка между ними;
  - PLAN: базово диссолв + 3-4 фактурных перехода на ключевых стыках
    (превращение избы, полёт ступы, обещание даров → POV-приближение);
  - EFFECT_PLAN ПУСТОЙ — «Финальный круг» запрещён каноном
    (см. memory feedback_banned_transitions_and_effects);
  - HALFTONE «Зелёные точки» НЕ применяется — этот миф БЕЗ титульной
    строки «Баба-Яга. Миф за минуту.» (см. memory
    project_baba_yaga_no_title_line), а halftone канонически кладётся
    поверх sentence_002-титула. Нет титула → нет halftone;
  - стикеров нет (предварительный монтаж);
  - fade_out музыки 2.9 с в конце;
  - громкости как у Персефоны: voice 1.0, video 0.34, music 0.1348.

Шаблоны переходов/эффектов берём из живого драфта **Персефоны и Аид**
(эталон канала). Все effect_id оттуда уже скачаны в CapCut Cache.

Запуск (CapCut должен быть полностью закрыт, включая трей):
    python enrich_baba_yaga.py
    python enrich_baba_yaga.py --dry-run   # только показать план
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
YAGA_DIR = DRAFTS / "Баба-Яга"
YAGA_FILE = YAGA_DIR / "draft_content.json"
# Источник шаблонов переходов/эффектов — живой драфт Персефоны.
EXAMPLE_FILE = DRAFTS / "Персефона и Аид" / "draft_content.json"


# ─────────────────────────────────────────────────────────────────────
# Карта sid сцены → число шотов в треке.
# Должна совпадать со scene_structure_baba_yaga.py: 23 сцены, у всех 1 шот.
# ─────────────────────────────────────────────────────────────────────

SCENE_LAYOUT: List[Tuple[str, int]] = [
    ("001", 1), ("002", 1), ("003", 1), ("004", 1), ("005", 1),
    ("006", 1), ("007", 1), ("008", 1), ("009", 1), ("010", 1),
    ("011", 1), ("012", 1), ("013", 1), ("014", 1), ("015", 1),
    ("016", 1), ("017", 1), ("018", 1), ("019", 1), ("020", 1),
    ("021", 1), ("022", 1), ("023", 1),
]
# Сумма: 23 ✓


# ─────────────────────────────────────────────────────────────────────
# План переходов под драматургию Бабы-Яги (предварительный):
#   001 → 002  хук-изба → Яга в дверях      — диссолв
#   002 → 003  дверь → порог двух миров     — диссолв
#   003 → 004  миры → древний дуб           — диссолв
#   004 → 005  дуб → путник шепчет формулу  — диссолв
#   005 → 006  формула → изба поворачивается — Резкий зум (магия активируется)
#   006 → 007  поворот → дверь скрипит       — диссолв
#   007 → 008  дверь → устье печи            — диссолв (вход внутрь)
#   008 → 009  печь → ступа в углу           — диссолв
#   009 → 010  ступа → полёт ступы           — Размытие (шар) (магический скачок)
#   010 → 011  полёт → забор из костей       — диссолв
#   011 → 012  забор → крупный план черепа   — диссолв
#   012 → 013  череп → передача путнику      — диссолв
#   013 → 014  благословение → суд (печь)    — Глитч-вспышка (резкий поворот к каре)
#   014 → 015  кара → портрет Яги            — диссолв (выдох после драмы)
#   015 → 016  портрет → силуэт против луны  — диссолв
#   016 → 017  силуэт → сплит-кадр           — диссолв
#   017 → 018  сплит → три рунических знака  — диссолв
#   018 → 019  руны → три задачи             — диссолв
#   019 → 020  задачи → котёл (угроза)       — Размытие (шар) (магическая угроза)
#   020 → 021  котёл → три магических дара   — диссолв
#   021 → 022  дары → POV: куриная лапа      — Бумажный шар (нарративный поворот в POV)
#   022 → 023  POV-лапа → POV-шаг            — диссолв (продолжение POV)
#   (023 — последняя, переход не нужен)
#
# ⚠ ЗАПРЕЩЕНО: «Полутоновая вспышка» (7609529907026119941),
# «Пастельные блики» (7550260993348177213), «Зум с тряской» 7262258307128103425
# и «Зум с тряской 2» 7340177833508999681 — больше не используем (решение
# 2026-05-18). См. memory feedback_banned_transitions_and_effects.
# Принципиальная политика: базовый перебор — Dissolve, ярких акцентов
# не больше 4-5 на ролик. Здесь 4 акцента (006, 009, 013, 019, 021) — на
# ключевых точках сюжета (магия / поворот / угроза / финальный нарратив).
# ─────────────────────────────────────────────────────────────────────

PLAN: List[Tuple[str, str, float, str]] = [
    ("001", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("002", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("003", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("004", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("005", "7574908666210471221", 1.10, "Резкий зум"),
    ("006", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("007", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("008", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("009", "7159450506648097281", 1.20, "Размытие (шар)"),
    ("010", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("011", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("012", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("013", "7234817586234397186", 0.70, "Глитч-вспышка"),
    ("014", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("015", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("016", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("017", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("018", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("019", "7159450506648097281", 1.20, "Размытие (шар)"),
    ("020", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("021", "7249296835204878850", 1.30, "Бумажный шар"),
    ("022", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    # 023 — последняя сцена, переход не нужен
]


# ─────────────────────────────────────────────────────────────────────
# Видео-эффекты:
# ⚠ ЗАПРЕЩЕНО: «Финальный круг» (7613711779025358087) — больше не
# используем в проекте (решение 2026-05-18). EFFECT_PLAN пустой;
# финал ролика заканчивается без видео-эффекта на хвосте.
# См. memory feedback_banned_transitions_and_effects.
# ─────────────────────────────────────────────────────────────────────

EFFECT_PLAN: List[Tuple[str, str, str]] = []


# ─────────────────────────────────────────────────────────────────────
# Halftone «Зеленые точки» — обязательный элемент канона канала.
# Спецэффект CapCut, ложится на отдельный effect-трек поверх интро-сцены
# на время произнесения титула (sentence_002). Параметры подобраны
# вручную в драфте Персефоны: текстура 37, фильтры 74, цвет 40, размер 100.
# См. CAPCUT.md §5.1 + memory feedback_halftone_intro.
# ─────────────────────────────────────────────────────────────────────

HALFTONE_SCENE = "001"
HALFTONE_EFFECT_ID = "7399468802095795462"
HALFTONE_EFFECT_NAME = "Зеленые точки"
HALFTONE_EFFECT_MD5 = "87e58ba33f7dc96c4e108cd67c67e2a4"
HALFTONE_EFFECT_PATH = (
    LOCALAPPDATA / "CapCut" / "User Data" / "Cache" / "effect"
    / HALFTONE_EFFECT_ID / HALFTONE_EFFECT_MD5
)
# Halftone ложится на длительность аудио титула. В oh_01 титул —
# sentence_002 (вторая часть Сцены 001 после хука).
HALFTONE_AUDIO_NAME = "sentence_002_v1.mp3"


# ─────────────────────────────────────────────────────────────────────
# Crumpled paper SFX — обязательный звук на каждом переходе «Бумажный шар».
# См. CAPCUT.md §6.3 + memory feedback_paper_bag_sfx и эталон enrich_orpheus.py.
# ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CRUMPLED_PAPER_FILE = PROJECT_ROOT / "assets" / "sfx" / "crumpled_paper.mp3"
CRUMPLED_PAPER_LEN_US = 866_667           # 0.866s — длительность SFX
CRUMPLED_PAPER_LEAD_US = 333_334          # 0.333s — старт до начала следующей сцены
VOLUME_CRUMPLED_PAPER = 1.0
PAPER_BAG_EFFECT_ID = "7249296835204878850"  # переход «Бумажный шар»


# Длительность fade_out на фоновой музыке (эталон Персефоны).
MUSIC_FADE_OUT_SECONDS = 2.9
MUSIC_FADE_OUT_US = int(MUSIC_FADE_OUT_SECONDS * 1_000_000)

MAX_TRANSITION_RATIO = 0.45
MIN_TRANSITION_US = 200_000

# Громкости — эталон Персефоны (музыка тише, чем у Тесея — 0.1348 vs 0.1954).
VOLUME_VOICE = 1.00
VOLUME_VIDEO = 0.34
VOLUME_MUSIC = 0.1348


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
    seg_to_sid = build_segment_to_sid_map()
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    total = 0
    for i, seg in enumerate(main["segments"]):
        if i < len(seg_to_sid) and seg_to_sid[i] == sid:
            total += seg["target_timerange"]["duration"]
    return total


# ─────────────────────────────────────────────────────────────────────
# Сборка библиотеки шаблонов из источника
# ─────────────────────────────────────────────────────────────────────

def build_template_library(example_draft: dict) -> dict:
    mats = example_draft["materials"]
    transitions: Dict[str, dict] = {}
    for t in mats.get("transitions", []):
        transitions[str(t["effect_id"])] = t
    video_effects: Dict[str, dict] = {}
    for e in mats.get("video_effects", []):
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
# Halftone «Зеленые точки» — материал и трек
# ─────────────────────────────────────────────────────────────────────

def make_global_video_effect(effect_id: str, name: str) -> dict:
    """Material для глобального video_effect (halftone). Параметры под текстура 37 /
    фильтры 74 / цвет 40 / размер 100 — эталон Персефоны."""
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
        "request_id": "20260518HALFTONE",
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
        "enable_color_wheels": True, "enable_hsl": False,
        "enable_hsl_curves": True, "enable_lut": False,
        "enable_mask_shadow": False, "enable_mask_stroke": False,
        "enable_smart_color_adjust": False, "enable_video_mask": True,
        "extra_material_refs": [],
        "group_id": "",
        "hdr_settings": None,
        "id": str(uuid.uuid4()).upper(),
        "intensifies_audio": False, "is_loop": False, "is_placeholder": False,
        "is_tone_modify": False, "keyframe_refs": [],
        "last_nonzero_volume": 1.0,
        "lyric_keyframes": None,
        "material_id": material_id,
        "raw_segment_id": "",
        "render_index": 11000,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False, "horizontal_pos_layout": 0, "size_layout": 0,
            "target_follow": "", "vertical_pos_layout": 0,
        },
        "reverse": False, "source": "segmentsourcenormal",
        "source_timerange": None,
        "speed": 1.0,
        "state": 0,
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


def mp3_duration_us(path: Path) -> int:
    """Длительность аудиофайла. Пытаемся MP3, потом M4A — assets/sfx/crumpled_paper.mp3
    на самом деле ISO Media (ALAC/AAC), так что MP3-парсер на нём падает."""
    try:
        from mutagen.mp3 import MP3
        return int(MP3(str(path)).info.length * 1_000_000)
    except Exception:
        pass
    try:
        from mutagen.mp4 import MP4
        return int(MP4(str(path)).info.length * 1_000_000)
    except Exception:
        pass
    try:
        from mutagen import File as MutagenFile
        f = MutagenFile(str(path))
        if f is not None and f.info is not None:
            return int(f.info.length * 1_000_000)
    except Exception:
        pass
    # Fallback: длительность достаточно для CRUMPLED_PAPER_LEN_US + запас.
    return CRUMPLED_PAPER_LEN_US + 200_000


def make_whoosh_audio_material(path: Path, full_dur_us: int) -> dict:
    """Material для extract_music аудио-SFX (whoosh / crumpled paper / и т.п.)."""
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


def make_sfx_segment(material_id: str, start_us: int, dur_us: int, volume: float) -> dict:
    """Сегмент SFX-аудио (whoosh, crumpled paper и т.п.)."""
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
        "visible": True, "volume": volume,
    }


def apply_crumpled_paper_sfx(draft: dict) -> List[str]:
    """Кладёт «Crumpled paper» на каждом стыке, где в PLAN стоит «Бумажный шар».
    Универсальная функция: автоматически находит ВСЕ переходы с effect_id
    PAPER_BAG_EFFECT_ID и ставит звук за 0.333с до старта следующей сцены."""
    log: List[str] = []
    if not CRUMPLED_PAPER_FILE.is_file():
        log.append(f"  ⚠ нет файла {CRUMPLED_PAPER_FILE} — paper-SFX пропускаю")
        return log

    # Собираем sid-ы, после которых стоит «Бумажный шар»
    paper_bag_sids = [sid for sid, eff_id, _dur, _name in PLAN if eff_id == PAPER_BAG_EFFECT_ID]
    if not paper_bag_sids:
        log.append("  (в PLAN нет «Бумажного шара» — paper-SFX не нужен)")
        return log

    sids_in_order = [sid for sid, _ in SCENE_LAYOUT]
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    seg_to_sid = build_segment_to_sid_map()
    first_idx_for_sid: Dict[str, int] = {}
    for i, sid in enumerate(seg_to_sid):
        first_idx_for_sid.setdefault(sid, i)

    # Один материал-аудио на все вхождения crumpled paper (CapCut допускает).
    full_dur = mp3_duration_us(CRUMPLED_PAPER_FILE)
    use_dur = min(CRUMPLED_PAPER_LEN_US, full_dur)
    paper_mat = make_whoosh_audio_material(CRUMPLED_PAPER_FILE, full_dur)
    paper_mat["name"] = "Crumpled paper"
    paper_mat["type"] = "sound"
    paper_mat["effect_id"] = "7350583934167552513"
    draft["materials"]["audios"].append(paper_mat)

    # Получаем/создаём sfx-трек
    sfx_track = next(
        (t for t in draft["tracks"] if t["type"] == "audio" and t.get("name") == "sfx"),
        None,
    )
    if sfx_track is None:
        sfx_track = {
            "attribute": 0, "flag": 0, "id": gen_id_hex(),
            "is_default_name": True, "name": "sfx",
            "segments": [], "type": "audio",
        }
        draft["tracks"].append(sfx_track)

    placed = 0
    for sid in paper_bag_sids:
        try:
            next_sid = sids_in_order[sids_in_order.index(sid) + 1]
        except (ValueError, IndexError):
            log.append(f"  ⚠ sid {sid}: нет следующей сцены — paper-SFX пропускаю")
            continue
        next_seg_idx = first_idx_for_sid.get(next_sid)
        if next_seg_idx is None:
            log.append(f"  ⚠ sid {next_sid}: не нашёл сегмент — paper-SFX пропускаю")
            continue
        next_seg = main["segments"][next_seg_idx]
        next_start = int(next_seg["target_timerange"]["start"])
        start_us = max(0, next_start - CRUMPLED_PAPER_LEAD_US)
        sfx_track["segments"].append(
            make_sfx_segment(paper_mat["id"], start_us, use_dur, VOLUME_CRUMPLED_PAPER)
        )
        placed += 1
        log.append(
            f"  📄 {sid} → {next_sid}  Crumpled paper {start_us/1_000_000:.2f}s "
            f"dur={use_dur/1_000_000:.2f}s vol={VOLUME_CRUMPLED_PAPER}"
        )

    sfx_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])
    log.append(f"  paper-SFX: добавлено {placed} вхождений")
    return log


def apply_halftone_effect(draft: dict) -> List[str]:
    """Кладёт «Зеленые точки» на effect-трек на длительность аудио титула sentence_002."""
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


# ─────────────────────────────────────────────────────────────────────
# Применение к драфту
# ─────────────────────────────────────────────────────────────────────

def apply_transitions(draft: dict, library: dict) -> List[str]:
    log: List[str] = []
    last_idx = last_shot_index_per_sid()
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    sids_in_order = [sid for sid, _ in SCENE_LAYOUT]

    durs_by_sid = {sid: scene_duration_us(draft, sid) for sid, _ in SCENE_LAYOUT}

    for sid, eff_id, want_dur_s, label in PLAN:
        try:
            next_sid = sids_in_order[sids_in_order.index(sid) + 1]
        except (ValueError, IndexError):
            log.append(f"  ⚠ sid {sid}: нет следующей сцены, пропуск")
            continue
        prev_dur = durs_by_sid.get(sid, 0)
        next_dur = durs_by_sid.get(next_sid, 0)
        cap = int(min(prev_dur, next_dur) * MAX_TRANSITION_RATIO)
        want_us = int(want_dur_s * 1_000_000)
        dur_us = max(MIN_TRANSITION_US, min(want_us, cap))

        template = library["transitions"].get(eff_id)
        if template is None:
            log.append(f"  ⚠ effect_id {eff_id} ({label}) не нашёлся — пропуск")
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
    """«Финальный круг» на хвост сцены 019: эффект сидит на последних 1.5 с."""
    log: List[str] = []
    first_idx = first_shot_index_per_sid()
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    for sid, eff_id, label in EFFECT_PLAN:
        template = library["video_effects"].get(eff_id)
        if template is None:
            log.append(f"  ⚠ video_effect {eff_id} ({label}) не нашёлся — пропуск")
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
        # Для «Финального круга» — только последние 1.5 с сегмента,
        # как в CAPCUT.md §6.3.
        seg_dur = int(seg["target_timerange"]["duration"])
        tail_us = min(1_500_000, seg_dur)
        ve_mat["time_range"] = {
            "start": seg_dur - tail_us,
            "duration": tail_us,
        }
        log.append(f"  ★ {sid:<4} {label}  (сегмент #{seg_idx}, последние {tail_us/1_000_000:.1f}с)")
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
    draft["materials"].setdefault("audio_fades", []).append(fade_mat)
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

    trans_ids = {t["id"] for t in mats.get("transitions", [])}
    ve_ids = {e["id"] for e in mats.get("video_effects", [])}
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

    n_t = len(mats.get("transitions", []))
    n_v = len(mats.get("video_effects", []))
    n_f = len(mats.get("audio_fades", []))
    mats["transitions"] = []
    mats["video_effects"] = []
    mats["audio_fades"] = []

    # Снимаем effect-треки (halftone и аналоги), оставшиеся от прошлого прогона.
    n_eff_tracks = 0
    cleaned_tracks = []
    for t in draft["tracks"]:
        if t.get("type") == "effect" and t.get("name") == "halftone_green_dots":
            n_eff_tracks += 1
            continue
        cleaned_tracks.append(t)
    draft["tracks"] = cleaned_tracks

    # Снимаем SFX-трек (crumpled paper и т.п.) — пересоберётся в apply_crumpled_paper_sfx.
    sfx_tracks = [t for t in draft["tracks"]
                  if t["type"] == "audio" and t.get("name") == "sfx"]
    n_sfx_segs = 0
    sfx_audio_ids: set[str] = set()
    for tr in sfx_tracks:
        n_sfx_segs += len(tr.get("segments", []))
        for s in tr.get("segments", []):
            sfx_audio_ids.add(s.get("material_id", ""))
        draft["tracks"].remove(tr)
    # Удаляем материалы аудио, на которые ссылались только эти sfx-сегменты.
    if sfx_audio_ids:
        used_elsewhere: set[str] = set()
        for tr in draft["tracks"]:
            if tr["type"] != "audio":
                continue
            for s in tr.get("segments", []):
                used_elsewhere.add(s.get("material_id", ""))
        mats["audios"] = [a for a in mats.get("audios", [])
                          if a["id"] not in sfx_audio_ids or a["id"] in used_elsewhere]

    log.append(f"  снято: {n_t} transitions, {n_v} video_effects, {n_f} audio_fades, "
               f"{n_eff_tracks} effect-треков, {n_sfx_segs} sfx-сегментов")
    return log


# ─────────────────────────────────────────────────────────────────────
# Громкости
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
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Только показать план, не писать драфт.")
    args = p.parse_args()

    if not YAGA_FILE.is_file():
        print(f"Не нашёл драфт: {YAGA_FILE}")
        print("Сначала запусти: python build_oh_01.py")
        return 1
    if not EXAMPLE_FILE.is_file():
        print(f"Не нашёл драфт-эталон Персефоны: {EXAMPLE_FILE}")
        print("Для забора шаблонов переходов нужен живой драфт «Персефона и Аид».")
        return 1

    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой его полностью (включая трей) и перезапусти скрипт.")
        return 1

    print(f"Читаю Баба-Яга: {YAGA_FILE}")
    draft = json.load(open(YAGA_FILE, encoding="utf-8"))

    print(f"Читаю эталон шаблонов из Персефоны: {EXAMPLE_FILE}")
    example = json.load(open(EXAMPLE_FILE, encoding="utf-8"))
    library = build_template_library(example)
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
    print("План переходов:")
    log_tr = apply_transitions(draft, library)
    for line in log_tr:
        print(line)

    print()
    print("Видео-эффекты:")
    log_ve = apply_video_effects(draft, library)
    for line in log_ve:
        print(line)

    # Halftone «Зеленые точки» в этом мифе ОТКЛЮЧЁН: у Бабы-Яги нет
    # титульной строки «Баба-Яга. Миф за минуту.» — halftone канонически
    # кладётся поверх sentence_002-титула, а здесь sentence_002 — это
    # обычное сюжетное предложение. См. memory project_baba_yaga_no_title_line.

    print()
    print("Crumpled paper SFX (на каждом «Бумажном шаре»):")
    log_paper = apply_crumpled_paper_sfx(draft)
    for line in log_paper:
        print(line)

    print()
    print("Музыка:")
    log_mu = apply_music_fade(draft)
    for line in log_mu:
        print(line)

    if args.dry_run:
        print("\n--dry-run: драфт не трогаю.")
        return 0

    bkp = YAGA_FILE.with_suffix(".json.enrich-backup")
    shutil.copy2(YAGA_FILE, bkp)
    print(f"\nБэкап: {bkp.name}")

    json.dump(draft, open(YAGA_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = YAGA_DIR / tgt_name
        try:
            shutil.copy2(YAGA_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    mats = draft["materials"]
    print(f"\n✓ Готово. transitions={len(mats['transitions'])}, "
          f"video_effects={len(mats['video_effects'])}, "
          f"audio_fades={len(mats.get('audio_fades', []))}.")
    print("Открой CapCut → проект «Баба-Яга» → проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
