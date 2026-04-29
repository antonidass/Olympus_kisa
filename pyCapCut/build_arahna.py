"""
Сборка CapCut-драфта «Арахна» через pyCapCut.

Что делает скрипт:
  1. Берёт готовые mp4 из `content/Арахна/video/`
     и mp3 из `content/Арахна/voiceover/audio/approved_sentences/`.
  2. Читает длительность каждого mp3 (pymediainfo) и раскладывает сцены
     по таймлайну: один аудиосегмент = одно предложение, видеошоты
     внутри сцены делят её время поровну.
  3. Поверх — дорожка субтитров (`SCENE_TEXTS`), фоновая музыка и
     whoosh-SFX на slide-переходах.
  4. Сохраняет драфт в папку CapCut. Потом открываешь CapCut, выбираешь
     проект «Арахна» и рендеришь финал оттуда.

Использование:
    python build_arahna.py                                   # автоопределение папки CapCut
    python build_arahna.py --drafts "D:\\...\\com.lveditor.draft"
    python build_arahna.py --name "Арахна v2"
    python build_arahna.py --dry-run                         # только напечатать план таймлайна
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

from scene_structure_arahna import SCENES, Scene
from transitions import resolve as resolve_transition_name, is_long as is_long_transition


# ─────────────────────────────────────────────────────────────────────
# Константы проекта
# ─────────────────────────────────────────────────────────────────────

WIDTH = 1080
HEIGHT = 1920
FPS = 30

US = 1_000_000
GAP_US = int(2 / FPS * US)

DEFAULT_TRANSITION_US = int(0.60 * US)
LONG_TRANSITION_US = int(1.20 * US)
MAX_TRANSITION_RATIO = 0.45

DEFAULT_PROJECT_NAME = "Арахна"

VOICE_VOLUME = 1.0
ORIGINAL_CLIP_VOLUME = 0.5
MUSIC_VOLUME = 0.2
WHOOSH_VOLUME = 0.7


# ─────────────────────────────────────────────────────────────────────
# Пути к ассетам
# ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # …/BOGI AI/
ARAHNA_ROOT = PROJECT_ROOT / "content" / "Арахна"

SCENES_DIR = ARAHNA_ROOT / "video"
AUDIO_DIR = ARAHNA_ROOT / "voiceover" / "audio" / "approved_sentences"

# Общие SFX/музыка для всех мифов — в корневом assets/.
ASSETS_DIR = PROJECT_ROOT / "assets"
MUSIC_FILE = ASSETS_DIR / "music" / "Dorian_Concept_-_Hide_CS01_Version_(SkySound.cc).mp3"
WHOOSH_FILE = ASSETS_DIR / "audio" / "WHOOSH.mp3"


# ─────────────────────────────────────────────────────────────────────
# Длительность mp3 через pymediainfo (тот же источник правды, что у pyCapCut)
# ─────────────────────────────────────────────────────────────────────

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
    script.add_track(cc.TrackType.audio, track_name="voice")
    script.add_track(cc.TrackType.audio, track_name="music")
    script.add_track(cc.TrackType.audio, track_name="sfx")
    script.add_track(cc.TrackType.text,  track_name="subtitles")

    # ── Видеосегменты ──
    scene_last_shot = {}
    video_segments = []
    for ts in plan:
        n = len(ts.scene.videos)
        base = ts.duration_us // n
        remainder = ts.duration_us - base * n
        cur = ts.start_us
        for i, shot in enumerate(ts.scene.videos):
            shot_dur_us = base + (remainder if i == n - 1 else 0)
            file_path = str(SCENES_DIR / shot.file)
            kwargs = {}
            if shot.start_from > 0:
                kwargs["source_timerange"] = trange(
                    int(shot.start_from * US), shot_dur_us
                )
            vseg = cc.VideoSegment(
                file_path,
                trange(cur, shot_dur_us),
                volume=(ORIGINAL_CLIP_VOLUME if shot.muted else 1.0),
                **kwargs,
            )
            video_segments.append(vseg)
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
            print(f"  ⚠ переход {ts.scene.transition_after} не найден в TransitionType (сцена {ts.scene.sid})")
            continue
        dur_us = clamped_transition_duration_us(
            ts.scene.transition_after, ts.duration_us, plan[idx + 1].duration_us
        )
        transition_dur_by_sid[ts.scene.sid] = dur_us
        try:
            vseg.add_transition(resolved, duration=dur_us)
            print(f"  → {ts.scene.sid:<6} {ts.scene.transition_after:<14} {dur_us/US:.2f}s")
        except Exception as ex:
            print(f"  ⚠ переход {ts.scene.transition_after} на сцене {ts.scene.sid} не применился: {ex}")

    # Вставляем видео в трек
    for vseg in video_segments:
        script.add_segment(vseg, "main")

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
            music_seg.add_keyframe(plan[-1].start_us, MUSIC_VOLUME)
            music_seg.add_keyframe(total_us, 0.0)
        except Exception as ex:
            print(f"  ⚠ фейд музыки не применился: {ex}")
        script.add_segment(music_seg, "music")
    else:
        print(f"  ⚠ не нашёл {MUSIC_FILE}, музыку пропускаю")

    # ── Whoosh-SFX на slide-переходах ──
    whoosh_dur_us = int(0.6 * US)
    slide_aliases = {"сдвиг влево", "сдвиг вправо", "slide_left", "slide_right"}
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
    # Кладём ТОЛЬКО интро-сегмент сцены 01. Сценные субтитры (SCENE_TEXTS)
    # НЕ добавляем — на финальной сборке их всё равно перекрывает караоке
    # из karaoke_arahna.py, и в драфте они оседают «выключенными» мусорными
    # сегментами. Интро на subtitles-дорожке нужен только как шаблон, из
    # которого karaoke_*.py берёт font/style для своих текстовых сегментов.
    intro_ts = next((ts for ts in plan if ts.scene.sid == "01"), None)
    if intro_ts is not None:
        tseg = cc.TextSegment(
            "Арахна\nМиф за минуту",
            trange(intro_ts.start_us, intro_ts.audio_span_us),
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
    p = argparse.ArgumentParser(description="Собрать CapCut-драфт «Арахна» через pyCapCut.")
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
            "  python build_arahna.py --drafts "
            '"%LOCALAPPDATA%\\CapCut\\User Data\\Projects\\com.lveditor.draft"'
        )
        return 1

    try:
        draft_path = build_draft(drafts, args.name)
    except Exception as e:
        print(f"Ошибка сборки: {e}")
        raise

    print()
    print("✓ Драфт собран.")
    print(f"  Папка драфта: {draft_path}")
    print("  Открой CapCut → Drafts → выбери проект → правь / экспортируй.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
