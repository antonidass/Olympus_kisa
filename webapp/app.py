"""
Веб-приложение для ревью озвучки, изображений и видео.

Режим «озвучка»:
  Аудио:     content/<scenario>/voiceover/audio/
  Тексты:    content/<scenario>/voiceover/texts/
  Выбор:     webapp/selections/<scenario>.json

Режим «изображения»:
  Картинки:  content/<scenario>/images/review_images/scene_XX/vN.{jpg,png}
  Промпты:   content/<scenario>/prompts/images.md (опционально)
  Выбор:     webapp/selections/images_<scenario>.json

Режим «видео»:
  Клипы:     content/<scenario>/video/scene_XX_vN.mp4
  Промпты:   content/<scenario>/prompts/video.md
  Выбор:     webapp/selections/videos_<scenario>.json
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from flask import Flask, jsonify, request, send_from_directory, abort

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
SELECTIONS_DIR = Path(__file__).resolve().parent / "selections"
STATIC_DIR = Path(__file__).resolve().parent / "static"

SELECTIONS_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")


# ─── CORS для Chrome-расширения ────────────────────────────────────────────
# Расширение живёт на схеме chrome-extension://<id>, и при POST application/json
# браузер шлёт preflight OPTIONS. Разрешаем только chrome-extension://, чтобы
# не открывать webapp всему миру.

@app.before_request
def _ext_cors_preflight():
    if request.method != "OPTIONS":
        return None
    origin = request.headers.get("Origin", "")
    if not origin.startswith("chrome-extension://"):
        return None
    resp = app.make_default_options_response()
    resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.after_request
def _ext_cors_headers(response):
    origin = request.headers.get("Origin", "")
    if origin.startswith("chrome-extension://"):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def _dir_creation_time(p: Path) -> float:
    """Время создания папки сценария.

    На Windows `st_ctime` — это реально время создания. На macOS пытаемся
    взять `st_birthtime`, на Linux он отсутствует — fallback на `st_mtime`,
    что для папок content/ обычно близко к моменту добавления.
    """
    try:
        st = p.stat()
    except OSError:
        return 0.0
    return getattr(st, "st_birthtime", None) or st.st_ctime


def iter_scenarios_by_creation(content_dir: Path):
    """Итератор по папкам сценариев, отсортированным от самой старой к новой."""
    if not content_dir.exists():
        return []
    return sorted(
        (d for d in content_dir.iterdir() if d.is_dir()),
        key=_dir_creation_time,
    )


# ── parsing ────────────────────────────────────────────────────────────────

# Поддерживаем разные схемы именования:
#   scene_18_01.mp3       -> base: scene_18,       variant: 01
#   scene_01.mp3          -> base: scene_01,       variant: None
#   scene_00_intro.mp3    -> base: scene_00_intro, variant: None (слово в суффиксе)
#   sentence_001_v1.mp3   -> base: sentence_001,   variant: v1
#   sentence_001.mp3      -> base: sentence_001,   variant: None

# _v<digits> — явный вариант (для Сизифа)
VARIANT_V_RE = re.compile(r"^(?P<base>.+?)_v(?P<variant>\d+)$")
# <prefix>_<number>_<number> — числовой вариант (для Дедала)
VARIANT_NUM_RE = re.compile(
    r"^(?P<base>[a-zA-Zа-яА-Я]+_\d+(?:_[a-zA-Zа-яА-Я]+)?)_(?P<variant>\d+)$"
)


def parse_scene_filename(stem: str) -> tuple[str, str | None]:
    """Разбирает имя файла на (base, variant). variant=None если одиночный."""
    m = VARIANT_V_RE.match(stem)
    if m:
        return m.group("base"), "v" + m.group("variant")
    m = VARIANT_NUM_RE.match(stem)
    if m:
        return m.group("base"), m.group("variant")
    return stem, None


def scene_sort_key(base: str) -> tuple[int, str]:
    """Сортировка сцен по первому числу в имени базы."""
    m = re.search(r"\d+", base)
    num = int(m.group()) if m else 999
    return (num, base)


# Подпапки, которые не являются источниками вариантов для ревью
# (используются пайплайном сборки / финализации).
EXCLUDED_DIRS = {"approved_sentences", "scenes", "final", "outdated", "_preview"}


def discover_scenes(audio_dir: Path) -> dict[str, list[dict]]:
    """Рекурсивно находит все mp3 и группирует по сценам.

    Поддерживает любую вложенность:
      audio/scene_01.mp3                                       (плоская)
      audio/scene_18_01.mp3                                    (плоская с вариантом)
      audio/sentence_001/sentence_001_v1.mp3                   (подпапка = база)
      audio/review_sentences/sentence_001/sentence_001_v1.mp3  (группирующая папка)

    Правило: если mp3 лежит прямо в audio_dir — парсим имя файла;
    иначе база = имя непосредственного родителя файла.
    """
    scenes: dict[str, list[dict]] = {}

    for mp3 in audio_dir.rglob("*.mp3"):
        rel_path = mp3.relative_to(audio_dir).as_posix()
        # Пропускаем файлы, лежащие внутри служебных папок пайплайна
        if any(part in EXCLUDED_DIRS for part in mp3.relative_to(audio_dir).parts):
            continue
        if mp3.parent == audio_dir:
            # Плоская схема
            base, variant = parse_scene_filename(mp3.stem)
        else:
            # Вложенная: база = имя родительской папки
            base = mp3.parent.name
            _, variant = parse_scene_filename(mp3.stem)

        # Валидная база должна содержать хотя бы одну цифру (номер сцены).
        # Это отсеивает мусорные папки вроде 'sentences/X/t/*.mp3'.
        if not re.search(r"\d", base):
            continue

        scenes.setdefault(base, []).append({
            "filename": mp3.name,
            "path": rel_path,
            "variant": variant or "1",
            "size_kb": round(mp3.stat().st_size / 1024, 1),
        })

    return scenes


def find_text_for_scene(scenario_dir: Path, base: str) -> str:
    """Ищет текст сцены в нескольких местах."""
    candidates = [
        scenario_dir / "voiceover" / "texts" / f"{base}.txt",
        scenario_dir / "voiceover" / "audio" / base / f"{base}.txt",
        scenario_dir / "voiceover" / "audio" / f"{base}.txt",
    ]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    return ""


def discover_sentences_from_texts(scenario_dir: Path) -> list[str]:
    """Читает voiceover/texts/ и возвращает список base-имён (sentence_NNN).

    Используется как fallback, когда voiceover/audio/ ещё не создан
    (свежий сценарий, озвучки нет). Позволяет открыть ревью и запустить
    массовую генерацию прямо из UI — иначе сценарий бы 404-ил.
    """
    texts_dir = scenario_dir / "voiceover" / "texts"
    if not texts_dir.exists():
        return []
    bases: list[str] = []
    for txt in sorted(texts_dir.glob("*.txt")):
        base = txt.stem
        # Отсеиваем файлы без номера сцены (напр. служебные README)
        if not re.search(r"\d", base):
            continue
        bases.append(base)
    return bases


def load_selections(scenario: str) -> dict:
    path = SELECTIONS_DIR / f"{scenario}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_selections(scenario: str, data: dict) -> None:
    path = SELECTIONS_DIR / f"{scenario}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── published flag ──────────────────────────────────────────────────────────
#
# Флаг «опубликован» — общий для сценария (один на все режимы: озвучка /
# изображения / видео). Хранится отдельным файлом, чтобы не примешиваться к
# selections, которые специфичны для каждого режима. Содержимое:
#   {"published": true, "published_at": "2026-04-21T12:34:56"}
# Никаких ограничений в UI этот флаг не накладывает — это чисто визуальная
# отметка «миф уже выложен в TikTok / YouTube».


def _published_path(scenario: str) -> Path:
    return SELECTIONS_DIR / f"published_{scenario}.json"


def load_published_state(scenario: str) -> dict:
    path = _published_path(scenario)
    if not path.exists():
        return {"published": False, "published_at": None}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "published": bool(data.get("published")),
            "published_at": data.get("published_at"),
        }
    except Exception:
        return {"published": False, "published_at": None}


def save_published_state(scenario: str, on: bool) -> dict:
    path = _published_path(scenario)
    if on:
        data = {
            "published": True,
            "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return data
    # выключение — стираем файл, не оставляем мусор
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass
    return {"published": False, "published_at": None}


# ── approved_sentences ──────────────────────────────────────────────────────
#
# Папка `approved_sentences` — источник истины о том, какие варианты уже
# отобраны и зафиксированы. Файлы внутри именуются с суффиксом варианта:
#   sentence_001_v3.mp3  → база=sentence_001, вариант=v3
#   scene_01_02.mp3      → база=scene_01,     вариант=02
#
# Вариант сохраняется ЛИТЕРАЛЬНО в том виде, в каком его отдаёт
# discover_scenes, — чтобы сравнение `scene.approved === variant.variant`
# в UI всегда срабатывало без дополнительной нормализации.
#
# При запуске UI подтягивает отсюда {base: variant} и отмечает эти сцены
# как «одобренные», чтобы ревьюер видел свою предыдущую работу.

# Разделитель между базой и вариантом — последний `_`, справа либо `v<цифры>`,
# либо просто `<цифры>`.
APPROVED_FILE_RE = re.compile(r"^(?P<base>.+)_(?P<variant>v\d+|\d+)$")


def approved_filename(base: str, variant: str) -> str:
    """Имя файла в approved_sentences/ — база + _ + литеральный вариант."""
    return f"{base}_{variant}.mp3"


# ffmpeg / ffprobe — берутся из системного PATH. На рабочей машине лежат в
# external/ffmpeg/ffmpeg-8.1-full_build-shared/bin/ (этот каталог добавлен
# в PATH через переменные среды Windows).


def _find_ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def _find_ffprobe() -> str | None:
    """Ищет ffprobe в PATH. Используется для длительностей предложений в
    склейке «Песни целиком» — нужно фронту, чтобы сегменты плеера встали
    пропорционально и клик попадал ровно в начало sentence_NN."""
    return shutil.which("ffprobe")


def _audio_duration(path: Path) -> float | None:
    """Длительность mp3 в секундах через ffprobe. None — если не получилось."""
    ffprobe = _find_ffprobe()
    if not ffprobe:
        return None
    try:
        res = subprocess.run(
            [
                ffprobe, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if res.returncode != 0:
            return None
        return float(res.stdout.strip())
    except (ValueError, subprocess.SubprocessError, OSError):
        return None


def concat_approved_audio(approved_dir: Path, filenames: list[str]) -> tuple[Path | None, str | None]:
    """Склеивает отобранные mp3 в approved_dir/full.mp3 через ffmpeg concat.

    Возвращает (путь_к_файлу, None) при успехе или (None, сообщение_об_ошибке).
    """
    if not filenames:
        return None, "нет файлов для склейки"

    ffmpeg = _find_ffmpeg()
    if ffmpeg is None:
        return None, "ffmpeg не найден в PATH"

    # Сортируем по номеру сцены (sentence_001, sentence_002, …)
    def sort_key(name: str) -> tuple[int, str]:
        stem = Path(name).stem
        m = APPROVED_FILE_RE.match(stem)
        base = m.group("base") if m else stem
        return scene_sort_key(base)

    ordered = sorted(filenames, key=sort_key)

    list_file = approved_dir / "_concat_list.txt"
    out_file = approved_dir / "full.mp3"

    try:
        # ffmpeg concat требует экранирования одинарных кавычек в путях — у нас
        # только имена файлов без кавычек, так что просто оборачиваем.
        list_file.write_text(
            "\n".join(f"file '{name}'" for name in ordered) + "\n",
            encoding="utf-8",
        )

        # Сначала пробуем без перекодирования (быстро, без потерь качества).
        # ElevenLabs отдаёт одинаковые параметры mp3 для всех файлов, так что
        # обычно -c copy работает. Если упадёт — fallback на реэнкод.
        cmd_copy = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(out_file),
        ]
        res = subprocess.run(cmd_copy, capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            # Fallback: реэнкод в 192 kbps mp3 (одинаковый формат для всего).
            cmd_reencode = [
                ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-c:a", "libmp3lame", "-b:a", "192k",
                str(out_file),
            ]
            res = subprocess.run(cmd_reencode, capture_output=True, text=True, encoding="utf-8")
            if res.returncode != 0:
                return None, f"ffmpeg exit={res.returncode}: {res.stderr.strip()[:300]}"
        return out_file, None
    finally:
        list_file.unlink(missing_ok=True)


def concat_audio_to(out_file: Path, source_paths: list[Path]) -> tuple[Path | None, str | None]:
    """Склеивает source_paths в out_file через ffmpeg concat. Принимает абсолютные пути.

    Используется блоком «Песнь целиком» — собирает превью full.mp3 из текущих
    selections, не трогая approved_sentences/. Концепция:
      - approved_sentences/full.mp3 — финальная склейка, делается «Собрать финал»
      - voiceover/audio/_preview/full.mp3 — текущее превью, регенерится по требованию
    """
    if not source_paths:
        return None, "нет файлов для склейки"
    ffmpeg = _find_ffmpeg()
    if ffmpeg is None:
        return None, "ffmpeg не найден в PATH"

    out_file.parent.mkdir(parents=True, exist_ok=True)
    list_file = out_file.parent / "_concat_list.txt"
    try:
        # ffmpeg concat принимает абсолютные пути в `file '...'` — оборачиваем
        # одинарными кавычками. На Windows используем forward-slash через as_posix.
        list_file.write_text(
            "\n".join(f"file '{p.as_posix()}'" for p in source_paths) + "\n",
            encoding="utf-8",
        )
        cmd_copy = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(out_file),
        ]
        res = subprocess.run(cmd_copy, capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            cmd_reencode = [
                ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-c:a", "libmp3lame", "-b:a", "192k",
                str(out_file),
            ]
            res = subprocess.run(cmd_reencode, capture_output=True, text=True, encoding="utf-8")
            if res.returncode != 0:
                return None, f"ffmpeg exit={res.returncode}: {res.stderr.strip()[:300]}"
        return out_file, None
    finally:
        list_file.unlink(missing_ok=True)


def load_approved_sentences(scenario_dir: Path) -> dict[str, str]:
    """Читает approved_sentences/ сценария и возвращает {base: variant}.

    variant хранится в том же виде, что и в `discover_scenes` — либо `v1/v2/…`,
    либо `01/02/…`.
    """
    approved_dir = scenario_dir / "voiceover" / "audio" / "approved_sentences"
    if not approved_dir.exists():
        return {}
    result: dict[str, str] = {}
    for mp3 in approved_dir.glob("*.mp3"):
        m = APPROVED_FILE_RE.match(mp3.stem)
        if not m:
            # Старые файлы без версии — пропускаем, к варианту не привязаны
            continue
        result[m.group("base")] = m.group("variant")
    return result


# ── images: discovery, md parsing, selections ──────────────────────────────

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
# Имена файлов вида v1.jpg, v2.png, v10.webp
IMAGE_VARIANT_RE = re.compile(r"^v(\d+)$")
# Папки сцен: scene_01, scene_02, ...
IMAGE_SCENE_DIR_RE = re.compile(r"^scene_\d+$")


def discover_image_scenes(review_dir: Path) -> dict[str, list[dict]]:
    """Сканирует content/<миф>/images/review_images/ и группирует по сценам.

    Ожидаемая структура: review_images/scene_XX/vN.{jpg,png}.
    Возвращает {base: [{filename, variant, size_kb}, ...]}.
    """
    scenes: dict[str, list[dict]] = {}
    if not review_dir.exists():
        return scenes

    for scene_dir in sorted(review_dir.iterdir()):
        if not scene_dir.is_dir():
            continue
        if not IMAGE_SCENE_DIR_RE.match(scene_dir.name):
            continue
        variants: list[dict] = []
        for img in sorted(scene_dir.iterdir()):
            if img.suffix.lower() not in IMAGE_EXTS:
                continue
            m = IMAGE_VARIANT_RE.match(img.stem)
            if not m:
                continue
            variants.append({
                "filename": img.name,
                "variant": "v" + m.group(1),
                "size_kb": round(img.stat().st_size / 1024, 1),
            })
        if variants:
            # Сортируем варианты по номеру (v1, v2, v10 — не лексикографически)
            variants.sort(key=lambda v: int(v["variant"][1:]))
            scenes[scene_dir.name] = variants
    return scenes


def parse_images_md(md_path: Path) -> dict[str, dict]:
    """Парсит content/<миф>/prompts/images.md в {scene_01: {text, prompt}}.

    Формат блока (из imagefx_runner.py):
        ## Сцена 1
        **Текст:** ...
        **Промпт:** ...
    """
    if not md_path.exists():
        return {}
    content = md_path.read_text(encoding="utf-8")
    # re.split с захватом номера: [prefix, '1', block1, '2', block2, ...]
    # Разрешаем хвост после номера — например, «## Сцена 1 (sent_001)».
    parts = re.split(r"^##\s+Сцена\s+(\d+)[^\n]*$", content, flags=re.MULTILINE)
    result: dict[str, dict] = {}
    for i in range(1, len(parts), 2):
        try:
            num = int(parts[i])
        except ValueError:
            continue
        block = parts[i + 1] if i + 1 < len(parts) else ""
        text_m = re.search(
            r"\*\*Текст:\*\*\s*(.+?)(?=\n\n|\*\*Промпт:\*\*|\Z)", block, re.DOTALL
        )
        prompt_m = re.search(
            r"\*\*Промпт:\*\*\s*(.+?)(?=\n##|\Z)", block, re.DOTALL
        )
        result[f"scene_{num:02d}"] = {
            "text": text_m.group(1).strip() if text_m else "",
            "prompt": prompt_m.group(1).strip() if prompt_m else "",
        }
    return result


def load_image_selections(scenario: str) -> dict:
    path = SELECTIONS_DIR / f"images_{scenario}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_image_selections(scenario: str, data: dict) -> None:
    path = SELECTIONS_DIR / f"images_{scenario}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_approved_images(scenario_dir: Path) -> dict[str, str]:
    """Читает content/<миф>/images/approved_images/ и возвращает {base: variant}.

    Файлы именуются как в approved_sentences: scene_01_v2.jpg, scene_18_v3.png.
    variant хранится в том же виде, что отдаёт discover_image_scenes (v1/v2/…).
    """
    approved_dir = scenario_dir / "images" / "approved_images"
    if not approved_dir.exists():
        return {}
    result: dict[str, str] = {}
    for img in approved_dir.iterdir():
        if img.suffix.lower() not in IMAGE_EXTS:
            continue
        m = APPROVED_FILE_RE.match(img.stem)
        if not m:
            continue
        result[m.group("base")] = m.group("variant")
    return result


def image_scenario_status(scenes: dict, selections: dict, approved: dict) -> tuple[int, int, int, str]:
    """Считает done/regen/pending и общий статус сценария.

    Логика повторяет voiceover: сцена done если есть approved вариант ИЛИ
    явный selections[base]; regen — только если явно отмечено.
    """
    done = regen = 0
    for base in scenes.keys():
        explicit_status = selections.get(f"{base}::status")
        if explicit_status == "regen":
            regen += 1
            continue
        if explicit_status == "done":
            done += 1
            continue
        # Неявный статус: done если approved или выбран
        if approved.get(base) or selections.get(base):
            done += 1
    total = len(scenes)
    pending = total - done - regen
    if total == 0:
        s = "wip"
    elif done == total and regen == 0:
        s = "ready"
    elif done > 0 or regen > 0:
        s = "in_progress"
    else:
        s = "new"
    return done, regen, pending, s


def approved_image_filename(base: str, variant: str, ext: str) -> str:
    """Имя файла в approved_images/ — база + _ + вариант + расширение."""
    return f"{base}_{variant}{ext}"


# ── routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")


@app.route("/api/scenarios")
def api_scenarios():
    """Список сценариев (отсортирован от самого старого к новому)."""
    scenarios = []
    for d in iter_scenarios_by_creation(CONTENT_DIR):
        if (d / "voiceover" / "audio").exists():
            scenarios.append(d.name)
    return jsonify(scenarios)


@app.route("/api/scenarios-summary")
def api_scenarios_summary():
    """Список сценариев со статистикой для страницы выбора мифа.

    Сортировка — по времени создания папки сценария, от самой старой к новой.
    """
    result = []
    for d in iter_scenarios_by_creation(CONTENT_DIR):
        audio_dir = d / "voiceover" / "audio"
        texts_dir = d / "voiceover" / "texts"

        if not audio_dir.exists() and not texts_dir.exists():
            # Ни озвучки, ни разбиения текста — сценарий ещё совсем сырой
            continue

        pub = load_published_state(d.name)

        if not audio_dir.exists():
            # Озвучки нет, но текст уже разбит на предложения — показываем
            # как WIP с количеством сцен из texts/. Это нужно, чтобы
            # пользователь мог зайти в ревью и нажать «Озвучить всё».
            text_bases = discover_sentences_from_texts(d)
            result.append({
                "name": d.name,
                "display_name": d.name,
                "scene_count": len(text_bases),
                "done": 0,
                "regen": 0,
                "pending": len(text_bases),
                "approved_count": 0,
                "variants_total": 0,
                "status": "new" if text_bases else "wip",
                "published": pub["published"],
                "published_at": pub["published_at"],
            })
            continue

        raw_scenes = discover_scenes(audio_dir)
        # Подмешиваем базы из texts/ — чтобы счётчик показывал реальный
        # объём сценария даже до запуска первой генерации
        for tb in discover_sentences_from_texts(d):
            raw_scenes.setdefault(tb, [])
        selections = load_selections(d.name)
        approved = load_approved_sentences(d)

        scene_count = len(raw_scenes)
        variants_total = sum(len(v) for v in raw_scenes.values())

        done = regen = 0
        for base in raw_scenes.keys():
            approved_variant = approved.get(base)
            status = selections.get(f"{base}::status")
            if status is None:
                status = "done" if approved_variant else "pending"
            if status == "done":
                done += 1
            elif status == "regen":
                regen += 1
        pending = scene_count - done - regen

        if scene_count == 0:
            scenario_status = "wip"
        elif done == scene_count and regen == 0:
            scenario_status = "ready"
        elif done > 0 or regen > 0:
            scenario_status = "in_progress"
        else:
            scenario_status = "new"

        result.append({
            "name": d.name,
            "display_name": d.name,
            "scene_count": scene_count,
            "done": done,
            "regen": regen,
            "pending": pending,
            "approved_count": len(approved),
            "variants_total": variants_total,
            "status": scenario_status,
            "published": pub["published"],
            "published_at": pub["published_at"],
        })

    return jsonify(result)


@app.route("/api/scenes/<path:scenario>")
def api_scenes(scenario: str):
    """Список сцен с вариантами озвучки и текстом.

    Источники сцен объединяются:
      1. voiceover/audio/ — уже сгенерированные mp3 (с вариантами)
      2. voiceover/texts/ — sentence_NNN.txt файлы (как потенциальные сцены)

    Это позволяет открыть ревью свежего сценария, в котором ещё нет ни одного
    mp3, и запустить массовую генерацию через кнопку «Озвучить всё».
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    audio_dir = scenario_dir / "voiceover" / "audio"

    # Если нет ни audio, ни texts — считаем что сценария не существует
    if not audio_dir.exists() and not (scenario_dir / "voiceover" / "texts").exists():
        abort(404, description=f"Ни audio/, ни texts/ не найдены для {scenario!r}")

    raw_scenes = discover_scenes(audio_dir) if audio_dir.exists() else {}
    # Подмешиваем сцены из texts/ — для тех баз, у которых ещё нет mp3
    for base in discover_sentences_from_texts(scenario_dir):
        raw_scenes.setdefault(base, [])

    selections = load_selections(scenario)
    approved = load_approved_sentences(scenario_dir)

    result = []
    for base in sorted(raw_scenes.keys(), key=scene_sort_key):
        variants = sorted(raw_scenes[base], key=lambda v: v["variant"])
        approved_variant = approved.get(base)
        # Выбор: явный из selections.json имеет приоритет, иначе — одобренный
        selected = selections.get(base, approved_variant)
        # Статус: explicit override → selections; иначе done при approved; иначе pending
        status = selections.get(f"{base}::status")
        if status is None:
            status = "done" if approved_variant else "pending"
        result.append({
            "base": base,
            "variants": variants,
            "text": find_text_for_scene(scenario_dir, base),
            "selected": selected,
            "approved": approved_variant,
            "status": status,
        })

    return jsonify({
        "scenario": scenario,
        "scenes": result,
    })


