"""
Добавляет Whoosh/Swoosh SFX на переходы Каллисто и Аркаса по правилу
CAPCUT.md §3.3.1 + §4.1:

  Swoosh (зум-семейство + Свист) — на sid:
    003 Зум с тряской 2  (003 → 004)
    006 Переход-зум      (006 → 007)
    010 Зум с тряской 2  (010 → 011)
    014 Переход-зум      (014 → 015)
    015 Зум с тряской    (015 → 016)
    017 Зум с тряской 2  (017 → 018)
    018 Переход-зум      (018 → 019)

  Swish (направленные + Растяжение + Взмах лапки) — на sid:
    012 Взмах лапки      (012 → 013)

Параметры (по эталону Дионис):
  - Swoosh: cache d=66e28892b747b1467c40e910b098a824.mp3, dur=1.050s, effect_id=7517145081548326948
  - Swish:  cache d=d2059d83f11fa732e2c6599c9fccf301.mp3, dur=0.417s, effect_id=6993230936993204226

Размещение: SFX-сегмент стартует за ~0.2с до визуального стыка сцен (т.е.
target_timerange.start = (start следующей сцены) − 200_000 us). Длительность
равна полной длительности файла. Громкость 1.0.

CapCut должен быть полностью закрыт (включая трей).
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


LOCALAPPDATA = Path(os.environ["LOCALAPPDATA"])
KALLISTO_DIR = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft" / "Каллисто и Аркас"
DRAFT_FILE = KALLISTO_DIR / "draft_content.json"
CAPCUT_CACHE_MUSIC = LOCALAPPDATA / "CapCut" / "User Data" / "Cache" / "music"

# ─────────────────────────────────────────────────────────────────────
# Шаблоны Swoosh / Swish — пути и effect_id из CapCut Cache
# ─────────────────────────────────────────────────────────────────────

SWOOSH_HASH = "66e28892b747b1467c40e910b098a824.mp3"
SWOOSH_EFFECT_ID = "7517145081548326948"
SWOOSH_DUR_US = 1_050_000
SWOOSH_FILE = CAPCUT_CACHE_MUSIC / SWOOSH_HASH

SWISH_HASH = "d2059d83f11fa732e2c6599c9fccf301.mp3"
SWISH_EFFECT_ID = "6993230936993204226"
SWISH_DUR_US = 416_666
SWISH_FILE = CAPCUT_CACHE_MUSIC / SWISH_HASH

# За сколько микросекунд до стыка стартовать SFX
LEAD_US = 200_000
VOLUME = 1.0

# SCENE_LAYOUT для индексирования (совпадает со scene_structure_kallisto)
SCENE_LAYOUT = [
    ("001", 1), ("002", 1), ("003", 1), ("004", 1), ("005", 1),
    ("006", 2), ("007", 1), ("008", 1), ("009", 1), ("010", 1),
    ("011", 1), ("012", 1), ("013", 1), ("014", 1), ("015", 1),
    ("016", 1), ("017", 1), ("018", 1), ("019", 2), ("020", 1),
    ("021", 1), ("022", 1),
]

# Какой sid → какой SFX
# (По PLAN из enrich_kallisto.py + правилу CAPCUT.md §4.1)
SWOOSH_SIDS = ["003", "006", "010", "014", "015", "017", "018"]
SWISH_SIDS  = ["012"]


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


def make_whoosh_material(name: str, mp3_path: Path, effect_id: str, full_dur_us: int) -> dict:
    """Шаблон Swish/Swoosh-материала — точно как в Дионис/Персефона драфтах."""
    return {
        "id": gen_id_upper(),
        "unique_id": "",
        "type": "sound",
        "name": name,
        "duration": int(full_dur_us),
        "path": str(mp3_path).replace("\\", "/"),
        "category_name": "Избранное",
        "wave_points": [],
        "music_id": "",
        "app_id": 1775,
        "text_id": "",
        "tone_type": "",
        "source_platform": 0,
        "video_id": "",
        "effect_id": effect_id,
        "resource_id": "",
        "third_resource_id": "",
        "category_id": "-100",
        "intensifies_path": "",
        "formula_id": "",
        "check_flag": 1,
        "team_id": "",
        "local_material_id": "",
        "tone_speaker": "", "mock_tone_speaker": "",
        "tone_effect_id": "", "tone_effect_name": "", "tone_platform": "",
        "cloned_model_type": "",
        "tone_category_id": "", "tone_category_name": "",
        "tone_second_category_id": "", "tone_second_category_name": "",
        "tone_emotion_name_key": "", "tone_emotion_style": "",
        "tone_emotion_role": "", "tone_emotion_selection": "",
        "tone_emotion_scale": 0.0, "moyin_emotion": "",
        "request_id": "20260521WHOOSH",
        "query": "", "search_id": "",
        "sound_separate_type": "",
        "is_text_edit_overdub": False, "is_ugc": False,
        "is_ai_clone_tone": False, "is_ai_clone_tone_post": False,
        "source_from": "", "copyright_limit_type": "none",
        "aigc_history_id": "", "aigc_item_id": "",
        "music_source": "",
        "pgc_id": "", "pgc_name": "",
        "similiar_music_info": {"original_song_id": "", "original_song_name": ""},
        "ai_music_type": 0, "ai_music_enter_from": "",
        "lyric_type": 0,
        "tts_task_id": "", "tts_generate_scene": "",
        "ai_music_generate_scene": 0,
        "tts_benefit_info": {
            "benefit_type": "none", "benefit_log_id": "",
            "benefit_log_extra": "", "benefit_amount": -1,
        },
    }


def make_sfx_segment(material_id: str, start_us: int, dur_us: int) -> dict:
    """Аудио-сегмент SFX на трек sfx."""
    return {
        "id": gen_id_upper(),
        "source_timerange": {"start": 0, "duration": int(dur_us)},
        "target_timerange": {"start": int(start_us), "duration": int(dur_us)},
        "render_timerange": {"start": 0, "duration": 0},
        "desc": "", "state": 0, "speed": 1.0,
        "is_loop": False, "is_tone_modify": False, "reverse": False,
        "intensifies_audio": False, "cartoon": False,
        "volume": VOLUME, "last_nonzero_volume": VOLUME,
        "clip": None, "uniform_scale": None,
        "material_id": material_id,
        "extra_material_refs": [],
        "render_index": 0,
        "keyframe_refs": [],
        "enable_lut": False, "enable_adjust": False, "enable_hsl": False,
        "visible": True, "group_id": "",
        "enable_color_curves": True, "enable_hsl_curves": True,
        "track_render_index": 0, "hdr_settings": None,
        "enable_color_wheels": True,
        "track_attribute": 0,
        "is_placeholder": False, "template_id": "",
        "enable_smart_color_adjust": False, "template_scene": "default",
        "common_keyframes": [], "caption_info": None,
        "responsive_layout": {
            "enable": False, "target_follow": "", "size_layout": 0,
            "horizontal_pos_layout": 0, "vertical_pos_layout": 0,
        },
        "enable_color_match_adjust": False,
        "enable_video_mask": True,
        "enable_color_correct_adjust": False,
        "enable_color_adjust_pro": False,
        "color_correct_alg_result": "",
        "digital_human_template_group_id": "",
        "enable_mask_shadow": False, "enable_mask_stroke": False,
        "lyric_keyframes": None,
        "raw_segment_id": "",
        "stretch_alg": "",
    }


def first_shot_index_per_sid(scene_layout) -> dict[str, int]:
    out: dict[str, int] = {}
    idx = 0
    for sid, n in scene_layout:
        out[sid] = idx
        idx += n
    return out


def main() -> int:
    if not DRAFT_FILE.is_file():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1
    if not check_capcut_closed():
        print("WARN CapCut запущен. Закрой полностью (включая трей).")
        return 1
    if not SWOOSH_FILE.is_file():
        print(f"WARN: Swoosh mp3 не в кэше: {SWOOSH_FILE}")
        return 1
    if not SWISH_FILE.is_file():
        print(f"WARN: Swish mp3 не в кэше: {SWISH_FILE}")
        return 1

    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = KALLISTO_DIR / f"draft_content.json.whoosh-sfx-backup-{ts}"
    shutil.copy2(DRAFT_FILE, backup)
    print(f"Бэкап: {backup.name}\n")

    main_track = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    first_idx = first_shot_index_per_sid(SCENE_LAYOUT)
    sids_in_order = [sid for sid, _ in SCENE_LAYOUT]

    # 1. Снимаем старые Swish/Swoosh сегменты с трека sfx (идемпотентность)
    audios_by_id = {a["id"]: a for a in draft["materials"].get("audios", [])}
    sfx_track = next((t for t in draft["tracks"] if t["type"] == "audio" and t.get("name") == "sfx"), None)
    if sfx_track is None:
        sfx_track = {
            "attribute": 0, "flag": 0, "id": gen_id_hex(),
            "is_default_name": True, "name": "sfx",
            "segments": [], "type": "audio",
        }
        draft["tracks"].append(sfx_track)

    removed = 0
    new_segs = []
    for s in sfx_track["segments"]:
        mat = audios_by_id.get(s.get("material_id"), {})
        if mat.get("name") in ("Swish", "Swoosh"):
            removed += 1
            continue
        new_segs.append(s)
    sfx_track["segments"] = new_segs
    if removed:
        print(f"Снято старых Swish/Swoosh сегментов: {removed}")

    # 2. Чистим старые материалы Swish/Swoosh, если на них больше никто не ссылается
    used_mat_ids: set[str] = set()
    for tr in draft["tracks"]:
        if tr["type"] != "audio":
            continue
        for s in tr.get("segments", []):
            used_mat_ids.add(s.get("material_id", ""))
    draft["materials"]["audios"] = [
        a for a in draft["materials"].get("audios", [])
        if not (a.get("name") in ("Swish", "Swoosh") and a["id"] not in used_mat_ids)
    ]

    # 3. Создаём по одному материалу Swish и Swoosh (CapCut допускает шаринг между сегментами)
    swoosh_mat = make_whoosh_material("Swoosh", SWOOSH_FILE, SWOOSH_EFFECT_ID, SWOOSH_DUR_US)
    swish_mat = make_whoosh_material("Swish", SWISH_FILE, SWISH_EFFECT_ID, SWISH_DUR_US)
    draft["materials"]["audios"].append(swoosh_mat)
    draft["materials"]["audios"].append(swish_mat)

    # 4. Расставляем сегменты
    placed_swoosh = 0
    placed_swish = 0
    for sid_list, mat, dur, label in [
        (SWOOSH_SIDS, swoosh_mat, SWOOSH_DUR_US, "Swoosh"),
        (SWISH_SIDS,  swish_mat,  SWISH_DUR_US,  "Swish"),
    ]:
        for sid in sid_list:
            try:
                next_sid = sids_in_order[sids_in_order.index(sid) + 1]
            except (ValueError, IndexError):
                print(f"  WARN sid {sid}: нет next_sid, пропуск")
                continue
            next_idx = first_idx.get(next_sid)
            if next_idx is None:
                print(f"  WARN sid {next_sid} не в main, пропуск")
                continue
            next_seg = main_track["segments"][next_idx]
            boundary_us = int(next_seg["target_timerange"]["start"])
            start_us = max(0, boundary_us - LEAD_US)
            seg = make_sfx_segment(mat["id"], start_us, dur)
            sfx_track["segments"].append(seg)
            if label == "Swoosh":
                placed_swoosh += 1
            else:
                placed_swish += 1
            print(f"  {label:<6}  sid {sid} -> {next_sid}: SFX {start_us/1e6:.3f}–{(start_us+dur)/1e6:.3f}s "
                  f"(стык на {boundary_us/1e6:.3f}s, lead -{LEAD_US/1e6:.2f}s, vol={VOLUME})")

    # Сортируем сегменты на дорожке по target_timerange.start
    sfx_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])

    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        try:
            shutil.copy2(DRAFT_FILE, KALLISTO_DIR / tgt_name)
        except Exception:
            pass

    print(f"\nOK: добавлено {placed_swoosh} Swoosh + {placed_swish} Swish SFX-сегментов.")
    print("Открой CapCut → проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
