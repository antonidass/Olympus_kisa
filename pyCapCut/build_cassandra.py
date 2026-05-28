"""
Сборка CapCut-драфта «Аполлон и Кассандра» через pyCapCut.

16 предложений озвучки → 20 видеошотов в 15 таймлайн-сценах. Сцена 001
содержит хук (sent_001) + интро-титул (sent_002). CTA-аутро нет —
финальный кадр заканчивается по последней озвучке. Стикеры в первый
проход не раскладываются (пользователь добавит руками).

Использование:
    python build_cassandra.py
    python build_cassandra.py --drafts "D:\\...\\com.lveditor.draft"
    python build_cassandra.py --name "Аполлон и Кассандра v2"
    python build_cassandra.py --dry-run
"""

from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path
from typing import List, Optional

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from scene_structure_cassandra import SCENES, Scene


# ─────────────────────────────────────────────────────────────────────
# Константы проекта
# ─────────────────────────────────────────────────────────────────────

WIDTH = 1080
HEIGHT = 1920
FPS = 60

US = 1_000_000
GAP_US = int(2 / FPS * US)

DEFAULT_PROJECT_NAME = "Аполлон и Кассандра"

VOICE_VOLUME = 1.0
ORIGINAL_CLIP_VOLUME = 0.34
MUSIC_VOLUME = 0.1348


# ─────────────────────────────────────────────────────────────────────
# Пути к ассетам
# ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MYTH_ROOT = PROJECT_ROOT / "content" / "Аполлон и Кассандра"

SCENES_DIR = MYTH_ROOT / "video"
AUDIO_DIR = MYTH_ROOT / "voiceover" / "audio" / "approved_sentences"

ASSETS_DIR = PROJECT_ROOT / "assets"
MUSIC_FILE = ASSETS_DIR / "music" / "Dorian_Concept_-_Hide_CS01_Version_(SkySound.cc).mp3"


# ─────────────────────────────────────────────────────────────────────
# Длительность mp3 + квантование к кадру (см. CAPCUT.md §7.2).
# ─────────────────────────────────────────────────────────────────────

def floor_to_frame_us(us: int, fps: int = FPS) -> int:
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
    print(f"{'sid':<6} {'start':>7} {'dur':>7} {'audio':>7} shots  text")
    print("-" * 72)
    for ts in plan:
        text_preview = (ts.scene.text or "").replace("\n", " ")[:30]
        start_s = ts.start_us / US
        dur_s = ts.duration_us / US
        audio_s = ts.audio_span_us / US
        n_shots = len(ts.scene.videos)
        print(
            f"{ts.scene.sid:<6} "
            f"{start_s:7.2f} {dur_s:7.2f} {audio_s:7.2f} "
            f"{n_shots:<5}  {text_preview}"
        )
    if plan:
        total = plan[-1].end_us / US
        print("-" * 72)
        print(f"Всего: {total:.2f} сек ({total/60:.2f} мин)")


# ─────────────────────────────────────────────────────────────────────
# Основная сборка
# ─────────────────────────────────────────────────────────────────────

def build_draft(drafts_folder: Path, project_name: str) -> Path:
    try:
        import pycapcut as cc  # type: ignore
        from pycapcut import trange, TextStyle, ClipSettings  # type: ignore
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

    script.add_track(cc.TrackType.video, track_name="main")
    script.add_track(cc.TrackType.video, track_name="stickers")
    script.add_track(cc.TrackType.audio, track_name="voice")
    script.add_track(cc.TrackType.audio, track_name="music")
    script.add_track(cc.TrackType.audio, track_name="sfx")
    script.add_track(cc.TrackType.audio, track_name="sticker_sfx")
    script.add_track(cc.TrackType.text,  track_name="subtitles")

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
            cur += shot_dur_us

    for vseg in video_segments:
        script.add_segment(vseg, "main")

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

    total_us = plan[-1].end_us
    if MUSIC_FILE.is_file():
        music_seg = cc.AudioSegment(
            str(MUSIC_FILE),
            trange(0, total_us),
            volume=MUSIC_VOLUME,
        )
        try:
            fade_us = int(2.9 * US)
            music_seg.add_keyframe(max(0, total_us - fade_us), MUSIC_VOLUME)
            music_seg.add_keyframe(total_us, 0.0)
        except Exception as ex:
            print(f"  WARN фейд музыки не применился: {ex}")
        script.add_segment(music_seg, "music")
    else:
        print(f"  WARN не нашёл {MUSIC_FILE}, музыку пропускаю")

    intro_ts = next((ts for ts in plan if ts.scene.sid == "001"), None)
    if intro_ts is not None and len(intro_ts.audio_durs_us) >= 2:
        intro_start_us = intro_ts.start_us + intro_ts.audio_durs_us[0] + GAP_US
        intro_dur_us = intro_ts.audio_durs_us[1]
        tseg = cc.TextSegment(
            "Аполло́н и Касса́ндра\nМиф за минуту",
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
    p = argparse.ArgumentParser(description="Собрать CapCut-драфт «Аполлон и Кассандра».")
    p.add_argument("--drafts", help="Путь к CapCut\\User Data\\Projects\\com.lveditor.draft.")
    p.add_argument("--name", default=DEFAULT_PROJECT_NAME, help="Имя проекта в CapCut.")
    p.add_argument("--dry-run", action="store_true", help="Только напечатать план таймлайна.")
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
            "  python build_cassandra.py --drafts "
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
