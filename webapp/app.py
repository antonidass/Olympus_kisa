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
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from flask import Flask, jsonify, request, send_from_directory, abort

try:
    import urllib.request as _urlreq
    import urllib.error as _urlerr
except ImportError:  # pragma: no cover
    _urlreq = None  # type: ignore[assignment]
    _urlerr = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
SELECTIONS_DIR = Path(__file__).resolve().parent / "selections"
STATIC_DIR = Path(__file__).resolve().parent / "static"

# Адрес долгоживущего CosyVoice-сервера (см. automation/cosyvoice_server.py).
# Можно переопределить переменной окружения, иначе используем 127.0.0.1:5001.
COSY_SERVER_URL = os.environ.get("COSY_SERVER_URL", "http://127.0.0.1:5001").rstrip("/")
COSY_SERVER_START_BAT = ROOT / "automation" / "start_cosyvoice_server.bat"

# Раскатка нового сценария — общий модуль с CLI (`automation/create_scenario.py`).
sys.path.insert(0, str(ROOT))
from automation.scenario_scaffold import (  # noqa: E402
    ScenarioExistsError,
    create_scenario as scaffold_create_scenario,
    validate_scenario_name,
)

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


# Подпапки, по которым папку считаем валидным сценарием. Любая из них —
# признак, что это «контейнер мифа» в нашей конвенции.
SCENARIO_MARKERS: tuple[str, ...] = (
    "prompts",
    "voiceover",
    "images",
    "video",
    "final",
    "music",
)


# Имя папки одной части сериала «От Хаоса до Олимпа»: `часть_01_Хаос`
# (нижний регистр «часть», подчёркивание, двузначный номер, тема).
SERIES_PART_RE = re.compile(r"^часть_(\d{1,2})_(.+)$")


def _looks_like_scenario_dir(p: Path) -> bool:
    """Папка — это сценарий, если в ней есть хоть один маркер (prompts/, voiceover/…)."""
    if not p.is_dir():
        return False
    for marker in SCENARIO_MARKERS:
        if (p / marker).exists():
            return True
    return False


def _series_display_name(parent_name: str, part_dir_name: str) -> str:
    """`часть_01_Хаос` под зонтиком «От Хаоса до Олимпа» → «От Хаоса до Олимпа — Ч.01 Хаос».

    Если имя части не подпадает под шаблон `часть_NN_<тема>` — отдаём
    fallback `<parent> / <part_dir_name>`, чтобы хаб всё равно показал
    её осмысленно.
    """
    m = SERIES_PART_RE.match(part_dir_name)
    if not m:
        return f"{parent_name} / {part_dir_name}"
    num = m.group(1).zfill(2)
    theme = m.group(2).replace("_", " ")
    return f"{parent_name} — Ч.{num} {theme}"


class ScenarioEntry:
    """Лёгкая обёртка для записи сценария в discovery.

    - `name` / `id` — идентификатор сценария, по нему строятся URL и selections.
      Для одиночных мифов это просто имя папки («Икар и Дедал»).
      Для частей сериала — относительный путь со слешем
      («От Хаоса до Олимпа/часть_01_Хаос»).
    - `path` — абсолютный путь к папке сценария.
    - `display_name` — человекочитаемое название для UI («От Хаоса до Олимпа — Ч.01 Хаос»).
    - `ctime` — время создания (для сортировки).
    """

    __slots__ = ("name", "path", "display_name", "ctime")

    def __init__(self, name: str, path: Path, display_name: str, ctime: float):
        self.name = name
        self.path = path
        self.display_name = display_name
        self.ctime = ctime

    # Совместимость с прошлым API (раньше в эндпоинтах писали `d.name`,
    # `d / "voiceover"`, итд. — теперь делаем то же самое через путь).
    def __truediv__(self, other: str) -> Path:
        return self.path / other


def iter_scenarios_by_creation(content_dir: Path) -> list[ScenarioEntry]:
    """Итератор по сценариям, отсортированным от самой старой к новой.

    Сценарием считаем:
      1. Папку первого уровня `content/<X>/`, если в ней есть маркеры
         (`prompts/`, `voiceover/`, `images/`, `video/`, …) — это
         одиночный миф.
      2. Папку второго уровня `content/<X>/<Y>/`, если родитель НЕ
         сценарий, а сам `<Y>` имеет маркеры — это часть сериала
         (например, «От Хаоса до Олимпа/часть_01_Хаос»).

    Так зонтичная папка цикла («От Хаоса до Олимпа/») не показывается
    в хабе как один пустой сценарий, а её части видны и кликабельны
    каждая по отдельности.
    """
    if not content_dir.exists():
        return []

    entries: list[ScenarioEntry] = []
    for top in content_dir.iterdir():
        if not top.is_dir():
            continue

        if _looks_like_scenario_dir(top):
            # Одиночный миф.
            entries.append(ScenarioEntry(
                name=top.name,
                path=top,
                display_name=top.name,
                ctime=_dir_creation_time(top),
            ))
            continue

        # Не сценарий сам по себе — пробуем как зонтик серии. Каждая
        # внутренняя папка-часть со своими маркерами становится сценарием.
        # Если внутри ничего такого нет — это какая-то служебная папка
        # (`trash`, и т.п.), её просто пропускаем.
        #
        # Особый случай — `content/архив/<миф>/`: технически это тоже
        # вложенный сценарий со слешем в id («архив/Икар и Дедал»),
        # но display_name даём без префикса — архивность показывается
        # отдельно через is_archived/сегмент UI, дублировать «архив /»
        # в имени не нужно.
        is_archive_root = (top.name == ARCHIVE_FOLDER_NAME)
        for sub in top.iterdir():
            if _looks_like_scenario_dir(sub):
                rel_id = f"{top.name}/{sub.name}"
                display = sub.name if is_archive_root \
                    else _series_display_name(top.name, sub.name)
                entries.append(ScenarioEntry(
                    name=rel_id,
                    path=sub,
                    display_name=display,
                    ctime=_dir_creation_time(sub),
                ))

    entries.sort(key=lambda e: e.ctime)
    return entries


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
    # `scenario` для частей сериала содержит слеш («От Хаоса до Олимпа/часть_01_Хаос»),
    # из-за чего файл попадает в подпапку — создаём её, иначе write_text упадёт.
    path.parent.mkdir(parents=True, exist_ok=True)
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
        # См. save_selections — для частей сериала имя содержит слеш.
        path.parent.mkdir(parents=True, exist_ok=True)
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


# ── архивирование мифа ────────────────────────────────────────────────────
#
# При публикации (POST /publish с on=true) одиночный миф физически переезжает
# в `content/архив/<миф>/`. Имя сценария меняется: «Икар и Дедал» →
# «архив/Икар и Дедал». Соответствующие JSON-файлы в `webapp/selections/`
# должны переехать вместе с папкой, иначе UI потеряет выборы.
#
# Серии («От Хаоса до Олимпа/часть_01_Хаос») сейчас не архивируются — discovery
# работает только на 2 уровнях, а архив серии = 3 уровня. Заранее блокируем
# на уровне API.

ARCHIVE_FOLDER_NAME = "архив"

# Префиксы файлов в SELECTIONS_DIR, которые ключуются по имени сценария.
# Все они должны переехать вместе с мифом. Порядок неважен, расширения
# одинаковые (.json).
SELECTIONS_FILE_PREFIXES = ("", "images_", "videos_", "published_")


def _is_archived(scenario: str) -> bool:
    """Лежит ли сценарий уже в `content/архив/`. Идентифицируем по префиксу
    в имени, не по диску — это быстрее и не зависит от FS."""
    return scenario.startswith(f"{ARCHIVE_FOLDER_NAME}/")


def _selections_files_for(scenario: str) -> list[Path]:
    """Все JSON-файлы в SELECTIONS_DIR, привязанные к имени сценария.

    Включает как «рабочие» (selections, images_, videos_, published_), так и
    `*__FINAL.json` версии. Возвращает только существующие пути."""
    files: list[Path] = []
    for prefix in SELECTIONS_FILE_PREFIXES:
        base = SELECTIONS_DIR / f"{prefix}{scenario}"
        for suffix in (".json", "__FINAL.json"):
            p = base.with_name(base.name + suffix) if suffix == "__FINAL.json" \
                else base.with_suffix(".json")
            if p.exists():
                files.append(p)
    return files


def _move_with_retry(src: Path, dst: Path, attempts: int = 3) -> None:
    """`shutil.move` с retry на Windows file-lock.

    На Windows папка может быть занята браузером (открыт mp3 в плеере) или
    другим процессом (cosyvoice runner). Делаем 3 попытки с короткой паузой;
    последняя пробрасывает исходное исключение."""
    last_err: Exception | None = None
    for attempt in range(attempts):
        try:
            shutil.move(str(src), str(dst))
            return
        except (PermissionError, OSError) as e:
            last_err = e
            if attempt < attempts - 1:
                time.sleep(0.2)
    if last_err:
        raise last_err


def archive_scenario(scenario: str) -> tuple[str, list[str]]:
    """Физический перенос мифа в `content/архив/` + selections-файлы.

    Возвращает (новое_имя_сценария, список_перемещённых_файлов_для_лога).
    Бросает ValueError, если сценарий — серия (имя со слешем) или уже в
    архиве, либо FileNotFoundError, если папки нет.
    """
    if "/" in scenario:
        raise ValueError(
            f"Архивация сериалов пока не поддерживается ({scenario!r})"
        )
    if _is_archived(scenario):
        raise ValueError(f"Сценарий {scenario!r} уже в архиве")

    src_dir = CONTENT_DIR / scenario
    if not src_dir.exists():
        raise FileNotFoundError(f"Папка сценария не найдена: {src_dir}")

    archive_root = CONTENT_DIR / ARCHIVE_FOLDER_NAME
    archive_root.mkdir(parents=True, exist_ok=True)
    dst_dir = archive_root / scenario
    if dst_dir.exists():
        # Маловероятно, но возможно — если уже архивировали и снова кладут
        # папку с тем же именем в content/. Не перезаписываем — пусть
        # пользователь разберётся вручную.
        raise FileExistsError(
            f"В архиве уже есть {dst_dir} — конфликт имён, разрулите вручную"
        )

    moved: list[str] = []
    _move_with_retry(src_dir, dst_dir)
    moved.append(f"content/{scenario}/ → content/{ARCHIVE_FOLDER_NAME}/{scenario}/")

    # Selections-файлы: переезжают в selections/архив/<scenario>.json и т.д.
    # Подпапку создаём лениво — на первом файле, через `dst_file.parent.mkdir`.
    new_name = f"{ARCHIVE_FOLDER_NAME}/{scenario}"
    for src_file in _selections_files_for(scenario):
        # Имя файла: префикс + scenario.json или префикс + scenario__FINAL.json
        new_filename = src_file.name.replace(scenario, new_name, 1)
        dst_file = SELECTIONS_DIR / new_filename
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            _move_with_retry(src_file, dst_file)
            moved.append(f"selections/{src_file.name} → selections/{new_filename}")
        except OSError as e:
            # Не блокер: основная папка уже переехала, восстанавливать
            # обратно опасно. Логируем и продолжаем — пользователь увидит
            # в toast, что какие-то выборы не подхватились.
            print(f"[archive] не смог перенести {src_file}: {e}")

    return new_name, moved


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


def drop_approved_for_base(scenario_dir: Path, base: str) -> list[str]:
    """Удаляет одобренный mp3 для сцены `base` из approved_sentences/.

    Вызывается перед перегенерацией: старый approved-файл (например,
    sentence_009_v2.mp3) соответствовал ПРЕДЫДУЩЕЙ озвучке. Новые варианты
    с теми же именами _vN имеют уже другое содержимое, и зафиксированный
    approved становится устаревшим — UI рисовал бы «★ Одобрено» на чужом
    физическом файле, а финальная склейка использовала бы старую озвучку.
    Возвращает список имён, которые не удалось удалить (Windows lock).
    """
    approved_dir = scenario_dir / "voiceover" / "audio" / "approved_sentences"
    if not approved_dir.exists():
        return []
    stuck: list[str] = []
    targets = (
        list(approved_dir.glob(f"{base}_*.mp3"))
        + list(approved_dir.glob(f"{base}.mp3"))
    )
    # На Windows файл может быть занят браузером (HTML5 <audio> держит
    # handle на mp3, который сейчас играется). Делаем 3 попытки с короткой
    # паузой; если всё равно занят — возвращаем имя наверх, вызывающий
    # пусть логирует. Хуже не будет: при следующем finalize файл
    # перезапишется.
    for old in targets:
        for attempt in range(3):
            try:
                old.unlink(missing_ok=True)
                break
            except PermissionError:
                if attempt == 2:
                    stuck.append(old.name)
                else:
                    time.sleep(0.15)
    return stuck


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


