"""
Обогащает уже собранный CapCut-драфт «Одиссей и Пенелопа» переходами,
видео-эффектами, фейдом музыки, громкостями. Структура — копия
enrich_persephone.py: тянем готовые transition / video_effect шаблоны
из живого драфта «Персефона и Аид» (там расставлены и закэшированы
все 18 канонических эффектов с актуальными resource_id).

24 сцены, 24 видеошота (все односегментные). Хук+интро живут в одной
сцене 001. CTA-аутро нет — Финальный круг ставится на sid="024".

Опционального зума 1.04 / Y=-77 НЕ применяю (см. CAPCUT.md §6.1: базовый
масштаб — 100%, зум — только по явной просьбе пользователя).

Запуск (CapCut должен быть закрыт):
    python enrich_odysseus.py
    python enrich_odysseus.py --dry-run
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
ODYSSEUS_DIR = DRAFTS / "Одиссей и Пенелопа"
ODYSSEUS_FILE = ODYSSEUS_DIR / "draft_content.json"
# Эталон Персефоны как источник всех 18 канонических transition-шаблонов
# и видео-эффекта «Финальный круг».
TEMPLATE_FILE = DRAFTS / "Персефона и Аид" / "draft_content.json"
# Запасной источник — Мидас (на случай, если у пользователя нет Персефоны).
FALLBACK_TEMPLATE_FILE = DRAFTS / "Мидас и золотое прикосновение" / "draft_content.json"


# ─────────────────────────────────────────────────────────────────────
# Карта sid → число шотов. У Одиссея все сцены односегментные.
# ─────────────────────────────────────────────────────────────────────

SCENE_LAYOUT: List[Tuple[str, int]] = [
    ("001", 1), ("002", 1), ("003", 1), ("004", 1), ("005", 1),
    ("006", 1), ("007", 1), ("008", 1), ("009", 1), ("010", 1),
    ("011", 1), ("012", 1), ("013", 1), ("014", 1), ("015", 1),
    ("016", 1), ("017", 1), ("018", 1), ("019", 1), ("020", 1),
    ("021", 1), ("022", 1), ("023", 1), ("024", 1),
]


# ─────────────────────────────────────────────────────────────────────
# План переходов под драматургию мифа.
#   001 хук+интро → 002      плавный диссолв (мягкое раскрытие)
#   002 ушёл на войну → 003  Зум с тряской 2 (тревога)
#   003 не вернулся → 004    диссолв (время идёт)
#   004 двадцать лет → 005   Резкий зум (вторжение женихов)
#   005 женихи → 006         диссолв
#   006 требуют → 007        Глитч-вспышка (хитрый разворот)
#   007 хитрость → 008       диссолв
#   008 обещание ткать → 009 Размытие шар (день/ночь магия)
#   009 днём ткёт → 010      Переход-зум (день → ночь)
#   010 ночью распускает → 011 Зум с тряской 2 (три года накопления)
#   011 три года → 012       Полутоновая вспышка (предательство)
#   012 служанка → 013       Глитч-вспышка (раскрытие тайны)
#   013 Одиссей плывёт → 014 диссолв (прибытие)
#   014 нищим → 015          диссолв (маскировка)
#   015 не узнали → 016      Переход-зум (состязание)
#   016 двенадцать колец → 017 Зум с тряской (старый лук)
#   017 лук → 018            Свист (стремительность)
#   018 женихи провалились → 019 Пастельные блики (звёздный момент)
#   019 нищий натянул → 020  Резкий зум (выстрел)
#   020 стрела → 021         Полутоновая вспышка (узнавание)
#   021 узнала → 022         диссолв (тест с кроватью)
#   022 кровать → 023        Зум с тряской 2 (раскрытие)
#   023 олива → 024          диссолв (объятие)
#   024 — финал, переход после не нужен
# ─────────────────────────────────────────────────────────────────────

PLAN: List[Tuple[str, str, float, str]] = [
    ("001", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("002", "7340177833508999681", 1.00, "Зум с тряской 2"),
    ("003", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("004", "7574908666210471221", 1.00, "Резкий зум"),
    ("005", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("006", "7234817586234397186", 0.70, "Глитч-вспышка"),
    ("007", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("008", "7159450506648097281", 1.20, "Размытие (шар)"),
    ("009", "7464433696658001213", 1.00, "Переход-зум"),
    ("010", "7340177833508999681", 1.00, "Зум с тряской 2"),
    ("011", "7609529907026119941", 1.20, "Полутоновая вспышка"),
    ("012", "7234817586234397186", 0.70, "Глитч-вспышка"),
    ("013", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("014", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("015", "7464433696658001213", 1.00, "Переход-зум"),
    ("016", "7262258307128103425", 1.00, "Зум с тряской"),
    ("017", "6724239584663704071", 0.90, "Свист"),
    ("018", "7550260993348177213", 1.10, "Пастельные блики"),
    ("019", "7574908666210471221", 1.00, "Резкий зум"),
    ("020", "7609529907026119941", 1.20, "Полутоновая вспышка"),
    ("021", "6724845717472416269", 0.80, "叠化 (Dissolve)"),
    ("022", "7340177833508999681", 1.20, "Зум с тряской 2"),
    ("023", "6724845717472416269", 1.00, "叠化 (Dissolve)"),
    # 024 — последняя
]

WHOOSH_TRANSITION_EFFECT_IDS = {
    "6724227717195108867", "6724227330190873100", "6724227090872275463",
    "7327547930728993282", "6724227965965435396",
}
WHOOSH_TRANSITION_LABELS = {"Влево", "Вправо", "Вверх", "Вниз", "Поворот и изменение"}


# ─────────────────────────────────────────────────────────────────────
# Видео-эффекты: «Финальный круг» на финал.
# ─────────────────────────────────────────────────────────────────────

EFFECT_PLAN: List[Tuple[str, str, str]] = [
    ("024", "7613711779025358087", "Финальный круг"),
]


# Громкости — по эталону Персефоны.
VOLUME_VOICE = 1.00
VOLUME_VIDEO = 0.34
VOLUME_MUSIC = 0.1348
VOLUME_WHOOSH = 0.70

MUSIC_FADE_OUT_SECONDS = 2.9
MUSIC_FADE_OUT_US = int(MUSIC_FADE_OUT_SECONDS * 1_000_000)

MAX_TRANSITION_RATIO = 0.45
MIN_TRANSITION_US = 200_000

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WHOOSH_FILE = PROJECT_ROOT / "assets" / "audio" / "WHOOSH.mp3"
WHOOSH_LEN_US = 600_000


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
# Библиотека шаблонов (из эталонного драфта)
# ─────────────────────────────────────────────────────────────────────

def build_template_library(*template_drafts: dict) -> dict:
    transitions: Dict[str, dict] = {}
    video_effects: Dict[str, dict] = {}
    for d in template_drafts:
        mats = d.get("materials", {})
        for t in mats.get("transitions", []):
            transitions.setdefault(str(t["effect_id"]), t)
        for e in mats.get("video_effects", []):
            video_effects.setdefault(str(e["effect_id"]), e)
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
# Применение
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
            log.append(f"  ⚠ sid {sid}: нет следующей сцены, пропускаю")
            continue
        prev_dur = durs_by_sid.get(sid, 0)
        next_dur = durs_by_sid.get(next_sid, 0)
        cap = int(min(prev_dur, next_dur) * MAX_TRANSITION_RATIO)
        want_us = int(want_dur_s * 1_000_000)
        dur_us = max(MIN_TRANSITION_US, min(want_us, cap))

        template = library["transitions"].get(eff_id)
        if template is None:
            log.append(f"  ⚠ effect_id {eff_id} ({label}) не нашёлся в библиотеке — пропуск")
            continue

        tr_mat = clone_transition(template, dur_us)
        draft["materials"]["transitions"].append(tr_mat)

        seg_idx = last_idx[sid]
        seg = main["segments"][seg_idx]
        refs = seg.setdefault("extra_material_refs", [])
        refs.append(tr_mat["id"])

        clamped = " (cap'd)" if want_us > cap else ""
        log.append(
            f"  → {sid:<4} → {next_sid:<4}  {label:<24} {dur_us/1_000_000:.2f}s{clamped}"
        )
    return log


def apply_video_effects(draft: dict, library: dict) -> List[str]:
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
    draft["materials"].setdefault("audio_fades", []).append(fade_mat)
    seg = music_track["segments"][0]
    refs = seg.setdefault("extra_material_refs", [])
    refs.append(fade_mat["id"])
    log.append(f"  ♪ музыка: fade_out {MUSIC_FADE_OUT_US/1_000_000:.1f}s")
    return log


# ─────────────────────────────────────────────────────────────────────
# Чистка прошлых правок
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

    if not ODYSSEUS_FILE.is_file():
        print(f"Не нашёл драфт Одиссея: {ODYSSEUS_FILE}")
        print("Сначала запусти: python build_odysseus.py")
        return 1

    template_drafts: List[dict] = []
    for f in (TEMPLATE_FILE, FALLBACK_TEMPLATE_FILE):
        if f.is_file():
            template_drafts.append(json.load(open(f, encoding="utf-8")))
            print(f"Источник шаблонов: {f}")
    if not template_drafts:
        print("Не нашёл ни Персефоны, ни Мидаса как источник шаблонов transitions/video_effects.")
        print(f"  ожидал: {TEMPLATE_FILE}")
        print(f"  или:    {FALLBACK_TEMPLATE_FILE}")
        return 1

    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой его полностью (включая трей) и запусти скрипт ещё раз.")
        return 1

    print(f"Читаю Одиссея: {ODYSSEUS_FILE}")
    draft = json.load(open(ODYSSEUS_FILE, encoding="utf-8"))

    library = build_template_library(*template_drafts)
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
    for line in apply_transitions(draft, library):
        print(line)

    print()
    print("Видео-эффекты:")
    for line in apply_video_effects(draft, library):
        print(line)

    print()
    print("Музыка:")
    for line in apply_music_fade(draft):
        print(line)

    if args.dry_run:
        print("\n--dry-run: драфт не трогаю.")
        return 0

    bkp = ODYSSEUS_FILE.with_suffix(".json.enrich-backup")
    shutil.copy2(ODYSSEUS_FILE, bkp)
    print(f"\nБэкап: {bkp.name}")

    json.dump(draft, open(ODYSSEUS_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = ODYSSEUS_DIR / tgt_name
        try:
            shutil.copy2(ODYSSEUS_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    mats = draft["materials"]
    print(f"\n✓ Готово. transitions={len(mats['transitions'])}, "
          f"video_effects={len(mats['video_effects'])}, "
          f"audio_fades={len(mats.get('audio_fades', []))}.")
    print("Открой CapCut → проект «Одиссей и Пенелопа» → проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
