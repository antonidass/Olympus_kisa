"""
Подменяет переходы и whoosh-SFX в драфте «Цирцея и Одиссей» на
канон «Персей и Медуза».

Что трогает:
  - materials.transitions — полностью переписывает под Perseus-PLAN
  - main-сегменты — только их extra_material_refs (удаляет старые
    transition-ссылки, добавляет новые)
  - audio-трек `sfx` — удаляет старые whoosh-сегменты и whoosh-материал,
    пересоздаёт новый трек по правилам Perseus (на каждом whoosh-friendly
    переходе один свуш)

Что НЕ трогает:
  - voice, music, sticker_sfx, hermes_scroll_sfx — никакие другие
    аудио-треки
  - стикеры, halftone, hermes-карточку, karaoke, intro-текст
  - громкости видео-сегментов, geometry, fade_out музыки
  - materials.video_effects, audio_fades

Запуск (CapCut должен быть полностью закрыт):
    python patch_circe_perseus_transitions.py
    python patch_circe_perseus_transitions.py --dry-run
"""

from __future__ import annotations

import argparse
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
from typing import Dict, List, Tuple

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFTS = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
CIRCE_DIR = DRAFTS / "Цирцея и Одиссей"
CIRCE_FILE = CIRCE_DIR / "draft_content.json"
# Шаблоны переходов берём из Мидаса — там лежат все 9 нужных id (включая
# исторические запрещённые, на которых строится канон Персея).
MIDAS_FILE = DRAFTS / "Мидас и золотое прикосновение" / "draft_content.json"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WHOOSH_FILE = PROJECT_ROOT / "assets" / "audio" / "WHOOSH.mp3"
WHOOSH_LEN_US = 600_000
VOLUME_WHOOSH = 0.7

MAX_TRANSITION_RATIO = 0.45
MIN_TRANSITION_US = 200_000


# Раскладка сцен Цирцеи: 19 сцен по одному шоту.
SCENE_LAYOUT: List[Tuple[str, int]] = [(f"{i:03d}", 1) for i in range(1, 20)]