def parse_scene_sentence_mapping(md_path: Path) -> dict[str, list[int]]:
    """Извлекает scene_NN → [sentence_numbers] из заголовков сцен `## Сцена N`.

    В новом формате (от `От Хаоса до Олимпа`) заголовок сцены прямо несёт
    маппинг на предложения озвучки:

        ## Сцена 1 (sent_001 + sent_002 — хук + титул)
        ## Сцена 3 (sent_004 — «И в этой пустоте что-то шевельнулось»)

    Тогда `scene_01 → [1, 2]`, `scene_03 → [4]`. Это используется в API
    `api_images_scenes` чтобы подмешать текст из `voiceover/texts/sentence_NNN.txt`
    в info-панель ревью, когда самого блока `**Текст:**` в images.md нет.

    Возвращает только те сцены, у которых mapping в заголовке реально есть —
    для старого формата (без `(sent_NNN ...)`) словарь будет пустым.
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


def load_sentence_text(scenario_dir: Path, sent_num: int) -> str:
    """Читает content/<миф>/voiceover/texts/sentence_NNN.txt → одну строку.

    Возвращает пустую строку если файла нет (это нормально — sentence-файлы
    создаются автоматически из voiceover.md, но могут отставать).
    """
    fp = scenario_dir / "voiceover" / "texts" / f"sentence_{sent_num:03d}.txt"
    if not fp.exists():
        return ""
    try:
        return fp.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


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
    # Принимаем оба формата заголовков: `## Сцена 1` и `## Сцена scene_01`
    # (формат stickers.md в т.ч. использует `scene_NN` префикс).
    parts = re.split(r"^##\s+Сцена\s+(?:scene_)?(\d+)[^\n]*$", content, flags=re.MULTILINE)
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
    # См. save_selections — для частей сериала имя содержит слеш.
    path.parent.mkdir(parents=True, exist_ok=True)
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
    for entry in iter_scenarios_by_creation(CONTENT_DIR):
        if (entry.path / "voiceover" / "audio").exists():
            scenarios.append(entry.name)
    return jsonify(scenarios)


@app.route("/api/scenarios-summary")
def api_scenarios_summary():
    """Список сценариев со статистикой для страницы выбора мифа.

    Сортировка — по времени создания папки сценария, от самой старой к новой.
    """
    result = []
    for entry in iter_scenarios_by_creation(CONTENT_DIR):
        audio_dir = entry.path / "voiceover" / "audio"
        texts_dir = entry.path / "voiceover" / "texts"

        if not audio_dir.exists() and not texts_dir.exists():
            # Ни озвучки, ни разбиения текста — сценарий ещё совсем сырой
            continue

        pub = load_published_state(entry.name)

        if not audio_dir.exists():
            # Озвучки нет, но текст уже разбит на предложения — показываем
            # как WIP с количеством сцен из texts/. Это нужно, чтобы
            # пользователь мог зайти в ревью и нажать «Озвучить всё».
            text_bases = discover_sentences_from_texts(entry.path)
            result.append({
                "name": entry.name,
                "display_name": entry.display_name,
                "scene_count": len(text_bases),
                "done": 0,
                "regen": 0,
                "pending": len(text_bases),
                "approved_count": 0,
                "variants_total": 0,
                "status": "new" if text_bases else "wip",
                "published": pub["published"],
                "published_at": pub["published_at"],
                "is_archived": _is_archived(entry.name),
            })
            continue

        raw_scenes = discover_scenes(audio_dir)
        # Подмешиваем базы из texts/ — чтобы счётчик показывал реальный
        # объём сценария даже до запуска первой генерации
        for tb in discover_sentences_from_texts(entry.path):
            raw_scenes.setdefault(tb, [])
        selections = load_selections(entry.name)
        approved = load_approved_sentences(entry.path)

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
            "name": entry.name,
            "display_name": entry.display_name,
            "scene_count": scene_count,
            "done": done,
            "regen": regen,
            "pending": pending,
            "approved_count": len(approved),
            "variants_total": variants_total,
            "status": scenario_status,
            "published": pub["published"],
            "published_at": pub["published_at"],
            "is_archived": _is_archived(entry.name),
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


@app.route("/audio/<path:scenario>")
def audio_file(scenario: str):
    """Отдаёт mp3 сценария. Путь к файлу — query-параметр `?path=`.

    Раньше было `/audio/<path:scenario>/<path:filename>` — два path-параметра
    подряд. Это сломалось когда scenario стал содержать слеш («От Хаоса до
    Олимпа/часть_01_Хаос»): werkzeug greedy-захватывал всё в scenario, и
    filename оставался пустым → 404. Query-string снимает неоднозначность.

    После перегенерации имя mp3 остаётся тем же, но контент меняется —
    без no-cache браузер отдаёт старую озвучку из кеша. Ставим
    no-cache + must-revalidate.
    """
    scenario = unquote(scenario)
    filename = unquote(request.args.get("path", "") or "")
    if not filename:
        abort(400, "Параметр ?path= обязателен")
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
# Речь синтезируем с клонированием голоса из Ящика Пандоры — TTS.mp3 + TTS.txt.
# 10 вариантов. Скорость задаётся пользователем в UI (input в модалке
# регенерации); 1.1 — fallback, если фронт не прислал значение.
COSYVOICE_MODEL_NAME = "Fun-CosyVoice3-0.5B"
COSYVOICE_DEFAULT_SPEED = 1.1
COSYVOICE_DEFAULT_VARIANTS = 10


# ── Каталог голосов для CosyVoice ─────────────────────────────────────────
# Каждый голос — папка в assets/TTS/<имя голоса>/ с двумя файлами:
#   TTS.mp3 — короткий референс (5-15 сек чистой речи)
#   TTS.txt — точная расшифровка этого референса
# Ключ ("max", "burunov") — ASCII id, используется в URL/JSON; label —
# человеческое имя для UI; dir — папка с файлами. Если кто-то заведёт ещё
# одного диктора, достаточно положить assets/TTS/<NewVoice>/{TTS.mp3,TTS.txt}
# и добавить запись сюда.
ASSETS_TTS_DIR = ROOT / "assets" / "TTS"
COSY_VOICES: dict[str, dict] = {
    "max": {
        "label": "Макс Энергичный",
        "dir": ASSETS_TTS_DIR / "Макс",
    },
    "burunov": {
        "label": "Сергей Бурунов",
        "dir": ASSETS_TTS_DIR / "Бурунов",
    },
}
COSY_DEFAULT_VOICE = "max"


def _voice_files(voice_id: str) -> tuple[Path, Path]:
    """Возвращает (wav, txt) для указанного голоса. Если голос не известен —
    откатываемся на дефолтный, чтобы не падать на старых запросах без поля."""
    cfg = COSY_VOICES.get(voice_id) or COSY_VOICES[COSY_DEFAULT_VOICE]
    return cfg["dir"] / "TTS.mp3", cfg["dir"] / "TTS.txt"


def _resolve_voice_id(value: object) -> str:
    """Приводит присланное фронтом значение к валидному voice_id."""
    if isinstance(value, str) and value in COSY_VOICES:
        return value
    return COSY_DEFAULT_VOICE


# Дефолтный голос — для совместимости со старыми ссылками на эти константы.
COSYVOICE_PROMPT_WAV, COSYVOICE_PROMPT_TXT = _voice_files(COSY_DEFAULT_VOICE)
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

    # Голос диктора — выбирается в UI из COSY_VOICES. Пустое поле / неизвестный
    # id = откат на дефолтный (Макс), чтобы старые скрипты без поля не ломались.
    voice_id = _resolve_voice_id(data.get("voice"))
    prompt_wav, prompt_txt = _voice_files(voice_id)

    # Проверки файлов prompt — пользовательские, явные.
    if not prompt_wav.exists():
        abort(500, f"Нет prompt-wav: {prompt_wav}")
    if not prompt_txt.exists():
        abort(500, f"Нет prompt-txt: {prompt_txt}")

    variants = int(data.get("variants") or COSYVOICE_DEFAULT_VARIANTS)
    speed = float(data.get("speed") or COSYVOICE_DEFAULT_SPEED)

    # ── НОВЫЙ ПУТЬ: если cosy-сервер запущен, отправляем туда HTTP-задачу.
    # Модель уже в памяти — генерация стартует мгновенно, без ~30 сек прогрева.
    # Сервер пишет mp3 в ту же папку (voiceover/audio/review_sentences/<base>/),
    # которую дальше поллит существующий /api/cosyvoice-status — UI без правок.
    if _cosy_server_is_ready():
        code, job_data, err = _cosy_http_request("POST", "/jobs", {
            "type": "single",
            "scenario": scenario,
            "base": base,
            "text": text,
            "variants": variants,
            "speed": speed,
            "prompt_wav": str(prompt_wav),
            "prompt_text": prompt_txt.read_text(encoding="utf-8").strip(),
        }, timeout=15)
        if code != 200:
            abort(503, f"Cosy-сервер не принял задачу: {err or f'HTTP {code}'}")

        # Сбрасываем старый approved для этой сцены — иначе UI после
        # завершения регенерации снова подтянет «звёздочку» на варианте,
        # чей физический файл уже перезаписан новой озвучкой (см. помощник
        # drop_approved_for_base).
        stuck = drop_approved_for_base(scenario_dir, base)
        if stuck:
            print(f"[cosyvoice/server] approved-файлы заняты, оставлены до finalize: {stuck}")

        # Помечаем сцену как regen — UI сразу нарисует оранжевый статус.
        selections = load_selections(scenario)
        selections.pop(base, None)
        selections[f"{base}::status"] = "regen"
        save_selections(scenario, selections)

        return jsonify({
            "ok": True,
            "via_server": True,
            "job_id": (job_data or {}).get("job_id"),
            "scenario": scenario,
            "base": base,
            "variants": variants,
            "speed": speed,
            "voice": voice_id,
            "voice_label": COSY_VOICES[voice_id]["label"],
            "model": COSYVOICE_MODEL_NAME,
            "prompt_wav": str(prompt_wav.relative_to(ROOT)),
            "prompt_text_file": str(prompt_txt.relative_to(ROOT)),
            "prompt_text_preview": prompt_txt.read_text(encoding="utf-8").strip()[:120],
            "text_preview": text[:120],
            "out_dir": f"content/{scenario}/voiceover/audio/review_sentences/{base}",
            "message": (
                f"CosyVoice3 ({COSY_VOICES[voice_id]['label']}) через сервер: "
                f"{variants} вариантов, скорость {speed}. Модель уже в памяти — без прогрева."
            ),
        })

    # ── СТАРЫЙ ПУТЬ: сервер недоступен → запускаем subprocess как раньше.
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
        "--prompt-wav", str(prompt_wav),
        "--prompt-text", str(prompt_txt),
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

    # Сбрасываем одобренный вариант для этой сцены — см. drop_approved_for_base.
    stuck = drop_approved_for_base(scenario_dir, base)
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
        "voice": voice_id,
        "voice_label": COSY_VOICES[voice_id]["label"],
        "prompt_wav": str(prompt_wav.relative_to(ROOT)),
        "prompt_text_file": str(prompt_txt.relative_to(ROOT)),
        "prompt_text_preview": prompt_txt.read_text(encoding="utf-8").strip()[:120],
        "text_preview": text[:120],
        "log_file": str(log_path.relative_to(ROOT)),
        "out_dir": f"content/{scenario}/voiceover/audio/{base}",
        "message": (
            f"CosyVoice3 ({COSY_VOICES[voice_id]['label']}): {variants} вариантов, "
            f"скорость {speed}, клон из {prompt_wav.name}"
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


# ── Batch CosyVoice (option A: одна загрузка модели на весь миф) ──────────
#
# Один subprocess cosyvoice_runner.py --auto, который ВНУТРИ обходит все
# сцены из --bases и грузит модель ровно один раз. Экономит ~30% времени
# на массовой генерации (один прогрев на 24 сцены вместо 24).

def cosyvoice_batch_status_path(scenario: str) -> Path:
    return CONTENT_DIR / scenario / "voiceover" / "audio" / "_cosyvoice_batch.json"


def cosyvoice_batch_log_path(scenario: str) -> Path:
    return CONTENT_DIR / scenario / "voiceover" / "audio" / "_cosyvoice_batch.log"


@app.route("/api/cosyvoice-batch-start/<path:scenario>", methods=["POST"])
def api_cosyvoice_batch_start(scenario: str):
    """Стартует один subprocess CosyVoice runner в auto-режиме на список сцен.

    Тело запроса: { "bases": ["sentence_001", ...], "speed": 1.1, "variants": 10 }

    bases должны существовать как файлы content/<scenario>/voiceover/texts/<base>.txt —
    runner читает текст оттуда (а не передаёт через CLI, чтобы не упереться в
    лимиты Windows command line на длинных мифах).

    Возвращает PID и пути к статус/лог файлам.
    """
    scenario = unquote(scenario)
    data = request.get_json(force=True)
    bases = data.get("bases") or []
    if not isinstance(bases, list) or not bases:
        abort(400, "bases must be a non-empty list")
    bases = [str(b).strip() for b in bases if str(b).strip()]
    if not bases:
        abort(400, "bases is empty after sanitization")

    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.exists():
        abort(404, f"Сценарий {scenario!r} не найден")

    # Проверяем, что для всех баз есть файл с текстом — иначе runner упадёт
    # уже на одной из сцен. Лучше отказать сразу с понятным сообщением.
    texts_dir = scenario_dir / "voiceover" / "texts"
    missing = [b for b in bases if not (texts_dir / f"{b}.txt").exists()]
    if missing:
        abort(400, f"Нет файлов текста для: {', '.join(missing[:5])}"
                   + (f" (и ещё {len(missing) - 5})" if len(missing) > 5 else ""))

    voice_id = _resolve_voice_id(data.get("voice"))
    prompt_wav, prompt_txt = _voice_files(voice_id)

    if not prompt_wav.exists():
        abort(500, f"Нет prompt-wav: {prompt_wav}")
    if not prompt_txt.exists():
        abort(500, f"Нет prompt-txt: {prompt_txt}")

    variants = int(data.get("variants") or COSYVOICE_DEFAULT_VARIANTS)
    speed = float(data.get("speed") or COSYVOICE_DEFAULT_SPEED)

    # ── НОВЫЙ ПУТЬ: cosy-сервер ready → шлём одну batch-задачу. Сервер
    # обходит сцены последовательно в воркер-потоке, модель загружена
    # один раз ещё при старте. Никаких новых cmd-окон.
    if _cosy_server_is_ready():
        code, job_data, err = _cosy_http_request("POST", "/jobs", {
            "type": "batch",
            "scenario": scenario,
            "bases": bases,
            "variants": variants,
            "speed": speed,
            "prompt_wav": str(prompt_wav),
            "prompt_text": prompt_txt.read_text(encoding="utf-8").strip(),
        }, timeout=15)
        if code != 200:
            abort(503, f"Cosy-сервер не принял batch: {err or f'HTTP {code}'}")

        # Маркируем все сцены батча как regen — UI сразу оранжевый.
        selections = load_selections(scenario)
        for b in bases:
            selections.pop(b, None)
            selections[f"{b}::status"] = "regen"
        save_selections(scenario, selections)

        # Имитируем формат старого ответа — фронт ожидает эти поля.
        # status_file НЕ нужен — фронт всё равно поллит /api/cosyvoice-batch-status.
        return jsonify({
            "ok": True,
            "via_server": True,
            "job_id": (job_data or {}).get("job_id"),
            "model": COSYVOICE_MODEL_NAME,
            "total": len(bases),
            "bases": bases,
            "variants": variants,
            "speed": speed,
            "voice": voice_id,
            "voice_label": COSY_VOICES[voice_id]["label"],
            "prompt_wav": str(prompt_wav.relative_to(ROOT)),
            "message": (
                f"CosyVoice3 batch ({COSY_VOICES[voice_id]['label']}) через сервер: "
                f"{len(bases)} сцен, модель уже в памяти, без прогрева"
            ),
        })

    # ── СТАРЫЙ ПУТЬ: сервер недоступен → fallback на subprocess.
    # Тот же поиск интерпретатора, что и в одиночном эндпоинте.
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
        "--auto",
        "--scenario", scenario,
        "--bases", ",".join(bases),
        "--variants", str(variants),
        "--speed", str(speed),
        "--prompt-wav", str(prompt_wav),
        "--prompt-text", str(prompt_txt),
    ]

    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

    # Чистим старый batch-лог и статус, чтобы фронт не путался с прошлым прогоном.
    log_path = cosyvoice_batch_log_path(scenario)
    status_path = cosyvoice_batch_status_path(scenario)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.unlink(missing_ok=True)
    status_path.unlink(missing_ok=True)

    # Помечаем все сцены батча как regen — UI сразу нарисует оранжевый статус.
    selections = load_selections(scenario)
    for b in bases:
        selections.pop(b, None)
        selections[f"{b}::status"] = "regen"
    save_selections(scenario, selections)

    log_file = open(log_path, "ab")  # noqa: SIM115 — держим для subprocess
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
        abort(500, f"Не удалось запустить cosyvoice_runner --auto: {e}")

    print(
        f"[cosyvoice-batch] PID={pid} scenario={scenario!r} bases={len(bases)} "
        f"variants={variants} speed={speed} log={log_path.name}"
    )

    return jsonify({
        "ok": True,
        "pid": pid,
        "python_exe": python_exe,
        "model": COSYVOICE_MODEL_NAME,
        "total": len(bases),
        "bases": bases,
        "variants": variants,
        "speed": speed,
        "voice": voice_id,
        "voice_label": COSY_VOICES[voice_id]["label"],
        "prompt_wav": str(prompt_wav.relative_to(ROOT)),
        "log_file": str(log_path.relative_to(ROOT)),
        "status_file": str(status_path.relative_to(ROOT)),
        "message": (
            f"CosyVoice3 batch ({COSY_VOICES[voice_id]['label']}): {len(bases)} сцен, "
            f"скорость {speed}, одна загрузка модели"
        ),
    })


@app.route("/api/cosyvoice-batch-status/<path:scenario>")
def api_cosyvoice_batch_status(scenario: str):
    """Прогресс batch-генерации. Фронт поллит каждые 1.5 сек.

    Источник правды — _cosyvoice_batch.json, который runner пишет сам.
    Лог тейлим из _cosyvoice_batch.log, чтобы UI мог показать tail при ошибке.

    Возвращаем:
      { exists, active, done, total, completed_count, current_base, current_index,
        current_produced, completed_bases, failed, log_tail, error_hint, ... }
    """
    scenario = unquote(scenario)
    status_path = cosyvoice_batch_status_path(scenario)
    log_path = cosyvoice_batch_log_path(scenario)

    # ── Если активная batch-задача идёт через сервер — берём её прогресс
    # оттуда. У сервера нет файла _cosyvoice_batch.json, у нас один воркер
    # делает item за item, и Job.to_dict() возвращает items с current_variant.
    server_batch = _fetch_server_batch_status(scenario)
    if server_batch is not None:
        return jsonify(server_batch)

    if not status_path.exists():
        return jsonify({
            "exists": False, "active": False, "done": False,
            "total": 0, "completed_count": 0,
            "current_base": None, "current_index": 0, "current_produced": 0,
            "completed_bases": [], "failed": [],
            "log_tail": "", "error_hint": None,
        })

    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except Exception as e:
        return jsonify({
            "exists": True, "active": False, "done": False,
            "error_hint": f"не смог прочитать статус: {e}",
            "log_tail": "",
        })

    log_tail = ""
    log_mtime = 0.0
    if log_path.exists():
        try:
            raw = log_path.read_bytes()
            log_tail = raw[-8000:].decode("utf-8", errors="replace")
            log_mtime = log_path.stat().st_mtime
        except Exception:
            pass

    # Эвристика ошибки — те же маркеры, что и в одиночном статусе.
    error_hint = status.get("error")
    if not error_hint and not status.get("done") and log_tail:
        for marker in (
            "Traceback (most recent call last)", "ModuleNotFoundError",
            "ImportError", "FileNotFoundError",
            "ОТСУТСТВУЮТ ЗАВИСИМОСТИ",
        ):
            if marker in log_tail:
                error_hint = marker
                break
        if error_hint is None and log_mtime:
            silence_sec = datetime.now().timestamp() - log_mtime
            # Загрузка модели может занимать до 30 сек на холодном старте,
            # поэтому считаем «зависанием» только тишину >60 сек.
            if silence_sec > 60:
                error_hint = f"no log activity ({int(silence_sec)}s)"

    completed_bases = status.get("completed_bases", []) or []
    return jsonify({
        "exists": True,
        "active": bool(status.get("active")),
        "done": bool(status.get("done")),
        "scenario": status.get("scenario", scenario),
        "model": status.get("model", COSYVOICE_MODEL_NAME),
        "speed": status.get("speed", COSYVOICE_DEFAULT_SPEED),
        "variants": status.get("variants", COSYVOICE_DEFAULT_VARIANTS),
        "total": int(status.get("total", 0)),
        "completed_count": len(completed_bases),
        "completed_bases": completed_bases,
        "failed": status.get("failed", []) or [],
        "queue": status.get("queue", []) or [],
        "current_base": status.get("current_base"),
        "current_index": int(status.get("current_index", 0)),
        "current_produced": int(status.get("current_produced", 0)),
        "started_at": status.get("started_at"),
        "updated_at": status.get("updated_at"),
        "elapsed_sec": status.get("elapsed_sec"),
        "log_tail": log_tail,
        "log_mtime": log_mtime,
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
    manifest_file = preview_dir / "full_manifest.json"

    # Кэш через манифест: если набор source-файлов и их mtime/size не менялись,
    # не зовём ffmpeg/ffprobe — просто отдаём тот же URL. Это критично для UX
    # «Песнь целиком»: при F5 страницы плеер должен играть мгновенно, а
    # ffmpeg-сборка с ffprobe-замером длительностей занимает несколько секунд.
    # Сам набор `sources` уже отражает текущие selections (см. цикл выше), так
    # что отпечаток ловит и смену выбранных вариантов, и регенерацию mp3.
    current_fingerprint = [
        {
            "path": src.relative_to(audio_dir).as_posix(),
            "mtime": int(src.stat().st_mtime),
            "size": src.stat().st_size,
        }
        for src in sources
    ]

    cached: dict | None = None
    if out_file.exists() and manifest_file.exists():
        try:
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            if data.get("version") == 1 and data.get("sources") == current_fingerprint:
                cached = data
        except (OSError, json.JSONDecodeError):
            cached = None

    if cached is not None:
        full_path = out_file
        durations = cached.get("durations")
        starts = cached.get("starts")
        total_duration = cached.get("total_duration")
    else:
        full_path, err = concat_audio_to(out_file, sources)
        if err:
            return jsonify({"ok": False, "error": err}), 500

        # Замеряем длительность каждого исходника — фронту нужны реальные
        # тайминги, чтобы сегменты в плеере были пропорциональны и клик попадал
        # ровно в начало sentence_NN. Если ffprobe недоступен (durations ==
        # None), фронт деградирует на равномерную сетку.
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

        # Манифест пишем только после успешной сборки. Если запись упадёт —
        # не критично, в следующий раз просто пересоберём (а пользователю
        # это всё равно стоит одного ffmpeg-прохода).
        try:
            manifest_file.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "sources": current_fingerprint,
                        "durations": durations,
                        "starts": starts,
                        "total_duration": total_duration,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except OSError:
            pass

    mtime = int(full_path.stat().st_mtime)
    # Эндпоинт /audio/<scenario>?path=... — query-параметр, не URL-сегмент.
    # Раньше был сегментом, но для сценариев со слешем (части сериала)
    # werkzeug не справлялся с двумя <path:> подряд. См. audio_file.
    from urllib.parse import quote  # noqa: PLC0415 — локальный импорт
    scenario_enc = quote(scenario, safe="")
    path_enc = quote("_preview/full.mp3", safe="")
    return jsonify({
        "ok": True,
        # cache-buster через mtime, чтобы браузер не отдал старую склейку
        "url": f"/audio/{scenario_enc}?path={path_enc}&t={mtime}",
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
    for entry in iter_scenarios_by_creation(CONTENT_DIR):
        review_dir = entry.path / "images" / "review_images"
        images_md = entry.path / "prompts" / "images.md"

        if not review_dir.exists() and not images_md.exists():
            continue

        pub = load_published_state(entry.name)

        if not review_dir.exists():
            # Есть промпты, но картинок ещё нет — показываем как NEW с числом
            # сцен из markdown, чтобы пользователь мог зайти и нажать batch.
            md_data = parse_images_md(images_md)
            scene_count = len(md_data) if md_data else 0
            result.append({
                "name": entry.name,
                "display_name": entry.display_name,
                "scene_count": scene_count,
                "done": 0,
                "regen": 0,
                "pending": scene_count,
                "approved_count": 0,
                "variants_total": 0,
                "status": "new" if scene_count else "wip",
                "published": pub["published"],
                "published_at": pub["published_at"],
                "is_archived": _is_archived(entry.name),
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
        selections = load_image_selections(entry.name)
        approved = load_approved_images(entry.path)
        done, regen, pending, status = image_scenario_status(scenes, selections, approved)
        variants_total = sum(len(v) for v in scenes.values())

        result.append({
            "name": entry.name,
            "display_name": entry.display_name,
            "scene_count": len(scenes),
            "done": done,
            "regen": regen,
            "pending": pending,
            "approved_count": len(approved),
            "variants_total": variants_total,
            "status": status,
            "published": pub["published"],
            "published_at": pub["published_at"],
            "is_archived": _is_archived(entry.name),
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

    # Если у сцены в images.md нет блока `**Текст:**`, но в заголовке указан
    # маппинг `(sent_NNN ...)` — собираем текст из voiceover/texts/sentence_NNN.txt.
    # Это формат «От Хаоса до Олимпа», где scene-номер ≠ sentence-номеру
    # (одна сцена может покрывать 1-2 предложения, например хук+титул).
    scene_to_sents = parse_scene_sentence_mapping(images_md)
    sentence_text_cache: dict[int, str] = {}

    def _resolve_scene_text(base: str, md_text: str) -> str:
        if md_text:
            return md_text
        sent_nums = scene_to_sents.get(base, [])
        if not sent_nums:
            return ""
        parts_: list[str] = []
        for n in sent_nums:
            if n not in sentence_text_cache:
                sentence_text_cache[n] = load_sentence_text(scenario_dir, n)
            t = sentence_text_cache[n]
            if t:
                parts_.append(t)
        return " ".join(parts_).strip()

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
            "text": _resolve_scene_text(base, meta.get("text", "")),
            "prompt": meta.get("prompt", ""),
            "selected": selected,
            "approved": approved_variant,
            "status": status,
        })

    return jsonify({"scenario": scenario, "scenes": result})


@app.route("/image/<path:scenario>")
def image_file(scenario: str):
    """Отдаёт jpg/png/webp из review_images/<scene>/.

    Параметры query: ?scene=scene_NN&file=v1.jpg. См. audio_file —
    то же самое: с scenario, содержащим слеш («От Хаоса до Олимпа/часть_01_Хаос»),
    два path-сегмента после `<path:scenario>` ломаются — приходится
    через query-string.
    """
    scenario = unquote(scenario)
    scene = unquote(request.args.get("scene", "") or "")
    filename = unquote(request.args.get("file", "") or "")
    if not scene or not filename:
        abort(400, "Параметры ?scene= и ?file= обязательны")
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
    # Принимаем оба формата заголовков: `## Сцена 1` и `## Сцена scene_01`
    # (формат stickers.md в т.ч. использует `scene_NN` префикс).
    parts = re.split(r"^##\s+Сцена\s+(?:scene_)?(\d+)[^\n]*$", content, flags=re.MULTILINE)
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
    # См. save_selections — для частей сериала имя содержит слеш.
    path.parent.mkdir(parents=True, exist_ok=True)
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
    for entry in iter_scenarios_by_creation(CONTENT_DIR):
        video_dir = entry.path / "video"
        video_md = entry.path / "prompts" / "video.md"

        if not video_dir.exists() and not video_md.exists():
            continue

        md_data = parse_video_md(video_md) if video_md.exists() else {}
        scenes = discover_video_scenes(video_dir) if video_dir.exists() else {}
        # Подмешиваем сцены из markdown — для тех, у которых ещё нет клипов
        for base in md_data:
            scenes.setdefault(base, [])

        if not scenes:
            continue

        selections = load_video_selections(entry.name)
        done, regen, pending, status = video_scenario_status(scenes, selections)
        variants_total = sum(len(v) for v in scenes.values())
        scenes_with_clips = sum(1 for v in scenes.values() if v)
        pub = load_published_state(entry.name)

        result.append({
            "name": entry.name,
            "display_name": entry.display_name,
            "scene_count": len(scenes),
            "done": done,
            "regen": regen,
            "pending": pending,
            "approved_count": scenes_with_clips,
            "variants_total": variants_total,
            "status": status,
            "published": pub["published"],
            "published_at": pub["published_at"],
            "is_archived": _is_archived(entry.name),
        })

    return jsonify(result)


# ─── РЕЖИМ 04 · МОНТАЖ В CAPCUT ────────────────────────────────────────────
# Pipeline пока не реализован, эндпоинт — заглушка для UI хаба монтажа.
# Возвращает те же мифы, что и /api/videos/myths, но с полем `montage_step`
# (0–4), отражающим прогресс CapCut-сборки:
#   0 — материалы не готовы (voice или video не аппрувнуты)
#   1 — скелет собран (build_<myth>.py отработал; пока определяем по наличию
#       content/<myth>/montage/draft_content.json)
#   2 — переходы и SFX добавлены (enrich_<myth>.py)
#   3 — стикеры разложены
#   4 — анимация стикеров готова, мастер в content/final/<myth>.mp4
# До реальной интеграции с pipeline-скриптами используем эвристики:
# наличие final/<myth>.mp4 → 4; иначе если voice+video готовы → ready (0).


def _detect_montage_step(scenario_name: str) -> int:
    """Грубо угадываем, на каком шаге CapCut-сборки находится миф.

    Источники истины (по приоритету):
      step 4 — есть финальный мастер в content/final/
      step N — content/<myth>/montage/conveyor_state.json пишет step (1–3),
               но ТОЛЬКО если CapCut-драфт по step_1.draft_dir реально существует.
               Иначе пользователь грохнул проект в CapCut руками — снижаем до 0.
      step 1 — legacy: content/<myth>/montage/draft_content.json (старые ручные сборки)
    """
    final_dir = CONTENT_DIR / "final"
    if final_dir.exists():
        # Поддерживаем оба варианта: «<имя>.mp4» в корне final/ и подпапку.
        candidates = [
            final_dir / f"{scenario_name}.mp4",
            final_dir / scenario_name / f"{scenario_name}.mp4",
        ]
        if any(p.exists() for p in candidates):
            return 4
    state_file = CONTENT_DIR / scenario_name / "montage" / "conveyor_state.json"
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            step = max(0, min(4, int(data.get("step", 0))))
            step_1 = data.get("step_1") or {}
            draft_dir_str = step_1.get("draft_dir")
            if draft_dir_str:
                draft_file = Path(draft_dir_str) / "draft_content.json"
                if not draft_file.exists():
                    # Пользователь удалил проект в CapCut → state-файл протух.
                    return 0
            return step
        except Exception:
            pass
    draft = CONTENT_DIR / scenario_name / "montage" / "draft_content.json"
    if draft.exists():
        return 1
    return 0


@app.route("/api/montage/myths")
def api_montage_myths():
    """Список мифов для хаба монтажа.

    Берём пересечение мифов, у которых есть аппрув-озвучка И аппрув-видео:
    без этих двух «входов» pipeline всё равно не запустить. Каждому
    добавляем поле `montage_step` (см. `_detect_montage_step`) — UI рисует
    по нему статус «в работе / готов / новый».

    Базовая статистика (`scene_count`, `done`, …) переиспользует данные из
    видео-режима — это то же количество шотов, что и в ревью видео.
    """
    result = []
    for entry in iter_scenarios_by_creation(CONTENT_DIR):
        video_dir = entry.path / "video"
        video_md = entry.path / "prompts" / "video.md"

        # Минимум для монтажа — наличие хотя бы прампт-файла видео.
        # Если нет даже video.md — миф ещё не дошёл до стадии озвучки+видео,
        # в хабе монтажа его показывать рано.
        if not video_dir.exists() and not video_md.exists():
            continue

        md_data = parse_video_md(video_md) if video_md.exists() else {}
        scenes = discover_video_scenes(video_dir) if video_dir.exists() else {}
        for base in md_data:
            scenes.setdefault(base, [])

        if not scenes:
            continue

        selections = load_video_selections(entry.name)
        done, regen, pending, video_status = video_scenario_status(scenes, selections)
        variants_total = sum(len(v) for v in scenes.values())
        scenes_with_clips = sum(1 for v in scenes.values() if v)
        pub = load_published_state(entry.name)
        montage_step = _detect_montage_step(entry.name)

        # Аудио считается отдельно: в монтажном хабе «Аудио sentence»
        # это число sentence-файлов с аппрув-озвучкой в approved_sentences/,
        # а не число видео-сцен с выбранным шотом. Source of truth — папка
        # voiceover/audio/approved_sentences/, total — voiceover/texts/.
        approved_audio = load_approved_sentences(entry.path)
        audio_done = len(approved_audio)
        audio_total = len(discover_sentences_from_texts(entry.path))
        if audio_total == 0:
            audio_total = audio_done or len(scenes)

        # Статус карточки в хабе монтажа маппится из montage_step:
        #   4   → ready (мастер готов)
        #   1–3 → in_progress (pipeline начат, не закончен)
        #   0 + video готов → ready (можно начинать шаг 1)
        #   0 + video не готов → wip (материалы ещё не собраны)
        if montage_step == 4:
            status = "ready"
        elif montage_step >= 1:
            status = "in_progress"
        elif video_status == "ready":
            status = "ready"
        else:
            status = "wip"

        result.append({
            "name": entry.name,
            "display_name": entry.display_name,
            "scene_count": len(scenes),
            "done": done,
            "regen": regen,
            "pending": pending,
            "approved_count": scenes_with_clips,
            "variants_total": variants_total,
            "status": status,
            "published": pub["published"],
            "published_at": pub["published_at"],
            "is_archived": _is_archived(entry.name),
            # Поля, специфичные для монтажа:
            "montage_step": montage_step,
            "montage_total_steps": 4,
            "audio_done": audio_done,
            "audio_total": audio_total,
        })

    return jsonify(result)


# ── ШАГ 1 КОНВЕЙЕРА: «Скелет» CapCut-проекта ──────────────────────────
# Запускает automation/conveyor/step_1_build.py в подпроцессе. Скрипт
# создаёт CapCut-черновик `AUTO <миф>` со скелетом (voice + main + music +
# intro-капс + halftone + karaoke). Blocking-вызов, длительность 10-60 с
# (с whisper-моделью — до нескольких минут).

CONVEYOR_DIR = ROOT / "automation" / "conveyor"


@app.route("/api/montage/<path:scenario>/step/1", methods=["POST"])
def api_montage_step_1(scenario: str):
    """Запускает шаг 1 (скелет) для указанного мифа.

    Body (json, опционально):
      {"karaoke": "auto"|"whisper"|"equi"|"none", "name": "AUTO ..."}

    Возвращает {ok, message, stdout, stderr, project_name, exit_code}.
    Ошибки от скрипта (exit_code != 0) приходят с HTTP 200 + ok=False, чтобы
    UI мог показать stderr в модалке вместо общего 500.
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.is_dir():
        abort(404, description=f"Нет папки сценария: {scenario}")

    body = request.get_json(silent=True) or {}
    karaoke_mode = body.get("karaoke", "auto")
    if karaoke_mode not in ("auto", "whisper", "equi", "none"):
        return jsonify({"ok": False, "message": f"Неизвестный karaoke-режим: {karaoke_mode}"}), 400
    project_name = body.get("name") or f"AUTO {scenario}"

    script = CONVEYOR_DIR / "step_1_build.py"
    if not script.is_file():
        return jsonify({"ok": False, "message": f"Не нашёл скрипт {script}"}), 500

    cmd = [
        sys.executable,
        str(script),
        "--scenario", scenario,
        "--karaoke", karaoke_mode,
        "--name", project_name,
    ]
    print(f"[montage] step 1 → {' '.join(cmd)}")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(ROOT),
            timeout=20 * 60,  # 20 минут — на случай whisper-medium на медленной GPU
        )
    except subprocess.TimeoutExpired as ex:
        return jsonify({
            "ok": False,
            "message": "Скрипт не завершился за 20 минут — прерван.",
            "stdout": ex.stdout or "",
            "stderr": ex.stderr or "",
        }), 200
    except Exception as ex:
        return jsonify({"ok": False, "message": f"Не удалось запустить скрипт: {ex}"}), 500

    ok = proc.returncode == 0
    msg = (
        f"Шаг 1 завершён: «{project_name}» собран в CapCut."
        if ok
        else f"Скрипт упал (exit={proc.returncode}). Подробности в логе."
    )
    return jsonify({
        "ok": ok,
        "exit_code": proc.returncode,
        "message": msg,
        "project_name": project_name,
        "stdout": proc.stdout or "",
        "stderr": proc.stderr or "",
    })


