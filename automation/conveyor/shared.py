"""
Общие хелперы для конвейерных скриптов automation/conveyor/*.

Здесь — то, что не зависит ни от номера шага, ни от мифа: пути проекта,
парсинг images.md, дискавер аппрув-озвучки и аппрув-видео, автодетект
папки CapCut Drafts, длительность mp3 с квантованием к кадру 60fps.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────
# Пути проекта
# ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # …/BOGI AI/
CONTENT_DIR = PROJECT_ROOT / "content"
ASSETS_DIR = PROJECT_ROOT / "assets"
SELECTIONS_DIR = PROJECT_ROOT / "webapp" / "selections"

MUSIC_FILE = ASSETS_DIR / "music" / "Dorian_Concept_-_Hide_CS01_Version_(SkySound.cc).mp3"

# Имя CapCut-проекта префиксуется AUTO, чтобы не затирать ручные сборки
# из pyCapCut/build_<myth>.py. См. CAPCUT.md.
AUTO_PROJECT_PREFIX = "AUTO "


# ─────────────────────────────────────────────────────────────────────
# Кадровое квантование (60fps канон, CAPCUT.md §7.2)
# ─────────────────────────────────────────────────────────────────────

FPS = 60
US = 1_000_000
# 2 кадра при 60fps — стандартный микро-gap между голосовыми сегментами
# внутри одной timeline-сцены (см. CAPCUT.md). Дублируется и в shared, и
# в step_1_build для удобства; значения должны совпадать.
GAP_US = int(2 / FPS * US)


def floor_to_frame_us(us: int, fps: int = FPS) -> int:
    """Округляет длительность вниз до границы кадра 60fps.

    Без этого CapCut снапит target_timerange к кадру и включает таймстретч
    голоса — получается «робовойс / как из ведра» (см. feedback memo).
    """
    frames = (us * fps) // US
    return (frames * US) // fps


def mp3_duration_us(path: Path) -> int:
    """Длительность mp3 через mutagen, квантованная до кадра 60fps."""
    try:
        from mutagen.mp3 import MP3  # type: ignore
    except ImportError as e:
        raise SystemExit(
            "Не установлен mutagen. Поставь зависимости:\n"
            "  pip install -r automation/requirements.txt"
        ) from e
    raw_us = int(MP3(str(path)).info.length * 1_000_000)
    return floor_to_frame_us(raw_us)


def video_duration_us(path: Path) -> int:
    """Длительность видео через pymediainfo (mp4/webm/mov)."""
    try:
        from pymediainfo import MediaInfo  # type: ignore
    except ImportError as e:
        raise SystemExit(
            "Не установлен pymediainfo. Поставь зависимости:\n"
            "  pip install -r automation/requirements.txt"
        ) from e
    mi = MediaInfo.parse(str(path))
    for t in mi.tracks:
        if t.track_type == "Video" and t.duration is not None:
            return int(float(t.duration) * 1000)
    raise RuntimeError(f"Не нашёл video-дорожку в {path}")


# ─────────────────────────────────────────────────────────────────────
# Автодетект CapCut Drafts
# ─────────────────────────────────────────────────────────────────────

def autodetect_drafts_folder() -> Optional[Path]:
    """Возвращает путь до CapCut\\User Data\\Projects\\com.lveditor.draft на Windows.

    Поддерживает международный CapCut и китайский JianyingPro.
    """
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
# Версии CapCut-проекта
# ─────────────────────────────────────────────────────────────────────
# pycapcut пишет в draft несовместимые с установленным CapCut версии, из-за
# чего при открытии всплывает «Этот проект создан в более новой версии».
#
# Что определяет совместимость (эмпирически, эталон — Баба-Яга/Цирцея,
# которые открываются на CapCut 7.5.0 без диалога):
#   draft_content.new_version                     = "148.0.0"   (НЕ 167!)
#   draft_content.last_modified_platform.app_version = "7.5.0"  (установленная)
#   draft_meta_info.draft_new_version             = ""          (ПУСТОЙ!)
#
# Подводный камень: проекты с draft_new_version="164.0.0"/new_version="167.0.0"
# — это сломанные (созданы более новой версией CapCut до отката на 7.5.0),
# они как раз и требуют обновление. Поэтому эталон ищем по ПУСТОМУ
# draft_new_version, а не по непустому.

FALLBACK_CONTENT_NEW_VERSION = "148.0.0"
FALLBACK_LAST_MODIFIED_APP = "7.5.0"
FALLBACK_META_NEW_VERSION = ""


def detect_capcut_versions(drafts_folder: Path, exclude: Optional[str] = None
                           ) -> tuple[str, str, str]:
    """(content_new_version, last_modified_app_version, meta_new_version).

    Эталон — «здоровый» проект, который CapCut открывает молча: признак —
    ПУСТОЙ draft_meta_info.draft_new_version. Из него берём content.new_version
    и content.last_modified_platform.app_version. Если эталона нет — fallback.
    """
    if drafts_folder and drafts_folder.is_dir():
        for proj in sorted(drafts_folder.iterdir()):
            if not proj.is_dir() or proj.name == exclude:
                continue
            dm = proj / "draft_meta_info.json"
            dc = proj / "draft_content.json"
            if not dm.is_file() or not dc.is_file():
                continue
            try:
                meta_ver = json.loads(dm.read_text(encoding="utf-8")).get("draft_new_version")
                # «здоровый» проект → draft_new_version пустой
                if meta_ver:
                    continue
                dcd = json.loads(dc.read_text(encoding="utf-8"))
                content_ver = dcd.get("new_version") or ""
                lmp = dcd.get("last_modified_platform") or {}
                last_app = lmp.get("app_version") or ""
            except Exception:
                continue
            if content_ver and last_app:
                return content_ver, last_app, ""
    return FALLBACK_CONTENT_NEW_VERSION, FALLBACK_LAST_MODIFIED_APP, FALLBACK_META_NEW_VERSION


def fix_project_versions(draft_dir: Path, content_ver: str,
                         last_modified_app: str, meta_ver: str) -> None:
    """Приводит версии проекта к «здоровым», чтобы CapCut не требовал обновление.

    Меняет:
      draft_content.new_version
      draft_content.last_modified_platform.app_version
      draft_meta_info.draft_new_version

    Вызывать ПОСЛЕ записи драфта и ДО синхронизации .bak/template-tmp.
    """
    dc_path = draft_dir / "draft_content.json"
    dm_path = draft_dir / "draft_meta_info.json"
    if dc_path.is_file():
        try:
            dc = json.loads(dc_path.read_text(encoding="utf-8"))
            dc["new_version"] = content_ver
            lmp = dc.get("last_modified_platform")
            if isinstance(lmp, dict):
                lmp["app_version"] = last_modified_app
            dc_path.write_text(json.dumps(dc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        except Exception:
            pass
    if dm_path.is_file():
        try:
            dm = json.loads(dm_path.read_text(encoding="utf-8"))
            dm["draft_new_version"] = meta_ver
            dm_path.write_text(json.dumps(dm, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────
# Парсинг images.md / approved_sentences / video_selections
# ─────────────────────────────────────────────────────────────────────

APPROVED_FILE_RE = re.compile(r"^(?P<base>sentence_\d{3})_(?P<variant>v?\d+)$")
VIDEO_FILE_RE = re.compile(r"^scene_(\d+)_v(\d+)$")
VIDEO_EXTS = {".mp4", ".webm", ".mov"}


def parse_scene_sentence_mapping(md_path: Path) -> dict[str, list[int]]:
    """scene_NN → [sent_numbers] из заголовков `## Сцена N (sent_NNN — ...)`.

    Дубликат логики из webapp/app.py — оставлен здесь, чтобы конвейер мог
    запускаться без зависимости от Flask-приложения.
    """
    if not md_path.exists():
        return {}
    content = md_path.read_text(encoding="utf-8")
    out: dict[str, list[int]] = {}
    for m in re.finditer(
        r"^##\s+Сцена\s+(?:scene_)?(\d+)([^\n]*)$", content, re.MULTILINE
    ):
        try:
            scene_num = int(m.group(1))
        except ValueError:
            continue
        tail = m.group(2) or ""
        sents = [int(x) for x in re.findall(r"sent[_\s]*(\d{1,4})", tail)]
        if sents:
            out[f"scene_{scene_num:02d}"] = sents
    return out


def load_approved_sentences(scenario_dir: Path) -> dict[str, str]:
    """{base: variant} для одобренных озвучек, например {sentence_001: v4}."""
    approved_dir = scenario_dir / "voiceover" / "audio" / "approved_sentences"
    if not approved_dir.exists():
        return {}
    result: dict[str, str] = {}
    for mp3 in approved_dir.glob("*.mp3"):
        m = APPROVED_FILE_RE.match(mp3.stem)
        if not m:
            continue
        result[m.group("base")] = m.group("variant")
    return result


def discover_video_scenes(video_dir: Path) -> dict[str, list[str]]:
    """{scene_NN: [filename, ...]} отсортированный по variant (v1, v2, ...)."""
    scenes: dict[str, list[tuple[int, str]]] = {}
    if not video_dir.exists():
        return {}
    for v in sorted(video_dir.iterdir()):
        if not v.is_file() or v.suffix.lower() not in VIDEO_EXTS:
            continue
        m = VIDEO_FILE_RE.match(v.stem)
        if not m:
            continue
        idx, variant = int(m.group(1)), int(m.group(2))
        base = f"scene_{idx:02d}"
        scenes.setdefault(base, []).append((variant, v.name))
    return {
        base: [fn for _, fn in sorted(lst, key=lambda x: x[0])]
        for base, lst in scenes.items()
    }


def load_video_selections(scenario: str) -> dict:
    """Читает webapp/selections/videos_<scenario>.json. Может быть пустым."""
    path = SELECTIONS_DIR / f"videos_{scenario}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_sentence_text(scenario_dir: Path, sent_num: int) -> str:
    fp = scenario_dir / "voiceover" / "texts" / f"sentence_{sent_num:03d}.txt"
    if not fp.exists():
        return ""
    try:
        return fp.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────
# Сборка таймлайн-плана из сырья
# ─────────────────────────────────────────────────────────────────────

@dataclass
class TimelineShot:
    file: str          # имя файла в video/, например "scene_06_v1.mp4"
    scene_num: int     # 6


@dataclass
class TimelineScene:
    """Один смысловой блок таймлайна = одно или несколько подряд идущих
    предложений озвучки + один или несколько видеошотов под них.

    Mapping берётся из заголовков images.md: `## Сцена N (sent_X + sent_Y)`.
    """
    sid: str                       # "001", "002", ...
    audios: List[str]              # ["sentence_001_v4.mp3", "sentence_002_v6.mp3"]
    shots: List[TimelineShot]      # [TimelineShot(file="scene_01_v1.mp4", scene_num=1)]
    sentence_nums: List[int]       # [1, 2]


def _pick_audio_variant(approved: dict[str, str], sent_num: int) -> Optional[str]:
    """sentence_001 → 'sentence_001_v4.mp3', если в approved_sentences/ лежит v4."""
    base = f"sentence_{sent_num:03d}"
    variant = approved.get(base)
    if variant is None:
        return None
    variant_token = variant if variant.startswith("v") else f"v{variant}"
    return f"{base}_{variant_token}.mp3"


def _pick_video_variant(scenes: dict[str, list[str]], selections: dict,
                        plan: dict, scene_num: int) -> Optional[str]:
    """scene_06 → "scene_06_v2.mp4".

    Приоритет выбора версии:
      1. plan.json `variant` (ручной выбор в редакторе плана)
      2. webapp/selections/videos_*.json (выбор в ревью видео)
      3. первый доступный файл по variant-сортировке
    """
    base = f"scene_{scene_num:02d}"
    variants = scenes.get(base, [])
    if not variants:
        return None

    def _match(token: str) -> Optional[str]:
        token = token if str(token).startswith("v") else f"v{token}"
        target = f"{base}_{token}"
        for fn in variants:
            if Path(fn).stem == target:
                return fn
        return None

    # 1. plan.variant
    _, _, plan_variant = get_scene_override(plan, scene_num)
    if plan_variant:
        hit = _match(plan_variant)
        if hit:
            return hit

    # 2. selections
    selected = selections.get(base) if isinstance(selections, dict) else None
    if selected:
        hit = _match(selected)
        if hit:
            return hit

    # 3. первый
    return variants[0]


def resolve_timeline_scenes(scenario: str) -> List[TimelineScene]:
    """Главная функция: строит SCENES для CapCut-сборки из аппрув-материалов.

    Шаги:
      1. Читаем `prompts/images.md` (или video.md) → mapping scene_NN ↔ [sent_NNN].
      2. Для каждого sent_NNN ищем mp3 в `voiceover/audio/approved_sentences/`.
      3. Для каждого scene_NN ищем mp4 в `video/`, уважая `webapp/selections/videos_*.json`.
      4. Группируем последовательные scene_NN, у которых один и тот же sent_NNN,
         в одну TimelineScene с двумя шотами (как в build_cassandra.py).
    """
    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.is_dir():
        raise SystemExit(f"Нет папки сценария: {scenario_dir}")

    images_md = scenario_dir / "prompts" / "images.md"
    video_md = scenario_dir / "prompts" / "video.md"
    sent_mapping = parse_scene_sentence_mapping(images_md)
    if not sent_mapping:
        sent_mapping = parse_scene_sentence_mapping(video_md)
    if not sent_mapping:
        raise SystemExit(
            f"Не нашёл mapping `## Сцена N (sent_NNN …)` ни в {images_md.name}, "
            f"ни в {video_md.name}. Конвейер не может разложить sentence↔scene."
        )

    approved = load_approved_sentences(scenario_dir)
    video_scenes = discover_video_scenes(scenario_dir / "video")
    selections = load_video_selections(scenario)
    plan = load_plan(scenario)

    # Группируем подряд идущие scene_NN по их sent_NNN. Если несколько сцен
    # ссылаются на один и тот же sent_NNN (например, scene_06 + scene_07 → sent_007),
    # они становятся одной TimelineScene с двумя шотами.
    scene_keys = sorted(sent_mapping.keys(), key=lambda k: int(k.split("_")[1]))

    groups: List[tuple[List[int], List[int]]] = []  # (sents, scene_nums)
    for scene_key in scene_keys:
        scene_num = int(scene_key.split("_")[1])
        sents = sent_mapping[scene_key]
        if groups and groups[-1][0] == sents:
            groups[-1][1].append(scene_num)
        else:
            groups.append((list(sents), [scene_num]))

    out: List[TimelineScene] = []
    missing_audio: List[int] = []
    missing_video: List[int] = []
    for idx, (sents, scene_nums) in enumerate(groups, start=1):
        audios: List[str] = []
        for n in sents:
            picked = _pick_audio_variant(approved, n)
            if picked is None:
                missing_audio.append(n)
                continue
            audios.append(picked)
        shots: List[TimelineShot] = []
        for sn in scene_nums:
            picked_v = _pick_video_variant(video_scenes, selections, plan, sn)
            if picked_v is None:
                missing_video.append(sn)
                continue
            shots.append(TimelineShot(file=picked_v, scene_num=sn))
        if not audios or not shots:
            continue
        out.append(TimelineScene(
            sid=f"{idx:03d}",
            audios=audios,
            shots=shots,
            sentence_nums=sents,
        ))

    if missing_audio or missing_video:
        msg = []
        if missing_audio:
            msg.append(f"нет одобренной озвучки для sent_{', sent_'.join(f'{n:03d}' for n in missing_audio)}")
        if missing_video:
            msg.append(f"нет видеоклипа для scene_{', scene_'.join(f'{n:02d}' for n in missing_video)}")
        raise SystemExit("Не хватает материалов: " + "; ".join(msg))
    return out


# ─────────────────────────────────────────────────────────────────────
# Halftone / эффект-трек (взято из pyCapCut/enrich_dionysus.py)
# ─────────────────────────────────────────────────────────────────────

LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))

HALFTONE_EFFECT_ID = "7399468802095795462"
HALFTONE_EFFECT_NAME = "Зеленые точки"
HALFTONE_EFFECT_MD5 = "87e58ba33f7dc96c4e108cd67c67e2a4"
HALFTONE_EFFECT_PATH = (
    LOCALAPPDATA / "CapCut" / "User Data" / "Cache" / "effect"
    / HALFTONE_EFFECT_ID / HALFTONE_EFFECT_MD5
)


def _u() -> str:
    return str(uuid.uuid4()).upper()


def make_halftone_material() -> dict:
    """Video-effect material с каноничными параметрами (37/74/40/100)."""
    return {
        "adjust_params": [
            {"default_value": 0.6, "max_value": 1.0, "min_value": 0.0,
             "name": "effects_adjust_texture", "parameterIndex": 0, "portIndex": 0, "value": 0.37},
            {"default_value": 1.0, "max_value": 1.0, "min_value": 0.0,
             "name": "effects_adjust_filter", "parameterIndex": 1, "portIndex": 0, "value": 0.74},
            {"default_value": 0.5, "max_value": 1.0, "min_value": 0.0,
             "name": "effects_adjust_color", "parameterIndex": 2, "portIndex": 0, "value": 0.4},
            {"default_value": 0.5, "max_value": 1.0, "min_value": 0.0,
             "name": "effects_adjust_size", "parameterIndex": 3, "portIndex": 0, "value": 1.0},
        ],
        "algorithm_artifact_path": "",
        "apply_target_type": 2,
        "apply_time_range": None,
        "bind_segment_id": "",
        "category_id": "",
        "category_name": "",
        "common_keyframes": [],
        "covering_relation_change": 0,
        "disable_effect_faces": [],
        "effect_mask": [],
        "effect_id": HALFTONE_EFFECT_ID,
        "enable_mask": True,
        "enable_video_mask_shadow": True,
        "enable_video_mask_stroke": True,
        "formula_id": "",
        "id": _u(),
        "item_effect_type": 0,
        "name": HALFTONE_EFFECT_NAME,
        "path": str(HALFTONE_EFFECT_PATH).replace("\\", "/"),
        "platform": "all",
        "render_index": 11000,
        "request_id": "20260528000000HALFTONE",
        "resource_id": HALFTONE_EFFECT_ID,
        "source_platform": 1,
        "sub_type": 0,
        "transparent_params": "",
        "time_range": None,
        "track_render_index": 0,
        "type": "video_effect",
        "value": 1.0,
        "version": "",
    }


def make_halftone_effect_segment(material_id: str, start_us: int, duration_us: int) -> dict:
    return {
        "caption_info": None, "cartoon": False, "clip": None,
        "color_correct_alg_result": "", "common_keyframes": [], "desc": "",
        "digital_human_template_group_id": "",
        "enable_adjust": False, "enable_adjust_mask": False,
        "enable_color_adjust_pro": False, "enable_color_correct_adjust": False,
        "enable_color_curves": True, "enable_color_match_adjust": False,
        "enable_color_wheels": True, "enable_hsl": False, "enable_hsl_curves": True,
        "enable_lut": False, "enable_mask_shadow": False, "enable_mask_stroke": False,
        "enable_smart_color_adjust": False, "enable_video_mask": True,
        "extra_material_refs": [], "group_id": "", "hdr_settings": None,
        "id": _u(), "intensifies_audio": False, "is_loop": False,
        "is_placeholder": False, "is_tone_modify": False, "keyframe_refs": [],
        "last_nonzero_volume": 1.0, "lyric_keyframes": None,
        "material_id": material_id, "raw_segment_id": "", "render_index": 11000,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {"enable": False, "horizontal_pos_layout": 0,
                              "size_layout": 0, "target_follow": "",
                              "vertical_pos_layout": 0},
        "reverse": False, "source": "segmentsourcenormal",
        "source_timerange": None, "speed": 1.0, "state": 0,
        "target_timerange": {"duration": int(duration_us), "start": int(start_us)},
        "template_id": "", "template_scene": "default",
        "track_attribute": 0, "track_render_index": 0, "uniform_scale": None,
        "visible": True, "volume": 1.0,
    }


def make_halftone_track(segment: dict) -> dict:
    return {
        "attribute": 0, "flag": 0, "id": _u(),
        "is_default_name": False, "name": "halftone_green_dots",
        "segments": [segment], "type": "effect",
    }


def make_audio_fade(fade_in_us: int, fade_out_us: int) -> dict:
    return {
        "fade_in_duration": int(fade_in_us),
        "fade_out_duration": int(fade_out_us),
        "fade_type": 0,
        "id": _u(),
        "type": "audio_fade",
    }


# ─────────────────────────────────────────────────────────────────────
# Текстовые утилиты
# ─────────────────────────────────────────────────────────────────────

def strip_stresses(text: str) -> str:
    """Убирает U+0301 (комбинирующий акут) но оставляет ё/й.

    Используется при подготовке reference-текста к whisper-выравниванию
    и при upper-casing для караоке.
    """
    nfd = unicodedata.normalize("NFD", text)
    cleaned = nfd.replace("́", "")
    return unicodedata.normalize("NFC", cleaned)


# ─────────────────────────────────────────────────────────────────────
# План правок шагов конвейера — content/<миф>/montage/plan.json
# ─────────────────────────────────────────────────────────────────────
#
# Структура plan.json:
#   {
#     "version": 1,
#     "shots": {
#       "scene_03_v1": {"start_from": 1.0, "speed_override": null},
#       "scene_05_v1": {"start_from": 0.0, "speed_override": 1.2}
#     }
#   }
#
# Ключи — `<stem>` файла видео (scene_03_v1 для scene_03_v1.mp4). Это
# даёт точный таргет — если пользователь поменял selection с v1 на v2,
# правки для v1 не подтянутся к v2 автоматически (что правильно: v2 может
# иметь другую длительность и start_from будет невалиден).
#
# start_from — секунды от начала исходного видео (0.0 = без отступа).
# speed_override — множитель скорости (1.0 = оригинал, 0.5 = в 2 раза
# медленнее). null/отсутствует = автоматика по длительности голоса.


PLAN_VERSION = 1


def _plan_path(scenario_dir: Path) -> Path:
    return scenario_dir / "montage" / "plan.json"


def plan_scene_key(scene_ref) -> str:
    """Нормализует ссылку на сцену к базовому ключу `scene_NN`.

    Принимает int (3 → scene_03), либо строку scene_03 / scene_03_v1 /
    scene_03_v1.mp4 — версия и расширение отбрасываются. Ключ плана НЕ
    содержит версию: версия хранится отдельным полем `variant`, чтобы её
    смена не плодила новые записи и не теряла start/speed.
    """
    if isinstance(scene_ref, int):
        return f"scene_{scene_ref:02d}"
    m = re.match(r"(scene_\d+)", str(scene_ref))
    return m.group(1) if m else str(scene_ref)


def _migrate_plan_keys(shots: dict) -> dict:
    """Старые планы хранили ключи как scene_03_v1 — мигрируем в scene_03 +variant."""
    out: dict = {}
    for key, entry in (shots or {}).items():
        if not isinstance(entry, dict):
            continue
        base = plan_scene_key(key)
        m = re.search(r"_(v\d+)$", str(key))
        if m and "variant" not in entry:
            entry = dict(entry)
            entry["variant"] = m.group(1)
        out[base] = entry
    return out


def load_plan(scenario: str) -> dict:
    """Читает plan.json. Возвращает пустой план если файла нет."""
    path = _plan_path(CONTENT_DIR / scenario)
    if not path.exists():
        return {"version": PLAN_VERSION, "shots": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"version": PLAN_VERSION, "shots": {}}
        data.setdefault("version", PLAN_VERSION)
        data["shots"] = _migrate_plan_keys(data.get("shots") or {})
        return data
    except Exception:
        return {"version": PLAN_VERSION, "shots": {}}


def save_plan(scenario: str, plan: dict) -> None:
    """Сохраняет plan.json. Создаёт content/<миф>/montage/ если надо."""
    path = _plan_path(CONTENT_DIR / scenario)
    path.parent.mkdir(parents=True, exist_ok=True)
    plan = dict(plan)
    plan.setdefault("version", PLAN_VERSION)
    plan["shots"] = _migrate_plan_keys(plan.get("shots") or {})
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


def get_scene_override(plan: dict, scene_ref) -> tuple[float, Optional[float], Optional[str]]:
    """(start_from_seconds, speed_override, variant) для сцены.

    Если плана/ключа нет — (0.0, None, None).
    speed_override=None → «автомат» (рассчитать по длительности).
    variant=None → версия не переопределена (взять selections/первую).
    """
    shots = (plan or {}).get("shots") or {}
    entry = shots.get(plan_scene_key(scene_ref))
    if not isinstance(entry, dict):
        return 0.0, None, None
    try:
        start = float(entry.get("start_from", 0.0) or 0.0)
    except (TypeError, ValueError):
        start = 0.0
    raw_speed = entry.get("speed_override")
    if raw_speed in (None, "", "auto"):
        speed = None
    else:
        try:
            speed = float(raw_speed)
            if speed <= 0:
                speed = None
        except (TypeError, ValueError):
            speed = None
    variant = entry.get("variant") or None
    if variant and not str(variant).startswith("v"):
        variant = f"v{variant}"
    return start, speed, variant


def build_plan_metadata(scenario: str) -> dict:
    """Подготовка данных для редактора плана в UI.

    Возвращает структуру с list timeline-сцен и информацией о каждом шоте:
    sentence_NNN с длительностью голоса, scene_NN_vM с длительностью видео
    в исходнике, текущие правки start_from / speed_override и подсчёт
    auto-speed (длительность_голоса / длительность_видео).

    Длительности считаются через mp3_duration_us / video_duration_us
    (mutagen + pymediainfo). На 20 файлах занимает ~0.5 сек.
    """
    scenes = resolve_timeline_scenes(scenario)
    scenario_dir = CONTENT_DIR / scenario
    audio_dir = scenario_dir / "voiceover" / "audio" / "approved_sentences"
    video_dir = scenario_dir / "video"
    video_scenes = discover_video_scenes(video_dir)

    plan = load_plan(scenario)

    out_scenes: List[dict] = []
    for ts in scenes:
        audio_meta = []
        for a in ts.audios:
            dur_us = mp3_duration_us(audio_dir / a)
            m = re.match(r"sentence_(\d+)", a)
            sent_num = int(m.group(1)) if m else None
            text = load_sentence_text(scenario_dir, sent_num) if sent_num else ""
            audio_meta.append({
                "file": a,
                "sent": f"sent_{sent_num:03d}" if sent_num else a,
                "duration_us": dur_us,
                "duration_s": round(dur_us / US, 2),
                "text": text,
            })
        voice_span_us = sum(m["duration_us"] for m in audio_meta) + GAP_US * max(0, len(audio_meta) - 1)

        shot_meta = []
        for shot in ts.shots:
            scene_key = f"scene_{shot.scene_num:02d}"
            # Все доступные версии этой сцены с их длительностями — для дропдауна.
            variants_meta = []
            for fn in video_scenes.get(scene_key, []):
                vm = re.search(r"_(v\d+)$", Path(fn).stem)
                vtoken = vm.group(1) if vm else "v?"
                vdur_us = 0
                fp = video_dir / fn
                if fp.exists():
                    try:
                        vdur_us = video_duration_us(fp)
                    except Exception:
                        vdur_us = 0
                variants_meta.append({
                    "variant": vtoken,
                    "file": fn,
                    "duration_us": vdur_us,
                    "duration_s": round(vdur_us / US, 2) if vdur_us else None,
                })

            cur_vm = re.search(r"_(v\d+)$", Path(shot.file).stem)
            cur_variant = cur_vm.group(1) if cur_vm else "v?"
            v_dur_us = next((v["duration_us"] for v in variants_meta if v["variant"] == cur_variant), 0)

            start_from, speed_override, _ = get_scene_override(plan, shot.scene_num)
            shot_meta.append({
                "file": shot.file,
                "scene_num": shot.scene_num,
                "scene_key": scene_key,
                "variant": cur_variant,
                "variants": variants_meta,
                "src_duration_us": v_dur_us,
                "src_duration_s": round(v_dur_us / US, 2) if v_dur_us else None,
                "start_from": start_from,
                "speed_override": speed_override,
            })

        # Распределение voice_span между шотами (как в build_skeleton)
        n = len(shot_meta)
        if n > 0:
            base = voice_span_us // n
            remainder = voice_span_us - base * n
            for i, sh in enumerate(shot_meta):
                target_us = base + (remainder if i == n - 1 else 0)
                sh["target_duration_us"] = target_us
                sh["target_duration_s"] = round(target_us / US, 2)
                # auto-speed считается из логики build_skeleton:
                #   src >= target → видео ОБРЕЗАЕТСЯ до target, speed = 1.0×
                #   src <  target → видео ЗАМЕДЛЯЕТСЯ (speed = src/target < 1)
                # «Ускорение» в авто-режиме никогда не включается — это была
                # бы порча оригинала. Если пользователю нужно ускорить, он
                # ставит speed_override руками.
                if sh["src_duration_us"] and target_us:
                    eff_src_us = max(1, sh["src_duration_us"] - int(sh["start_from"] * US))
                    if eff_src_us >= target_us:
                        sh["auto_speed"] = 1.0
                    else:
                        sh["auto_speed"] = round(eff_src_us / target_us, 3)
                else:
                    sh["auto_speed"] = None

        out_scenes.append({
            "sid": ts.sid,
            "audios": audio_meta,
            "shots": shot_meta,
            "voice_span_us": voice_span_us,
            "voice_span_s": round(voice_span_us / US, 2),
        })

    edited_count = sum(
        1 for s in out_scenes for sh in s["shots"]
        if sh["start_from"] > 0 or sh["speed_override"] is not None
    )
    return {
        "scenario": scenario,
        "plan": plan,
        "scenes": out_scenes,
        "edited_count": edited_count,
        "total_shots": sum(len(s["shots"]) for s in out_scenes),
    }


def tokenize_words(text: str) -> list[str]:
    """Делит текст на слова-токены как whisper: по пробелам и дефисам."""
    raw = re.split(r"\s+", text.strip())
    split: list[str] = []
    for t in raw:
        split.extend(t.split("-"))
    out: list[str] = []
    for w in split:
        if not w:
            continue
        if not re.search(r"\w", w, flags=re.UNICODE):
            continue
        out.append(w)
    return out