@app.route("/audio/<path:scenario>/<path:filename>")
def audio_file(scenario: str, filename: str):
    """Отдаёт mp3. filename может быть вложенным: 'sentence_001/sentence_001_v1.mp3'.

    После перегенерации имя mp3 остаётся тем же (sentence_009_v1.mp3), но
    контент меняется — без no-cache браузер отдаёт старую озвучку из кеша
    и создаётся впечатление, что «перегенерация не сработала». Ставим
    no-cache + must-revalidate: браузер каждый раз спрашивает сервер, и
    при изменении mtime получает свежие байты.
    """
    scenario = unquote(scenario)
    audio_dir = CONTENT_DIR / scenario / "voiceover" / "audio"
    if not audio_dir.exists():
        abort(404)
    # send_from_directory безопасно защищает от path traversal
    resp = send_from_directory(str(audio_dir), filename, conditional=True)
    resp.headers["Cache-Control"] = "no-cache, must-revalidate"
    return resp


@app.route("/api/select/<path:scenario>", methods=["POST"])
def api_select(scenario: str):
    """Сохраняет выбор варианта для сцены."""
    scenario = unquote(scenario)
    data = request.get_json(force=True)
    base = data.get("base")
    variant = data.get("variant")  # None → снять выбор
    if not base:
        abort(400, "base is required")

    selections = load_selections(scenario)
    if variant is None:
        selections.pop(base, None)
        selections.pop(f"{base}::status", None)
    else:
        selections[base] = variant
        selections[f"{base}::status"] = "done"
    save_selections(scenario, selections)
    return jsonify({"ok": True})


