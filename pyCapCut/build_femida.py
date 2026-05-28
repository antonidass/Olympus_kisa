"""
Сборка CapCut-драфта «Фемида» через pyCapCut.

23 предложения озвучки → 18 видеошотов в 18 таймлайн-сценах. Сцена 001
содержит хук + интро-титул. Пять сцен (001, 008, 013, 014, 018) покрывают
по два предложения каждая. CTA-аутро нет — финальный кадр заканчивается
по последней озвучке.

Использование:
    python build_femida.py                                    # автоопределение папки CapCut
    python build_femida.py --drafts "D:\\...\\com.lveditor.draft"
    python build_femida.py --name "Фемида v2"
    python build_femida.py --dry-run                          # только напечатать план таймлайна
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

from scene_structure_femida import SCENES, Scene
from transitions import resolve as resolve_transition_name, is_long as is_long_transition


# ─────────────────────────────────────────────────────────────────────
# Константы проекта
# ─────────────────────────────────────────────────────────────────────

WIDTH = 1080
HEIGHT = 1920
FPS = 60

US = 1_000_000
GAP_US = int(2 / FPS * US)

DEFAULT_TRANSITION_US = int(0.60 * US)
LONG_TRANSITION_US = int(1.20 * US)
MAX_TRANSITION_RATIO = 0.45

DEFAULT_PROJECT_NAME = "Фемида"

VOICE_VOLUME = 1.0
ORIGINAL_CLIP_VOLUME = 0.34   # эталон Тесея
MUSIC_VOLUME = 0.1348         # эталон Тесея
WHOOSH_VOLUME = 1.0           # эталон Тесея


# ─────────────────────────────────────────────────────────────────────
# Пути к ассетам
# ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # …/BOGI AI/
MYTH_ROOT = PROJECT_ROOT / "content" / "Фемида"

SCENES_DIR = MYTH_ROOT / "video"
AUDIO_DIR = MYTH_ROOT / "voiceover" / "audio" / "approved_sentences"
# Используем cutout-версии (.png) с прозрачным фоном вместо исходных .jpg
STICKERS_DIR = MYTH_ROOT / "images" / "stickers" / "cutout"

# Общие SFX/музыка для всех мифов — в корневом assets/.
ASSETS_DIR = PROJECT_ROOT / "assets"
MUSIC_FILE = ASSETS_DIR / "music" / "Dorian_Concept_-_Hide_CS01_Version_(SkySound.cc).mp3"
WHOOSH_FILE = ASSETS_DIR / "audio" / "WHOOSH.mp3"
CRUMPLED_FILE = ASSETS_DIR / "sfx" / "crumpled_paper.mp3"

CAPCUT_MUSIC_CACHE = Path(os.environ.get("LOCALAPPDATA", "")) / "CapCut" / "User Data" / "Cache" / "music"
PAC_FILE = CAPCUT_MUSIC_CACHE / "e7a6cec88ef0921b00a416c9bed90074.mp3"
MOUSE_CLICK_FILE = CAPCUT_MUSIC_CACHE / "d91f21d1c2b6ec21cf77a8d7185bdb47.mp3"
COIN_FILE = CAPCUT_MUSIC_CACHE / "f4d76f47351109ffb8b5068c2a5dbe71.mp3"

STICKER_SFX = {
    "pac": (PAC_FILE, 0.40, 1.0),
    "mouse": (MOUSE_CLICK_FILE, 0.183333, 0.75),
    "coin": (COIN_FILE, 0.783333, 0.28),
}

# Формат: (shot_file, sticker_file, x, y, scale, sfx_key, start_offset_s, dur_s)
# start_offset_s — сдвиг старта стикера относительно начала шота
# dur_s          — длительность показа стикера
# На сценах с двумя стикерами (013, 014, 018) они монтируются ПОСЛЕДОВАТЕЛЬНО
# встык: первый с offset≈0.2, второй с offset≈2.2 — по канону Дионис (см.
# stickers.md «монтируются последовательно встык, не наслаиваясь»).
STICKER_PLAN = [
    ("scene_02_v1.mp4", "scene_02_seer_mode_toggle_eye.png", 0.54, 0.39, 0.245, "coin", 0.25, 1.5),
    ("scene_06_v1.mp4", "scene_06_verified_rich_wax_seal.png", -0.54, 0.40, 0.245, "coin", 0.25, 1.5),
    ("scene_08_v1.mp4", "scene_08_auth_success_fabric_gold.png", 0.54, 0.38, 0.245, "mouse", 0.25, 1.5),
    ("scene_10_v1.mp4", "scene_10_fivestar_perjury_paid_review.png", -0.54, 0.40, 0.245, "coin", 0.25, 1.5),
    ("scene_11_v1.mp4", "scene_11_banned_hellas_ban_stamp.png", 0.0, 0.42, 0.265, "mouse", 0.25, 1.5),
    # scene_13 — два стикера встык (PLOT TWIST → TRUSTED PRIEST)
    ("scene_13_v1.mp4", "scene_13_plot_twist_inside_job.png", 0.54, 0.39, 0.245, "pac", 0.20, 1.8),
    ("scene_13_v1.mp4", "scene_13_trusted_priest_lol_rating.png", -0.54, 0.40, 0.245, "mouse", 2.20, 1.8),
    # scene_14 — два стикера встык (NOT RESPONDING → 404 NOT FOUND)
    ("scene_14_v1.mp4", "scene_14_status_not_responding_window.png", 0.54, 0.38, 0.245, "mouse", 0.20, 1.8),
    ("scene_14_v1.mp4", "scene_14_eyes_404_not_found.png", -0.54, 0.39, 0.245, "mouse", 2.20, 1.8),
    ("scene_15_v1.mp4", "scene_15_uninstalling_vision_exe_bar.png", 0.0, 0.42, 0.265, "pac", 0.25, 1.5),
    ("scene_16_v1.mp4", "scene_16_blind_mode_toggle_on.png", 0.54, 0.39, 0.245, "coin", 0.25, 1.5),
    # scene_18 — два стикера встык (AUDIO-ONLY → JUSTICE 2.0)
    ("scene_18_v1.mp4", "scene_18_audio_only_mode_headphones.png", -0.54, 0.39, 0.245, "pac", 0.20, 1.8),
    ("scene_18_v1.mp4", "scene_18_justice_2_verified_medal.png", 0.0, 0.42, 0.265, "coin", 2.20, 1.8),
]


# ─────────────────────────────────────────────────────────────────────
# Длительность mp3 через mutagen (точный счётчик MPEG-фреймов).
#
# Ранее использовался pymediainfo, но он возвращает длительность из
# заголовка контейнера и может на 5–15 мс превышать реальную длину
# декодированного аудио. CapCut при speed=1.0 пытается читать «за концом
# файла» → декодер повторяет хвост → робовойс на последнем слоге.
# mutagen считает MPEG-фреймы напрямую и `int()` дальше делает floor —
# гарантирует, что ни одно поле длительности не превысит реальный mp3.
#
# Дополнительно квантуем результат вниз до границы кадра проекта
# (60fps → 16 666.67 µs/кадр). Иначе CapCut при открытии драфта
# округляет target_timerange.duration аудио-сегмента вниз до целого
# числа кадров, а source_timerange.duration оставляет как есть, после
# чего src ≠ tgt → включается таймстретч → «звук как из ведра» /
# робовойс на половине предложений. После квантования src == tgt и
# никакого стретча.
#
# Тот же источник правды используется в диагностическом скрипте из
# CAPCUT.md §7.1.
# ─────────────────────────────────────────────────────────────────────

def floor_to_frame_us(us: int, fps: int = FPS) -> int:
    """Округлить длительность в µs вниз до границы кадра проекта."""
    frames = (us * fps) // US
    return (frames * US) // fps


def mp3_duration_us(path: Path) -> int:
    try:
        from mutagen.mp3 import MP3
    except ImportError as e:
        raise SystemExit(
            "Не установлен mutagen. Поставь зависимости:\n"
            "  pip install -r requirements.txt"
        ) from e
    raw_us = int(MP3(str(path)).info.length * 1_000_000)
    return floor_to_frame_us(raw_us)


# ─────────────────────────────────────────────────────────────────────
# Автоопределение пути к папке CapCut Drafts на Windows
# ─────────────────────────────────────────────────────────────────────

def autodetect_drafts_folder() -> Optional[Path]:
    candidates: List[Path] = []
    local = os.environ.get("LOCALAPPDATA")
    roaming = os.environ.get("APPDATA")
    if local:
        candidates.append(Path(local) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft")
    if roaming:
        candidates.append(Path(roaming) / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft")
        candidates.append(Path(roaming) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft")
    for c in candidates:
        if c.is_dir():
            return c
    return None


# ─────────────────────────────────────────────────────────────────────
# Планирование таймлайна
# ─────────────────────────────────────────────────────────────────────

class TimelineScene:
    def __init__(self, scene: Scene, start_us: int):
        self.scene = scene
        self.start_us = start_us
        self.audio_durs_us: List[int] = [
            mp3_duration_us(AUDIO_DIR / a) for a in scene.audios
        ]
        gaps = GAP_US * (len(self.audio_durs_us) - 1) if self.audio_durs_us else 0
        self.audio_span_us = sum(self.audio_durs_us) + gaps
        self.duration_us = self.audio_span_us + int(scene.trailing_pad * US)

    @property
    def end_us(self) -> int:
        return self.start_us + self.duration_us


def plan_timeline(scenes: List[Scene]) -> List[TimelineScene]:
    out: List[TimelineScene] = []
    cursor = 0
    for s in scenes:
        ts = TimelineScene(s, cursor)
        out.append(ts)
        cursor += ts.duration_us
    return out


def print_plan(plan: List[TimelineScene]) -> None:
    print(f"{'sid':<6} {'start':>7} {'dur':>7} {'audio':>7} {'trans':<14} text")
    print("-" * 72)
    for ts in plan:
        trans = ts.scene.transition_after or ""
        text_preview = (ts.scene.text or "").replace("\n", " ")[:30]
        start_s = ts.start_us / US
        dur_s = ts.duration_us / US
        audio_s = ts.audio_span_us / US
        print(
            f"{ts.scene.sid:<6} "
            f"{start_s:7.2f} {dur_s:7.2f} {audio_s:7.2f} "
            f"{trans:<14} {text_preview}"
        )
    if plan:
        total = plan[-1].end_us / US
        print("-" * 72)
        print(f"Всего: {total:.2f} сек ({total/60:.2f} мин)")


# ─────────────────────────────────────────────────────────────────────
# Переходы
# ─────────────────────────────────────────────────────────────────────

def base_transition_duration_us(name: Optional[str]) -> int:
    if name and is_long_transition(name):
        return LONG_TRANSITION_US
    return DEFAULT_TRANSITION_US


def clamped_transition_duration_us(name: Optional[str], prev_us: int, next_us: int) -> int:
    wanted = base_transition_duration_us(name)
    cap = int(min(prev_us, next_us) * MAX_TRANSITION_RATIO)
    return max(150_000, min(wanted, cap))


# ─────────────────────────────────────────────────────────────────────
# Основная сборка
# ─────────────────────────────────────────────────────────────────────

def build_draft(drafts_folder: Path, project_name: str) -> Path:
    try:
        import pycapcut as cc  # type: ignore
        from pycapcut import trange, TransitionType, TextStyle, ClipSettings  # type: ignore
    except ImportError as e:
        raise SystemExit(
            "Не установлен pycapcut. Поставь зависимости:\n"
            "  pip install -r requirements.txt"
        ) from e

    plan = plan_timeline(SCENES)

    print(f"CapCut drafts folder: {drafts_folder}")
    print(f"Создаём проект:       {project_name} ({WIDTH}x{HEIGHT}, {FPS} fps)")
    print_plan(plan)

    folder = cc.DraftFolder(str(drafts_folder))
    script = folder.create_draft(project_name, WIDTH, HEIGHT, fps=FPS, allow_replace=True)

    # Треки (порядок = слои снизу вверх)
    script.add_track(cc.TrackType.video, track_name="main")
    script.add_track(cc.TrackType.video, track_name="stickers")
    script.add_track(cc.TrackType.audio, track_name="voice")
    script.add_track(cc.TrackType.audio, track_name="music")
    script.add_track(cc.TrackType.audio, track_name="sfx")
    script.add_track(cc.TrackType.audio, track_name="sticker_sfx")
    script.add_track(cc.TrackType.text,  track_name="subtitles")

    # ── Видеосегменты ──
    scene_last_shot = {}
    shot_ranges: dict[str, tuple[int, int]] = {}
    video_segments = []
    for ts in plan:
        n = len(ts.scene.videos)
        base = ts.duration_us // n
        remainder = ts.duration_us - base * n
        cur = ts.start_us
        for i, shot in enumerate(ts.scene.videos):
            shot_dur_us = base + (remainder if i == n - 1 else 0)
            file_path = str(SCENES_DIR / shot.file)
            material = cc.VideoMaterial(file_path)
            kwargs = {}
            source_start_us = int(shot.start_from * US)
            source_available_us = max(1, material.duration - source_start_us)
            if shot.start_from > 0:
                source_dur_us = min(shot_dur_us, source_available_us)
                kwargs["source_timerange"] = trange(
                    source_start_us, source_dur_us
                )
                if shot_dur_us > source_dur_us:
                    kwargs["speed"] = source_dur_us / shot_dur_us
            elif shot_dur_us > source_available_us:
                kwargs["speed"] = source_available_us / shot_dur_us
            vseg = cc.VideoSegment(
                material,
                trange(cur, shot_dur_us),
                volume=(ORIGINAL_CLIP_VOLUME if shot.muted else 1.0),
                **kwargs,
            )
            video_segments.append(vseg)
            shot_ranges[shot.file] = (cur, shot_dur_us)
            if i == n - 1:
                scene_last_shot[ts.scene.sid] = vseg
            cur += shot_dur_us

    # Навешиваем переходы
    transition_dur_by_sid: dict = {}
    for idx, ts in enumerate(plan):
        if idx == len(plan) - 1:
            break
        if not ts.scene.transition_after:
            continue
        vseg = scene_last_shot.get(ts.scene.sid)
        if vseg is None:
            continue
        resolved = resolve_transition_name(ts.scene.transition_after, TransitionType)
        if resolved is None:
            print(f"  WARN переход {ts.scene.transition_after} не найден в TransitionType (сцена {ts.scene.sid})")
            continue
        dur_us = clamped_transition_duration_us(
            ts.scene.transition_after, ts.duration_us, plan[idx + 1].duration_us
        )
        transition_dur_by_sid[ts.scene.sid] = dur_us
        try:
            vseg.add_transition(resolved, duration=dur_us)
            print(f"  -> {ts.scene.sid:<6} {ts.scene.transition_after:<14} {dur_us/US:.2f}s")
        except Exception as ex:
            print(f"  WARN переход {ts.scene.transition_after} на сцене {ts.scene.sid} не применился: {ex}")

    # Вставляем видео в трек
    for vseg in video_segments:
        script.add_segment(vseg, "main")

    # ── Meme/image-overlay стикеры + короткий SFX на появление ──
    for entry in STICKER_PLAN:
        # Поддержка двух форматов: 6-элементный (старый) и 8-элементный
        # (новый, с явными offset/dur — для двух стикеров на одной сцене)
        if len(entry) == 8:
            shot_file, sticker_file, x, y, scale, sfx_key, offset_s, dur_s = entry
        else:
            shot_file, sticker_file, x, y, scale, sfx_key = entry
            offset_s, dur_s = 0.25, 1.5
        sticker_path = STICKERS_DIR / sticker_file
        if not sticker_path.is_file() or shot_file not in shot_ranges:
            print(f"  WARN стикер пропущен: {sticker_file} для {shot_file}")
            continue
        shot_start_us, shot_dur_us = shot_ranges[shot_file]
        # Если шот короче, чем offset+dur — сжимаем по реальной длине шота
        max_dur_us = max(int(0.5 * US), shot_dur_us - int(offset_s * US) - int(0.1 * US))
        dur_us = min(int(dur_s * US), max_dur_us)
        start_us = shot_start_us + int(offset_s * US)
        if start_us + dur_us > shot_start_us + shot_dur_us:
            dur_us = max(int(0.3 * US), shot_start_us + shot_dur_us - start_us - int(0.1 * US))
        sticker_seg = cc.VideoSegment(
            str(sticker_path),
            trange(start_us, dur_us),
            volume=0.0,
            clip_settings=ClipSettings(
                scale_x=scale,
                scale_y=scale,
                transform_x=x,
                transform_y=y,
            ),
        )
        script.add_segment(sticker_seg, "stickers")

        sfx_path, sfx_dur_s, sfx_volume = STICKER_SFX.get(sfx_key, (CRUMPLED_FILE, 0.40, 0.7))
        if not sfx_path.is_file():
            sfx_path, sfx_dur_s, sfx_volume = CRUMPLED_FILE, 0.40, 0.7
        if sfx_path.is_file():
            sfx_dur_us = min(int(sfx_dur_s * US), dur_us)
            script.add_segment(
                cc.AudioSegment(str(sfx_path), trange(start_us, sfx_dur_us), volume=sfx_volume),
                "sticker_sfx",
            )

    # ── Озвучка ──
    for ts in plan:
        local_us = 0
        for a_file, a_dur_us in zip(ts.scene.audios, ts.audio_durs_us):
            aseg = cc.AudioSegment(
                str(AUDIO_DIR / a_file),
                trange(ts.start_us + local_us, a_dur_us),
                volume=VOICE_VOLUME,
            )
            script.add_segment(aseg, "voice")
            local_us += a_dur_us + GAP_US

    # ── Фоновая музыка ──
    total_us = plan[-1].end_us
    if MUSIC_FILE.is_file():
        music_seg = cc.AudioSegment(
            str(MUSIC_FILE),
            trange(0, total_us),
            volume=MUSIC_VOLUME,
        )
        try:
            # фейд-аут 2.9 с в самом конце
            fade_us = int(2.9 * US)
            music_seg.add_keyframe(max(0, total_us - fade_us), MUSIC_VOLUME)
            music_seg.add_keyframe(total_us, 0.0)
        except Exception as ex:
            print(f"  WARN фейд музыки не применился: {ex}")
        script.add_segment(music_seg, "music")
    else:
        print(f"  WARN не нашёл {MUSIC_FILE}, музыку пропускаю")

    # ── Whoosh-SFX на slide-переходах (placeholder; enrich-скрипт расставит детально) ──
    whoosh_dur_us = int(0.6 * US)
    slide_aliases = {"сдвиг влево", "сдвиг вправо", "сдвиг вверх", "сдвиг вниз", "slide_left", "slide_right"}
    if WHOOSH_FILE.is_file():
        for ts in plan[:-1]:
            if ts.scene.transition_after in slide_aliases:
                whoosh_start_us = ts.end_us - transition_dur_by_sid.get(ts.scene.sid, DEFAULT_TRANSITION_US) // 2
                wseg = cc.AudioSegment(
                    str(WHOOSH_FILE),
                    trange(whoosh_start_us, whoosh_dur_us),
                    volume=WHOOSH_VOLUME,
                )
                script.add_segment(wseg, "sfx")

    # ── Субтитры ──
    # Только интро-сегмент sentence_002 как шаблон стиля для karaoke-скрипта.
    # Остальные SCENE_TEXTS не добавляем — их перекроет karaoke_dionysus.py.
    intro_ts = next((ts for ts in plan if ts.scene.sid == "001"), None)
    if intro_ts is not None and len(intro_ts.audio_durs_us) >= 2:
        intro_start_us = intro_ts.start_us + intro_ts.audio_durs_us[0] + GAP_US
        intro_dur_us = intro_ts.audio_durs_us[1]
        tseg = cc.TextSegment(
            "Феми́да\nМиф за минуту",
            trange(intro_start_us, intro_dur_us),
            style=TextStyle(
                size=14.0,
                color=(1.0, 1.0, 1.0),
                align=1,
                auto_wrapping=True,
                max_line_width=0.85,
            ),
            clip_settings=ClipSettings(
                transform_x=0.0,
                transform_y=0.0,
            ),
        )
        script.add_segment(tseg, "subtitles")

    script.save()

    draft_path = drafts_folder / project_name
    return draft_path


# ─────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description="Собрать CapCut-драфт «Фемида» через pyCapCut.")
    p.add_argument("--drafts", help="Путь к CapCut\\User Data\\Projects\\com.lveditor.draft. По умолчанию — автоопределение.")
    p.add_argument("--name", default=DEFAULT_PROJECT_NAME, help="Имя проекта в CapCut.")
    p.add_argument("--dry-run", action="store_true", help="Только напечатать план таймлайна, ничего не создавать.")
    args = p.parse_args()

    missing: List[Path] = []
    for s in SCENES:
        for a in s.audios:
            if not (AUDIO_DIR / a).is_file():
                missing.append(AUDIO_DIR / a)
        for v in s.videos:
            if not (SCENES_DIR / v.file).is_file():
                missing.append(SCENES_DIR / v.file)
    if missing:
        print("Не хватает ассетов:")
        for m in missing:
            print(f"  - {m}")
        return 1

    if args.dry_run:
        plan = plan_timeline(SCENES)
        print_plan(plan)
        return 0

    drafts = Path(args.drafts) if args.drafts else autodetect_drafts_folder()
    if drafts is None or not drafts.is_dir():
        print(
            "Не нашёл папку CapCut drafts. Укажи её вручную, например:\n"
            "  python build_femida.py --drafts "
            '"%LOCALAPPDATA%\\CapCut\\User Data\\Projects\\com.lveditor.draft"'
        )
        return 1

    try:
        draft_path = build_draft(drafts, args.name)
    except Exception as e:
        print(f"Ошибка сборки: {e}")
        raise

    print()
    print("OK Драфт собран.")
    print(f"  Папка драфта: {draft_path}")
    print("  Открой CapCut -> Drafts -> выбери проект -> правь / экспортируй.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