# ── РЕДАКТОР ПЛАНА: GET/POST для content/<миф>/montage/plan.json ──────
# Plan хранит ручные правки start_from / speed_override для каждого
# scene_NN_vM-шота. Применяется в automation/conveyor/step_1_build.py
# (build_skeleton) перед записью CapCut-сегментов. Структура и логика —
# в automation/conveyor/shared.py (build_plan_metadata, load/save_plan).

def _import_conveyor_shared():
    """Лениво подкладываем automation/conveyor/ в sys.path и импортим shared."""
    conveyor_dir = ROOT / "automation" / "conveyor"
    if str(conveyor_dir) not in sys.path:
        sys.path.insert(0, str(conveyor_dir))
    import shared  # type: ignore  # noqa: WPS433
    return shared


@app.route("/api/montage/<path:scenario>/plan", methods=["GET"])
def api_montage_plan_get(scenario: str):
    """Возвращает план + метаданные всех шотов (для UI редактора).

    Длительности видео/аудио считаются на лету (mutagen + pymediainfo),
    что занимает 0.3-1 сек на ~20 шотов — приемлемо для редкого открытия.
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.is_dir():
        abort(404, description=f"Нет папки сценария: {scenario}")

    try:
        shared = _import_conveyor_shared()
    except ImportError as ex:
        return jsonify({"ok": False, "message": f"Не подключился shared.py: {ex}"}), 500

    try:
        meta = shared.build_plan_metadata(scenario)
    except SystemExit as ex:
        return jsonify({"ok": False, "message": str(ex)}), 400
    except Exception as ex:
        return jsonify({"ok": False, "message": f"Сбой при сборе плана: {ex}"}), 500
    return jsonify({"ok": True, **meta})


def _resolve_capcut_draft(scenario: str) -> Path | None:
    """Путь к draft_content.json живого CapCut-проекта мифа.

    Источник истины — content/<myth>/montage/conveyor_state.json →
    step_1.draft_dir (туда build_<myth>.py кладёт проект). Возвращаем None,
    если состояние/драфт ещё не созданы.
    """
    state_file = CONTENT_DIR / scenario / "montage" / "conveyor_state.json"
    if not state_file.exists():
        return None
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return None
    draft_dir = (data.get("step_1") or {}).get("draft_dir")
    if not draft_dir:
        return None
    draft_file = Path(draft_dir) / "draft_content.json"
    return draft_file if draft_file.exists() else None


def _import_transitions_io():
    """Логика переходов живёт в automation/conveyor/transitions.py — её же
    использует step_2_enrich.py. Подкладываем conveyor в sys.path и импортим."""
    import importlib
    conveyor_dir = str(ROOT / "automation" / "conveyor")
    if conveyor_dir not in sys.path:
        sys.path.insert(0, conveyor_dir)
    return importlib.import_module("transitions")


@app.route("/api/montage/<path:scenario>/transitions", methods=["GET"])
def api_montage_transitions(scenario: str):
    """Реальные переходы между сценами из живого CapCut-драфта + каталог.

    Читаем draft_content.json (его пользователь правит руками в CapCut) и
    собираем стыки по главной видео-дорожке. Возвращаем список
    {from, to, effect_id, label, duration} и каталог канон-переходов для
    редактора.
    """
    scenario = unquote(scenario)
    if not (CONTENT_DIR / scenario).is_dir():
        abort(404, description=f"Нет папки сценария: {scenario}")

    tio = _import_transitions_io()
    draft_file = _resolve_capcut_draft(scenario)
    if draft_file is None:
        return jsonify({"ok": True, "ready": False, "transitions": [],
                        "catalog": tio.TRANSITION_CATALOG})

    try:
        draft = json.loads(draft_file.read_text(encoding="utf-8"))
    except Exception as ex:
        return jsonify({"ok": False, "message": f"Не прочитал draft_content.json: {ex}"}), 500

    result = tio.read_transitions(draft)
    picked = sum(1 for r in result if r["effect_id"])
    return jsonify({
        "ok": True,
        "ready": True,
        "transitions": result,
        "catalog": tio.TRANSITION_CATALOG,
        "picked": picked,
        "total": len(result),
    })


def _validate_transition_plan(tio, plan_in):
    """Чистит план из тела запроса. Возвращает (plan|None, error_message|None)."""
    if not isinstance(plan_in, list):
        return None, "transitions должен быть массивом"
    plan: list[dict] = []
    for e in plan_in:
        if not isinstance(e, dict):
            continue
        try:
            idx = int(e.get("index"))
        except (TypeError, ValueError):
            continue
        eid = e.get("effect_id")
        if eid in (None, "", "cut"):
            plan.append({"index": idx, "effect_id": None})
            continue
        eid = str(eid)
        if eid not in tio.CATALOG_BY_ID:
            return None, f"effect_id {eid} вне каталога"
        dur = e.get("duration")
        try:
            dur = float(dur) if dur not in (None, "") else None
        except (TypeError, ValueError):
            dur = None
        plan.append({"index": idx, "effect_id": eid, "duration": dur})
    return plan, None


def _write_transition_plan_file(scenario: str, plan: list[dict]) -> Path:
    """Пишет план в content/<миф>/montage/transition_plan.json (его читает step_2)."""
    state_dir = CONTENT_DIR / scenario / "montage"
    state_dir.mkdir(parents=True, exist_ok=True)
    plan_file = state_dir / "transition_plan.json"
    plan_file.write_text(json.dumps({"transitions": plan}, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    return plan_file


def _run_step_2(scenario: str, plan_file: Path):
    """Запускает step_2_enrich.py (он сам решает, надо ли закрывать/открывать
    CapCut через WriteGuard). Возвращает (ok, proc|None, message)."""
    script = CONVEYOR_DIR / "step_2_enrich.py"
    if not script.is_file():
        return False, None, f"Не нашёл скрипт {script}"
    cmd = [sys.executable, str(script), "--scenario", scenario, "--plan-file", str(plan_file)]
    print(f"[montage] step 2 → {' '.join(cmd)}")
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(ROOT), timeout=5 * 60,
        )
    except subprocess.TimeoutExpired:
        return False, None, "Шаг 2 не завершился за 5 минут — прерван."
    except Exception as ex:
        return False, None, f"Не удалось запустить шаг 2: {ex}"
    return proc.returncode == 0, proc, None


@app.route("/api/montage/<path:scenario>/transitions", methods=["POST"])
def api_montage_transitions_save(scenario: str):
    """Сохраняет план переходов и запускает шаг 2 (enrich).

    Body: {"transitions": [{"index": 0, "effect_id": "...", "duration": 0.8},
    ...]} — полный желаемый список стыков (index 0-based). effect_id=null/
    отсутствует = Cut. Скрипт step_2_enrich.py сам закроет CapCut, если он
    открыт, запишет переходы + SFX и перезапустит CapCut с открытием проекта.
    """
    scenario = unquote(scenario)
    if not (CONTENT_DIR / scenario).is_dir():
        abort(404, description=f"Нет папки сценария: {scenario}")

    tio = _import_transitions_io()
    if _resolve_capcut_draft(scenario) is None:
        return jsonify({"ok": False, "message": "CapCut-драфт не найден — сначала запусти шаг 1"}), 400

    body = request.get_json(silent=True) or {}
    plan, err = _validate_transition_plan(tio, body.get("transitions"))
    if err:
        return jsonify({"ok": False, "message": err}), 400

    plan_file = _write_transition_plan_file(scenario, plan)
    ok, proc, msg = _run_step_2(scenario, plan_file)
    if proc is None:
        return jsonify({"ok": False, "message": msg}), 500
    if not ok:
        return jsonify({"ok": False,
                        "message": f"Шаг 2 упал (exit={proc.returncode}). Подробности в логе.",
                        "stdout": proc.stdout or "", "stderr": proc.stderr or ""}), 200

    draft_file = _resolve_capcut_draft(scenario)
    result = []
    if draft_file is not None:
        try:
            result = tio.read_transitions(json.loads(draft_file.read_text(encoding="utf-8")))
        except Exception:
            result = []
    picked = sum(1 for r in result if r["effect_id"])
    return jsonify({"ok": True, "transitions": result, "picked": picked,
                    "total": len(result), "stdout": proc.stdout or ""})


@app.route("/api/montage/<path:scenario>/transitions/apply-one", methods=["POST"])
def api_montage_transition_apply_one(scenario: str):
    """Применяет ОДИН стык к живому драфту, не трогая прочие.

    Body: {"index": 3, "effect_id": "..."|null, "duration": 0.8}. Берём
    текущую раскладку из драфта, подменяем только указанный стык и
    запускаем шаг 2 — остальные стыки остаются как в драфте (а не как в
    несохранённом состоянии редактора). Аналог точечного patch-shot шага 1;
    step_2_enrich.py сам управляет CapCut (закрыть/записать/открыть).
    """
    scenario = unquote(scenario)
    if not (CONTENT_DIR / scenario).is_dir():
        abort(404, description=f"Нет папки сценария: {scenario}")

    tio = _import_transitions_io()
    draft_file = _resolve_capcut_draft(scenario)
    if draft_file is None:
        return jsonify({"ok": False, "message": "CapCut-драфт не найден — сначала запусти шаг 1"}), 400

    body = request.get_json(silent=True) or {}
    try:
        target_idx = int(body.get("index"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "index обязателен"}), 400
    eid = body.get("effect_id")
    if eid in (None, "", "cut"):
        eid = None
    else:
        eid = str(eid)
        if eid not in tio.CATALOG_BY_ID:
            return jsonify({"ok": False, "message": f"effect_id {eid} вне каталога"}), 400
    dur = body.get("duration")
    try:
        dur = float(dur) if dur not in (None, "") else None
    except (TypeError, ValueError):
        dur = None

    try:
        draft = json.loads(draft_file.read_text(encoding="utf-8"))
    except Exception as ex:
        return jsonify({"ok": False, "message": f"Не прочитал draft: {ex}"}), 500

    # План = текущий драфт, в котором меняем только target_idx.
    current = tio.read_transitions(draft)
    if target_idx < 0 or target_idx >= len(current):
        return jsonify({"ok": False, "message": f"index {target_idx} вне диапазона стыков"}), 400
    plan = []
    for i, r in enumerate(current):
        if i == target_idx:
            plan.append({"index": i, "effect_id": eid, "duration": dur})
        else:
            plan.append({"index": i, "effect_id": r["effect_id"], "duration": r["duration"]})

    plan_file = _write_transition_plan_file(scenario, plan)
    ok, proc, msg = _run_step_2(scenario, plan_file)
    if proc is None:
        return jsonify({"ok": False, "message": msg}), 500
    if not ok:
        return jsonify({"ok": False,
                        "message": f"Шаг 2 упал (exit={proc.returncode}). Подробности в логе.",
                        "stdout": proc.stdout or "", "stderr": proc.stderr or ""}), 200

    result = []
    df = _resolve_capcut_draft(scenario)
    if df is not None:
        try:
            result = tio.read_transitions(json.loads(df.read_text(encoding="utf-8")))
        except Exception:
            result = []
    picked = sum(1 for r in result if r["effect_id"])
    return jsonify({"ok": True, "index": target_idx, "transitions": result,
                    "picked": picked, "total": len(result), "stdout": proc.stdout or ""})


@app.route("/api/montage/<path:scenario>/plan", methods=["POST"])
def api_montage_plan_save(scenario: str):
    """Сохраняет план правок шотов.

    Body: {"shots": {"scene_03_v1": {"start_from": 1.0, "speed_override": null}, ...}}

    Валидация: start_from ∈ [0, 30], speed_override ∈ [0.25, 4.0] или null.
    Шоты с (start_from==0 AND speed_override==null) удаляются из плана —
    это «авто», хранить нечего.
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.is_dir():
        abort(404, description=f"Нет папки сценария: {scenario}")

    body = request.get_json(silent=True) or {}
    shots_in = body.get("shots") or {}
    if not isinstance(shots_in, dict):
        return jsonify({"ok": False, "message": "shots должен быть object"}), 400

    cleaned: dict[str, dict] = {}
    for key, entry in shots_in.items():
        if not isinstance(entry, dict):
            continue
        try:
            start = float(entry.get("start_from", 0.0) or 0.0)
        except (TypeError, ValueError):
            start = 0.0
        start = max(0.0, min(30.0, start))
        raw = entry.get("speed_override")
        if raw in (None, "", "auto"):
            speed = None
        else:
            try:
                speed = float(raw)
            except (TypeError, ValueError):
                speed = None
            if speed is not None:
                speed = max(0.25, min(4.0, speed))
        # variant: "v2" (или null/"" = версия не переопределена).
        variant = entry.get("variant")
        if variant in (None, "", "auto"):
            variant = None
        else:
            variant = str(variant)
            if not variant.startswith("v"):
                variant = f"v{variant}"
        # Полный автомат (нет ни старта, ни скорости, ни версии) — не храним.
        if start == 0.0 and speed is None and variant is None:
            continue
        rec: dict = {"start_from": round(start, 3), "speed_override": speed}
        if variant is not None:
            rec["variant"] = variant
        cleaned[str(key)] = rec

    shared = _import_conveyor_shared()
    shared.save_plan(scenario, {"shots": cleaned})
    return jsonify({"ok": True, "shots": cleaned, "edited_count": len(cleaned)})


