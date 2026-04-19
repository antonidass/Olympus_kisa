"""
Веб-приложение для ревью озвучки и изображений.

Режим «озвучка»:
  Аудио:     content/<scenario>/voiceover/audio/
  Тексты:    content/<scenario>/voiceover/texts/
  Выбор:     webapp/selections/<scenario>.json

Режим «изображения»:
  Картинки:  content/<scenario>/images/review_images/scene_XX/vN.{jpg,png}
  Промпты:   content/<scenario>/prompts/images.md (опционально)
  Выбор:     webapp/selections/images_<scenario>.json
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
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
EXCLUDED_DIRS = {"approved_sentences", "scenes", "final", "outdated"}


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


# ffmpeg: сначала пробуем системный PATH, затем тот, что лежит внутри Remotion
# (на Windows-машине пользователя он гарантированно есть).
_REMOTION_FFMPEG = (
    ROOT / "remotion" / "node_modules" / "@remotion" /
    "compositor-win32-x64-msvc" / "ffmpeg.exe"
)


def _find_ffmpeg() -> str | None:
    which = shutil.which("ffmpeg")
    if which:
        return which
    if _REMOTION_FFMPEG.exists():
        return str(_REMOTION_FFMPEG)
    return None


def concat_approved_audio(approved_dir: Path, filenames: list[str]) -> tuple[Path | None, str | None]:
    """Склеивает отобранные mp3 в approved_dir/full.mp3 через ffmpeg concat.

    Возвращает (путь_к_файлу, None) при успехе или (None, сообщение_об_ошибке).
    """
    if not filenames:
        return None, "нет файлов для склейки"

    ffmpeg = _find_ffmpeg()
    if ffmpeg is None:
        return None, "ffmpeg не найден ни в PATH, ни в remotion/node_modules"

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
    parts = re.split(r"^##\s+Сцена\s+(\d+)\s*$", content, flags=re.MULTILINE)
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
    """Список сценариев."""
    if not CONTENT_DIR.exists():
        return jsonify([])
    scenarios = []
    for d in sorted(CONTENT_DIR.iterdir()):
        if d.is_dir() and (d / "voiceover" / "audio").exists():
            scenarios.append(d.name)
    return jsonify(scenarios)


@app.route("/api/scenarios-summary")
def api_scenarios_summary():
    """Список сценариев со статистикой для страницы выбора мифа."""
    if not CONTENT_DIR.exists():
        return jsonify([])

    result = []
    for d in sorted(CONTENT_DIR.iterdir()):
        if not d.is_dir():
            continue

        audio_dir = d / "voiceover" / "audio"
        if not audio_dir.exists():
            # Сценарий есть, но озвучка ещё не готова — показываем как WIP
            result.append({
                "name": d.name,
                "display_name": d.name,
                "scene_count": 0,
                "done": 0,
                "regen": 0,
                "pending": 0,
                "approved_count": 0,
                "variants_total": 0,
                "status": "wip",
            })
            continue

        raw_scenes = discover_scenes(audio_dir)
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
        })

    return jsonify(result)


@app.route("/api/scenes/<path:scenario>")
def api_scenes(scenario: str):
    """Список сцен с вариантами озвучки и текстом."""
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    audio_dir = scenario_dir / "voiceover" / "audio"

    if not audio_dir.exists():
        abort(404, description=f"Папка {audio_dir} не найдена")

    raw_scenes = discover_scenes(audio_dir)
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
    """Отдаёт mp3. filename может быть вложенным: 'sentence_001/sentence_001_v1.mp3'."""
    scenario = unquote(scenario)
    audio_dir = CONTENT_DIR / scenario / "voiceover" / "audio"
    if not audio_dir.exists():
        abort(404)
    # send_from_directory безопасно защищает от path traversal
    return send_from_directory(str(audio_dir), filename, conditional=True)


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
# content/Ящик Пандоры/TTS.mp3, скорость 1.1, 10 вариантов.
COSYVOICE_MODEL_NAME = "Fun-CosyVoice3-0.5B"
COSYVOICE_DEFAULT_SPEED = 1.1
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

    for base, variant in chosen.items():
        rel = variant_index.get((base, variant))
        if rel is None:
            missing.append(f"{base}/{variant}")
            continue
        src = audio_dir / rel
        # Удаляем ранее одобренные версии этой же базы, чтобы не копилось
        # (sentence_001_v1.mp3 + sentence_001_v3.mp3 одновременно), а также
        # legacy-файлы без суффикса версии (sentence_001.mp3).
        for old in list(approved_dir.glob(f"{base}_*.mp3")) + list(approved_dir.glob(f"{base}.mp3")):
            old.unlink(missing_ok=True)
        dst = approved_dir / approved_filename(base, variant)
        shutil.copy2(src, dst)
        copied.append(dst.name)

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


# ── routes: изображения ────────────────────────────────────────────────────

@app.route("/api/images/myths")
def api_images_myths():
    """Список мифов, у которых есть review_images/. Та же форма, что и
    /api/scenarios-summary — фронт рисует хаб единым рендером."""
    if not CONTENT_DIR.exists():
        return jsonify([])

    result = []
    for d in sorted(CONTENT_DIR.iterdir()):
        if not d.is_dir():
            continue
        review_dir = d / "images" / "review_images"
        if not review_dir.exists():
            # Миф без картинок вообще — в image-хабе не показываем
            continue

        scenes = discover_image_scenes(review_dir)
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
        })

    return jsonify(result)


@app.route("/api/images/<path:scenario>/scenes")
def api_images_scenes(scenario: str):
    """Список сцен с вариантами картинок, текстом и промптом."""
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    review_dir = scenario_dir / "images" / "review_images"

    if not review_dir.exists():
        abort(404, description=f"Папка {review_dir} не найдена")

    raw_scenes = discover_image_scenes(review_dir)
    md_data = parse_images_md(scenario_dir / "prompts" / "images.md")
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


if __name__ == "__main__":
    print(f"Content: {CONTENT_DIR}")
    print(f"Selections: {SELECTIONS_DIR}")
    print("-> http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