# ── CosyVoice3 regeneration ────────────────────────────────────────────────
#
# Параметры по умолчанию, которые UI показывает пользователю в toast.
# Пользователь задал их явно: речь синтезируем с клонированием голоса из
# content/Ящик Пандоры/TTS.mp3, скорость 1.0, 10 вариантов.
COSYVOICE_MODEL_NAME = "Fun-CosyVoice3-0.5B"
COSYVOICE_DEFAULT_SPEED = 1.0
COSYVOICE_DEFAULT_VARIANTS = 10
COSYVOICE_PROMPT_WAV = CONTENT_DIR / "Ящик Пандоры" / "TTS.mp3"
COSYVOICE_PROMPT_TXT = CONTENT_DIR / "Ящик Пандоры" / "TTS.txt"
COSYVOICE_RUNNER = ROOT / "automation" / "cosyvoice_runner.py"


def cosyvoice_out_dir(scenario: str, base: str) -> Path:
    """Путь к папке вариантов CosyVoice для сцены.

    Изменение от предыдущей логики: всё кладём в review_sentences/<base>/,
    чтобы legacy-файлы от ElevenLabs (лежат прямо в audio/) не смешивались
    с новыми CosyVoice-вариантами.
    """
    return CONTENT_DIR / scenario / "voiceover" / "audio" / "review_sentences" / base


@app.route("/api/regenerate-cosyvoice/<path:scenario>", methods=["POST"])
def api_regenerate_cosyvoice(scenario: str):
    """Запускает CosyVoice3 для перегенерации 10 вариантов озвучки сцены.

    Шаги:
      1. Читает текст сцены из voiceover/texts/<base>.txt (или соседних путей).
      2. Спавнит automation/cosyvoice_runner.py как subprocess в фоне
         (Popen — UI не ждёт окончания).
      3. Помечает сцену как `regen` в selections, чтобы прогресс-бар
         ревью отражал перегенерацию.
      4. Возвращает параметры генерации — фронт показывает их в toast.
    """
    scenario = unquote(scenario)
    data = request.get_json(force=True)
    base = data.get("base")
    if not base:
        abort(400, "base is required")

    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.exists():
        abort(404, f"Сценарий {scenario!r} не найден")

    text = find_text_for_scene(scenario_dir, base)
    if not text:
        # Fallback: используем data.text если прилетел с фронта
        text = (data.get("text") or "").strip()
    if not text:
        abort(400, f"Не нашёл текст сцены {base!r} — нечего озвучивать")

    # Проверки файлов prompt — пользовательские, явные.
    if not COSYVOICE_PROMPT_WAV.exists():
        abort(500, f"Нет prompt-wav: {COSYVOICE_PROMPT_WAV}")
    if not COSYVOICE_PROMPT_TXT.exists():
        abort(500, f"Нет prompt-txt: {COSYVOICE_PROMPT_TXT}")

    variants = int(data.get("variants") or COSYVOICE_DEFAULT_VARIANTS)
    speed = float(data.get("speed") or COSYVOICE_DEFAULT_SPEED)

    # Если у пользователя CosyVoice живёт в отдельном venv (torch, torchaudio,
    # cosyvoice — тяжёлые, ставить в Flask'овский Python не хочется), позволяем
    # переопределить интерпретатор через переменную окружения.
    # Порядок поиска: ENV > стандартный user-venv > sys.executable (fallback).
    default_venv = Path.home() / "cosyvoice-venv" / "Scripts" / "python.exe"
    env_val = os.environ.get("COSYVOICE_PYTHON")
    if env_val and Path(env_val).exists():
        python_exe = env_val
    elif default_venv.exists():
        python_exe = str(default_venv)
    else:
        python_exe = sys.executable

    cmd = [
        python_exe,
        str(COSYVOICE_RUNNER),
        "--scenario", scenario,
        "--base", base,
        "--text", text,
        "--variants", str(variants),
        "--speed", str(speed),
        "--prompt-wav", str(COSYVOICE_PROMPT_WAV),
        "--prompt-text", str(COSYVOICE_PROMPT_TXT),
    ]

    # UTF-8 в stdout — иначе на Windows в логе будут кракозябры cp1251.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

    # Логи runner'а складываем рядом с выходной папкой (там же, где кладутся
    # сами варианты): audio/review_sentences/<base>/.
    # Чистим предыдущий лог и отчёт, чтобы прогресс-бар не путался
    # с остатками прошлого прогона. Сами mp3-варианты НЕ трогаем —
    # runner сам переместит их в outdated/<ts>/ перед новой генерацией.
    log_dir = cosyvoice_out_dir(scenario, base)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "_cosyvoice_runner.log"
    report_path = log_dir / "_cosyvoice_report.json"
    log_path.unlink(missing_ok=True)
    report_path.unlink(missing_ok=True)

    # Сбрасываем одобренный вариант для этой сцены: старый approved-файл
    # (например, sentence_009_v2.mp3) соответствовал ПРЕДЫДУЩЕЙ озвучке.
    # Новые варианты с теми же именами _vN имеют уже другое содержимое, и
    # зафиксированный approved становится устаревшим. Убираем его, чтобы
    # после перегенерации пользователь выбирал заново, а UI не подсвечивал
    # «★ Одобрено» на варианте, который физически лежит в другом файле.
    #
    # На Windows файл может быть занят браузером (HTML5 <audio> держит
    # handle на mp3, который сейчас играется). В этом случае unlink падает
    # с PermissionError [WinError 32]. Делаем 3 попытки с короткой паузой
    # (фронт стопит плеер перед запросом, но IO браузера — не мгновенный),
    # а если всё равно занят — игнорируем: задача endpoint'а — запустить
    # перегенерацию, а старый approved всё равно перезапишется при следующем
    # finalize. Сцена в любом случае помечается как 'regen' в selections,
    # звёздочка в UI снимется через ответ.
    approved_dir = scenario_dir / "voiceover" / "audio" / "approved_sentences"
    if approved_dir.exists():
        stuck = []
        for old in list(approved_dir.glob(f"{base}_*.mp3")) + list(approved_dir.glob(f"{base}.mp3")):
            for attempt in range(3):
                try:
                    old.unlink(missing_ok=True)
                    break
                except PermissionError:
                    if attempt == 2:
                        stuck.append(old.name)
                    else:
                        time.sleep(0.15)
        if stuck:
            print(f"[cosyvoice] approved-файлы заняты, оставлены до finalize: {stuck}")
    log_file = open(log_path, "ab")  # noqa: SIM115 — держим открытым для subprocess

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=str(ROOT),
            env=env,
            creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP
                if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP") else 0
            ),
        )
        pid = proc.pid
    except Exception as e:
        log_file.close()
        abort(500, f"Не удалось запустить cosyvoice_runner: {e}")

    # Помечаем сцену как regen в selections — ревью покажет оранжевый статус.
    selections = load_selections(scenario)
    selections.pop(base, None)
    selections[f"{base}::status"] = "regen"
    save_selections(scenario, selections)

    print(
        f"[cosyvoice] PID={pid} scenario={scenario!r} base={base!r} "
        f"variants={variants} speed={speed} log={log_path.name}"
    )

    return jsonify({
        "ok": True,
        "pid": pid,
        "python_exe": python_exe,
        "python_from_env": bool(os.environ.get("COSYVOICE_PYTHON")),
        "model": COSYVOICE_MODEL_NAME,
        "variants": variants,
        "speed": speed,
        "prompt_wav": str(COSYVOICE_PROMPT_WAV.relative_to(ROOT)),
        "prompt_text_file": str(COSYVOICE_PROMPT_TXT.relative_to(ROOT)),
        "prompt_text_preview": COSYVOICE_PROMPT_TXT.read_text(encoding="utf-8").strip()[:120],
        "text_preview": text[:120],
        "log_file": str(log_path.relative_to(ROOT)),
        "out_dir": f"content/{scenario}/voiceover/audio/{base}",
        "message": (
            f"CosyVoice3: {variants} вариантов, скорость {speed}, "
            f"клонирование голоса из {COSYVOICE_PROMPT_WAV.name}"
        ),
    })