@app.route("/api/montage/<path:scenario>/patch-shot", methods=["POST"])
def api_montage_patch_shot(scenario: str):
    """Точечный патч одного шота в УЖЕ собранном CapCut-проекте.

    Меняет только source_timerange + speed одного видеосегмента — не
    пересобирает весь шаг 1, не трогает переходы/караоке/стикеры.

    Body: {"shot_key": "scene_07", "start_from": 1.0, "speed_override": 0.8, "variant": "v2"}
      shot_key — базовое имя сцены (scene_NN), версия отдельным полем variant.
      speed_override = null → авто (обрезка или замедление по длине голоса).
      variant = null → версия не переопределена.

    Перед патчем правка сохраняется в plan.json (чтобы полная пересборка
    дала тот же результат). Затем запускается patch_shot.py для этой сцены.
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.is_dir():
        abort(404, description=f"Нет папки сценария: {scenario}")

    shared = _import_conveyor_shared()

    body = request.get_json(silent=True) or {}
    raw_key = str(body.get("shot_key") or "").strip()
    if not raw_key:
        return jsonify({"ok": False, "message": "shot_key обязателен"}), 400
    scene_key = shared.plan_scene_key(raw_key)  # scene_07_v2 → scene_07

    try:
        start = float(body.get("start_from", 0.0) or 0.0)
    except (TypeError, ValueError):
        start = 0.0
    start = max(0.0, min(30.0, start))
    raw = body.get("speed_override")
    if raw in (None, "", "auto"):
        speed = None
    else:
        try:
            speed = float(raw)
        except (TypeError, ValueError):
            speed = None
        if speed is not None:
            speed = max(0.25, min(4.0, speed))
    variant = body.get("variant")
    if variant in (None, "", "auto"):
        variant = None
    else:
        variant = str(variant)
        if not variant.startswith("v"):
            variant = f"v{variant}"

    # 1. Обновляем запись в plan.json (merge с существующим планом).
    plan = shared.load_plan(scenario)
    shots = plan.get("shots") or {}
    if start == 0.0 and speed is None and variant is None:
        shots.pop(scene_key, None)  # вернули к авто → убираем запись
    else:
        rec = {"start_from": round(start, 3), "speed_override": speed}
        if variant is not None:
            rec["variant"] = variant
        shots[scene_key] = rec
    shared.save_plan(scenario, {"shots": shots})

    # 2. Запускаем точечный патч драфта.
    script = CONVEYOR_DIR / "patch_shot.py"
    if not script.is_file():
        return jsonify({"ok": False, "message": f"Не нашёл скрипт {script}"}), 500
    cmd = [sys.executable, str(script), "--scenario", scenario, "--shot", scene_key]
    print(f"[montage] patch-shot → {' '.join(cmd)}")
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", cwd=str(ROOT), timeout=120,
        )
    except Exception as ex:
        return jsonify({"ok": False, "message": f"Не удалось запустить патч: {ex}"}), 500

    ok = proc.returncode == 0
    return jsonify({
        "ok": ok,
        "exit_code": proc.returncode,
        "message": (f"Сцена {scene_key} обновлена в CapCut."
                    if ok else f"Патч упал (exit={proc.returncode})."),
        "shot_key": scene_key,
        "stdout": proc.stdout or "",
        "stderr": proc.stderr or "",
    })


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

    # В формате «От Хаоса до Олимпа» текста нет ни в video.md, ни в images.md
    # как блок `**Текст:**` — он лежит в voiceover/texts/sentence_NNN.txt, и
    # mapping scene↔sentence закодирован в заголовке сцены `(sent_NNN — ...)`.
    # Парсим заголовки и подмешиваем тексты из sentence-файлов.
    scene_to_sents = parse_scene_sentence_mapping(images_md)
    if not scene_to_sents:
        # Если в images.md mapping не нашёлся, пробуем video.md (в нём
        # часто такой же формат заголовков).
        scene_to_sents = parse_scene_sentence_mapping(video_md)
    sentence_text_cache: dict[int, str] = {}

    def _resolve_scene_text(base: str, md_text: str) -> str:
        if md_text:
            return md_text
        sent_nums = scene_to_sents.get(base, [])
        if not sent_nums:
            return ""
        parts_: list[str] = []
        for n in sent_nums:
            if n not in sentence_text_cache:
                sentence_text_cache[n] = load_sentence_text(scenario_dir, n)
            t = sentence_text_cache[n]
            if t:
                parts_.append(t)
        return " ".join(parts_).strip()

    selections = load_video_selections(scenario)

    result = []
    for base in sorted(raw_scenes.keys(), key=scene_sort_key):
        meta = md_data.get(base, {})
        text_from_video = meta.get("text", "")
        text_from_image = image_meta.get(base, {}).get("text", "")
        resolved_text = _resolve_scene_text(
            base, text_from_video or text_from_image
        )
        selected = selections.get(base)
        status = selections.get(f"{base}::status")
        if status is None:
            status = "done" if selected else ("pending" if raw_scenes[base] else "empty")
        result.append({
            "base": base,
            "variants": raw_scenes[base],
            "image": meta.get("image", ""),
            "text": resolved_text,
            "prompt": meta.get("prompt", ""),
            "sounds": meta.get("sounds", ""),
            "selected": selected,
            "status": status,
        })

    return jsonify({"scenario": scenario, "scenes": result})


@app.route("/video/<path:scenario>")
def video_file(scenario: str):
    """Отдаёт mp4/webm/mov из content/<миф>/video/. См. audio_file для
    объяснения, почему filename через ?file= а не отдельный path-сегмент.
    """
    scenario = unquote(scenario)
    filename = unquote(request.args.get("file", "") or "")
    if not filename:
        abort(400, "Параметр ?file= обязателен")
    video_dir = CONTENT_DIR / scenario / "video"
    if not video_dir.exists():
        abort(404)
    return send_from_directory(str(video_dir), filename, conditional=True)


@app.route("/video-thumb/<path:scenario>")
def video_thumb_file(scenario: str):
    """Отдаёт картинку-источник (image-to-video) для превью сцены.

    Берём из images/approved_images/. filename (через ?file=) — это путь из
    `**Изображение:**` в video.md, либо просто имя файла approved-варианта.
    """
    scenario = unquote(scenario)
    filename = unquote(request.args.get("file", "") or "")
    if not filename:
        abort(400, "Параметр ?file= обязателен")
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
    POST → принимает {on: bool}, сохраняет состояние, при on=true ещё и
           физически переносит миф в `content/архив/<миф>/` вместе с
           selections-файлами. При on=false миф остаётся в архиве, просто
           снимается флаг.

    Возвращает {ok, published, published_at, name, archived?, moved?}. Поле
    `name` важно для фронта: после переноса имя сценария меняется
    («Икар и Дедал» → «архив/Икар и Дедал»), фронт обязан обновить
    state.summaries и активный сценарий.

    Серии (имя со слешем) не архивируем — discovery работает на 2 уровнях,
    архив серии = 3 уровня. Возвращаем 400 с понятным сообщением.
    """
    scenario = unquote(scenario)
    if not (CONTENT_DIR / scenario).exists():
        abort(404, description=f"Сценарий {scenario!r} не найден")

    if request.method == "GET":
        return jsonify({"name": scenario, **load_published_state(scenario)})

    payload = request.get_json(silent=True) or {}
    on = bool(payload.get("on"))

    # Снятие публикации — миф НЕ возвращается в общий пул. Только флаг.
    if not on:
        state = save_published_state(scenario, False)
        return jsonify({"ok": True, "name": scenario, **state})

    # Включение публикации. Если миф уже в архиве — просто ставим флаг.
    if _is_archived(scenario):
        state = save_published_state(scenario, True)
        return jsonify({
            "ok": True, "name": scenario, "archived": True, "moved": [],
            **state,
        })

    # Свежая публикация одиночного мифа — переносим в архив.
    # Для частей сериала («От Хаоса до Олимпа/часть_01_Хаос») просто ставим
    # флаг published без переноса — архивация сериалов не реализована
    # (discovery 2-уровневое, архив будет 3-уровневым), но пометка
    # «опубликован» полезна для UI и аналитики.
    if "/" in scenario:
        state = save_published_state(scenario, True)
        return jsonify({
            "ok": True,
            "name": scenario,
            "archived": False,
            "moved": [],
            **state,
        })

    try:
        new_name, moved = archive_scenario(scenario)
    except (ValueError, FileNotFoundError, FileExistsError) as e:
        abort(400, description=str(e))
    except OSError as e:
        # Файл/папка занята другим процессом — даём пользователю шанс
        # закрыть плеер/проводник и повторить.
        abort(409, description=f"Не удалось перенести {scenario!r}: {e}")

    # Записываем флаг публикации УЖЕ под новым именем — старого published-
    # файла больше нет (он переехал archive_scenario'м, но мог не существовать
    # вовсе, если миф публикуется впервые).
    state = save_published_state(new_name, True)
    return jsonify({
        "ok": True,
        "name": new_name,
        "archived": True,
        "moved": moved,
        **state,
    })


