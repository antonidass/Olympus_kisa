"""
Копирует переходы и связанные whoosh/swoosh-звуки из живого драфта
«Дионис и Ариадна» в «Одиссей и Пенелопа» — стык в стык, в той же
последовательности.

Что делает:
1. Снимает ВСЕ текущие переходы с main-сегментов Одиссея.
2. Прокладывает 23 стыка по плану Диониса (4 стыка — без перехода).
   Используются оригинальные effect_id / path / category_id, ничего
   не выдумываем.
3. Полностью пересобирает дорожку `sfx`: убирает старые 15 WHOOSH,
   подкладывает SFX ровно туда, где они стояли у Диониса (WHOOSH x 4,
   Swoosh x 1, с теми же громкостями и теми же оффсетами относительно
   стыка). Длительности переходов кэпуются до 45% от соседних сегментов,
   чтобы CapCut не ругался.

Запуск (CapCut закрыт):
    python pyCapCut/copy_dionysus_transitions_to_odysseus.py
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

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFTS = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
ODY_FILE = DRAFTS / "Одиссей и Пенелопа" / "draft_content.json"
DIO_FILE = DRAFTS / "Дионис и Ариадна" / "draft_content.json"

WHOOSH_FILE_LOCAL = (
    Path(__file__).resolve().parent.parent / "assets" / "audio" / "WHOOSH.mp3"
)
SWOOSH_CACHE = (
    LOCALAPPDATA / "CapCut" / "User Data" / "Cache" / "music"
    / "66e28892b747b1467c40e910b098a824.mp3"
)

MAX_TRANSITION_RATIO = 0.45
MIN_TRANSITION_US = 200_000


# План Диониса по стыкам.
# Поля: (effect_id, имя, длительность_us, имя_sfx, offset_to_stake_us, vol, sfx_dur_us)
# effect_id="" → без перехода (4 штуки).
# имя_sfx="" → без SFX на стыке.
NONE = ""
DIONYSUS_PLAN: list[tuple[str, str, int, str, int, float, int]] = [
    # T0   стык seg0→seg1
    ("6724227717195108867", "Влево",                  466_666, "WHOOSH",  -300_000, 0.7,   600_000),
    # T1
    ("6724226861666144779", "Втягивание",             933_333, "Swoosh",  -466_666, 0.505, 883_333),
    # T2
    ("7561440477262761277", "Взмах лапки",            466_666, "WHOOSH",  -150_000, 0.7,   600_000),
    # T3
    ("7298273321471185410", "Размытие с отдалением",  1_200_000, NONE,    0,        0.0,   0),
    # T4
    ("6724845717472416269", "叠化 (Dissolve)",         800_000,   NONE,    0,        0.0,   0),
    # T5
    ("7259950322024452610", "Вдох",                    800_000,   NONE,    0,        0.0,   0),
    # T6
    ("7234817586234397186", "Глитч-вспышка",           700_000,   NONE,    0,        0.0,   0),
    # T7  — без перехода
    (NONE,                  "БЕЗ ПЕРЕХОДА",            0,         NONE,    0,        0.0,   0),
    # T8
    ("6724845717472416269", "叠化 (Dissolve)",         800_000,   NONE,    0,        0.0,   0),
    # T9
    ("7340177833508999681", "Зум с тряской 2",          600_000,   "WHOOSH", -300_000, 0.7,   600_000),
    # T10 — без перехода
    (NONE,                  "БЕЗ ПЕРЕХОДА",            0,         NONE,    0,        0.0,   0),
    # T11
    ("7488094700159782145", "Зум с задержкой",          933_333,   NONE,    0,        0.0,   0),
    # T12
    ("7464433696658001213", "Переход-зум",              1_000_000, NONE,    0,        0.0,   0),
    # T13
    ("6724239584663704071", "Свист",                    900_000,   NONE,    0,        0.0,   0),
    # T14
    ("6724227090872275463", "Вверх",                    500_000,   "WHOOSH", -250_000, 0.7,   600_000),
    # T15 — без перехода
    (NONE,                  "БЕЗ ПЕРЕХОДА",            0,         NONE,    0,        0.0,   0),
    # T16
    ("7159450506648097281", "Размытие (шар)",           800_000,   NONE,    0,        0.0,   0),
    # T17
    ("7550260993348177213", "Пастельные блики",         800_000,   NONE,    0,        0.0,   0),
    # T18
    ("7340177833508999681", "Зум с тряской 2",          733_333,   NONE,    0,        0.0,   0),
    # T19
    ("6724845717472416269", "叠化 (Dissolve)",          733_333,   NONE,    0,        0.0,   0),
    # T20
    ("7159450506648097281", "Размытие (шар)",           766_666,   NONE,    0,        0.0,   0),
    # T21
    ("6724227330190873100", "Вниз",                     500_000,   "WHOOSH", -166_666, 0.7,   600_000),
    # T22
    ("6724226861666144779", "Втягивание",                500_000,   NONE,    0,        0.0,   0),
]


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
# Transitions
# ─────────────────────────────────────────────────────────────────────

def build_transition_library(dio_draft: dict) -> dict[str, dict]:
    """effect_id → шаблон transition-материала Диониса."""
    lib: dict[str, dict] = {}
    for t in dio_draft["materials"].get("transitions", []):
        lib[str(t["effect_id"])] = t
    return lib


def clear_existing_transitions(ody_draft: dict) -> int:
    """Удаляет все transition-материалы и ссылки на них из main-сегментов."""
    trans_ids = {t["id"] for t in ody_draft["materials"].get("transitions", [])}
    main = next(t for t in ody_draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    removed = 0
    for seg in main["segments"]:
        refs = seg.get("extra_material_refs", [])
        kept = [r for r in refs if r not in trans_ids]
        if len(kept) != len(refs):
            removed += len(refs) - len(kept)
            seg["extra_material_refs"] = kept
    ody_draft["materials"]["transitions"] = []
    return removed


def apply_transition_plan(ody_draft: dict, dio_lib: dict[str, dict]) -> list[str]:
    log: list[str] = []
    main = next(t for t in ody_draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    segs = main["segments"]
    n = len(segs)
    if n - 1 != len(DIONYSUS_PLAN):
        log.append(f"⚠ main сегментов={n}, стыков в плане={len(DIONYSUS_PLAN)} — могут не совпасть")

    durs = [int(s["target_timerange"]["duration"]) for s in segs]

    for stake_idx, (eid, name, want_dur, _sfx, _off, _vol, _sd) in enumerate(DIONYSUS_PLAN):
        if stake_idx >= n - 1:
            log.append(f"  T{stake_idx:>2}: пропуск — у Одиссея нет следующей сцены")
            continue
        if eid == NONE:
            log.append(f"  T{stake_idx:>2}: БЕЗ ПЕРЕХОДА")
            continue
        template = dio_lib.get(eid)
        if template is None:
            log.append(f"  T{stake_idx:>2}: ⚠ effect_id {eid} ({name}) нет в Дионис-материалах — пропуск")
            continue
        prev_dur, next_dur = durs[stake_idx], durs[stake_idx + 1]
        cap = int(min(prev_dur, next_dur) * MAX_TRANSITION_RATIO)
        dur_us = max(MIN_TRANSITION_US, min(want_dur, cap))
        clamped = " (cap'd)" if want_dur > cap else ""

        new_mat = copy.deepcopy(template)
        new_mat["id"] = gen_id_hex()
        new_mat["duration"] = int(dur_us)
        ody_draft["materials"]["transitions"].append(new_mat)

        seg = segs[stake_idx]
        seg.setdefault("extra_material_refs", []).append(new_mat["id"])

        log.append(
            f"  T{stake_idx:>2}: {name:<25} {dur_us/1e6:.3f}s{clamped}  → seg{stake_idx}"
        )
    return log


# ─────────────────────────────────────────────────────────────────────
# SFX track rebuild
# ─────────────────────────────────────────────────────────────────────

def find_or_create_sfx_material(ody_draft: dict, kind: str) -> str:
    """Возвращает material_id для WHOOSH или Swoosh, создавая при необходимости."""
    audios = ody_draft["materials"].setdefault("audios", [])
    if kind == "WHOOSH":
        for a in audios:
            if a.get("name") == "WHOOSH.mp3" and "assets/audio" in (a.get("path") or "").replace("\\", "/").lower():
                return a["id"]
        mid = gen_id_hex()
        mat = {
            "id": mid, "unique_id": "", "type": "extract_music",
            "name": "WHOOSH.mp3", "duration": 916666,
            "path": str(WHOOSH_FILE_LOCAL).replace("\\", "/"),
            "category_name": "local", "wave_points": [],
            "music_id": mid, "app_id": 0, "text_id": "", "tone_type": "",
            "source_platform": 0, "video_id": "", "effect_id": "",
            "resource_id": "", "third_resource_id": "", "category_id": "",
            "intensifies_path": "", "formula_id": "", "check_flag": 3,
            "team_id": "", "local_material_id": mid,
            "tone_speaker": "", "mock_tone_speaker": "",
            "tone_effect_id": "", "tone_effect_name": "", "tone_platform": "",
            "cloned_model_type": "", "tone_category_id": "", "tone_category_name": "",
            "tone_second_category_id": "", "tone_second_category_name": "",
            "tone_emotion_name_key": "", "tone_emotion_style": "", "tone_emotion_role": "",
            "tone_emotion_selection": "", "tone_emotion_scale": 0.0,
            "moyin_emotion": "", "request_id": "", "query": "", "search_id": "",
            "sound_separate_type": "", "is_text_edit_overdub": False,
            "is_ugc": False, "is_ai_clone_tone": False, "is_ai_clone_tone_post": False,
            "source_from": "", "copyright_limit_type": "none",
            "aigc_history_id": "", "aigc_item_id": "", "music_source": "",
            "pgc_id": "", "pgc_name": "",
            "similiar_music_info": {"original_song_id": "", "original_song_name": ""},
            "ai_music_type": 0, "ai_music_enter_from": "",
            "lyric_type": 0, "tts_task_id": "", "tts_generate_scene": "",
            "ai_music_generate_scene": 0,
            "tts_benefit_info": {
                "benefit_type": "none", "benefit_log_id": "",
                "benefit_log_extra": "", "benefit_amount": -1,
            },
        }
        audios.append(mat)
        return mid
    if kind == "Swoosh":
        mid = gen_id_upper()
        mat = {
            "id": mid, "unique_id": "", "type": "sound",
            "name": "Swoosh", "duration": 1_050_000,
            "path": str(SWOOSH_CACHE).replace("\\", "/"),
            "category_name": "Избранное", "wave_points": [],
            "music_id": "", "app_id": 1775, "text_id": "", "tone_type": "",
            "source_platform": 0, "video_id": "",
            "effect_id": "7517145081548326948",
            "resource_id": "", "third_resource_id": "",
            "category_id": "-100", "intensifies_path": "",
            "formula_id": "", "check_flag": 1,
            "team_id": "", "local_material_id": "",
            "tone_speaker": "", "mock_tone_speaker": "",
            "tone_effect_id": "", "tone_effect_name": "", "tone_platform": "",
            "cloned_model_type": "", "tone_category_id": "", "tone_category_name": "",
            "tone_second_category_id": "", "tone_second_category_name": "",
            "tone_emotion_name_key": "", "tone_emotion_style": "", "tone_emotion_role": "",
            "tone_emotion_selection": "", "tone_emotion_scale": 0.0,
            "moyin_emotion": "", "request_id": "20260516SWOOSHODY",
            "query": "", "search_id": "", "sound_separate_type": "",
            "is_text_edit_overdub": False, "is_ugc": False,
            "is_ai_clone_tone": False, "is_ai_clone_tone_post": False,
            "source_from": "", "copyright_limit_type": "none",
            "aigc_history_id": "", "aigc_item_id": "", "music_source": "",
            "pgc_id": "", "pgc_name": "",
            "similiar_music_info": {"original_song_id": "", "original_song_name": ""},
            "ai_music_type": 0, "ai_music_enter_from": "",
            "lyric_type": 0, "tts_task_id": "", "tts_generate_scene": "",
            "ai_music_generate_scene": 0,
            "tts_benefit_info": {
                "benefit_type": "none", "benefit_log_id": "",
                "benefit_log_extra": "", "benefit_amount": -1,
            },
        }
        audios.append(mat)
        return mid
    raise ValueError(f"Unknown SFX kind: {kind}")


def make_sfx_supports(ody_draft: dict) -> tuple[str, str, str, str]:
    speed = {"id": gen_id_hex(), "type": "speed", "mode": 0, "speed": 1.0, "curve_speed": None}
    ph = {
        "id": gen_id_hex(), "type": "placeholder_info", "meta_type": "none",
        "res_path": "", "res_text": "", "error_path": "", "error_text": "",
    }
    sm = {"id": gen_id_hex(), "type": "none", "audio_channel_mapping": 0, "is_config_open": False}
    vs = {
        "id": gen_id_hex(), "type": "vocal_separation", "choice": 0,
        "removed_sounds": [], "time_range": None, "production_path": "",
        "final_algorithm": "", "enter_from": "",
    }
    ody_draft["materials"].setdefault("speeds", []).append(speed)
    ody_draft["materials"].setdefault("placeholder_infos", []).append(ph)
    ody_draft["materials"].setdefault("sound_channel_mappings", []).append(sm)
    ody_draft["materials"].setdefault("vocal_separations", []).append(vs)
    return speed["id"], ph["id"], sm["id"], vs["id"]


def make_sfx_segment(material_id: str, start_us: int, duration_us: int,
                     volume: float, supports: tuple[str, str, str, str]) -> dict:
    return {
        "id": gen_id_hex(),
        "source_timerange": {"start": 0, "duration": int(duration_us)},
        "target_timerange": {"start": int(start_us), "duration": int(duration_us)},
        "render_timerange": {"start": 0, "duration": 0},
        "desc": "", "state": 0, "speed": 1.0, "is_loop": False,
        "is_tone_modify": False, "reverse": False, "intensifies_audio": False,
        "cartoon": False, "volume": float(volume), "last_nonzero_volume": 1.0,
        "clip": None, "uniform_scale": None,
        "material_id": material_id,
        "extra_material_refs": list(supports),
        "render_index": 0, "keyframe_refs": [],
        "enable_lut": False, "enable_adjust": False, "enable_hsl": False,
        "visible": True, "group_id": "",
        "enable_color_curves": True, "enable_hsl_curves": True,
        "track_render_index": 0, "hdr_settings": None,
        "enable_color_wheels": True, "track_attribute": 0,
        "is_placeholder": False, "template_id": "",
        "enable_smart_color_adjust": False, "template_scene": "default",
        "common_keyframes": [], "caption_info": None,
        "responsive_layout": {
            "enable": False, "target_follow": "",
            "size_layout": 0, "horizontal_pos_layout": 0, "vertical_pos_layout": 0,
        },
        "enable_color_match_adjust": False, "enable_color_correct_adjust": False,
        "enable_adjust_mask": False, "raw_segment_id": "",
        "lyric_keyframes": None, "enable_video_mask": True,
        "digital_human_template_group_id": "",
        "color_correct_alg_result": "", "source": "segmentsourcenormal",
        "enable_mask_stroke": False, "enable_mask_shadow": False,
        "enable_color_adjust_pro": False,
    }


def rebuild_sfx_track(ody_draft: dict) -> list[str]:
    """Полностью пересобираем sfx-трек: убираем все старые сегменты,
    добавляем новые согласно DIONYSUS_PLAN."""
    log: list[str] = []
    sfx_track = next(
        (t for t in ody_draft["tracks"] if t.get("type") == "audio" and t.get("name") == "sfx"),
        None,
    )
    if not sfx_track:
        sfx_track = {
            "id": gen_id_hex(), "type": "audio", "segments": [],
            "flag": 0, "attribute": 0, "name": "sfx", "is_default_name": False,
        }
        ody_draft["tracks"].append(sfx_track)
        log.append("  · создал новый трек sfx")

    sfx_track["segments"] = []

    main = next(t for t in ody_draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    segs = main["segments"]
    # Стык T_i = граница между seg_i и seg_(i+1) = старт seg_(i+1)
    stake_starts = [int(s["target_timerange"]["start"]) for s in segs]

    mid_whoosh: str | None = None
    mid_swoosh: str | None = None

    for stake_idx, (_eid, _name, _dur, sfx_kind, offset_us, vol, sfx_dur_us) in enumerate(DIONYSUS_PLAN):
        if sfx_kind == NONE:
            continue
        if stake_idx + 1 >= len(stake_starts):
            continue
        boundary_us = stake_starts[stake_idx + 1]
        start_us = max(0, boundary_us + offset_us)
        if sfx_kind == "WHOOSH":
            if mid_whoosh is None:
                mid_whoosh = find_or_create_sfx_material(ody_draft, "WHOOSH")
            mid = mid_whoosh
        else:
            if mid_swoosh is None:
                mid_swoosh = find_or_create_sfx_material(ody_draft, "Swoosh")
            mid = mid_swoosh
        supports = make_sfx_supports(ody_draft)
        seg = make_sfx_segment(mid, start_us, sfx_dur_us, vol, supports)
        sfx_track["segments"].append(seg)
        log.append(
            f"  T{stake_idx:>2}: {sfx_kind:<6} t={start_us/1e6:6.2f}s "
            f"dur={sfx_dur_us/1e6:.3f}s vol={vol:.3f}"
        )

    return log


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    if not ODY_FILE.exists():
        print(f"Не нашёл драфт Одиссея: {ODY_FILE}")
        return 1
    if not DIO_FILE.exists():
        print(f"Не нашёл драфт Диониса: {DIO_FILE}")
        return 1
    if not check_capcut_closed():
        print("⛔ CapCut запущен — закрой его.")
        return 1
    if not WHOOSH_FILE_LOCAL.exists():
        print(f"⛔ нет файла WHOOSH: {WHOOSH_FILE_LOCAL}")
        return 1
    if not SWOOSH_CACHE.exists():
        print(f"⛔ нет файла Swoosh: {SWOOSH_CACHE} — открой Дионис в CapCut один раз")
        return 1

    with open(ODY_FILE, "r", encoding="utf-8") as f:
        ody = json.load(f)
    with open(DIO_FILE, "r", encoding="utf-8") as f:
        dio = json.load(f)

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ODY_FILE.parent / f"draft_content.json.transitions-from-dionysus-{ts}"
    shutil.copy(ODY_FILE, backup)
    print(f"Бекап: {backup.name}")

    print()
    print("Снимаю старые переходы…")
    removed = clear_existing_transitions(ody)
    print(f"  · удалено transition-ref из сегментов: {removed}")

    print()
    print("Раскладываю план Диониса…")
    dio_lib = build_transition_library(dio)
    for line in apply_transition_plan(ody, dio_lib):
        print(line)

    print()
    print("Пересобираю sfx-дорожку под переходы…")
    for line in rebuild_sfx_track(ody):
        print(line)

    with open(ODY_FILE, "w", encoding="utf-8") as f:
        json.dump(ody, f, ensure_ascii=False)

    print()
    print("✓ готово. Открой CapCut и проверь стыки 1-23 — должны идти как у Диониса.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
