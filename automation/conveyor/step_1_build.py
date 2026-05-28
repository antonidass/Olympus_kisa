"""
Шаг 1 конвейера — «Скелет» CapCut-проекта.

Собирает CapCut-драфт `AUTO <миф>` из аппрув-материалов webapp:
  • voice  — sentence_NNN_vM.mp3 из approved_sentences/
  • main   — scene_NN_vM.mp4 из video/ (учитывая webapp/selections/videos_*.json)
  • music  — assets/music/Dorian_Concept_-_Hide_CS01_Version_(SkySound.cc).mp3
            с fade_out 2.9 с
  • intro  — двухстрочный титр «<МИФ>\\nМИФ ЗА МИНУТУ» (STRome Bold, белый/красный)
             + halftone-effect «Зеленые точки» на длительность sentence_002
             + SFX «Realistic typing keyboard» на длительность typewriter-анимации
  • subs   — пословное караоке КАПСОМ (Anticva Bold с обводкой),
             whisper-тайминги если доступен, иначе равномерное разделение

Маппинг scene↔sentence строится автоматически из заголовков
content/<миф>/prompts/images.md (`## Сцена N (sent_NNN + sent_MMM — ...)`).
Никакого ручного scene_structure_<myth>.py не требуется.

CLI:
    python automation/conveyor/step_1_build.py --scenario "Аполлон и Кассандра"
    python automation/conveyor/step_1_build.py --scenario "..." --dry-run
    python automation/conveyor/step_1_build.py --scenario "..." --karaoke=none
    python automation/conveyor/step_1_build.py --scenario "..." --karaoke=whisper

По умолчанию karaoke=auto — если установлен openai-whisper, точные тайминги;
иначе равномерное разделение слов sentence_NNN.txt по длительности озвучки.
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import List, Optional

# Forced UTF-8 stdout (Windows cp1251 ломается на кириллице и стрелках).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # py3.7+
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# automation/conveyor/* и pyCapCut/* нужно положить в sys.path, потому что
# скрипт может быть запущен и как `python automation/conveyor/step_1_build.py`,
# и как `python -m automation.conveyor.step_1_build`.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from shared import (  # noqa: E402
    AUTO_PROJECT_PREFIX, CONTENT_DIR, MUSIC_FILE, US, FPS, GAP_US,
    HALFTONE_EFFECT_ID, HALFTONE_EFFECT_PATH,
    autodetect_drafts_folder, floor_to_frame_us, mp3_duration_us,
    make_audio_fade, make_halftone_material,
    make_halftone_effect_segment, make_halftone_track,
    resolve_timeline_scenes, strip_stresses, tokenize_words,
    load_sentence_text, load_plan, get_scene_override,
    detect_capcut_versions, fix_project_versions,
)
import capcut_control  # noqa: E402


# ─────────────────────────────────────────────────────────────────────
# Константы проекта (канон CAPCUT.md §1, §3)
# ─────────────────────────────────────────────────────────────────────

WIDTH = 1080
HEIGHT = 1920

VOICE_VOLUME = 1.0
ORIGINAL_CLIP_VOLUME = 0.34
MUSIC_VOLUME = 0.1348
MUSIC_FADE_OUT_US = int(2.9 * US)

# Шрифты — установлены в Windows Fonts (см. CAPCUT.md §3.1).
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
WINDOWS_FONTS_DIR = LOCALAPPDATA / "Microsoft" / "Windows" / "Fonts"
ANTICVA_FONT = WINDOWS_FONTS_DIR / "Anticva-Regular.otf"
STROME_FONT = WINDOWS_FONTS_DIR / "STRomeTrial-Bold.otf"

# Караоке-стиль (канон, см. pyCapCut/karaoke_*.py).
KARAOKE_FONT_SIZE = 10
KARAOKE_Y = 0.75
KARAOKE_COLOR = [1.0, 1.0, 1.0]
KARAOKE_BORDER_COLOR = [0.0, 0.0, 0.0]
KARAOKE_BORDER_ALPHA = 1.0
KARAOKE_BORDER_WIDTH = 0.08
MIN_WORD_MS = 120

# Интро-капс (двухстрочный титр, канон 16.0 после эволюции 22.75→17→16).
INTRO_FONT_SIZE = 16.0
INTRO_Y = 0.0
INTRO_COLOR_WHITE = [1.0, 1.0, 1.0]
INTRO_COLOR_RED = [0.7960784435, 0.2274509817, 0.2274509817]  # #cb3a3a

# Текст-эффект «字幕-直角描边» — обводка караоке-слов.
TEXT_EFFECT_ID = "7298651529408498952"
TEXT_EFFECT_THIRD_RESOURCE_ID = "7300850737280455169"
TEXT_EFFECT_PATH = (
    LOCALAPPDATA / "CapCut" / "User Data" / "Cache" / "effect"
    / TEXT_EFFECT_ID / "b32bee358ebfb58a17d9121ed2418ec2"
)

# Анимация «Пишущая машинка» на интро-титре, 1.666с.
TYPEWRITER_ANIM_ID = "7255573948300005889"
TYPEWRITER_DURATION_US = 1_666_666
TYPEWRITER_PATH = (
    LOCALAPPDATA / "CapCut" / "User Data" / "Cache" / "effect"
    / TYPEWRITER_ANIM_ID / "729d5e76cb22236d447b602d48d31b91"
)

# Анимация «Фокусировка» на каждом караоке-слове, 0.1с.
FOCUS_ANIM_ID = "7592158463770332432"
FOCUS_PATH = (
    LOCALAPPDATA / "CapCut" / "User Data" / "Cache" / "effect"
    / FOCUS_ANIM_ID / "5c93996262676ed0e150257ff4204fb4"
)

# SFX «Realistic typing keyboard» под интро-титром.
KEYBOARD_TYPING_NAME = "Realistic sound effects for typing on keyboards"
KEYBOARD_TYPING_EFFECT_ID = "6817471517962536962"
KEYBOARD_TYPING_PATH = (
    LOCALAPPDATA / "CapCut" / "User Data" / "Cache" / "music"
    / "2ec69836badb594b44950d6cbf32741e.mp3"
)
KEYBOARD_TYPING_SOURCE_DURATION_US = 3_400_000
KEYBOARD_TYPING_VOLUME = 0.6865413188934326


# ─────────────────────────────────────────────────────────────────────
# Утилиты
# ─────────────────────────────────────────────────────────────────────

def _u() -> str:
    return str(uuid.uuid4()).upper()


def _hex() -> str:
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


def derive_intro_title(scenario: str, sentence_002_text: str) -> str:
    """Двухстрочный титр для интро (без ударений, капсуется на месте отрисовки).

    Берём предложение sentence_002.txt («Аполло́н и Касса́ндра. Миф за минуту.»),
    режем по точке: первая часть → строка 1, оставшееся «Миф за минуту» →
    строка 2. Ударения (U+0301) нужны только TTS-движку; в визуальном
    титре они смотрятся как «грязь» поверх букв, поэтому снимаем.

    Fallback — имя сценария + «Миф за минуту».
    """
    text = strip_stresses(sentence_002_text.strip())
    # Канонический шаблон озвучки: «<имя мифа>. Миф за минуту.» — после
    # первой точки идёт ровно «Миф за минуту».
    m = re.match(r"^(.+?)\.\s*Миф за минуту\.?\s*$", text)
    if m:
        title_part = m.group(1).strip()
        return f"{title_part}\nМиф за минуту"
    if text:
        # Любой другой формат — берём как есть, без второй строки.
        return text.rstrip(".")
    return f"{strip_stresses(scenario)}\nМиф за минуту"


# ─────────────────────────────────────────────────────────────────────
# Сборка скелета через pycapcut
# ─────────────────────────────────────────────────────────────────────

def build_skeleton(
    scenes: list,
    scenario_dir: Path,
    drafts_folder: Path,
    project_name: str,
    intro_title_text: str,
    plan: dict,
) -> Path:
    """Создаёт CapCut-проект `project_name` со всеми базовыми треками.

    Возвращает путь к папке драфта (там лежит draft_content.json).
    """
    try:
        import pycapcut as cc  # type: ignore
        from pycapcut import trange, TextStyle, ClipSettings  # type: ignore
    except ImportError as e:
        raise SystemExit(
            "Не установлен pycapcut. Поставь зависимости:\n"
            "  pip install -r automation/requirements.txt"
        ) from e

    audio_dir = scenario_dir / "voiceover" / "audio" / "approved_sentences"
    video_dir = scenario_dir / "video"

    # ── Шаг A: длительности аудио сцен ──────────────────────────────
    audio_durs: list[list[int]] = []
    for scene in scenes:
        durs = [mp3_duration_us(audio_dir / a) for a in scene.audios]
        audio_durs.append(durs)

    # ── Шаг B: таймлайн-планирование ────────────────────────────────
    scene_starts: list[int] = []
    scene_durations: list[int] = []
    cursor = 0
    for durs in audio_durs:
        gaps = GAP_US * (len(durs) - 1) if durs else 0
        span = sum(durs) + gaps
        scene_starts.append(cursor)
        scene_durations.append(span)
        cursor += span
    total_us = cursor

    print(f"CapCut drafts folder: {drafts_folder}")
    print(f"Создаём проект:       {project_name} ({WIDTH}x{HEIGHT}, {FPS} fps)")
    print(f"{'sid':<5} {'start':>7} {'dur':>7} shots  audios")
    print("-" * 60)
    for s, start_us, dur_us, durs in zip(scenes, scene_starts, scene_durations, audio_durs):
        print(
            f"{s.sid:<5} {start_us/US:7.2f} {dur_us/US:7.2f} "
            f"{len(s.shots):<5}  {len(durs)}"
        )
    print("-" * 60)
    print(f"Всего: {total_us/US:.2f} сек ({total_us/US/60:.2f} мин)")

    # ── Шаг C: pycapcut Draft ───────────────────────────────────────
    folder = cc.DraftFolder(str(drafts_folder))
    script = folder.create_draft(project_name, WIDTH, HEIGHT, fps=FPS, allow_replace=True)

    script.add_track(cc.TrackType.video, track_name="main")
    script.add_track(cc.TrackType.audio, track_name="voice")
    script.add_track(cc.TrackType.audio, track_name="music")
    script.add_track(cc.TrackType.text,  track_name="subtitles")

    # ── Шаг D: видеошоты на main-трек ──────────────────────────────
    plan_log: list[str] = []
    for scene, start_us, dur_us in zip(scenes, scene_starts, scene_durations):
        n = len(scene.shots)
        base = dur_us // n
        remainder = dur_us - base * n
        cur = start_us
        for i, shot in enumerate(scene.shots):
            shot_dur_us = base + (remainder if i == n - 1 else 0)
            file_path = str(video_dir / shot.file)
            material = cc.VideoMaterial(file_path)
            kwargs = {}

            # plan.json: ручные start_from (секунды) и speed_override (×).
            # variant уже учтён в resolve_timeline_scenes при выборе shot.file.
            start_from_s, speed_override, _ = get_scene_override(plan, shot.scene_num)
            start_from_us = int(start_from_s * US)
            source_available_us = max(1, material.duration - start_from_us)

            if speed_override is not None:
                # Пользователь жёстко задал скорость. Source-окно считается
                # из неё: сколько секунд исходника нужно отрезать = target/speed.
                source_dur_us = int(shot_dur_us * speed_override)
                source_dur_us = max(1, min(source_dur_us, source_available_us))
                kwargs["source_timerange"] = trange(start_from_us, source_dur_us)
                if source_dur_us != shot_dur_us:
                    kwargs["speed"] = source_dur_us / shot_dur_us
                plan_log.append(
                    f"  ✎ {shot.file:<22} start={start_from_s:.2f}s speed={speed_override:.2f}× (manual)"
                )
            elif start_from_us > 0:
                # Только сдвиг старта, скорость авто.
                source_dur_us = min(shot_dur_us, source_available_us)
                kwargs["source_timerange"] = trange(start_from_us, source_dur_us)
                if shot_dur_us > source_dur_us:
                    kwargs["speed"] = source_dur_us / shot_dur_us
                plan_log.append(
                    f"  ✎ {shot.file:<22} start={start_from_s:.2f}s speed=auto"
                )
            elif shot_dur_us > source_available_us:
                # Видео короче голоса — замедляем, чтобы дотянуть.
                kwargs["speed"] = source_available_us / shot_dur_us
            elif shot_dur_us < source_available_us:
                # Видео длиннее голоса — обрезаем source_timerange.
                kwargs["source_timerange"] = trange(0, shot_dur_us)
            vseg = cc.VideoSegment(
                material,
                trange(cur, shot_dur_us),
                volume=ORIGINAL_CLIP_VOLUME,
                **kwargs,
            )
            script.add_segment(vseg, "main")
            cur += shot_dur_us
    if plan_log:
        print()
        print(f"План правок ({len(plan_log)}):")
        for line in plan_log:
            print(line)

    # ── Шаг E: voice-трек ────────────────────────────────────────────
    for scene, start_us, durs in zip(scenes, scene_starts, audio_durs):
        local_us = 0
        for a_file, a_dur_us in zip(scene.audios, durs):
            aseg = cc.AudioSegment(
                str(audio_dir / a_file),
                trange(start_us + local_us, a_dur_us),
                volume=VOICE_VOLUME,
            )
            script.add_segment(aseg, "voice")
            local_us += a_dur_us + GAP_US

    # ── Шаг F: music-трек с fade_out (через keyframes на сегменте) ──
    if MUSIC_FILE.is_file():
        music_seg = cc.AudioSegment(
            str(MUSIC_FILE),
            trange(0, total_us),
            volume=MUSIC_VOLUME,
        )
        try:
            music_seg.add_keyframe(max(0, total_us - MUSIC_FADE_OUT_US), MUSIC_VOLUME)
            music_seg.add_keyframe(total_us, 0.0)
        except Exception as ex:
            print(f"  WARN fade музыки не применился: {ex}")
        script.add_segment(music_seg, "music")
    else:
        print(f"  WARN не нашёл музыку: {MUSIC_FILE}")

    # ── Шаг G: интро-капс на subtitles-треке ────────────────────────
    # Кладём один text-сегмент. Двухцветный (белый/красный) стиль
    # допиливается ниже через прямую правку draft_content.json — pycapcut
    # TextStyle поддерживает только один цвет.
    if scenes and len(audio_durs[0]) >= 2:
        intro_start_us = scene_starts[0] + audio_durs[0][0] + GAP_US
        intro_dur_us = audio_durs[0][1]
        tseg = cc.TextSegment(
            intro_title_text,
            trange(intro_start_us, intro_dur_us),
            style=TextStyle(
                size=INTRO_FONT_SIZE,
                color=(1.0, 1.0, 1.0),
                align=1,
                auto_wrapping=True,
                max_line_width=0.85,
            ),
            clip_settings=ClipSettings(transform_x=0.0, transform_y=INTRO_Y),
        )
        script.add_segment(tseg, "subtitles")

    script.save()
    return drafts_folder / project_name


# ─────────────────────────────────────────────────────────────────────
# Post-processing draft_content.json: halftone + karaoke
# ─────────────────────────────────────────────────────────────────────

def find_voice_segments(draft: dict) -> list[dict]:
    """[{fname, abs_start_us, duration_us}, ...] из voice-трека."""
    audios_by_id = {a["id"]: a for a in draft.get("materials", {}).get("audios", [])}
    voice_track = next(
        (t for t in draft["tracks"] if t.get("type") == "audio" and t.get("name") == "voice"),
        None,
    )
    if not voice_track:
        return []
    out = []
    for seg in sorted(voice_track["segments"], key=lambda s: s["target_timerange"]["start"]):
        aud = audios_by_id.get(seg["material_id"])
        if not aud:
            continue
        out.append({
            "fname": os.path.basename(aud.get("path", "")),
            "abs_start_us": int(seg["target_timerange"]["start"]),
            "duration_us": int(seg["target_timerange"]["duration"]),
        })
    return out


def apply_halftone(draft: dict, intro_voice_seg: dict) -> str:
    """Накладывает «Зеленые точки» на длительность интро-аудио (sent_002)."""
    mat = make_halftone_material()
    draft["materials"].setdefault("video_effects", []).append(mat)
    effect_seg = make_halftone_effect_segment(
        mat["id"], intro_voice_seg["abs_start_us"], intro_voice_seg["duration_us"]
    )
    draft["tracks"].append(make_halftone_track(effect_seg))
    return (f"  ◌ halftone «Зеленые точки» {intro_voice_seg['abs_start_us']/US:.2f}–"
            f"{(intro_voice_seg['abs_start_us'] + intro_voice_seg['duration_us'])/US:.2f}s")


# ── Интро-титр: двухцветный + typewriter + text-effect ──────────────

def _font_block(path: Path) -> dict:
    return {"path": str(path).replace("\\", "/"), "id": ""}


def _stroke_block() -> dict:
    return {
        "content": {"solid": {"alpha": KARAOKE_BORDER_ALPHA, "color": list(KARAOKE_BORDER_COLOR)}},
        "width": KARAOKE_BORDER_WIDTH,
    }


def _effect_style_block() -> dict:
    return {"path": str(TEXT_EFFECT_PATH).replace("\\", "/"), "id": TEXT_EFFECT_ID}


def find_subtitles_track(draft: dict) -> Optional[dict]:
    for t in draft["tracks"]:
        if t.get("type") == "text" and t.get("name") == "subtitles":
            return t
    return None


def grab_text_template(draft: dict) -> tuple[dict, dict]:
    """Берём intro-сегмент (мы положили его в build_skeleton) и его material
    как шаблон для всех будущих text-сегментов (караоке + intro апгрейд).
    """
    texts = {m["id"]: m for m in draft["materials"]["texts"]}
    sub = find_subtitles_track(draft)
    if sub and sub["segments"]:
        seg = sub["segments"][0]
        mat = texts.get(seg["material_id"])
        if mat is not None:
            return copy.deepcopy(seg), copy.deepcopy(mat)
    raise RuntimeError("В драфте нет ни одного text-сегмента — шаблон взять неоткуда.")


def build_intro_content_json(text: str) -> str:
    """Двухстрочный титр: первая строка белая (STRome), вторая красная."""
    nl_pos = text.find("\n")
    stroke = _stroke_block()

    def style(rng: list[int], color: list[float]) -> dict:
        return {
            "fill": {"alpha": 1.0, "content": {"render_type": "solid",
                                                "solid": {"alpha": 1.0, "color": color}}},
            "font": _font_block(STROME_FONT),
            "range": rng,
            "size": INTRO_FONT_SIZE,
            "effectStyle": _effect_style_block(),
            "useLetterColor": True,
            "strokes": [stroke],
        }

    if nl_pos < 0:
        styles = [style([0, len(text)], INTRO_COLOR_WHITE)]
    else:
        styles = [
            style([0, nl_pos], INTRO_COLOR_WHITE),
            style([nl_pos + 1, len(text)], INTRO_COLOR_RED),
        ]
    return json.dumps({"text": text, "styles": styles}, ensure_ascii=False)


def upgrade_intro_segment(draft: dict, intro_text: str) -> None:
    """Превращаем заглушку intro-сегмента из pycapcut в полноценный двухцветный
    титр со STRome шрифтом, обводкой и текст-эффектом.
    """
    sub = find_subtitles_track(draft)
    if not sub or not sub["segments"]:
        return
    texts_by_id = {m["id"]: m for m in draft["materials"]["texts"]}
    seg = sub["segments"][0]
    mat = texts_by_id.get(seg["material_id"])
    if mat is None:
        return
    mat["content"] = build_intro_content_json(intro_text)
    mat["base_content"] = mat["content"]
    mat.update({
        "type": "text",
        "line_spacing": -0.20,
        "font_size": INTRO_FONT_SIZE, "text_size": INTRO_FONT_SIZE,
        "text_color": "#cb3a3a",
        "font_path": str(STROME_FONT).replace("\\", "/"),
        "border_alpha": KARAOKE_BORDER_ALPHA,
        "border_color": KARAOKE_BORDER_COLOR,
        "border_width": KARAOKE_BORDER_WIDTH,
        "background_color": "#000000",
        "language": "ru", "check_flag": 15,
    })

    # Typewriter-анимация (mat_animations) + text-effect (effects).
    anim = {
        "id": _u(),
        "type": "sticker_animation",
        "animations": [{
            "id": TYPEWRITER_ANIM_ID, "type": "in",
            "start": 0, "duration": min(TYPEWRITER_DURATION_US, seg["target_timerange"]["duration"]),
            "path": str(TYPEWRITER_PATH).replace("\\", "/"),
            "platform": "all", "resource_id": TYPEWRITER_ANIM_ID,
            "third_resource_id": TYPEWRITER_ANIM_ID, "source_platform": 1,
            "name": "Пишущая машинка", "category_id": "ruchang",
            "category_name": "Ввод", "panel": "", "material_type": "sticker",
            "anim_adjust_params": None, "request_id": "",
        }],
        "multi_language_current": "none",
    }
    text_effect = {
        "id": _u(),
        "effect_id": TEXT_EFFECT_ID, "resource_id": TEXT_EFFECT_ID,
        "third_resource_id": TEXT_EFFECT_THIRD_RESOURCE_ID,
        "name": "字幕-直角描边", "type": "text_effect", "sub_type": "none",
        "path": str(TEXT_EFFECT_PATH).replace("\\", "/"),
        "value": 1.0, "visible": True, "item_effect_type": 0,
        "category_id": "panel-text-flower", "category_name": "Все",
        "platform": "all", "apply_target_type": 0, "source_platform": 1,
        "adjust_params": [], "time_range": None, "formula_id": "",
    }
    draft["materials"].setdefault("material_animations", []).append(anim)
    draft["materials"].setdefault("effects", []).append(text_effect)
    seg["extra_material_refs"] = [anim["id"], text_effect["id"], text_effect["id"]]


def add_keyboard_typing_sfx(draft: dict, start_us: int, duration_us: int) -> str:
    """SFX «Realistic typing keyboard» под интро-титром на отдельной audio-дорожке."""
    duration_us = min(int(duration_us), TYPEWRITER_DURATION_US, KEYBOARD_TYPING_SOURCE_DURATION_US)
    audio = {
        "id": _u(), "unique_id": "", "type": "sound",
        "name": KEYBOARD_TYPING_NAME,
        "duration": KEYBOARD_TYPING_SOURCE_DURATION_US,
        "path": str(KEYBOARD_TYPING_PATH).replace("\\", "/"),
        "category_name": "heycan_search_sound", "wave_points": [],
        "music_id": "", "app_id": 1775,
        "effect_id": KEYBOARD_TYPING_EFFECT_ID, "resource_id": "",
        "category_id": "0", "intensifies_path": "", "formula_id": "",
        "check_flag": 1, "team_id": "", "local_material_id": "",
        "source_from": "", "copyright_limit_type": "none",
        "music_source": "", "pgc_id": "", "pgc_name": "",
        "similiar_music_info": {"original_song_id": "", "original_song_name": ""},
    }
    draft["materials"]["audios"].append(audio)
    seg = {
        "id": _u(),
        "source_timerange": {"start": 0, "duration": duration_us},
        "target_timerange": {"start": int(start_us), "duration": duration_us},
        "render_timerange": {"start": 0, "duration": 0},
        "desc": "", "state": 0, "speed": 1.0, "is_loop": False,
        "is_tone_modify": False, "reverse": False,
        "intensifies_audio": False, "cartoon": False,
        "volume": KEYBOARD_TYPING_VOLUME, "last_nonzero_volume": 1.0,
        "clip": None, "uniform_scale": None,
        "material_id": audio["id"], "extra_material_refs": [],
        "render_index": 0, "keyframe_refs": [],
        "enable_lut": False, "enable_adjust": False, "enable_hsl": False,
        "visible": True, "group_id": "",
        "track_render_index": 0, "track_attribute": 0,
        "is_placeholder": False, "template_id": "",
        "template_scene": "default", "common_keyframes": [],
        "caption_info": None,
        "responsive_layout": {"enable": False, "target_follow": "",
                              "size_layout": 0, "horizontal_pos_layout": 0,
                              "vertical_pos_layout": 0},
        "raw_segment_id": "", "lyric_keyframes": None,
        "source": "segmentsourcenormal",
        "digital_human_template_group_id": "",
    }
    track = {
        "id": _u(), "type": "audio", "segments": [seg],
        "flag": 0, "attribute": 0, "name": "", "is_default_name": True,
    }
    draft["tracks"].append(track)
    return f"  ⌨ SFX typing keyboard {start_us/US:.2f}+{duration_us/US:.2f}s"


# ── Караоке ───────────────────────────────────────────────────────────

def whisper_available() -> bool:
    try:
        import whisper  # type: ignore # noqa: F401
        return True
    except ImportError:
        return False


def find_cosyvoice_python() -> Optional[Path]:
    """Ищет python.exe из CosyVoice venv — там обычно установлен whisper."""
    candidates = [
        Path(__file__).resolve().parent.parent.parent
        / "external" / "CosyVoice" / ".venv_cosyvoice" / "Scripts" / "python.exe",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def whisper_transcribe(audio_dir: Path, fname: str, model_name: str) -> list[dict]:
    """[{word, start, end}, ...] из whisper-транскрипции с word_timestamps."""
    import whisper  # type: ignore
    model = whisper.load_model(model_name)
    res = model.transcribe(
        str(audio_dir / fname),
        language="ru",
        word_timestamps=True,
        fp16=False,
        condition_on_previous_text=False,
    )
    words = []
    for seg in res.get("segments", []):
        for w in seg.get("words", []):
            words.append({
                "start": float(w["start"]),
                "end": float(w["end"]),
                "word": w["word"].strip(),
            })
    return words


def equispaced_words(text: str, duration_us: int) -> list[dict]:
    """Fallback без whisper: делим длительность поровну на слова из текста."""
    words = tokenize_words(strip_stresses(text))
    if not words:
        return []
    dur_per = duration_us / len(words)
    out = []
    for i, w in enumerate(words):
        start_s = (i * dur_per) / US
        end_s = ((i + 1) * dur_per) / US
        out.append({"word": w, "start": start_s, "end": end_s})
    return out


def build_karaoke_words(
    voice_segments: list[dict],
    scenario_dir: Path,
    karaoke_mode: str,
    intro_sentence_fname: Optional[str],
) -> list[tuple[int, int, str]]:
    """[(abs_start_us, abs_end_us, word), ...] для всей дорожки.

    karaoke_mode:
      • 'whisper' — обязательно вызывает whisper. Падает если он недоступен.
      • 'equi'    — равномерное разделение по sentence_NNN.txt (без whisper).
      • 'none'    — пустой результат (караоке не нужно).
    """
    if karaoke_mode == "none":
        return []

    audio_dir = scenario_dir / "voiceover" / "audio" / "approved_sentences"
    texts_dir = scenario_dir / "voiceover" / "texts"

    sentences: list[dict] = []
    for vseg in voice_segments:
        if intro_sentence_fname and vseg["fname"] == intro_sentence_fname:
            # Интро-аудио не получает караоке — там halftone+титр.
            continue
        sentences.append(dict(vseg))  # копия

    if not sentences:
        return []

    if karaoke_mode == "whisper":
        import whisper  # noqa: F401  (импорт здесь, чтобы equi-режим не требовал его)
        model = None
        for s in sentences:
            words = whisper_transcribe(audio_dir, s["fname"], "medium")
            s["words"] = words
        # Поверх — equi-fallback на пустые результаты
        for s in sentences:
            if not s.get("words"):
                m = re.match(r"sentence_(\d+)", s["fname"])
                if m:
                    n = int(m.group(1))
                    txt = load_sentence_text(scenario_dir, n)
                    s["words"] = equispaced_words(txt, s["duration_us"])
    else:
        for s in sentences:
            m = re.match(r"sentence_(\d+)", s["fname"])
            if not m:
                s["words"] = []
                continue
            n = int(m.group(1))
            txt = load_sentence_text(scenario_dir, n)
            s["words"] = equispaced_words(txt, s["duration_us"])

    out: list[tuple[int, int, str]] = []
    for s in sentences:
        words = s.get("words") or []
        if not words:
            continue
        base_us = s["abs_start_us"]
        sentence_end_us = base_us + s["duration_us"]
        n = len(words)
        for i, w in enumerate(words):
            start_us = base_us + int(w["start"] * US)
            start_us = max(start_us, base_us)
            if start_us >= sentence_end_us:
                continue
            if i < n - 1:
                end_us = base_us + int(words[i + 1]["start"] * US)
            else:
                end_us = sentence_end_us
            end_us = min(end_us, sentence_end_us)
            if end_us - start_us < MIN_WORD_MS * 1000:
                end_us = min(sentence_end_us, start_us + MIN_WORD_MS * 1000)
            if end_us <= start_us:
                continue
            out.append((start_us, end_us, w["word"]))
    out.sort(key=lambda x: x[0])
    return out


def build_karaoke_content_json(text: str) -> str:
    """Караоке-слово КАПСОМ с Anticva, обводкой и текст-эффектом."""
    style = {
        "fill": {"alpha": 1.0, "content": {"render_type": "solid",
                                            "solid": {"alpha": 1.0, "color": KARAOKE_COLOR}}},
        "font": _font_block(ANTICVA_FONT),
        "range": [0, len(text)],
        "size": KARAOKE_FONT_SIZE,
        "bold": True,
        "effectStyle": _effect_style_block(),
        "useLetterColor": True,
        "strokes": [_stroke_block()],
    }
    return json.dumps({"text": text, "styles": [style]}, ensure_ascii=False)


def make_karaoke_material(template_mat: dict, text: str) -> dict:
    m = copy.deepcopy(template_mat)
    m["id"] = _hex()
    m["content"] = build_karaoke_content_json(text)
    m["base_content"] = m["content"]
    m.update({
        "type": "text",
        "font_size": KARAOKE_FONT_SIZE,
        "text_size": KARAOKE_FONT_SIZE,
        "text_color": "#ffffff",
        "font_path": str(ANTICVA_FONT).replace("\\", "/"),
        "border_alpha": KARAOKE_BORDER_ALPHA,
        "border_color": KARAOKE_BORDER_COLOR,
        "border_width": KARAOKE_BORDER_WIDTH,
        "language": "ru", "check_flag": 15,
        "line_spacing": 0.0,
    })
    m["words"] = {"text": [text], "start_time": [0], "end_time": [0]}
    return m


def make_karaoke_segment(template_seg: dict, material_id: str,
                          start_us: int, duration_us: int) -> dict:
    s = copy.deepcopy(template_seg)
    s["id"] = _hex()
    s["material_id"] = material_id
    s["target_timerange"] = {"start": int(start_us), "duration": int(duration_us)}
    s["source_timerange"] = None
    clip = s.setdefault("clip", {})
    clip.setdefault("scale", {"x": 1.0, "y": 1.0})
    clip.setdefault("flip", {"vertical": False, "horizontal": False})
    clip["transform"] = {"x": 0.0, "y": KARAOKE_Y}
    clip["alpha"] = 1.0
    s["render_timerange"] = {"start": 0, "duration": 0}
    s["common_keyframes"] = []
    s["caption_info"] = None
    s["extra_material_refs"] = []
    s["source"] = ""
    s["raw_segment_id"] = ""
    s["group_id"] = ""
    s["template_id"] = ""
    s["visible"] = True
    return s


def apply_karaoke(draft: dict, words: list[tuple[int, int, str]]) -> str:
    """Добавляет text-track 'karaoke' со словами КАПСОМ."""
    if not words:
        return "  ♪ караоке пропущено (нет слов)"

    tmpl_seg, tmpl_mat = grab_text_template(draft)
    karaoke_track = {
        "attribute": 0, "flag": 0, "id": _hex(),
        "is_default_name": True, "name": "karaoke",
        "segments": [], "type": "text",
    }
    draft["tracks"].append(karaoke_track)

    focus_anim_template = {
        "id": FOCUS_ANIM_ID, "type": "in",
        "start": 0, "duration": 100_000,
        "path": str(FOCUS_PATH).replace("\\", "/"),
        "platform": "all", "resource_id": FOCUS_ANIM_ID,
        "third_resource_id": "0", "source_platform": 1,
        "name": "Фокусировка", "category_id": "ruchang_fav",
        "category_name": "Избранное", "panel": "",
        "material_type": "sticker", "anim_adjust_params": None,
        "request_id": "",
    }

    for start_us, end_us, word in words:
        mat = make_karaoke_material(tmpl_mat, strip_stresses(word).upper())
        seg = make_karaoke_segment(tmpl_seg, mat["id"], start_us, end_us - start_us)
        anim = {
            "id": _u(),
            "type": "sticker_animation",
            "animations": [copy.deepcopy(focus_anim_template)],
            "multi_language_current": "none",
        }
        draft["materials"]["texts"].append(mat)
        draft["materials"].setdefault("material_animations", []).append(anim)
        seg["extra_material_refs"] = [anim["id"]]
        karaoke_track["segments"].append(seg)

    karaoke_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])
    return f"  ♪ караоке: {len(words)} слов"


def apply_music_fade(draft: dict) -> str:
    """Дублирует fade_out из build_skeleton как audio_fade-материал.

    pycapcut кладёт fade через keyframes, и этого достаточно — но добавляем
    ещё и явный audio_fade material для совместимости с enrich-скриптами
    (они ищут именно его).
    """
    music = next(
        (t for t in draft["tracks"] if t["type"] == "audio" and t.get("name") == "music"),
        None,
    )
    if not music or not music.get("segments"):
        return "  ⚠ music-трека нет, fade пропущен"
    fade = make_audio_fade(0, MUSIC_FADE_OUT_US)
    draft["materials"].setdefault("audio_fades", []).append(fade)
    seg = music["segments"][0]
    seg.setdefault("extra_material_refs", []).append(fade["id"])
    return f"  ♪ музыка: fade_out {MUSIC_FADE_OUT_US/US:.1f}s"


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description="Шаг 1 конвейера — скелет CapCut-проекта.")
    p.add_argument("--scenario", required=True, help="Имя мифа, как в content/ (например «Аполлон и Кассандра»).")
    p.add_argument("--drafts", help="Путь к CapCut\\User Data\\Projects\\com.lveditor.draft (по умолчанию автодетект).")
    p.add_argument("--name", help="Имя CapCut-проекта (по умолчанию «AUTO <scenario>»).")
    p.add_argument("--karaoke", choices=("auto", "whisper", "equi", "none"), default="auto",
                   help="Источник таймингов: auto=whisper-если-есть-иначе-equi (default), whisper=обязательно, equi=без whisper, none=пропустить.")
    p.add_argument("--dry-run", action="store_true", help="Только распечатать план таймлайна, ничего не писать.")
    p.add_argument("--whisper-model", default=os.environ.get("WHISPER_MODEL", "medium"),
                   help="Имя whisper-модели для --karaoke=whisper (default medium).")
    args = p.parse_args()

    scenario = args.scenario
    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.is_dir():
        print(f"Нет папки сценария: {scenario_dir}", file=sys.stderr)
        return 1

    print(f"=== Шаг 1 (скелет) для «{scenario}» ===")
    print()

    scenes = resolve_timeline_scenes(scenario)
    if not scenes:
        print("Не удалось собрать ни одной сцены — нечего монтировать.", file=sys.stderr)
        return 1

    intro_text_raw = load_sentence_text(scenario_dir, 2)
    intro_title = derive_intro_title(scenario, intro_text_raw)
    print(f"Интро-титр: {intro_title!r}")
    print()
    print(f"Сцен в таймлайне: {len(scenes)}")
    print(f"{'sid':<5} {'audios':<35} {'shots'}")
    print("-" * 80)
    for s in scenes:
        audios_str = ", ".join(s.audios)
        shots_str = ", ".join(sh.file for sh in s.shots)
        print(f"{s.sid:<5} {audios_str:<35} {shots_str}")

    if args.dry_run:
        return 0

    drafts = Path(args.drafts) if args.drafts else autodetect_drafts_folder()
    if drafts is None or not drafts.is_dir():
        print("Не нашёл папку CapCut drafts. Укажи её через --drafts.", file=sys.stderr)
        return 1

    project_name = args.name or (AUTO_PROJECT_PREFIX + scenario)

    # Решаем karaoke-режим
    karaoke_mode = args.karaoke
    if karaoke_mode == "auto":
        karaoke_mode = "whisper" if whisper_available() else "equi"
    print(f"Karaoke-режим: {karaoke_mode}")
    if karaoke_mode == "whisper" and not whisper_available():
        cv = find_cosyvoice_python()
        if cv:
            print(f"whisper не доступен в текущем venv, но найден {cv}", file=sys.stderr)
            print("Запусти скрипт его python.exe:", file=sys.stderr)
            print(f'  "{cv}" automation/conveyor/step_1_build.py --scenario "{scenario}" '
                  f'--karaoke=whisper', file=sys.stderr)
        else:
            print("--karaoke=whisper выставлен, но openai-whisper не установлен.", file=sys.stderr)
        return 1

    plan = load_plan(scenario)
    edited_shots = sum(
        1 for sh in (plan.get("shots") or {}).values()
        if isinstance(sh, dict) and (sh.get("start_from") or sh.get("speed_override"))
    )
    if edited_shots:
        print(f"План правок: {edited_shots} шотов с ручными настройками (plan.json).")
    else:
        print("План правок: пуст — все шоты на автомате.")

    # Авто-управление CapCut: если проект открыт в редакторе — сохраняем и
    # закрываем приложение (UI-дерево QML недоступно, кнопкой выйти нельзя);
    # в конце (finally) перезапускаем. Если CapCut в галерее/закрыт — сразу.
    guard = capcut_control.WriteGuard(auto=not args.dry_run)
    guard.__enter__()
    try:
        return _build_and_save(
            args, scenario, scenario_dir, scenes, intro_title,
            drafts, project_name, karaoke_mode, plan,
        )
    finally:
        guard.__exit__(None, None, None)


def _build_and_save(args, scenario, scenario_dir, scenes, intro_title,
                    drafts, project_name, karaoke_mode, plan) -> int:
    print()
    print("→ build_skeleton …")
    draft_dir = build_skeleton(scenes, scenario_dir, drafts, project_name, intro_title, plan)
    draft_file = draft_dir / "draft_content.json"
    if not draft_file.is_file():
        print(f"pycapcut не создал {draft_file}", file=sys.stderr)
        return 1

    print()
    print("→ post-processing draft_content.json …")
    draft = json.load(open(draft_file, encoding="utf-8"))

    voice_segs = find_voice_segments(draft)
    intro_voice_seg = None
    intro_fname: Optional[str] = None
    if voice_segs and len(voice_segs) >= 2:
        # Интро-аудио — sentence_002 (второй voice-сегмент по таймлайну).
        intro_voice_seg = next(
            (s for s in voice_segs if re.match(r"sentence_002", s["fname"])),
            voice_segs[1],
        )
        intro_fname = intro_voice_seg["fname"]

    upgrade_intro_segment(draft, intro_title)
    print("  ✎ intro-капс: двухцветный STRome, обводка, typewriter-анимация")

    if intro_voice_seg is not None:
        print(apply_halftone(draft, intro_voice_seg))
        print(add_keyboard_typing_sfx(
            draft, intro_voice_seg["abs_start_us"],
            min(TYPEWRITER_DURATION_US, intro_voice_seg["duration_us"]),
        ))
    else:
        print("  ⚠ интро-аудио не найдено, halftone и typing-SFX пропущены")

    print(apply_music_fade(draft))

    karaoke_words = build_karaoke_words(voice_segs, scenario_dir, karaoke_mode, intro_fname)
    print(apply_karaoke(draft, karaoke_words))

    # Сохраняем + бэкап
    bkp = draft_file.with_suffix(".json.step1-backup")
    shutil.copy2(draft_file, bkp)
    json.dump(draft, open(draft_file, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))

    # Чиним версию проекта, иначе CapCut при открытии требует обновление
    # (pycapcut пишет устаревшую new_version). Берём актуальные версии из
    # эталонного проекта drafts.
    content_ver, last_app, meta_ver = detect_capcut_versions(drafts, exclude=project_name)
    fix_project_versions(draft_dir, content_ver, last_app, meta_ver)
    print(f"  ⚙ версия проекта → new_version={content_ver} last_modified={last_app} meta={meta_ver!r}")

    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = draft_dir / tgt_name
        try:
            shutil.copy2(draft_file, tgt)
        except Exception:
            pass

    # State-файл для webapp: _detect_montage_step читает его и показывает
    # шаг 1 как «готов». Лежит в content/<миф>/montage/, чтобы прогресс
    # переживал перемещения CapCut-папки и переустановку CapCut.
    state_dir = scenario_dir / "montage"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "conveyor_state.json"
    try:
        existing = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}
    except Exception:
        existing = {}
    existing.update({
        "step": max(int(existing.get("step", 0)), 1),
        "step_1": {
            "project_name": project_name,
            "draft_dir": str(draft_dir),
            "karaoke_mode": karaoke_mode,
            "scenes": len(scenes),
            "karaoke_words": len(karaoke_words),
        },
    })
    state_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"OK Шаг 1 завершён.")
    print(f"  Драфт: {draft_dir}")
    print(f"  Бэкап: {bkp.name}")
    print(f"  State: {state_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