@app.route("/api/cosyvoice-active/<path:scenario>")
def api_cosyvoice_active(scenario: str):
    """Список сцен сценария, где есть следы запуска CosyVoice (log есть).

    Фронт использует при открытии сценария, чтобы отметить в сайдбаре
    те сцены, у которых идёт / недавно шла перегенерация, — иначе после
    перезагрузки страницы пользователь не понимает, где что.

    Возвращает {base: {done, produced, requested, failed, stale_sec}}.
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    # CosyVoice теперь кладёт всё в review_sentences/<base>/.
    # Но оставляем fallback на audio/<base>/ — там могут висеть
    # artefact'ы прошлых запусков до этого рефакторинга.
    search_dirs = [
        scenario_dir / "voiceover" / "audio" / "review_sentences",
        scenario_dir / "voiceover" / "audio",
    ]

    result: dict[str, dict] = {}
    now_ts = datetime.now().timestamp()

    scanned = set()  # не обрабатываем одну и ту же base дважды
    for audio_dir in search_dirs:
        if not audio_dir.exists():
            continue
        for child in audio_dir.iterdir():
            if not child.is_dir():
                continue
            if child.name in scanned:
                continue
            if child.name in EXCLUDED_DIRS:
                continue
            log_path = child / "_cosyvoice_runner.log"
            report_path = child / "_cosyvoice_report.json"
            if not log_path.exists() and not report_path.exists():
                continue
            scanned.add(child.name)

            report = None
            if report_path.exists():
                try:
                    report = json.loads(report_path.read_text(encoding="utf-8"))
                except Exception:
                    report = {"error": "bad json"}

            produced = len(list(child.glob(f"{child.name}_v*.mp3")))
            requested = (report or {}).get("variants_requested", COSYVOICE_DEFAULT_VARIANTS)

            failed = False
            stale_sec = 0.0
            if log_path.exists() and report is None:
                try:
                    tail = log_path.read_bytes()[-4096:].decode("utf-8", errors="replace")
                    stale_sec = now_ts - log_path.stat().st_mtime
                    if ("Traceback" in tail or "ModuleNotFoundError" in tail
                            or "ОТСУТСТВУЮТ ЗАВИСИМОСТИ" in tail) and stale_sec > 10:
                        failed = True
                except Exception:
                    pass

            # Слишком старые failed-логи (>10 мин) — это мусор от предыдущих запусков,
            # в sidebar их не показываем, иначе красный «!» висит вечно.
            if failed and stale_sec > 600:
                continue

            result[child.name] = {
                "done": report is not None and "error" not in report,
                "produced": produced,
                "requested": requested,
                "failed": failed,
                "log_mtime": log_path.stat().st_mtime if log_path.exists() else 0,
            }

    return jsonify(result)


@app.route("/api/cosyvoice-clear/<path:scenario>/<path:base>", methods=["POST"])
def api_cosyvoice_clear(scenario: str, base: str):
    """Сносит мусорные следы CosyVoice-прогона для сцены.

    Нужно, когда на диске остался старый лог с traceback от упавшего runner'а,
    и в sidebar висит красный «!» на сцене, хотя процесса давно нет. Удаляем
    log, report и сам selections-флаг `regen`, чтобы UI пришёл в чистое
    состояние без повторной генерации. Сами mp3-варианты не трогаем.
    """
    scenario = unquote(scenario)
    base = unquote(base)
    out_dir = cosyvoice_out_dir(scenario, base)

    cleared = []
    for name in ("_cosyvoice_runner.log", "_cosyvoice_report.json"):
        p = out_dir / name
        if p.exists():
            p.unlink(missing_ok=True)
            cleared.append(name)

    # Снимаем status=regen, если никакой фактической перегенерации не было
    selections = load_selections(scenario)
    if selections.get(f"{base}::status") == "regen":
        selections.pop(f"{base}::status", None)
        save_selections(scenario, selections)
        cleared.append("selections::status")

    return jsonify({"ok": True, "cleared": cleared})


@app.route("/api/cosyvoice-status/<path:scenario>/<path:base>")
def api_cosyvoice_status(scenario: str, base: str):
    """Прогресс генерации CosyVoice3 для конкретной сцены.

    Читает:
      - _cosyvoice_report.json — если существует, значит runner дошёл до конца
      - _cosyvoice_runner.log  — хвост stdout+stderr для отображения в UI
      - {base}_v*.mp3          — сколько вариантов уже собрано (быстрый счётчик)

    Возвращает JSON, который фронт поллит каждые 1.5 сек:
      { exists, done, produced, requested, log_tail, log_mtime, report, error_hint }
    """
    scenario = unquote(scenario)
    base = unquote(base)
    out_dir = cosyvoice_out_dir(scenario, base)

    if not out_dir.exists():
        return jsonify({"exists": False, "done": False, "produced": 0, "requested": 10,
                        "log_tail": "", "report": None, "error_hint": None})

    report_path = out_dir / "_cosyvoice_report.json"
    log_path = out_dir / "_cosyvoice_runner.log"

    produced_files = sorted(out_dir.glob(f"{base}_v*.mp3"))
    produced_count = len(produced_files)

    report = None
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception as e:
            report = {"error": f"не смог прочитать отчёт: {e}"}

    log_tail = ""
    log_mtime = 0.0
    if log_path.exists():
        try:
            raw = log_path.read_bytes()
            log_tail = raw[-6000:].decode("utf-8", errors="replace")
            log_mtime = log_path.stat().st_mtime
        except Exception:
            pass

    now_ts = datetime.now().timestamp()
    # Эвристика ошибки: в логе явный traceback / наш preflight с exit-кодом,
    # либо log давно не обновлялся и отчёта нет (процесс умер без следа).
    error_hint = None
    if report is None and log_tail:
        for marker in (
            "Traceback (most recent call last)", "ModuleNotFoundError",
            "ImportError", "FileNotFoundError", "OSError", "RuntimeError",
            "ОТСУТСТВУЮТ ЗАВИСИМОСТИ",  # наш preflight
        ):
            if marker in log_tail:
                error_hint = marker
                break
        if error_hint is None and log_mtime:
            silence_sec = now_ts - log_mtime
            if silence_sec > 30:
                error_hint = f"no log activity ({int(silence_sec)}s)"

    requested = (report or {}).get("variants_requested", COSYVOICE_DEFAULT_VARIANTS)
    return jsonify({
        "exists": True,
        "done": report is not None and "error" not in report,
        "produced": produced_count,
        "requested": requested,
        "log_tail": log_tail,
        "log_mtime": log_mtime,
        "report": report,
        "error_hint": error_hint,
    })


@app.route("/api/regenerate-elevenlabs/<path:scenario>", methods=["POST"])
def api_regenerate_elevenlabs(scenario: str):
    """Заглушка: прямой запуск перегенерации через ElevenLabs API.
    В будущем — вызов elevenlabs_runner.py для этой сцены.
    """
    scenario = unquote(scenario)
    data = request.get_json(force=True)
    base = data.get("base")
    if not base:
        abort(400, "base is required")

    # TODO: subprocess.run(["python", "automation/elevenlabs_runner.py", "--scenario", scenario, "--sentence", base])
    print(f"[STUB] Прямая перегенерация ElevenLabs: {scenario} / {base}")

    return jsonify({
        "ok": True,
        "stub": True,
        "message": f"Запрос на озвучку {base} отправлен в ElevenLabs (заглушка)",
    })


@app.route("/api/regenerate/<path:scenario>", methods=["POST"])
def api_regenerate(scenario: str):
    """Заглушка: помечает сцену на перегенерацию."""
    scenario = unquote(scenario)
    data = request.get_json(force=True)
    base = data.get("base")
    if not base:
        abort(400, "base is required")

    selections = load_selections(scenario)
    selections.pop(base, None)
    selections[f"{base}::status"] = "regen"
    save_selections(scenario, selections)

    # TODO: здесь будет вызов перегенерации текста + ElevenLabs
    print(f"[STUB] Запрошена перегенерация сцены {base} в сценарии {scenario}")

    return jsonify({
        "ok": True,
        "stub": True,
        "message": f"Сцена {base} отправлена на перегенерацию (заглушка)",
    })


@app.route("/api/finalize/<path:scenario>", methods=["POST"])
def api_finalize(scenario: str):
    """Копирует выбранные озвучки в approved_sentences/<base>.mp3.
    Для сцен без выбора — записывает их в regen-список (заглушка пайплайна перегенерации).
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    audio_dir = scenario_dir / "voiceover" / "audio"
    approved_dir = audio_dir / "approved_sentences"
    approved_dir.mkdir(parents=True, exist_ok=True)

    selections = load_selections(scenario)
    chosen = {k: v for k, v in selections.items() if not k.endswith("::status")}
    regen_list = [
        k.replace("::status", "")
        for k, v in selections.items()
        if k.endswith("::status") and v == "regen"
    ]

    # Индекс {(base, variant): path} из discovery
    raw_scenes = discover_scenes(audio_dir)
    variant_index: dict[tuple[str, str], str] = {}
    for base, variants in raw_scenes.items():
        for v in variants:
            variant_index[(base, v["variant"])] = v["path"]

    copied: list[str] = []
    missing: list[str] = []

    stuck_files: list[str] = []
    for base, variant in chosen.items():
        rel = variant_index.get((base, variant))
        if rel is None:
            missing.append(f"{base}/{variant}")
            continue
        src = audio_dir / rel
        # Удаляем ранее одобренные версии этой же базы, чтобы не копилось
        # (sentence_001_v1.mp3 + sentence_001_v3.mp3 одновременно), а также
        # legacy-файлы без суффикса версии (sentence_001.mp3).
        #
        # На Windows файл может быть занят браузером (HTML5 <audio> держит
        # open handle на проигрываемый mp3) — unlink падает с PermissionError
        # [WinError 32]. 3 попытки с короткой паузой; если всё равно занят,
        # пропускаем — это означает, что юзер играет именно тот файл, и он
        # будет перезаписан shutil.copy2 ниже (если имя совпадёт) или останется
        # как stale-копия, которую можно удалить вручную после finalize.
        dst_name = approved_filename(base, variant)
        for old in list(approved_dir.glob(f"{base}_*.mp3")) + list(approved_dir.glob(f"{base}.mp3")):
            if old.name == dst_name:
                # Не удаляем тот же файл, что собираемся записать — copy2 его
                # перезапишет. Это типичный случай: юзер играет sentence_001_v3.mp3,
                # одобрил v3, finalize пытается удалить v3 чтобы потом скопировать v3.
                continue
            for attempt in range(3):
                try:
                    old.unlink(missing_ok=True)
                    break
                except PermissionError:
                    if attempt == 2:
                        stuck_files.append(old.name)
                    else:
                        time.sleep(0.15)
        dst = approved_dir / dst_name
        try:
            shutil.copy2(src, dst)
            copied.append(dst.name)
        except PermissionError:
            # dst занят (браузер играет именно его) — не валим весь finalize.
            stuck_files.append(dst.name)
    if stuck_files:
        print(f"[FINALIZE] approved-файлы заняты, пропущены: {stuck_files}")

    # Склейка: берём ВСЕ mp3 из approved_dir (включая ранее одобренные,
    # которых нет в текущем `copied`, — это нужно если пользователь в этом
    # заходе что-то добавил/перевыбрал, а остальное уже было).
    all_approved = sorted(p.name for p in approved_dir.glob("*.mp3") if p.name != "full.mp3")
    full_path, concat_error = concat_approved_audio(approved_dir, all_approved)

    # Отчёт в selections/
    final_path = SELECTIONS_DIR / f"{scenario}__FINAL.json"
    final_path.write_text(
        json.dumps({
            "scenario": scenario,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "approved_folder": str(approved_dir),
            "copied": copied,
            "missing": missing,
            "to_regenerate": regen_list,
            "full_audio": full_path.name if full_path else None,
            "concat_error": concat_error,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[FINALIZE] Скопировано {len(copied)} файлов в {approved_dir}")
    if missing:
        print(f"[FINALIZE] Не найдены варианты: {missing}")
    if full_path:
        print(f"[FINALIZE] Склейка: {full_path}")
    elif concat_error:
        print(f"[FINALIZE] Склейка не удалась: {concat_error}")
    print(f"[STUB] Перегенерация для сцен: {regen_list}")

    return jsonify({
        "ok": True,
        "approved_dir": str(approved_dir.relative_to(ROOT)),
        "copied_count": len(copied),
        "missing": missing,
        "regen_count": len(regen_list),
        "full_audio": full_path.name if full_path else None,
        "concat_error": concat_error,
    })


@app.route("/api/full-preview/<path:scenario>", methods=["POST"])
def api_full_preview(scenario: str):
    """Склеивает full.mp3 из текущих selections без копирования в approved_sentences.

    Используется блоком «Песнь целиком» в сайдбаре — пользователь после
    ревью всех сцен слушает озвучку целиком, чтобы оценить ритм и интонацию
    перед монтажом. Файл живёт в `voiceover/audio/_preview/full.mp3` и
    перегенерится по требованию.

    Возвращает 400, если хотя бы для одной сцены нет выбора (selection /
    approved). Это сигнал UI «ещё не все сцены отревьюены».
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    audio_dir = scenario_dir / "voiceover" / "audio"
    if not audio_dir.exists():
        abort(404, f"Нет {audio_dir.relative_to(ROOT)}")

    selections = load_selections(scenario)
    approved = load_approved_sentences(scenario_dir)

    raw_scenes = discover_scenes(audio_dir)
    variant_index: dict[tuple[str, str], str] = {}
    for base, variants in raw_scenes.items():
        for v in variants:
            variant_index[(base, v["variant"])] = v["path"]

    # Маппинг scene → выбранный файл. Приоритет: явный selections > approved.
    bases = sorted(raw_scenes.keys(), key=scene_sort_key)
    sources: list[Path] = []
    missing: list[str] = []
    for base in bases:
        # Сцены, помеченные на регенерацию, считаем «не готовыми»
        if selections.get(f"{base}::status") == "regen":
            missing.append(base)
            continue
        variant = selections.get(base) or approved.get(base)
        if not variant:
            missing.append(base)
            continue
        rel = variant_index.get((base, variant))
        if rel is None:
            missing.append(f"{base}/{variant}")
            continue
        sources.append(audio_dir / rel)

    if missing:
        return jsonify({
            "ok": False,
            "error": "Не все сцены отревьюены",
            "missing": missing,
        }), 400

    preview_dir = audio_dir / "_preview"
    out_file = preview_dir / "full.mp3"
    full_path, err = concat_audio_to(out_file, sources)
    if err:
        return jsonify({"ok": False, "error": err}), 500

    # Замеряем длительность каждого исходника — фронту нужны реальные тайминги,
    # чтобы сегменты в плеере были пропорциональны и клик попадал ровно
    # в начало sentence_NN. Если ffprobe недоступен (sentence_starts == None),
    # фронт деградирует на равномерную сетку.
    durations: list[float] | None = []
    for src in sources:
        d = _audio_duration(src)
        if d is None:
            durations = None
            break
        durations.append(round(d, 3))

    starts: list[float] | None = None
    total_duration: float | None = None
    if durations is not None:
        starts = []
        acc = 0.0
        for d in durations:
            starts.append(round(acc, 3))
            acc += d
        total_duration = round(acc, 3)

    mtime = int(full_path.stat().st_mtime)
    return jsonify({
        "ok": True,
        # cache-buster через mtime, чтобы браузер не отдал старую склейку
        "url": f"/audio/{scenario}/_preview/full.mp3?t={mtime}",
        "size_kb": round(full_path.stat().st_size / 1024, 1),
        "sentence_count": len(sources),
        "sentence_starts": starts,
        "sentence_durations": durations,
        "total_duration": total_duration,
    })


# ── routes: изображения ────────────────────────────────────────────────────

@app.route("/api/images/myths")
def api_images_myths():
    """Список мифов для хаба ревью изображений.

    Показываем сценарий если есть хоть одно из:
      - `images/review_images/` (уже сгенерированы картинки)
      - `prompts/images.md` (промпты есть, можно запустить Flow)

    Без второго условия новые сценарии вроде «Мидас» не появлялись бы в хабе,
    пока пользователь сам не создал review_images/ вручную.

    Сортировка — по времени создания папки сценария, от самой старой к новой.
    """
    result = []
    for d in iter_scenarios_by_creation(CONTENT_DIR):
        review_dir = d / "images" / "review_images"
        images_md = d / "prompts" / "images.md"

        if not review_dir.exists() and not images_md.exists():
            continue

        pub = load_published_state(d.name)

        if not review_dir.exists():
            # Есть промпты, но картинок ещё нет — показываем как NEW с числом
            # сцен из markdown, чтобы пользователь мог зайти и нажать batch.
            md_data = parse_images_md(images_md)
            scene_count = len(md_data) if md_data else 0
            result.append({
                "name": d.name,
                "display_name": d.name,
                "scene_count": scene_count,
                "done": 0,
                "regen": 0,
                "pending": scene_count,
                "approved_count": 0,
                "variants_total": 0,
                "status": "new" if scene_count else "wip",
                "published": pub["published"],
                "published_at": pub["published_at"],
            })
            continue

        scenes = discover_image_scenes(review_dir)
        # Если review_images/ есть, но пуста (так бывает — webapp создаёт
        # её при первой попытке генерации для marker-файла), дополняем
        # список сцен из prompts/images.md. Иначе scene_count=0 и
        # пользователь не может войти в ревью.
        if images_md.exists():
            md_data = parse_images_md(images_md)
            for base in md_data:
                scenes.setdefault(base, [])
        selections = load_image_selections(d.name)
        approved = load_approved_images(d)
        done, regen, pending, status = image_scenario_status(scenes, selections, approved)
        variants_total = sum(len(v) for v in scenes.values())

        result.append({
            "name": d.name,
            "display_name": d.name,
            "scene_count": len(scenes),
            "done": done,
            "regen": regen,
            "pending": pending,
            "approved_count": len(approved),
            "variants_total": variants_total,
            "status": status,
            "published": pub["published"],
            "published_at": pub["published_at"],
        })

    return jsonify(result)


@app.route("/api/images/<path:scenario>/scenes")
def api_images_scenes(scenario: str):
    """Список сцен с вариантами картинок, текстом и промптом.

    Источники сцен объединяются:
      1. images/review_images/scene_NN/ — уже сгенерированные картинки
      2. prompts/images.md — базы из markdown (как потенциальные сцены)

    Это позволяет открыть ревью свежего сценария без картинок и запустить
    массовую генерацию через кнопку «Сгенерировать все картинки».
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    review_dir = scenario_dir / "images" / "review_images"
    images_md = scenario_dir / "prompts" / "images.md"

    if not review_dir.exists() and not images_md.exists():
        abort(404, description=f"Нет ни review_images/, ни prompts/images.md для {scenario!r}")

    raw_scenes = discover_image_scenes(review_dir) if review_dir.exists() else {}
    md_data = parse_images_md(images_md)
    # Подмешиваем сцены из markdown — для тех, у которых ещё нет картинок
    for base in md_data:
        raw_scenes.setdefault(base, [])
    selections = load_image_selections(scenario)
    approved = load_approved_images(scenario_dir)

    result = []
    for base in sorted(raw_scenes.keys(), key=scene_sort_key):
        meta = md_data.get(base, {})
        approved_variant = approved.get(base)
        # Приоритет selections, иначе — одобренный вариант
        selected = selections.get(base, approved_variant)
        status = selections.get(f"{base}::status")
        if status is None:
            status = "done" if approved_variant else "pending"
        result.append({
            "base": base,
            "variants": raw_scenes[base],
            "text": meta.get("text", ""),
            "prompt": meta.get("prompt", ""),
            "selected": selected,
            "approved": approved_variant,
            "status": status,
        })

    return jsonify({"scenario": scenario, "scenes": result})


@app.route("/image/<path:scenario>/<scene>/<filename>")
def image_file(scenario: str, scene: str, filename: str):
    """Отдаёт jpg/png/webp из review_images/<scene>/."""
    scenario = unquote(scenario)
    scene_dir = CONTENT_DIR / scenario / "images" / "review_images" / scene
    if not scene_dir.exists():
        abort(404)
    return send_from_directory(str(scene_dir), filename, conditional=True)


IMAGEFX_RUNNER = ROOT / "automation" / "imagefx_runner.py"


@app.route("/api/images/<path:scenario>/regenerate-all", methods=["POST"])
def api_images_regenerate_all(scenario: str):
    """Запускает imagefx_runner.py в неинтерактивном --auto режиме.

    Runner открывает Chrome с сохранённым Flow-профилем, обходит все сцены из
    prompts/images.md, перехватывает image-ответы и сохраняет по пути
    <scenario>/images/review_images/scene_NN/vN.{jpg,png}. Subprocess запускаем
    фоном (Popen) — UI не блокируется. Логи читаем позже через статус-эндпоинт.

    Опциональный параметр `scenes`: список номеров сцен для регенерации
    (напр. [3, 7, 12]). Если не задан — обходим весь markdown.
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    images_md = scenario_dir / "prompts" / "images.md"
    if not images_md.exists():
        abort(404, f"Нет {images_md.relative_to(ROOT)} — сначала напиши промпты картинок")
    if not IMAGEFX_RUNNER.exists():
        abort(500, f"Не найден runner: {IMAGEFX_RUNNER}")

    data = request.get_json(silent=True) or {}
    scenes_filter = data.get("scenes")  # список int или None
    clean_session = bool(data.get("clean_session", False))

    review_dir = scenario_dir / "images" / "review_images"
    review_dir.mkdir(parents=True, exist_ok=True)
    # Маркер-файл для статус-эндпоинта: записываем время старта и PID,
    # чтобы после закрытия браузера / перезагрузки webapp можно было
    # понять «runner ещё активен или уже отработал».
    marker_path = review_dir / "_imagefx_runner.marker"

    auto_mode = bool(data.get("auto", False))

    # Пишем .bat-обёртку рядом с review_images/. Плюсы:
    #   (1) Окно cmd остаётся открытым после завершения (pause в конце),
    #       пользователь видит ошибку даже если скрипт упал в первую секунду.
    #   (2) chcp 65001 — корректная кодировка русских путей в консоли.
    #   (3) Всё логируется в stdout.log рядом через `>> ... 2>&1`, так webapp
    #       может показать причину падения без чтения самого cmd-окна.
    def _q(s: str) -> str:
        s = str(s)
        # В .bat заворачиваем в двойные кавычки если есть пробелы или кириллица.
        return f'"{s}"' if (' ' in s or any(ord(c) > 127 for c in s)) else s

    runner_parts = [_q(sys.executable), _q(str(IMAGEFX_RUNNER)), _q(str(images_md))]
    if auto_mode:
        runner_parts.append("--auto")
    if clean_session:
        runner_parts.append("--clean-session")
    if scenes_filter:
        runner_parts += ["--scenes", ",".join(str(int(n)) for n in scenes_filter)]
    runner_cmdline = " ".join(runner_parts)

    bat_path = review_dir / "_imagefx_runner_run.bat"
    bat_path.write_text(
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        "set PYTHONIOENCODING=utf-8\r\n"
        "set PYTHONUTF8=1\r\n"
        f'cd /d {_q(str(ROOT))}\r\n'
        f'{runner_cmdline} 2>&1\r\n'
        "set RC=%ERRORLEVEL%\r\n"
        "echo.\r\n"
        "echo =====================================================\r\n"
        "echo  Runner завершился (exit=%RC%). Окно останется открытым —\r\n"
        "echo  посмотри ошибки выше и закрой вручную.\r\n"
        "echo =====================================================\r\n"
        "pause\r\n",
        encoding="utf-8",
    )
    # Старый лог подчищаем — мог остаться от прошлого прогона, когда webapp
    # редиректил stdout в файл. Теперь stdout уходит в открытое окно cmd.
    (review_dir / "_imagefx_runner.log").unlink(missing_ok=True)

    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

    # CREATE_NEW_CONSOLE + запуск .bat = окно cmd, живущее независимо от
    # Flask'а, с интерактивным stdin (input() работает) и «pause» в конце,
    # чтобы любые ошибки оставались видны.
    creation_flags = 0
    if hasattr(subprocess, "CREATE_NEW_CONSOLE"):
        creation_flags = subprocess.CREATE_NEW_CONSOLE

    try:
        proc = subprocess.Popen(
            [str(bat_path)],
            cwd=str(ROOT),
            env=env,
            creationflags=creation_flags,
        )
    except Exception as e:
        abort(500, f"Не удалось запустить imagefx_runner: {e}")

    # Записываем маркер: pid + started_at. Статус-эндпоинт читает его,
    # чтобы знать, что именно этот прогон сейчас активен.
    marker_path.write_text(
        json.dumps({
            "pid": proc.pid,
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "scenes_filter": scenes_filter,
            "auto": auto_mode,
            "clean_session": clean_session,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        f"[imagefx] PID={proc.pid} scenario={scenario!r} "
        f"scenes={scenes_filter or 'all'} auto={auto_mode} "
        f"clean_session={clean_session} (new console)"
    )

    return jsonify({
        "ok": True,
        "pid": proc.pid,
        "markdown": str(images_md.relative_to(ROOT)),
        "scenes_filter": scenes_filter,
        "auto": auto_mode,
        "clean_session": clean_session,
        "message": (
            "Flow runner открыл отдельное окно cmd. "
            "Введи flow_id (если спросит) и нажми Enter когда Flow прогрузится."
        ),
    })


def _pid_alive(pid: int) -> bool:
    """Проверяет, жив ли процесс по PID. Кросс-платформенно.

    Windows: ctypes.OpenProcess(SYNCHRONIZE). Если вернулся валидный handle —
    процесс существует. Unix: os.kill(pid, 0) кидает ProcessLookupError для
    несуществующих PID.
    """
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes  # noqa: PLC0415
            SYNCHRONIZE = 0x00100000
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            h = kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))
            if h:
                kernel32.CloseHandle(h)
                return True
            return False
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


@app.route("/api/images/<path:scenario>/imagefx-status")
def api_images_imagefx_status(scenario: str):
    """Статус imagefx-прогона. Stdout ушёл в CREATE_NEW_CONSOLE, поэтому
    лога нет — источники сигнала:
      1. Маркер-файл `_imagefx_runner.marker` с pid+started_at
      2. Жив ли pid (ctypes.OpenProcess на Windows / os.kill(0) на Unix)
      3. mtime свежего image-файла в review_images/ — признак активности

    Состояния:
      running = маркер есть И (pid жив ИЛИ mtime свежее 90 сек)
      done    = маркер есть И pid мёртв И последние 30 сек без активности
      failed  = pid мёртв И с момента старта прошло <10 сек (быстро упал)
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    review_dir = scenario_dir / "images" / "review_images"
    marker_path = review_dir / "_imagefx_runner.marker"

    scenes = discover_image_scenes(review_dir) if review_dir.exists() else {}
    scenes_with_variants = sum(1 for v in scenes.values() if v)
    md_data = parse_images_md(scenario_dir / "prompts" / "images.md")
    scenes_total = len(md_data) if md_data else len(scenes)

    # Свежесть картинок: максимальный mtime среди всех variant-файлов
    latest_image_mtime = 0.0
    if review_dir.exists():
        for scene_dir in review_dir.iterdir():
            if not scene_dir.is_dir() or not IMAGE_SCENE_DIR_RE.match(scene_dir.name):
                continue
            for img in scene_dir.iterdir():
                if img.suffix.lower() in IMAGE_EXTS:
                    try:
                        m = img.stat().st_mtime
                        if m > latest_image_mtime:
                            latest_image_mtime = m
                    except Exception:
                        pass

    now_ts = datetime.now().timestamp()
    image_silence_sec = (now_ts - latest_image_mtime) if latest_image_mtime else 99999.0

    marker = None
    if marker_path.exists():
        try:
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
        except Exception:
            marker = None

    pid = (marker or {}).get("pid")
    pid_alive = _pid_alive(int(pid)) if pid else False

    # Состояния
    running = bool(marker) and (pid_alive or image_silence_sec < 90)

    started_at_ts = 0.0
    if marker and marker.get("started_at"):
        try:
            started_at_ts = datetime.fromisoformat(marker["started_at"]).timestamp()
        except Exception:
            pass
    since_start = (now_ts - started_at_ts) if started_at_ts else 99999.0

    # Runner умер быстро и ни одной картинки не появилось → упал
    failed = (
        bool(marker)
        and not pid_alive
        and since_start < 30
        and image_silence_sec > 30
        and scenes_with_variants == 0
    )

    # Нормально завершился: pid мёртв, картинки не менялись ≥30 сек,
    # начался давно (чтобы не путать со свежим запуском, когда pid ещё не
    # успел стать видимым в системе).
    done = (
        bool(marker)
        and not pid_alive
        and not running
        and not failed
        and since_start > 10
    )

    return jsonify({
        "exists": marker_path.exists(),
        "running": running,
        "done": done,
        "failed": failed,
        "error_hint": None,
        "scenes_with_variants": scenes_with_variants,
        "scenes_discovered": len(scenes),
        "scenes_total": scenes_total,
        "pid": pid,
        "pid_alive": pid_alive,
        "image_silence_sec": image_silence_sec,
        "since_start_sec": since_start,
        "started_at": (marker or {}).get("started_at"),
    })


@app.route("/api/images/<path:scenario>/select", methods=["POST"])
def api_images_select(scenario: str):
    """Сохраняет выбор варианта картинки для сцены."""
    scenario = unquote(scenario)
    data = request.get_json(force=True)
    base = data.get("base")
    variant = data.get("variant")  # None → снять выбор
    if not base:
        abort(400, "base is required")

    selections = load_image_selections(scenario)
    if variant is None:
        selections.pop(base, None)
        selections.pop(f"{base}::status", None)
    else:
        selections[base] = variant
        selections[f"{base}::status"] = "done"
    save_image_selections(scenario, selections)
    return jsonify({"ok": True})


@app.route("/api/images/<path:scenario>/regen", methods=["POST"])
def api_images_regen(scenario: str):
    """Помечает сцену на перегенерацию (картинки перегенерит imagefx_runner)."""
    scenario = unquote(scenario)
    data = request.get_json(force=True)
    base = data.get("base")
    if not base:
        abort(400, "base is required")

    selections = load_image_selections(scenario)
    selections.pop(base, None)
    selections[f"{base}::status"] = "regen"
    save_image_selections(scenario, selections)

    print(f"[STUB] Перегенерация картинки {base} в сценарии {scenario}")
    return jsonify({
        "ok": True,
        "stub": True,
        "message": f"Сцена {base} помечена на перегенерацию изображения",
    })


@app.route("/api/images/<path:scenario>/finalize", methods=["POST"])
def api_images_finalize(scenario: str):
    """Копирует выбранные картинки в content/<миф>/images/approved_images/.

    Логика зеркалит api_finalize (озвучка):
      - Для каждой сцены с выбором копируем файл как scene_XX_vN.<ext>
      - Старые approved для этой же базы удаляются перед копированием
      - regen-сцены попадают в отчёт (на перегенерацию через imagefx_runner)
    Склейки нет — картинки не являются временнóй дорожкой.
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    review_dir = scenario_dir / "images" / "review_images"
    approved_dir = scenario_dir / "images" / "approved_images"

    if not review_dir.exists():
        abort(404, description=f"Папка {review_dir} не найдена")

    approved_dir.mkdir(parents=True, exist_ok=True)

    selections = load_image_selections(scenario)
    chosen = {k: v for k, v in selections.items() if not k.endswith("::status")}
    regen_list = [
        k.replace("::status", "")
        for k, v in selections.items()
        if k.endswith("::status") and v == "regen"
    ]

    # Индекс {(base, variant): filename} из дискавери
    raw_scenes = discover_image_scenes(review_dir)
    variant_index: dict[tuple[str, str], str] = {}
    for base, variants in raw_scenes.items():
        for v in variants:
            variant_index[(base, v["variant"])] = v["filename"]

    copied: list[str] = []
    missing: list[str] = []

    for base, variant in chosen.items():
        fname = variant_index.get((base, variant))
        if fname is None:
            missing.append(f"{base}/{variant}")
            continue
        src = review_dir / base / fname
        ext = src.suffix  # .jpg / .png / .webp

        # Удаляем ранее одобренные версии этой базы (любой вариант, любое расширение)
        for old in approved_dir.glob(f"{base}.*"):
            old.unlink(missing_ok=True)
        for old in approved_dir.glob(f"{base}_*.*"):
            old.unlink(missing_ok=True)

        dst = approved_dir / approved_image_filename(base, variant, ext)
        shutil.copy2(src, dst)
        copied.append(dst.name)

    # Отчёт в selections/
    final_path = SELECTIONS_DIR / f"images_{scenario}__FINAL.json"
    final_path.write_text(
        json.dumps({
            "scenario": scenario,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "approved_folder": str(approved_dir),
            "copied": copied,
            "missing": missing,
            "to_regenerate": regen_list,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[FINALIZE-IMG] Скопировано {len(copied)} файлов в {approved_dir}")
    if missing:
        print(f"[FINALIZE-IMG] Не найдены варианты: {missing}")
    if regen_list:
        print(f"[STUB] Перегенерация картинок для сцен: {regen_list}")

    return jsonify({
        "ok": True,
        "approved_dir": str(approved_dir.relative_to(ROOT)),
        "copied_count": len(copied),
        "missing": missing,
        "regen_count": len(regen_list),
    })


# ═══════════════════════════════════════════════════════════════════════════
# VIDEO REVIEW — режим «видео»
# ═══════════════════════════════════════════════════════════════════════════
#
# Источники сцен:
#   1. content/<миф>/video/scene_NN_vN.mp4 — уже сгенерированные клипы
#   2. content/<миф>/prompts/video.md — блоки `## Сцена N` с промптами
#
# Выбор пользователя: webapp/selections/videos_<миф>.json
# Запуск Veo: automation/video_runner.py (через subprocess в новом cmd-окне).
# ═══════════════════════════════════════════════════════════════════════════

VIDEO_EXTS = {".mp4", ".webm", ".mov"}
# Имена клипов вида scene_01_v1.mp4, scene_15_v2.mp4
VIDEO_FILE_RE = re.compile(r"^scene_(\d+)_v(\d+)$")


def discover_video_scenes(video_dir: Path) -> dict[str, list[dict]]:
    """Сканирует content/<миф>/video/ и группирует клипы по сценам.

    Ожидаемая структура: video/scene_NN_vM.mp4 (плоско, без подпапок —
    так и сохраняет video_runner.py).

    Возвращает {base: [{filename, variant, size_mb, mtime}, ...]}
    отсортированно по номеру варианта (v1, v2, ..., v10 — числовая
    сортировка, не лексикографическая).
    """
    scenes: dict[str, list[dict]] = {}
    if not video_dir.exists():
        return scenes
    for v in sorted(video_dir.iterdir()):
        if not v.is_file():
            continue
        if v.suffix.lower() not in VIDEO_EXTS:
            continue
        m = VIDEO_FILE_RE.match(v.stem)
        if not m:
            continue
        idx, variant = int(m.group(1)), int(m.group(2))
        base = f"scene_{idx:02d}"
        scenes.setdefault(base, []).append({
            "filename": v.name,
            "variant": f"v{variant}",
            "size_mb": round(v.stat().st_size / (1024 * 1024), 2),
            "mtime": int(v.stat().st_mtime),
        })
    for base in scenes:
        scenes[base].sort(key=lambda x: int(x["variant"][1:]))
    return scenes


def parse_video_md(md_path: Path) -> dict[str, dict]:
    """Парсит content/<миф>/prompts/video.md → {scene_01: {image, prompt, sounds}}.

    Формат блока (как пишет агент):
        ## Сцена 1
        **Изображение:** content/<миф>/images/approved_images/scene_01_v2.jpg
        **Промпт:** ...
        **Звуки:** ...

    Поле `**Текст:**` тут опционально — если есть, тоже подхватим.
    Хвост после номера в заголовке (например, «## Сцена 1 (sent_001)»)
    разрешён.
    """
    if not md_path.exists():
        return {}
    content = md_path.read_text(encoding="utf-8")
    parts = re.split(r"^##\s+Сцена\s+(\d+)[^\n]*$", content, flags=re.MULTILINE)
    result: dict[str, dict] = {}
    for i in range(1, len(parts), 2):
        try:
            num = int(parts[i])
        except ValueError:
            continue
        block = parts[i + 1] if i + 1 < len(parts) else ""

        image_m = re.search(
            r"\*\*Изображение:\*\*\s*([^\n]+)", block
        )
        text_m = re.search(
            r"\*\*Текст:\*\*\s*(.+?)(?=\n\n|\*\*(?:Промпт|Изображение):\*\*|\Z)",
            block, re.DOTALL,
        )
        prompt_m = re.search(
            r"\*\*Промпт:\*\*\s*(.+?)(?=\n\*\*Звуки:\*\*|\n##\s+Сцена|\Z)",
            block, re.DOTALL,
        )
        sounds_m = re.search(
            r"\*\*Звуки:\*\*\s*(.+?)(?=\n##\s+Сцена|\Z)",
            block, re.DOTALL,
        )
        result[f"scene_{num:02d}"] = {
            "image": image_m.group(1).strip() if image_m else "",
            "text": text_m.group(1).strip() if text_m else "",
            "prompt": prompt_m.group(1).strip() if prompt_m else "",
            "sounds": sounds_m.group(1).strip() if sounds_m else "",
        }
    return result


def load_video_selections(scenario: str) -> dict:
    path = SELECTIONS_DIR / f"videos_{scenario}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_video_selections(scenario: str, data: dict) -> None:
    path = SELECTIONS_DIR / f"videos_{scenario}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def video_scenario_status(scenes: dict, selections: dict) -> tuple[int, int, int, str]:
    """Считает done/regen/pending и общий статус сценария.

    Сцена done — если в selections есть выбранный вариант ИЛИ статус "done".
    Regen — если статус "regen". Pending — иначе.

    Считаем только сцены, для которых есть хоть один сгенерированный клип
    (иначе вся таблица была бы pending до первого запуска video_runner).
    """
    done = regen = 0
    scenes_with_clips = {b: v for b, v in scenes.items() if v}
    for base in scenes_with_clips.keys():
        explicit = selections.get(f"{base}::status")
        if explicit == "regen":
            regen += 1
            continue
        if explicit == "done" or selections.get(base):
            done += 1
            continue
    total = len(scenes_with_clips)
    pending = total - done - regen
    if total == 0:
        status = "new"
    elif pending == 0 and regen == 0:
        status = "ready"
    elif done == 0 and regen == 0:
        status = "new"
    else:
        status = "in_progress"
    return done, regen, pending, status


# ── ЭНДПОИНТЫ ─────────────────────────────────────────────────────────────


@app.route("/api/videos/myths")
def api_videos_myths():
    """Список мифов для хаба ревью видео.

    Показываем сценарий, если есть `prompts/video.md` ИЛИ папка `video/`.
    Зеркалит api_images_myths — без `video.md` Тесей бы не появлялся в хабе
    до первого запуска video_runner.

    Сортировка — по времени создания папки сценария, от самой старой к новой.
    """
    result = []
    for d in iter_scenarios_by_creation(CONTENT_DIR):
        video_dir = d / "video"
        video_md = d / "prompts" / "video.md"

        if not video_dir.exists() and not video_md.exists():
            continue

        md_data = parse_video_md(video_md) if video_md.exists() else {}
        scenes = discover_video_scenes(video_dir) if video_dir.exists() else {}
        # Подмешиваем сцены из markdown — для тех, у которых ещё нет клипов
        for base in md_data:
            scenes.setdefault(base, [])

        if not scenes:
            continue

        selections = load_video_selections(d.name)
        done, regen, pending, status = video_scenario_status(scenes, selections)
        variants_total = sum(len(v) for v in scenes.values())
        scenes_with_clips = sum(1 for v in scenes.values() if v)
        pub = load_published_state(d.name)

        result.append({
            "name": d.name,
            "display_name": d.name,
            "scene_count": len(scenes),
            "done": done,
            "regen": regen,
            "pending": pending,
            "approved_count": scenes_with_clips,
            "variants_total": variants_total,
            "status": status,
            "published": pub["published"],
            "published_at": pub["published_at"],
        })

    return jsonify(result)


@app.route("/api/videos/<path:scenario>/scenes")
def api_videos_scenes(scenario: str):
    """Список сцен с вариантами клипов, текстом, промптом и звуками.

    Источники: video/ (готовые клипы) + prompts/video.md (промпты).
    Сцены без клипов всё равно отдаём — UI может показать «ещё не
    сгенерировано» и предложить запуск раннера.
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    video_dir = scenario_dir / "video"
    video_md = scenario_dir / "prompts" / "video.md"

    if not video_dir.exists() and not video_md.exists():
        abort(404, description=f"Нет ни video/, ни prompts/video.md для {scenario!r}")

    raw_scenes = discover_video_scenes(video_dir) if video_dir.exists() else {}
    md_data = parse_video_md(video_md) if video_md.exists() else {}
    for base in md_data:
        raw_scenes.setdefault(base, [])

    # Текст сцены в video.md обычно отсутствует — он живёт в images.md
    # (то же `## Сцена N` совпадает по нумерации). Подмешиваем тексты
    # оттуда, чтобы сайдбар и info-панель показывали реплику.
    images_md = scenario_dir / "prompts" / "images.md"
    image_meta = parse_images_md(images_md) if images_md.exists() else {}

    selections = load_video_selections(scenario)

    result = []
    for base in sorted(raw_scenes.keys(), key=scene_sort_key):
        meta = md_data.get(base, {})
        text_from_video = meta.get("text", "")
        text_from_image = image_meta.get(base, {}).get("text", "")
        selected = selections.get(base)
        status = selections.get(f"{base}::status")
        if status is None:
            status = "done" if selected else ("pending" if raw_scenes[base] else "empty")
        result.append({
            "base": base,
            "variants": raw_scenes[base],
            "image": meta.get("image", ""),
            "text": text_from_video or text_from_image,
            "prompt": meta.get("prompt", ""),
            "sounds": meta.get("sounds", ""),
            "selected": selected,
            "status": status,
        })

    return jsonify({"scenario": scenario, "scenes": result})


@app.route("/video/<path:scenario>/<filename>")
def video_file(scenario: str, filename: str):
    """Отдаёт mp4/webm/mov из content/<миф>/video/."""
    scenario = unquote(scenario)
    video_dir = CONTENT_DIR / scenario / "video"
    if not video_dir.exists():
        abort(404)
    return send_from_directory(str(video_dir), filename, conditional=True)


@app.route("/video-thumb/<path:scenario>/<filename>")
def video_thumb_file(scenario: str, filename: str):
    """Отдаёт картинку-источник (image-to-video) для превью сцены.

    Берём из images/approved_images/. filename — это относительный путь из
    `**Изображение:**` в video.md, либо просто имя файла approved-варианта.
    """
    scenario = unquote(scenario)
    approved_dir = CONTENT_DIR / scenario / "images" / "approved_images"
    if not approved_dir.exists():
        abort(404)
    # filename может прийти как «scene_15_v1.jpg» или с подпутями — берём basename
    safe_name = Path(filename).name
    return send_from_directory(str(approved_dir), safe_name, conditional=True)


VIDEO_RUNNER = ROOT / "automation" / "video_runner.py"


@app.route("/api/videos/<path:scenario>/regenerate-all", methods=["POST"])
def api_videos_regenerate_all(scenario: str):
    """Запускает automation/video_runner.py в отдельном cmd-окне.

    Зеркалит api_images_regenerate_all: пишем .bat-обёртку, открываем
    CREATE_NEW_CONSOLE с `pause` в конце (чтобы юзер увидел ошибки),
    маркер-файл с pid в video/ для последующего polling-статуса.

    Опциональный параметр `scenes`: список номеров сцен (1..23). Если
    задан — раннер получит `--scenes 1,2,3`.
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    video_md = scenario_dir / "prompts" / "video.md"
    if not video_md.exists():
        abort(404, f"Нет {video_md.relative_to(ROOT)} — сначала напиши промпты видео")
    if not VIDEO_RUNNER.exists():
        abort(500, f"Не найден runner: {VIDEO_RUNNER}")

    data = request.get_json(silent=True) or {}
    scenes_filter = data.get("scenes")
    clean_session = bool(data.get("clean_session", False))
    # Качество скачивания: 720p (дефолт, лёгкие файлы) или 1080p (мастер-копия).
    # Любые другие значения отбрасываем — раннер всё равно их не примет.
    quality = data.get("quality", "720p")
    if quality not in ("720p", "1080p"):
        quality = "720p"

    video_dir = scenario_dir / "video"
    video_dir.mkdir(parents=True, exist_ok=True)
    marker_path = video_dir / "_video_runner.marker"

    def _q(s: str) -> str:
        s = str(s)
        return f'"{s}"' if (' ' in s or any(ord(c) > 127 for c in s)) else s

    runner_parts = [_q(sys.executable), _q(str(VIDEO_RUNNER)), _q(str(video_md))]
    if clean_session:
        runner_parts.append("--clean-session")
    runner_parts += ["--quality", quality]
    if scenes_filter:
        runner_parts += ["--scenes", ",".join(str(int(n)) for n in scenes_filter)]
    runner_cmdline = " ".join(runner_parts)

    bat_path = video_dir / "_video_runner_run.bat"
    bat_path.write_text(
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        "set PYTHONIOENCODING=utf-8\r\n"
        "set PYTHONUTF8=1\r\n"
        f'cd /d {_q(str(ROOT))}\r\n'
        f'{runner_cmdline} 2>&1\r\n'
        "set RC=%ERRORLEVEL%\r\n"
        "echo.\r\n"
        "echo =====================================================\r\n"
        "echo  Video runner завершился (exit=%RC%). Окно останется открытым —\r\n"
        "echo  посмотри ошибки выше и закрой вручную.\r\n"
        "echo =====================================================\r\n"
        "pause\r\n",
        encoding="utf-8",
    )

    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

    creation_flags = 0
    if hasattr(subprocess, "CREATE_NEW_CONSOLE"):
        creation_flags = subprocess.CREATE_NEW_CONSOLE

    try:
        proc = subprocess.Popen(
            [str(bat_path)],
            cwd=str(ROOT),
            env=env,
            creationflags=creation_flags,
        )
    except Exception as e:
        abort(500, f"Не удалось запустить video_runner: {e}")

    marker_path.write_text(
        json.dumps({
            "pid": proc.pid,
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "scenes_filter": scenes_filter,
            "clean_session": clean_session,
            "quality": quality,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        f"[video_runner] PID={proc.pid} scenario={scenario!r} "
        f"scenes={scenes_filter or 'all'} clean_session={clean_session} "
        f"quality={quality} (new console)"
    )

    return jsonify({
        "ok": True,
        "pid": proc.pid,
        "markdown": str(video_md.relative_to(ROOT)),
        "scenes_filter": scenes_filter,
        "clean_session": clean_session,
        "quality": quality,
        "message": (
            "Video runner открыл отдельное окно cmd. "
            "Подключение к Chrome через CDP — убедись что launch_chrome_debug.bat "
            "запущен на порту 9222."
        ),
    })


@app.route("/api/videos/<path:scenario>/runner-status")
def api_videos_runner_status(scenario: str):
    """Статус video_runner.py — зеркалит imagefx-status.

    Источники сигнала:
      1. _video_runner.marker (pid + started_at)
      2. _pid_alive(pid)
      3. mtime свежего .mp4 в video/

    Состояния: running / done / failed.
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    video_dir = scenario_dir / "video"
    marker_path = video_dir / "_video_runner.marker"

    scenes = discover_video_scenes(video_dir) if video_dir.exists() else {}
    total_scenes = len({b for b in scenes.keys()})
    total_clips = sum(len(v) for v in scenes.values())

    marker = None
    if marker_path.exists():
        try:
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
        except Exception:
            marker = None

    pid = (marker or {}).get("pid")
    pid_alive = _pid_alive(int(pid)) if pid else False

    # mtime самого свежего mp4 в video/
    last_mtime = 0
    if video_dir.exists():
        for v in video_dir.glob("*.mp4"):
            last_mtime = max(last_mtime, int(v.stat().st_mtime))

    now = int(datetime.now().timestamp())
    silence_sec = (now - last_mtime) if last_mtime else None
    started_at_iso = (marker or {}).get("started_at")
    if started_at_iso:
        try:
            started_ts = int(datetime.fromisoformat(started_at_iso).timestamp())
            since_start = now - started_ts
        except Exception:
            since_start = None
    else:
        since_start = None

    # Видео-генерация в Veo медленная (~80 сек на клип), окно «активности»
    # шире, чем у imagefx — 180 секунд тишины ещё нормально.
    SILENCE_DEAD_SEC = 180
    QUICK_FAIL_SEC = 10

    running = bool(marker) and (
        pid_alive or (silence_sec is not None and silence_sec < SILENCE_DEAD_SEC)
    )
    failed = (
        bool(marker)
        and not pid_alive
        and since_start is not None
        and since_start < QUICK_FAIL_SEC
    )
    done = bool(marker) and not running and not failed

    return jsonify({
        "running": running,
        "done": done,
        "failed": failed,
        "scenes_with_clips": total_scenes,
        "clips_total": total_clips,
        "pid": pid,
        "pid_alive": pid_alive,
        "video_silence_sec": silence_sec,
        "since_start_sec": since_start,
        "started_at": started_at_iso,
    })


@app.route("/api/videos/<path:scenario>/select", methods=["POST"])
def api_videos_select(scenario: str):
    """Сохраняет выбор варианта клипа для сцены."""
    scenario = unquote(scenario)
    data = request.get_json(force=True)
    base = data.get("base")
    variant = data.get("variant")
    if not base:
        abort(400, "base is required")

    selections = load_video_selections(scenario)
    if variant is None:
        selections.pop(base, None)
        selections.pop(f"{base}::status", None)
    else:
        selections[base] = variant
        selections[f"{base}::status"] = "done"
    save_video_selections(scenario, selections)
    return jsonify({"ok": True})


@app.route("/api/videos/<path:scenario>/regen", methods=["POST"])
def api_videos_regen(scenario: str):
    """Помечает сцену на перегенерацию (клип перегенерит video_runner)."""
    scenario = unquote(scenario)
    data = request.get_json(force=True)
    base = data.get("base")
    if not base:
        abort(400, "base is required")

    selections = load_video_selections(scenario)
    selections.pop(base, None)
    selections[f"{base}::status"] = "regen"
    save_video_selections(scenario, selections)

    print(f"[STUB] Перегенерация видео {base} в сценарии {scenario}")
    return jsonify({
        "ok": True,
        "stub": True,
        "message": f"Сцена {base} помечена на перегенерацию видео",
    })


@app.route("/api/scenarios/<path:scenario>/publish", methods=["GET", "POST"])
def api_scenario_publish(scenario: str):
    """Переключатель «миф опубликован».

    GET  → текущее состояние {published, published_at}
    POST → принимает {on: bool}, сохраняет состояние, возвращает обновлённое.

    Никаких функциональных ограничений — только визуальная отметка.
    """
    scenario = unquote(scenario)
    if not (CONTENT_DIR / scenario).exists():
        abort(404, description=f"Сценарий {scenario!r} не найден")

    if request.method == "GET":
        return jsonify(load_published_state(scenario))

    payload = request.get_json(silent=True) or {}
    on = bool(payload.get("on"))
    state = save_published_state(scenario, on)
    return jsonify({"ok": True, **state})


# ─── Создание нового сценария ──────────────────────────────────────────────
# Один клик в UI «+ Новый миф» → создаётся вся папочная структура мифа
# (prompts/, voiceover/audio, voiceover/texts, images/, video/, music/,
# final/) и три заготовки промптов (voiceover.md / images.md / video.md)
# с шаблоном по правилам канала, чтобы дальше шаги пайплайна шли по
# готовой структуре без ручного «mkdir».


SCENARIO_SUBDIRS = (
    "prompts",
    "voiceover/audio",
    "voiceover/texts",
    "images",
    "video",
    "music",
    "final",
)


def _validate_scenario_name(name: str) -> tuple[bool, str]:
    """Имя папки нового сценария: непустое, без слешей, без `..`."""
    if not name or not name.strip():
        return False, "Имя не может быть пустым"
    name = name.strip()
    if any(ch in name for ch in ("/", "\\", "\0")):
        return False, "Имя не может содержать слеш"
    if name in (".", ".."):
        return False, "Недопустимое имя"
    if len(name) > 100:
        return False, "Имя слишком длинное (максимум 100 символов)"
    return True, ""


def _scenario_voiceover_template(name: str) -> str:
    """Шаблон prompts/voiceover.md для нового сценария.

    Структура соответствует правилу канала:
      - заголовок мифа
      - интро «<Имя/Название>. Миф за минуту.»
      - кликбейтный хук в 1–2 предложения (обязателен — удерживает зрителя
        в первые 3 секунды; см. Мидаса как эталон)
      - основной текст истории
    """
    return (
        f"# {name}\n"
        f"\n"
        f"{name}. Миф за минуту.\n"
        f"\n"
        f"<!-- ШАГ 1 — КЛИКБЕЙТНЫЙ ХУК (ОБЯЗАТЕЛЕН).\n"
        f"     Сразу после «Миф за минуту» идёт 1–2 предложения, которые\n"
        f"     удерживают зрителя в первые 3 секунды: интрига, вопрос или\n"
        f"     ошарашивающая ставка. Без хука ретеншн рассыпается на 2-й\n"
        f"     секунде. Эталон — Мидас:\n"
        f"\n"
        f"       «Представьте: всё, чего касаетесь, становится золотом.\n"
        f"        Царь Мида́с думал — это мечта. Оказалось — ловушка.»\n"
        f"\n"
        f"     Удалить эту инструкцию и заменить строку ниже на свой хук. -->\n"
        f"<КЛИКБЕЙТНЫЙ ХУК — заменить, 1–2 предложения, см. инструкцию выше>\n"
        f"\n"
        f"<!-- ШАГ 2 — ОСНОВНОЙ ТЕКСТ (~150–200 слов, 7–10 предложений).\n"
        f"     Правила: ударения только на именах собственных, без триггерных\n"
        f"     слов (убил→сразил, смерть→гибель), живой ритм без канцелярита.\n"
        f"     После готового текста разбить на предложения и положить\n"
        f"     каждое в voiceover/texts/sentence_NNN.txt. -->\n"
        f"<ОСНОВНОЙ ТЕКСТ — заменить>\n"
    )


def _scenario_images_template(name: str) -> str:
    """Заготовка prompts/images.md с напоминанием про правила канала."""
    return (
        f"<!-- {name} — промпты для генерации картинок (Google Flow / ImageFX).\n"
        f"\n"
        f"     Маппинг sentence ↔ scene_NN заполнить здесь после написания\n"
        f"     основного текста и разбиения на предложения. Пример:\n"
        f"       sentence_001 → scene_01 (1 шот)\n"
        f"       sentence_002 → scene_02 + scene_03 (2 шота, длинная фраза)\n"
        f"\n"
        f"     Правила канала, обязательны в каждом промпте:\n"
        f"       - Уникальный subject-маркер 3–4 английских слова в начале\n"
        f"         (например: persephone gathering spring flowers)\n"
        f"       - anthropomorphic bipedal cat character, standing upright\n"
        f"         on two legs like a human, humanoid body proportions\n"
        f"       - NO humans, NO people, NO real four-legged cats\n"
        f"       - Стилевой каркас: highly detailed pixel art, 9:16 vertical,\n"
        f"         ancient Greek setting, warm cinematic lighting,\n"
        f"         no text, no letters, no camera movement -->\n"
        f"\n"
        f"<!-- Карточка персонажей (для консистентности между сценами):\n"
        f"     <ОПИСАНИЕ ГЕРОЕВ — окрас, возраст, одежда, цвет глаз — заменить> -->\n"
        f"\n"
        f"## Сцена 1\n"
        f"\n"
        f"**Промпт:** <уникальный маркер 3-4 слова>, highly detailed pixel art, "
        f"9:16 vertical composition, ancient Greek setting, anthropomorphic "
        f"bipedal cat character, standing upright on two legs like a human, "
        f"humanoid body proportions, modern detailed pixel art style, warm "
        f"cinematic lighting, no text, no letters, no camera movement, "
        f"NO humans, NO people, NO real four-legged cats, "
        f"only anthropomorphic bipedal cat characters\n"
    )


def _scenario_video_template(name: str) -> str:
    """Заготовка prompts/video.md для image-to-video (Veo / LTX)."""
    return (
        f"<!-- {name} — промпты image-to-video (Veo / LTX) по картинкам,\n"
        f"     прошедшим ревью.\n"
        f"\n"
        f"     Правила канала:\n"
        f"       - Уникальный subject-маркер 3–4 английских слова в начале\n"
        f"       - Обязательный негатив в каждом промпте:\n"
        f"         No speech, no dialogue, no talking, no voices,\n"
        f"         no mouth movement, no music\n"
        f"       - Без зумов и панорамирования камеры (если не попросили)\n"
        f"       - no blood, no gore, no wounds (модерация TikTok/Shorts) -->\n"
        f"\n"
        f"## Сцена 1\n"
        f"\n"
        f"**Промпт:** <уникальный маркер 3-4 слова>, slight motion, "
        f"ancient Greek setting, anthropomorphic bipedal cat character, "
        f"No speech, no dialogue, no talking, no voices, no mouth movement, no music, "
        f"no blood, no gore\n"
    )


@app.route("/api/scenarios/create", methods=["POST"])
def api_scenarios_create():
    """Создаёт новый сценарий: папку content/<имя>/ со всей структурой.

    Body:    {"name": "Название мифа"}
    200/OK:  {"ok": true, "name": str, "created_paths": [str, ...]}
    400:     {"ok": false, "error": str}                        — невалидное имя
    409:     {"ok": false, "error": str, "exists": true}        — уже есть
    """
    payload = request.get_json(silent=True) or {}
    raw_name = (payload.get("name") or "").strip()

    ok, err = _validate_scenario_name(raw_name)
    if not ok:
        return jsonify({"ok": False, "error": err}), 400

    target = CONTENT_DIR / raw_name
    if target.exists():
        return jsonify({
            "ok": False,
            "error": f"Сценарий «{raw_name}» уже существует",
            "exists": True,
        }), 409

    created: list[str] = []
    target.mkdir(parents=True, exist_ok=False)
    created.append(str(target.relative_to(ROOT)).replace("\\", "/"))

    for sub in SCENARIO_SUBDIRS:
        p = target / sub
        p.mkdir(parents=True, exist_ok=True)
        created.append(str(p.relative_to(ROOT)).replace("\\", "/"))

    files = (
        ("prompts/voiceover.md", _scenario_voiceover_template(raw_name)),
        ("prompts/images.md", _scenario_images_template(raw_name)),
        ("prompts/video.md", _scenario_video_template(raw_name)),
    )
    for rel, content in files:
        fp = target / rel
        fp.write_text(content, encoding="utf-8")
        created.append(str(fp.relative_to(ROOT)).replace("\\", "/"))

    print(f"[create] Сценарий {raw_name!r} создан: {len(created)} путей")
    return jsonify({
        "ok": True,
        "name": raw_name,
        "created_paths": created,
    })


# ─── Эндпоинты для Chrome-расширения BOGI Promptr ──────────────────────────
# Расширение даёт sidebar с выбором сценария + список промптов с кнопками
# Copy. Запускать webapp обязательно — без него расширение пустое.


def _extension_marker(prompt: str) -> str:
    """Первые 3-4 слова промпта (subject-маркер до первой запятой), lowercase.

    Используется в UI расширения, чтобы коротко показать какая это сцена,
    и совпадает с тем что Google Flow подставляет в имя экспортируемого файла
    (см. distribute_images.py).
    """
    if not prompt:
        return ""
    head = prompt.split(",", 1)[0].strip().lower()
    return " ".join(head.split()[:4])


@app.route("/api/extension/scenarios")
def api_extension_scenarios():
    """Сценарии у которых есть prompts/images.md или prompts/video.md."""
    items = []
    for d in iter_scenarios_by_creation(CONTENT_DIR):
        images_md = d / "prompts" / "images.md"
        video_md = d / "prompts" / "video.md"
        has_images = images_md.exists()
        has_video = video_md.exists()
        if not (has_images or has_video):
            continue
        item = {
            "name": d.name,
            "has_images": has_images,
            "has_video": has_video,
            "image_count": len(parse_images_md(images_md)) if has_images else 0,
            "video_count": len(parse_video_md(video_md)) if has_video else 0,
        }
        items.append(item)
    return jsonify({"scenarios": items})


@app.route("/api/extension/prompts/<path:scenario>/<kind>")
def api_extension_prompts(scenario: str, kind: str):
    """Список промптов сценария: kind = images|video. С subject-маркерами."""
    if kind not in ("images", "video"):
        abort(400, description="kind должен быть images|video")
    scenario = unquote(scenario)
    md_path = CONTENT_DIR / scenario / "prompts" / f"{kind}.md"
    if not md_path.exists():
        abort(404, description=f"Нет {kind}.md для {scenario!r}")
    parsed = parse_images_md(md_path) if kind == "images" else parse_video_md(md_path)
    out = []
    for scene_id in sorted(parsed.keys()):
        try:
            scene_num = int(scene_id.split("_")[1])
        except (IndexError, ValueError):
            continue
        data = parsed[scene_id]
        prompt = data.get("prompt", "")
        out.append({
            "scene": scene_num,
            "scene_id": scene_id,
            "marker": _extension_marker(prompt),
            "text": data.get("text", ""),
            "prompt": prompt,
            "image": data.get("image", "") if kind == "video" else "",
        })
    return jsonify({"scenario": scenario, "kind": kind, "prompts": out})


@app.route("/api/extension/distribute", methods=["POST"])
def api_extension_distribute():
    """Запускает distribute_images.py для скачанного из Flow zip-архива.

    Body: {"scenario": "<имя мифа>", "archive_path": "<полный путь к zip>"}
    Возвращает stdout/stderr скрипта и returncode.
    """
    data = request.get_json(silent=True) or {}
    scenario = (data.get("scenario") or "").strip()
    archive_path = (data.get("archive_path") or "").strip()
    if not scenario or not archive_path:
        abort(400, description="Нужны scenario и archive_path")

    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.exists():
        abort(404, description=f"Сценарий {scenario!r} не найден")

    archive = Path(archive_path)
    if not archive.exists():
        abort(404, description=f"Архив не найден: {archive_path}")

    script = ROOT / "automation" / "distribute_images.py"
    cmd = [
        sys.executable, str(script), str(archive),
        "--myth-dir", str(scenario_dir),
        "--execute",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=180,
        )
    except subprocess.TimeoutExpired as e:
        return jsonify({
            "ok": False,
            "error": "timeout (180s)",
            "stdout": e.stdout or "",
            "stderr": e.stderr or "",
        }), 500

    return jsonify({
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "scenario": scenario,
        "archive": str(archive),
    })


if __name__ == "__main__":
    print(f"Content: {CONTENT_DIR}")
    print(f"Selections: {SELECTIONS_DIR}")
    print("-> http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
