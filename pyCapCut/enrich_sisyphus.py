"""
Обогащает уже собранный CapCut-драфт «Сизифов труд» переходами,
видео-эффектами и фейдом музыки.

Подход: берём готовые transition / video_effect / audio_fade материалы
прямо из соседнего драфта «Мидас и золотое прикосновение» (где
пользователь уже расставил их вручную) — это гарантирует, что:

  • все effect_id уже скачаны в CapCut Cache (path указывает туда),
  • схема полей строго соответствует тому, что CapCut ждёт.

Что делает:
  1. Читает draft_content.json «Сизифов труд» (создан build_sisyphus.py).
  2. Подтягивает библиотеку шаблонов transitions/video_effects/audio_fade
     из «Мидас и золотое прикосновение».
  3. По карте PLAN расставляет переходы между сценами Сизифа,
     соблюдая контекст мифа.
  4. Ставит «Ожоги на пленке» на интро-сцену 01 и «Финальный круг»
     на финальную сцену 27.
  5. Делает fade_out 4.2s на фоновой музыке.
  6. Сохраняет драфт + синхронизирует .bak / template-2.tmp.

Запуск (CapCut должен быть полностью закрыт, включая трей):
    python enrich_sisyphus.py
    python enrich_sisyphus.py --dry-run   # только показать план
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
SISYPHUS_DIR = DRAFTS / "Сизифов труд"
SISYPHUS_FILE = SISYPHUS_DIR / "draft_content.json"
MIDAS_FILE = DRAFTS / "Мидас и золотое прикосновение" / "draft_content.json"


# ─────────────────────────────────────────────────────────────────────
# Карта sid сцены → шотов в треке.
# Должна совпадать с тем, что строит build_sisyphus.py из SCENES.
# Здесь продублировано явно (а не через импорт), чтобы скрипт можно
# было запустить даже если scene_structure.py изменится.
# ─────────────────────────────────────────────────────────────────────

# (sid, число шотов)
SCENE_LAYOUT: List[Tuple[str, int]] = [
    ("01", 1), ("02", 2), ("03", 1), ("04-05", 2), ("06", 1), ("07", 1),
    ("08-09", 2), ("10", 1), ("11", 1), ("12", 1), ("13", 1), ("14-15", 2),
    ("16", 1), ("17", 1), ("18-19", 2), ("20", 1), ("21", 1), ("22", 1),
    ("23", 1), ("24", 1), ("25", 1), ("26", 1), ("27", 1),
]


# ─────────────────────────────────────────────────────────────────────
# План переходов под контекст мифа Сизифа.
#
# Формат: (sid_конец_сцены, effect_id, желаемая_длительность_секунды,
#          человекочитаемое_имя_для_лога).
#
# Логика подбора:
#   01→02  бодрый старт              — Глитч-вспышка
#   02→03  «первая жертва — Зевс»    — Зум с тряской 2 (драматизация)
#   03→04-05  ныряем в сцену с нимфой — Переход-зум
#   04-05→06  выбил источник воды    — Прыжок и отскок (энергия)
#   06→07  пришла Смерть              — 叠化 (мрачное растворение)
#   07→08-09  Танат явился            — Глитч-вспышка (короткий, сюрприз)
#   08-09→10  никто не умирает       — Поворот и изменение (мир сдвинулся)
#   10→11    мир в хаосе              — Свист (быстрый переброс)
#   11→12   продолжение перечня      — 叠化 (короткий)
#   12→13   «полный бардак»          — Глитч-вспышка (резко)
#   13→14-15 Арес влетает            — Растяжение влево (стремительно)
#   14-15→16 утащили в Аид           — Размытие (шар) — переход в подземный мир
#   16→17   мягкая хитрость           — 叠化
#   17→18-19 ныряем к Персефоне      — Переход-зум (другой effect_id)
#   18-19→20 напор речи              — Зум с тряской
#   20→21   резкая развязка          — Глитч-вспышка (короткий)
#   21→22   улёт во времени          — Свист
#   22→23   третий шанс не дали      — Полутоновая вспышка
#   23→24   разрыв судьбы → камень   — Разделение рваной бумагой
#   24→25   камень падает            — Прыжок и отскок (отскок)
#   25→26   повторение               — Зум с тряской 2
#   26→27   философский финал        — Рассеивание и зум
# ─────────────────────────────────────────────────────────────────────

PLAN: List[Tuple[str, str, float, str]] = [
    ("01",    "7234817586234397186", 0.87, "Глитч-вспышка"),
    ("02",    "7340177833508999681", 1.40, "Зум с тряской 2"),
    ("03",    "7464433696658001213", 1.67, "Переход-зум"),
    ("04-05", "7558885183924260113", 1.40, "Прыжок и отскок"),
    ("06",    "6724845717472416269", 1.07, "叠化 (Dissolve)"),
    ("07",    "7234817586234397186", 0.60, "Глитч-вспышка"),
    ("08-09", "7327547930728993282", 1.33, "Поворот и изменение"),
    ("10",    "6724239584663704071", 1.60, "Свист"),
    ("11",    "6724845717472416269", 0.60, "叠化 (Dissolve)"),
    ("12",    "7234817586234397186", 0.60, "Глитч-вспышка"),
    ("13",    "7620344224734629138", 1.40, "Растяжение влево"),
    ("14-15", "7159450506648097281", 1.33, "Размытие (шар)"),
    ("16",    "6724845717472416269", 1.07, "叠化 (Dissolve)"),
    ("17",    "7624223672038984968", 1.13, "Переход-зум II"),
    ("18-19", "7262258307128103425", 1.27, "Зум с тряской"),
    ("20",    "7234817586234397186", 0.60, "Глитч-вспышка"),
    ("21",    "6724239584663704071", 1.60, "Свист"),
    ("22",    "7609529907026119941", 1.27, "Полутоновая вспышка"),
    ("23",    "7604808025253137682", 2.07, "Разделение рваной бумагой"),
    ("24",    "7558885183924260113", 1.40, "Прыжок и отскок"),
    ("25",    "7340177833508999681", 1.40, "Зум с тряской 2"),
    ("26",    "7350583934167552513", 1.27, "Рассеивание и зум"),
    # 27 — финальная, без перехода
]


# ─────────────────────────────────────────────────────────────────────
# Видео-эффекты: какой эффект на какой sid сцены.
# Те же два, что у Мидаса: «Ожоги на пленке» — на старт, «Финальный
# круг» — на финал.
# ─────────────────────────────────────────────────────────────────────

EFFECT_PLAN: List[Tuple[str, str, str]] = [
    ("01", "7563294314475080965", "Ожоги на пленке"),
    ("27", "7613711779025358087", "Финальный круг"),
]


# Длительность fade_out на фоновой музыке (как у Мидаса).
MUSIC_FADE_OUT_US = 4_200_000

# Максимальная доля от меньшей соседней сцены, которую может занять
# переход. CapCut при превышении тихо обрежет — ставим запас.
MAX_TRANSITION_RATIO = 0.45
MIN_TRANSITION_US = 200_000

# Громкости — как у Мидаса (живой драфт):
#   voice = 1.0, video (исходный звук mp4) = 0.34, music = 0.30
# Для whoosh держим 0.7 (sfx).
VOLUME_VOICE = 1.0
VOLUME_VIDEO = 0.34
VOLUME_MUSIC = 0.1413  # = -17 dB
VOLUME_WHOOSH = 0.7

# Whoosh-SFX
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WHOOSH_FILE = PROJECT_ROOT / "assets" / "audio" / "WHOOSH.mp3"
WHOOSH_LEN_US = 600_000   # фиксированная длительность одного whoosh-сегмента


def mp3_duration_us(path: Path) -> int:
    """Длительность mp3 через pymediainfo — тот же источник правды,
    что использует pyCapCut, иначе CapCut будет ругаться на
    source_timerange > duration материала."""
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
    """Возвращает словари effect_id → шаблон (transition, video_effect)."""
    mats = midas_draft["materials"]
    transitions: Dict[str, dict] = {}
    for t in mats["transitions"]:
        transitions[str(t["effect_id"])] = t
    video_effects: Dict[str, dict] = {}
    for e in mats["video_effects"]:
        video_effects[str(e["effect_id"])] = e
    return {"transitions": transitions, "video_effects": video_effects}


def clone_transition(template: dict, duration_us: int) -> dict:
    """Глубокая копия с новым id и заданной длительностью.
    is_overlap, name, effect_id, path — всё остаётся от Мидаса."""
    m = copy.deepcopy(template)
    # CapCut использует hex без дефисов для transition.id
    m["id"] = gen_id_hex()
    m["duration"] = int(duration_us)
    return m


def clone_video_effect(template: dict) -> dict:
    m = copy.deepcopy(template)
    # video_effect.id у Мидаса — UUID в верхнем регистре. Сохраним стиль.
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
# Применение к драфту Сизифа
# ─────────────────────────────────────────────────────────────────────

def apply_transitions(draft: dict, library: dict) -> List[str]:
    """Возвращает список строк-логов (что куда повесили)."""
    log: List[str] = []
    last_idx = last_shot_index_per_sid()
    main = next(t for t in draft["tracks"] if t["type"] == "video" and t.get("name") == "main")
    sids_in_order = [sid for sid, _ in SCENE_LAYOUT]

    # Длительности всех сцен — для clamp.
    durs_by_sid = {sid: scene_duration_us(draft, sid) for sid, _ in SCENE_LAYOUT}

    for plan_idx, (sid, eff_id, want_dur_s, label) in enumerate(PLAN):
        # Длительность соседних сцен.
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
            f"  → {sid:<6} → {next_sid:<6}  {label:<28} {dur_us/1_000_000:.2f}s{clamped}"
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
        log.append(f"  ★ {sid:<6} {label}  (на сегмент #{seg_idx})")
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
    """Снимает все наши прошлые transitions / video_effects / audio_fades
    и удаляет sfx-track (с whoosh). Чтобы повторный запуск не дублировал."""
    log: List[str] = []
    mats = draft["materials"]

    # 1. Снимаем ссылки на transitions/video_effects из main
    trans_ids = {t["id"] for t in mats["transitions"]}
    ve_ids = {e["id"] for e in mats["video_effects"]}
    fade_ids = {f["id"] for f in mats["audio_fades"]}

    main = next((t for t in draft["tracks"]
                 if t["type"] == "video" and t.get("name") == "main"), None)
    if main:
        for seg in main["segments"]:
            seg["extra_material_refs"] = [
                r for r in seg.get("extra_material_refs", [])
                if r not in trans_ids and r not in ve_ids
            ]

    # 2. Снимаем ref'ы fade с music
    music = next((t for t in draft["tracks"]
                  if t["type"] == "audio" and t.get("name") == "music"), None)
    if music:
        for seg in music["segments"]:
            seg["extra_material_refs"] = [
                r for r in seg.get("extra_material_refs", [])
                if r not in fade_ids
            ]

    # 3. Удаляем сами материалы — они никому больше не нужны.
    n_t = len(mats["transitions"])
    n_v = len(mats["video_effects"])
    n_f = len(mats["audio_fades"])
    mats["transitions"] = []
    mats["video_effects"] = []
    mats["audio_fades"] = []

    # 4. Удаляем sfx-track и связанные whoosh-audios.
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
        # Снимаем audios, на которые ссылался только sfx
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
# Whoosh-SFX на каждом переходе
# ─────────────────────────────────────────────────────────────────────

def make_whoosh_audio_material(path: Path, full_dur_us: int) -> dict:
    """Audio material для WHOOSH.mp3. Один материал на все вставки."""
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
    """Кладёт whoosh-SFX в центр каждого перехода. Один материал на все
    вставки (≤ длительности самого mp3, иначе CapCut обрежет)."""
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

    # На каком сегменте стоит каждый переход — берём по PLAN.
    last_idx = last_shot_index_per_sid()
    main = next(t for t in draft["tracks"]
                if t["type"] == "video" and t.get("name") == "main")
    trans_ids_to_dur: Dict[str, int] = {}
    for tmat in draft["materials"]["transitions"]:
        trans_ids_to_dur[tmat["id"]] = tmat["duration"]

    placed = 0
    for sid, _eff_id, _want, label in PLAN:
        seg_idx = last_idx[sid]
        seg = main["segments"][seg_idx]
        # длительность перехода — берём из его материала, привязанного
        # к этому видеосегменту (могут быть и наши только что добавленные)
        my_trans_dur = 0
        for r in seg.get("extra_material_refs", []):
            if r in trans_ids_to_dur:
                my_trans_dur = trans_ids_to_dur[r]
                break
        if my_trans_dur == 0:
            continue
        end_us = seg["target_timerange"]["start"] + seg["target_timerange"]["duration"]
        # Whoosh центрируем точно на стыке сцен (= визуальный центр
        # overlap-перехода). Длительность перехода для расчёта не нужна.
        whoosh_start_us = max(0, end_us - use_dur // 2)
        wseg = make_whoosh_segment(whoosh_mat["id"], whoosh_start_us, use_dur)
        sfx_track["segments"].append(wseg)
        placed += 1

    sfx_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])
    log.append(f"  whoosh добавлен: {placed} вставок (vol={VOLUME_WHOOSH})")
    return log


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Только показать план, не писать драфт.")
    args = p.parse_args()

    if not SISYPHUS_FILE.is_file():
        print(f"Не нашёл драфт Сизифа: {SISYPHUS_FILE}")
        print("Сначала запусти: python build_sisyphus.py --no-transitions")
        return 1
    if not MIDAS_FILE.is_file():
        print(f"Не нашёл драфт Мидаса для забора шаблонов: {MIDAS_FILE}")
        return 1

    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой его полностью (включая трей) и запусти скрипт ещё раз.")
        return 1

    print(f"Читаю Сизифа: {SISYPHUS_FILE}")
    draft = json.load(open(SISYPHUS_FILE, encoding="utf-8"))

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

    # Бэкап.
    bkp = SISYPHUS_FILE.with_suffix(".json.enrich-backup")
    shutil.copy2(SISYPHUS_FILE, bkp)
    print(f"\nБэкап: {bkp.name}")

    # Сохраняем основной json + синхронизируем .bak / template-2.tmp,
    # иначе CapCut при открытии накатит "last known state" поверх наших правок.
    json.dump(draft, open(SISYPHUS_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = SISYPHUS_DIR / tgt_name
        try:
            shutil.copy2(SISYPHUS_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    mats = draft["materials"]
    sfx_count = sum(len(t.get("segments", [])) for t in draft["tracks"]
                    if t["type"] == "audio" and t.get("name") == "sfx")
    print(f"\n✓ Готово. transitions={len(mats['transitions'])}, "
          f"video_effects={len(mats['video_effects'])}, "
          f"audio_fades={len(mats['audio_fades'])}, "
          f"whoosh-сегментов={sfx_count}.")
    print("Открой CapCut → проект «Сизифов труд» → проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