# ─── Управление CosyVoice-сервером (внешний процесс на 5001) ──────────────
# Сервер живёт отдельно (automation/cosyvoice_server.py), грузит модель один
# раз и обслуживает webapp по HTTP. На стартовой странице UI показывает
# индикатор статуса и кнопку «Запустить сервер», если он не отвечает.


def _cosy_server_is_ready() -> bool:
    """Жив ли cosy-сервер и готова ли модель.

    Использует короткий timeout — если webapp вызывает это перед каждой
    генерацией, не хочется тормозить UI на 2 сек, когда сервер просто не запущен.
    """
    code, data, _ = _cosy_http_get("/health", timeout=1.0)
    return code == 200 and bool((data or {}).get("model_loaded"))


def _fetch_server_batch_status(scenario: str) -> dict | None:
    """Прогресс активной/недавней batch-задачи сценария на cosy-сервере.

    Возвращает dict в формате /api/cosyvoice-batch-status (для фронта) или
    None, если сервер недоступен / у сценария нет batch-задач.

    Логика:
      1. Сначала смотрим активные джобы сценария — если есть batch с
         queued/running, берём его.
      2. Иначе смотрим последние джобы (limit=5), ищем batch — это для
         случая когда генерация только что завершилась и UI ещё хочет
         показать «done».
    """
    code, active, _ = _cosy_http_get(
        f"/scenarios/{scenario}/active", timeout=1.0
    )
    if code != 200:
        return None

    batch_job_id: str | None = None
    if isinstance(active, dict) and active:
        # active: {base: job_id}. Если все base указывают на один job_id —
        # это batch. Если только одна сцена и одна job — это single regen.
        unique_ids = set(active.values())
        if len(unique_ids) == 1:
            batch_job_id = next(iter(unique_ids))

    # Если активной нет — ищем недавнюю batch в истории.
    if batch_job_id is None:
        code, listing, _ = _cosy_http_get(
            f"/jobs?scenario={scenario}&limit=5", timeout=1.0
        )
        if code != 200 or not isinstance(listing, dict):
            return None
        for j in listing.get("jobs", []):
            if j.get("type") == "batch":
                batch_job_id = j.get("id")
                break

    if not batch_job_id:
        return None

    code, job, _ = _cosy_http_get(f"/jobs/{batch_job_id}", timeout=1.0)
    if code != 200 or not isinstance(job, dict):
        return None

    if job.get("type") != "batch":
        # Это single-job, не batch — фронту не нужно (он поллит single-status).
        return None

    items = job.get("items", []) or []
    completed_bases = [it["base"] for it in items if it.get("status") == "done"]
    failed = [
        {"base": it["base"], "error": it.get("error")}
        for it in items if it.get("status") == "failed"
    ]
    queue = [it["base"] for it in items if it.get("status") == "queued"]
    current_item_index = next(
        (i for i, it in enumerate(items) if it.get("status") == "running"),
        None,
    )
    current_item = items[current_item_index] if current_item_index is not None else None
    is_done = job.get("status") in ("done", "failed", "cancelled")

    return {
        "exists": True,
        "via_server": True,
        "active": not is_done,
        "done": is_done,
        "scenario": job.get("scenario", scenario),
        "model": COSYVOICE_MODEL_NAME,
        "speed": job.get("speed", COSYVOICE_DEFAULT_SPEED),
        "variants": job.get("variants", COSYVOICE_DEFAULT_VARIANTS),
        "total": len(items),
        "completed_count": len(completed_bases),
        "completed_bases": completed_bases,
        "failed": failed,
        "queue": queue,
        "current_base": current_item.get("base") if current_item else None,
        "current_index": current_item_index or 0,
        "current_produced": (current_item or {}).get("current_variant", 0),
        "started_at": job.get("started_at"),
        "updated_at": None,
        "elapsed_sec": (job.get("progress") or {}).get("total_elapsed_sec"),
        # У сервера один общий лог, не per-batch. Фронту хвост не показываем,
        # но индикатор всё равно работает по completed_count/current_*.
        "log_tail": "",
        "log_mtime": 0,
        "error_hint": job.get("error"),
        "job_id": batch_job_id,
    }