# Канон переходов Персея, сдвинутый на одну сцену влево, чтобы
# попасть в 19-сценный таймлайн Цирцеи:
#   Persei PLAN sid 002–019 → Circe PLAN sid 001–018.
#   Этим Hermes-сцена (Circe sid 008) получает «Свист», моли-deflect
#   (sid 010) — «Глитч-вспышку», меч (sid 011) — «Переход-зум».
#
# Запрещённые в новых роликах (Полутоновая вспышка, Пастельные блики,
# Зум с тряской 2) пользователь явно попросил, как в Перcее — оставляем.
PLAN: List[Tuple[str, str, float, str]] = [
    ("001", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("002", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("003", "7609529907026119941", 1.00, "Полутоновая вспышка"),
    ("004", "7340177833508999681", 1.10, "Зум с тряской 2"),
    ("005", "7234817586234397186", 0.70, "Глитч-вспышка"),
    ("006", "7550260993348177213", 1.00, "Пастельные блики"),
    ("007", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("008", "6724239584663704071", 0.90, "Свист"),
    ("009", "7550260993348177213", 1.00, "Пастельные блики"),
    ("010", "7234817586234397186", 0.70, "Глитч-вспышка"),
    ("011", "7464433696658001213", 1.00, "Переход-зум"),
    ("012", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("013", "7340177833508999681", 1.20, "Зум с тряской 2"),
    ("014", "7609529907026119941", 1.20, "Полутоновая вспышка"),
    ("015", "7234817586234397186", 0.70, "Глитч-вспышка"),
    ("016", "7159450506648097281", 1.00, "Размытие (шар)"),
    ("017", "7340177833508999681", 1.20, "Зум с тряской 2"),
    ("018", "7609529907026119941", 1.20, "Полутоновая вспышка"),
]

# Под какие переходы кладём WHOOSH.mp3 — те же правила, что в enrich_perseus.py.
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


def check_capcut_closed() -> bool:
    try:
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
        text = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        return "CapCut.exe" not in text and "JianyingPro" not in text
    except Exception:
        return True


def gen_id_hex() -> str:
    return uuid.uuid4().hex


def build_segment_to_sid_map() -> List[str]:
    out: List[str] = []
    for sid, n in SCENE_LAYOUT:
        out.extend([sid] * n)
    return out


def last_shot_index_per_sid() -> Dict[str, int]:
    out: Dict[str, int] = {}
    for i, sid in enumerate(build_segment_to_sid_map()):
        out[sid] = i
    return out


def scene_duration_us(draft: dict, sid: str) -> int:
    seg_to_sid = build_segment_to_sid_map()
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    total = 0
    for i, seg in enumerate(main["segments"]):
        if i < len(seg_to_sid) and seg_to_sid[i] == sid:
            total += seg["target_timerange"]["duration"]
    return total


def build_transition_library(midas: dict) -> Dict[str, dict]:
    return {str(t["effect_id"]): t for t in midas["materials"]["transitions"]}


def clone_transition(template: dict, duration_us: int) -> dict:
    m = copy.deepcopy(template)
    m["id"] = gen_id_hex()
    m["duration"] = int(duration_us)
    return m


def wipe_transitions_and_sfx(draft: dict) -> Tuple[int, int]:
    """Снимает старые transition-материалы и whoosh-трек, не трогая остального."""
    mats = draft["materials"]
    old_trans_ids = {t["id"] for t in mats["transitions"]}

    main = next((t for t in draft["tracks"]
                 if t["type"] == "video" and t.get("name") == "main"), None)
    if main:
        for seg in main["segments"]:
            seg["extra_material_refs"] = [
                r for r in seg.get("extra_material_refs", [])
                if r not in old_trans_ids
            ]

    n_t = len(mats["transitions"])
    mats["transitions"] = []

    # Снимаем whoosh-трек (имя `sfx`) и его материалы — но не sticker_sfx
    # и не hermes_scroll_sfx.
    sfx_tracks = [t for t in draft["tracks"]
                  if t["type"] == "audio" and t.get("name") == "sfx"]
    n_sfx = 0
    sfx_audio_ids: set = set()
    for tr in sfx_tracks:
        n_sfx += len(tr.get("segments", []))
        for s in tr.get("segments", []):
            sfx_audio_ids.add(s.get("material_id", ""))
        draft["tracks"].remove(tr)

    if sfx_audio_ids:
        # Удаляем только те audio-материалы, которые больше нигде не используются
        used_elsewhere: set = set()
        for tr in draft["tracks"]:
            if tr["type"] != "audio":
                continue
            for s in tr.get("segments", []):
                used_elsewhere.add(s.get("material_id", ""))
        mats["audios"] = [a for a in mats["audios"]
                          if a["id"] not in sfx_audio_ids or a["id"] in used_elsewhere]

    return n_t, n_sfx


def apply_transitions(draft: dict, library: Dict[str, dict]) -> List[str]:
    log: List[str] = []
    last_idx = last_shot_index_per_sid()
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    sids_in_order = [sid for sid, _ in SCENE_LAYOUT]
    durs_by_sid = {sid: scene_duration_us(draft, sid) for sid, _ in SCENE_LAYOUT}

    for sid, eff_id, want_dur_s, label in PLAN:
        try:
            next_sid = sids_in_order[sids_in_order.index(sid) + 1]
        except (ValueError, IndexError):
            log.append(f"  ⚠ sid {sid}: нет следующей сцены — пропуск")
            continue
        prev_dur = durs_by_sid.get(sid, 0)
        next_dur = durs_by_sid.get(next_sid, 0)
        cap = int(min(prev_dur, next_dur) * MAX_TRANSITION_RATIO)
        want_us = int(want_dur_s * 1_000_000)
        dur_us = max(MIN_TRANSITION_US, min(want_us, cap))

        template = library.get(eff_id)
        if template is None:
            log.append(f"  ⚠ {eff_id} ({label}) нет в Мидасе — пропуск")
            continue
        tr_mat = clone_transition(template, dur_us)
        draft["materials"]["transitions"].append(tr_mat)

        seg = main["segments"][last_idx[sid]]
        seg.setdefault("extra_material_refs", []).append(tr_mat["id"])

        clamped = " (cap'd)" if want_us > cap else ""
        log.append(f"  → {sid} → {next_sid}  {label:<24} {dur_us/1_000_000:.2f}s{clamped}")
    return log


def make_whoosh_audio_material(path: Path, full_dur_us: int) -> dict:
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
        "visible": True, "volume": VOLUME_WHOOSH,
    }


def mp3_full_duration_us(path: Path) -> int:
    from pymediainfo import MediaInfo
    mi = MediaInfo.parse(str(path))
    for t in mi.tracks:
        if t.track_type == "Audio" and t.duration is not None:
            return int(float(t.duration) * 1000)
    raise RuntimeError(f"audio not found in {path}")


def apply_whoosh(draft: dict) -> List[str]:
    log: List[str] = []
    if not WHOOSH_FILE.is_file():
        log.append(f"  ⚠ нет {WHOOSH_FILE}")
        return log

    full_dur = mp3_full_duration_us(WHOOSH_FILE)
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
    trans_dur_by_id = {tm["id"]: tm["duration"] for tm in draft["materials"]["transitions"]}
    trans_by_id = {tm["id"]: tm for tm in draft["materials"]["transitions"]}

    placed = 0
    for sid, eff_id, _want, _label in PLAN:
        if eff_id not in WHOOSH_TRANSITION_EFFECT_IDS:
            continue
        seg = main["segments"][last_idx[sid]]
        my_trans_dur = 0
        for r in seg.get("extra_material_refs", []):
            tmat = trans_by_id.get(r)
            if tmat and str(tmat.get("effect_id", "")) == eff_id:
                my_trans_dur = trans_dur_by_id[r]
                break
        if my_trans_dur == 0:
            continue
        end_us = seg["target_timerange"]["start"] + seg["target_timerange"]["duration"]
        whoosh_start_us = max(0, end_us - use_dur // 2)
        sfx_track["segments"].append(
            make_whoosh_segment(whoosh_mat["id"], whoosh_start_us, use_dur)
        )
        placed += 1

    sfx_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])
    log.append(f"  whoosh: {placed} вставок (vol={VOLUME_WHOOSH})")
    return log


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not CIRCE_FILE.is_file():
        print(f"Нет драфта: {CIRCE_FILE}")
        return 1
    if not MIDAS_FILE.is_file():
        print(f"Нет Мидаса для шаблонов: {MIDAS_FILE}")
        return 1
    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut открыт — закрой полностью.")
        return 1

    print(f"Читаю Цирцею: {CIRCE_FILE}")
    draft = json.load(open(CIRCE_FILE, encoding="utf-8"))
    print(f"Читаю шаблоны из Мидаса: {MIDAS_FILE}")
    midas = json.load(open(MIDAS_FILE, encoding="utf-8"))
    library = build_transition_library(midas)
    print(f"  templates: {len(library)} transitions")

    print()
    print("Чистка старых переходов и whoosh:")
    n_t, n_sfx = wipe_transitions_and_sfx(draft)
    print(f"  снято: {n_t} transitions, {n_sfx} whoosh-сегментов")

    print()
    print("Канон Персея:")
    for line in apply_transitions(draft, library):
        print(line)

    print()
    print("Whoosh-SFX:")
    for line in apply_whoosh(draft):
        print(line)

    if args.dry_run:
        print("\n--dry-run: не сохраняю.")
        return 0

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bkp = CIRCE_DIR / f"draft_content.json.perseus-transitions-{ts}"
    shutil.copy2(CIRCE_FILE, bkp)
    json.dump(draft, open(CIRCE_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt in ("template-2.tmp", "draft_content.json.bak"):
        try:
            shutil.copy2(CIRCE_FILE, CIRCE_DIR / tgt)
        except Exception:
            pass

    sfx_count = sum(len(t.get("segments", [])) for t in draft["tracks"]
                    if t["type"] == "audio" and t.get("name") == "sfx")
    print(f"\n✓ Готово. transitions={len(draft['materials']['transitions'])}, "
          f"whoosh-сегментов={sfx_count}.")
    print(f"Бэкап: {bkp.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
