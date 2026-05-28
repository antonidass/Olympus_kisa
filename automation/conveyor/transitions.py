"""Чтение и запись переходов между сценами в живой CapCut-драфт.

Используется редактором переходов (шаг 2 конвейера). Логика повторяет
канон enrich_<myth>.py, но работает по произвольному плану из UI:

  • каталог канон-переходов (CAPCUT.md § 4.1, без запрещённых);
  • библиотека шаблонов — клонируем материал перехода из любого
    существующего драфта (там ассеты CapCut-online уже скачаны);
  • запись плана в draft_content.json: чистим все переходы и наши
    локальные SFX (WHOOSH.mp3 / crumpled_paper.mp3), затем раскладываем
    заново. Ручные онлайн-SFX (Swoosh/Swish) НЕ трогаем.

CapCut на момент записи должен быть закрыт (иначе он перезапишет файл).
"""

from __future__ import annotations

import copy
import os
import subprocess
import uuid
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent.parent  # …/BOGI AI/
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFTS_DIR = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"

WHOOSH_FILE = ROOT / "assets" / "audio" / "WHOOSH.mp3"
CRUMPLED_FILE = ROOT / "assets" / "sfx" / "crumpled_paper.mp3"

VOLUME_WHOOSH = 0.70
VOLUME_CRUMPLED = 1.00
WHOOSH_LEN_US = 600_000
CRUMPLED_LEN_US = 866_667
CRUMPLED_LEAD_US = 333_334  # crumpled заканчивается за 0.333 с до стыка

# Максимум длительности перехода. CapCut на материале перехода не хранит
# min/max, но реальный потолок ползунка — 2.0 с (самый длинный переход,
# встреченный во всех драфтах канала, — «Разделение рваной бумагой» ≈ 2.07 с).
TRANSITION_MIN_US = 200_000
TRANSITION_MAX_US = 2_000_000

# Имена локальных SFX-материалов, которыми управляет редактор. Сегменты с
# этими материалами на sfx-дорожке мы пересобираем; всё прочее (онлайн
# Swoosh/Swish, добавленные руками) оставляем как есть.
MANAGED_SFX_NAMES = {WHOOSH_FILE.name, CRUMPLED_FILE.name}

# ─────────────────────────────────────────────────────────────────────
# Каталог канон-переходов. family определяет авто-SFX:
#   directional / swish → WHOOSH.mp3 (0.70)
#   paper               → crumpled_paper.mp3 (1.00)
#   zoom                → Swoosh (онлайн, ставится вручную — не пишем)
#   texture             → без SFX (свой звук либо без звука)
# Запрещённые каноном (Полутоновая вспышка, Пастельные блики, Зум с
# тряской 1/2) в каталог не входят.
# ─────────────────────────────────────────────────────────────────────

TRANSITION_CATALOG: List[dict] = [
    {"effect_id": None, "name": "Cut (без перехода)", "family": "cut", "default_dur_us": 0, "sfx": None},
    # Зум-семейство (Swoosh вручную)
    {"effect_id": "7574908666210471221", "name": "Резкий зум", "family": "zoom", "default_dur_us": 966_666, "sfx": "swoosh"},
    {"effect_id": "6724226861666144779", "name": "Втягивание", "family": "zoom", "default_dur_us": 933_333, "sfx": "swoosh"},
    {"effect_id": "6724226338418332167", "name": "Вытягивание", "family": "zoom", "default_dur_us": 500_000, "sfx": "swoosh"},
    # Направленные (WHOOSH.mp3 0.70)
    {"effect_id": "6724227717195108867", "name": "Влево", "family": "directional", "default_dur_us": 800_000, "sfx": "whoosh"},
    {"effect_id": "6724227599616184836", "name": "Справа", "family": "directional", "default_dur_us": 466_666, "sfx": "whoosh"},
    {"effect_id": "6724227090872275463", "name": "Вверх", "family": "directional", "default_dur_us": 500_000, "sfx": "whoosh"},
    {"effect_id": "6724227330190873100", "name": "Вниз", "family": "directional", "default_dur_us": 500_000, "sfx": "whoosh"},
    # Взмах (WHOOSH.mp3 0.70)
    {"effect_id": "7561440477262761277", "name": "Взмах лапки", "family": "swish", "default_dur_us": 566_666, "sfx": "whoosh"},
    # Бумага (crumpled 1.00)
    {"effect_id": "7249296835204878850", "name": "Бумажный шар", "family": "paper", "default_dur_us": 666_666, "sfx": "crumpled"},
    # Фактурные / без авто-SFX
    {"effect_id": "6724239584663704071", "name": "Свист", "family": "texture", "default_dur_us": 900_000, "sfx": None},
    {"effect_id": "7159450506648097281", "name": "Размытие (шар)", "family": "texture", "default_dur_us": 1_200_000, "sfx": None},
    {"effect_id": "7259950322024452610", "name": "Вдох", "family": "texture", "default_dur_us": 333_333, "sfx": None},
    {"effect_id": "6724845717472416269", "name": "Диссолв", "family": "texture", "default_dur_us": 800_000, "sfx": None},
]