def _cosy_prompt_text_str() -> str:
    """Текст prompt для CosyVoice. Читаем заново, чтобы ловить правки в TTS.txt."""
    try:
        return COSYVOICE_PROMPT_TXT.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _cosy_http_get(path: str, timeout: float = 2.0) -> tuple[int, dict | None, str | None]:
    """Запрос к cosy-серверу. Возвращает (status_code, json_or_none, error_or_none)."""
    if _urlreq is None:
        return 0, None, "urllib не доступен"
    url = f"{COSY_SERVER_URL}{path}"
    try:
        req = _urlreq.Request(url, method="GET")
        with _urlreq.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body), None
    except _urlerr.URLError as e:
        return 0, None, f"{e.__class__.__name__}: {getattr(e, 'reason', e)}"
    except (json.JSONDecodeError, OSError, ValueError) as e:
        return 0, None, f"{type(e).__name__}: {e}"


def _cosy_http_request(
    method: str, path: str, payload: dict | None = None, timeout: float = 5.0
) -> tuple[int, dict | None, str | None]:
    """POST/DELETE с JSON body. См. _cosy_http_get."""
    if _urlreq is None:
        return 0, None, "urllib не доступен"
    url = f"{COSY_SERVER_URL}{path}"
    body = json.dumps(payload or {}).encode("utf-8") if payload is not None else None
    try:
        req = _urlreq.Request(
            url,
            method=method,
            data=body,
            headers={"Content-Type": "application/json"} if body is not None else {},
        )
        with _urlreq.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw) if raw else None
            return resp.status, data, None
    except _urlerr.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = str(e)
        return e.code, None, err_body[:400]
    except _urlerr.URLError as e:
        return 0, None, f"{e.__class__.__name__}: {getattr(e, 'reason', e)}"
    except (json.JSONDecodeError, OSError, ValueError) as e:
        return 0, None, f"{type(e).__name__}: {e}"


@app.route("/api/cosyvoice-voices")
def api_cosyvoice_voices():
    """Список голосов для UI-селектора. На каждый голос отдаём наличие
    файлов — UI может подсветить отсутствующие и не дать их выбрать."""
    voices = []
    for vid, cfg in COSY_VOICES.items():
        wav = cfg["dir"] / "TTS.mp3"
        txt = cfg["dir"] / "TTS.txt"
        voices.append({
            "id": vid,
            "label": cfg["label"],
            "available": wav.exists() and txt.exists(),
            "prompt_wav": str(wav.relative_to(ROOT)),
            "prompt_text_file": str(txt.relative_to(ROOT)),
        })
    return jsonify({"voices": voices, "default": COSY_DEFAULT_VOICE})


@app.route("/api/cosyvoice-server/health")
def api_cosyvoice_server_health():
    """Опрос cosy-сервера. UI поллит это на стартовой странице.

    Возвращает:
      reachable=False — сервер не отвечает (не запущен или порт занят чем-то ещё)
      reachable=True, model_loaded=False — сервер живой, модель ещё прогревается
      reachable=True, model_loaded=True  — всё готово
    """
    code, data, err = _cosy_http_get("/health", timeout=1.5)
    if code == 200 and data:
        return jsonify({
            "reachable": True,
            "url": COSY_SERVER_URL,
            "model_loaded": bool(data.get("model_loaded")),
            "model_error": data.get("model_error"),
            "uptime_sec": data.get("uptime_sec"),
            "jobs_total": data.get("jobs_total"),
            "queue_len": data.get("queue_len"),
        })
    return jsonify({
        "reachable": False,
        "url": COSY_SERVER_URL,
        "error": err or f"HTTP {code}",
    })


# ─── Демон-режим cosy-сервера ─────────────────────────────────────────────
# Сервер запускаем НАПРЯМУЮ как detached-процесс без своей консоли. Так он
# переживает закрытие webapp / любого окна и живёт до явного /stop.
# Логи идут в файл, PID сохраняем в файл для последующего kill.

COSY_SERVER_PY = ROOT / "automation" / "cosyvoice_server.py"
COSY_SERVER_LOG = ROOT / "automation" / "_cosyvoice_server.log"
COSY_SERVER_PID_FILE = ROOT / "automation" / "_cosyvoice_server.pid"


def _resolve_cosy_python(prefer_windowless: bool = False) -> Path | None:
    """Выбираем интерпретатор для cosy-сервера.

    Приоритет: env COSYVOICE_PYTHON > стандартный ~/cosyvoice-venv > None.
    Возвращаем None, если ни одного нет — UI покажет ошибку.

    Если prefer_windowless=True, пытаемся найти `pythonw.exe` рядом с
    `python.exe`. `pythonw.exe` — это GUI-subsystem Python, ОС никогда не
    создаёт для него окно консоли. Идеально для демона:
      - python.exe + CREATE_NO_WINDOW: Windows всё равно может показать
        окно при определённых настройках default-терминала (Windows Terminal
        в Win11 любит перехватывать любой console-процесс).
      - pythonw.exe: окна нет физически, никакой default-terminal не помогает.
    """
    env_val = os.environ.get("COSYVOICE_PYTHON")
    candidate: Path | None = None
    if env_val:
        p = Path(env_val)
        if p.exists():
            candidate = p
    if candidate is None:
        default_venv = Path.home() / "cosyvoice-venv" / "Scripts" / "python.exe"
        if default_venv.exists():
            candidate = default_venv
    if candidate is None:
        return None

    if prefer_windowless:
        # python.exe → pythonw.exe в той же папке Scripts/
        pythonw = candidate.with_name("pythonw.exe")
        if pythonw.exists():
            return pythonw
    return candidate


def _ensure_flask_in_venv(py: Path) -> tuple[bool, str | None]:
    """`python -c "import flask"` или ставим pip install flask. (ok, error)."""
    try:
        r = subprocess.run(
            [str(py), "-c", "import flask"],
            capture_output=True, text=True, timeout=10,
        )
    except Exception as e:  # noqa: BLE001
        return False, f"проверка flask упала: {e}"
    if r.returncode == 0:
        return True, None
    # Ставим. Это разовая операция — pip-install длится 5-15 сек.
    print(f"[cosy-server] flask не найден в {py}, ставлю pip install flask…", flush=True)
    try:
        r = subprocess.run(
            [str(py), "-m", "pip", "install", "flask"],
            capture_output=True, text=True, timeout=120,
        )
    except Exception as e:  # noqa: BLE001
        return False, f"pip install упал: {e}"
    if r.returncode != 0:
        return False, f"pip exit={r.returncode}: {(r.stderr or '')[:400]}"
    return True, None


def _read_pid_file() -> int | None:
    if not COSY_SERVER_PID_FILE.exists():
        return None
    try:
        return int(COSY_SERVER_PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def _is_pid_alive_win(pid: int, expected_names: tuple[str, ...] = ("python.exe", "pythonw.exe")) -> bool:
    """Жив ли процесс с этим PID на Windows И имя соответствует ожидаемому.

    Проверка имени критична: Windows переиспользует PID-ы, и если наш
    сервер умер, PID-файл может указывать на случайный powershell.exe /
    cmd.exe / explorer.exe. Без сверки имени `/stop` убил бы их.

    Допускаем как python.exe (старый путь, fallback), так и pythonw.exe
    (новый демон-режим без окна) — они оба валидны для cosy-сервера.
    """
    try:
        r = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0 or str(pid) not in (r.stdout or ""):
            return False
        # CSV формат: "Image","PID","Session Name","Session#","Mem Usage"
        first_line = (r.stdout or "").strip().splitlines()[0].lower()
        return any(name.lower() in first_line for name in expected_names)
    except Exception:
        return False


@app.route("/api/cosyvoice-server/start", methods=["POST"])
def api_cosyvoice_server_start():
    """Запускает cosyvoice_server.py как detached-процесс (без своей консоли).

    Логи идут в automation/_cosyvoice_server.log, PID — в _cosyvoice_server.pid.
    Сервер переживает закрытие webapp и любых окон cmd. Останавливается
    только через POST /api/cosyvoice-server/stop или taskkill вручную.
    """
    # Если уже запущен — ничего не делаем.
    code, data, _ = _cosy_http_get("/health", timeout=1.0)
    if code == 200:
        return jsonify({
            "ok": True,
            "already_running": True,
            "model_loaded": bool((data or {}).get("model_loaded")),
        })

    if not COSY_SERVER_PY.exists():
        abort(500, f"Не найден {COSY_SERVER_PY.relative_to(ROOT)}")

    # Для pip install нужен обычный python.exe (он печатает прогресс в stdout
    # и иногда требует interactive input при ошибках; pythonw.exe с этим путается).
    py_console = _resolve_cosy_python(prefer_windowless=False)
    if py_console is None:
        abort(500, (
            "Не найден python для CosyVoice. Ожидаем "
            f"{Path.home() / 'cosyvoice-venv' / 'Scripts' / 'python.exe'} "
            "или env COSYVOICE_PYTHON с абсолютным путём."
        ))

    ok, err = _ensure_flask_in_venv(py_console)
    if not ok:
        abort(500, f"flask не установлен: {err}")

    # Для запуска самого сервера предпочитаем pythonw.exe — это Windows-subsystem
    # Python, ОС НИКОГДА не создаёт для него консольное окно. Идеально для демона.
    # Если pythonw.exe нет — fallback на python.exe + CREATE_NO_WINDOW (последнее
    # помогает в большинстве случаев, но на Win11 с Windows Terminal как default
    # console host окно может всё равно мелькнуть).
    py = _resolve_cosy_python(prefer_windowless=True) or py_console

    # ── Флаги для Windows: ни видимого окна, ни наследования терминала ──
    # CREATE_NO_WINDOW = 0x08000000 — окно консоли не создаётся вовсе.
    #   Это правильнее, чем DETACHED_PROCESS: последний всего лишь запрещает
    #   наследовать консоль родителя, но Windows может всё равно открыть
    #   новую для дочернего console-subsystem процесса (что мы и видели —
    #   мигало окно Windows Terminal).
    # CREATE_NEW_PROCESS_GROUP = 0x00000200 — своя process-group: даже если
    #   родительский webapp получит CTRL_BREAK / CTRL_CLOSE, нашему серверу
    #   эти сигналы не дойдут.
    CREATE_NO_WINDOW = 0x08000000
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    creation_flags = CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP

    # ── Чистим env: см. WinError 10038-фикс ──
    child_env = {**os.environ}
    child_env.pop("WERKZEUG_SERVER_FD", None)
    child_env.pop("WERKZEUG_RUN_MAIN", None)
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONUTF8"] = "1"
    # Без буферизации stdout — иначе лог-файл показывает не текущий момент,
    # а то, что было N секунд назад (Python без TTY буферизует по 4-8 КБ).
    # В лог-окне UI создавалось ощущение что модель «зависла», хотя на
    # самом деле она уже работала, просто print'ы ещё не сбросились.
    child_env["PYTHONUNBUFFERED"] = "1"

    # ── Лог-файл: открываем append, чтобы при перезапуске видеть историю ──
    COSY_SERVER_LOG.parent.mkdir(parents=True, exist_ok=True)
    log_fh = open(COSY_SERVER_LOG, "ab")
    try:
        log_fh.write(
            f"\n\n========== START {datetime.now().isoformat(timespec='seconds')} ==========\n"
            .encode("utf-8")
        )
        log_fh.flush()

        # `-u` — самый надёжный способ получить unbuffered stdout/stderr.
        # PYTHONUNBUFFERED=1 в env иногда игнорируется библиотеками, которые
        # явно открывают stderr с buffering. -u перебивает всё.
        proc = subprocess.Popen(
            [str(py), "-u", str(COSY_SERVER_PY), "--host", "127.0.0.1", "--port", "5001"],
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            env=child_env,
            creationflags=creation_flags,
            close_fds=True,
        )
    except Exception as e:
        log_fh.close()
        abort(500, f"Не удалось запустить cosy-сервер: {e}")
    finally:
        # subprocess клонирует fd внутри Popen — оригинальный handle можно
        # закрыть здесь, дочерний продолжит писать.
        try:
            log_fh.close()
        except Exception:
            pass

    COSY_SERVER_PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    print(
        f"[cosy-server] detached процесс запущен (PID={proc.pid}), "
        f"модель грузится ~30 сек. Логи: {COSY_SERVER_LOG.relative_to(ROOT)}",
        flush=True,
    )
    return jsonify({
        "ok": True,
        "already_running": False,
        "pid": proc.pid,
        "log_file": str(COSY_SERVER_LOG.relative_to(ROOT)),
        "message": (
            "CosyVoice server запущен в фоне (без окна). "
            "Модель грузится ~30 сек — следи за индикатором. "
            f"Логи: {COSY_SERVER_LOG.name}"
        ),
    })


@app.route("/api/cosyvoice-server/stop", methods=["POST"])
def api_cosyvoice_server_stop():
    """Останавливает фоновый cosy-сервер через taskkill по PID из файла.

    Если PID-файла нет или процесс уже мёртв — возвращает ok=true с пометкой.
    """
    pid = _read_pid_file()
    if pid is None:
        return jsonify({"ok": True, "was_running": False, "message": "PID-файл не найден"})

    if not _is_pid_alive_win(pid):
        COSY_SERVER_PID_FILE.unlink(missing_ok=True)
        return jsonify({
            "ok": True,
            "was_running": False,
            "message": f"процесс PID={pid} уже не существует",
        })

    # taskkill /T — убить дерево, /F — принудительно (грация в случае
    # зависшей модели не критична, всё равно процесс отвалился от консоли).
    try:
        r = subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True, text=True, timeout=10,
        )
    except Exception as e:  # noqa: BLE001
        abort(500, f"taskkill упал: {e}")

    COSY_SERVER_PID_FILE.unlink(missing_ok=True)
    return jsonify({
        "ok": True,
        "was_running": True,
        "pid": pid,
        "taskkill_rc": r.returncode,
        "taskkill_out": (r.stdout or r.stderr or "")[:400],
    })


@app.route("/api/cosyvoice-server/log")
def api_cosyvoice_server_log():
    """Возвращает последние N строк лог-файла сервера.

    Полезно для диагностики: если /health → reachable=false, можно
    посмотреть, что упало при старте.
    """
    n = int(request.args.get("lines", "80"))
    n = max(1, min(n, 1000))
    if not COSY_SERVER_LOG.exists():
        return jsonify({"exists": False, "tail": ""})
    try:
        # Простой tail: читаем последние 200 КБ и берём последние N строк.
        size = COSY_SERVER_LOG.stat().st_size
        with COSY_SERVER_LOG.open("rb") as f:
            f.seek(max(0, size - 200 * 1024))
            raw = f.read().decode("utf-8", errors="replace")
        tail_lines = raw.splitlines()[-n:]
        return jsonify({
            "exists": True,
            "size_bytes": size,
            "tail": "\n".join(tail_lines),
            "path": str(COSY_SERVER_LOG.relative_to(ROOT)),
        })
    except Exception as e:  # noqa: BLE001
        abort(500, f"Не смог прочитать лог: {e}")


# ─── Создание нового сценария ──────────────────────────────────────────────
# Один клик в UI «+ Новый миф» → создаётся вся папочная структура мифа
# (prompts/, voiceover/audio, voiceover/texts, images/, video/, music/,
# final/) и три заготовки промптов (voiceover.md / images.md / video.md).
#
# Логика scaffolding вынесена в `automation/scenario_scaffold.py` —
# тот же модуль использует CLI `automation/create_scenario.py` (шаг 2
# пайплайна), чтобы UI и CLI не разъезжались.


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

    ok, err = validate_scenario_name(raw_name)
    if not ok:
        return jsonify({"ok": False, "error": err}), 400

    raw_name = raw_name.strip()

    try:
        created = scaffold_create_scenario(raw_name, CONTENT_DIR, root=ROOT)
    except ScenarioExistsError:
        return jsonify({
            "ok": False,
            "error": f"Сценарий «{raw_name}» уже существует",
            "exists": True,
        }), 409

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


EXTENSION_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
EXTENSION_VIDEO_EXTS = {".mp4", ".mov", ".webm", ".m4v"}


def _extension_target_dir(scenario_dir: Path, target: str) -> Path:
    if target == "images":
        return scenario_dir / "images"
    if target == "video":
        return scenario_dir / "video"
    if target == "stickers":
        return scenario_dir / "images" / "stickers"
    raise ValueError(f"unsupported target: {target}")


def _extension_safe_name(name: str) -> str:
    """Санитизирует имя файла из Flow для Windows/репозитория."""
    clean = Path(name).name.strip()
    clean = re.sub(r'[<>:"/\\|?*]+', "_", clean)
    return clean or "flow_download.bin"


def _extension_unique_path(dest_dir: Path, filename: str) -> Path:
    """Подбирает незанятое имя в target-директории: file.ext, file_2.ext, ..."""
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    idx = 2
    while True:
        probe = dest_dir / f"{stem}_{idx}{suffix}"
        if not probe.exists():
            return probe
        idx += 1


def _extension_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extension_existing_hashes(dest_dir: Path, allowed_exts: set[str]) -> set[str]:
    if not dest_dir.exists():
        return set()
    hashes: set[str] = set()
    for path in dest_dir.iterdir():
        if path.is_file() and path.suffix.lower() in allowed_exts:
            hashes.add(_extension_file_sha256(path))
    return hashes