CATALOG_BY_ID: Dict[str, dict] = {e["effect_id"]: e for e in TRANSITION_CATALOG if e["effect_id"]}


# ─────────────────────────────────────────────────────────────────────
# Вспомогательное
# ─────────────────────────────────────────────────────────────────────

def _gen_id_hex() -> str:
    return uuid.uuid4().hex


def check_capcut_closed() -> bool:
    """True, если процесс CapCut/JianyingPro не запущен."""
    try:
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
        text = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        if "CapCut.exe" in text or "JianyingPro" in text:
            return False
    except Exception:
        pass
    return True


def _mp3_duration_us(path: Path) -> int:
    from pymediainfo import MediaInfo
    mi = MediaInfo.parse(str(path))
    for t in mi.tracks:
        if t.track_type == "Audio" and t.duration is not None:
            return int(float(t.duration) * 1000)
    raise RuntimeError(f"Нет audio-дорожки в {path}")


def _main_track(draft: dict) -> Optional[dict]:
    return next(
        (t for t in draft.get("tracks", [])
         if t.get("type") == "video" and t.get("name") == "main"),
        None,
    )


def build_template_library(donor_dir: Optional[Path] = None) -> Dict[str, dict]:
    """Карта {effect_id: материал-перехода} из существующих драфтов.

    Сканируем все драфты CapCut и берём первый встреченный материал на
    каждый effect_id — ассеты там уже скачаны, клонировать безопасно.
    """
    import json
    library: Dict[str, dict] = {}
    if not DRAFTS_DIR.is_dir():
        return library
    for f in DRAFTS_DIR.glob("*/draft_content.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for t in d.get("materials", {}).get("transitions", []):
            eid = str(t.get("effect_id") or "")
            if eid and eid not in library:
                library[eid] = t
    return library


def _clone_transition(template: dict, duration_us: int) -> dict:
    m = copy.deepcopy(template)
    m["id"] = _gen_id_hex()
    m["duration"] = int(duration_us)
    return m


def _make_local_audio_material(path: Path, full_dur_us: int) -> dict:
    mid = _gen_id_hex()
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


def _make_audio_segment(material_id: str, start_us: int, dur_us: int, volume: float) -> dict:
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
        "id": _gen_id_hex(),
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


# ─────────────────────────────────────────────────────────────────────
# Чтение текущего плана
# ─────────────────────────────────────────────────────────────────────

def read_transitions(draft: dict) -> List[dict]:
    """Текущие стыки главной дорожки: from/to/effect_id/label/duration."""
    trans_by_id = {
        t.get("id"): t
        for t in draft.get("materials", {}).get("transitions", [])
        if t.get("id")
    }
    main = _main_track(draft)
    segments = main.get("segments", []) if main else []

    out: List[dict] = []
    for i in range(max(0, len(segments) - 1)):
        seg = segments[i]
        tr = None
        for ref in seg.get("extra_material_refs", []):
            if ref in trans_by_id:
                tr = trans_by_id[ref]
                break
        if tr is not None:
            eid = str(tr.get("effect_id") or "")
            out.append({
                "from": f"{i + 1:02d}", "to": f"{i + 2:02d}",
                "effect_id": eid or None,
                "label": tr.get("name") or "Переход",
                "duration": round(int(tr.get("duration", 0)) / 1_000_000, 2),
            })
        else:
            out.append({
                "from": f"{i + 1:02d}", "to": f"{i + 2:02d}",
                "effect_id": None, "label": "Cut", "duration": None,
            })
    return out


# ─────────────────────────────────────────────────────────────────────
# Запись плана
# ─────────────────────────────────────────────────────────────────────

def _wipe_managed(draft: dict) -> None:
    """Снимает ВСЕ переходы и наши локальные SFX-сегменты (WHOOSH/crumpled)."""
    mats = draft.setdefault("materials", {})
    trans_ids = {t["id"] for t in mats.get("transitions", []) if t.get("id")}
    # Снять ссылки на переходы со всех сегментов всех дорожек.
    for tr in draft.get("tracks", []):
        for seg in tr.get("segments", []):
            refs = seg.get("extra_material_refs")
            if refs:
                seg["extra_material_refs"] = [r for r in refs if r not in trans_ids]
    mats["transitions"] = []

    # Снять наши локальные SFX-сегменты с sfx-дорожки (по имени материала).
    audios_by_id = {a.get("id"): a for a in mats.get("audios", [])}
    managed_aud_ids = {
        aid for aid, a in audios_by_id.items()
        if (a.get("name") in MANAGED_SFX_NAMES)
    }
    for tr in draft.get("tracks", []):
        if tr.get("type") == "audio" and tr.get("name") == "sfx":
            tr["segments"] = [
                s for s in tr.get("segments", [])
                if s.get("material_id") not in managed_aud_ids
            ]
    # Удалить осиротевшие локальные SFX-материалы.
    still_used = {
        s.get("material_id")
        for tr in draft.get("tracks", [])
        for s in tr.get("segments", [])
    }
    mats["audios"] = [
        a for a in mats.get("audios", [])
        if a.get("id") not in managed_aud_ids or a.get("id") in still_used
    ]


def _sfx_track(draft: dict) -> dict:
    tr = next(
        (t for t in draft.get("tracks", [])
         if t.get("type") == "audio" and t.get("name") == "sfx"),
        None,
    )
    if tr is None:
        tr = {
            "attribute": 0, "flag": 0, "id": _gen_id_hex(),
            "is_default_name": True, "name": "sfx",
            "segments": [], "type": "audio",
        }
        draft["tracks"].append(tr)
    return tr


def apply_transition_plan(draft: dict, plan: List[dict],
                          library: Dict[str, dict]) -> List[str]:
    """Раскладывает переходы и локальные SFX по плану.

    plan — полный желаемый список стыков: [{index, effect_id|None,
    duration (сек, опц.)}], index 0-based (стык между seg[index] и
    seg[index+1]). Возвращает лог-строки.
    """
    log: List[str] = []
    mats = draft.setdefault("materials", {})
    main = _main_track(draft)
    if main is None:
        return ["⚠ нет main-дорожки — нечего раскладывать"]
    segments = main["segments"]
    n_bound = max(0, len(segments) - 1)

    _wipe_managed(draft)
    mats.setdefault("transitions", [])
    mats.setdefault("audios", [])

    # Локальные SFX-материалы создаём по одному и переиспользуем.
    whoosh_mat = None
    crumpled_mat = None
    whoosh_dur = crumpled_dur = 0
    if WHOOSH_FILE.is_file():
        wfull = _mp3_duration_us(WHOOSH_FILE)
        whoosh_dur = min(WHOOSH_LEN_US, wfull)
        whoosh_mat = _make_local_audio_material(WHOOSH_FILE, wfull)
    if CRUMPLED_FILE.is_file():
        cfull = _mp3_duration_us(CRUMPLED_FILE)
        crumpled_dur = min(CRUMPLED_LEN_US, cfull)
        crumpled_mat = _make_local_audio_material(CRUMPLED_FILE, cfull)

    sfx = _sfx_track(draft)
    whoosh_used = crumpled_used = False
    n_tr = n_whoosh = n_crumpled = 0

    for entry in plan:
        idx = int(entry.get("index", -1))
        if idx < 0 or idx >= n_bound:
            continue
        eid = entry.get("effect_id")
        if not eid:
            continue  # Cut — перехода нет
        eid = str(eid)
        cat = CATALOG_BY_ID.get(eid)
        if cat is None:
            log.append(f"  ⚠ стык {idx + 1:02d}: effect_id {eid} вне каталога — пропуск")
            continue
        template = library.get(eid)
        if template is None:
            log.append(f"  ⚠ стык {idx + 1:02d}: нет шаблона {cat['name']} в драфтах — пропуск")
            continue

        dur_s = entry.get("duration")
        dur_us = int(round(float(dur_s) * 1_000_000)) if dur_s else cat["default_dur_us"]
        dur_us = max(TRANSITION_MIN_US, min(TRANSITION_MAX_US, dur_us))

        tr_mat = _clone_transition(template, dur_us)
        mats["transitions"].append(tr_mat)
        seg = segments[idx]
        seg.setdefault("extra_material_refs", []).append(tr_mat["id"])
        n_tr += 1

        # Авто-SFX (только локальные семейства).
        end_us = seg["target_timerange"]["start"] + seg["target_timerange"]["duration"]
        if cat["sfx"] == "whoosh" and whoosh_mat is not None:
            start_us = max(0, end_us - whoosh_dur // 2)
            sfx["segments"].append(
                _make_audio_segment(whoosh_mat["id"], start_us, whoosh_dur, VOLUME_WHOOSH))
            whoosh_used = True
            n_whoosh += 1
        elif cat["sfx"] == "crumpled" and crumpled_mat is not None:
            start_us = max(0, end_us - CRUMPLED_LEAD_US)
            sfx["segments"].append(
                _make_audio_segment(crumpled_mat["id"], start_us, crumpled_dur, VOLUME_CRUMPLED))
            crumpled_used = True
            n_crumpled += 1

        log.append(f"  → стык {idx + 1:02d}→{idx + 2:02d}  {cat['name']}  {dur_us / 1e6:.2f}s")

    if whoosh_used:
        mats["audios"].append(whoosh_mat)
    if crumpled_used:
        mats["audios"].append(crumpled_mat)
    sfx["segments"].sort(key=lambda s: s["target_timerange"]["start"])

    log.append(f"  итого: {n_tr} переходов, {n_whoosh} WHOOSH, {n_crumpled} crumpled")
    return log