def _extension_zip_member_sha256(zf: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    digest = hashlib.sha256()
    with zf.open(info) as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extension_import_single_file(src: Path, dest_dir: Path, allowed_exts: set[str]) -> dict:
    ext = src.suffix.lower()
    if ext not in allowed_exts:
        raise ValueError(
            f"Неподдерживаемый тип файла {src.name!r}. Ожидался один из: {sorted(allowed_exts)}"
        )
    dest_dir.mkdir(parents=True, exist_ok=True)
    src_hash = _extension_file_sha256(src)
    if src_hash in _extension_existing_hashes(dest_dir, allowed_exts):
        return {
            "imported_count": 0,
            "skipped_count": 1,
            "files": [],
            "skipped": [src.name],
        }
    dst = _extension_unique_path(dest_dir, _extension_safe_name(src.name))
    shutil.copy2(src, dst)
    return {
        "imported_count": 1,
        "skipped_count": 0,
        "files": [dst.name],
        "skipped": [],
    }


def _extension_import_zip(src_zip: Path, dest_dir: Path, allowed_exts: set[str]) -> dict:
    """Достаёт из zip только нужные media-файлы и складывает в target-папку."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    imported: list[str] = []
    skipped: list[str] = []
    matched_count = 0

    with zipfile.ZipFile(src_zip) as zf:
        existing_hashes = _extension_existing_hashes(dest_dir, allowed_exts)
        for info in zf.infolist():
            if info.is_dir():
                continue
            inner_name = Path(info.filename).name
            if not inner_name:
                continue
            safe_name = _extension_safe_name(inner_name)
            ext = Path(safe_name).suffix.lower()
            if ext not in allowed_exts:
                skipped.append(inner_name)
                continue
            matched_count += 1
            member_hash = _extension_zip_member_sha256(zf, info)
            if member_hash in existing_hashes:
                skipped.append(inner_name)
                continue
            dst = _extension_unique_path(dest_dir, safe_name)
            with zf.open(info) as src_fh, dst.open("wb") as dst_fh:
                shutil.copyfileobj(src_fh, dst_fh)
            existing_hashes.add(member_hash)
            imported.append(dst.name)

    if not imported and matched_count == 0:
        raise ValueError(
            f"В архиве {src_zip.name!r} не нашлось файлов подходящего типа: {sorted(allowed_exts)}"
        )

    return {
        "imported_count": len(imported),
        "skipped_count": len(skipped),
        "files": imported,
        "skipped": skipped,
    }


def _extension_import_download(source_path: Path, scenario_dir: Path, target: str) -> dict:
    """Импортирует скачанный Flow-файл в content/<scenario>/{images,video,images/stickers}/."""
    # video → видео-расширения; images и stickers — оба картиночные.
    allowed_exts = EXTENSION_VIDEO_EXTS if target == "video" else EXTENSION_IMAGE_EXTS
    dest_dir = _extension_target_dir(scenario_dir, target)

    if source_path.suffix.lower() == ".zip":
        result = _extension_import_zip(source_path, dest_dir, allowed_exts)
    else:
        result = _extension_import_single_file(source_path, dest_dir, allowed_exts)

    result.update({
        "target": target,
        "destination_dir": str(dest_dir),
        "source": str(source_path),
    })
    return result


@app.route("/api/extension/scenarios")
def api_extension_scenarios():
    """Сценарии у которых есть prompts/{images,video,stickers}.md или voiceover/texts/."""
    items = []
    for entry in iter_scenarios_by_creation(CONTENT_DIR):
        images_md = entry.path / "prompts" / "images.md"
        video_md = entry.path / "prompts" / "video.md"
        stickers_md = entry.path / "prompts" / "stickers.md"
        has_images = images_md.exists()
        has_video = video_md.exists()
        has_stickers = stickers_md.exists()
        # `sentence_count` нужен расширению TTS EL — чтобы рисовать счётчик у
        # сценария в выпадающем списке (аналогично image_count для BOGI FLOW).
        sentences = discover_sentences_from_texts(entry.path)
        has_voiceover = bool(sentences)
        if not (has_images or has_video or has_stickers or has_voiceover):
            continue
        item = {
            "name": entry.name,
            "display_name": entry.display_name,
            "has_images": has_images,
            "has_video": has_video,
            "has_stickers": has_stickers,
            "has_voiceover": has_voiceover,
            "image_count": len(parse_images_md(images_md)) if has_images else 0,
            "video_count": len(parse_video_md(video_md)) if has_video else 0,
            "sticker_count": len(parse_images_md(stickers_md)) if has_stickers else 0,
            "sentence_count": len(sentences),
        }
        items.append(item)
    return jsonify({"scenarios": items})


@app.route("/api/extension/sentences/<path:scenario>")
def api_extension_sentences(scenario: str):
    """Список sentence_NNN сценария с текстами — для расширения TTS EL.

    Структура ответа симметрична `/api/extension/prompts/.../voiceover` (которой
    нет), но проще: у предложений нет subject-маркера и нет картинки-референса.
    Каждое предложение возвращает свой текст из voiceover/texts/<base>.txt и
    флаг `approved` — есть ли уже одобренный mp3 в approved_sentences/.
    """
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.exists():
        abort(404, description=f"Сценарий {scenario!r} не найден")

    bases = discover_sentences_from_texts(scenario_dir)
    if not bases:
        return jsonify({"scenario": scenario, "sentences": []})

    approved = load_approved_sentences(scenario_dir)
    out = []
    for base in bases:
        # base = "sentence_001" → достаём номер для удобства UI.
        m = re.search(r"(\d+)$", base)
        try:
            scene_num = int(m.group(1)) if m else 0
        except ValueError:
            scene_num = 0
        out.append({
            "base": base,
            "scene": scene_num,
            "text": find_text_for_scene(scenario_dir, base),
            "approved": approved.get(base, ""),
        })
    return jsonify({"scenario": scenario, "sentences": out})


@app.route("/api/extension/import-voiceover", methods=["POST"])
def api_extension_import_voiceover():
    """Импортирует mp3, скачанный из ElevenLabs, в approved_sentences/<base>_v1.mp3.

    Body:
      {
        "scenario": "<имя мифа>",
        "source_path": "<абсолютный путь к скачанному mp3>",
        "base": "sentence_001"
      }

    Политика: все существующие approved_sentences/<base>_*.mp3 удаляются
    (через `drop_approved_for_base`), новый файл всегда пишется как
    `<base>_v1.mp3`. Это симметрично BOGI FLOW: одна последняя одобренная
    озвучка на предложение — без накопления вариантов в approved_sentences/.
    """
    data = request.get_json(silent=True) or {}
    scenario = (data.get("scenario") or "").strip()
    source_path = (data.get("source_path") or "").strip()
    base = (data.get("base") or "").strip()

    if not scenario or not source_path or not base:
        abort(400, description="Нужны scenario, source_path и base")

    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.exists():
        abort(404, description=f"Сценарий {scenario!r} не найден")

    source = Path(source_path)
    if not source.exists():
        abort(404, description=f"Файл не найден: {source_path}")

    if source.suffix.lower() != ".mp3":
        return jsonify({
            "ok": False,
            "error": f"ожидался .mp3, пришёл {source.suffix!r}",
            "scenario": scenario,
            "base": base,
            "source": str(source),
        }), 400

    # Проверяем что у сценария вообще есть такой sentence в voiceover/texts/.
    texts_dir = scenario_dir / "voiceover" / "texts"
    if not (texts_dir / f"{base}.txt").exists():
        return jsonify({
            "ok": False,
            "error": f"нет voiceover/texts/{base}.txt — base не из этого сценария?",
            "scenario": scenario,
            "base": base,
        }), 400

    # Удаляем все старые approved для этой базы (sentence_001_v2.mp3 и т.п.).
    stuck = drop_approved_for_base(scenario_dir, base)

    approved_dir = scenario_dir / "voiceover" / "audio" / "approved_sentences"
    approved_dir.mkdir(parents=True, exist_ok=True)
    dest = approved_dir / f"{base}_v1.mp3"
    try:
        shutil.copy2(source, dest)
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"copy упал: {e}",
            "scenario": scenario,
            "base": base,
            "source": str(source),
            "dest": str(dest),
        }), 500

    return jsonify({
        "ok": True,
        "scenario": scenario,
        "base": base,
        "source": str(source),
        "dest": str(dest),
        "stuck": stuck,
    })


@app.route("/api/extension/prompts/<path:scenario>/<kind>")
def api_extension_prompts(scenario: str, kind: str):
    """Список промптов сценария: kind = images|video|stickers. С subject-маркерами.

    Стикеры используют тот же формат что и images.md (## Сцена N + **Промпт:**),
    поэтому парсим тем же `parse_images_md`.
    """
    if kind not in ("images", "video", "stickers"):
        abort(400, description="kind должен быть images|video|stickers")
    scenario = unquote(scenario)
    scenario_dir = CONTENT_DIR / scenario
    md_path = scenario_dir / "prompts" / f"{kind}.md"
    if not md_path.exists():
        abort(404, description=f"Нет {kind}.md для {scenario!r}")
    parsed = parse_video_md(md_path) if kind == "video" else parse_images_md(md_path)
    # Если в blocks нет `**Текст:**`, подмешиваем тексты из
    # voiceover/texts/sentence_NNN.txt через mapping в заголовке сцены
    # `## Сцена N (sent_NNN — ...)`. Для stickers.md и images.md из ч.1
    # «От Хаоса до Олимпа» это единственный источник текста.
    scene_to_sents = parse_scene_sentence_mapping(md_path)
    sentence_text_cache: dict[int, str] = {}

    def _resolve_text(scene_id: str, md_text: str) -> str:
        if md_text:
            return md_text
        sent_nums = scene_to_sents.get(scene_id, [])
        if not sent_nums:
            return ""
        parts_: list[str] = []
        for n in sent_nums:
            if n not in sentence_text_cache:
                sentence_text_cache[n] = load_sentence_text(scenario_dir, n)
            t = sentence_text_cache[n]
            if t:
                parts_.append(t)
        return " ".join(parts_).strip()

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
            "text": _resolve_text(scene_id, data.get("text", "")),
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


_DISTRIBUTE_SCRIPTS = {
    "images": "distribute_images.py",
    "stickers": "distribute_stickers.py",
    "video": "distribute_videos.py",
}


def _extension_run_distribute(target: str, scenario_dir: Path, import_result: dict) -> dict:
    """Запускает соответствующий distribute_*.py поверх результата импорта.

    Для images/stickers скрипт принимает zip-архив либо распакованную папку и
    раскладывает файлы по сценам через subject-маркеры из соответствующего
    prompts/*.md. Передаём в него **распакованную папку** (dest_dir, куда
    `_extension_import_download` уже скопировал содержимое архива), а не
    оригинальный source — это убирает зависимость от того, существует ли ещё
    исходный файл в Downloads/.

    Для video скрипт сравнивает первые кадры с approved_images. Передаём ему
    папку content/<scenario>/video/. Если approved_images пуст — скрипт
    ничего не переименует и просто скажет «0 сопоставлений», это нормальный
    сигнал «сначала одобри картинки».
    """
    script_name = _DISTRIBUTE_SCRIPTS.get(target)
    if not script_name:
        return {"ok": False, "error": f"unknown distribute target {target!r}"}

    script_path = ROOT / "automation" / script_name
    if not script_path.exists():
        return {"ok": False, "error": f"скрипт не найден: {script_path}"}

    dest_dir = Path(import_result.get("destination_dir") or "")
    if not dest_dir.exists():
        return {"ok": False, "error": f"папка распаковки не найдена: {dest_dir}"}

    cmd = [sys.executable, str(script_path), str(dest_dir)]
    # `--myth-dir` есть у distribute_images.py и distribute_videos.py.
    # У distribute_stickers.py его НЕТ — он определяет myth-dir автоматически
    # по пути входной папки (она уже лежит в content/<scenario>/images/stickers/).
    if target in {"images", "video"}:
        cmd += ["--myth-dir", str(scenario_dir)]
    # `--fuzzy`: bag-of-words matching между первыми 3-4 словами промпта
    # и именем файла из Flow. Flow при экспорте часто переставляет/
    # обобщает слова (например `Primordial_void_swirling_nebula` вместо
    # точного `chaos primordial swirling void`), и без --fuzzy distribute
    # отказывается раскладывать всё из-за единичных несопоставлений.
    # При запуске из расширения мы всегда подаём --fuzzy для images/stickers —
    # это безопасно (точные совпадения всё равно имеют приоритет) и сильно
    # снижает частоту ложных падений. У distribute_videos.py этого флага нет
    # (там механика через первый кадр, не через имена файлов).
    if target in {"images", "stickers"}:
        cmd += ["--fuzzy"]
    cmd += ["--execute"]

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300,
        )
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "error": "timeout (300s)",
            "stdout": e.stdout or "",
            "stderr": e.stderr or "",
            "cmd": cmd,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "cmd": cmd,
        }

    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "cmd": cmd,
        "script": script_name,
    }


@app.route("/api/extension/import-download", methods=["POST"])
def api_extension_import_download():
    """Импортирует вручную скачанный из Flow файл/zip в images/ или video/ сценария.

    Body:
      {
        "scenario": "<имя мифа>",
        "source_path": "<полный путь к скачанному файлу>",
        "target": "images" | "video" | "stickers",
        "auto_distribute": true | false  // default false — для бэк-совместимости
      }

    Если auto_distribute=true, после распаковки запускается соответствующий
    distribute_*.py с --execute. Возвращаемый JSON получает поле `distribute`
    с returncode/stdout/stderr скрипта. Если distribute упал — общий `ok`
    остаётся true (файлы уже разложены в целевую папку), но `distribute.ok`
    будет false. Расширение должно отдельно проверить оба флага.
    """
    data = request.get_json(silent=True) or {}
    scenario = (data.get("scenario") or "").strip()
    source_path = (data.get("source_path") or "").strip()
    target = (data.get("target") or "").strip().lower()
    auto_distribute = bool(data.get("auto_distribute", False))

    if not scenario or not source_path or target not in {"images", "video", "stickers"}:
        abort(400, description="Нужны scenario, source_path и target=images|video|stickers")

    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.exists():
        abort(404, description=f"Сценарий {scenario!r} не найден")

    source = Path(source_path)
    if not source.exists():
        abort(404, description=f"Файл не найден: {source_path}")

    try:
        result = _extension_import_download(source, scenario_dir, target)
    except zipfile.BadZipFile:
        return jsonify({
            "ok": False,
            "error": f"Файл {source.name!r} не удалось открыть как zip-архив",
            "scenario": scenario,
            "target": target,
            "source": str(source),
        }), 400
    except ValueError as e:
        return jsonify({
            "ok": False,
            "error": str(e),
            "scenario": scenario,
            "target": target,
            "source": str(source),
        }), 400
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e),
            "scenario": scenario,
            "target": target,
            "source": str(source),
        }), 500

    distribute_result = None
    if auto_distribute:
        distribute_result = _extension_run_distribute(target, scenario_dir, result)

    response = {
        "ok": True,
        "scenario": scenario,
        **result,
    }
    if distribute_result is not None:
        response["distribute"] = distribute_result
    return jsonify(response)


@app.route("/api/extension/import-grok", methods=["POST"])
def api_extension_import_grok():
    """Импортирует файл из Grok напрямую в папку нужной сцены по её номеру.

    Body:
      {
        "scenario": "<миф>",
        "source_path": "<абс. путь к скачанному файлу>",
        "target": "images" | "video" | "stickers",
        "scene_number": 5
      }

    video    → content/<scenario>/video/scene_NN_01.mp4 (или _02… если занято)
    images   → content/<scenario>/images/review_images/scene_NN/v1.ext (v2…)
    stickers → content/<scenario>/images/stickers/scene_NN_01.ext
    """
    data = request.get_json(silent=True) or {}
    scenario = (data.get("scenario") or "").strip()
    source_path = (data.get("source_path") or "").strip()
    target = (data.get("target") or "").strip().lower()
    scene_number = data.get("scene_number")

    if not scenario or not source_path or target not in {"images", "video", "stickers"}:
        abort(400, description="Нужны scenario, source_path и target=images|video|stickers")
    if scene_number is None:
        abort(400, description="Нужен scene_number")
    try:
        scene_number = int(scene_number)
    except (TypeError, ValueError):
        abort(400, description="scene_number должен быть числом")

    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.exists():
        abort(404, description=f"Сценарий {scenario!r} не найден")

    source = Path(source_path)
    if not source.exists():
        abort(404, description=f"Файл не найден: {source_path}")

    ext = source.suffix.lower()
    scene_tag = f"scene_{scene_number:02d}"

    if target == "video":
        if ext not in EXTENSION_VIDEO_EXTS:
            return jsonify({"ok": False, "error": f"Неподдерживаемый тип файла: {source.name!r}"}), 400
        dest_dir = scenario_dir / "video"
        dest_dir.mkdir(parents=True, exist_ok=True)
        v = 1
        while True:
            dest = dest_dir / f"{scene_tag}_v{v}{ext}"
            if not dest.exists():
                break
            v += 1
        shutil.copy2(source, dest)
        return jsonify({"ok": True, "file": dest.name, "dest": str(dest)})

    if target == "images":
        if ext not in EXTENSION_IMAGE_EXTS:
            return jsonify({"ok": False, "error": f"Неподдерживаемый тип файла: {source.name!r}"}), 400
        scene_dir_path = scenario_dir / "images" / "review_images" / scene_tag
        scene_dir_path.mkdir(parents=True, exist_ok=True)
        v = 1
        while True:
            dest = scene_dir_path / f"v{v}{ext}"
            if not dest.exists():
                break
            v += 1
        shutil.copy2(source, dest)
        return jsonify({"ok": True, "file": dest.name, "dest": str(dest)})

    # stickers
    if ext not in EXTENSION_IMAGE_EXTS:
        return jsonify({"ok": False, "error": f"Неподдерживаемый тип файла: {source.name!r}"}), 400
    dest_dir = scenario_dir / "images" / "stickers"
    dest_dir.mkdir(parents=True, exist_ok=True)
    v = 1
    while True:
        dest = dest_dir / f"{scene_tag}_v{v}{ext}"
        if not dest.exists():
            break
        v += 1
    shutil.copy2(source, dest)
    return jsonify({"ok": True, "file": dest.name, "dest": str(dest)})


if __name__ == "__main__":
    print(f"Content: {CONTENT_DIR}")
    print(f"Selections: {SELECTIONS_DIR}")
    print("-> http://127.0.0.1:5000")
    # threaded=True обязателен — иначе все запросы строго по очереди в одном
    # thread'е. С появлением cosy-сервера webapp делает синхронные HTTP-запросы
    # к нему (timeout 1 сек), и без threaded'а это блокирует абсолютно всё:
    # пока поллер batch-status ждёт 1 сек ответа от cosy, browser не получает
    # ни /api/scenarios-summary, ни /audio/..., ни /static/* — UI выглядит зависшим.
    app.run(host="127.0.0.1", port=5000, debug=True, threaded=True)
