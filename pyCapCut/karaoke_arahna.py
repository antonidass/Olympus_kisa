"""
Караоке-субтитры для «Арахна».

Что делает:
  1. Читает draft_content.json из CapCut (твои текущие правки сохраняются —
     переходы, whoosh-SFX, громкости и т.п.).
  2. По каждому sentence_NNN_vX.mp3 из approved_sentences запускает
     openai-whisper (CUDA, модуль `medium` по умолчанию) и вытягивает
     словные тайминги с флагом word_timestamps=True.
  3. Тайминги складываются со стартом voice-сегмента на таймлайне —
     получаем абсолютные моменты слов в проекте.
  4. Удаляет старые сценные субтитры (16 шт.), кроме интро-оверлея
     «АРАХНА / МИФ ЗА МИНУТУ».
  5. Добавляет новые текстовые сегменты — по одному на слово, КАПСОМ.
  6. Кэширует транскрипции в pyCapCut/_karaoke_cache_arahna.json.

Требования:
  - CapCut должен быть закрыт.
  - Запускать из CosyVoice venv (там whisper + CUDA):
        external\\CosyVoice\\.venv_cosyvoice\\Scripts\\python.exe pyCapCut\\karaoke_arahna.py

Опции:
    --model small|medium|large-v3   (по умолчанию medium)
    --dry-run                       (только транскрипция + отчёт, не писать драфт)
    --no-transcribe                 (использовать только кэш, не вызывать whisper)
    --keep-existing                 (не удалять старые субтитры, добавить караоке поверх)
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import re
import shutil
import sys
import time
import unicodedata
import uuid
from pathlib import Path

# Forced UTF-8 stdout (Windows cp1251 выпадает на кириллице/стрелках).
try:
    sys.stdout.reconfigure(encoding="utf-8")  # py3.7+
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ─────────────────────────────────────────────────────────────────────
# Пути
# ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARAHNA_NAME = "Арахна"
AUDIO_DIR = PROJECT_ROOT / "content" / ARAHNA_NAME / "voiceover" / "audio" / "approved_sentences"
REF_TEXTS_DIR = PROJECT_ROOT / "content" / ARAHNA_NAME / "voiceover" / "texts"
CACHE_FILE = Path(__file__).resolve().parent / "_karaoke_cache_arahna.json"

LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFT_DIR = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft" / ARAHNA_NAME
DRAFT_FILE = DRAFT_DIR / "draft_content.json"


# ─────────────────────────────────────────────────────────────────────
# ffmpeg — whisper зовёт его как внешний процесс. В PATH его нет,
# но CapCut приносит свой. Находим самый свежий и добавляем в PATH.
# ─────────────────────────────────────────────────────────────────────

def ensure_ffmpeg_in_path() -> None:
    import shutil as _sh
    if _sh.which("ffmpeg"):
        return
    apps = LOCALAPPDATA / "CapCut" / "Apps"
    cands = sorted(apps.glob("*/ffmpeg.exe"), key=lambda p: p.parent.name, reverse=True)
    if cands:
        os.environ["PATH"] = str(cands[0].parent) + os.pathsep + os.environ.get("PATH", "")
        print(f"ffmpeg: {cands[0]}")
        return
    print("⚠ ffmpeg не найден ни в PATH, ни в CapCut\\Apps — whisper упадёт.")


# ─────────────────────────────────────────────────────────────────────
# Стиль караоке-слова
# ─────────────────────────────────────────────────────────────────────

# ВНИМАНИЕ: в CapCut transform.y положительное = ВВЕРХ, отрицательное = ВНИЗ.

# Караоке-слова (sentence_002 и далее) — сверху, мельче, белые
KARAOKE_FONT_SIZE = 14
KARAOKE_Y = 0.75                 # чуть пониже от 0.85
KARAOKE_COLOR = [1.0, 1.0, 1.0]
KARAOKE_BORDER_ENABLED = True
KARAOKE_BORDER_COLOR = [0.0, 0.0, 0.0]
KARAOKE_BORDER_ALPHA = 1.0
KARAOKE_BORDER_WIDTH = 0.08

# Интро: накапливающийся текст из 3 шагов (sentence_001 = 4 слова).
# Строка 1: "АРАХНА" (белый), строка 2: "МИФ ЗА МИНУТУ" (красный #F20000)
INTRO_FONT_SIZE = 36                    # как у Мидаса
INTRO_Y = 0.0                           # центр кадра
INTRO_COLOR_WHITE = [1.0, 1.0, 1.0]
INTRO_COLOR_RED = [0.949, 0.0, 0.0]     # #F20000

# Минимальная длительность показа слова
MIN_WORD_MS = 120


# ─────────────────────────────────────────────────────────────────────
# Утилиты
# ─────────────────────────────────────────────────────────────────────

def gen_id_hex() -> str:
    return uuid.uuid4().hex


def gen_id_dashed_upper() -> str:
    return str(uuid.uuid4()).upper()


def check_capcut_closed() -> bool:
    try:
        import subprocess
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL, text=False)
        out_s = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        if "CapCut.exe" in out_s or "JianyingPro" in out_s:
            return False
    except Exception:
        pass
    return True


# ─────────────────────────────────────────────────────────────────────
# 1. Сбор голосовых сегментов из драфта
# ─────────────────────────────────────────────────────────────────────

def collect_voice_segments(draft: dict) -> list[dict]:
    audios_by_id = {a["id"]: a for a in draft.get("materials", {}).get("audios", [])}
    voice_tracks = [t for t in draft["tracks"] if t.get("type") == "audio" and t.get("name") == "voice"]
    if not voice_tracks:
        raise RuntimeError("Не нашёл audio-дорожку 'voice' в драфте.")
    voice_track = voice_tracks[0]
    segs = sorted(voice_track["segments"], key=lambda s: s["target_timerange"]["start"])
    out = []
    for seg in segs:
        aud = audios_by_id.get(seg["material_id"])
        if not aud:
            continue
        fname = os.path.basename(aud.get("path", ""))
        out.append({
            "fname": fname,
            "abs_start_us": seg["target_timerange"]["start"],
            "duration_us": seg["target_timerange"]["duration"],
        })
    return out


# ─────────────────────────────────────────────────────────────────────
# 2. Транскрипция через whisper
# ─────────────────────────────────────────────────────────────────────

def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.load(open(CACHE_FILE, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(cache: dict) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    json.dump(cache, open(CACHE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def strip_stresses(text: str) -> str:
    """
    Убирает ТОЛЬКО U+0301 (комбинирующий акут). Оставляет «й» (и+breve),
    «ё» и прочие составные буквы — иначе они превратятся в «и» и «е».
    """
    nfd = unicodedata.normalize("NFD", text)
    cleaned = nfd.replace("́", "")
    return unicodedata.normalize("NFC", cleaned)


def tokenize_reference(text: str) -> list[str]:
    """
    Делит эталонный текст на слова-токены, так же как их увидел бы whisper:
    - разбиваем по пробелам И дефисам (whisper "нет-нет" как два слова)
    - выкидываем чисто-пунктуационные токены («—», «…», отдельные кавычки)
    - оставляем пунктуацию, прилипшую к слову (запятые, точки, ! ? : )
    """
    raw = re.split(r"\s+", text.strip())
    split = []
    for t in raw:
        split.extend(t.split("-"))
    out = []
    for w in split:
        if not w:
            continue
        if not re.search(r"\w", w, flags=re.UNICODE):
            continue
        out.append(w)
    return out


def _word_key(w: str) -> str:
    """Нормализация слова для сравнения: убрать пунктуацию и lower."""
    return re.sub(r"[^\w]", "", w, flags=re.UNICODE).lower()


def align_whisper_to_reference(whisper_words: list[dict], ref_words: list[str]) -> list[dict]:
    """
    DP-выравнивание whisper-слов с эталонным текстом (Левенштейн по словам).
    Возвращает новый список слов с текстом из эталона и таймингами whisper
    (для пропусков эталона — делим пополам ближайшее whisper-слово).
    """
    m, n = len(whisper_words), len(ref_words)
    if m == 0 or n == 0:
        return whisper_words

    def sub_cost(i: int, j: int) -> int:
        return 0 if _word_key(whisper_words[i]["word"]) == _word_key(ref_words[j]) else 1

    D = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        D[i][0] = i
    for j in range(n + 1):
        D[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            D[i][j] = min(
                D[i - 1][j - 1] + sub_cost(i - 1, j - 1),
                D[i - 1][j] + 1,
                D[i][j - 1] + 1,
            )

    ops: list[tuple[str, int, int]] = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and D[i][j] == D[i - 1][j - 1] + sub_cost(i - 1, j - 1):
            ops.append(("sub", i - 1, j - 1))
            i -= 1
            j -= 1
        elif i > 0 and D[i][j] == D[i - 1][j] + 1:
            ops.append(("del_wh", i - 1, -1))
            i -= 1
        else:
            ops.append(("ins_ref", -1, j - 1))
            j -= 1
    ops.reverse()

    out: list[dict] = []
    for kind, wi, ri in ops:
        if kind == "sub":
            w = whisper_words[wi]
            out.append({"word": ref_words[ri], "start": w["start"], "end": w["end"]})
        elif kind == "del_wh":
            continue
        else:
            ref_text = ref_words[ri]
            if out:
                prev = out[-1]
                mid = (prev["start"] + prev["end"]) / 2
                out[-1] = {"word": prev["word"], "start": prev["start"], "end": mid}
                out.append({"word": ref_text, "start": mid, "end": prev["end"] if False else mid + max(0.1, (prev["end"] - mid))})
                out[-1]["end"] = max(mid + 0.15, out[-1]["end"])
            elif whisper_words:
                w0 = whisper_words[0]
                out.append({"word": ref_text, "start": max(0.0, w0["start"] - 0.2), "end": w0["start"]})
    return out


def load_reference_words(fname: str) -> list[str] | None:
    """По имени 'sentence_NNN_vX.mp3' тянет эталонный sentence_NNN.txt."""
    m = re.match(r"sentence_(\d+)", fname)
    if not m:
        return None
    nnn = m.group(1)
    ref = REF_TEXTS_DIR / f"sentence_{nnn}.txt"
    if not ref.is_file():
        return None
    text = ref.read_text(encoding="utf-8")
    text = strip_stresses(text)
    return tokenize_reference(text)


def substitute_with_reference(sentences: list[dict]) -> None:
    """
    Где число слов от whisper совпадает с эталонным — заменяем текст слов
    на эталон. Тайминги остаются whisper-овскими. Отчёт о рассинхронах
    печатаем отдельно.
    """
    total_subst = 0
    matched = 0
    mismatches: list[tuple[str, int, int, int]] = []
    for s in sentences:
        words = s.get("words") or []
        if not words:
            continue
        ref = load_reference_words(s["fname"])
        if ref is None:
            continue
        if len(ref) == len(words):
            for i, w in enumerate(words):
                w["word"] = ref[i]
            total_subst += len(words)
            matched += 1
        else:
            aligned = align_whisper_to_reference(words, ref)
            s["words"] = aligned
            mismatches.append((s["fname"], len(words), len(ref), len(aligned)))
    print(f"Эталонный текст подставлен в {matched}/{len(sentences)} предложений "
          f"({total_subst} слов). Рассинхронов (DP-выровнено): {len(mismatches)}.")
    for fname, nw, nr, na in mismatches:
        print(f"  ~ {fname}: whisper={nw} vs эталон={nr} → выровнено в {na} слов")


def transcribe_all(sentences: list[dict], model_name: str, allow_whisper: bool) -> None:
    cache = load_cache()
    to_run = [s for s in sentences if s["fname"] not in cache]
    if not to_run:
        print("Весь список уже в кэше — whisper не запускаю.")
        for s in sentences:
            s["words"] = cache[s["fname"]]
        return

    if not allow_whisper:
        raise SystemExit(
            f"--no-transcribe выставлен, но {len(to_run)} файлов отсутствуют в кэше. "
            f"Запусти без этого флага хотя бы один раз."
        )

    try:
        import whisper  # type: ignore
    except ImportError as e:
        raise SystemExit(
            "Не импортируется openai-whisper. Запусти скрипт из CosyVoice venv:\n"
            r"  external\CosyVoice\.venv_cosyvoice\Scripts\python.exe pyCapCut\karaoke_arahna.py"
        ) from e

    print(f"Загрузка whisper '{model_name}' …")
    t0 = time.time()
    model = whisper.load_model(model_name)
    print(f"  готово за {time.time()-t0:.1f}s")

    for s in sentences:
        if s["fname"] in cache:
            s["words"] = cache[s["fname"]]
            continue
        local = AUDIO_DIR / s["fname"]
        if not local.is_file():
            print(f"  ! пропуск, нет файла: {local}")
            s["words"] = []
            continue
        print(f"  → {s['fname']}")
        t1 = time.time()
        res = model.transcribe(
            str(local),
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
        s["words"] = words
        cache[s["fname"]] = words
        save_cache(cache)
        print(f"    {len(words)} слов, {time.time()-t1:.1f}s")


# ─────────────────────────────────────────────────────────────────────
# 3. Шаблон TextSegment / материала из существующей дорожки
# ─────────────────────────────────────────────────────────────────────

def find_subtitles_track(draft: dict) -> dict | None:
    for t in draft["tracks"]:
        if t.get("type") == "text" and t.get("name") == "subtitles":
            return t
    return None


def grab_template(draft: dict) -> tuple[dict, dict]:
    """
    Берём любой текстовый сегмент и его материал как шаблон.
    Приоритет: subtitles-дорожка → любая другая text-дорожка.
    Внутри дорожки сначала ищем ВИДИМЫЕ сегменты (visible=True), чтобы
    не унаследовать visible=False с ранее спрятанных плейсхолдеров.
    """
    texts = {m["id"]: m for m in draft["materials"]["texts"]}

    def pick(segs: list[dict]) -> tuple[dict, dict] | None:
        visibles = [s for s in segs if s.get("visible", True)]
        invisibles = [s for s in segs if not s.get("visible", True)]
        for seg in visibles + invisibles:
            mat = texts.get(seg.get("material_id"))
            if mat is not None:
                return copy.deepcopy(seg), copy.deepcopy(mat)
        return None

    sub = find_subtitles_track(draft)
    if sub and sub["segments"]:
        segs = sorted(sub["segments"], key=lambda s: s["target_timerange"]["start"])
        # Сперва не-первые (regular subs), потом первый (интро) — у интро
        # обычно другой size/y, его как шаблон брать в последнюю очередь.
        result = pick(segs[1:] + [segs[0]])
        if result:
            return result
    for tr in draft["tracks"]:
        if tr.get("type") != "text":
            continue
        result = pick(tr.get("segments", []))
        if result:
            return result
    raise RuntimeError("В драфте нет ни одного текстового сегмента — шаблон взять неоткуда.")


def _stroke_block() -> dict:
    """Единый блок чёрной обводки — вставляется в каждый style внутри content."""
    if not KARAOKE_BORDER_ENABLED:
        return None  # type: ignore
    return {
        "content": {
            "solid": {
                "alpha": KARAOKE_BORDER_ALPHA,
                "color": list(KARAOKE_BORDER_COLOR),
            }
        },
        "width": KARAOKE_BORDER_WIDTH,
    }


def build_content_json(text: str, template_content: str,
                        size: int, color: list[float]) -> str:
    """
    В CapCut content материала — это JSON-строка со styles и text.
    Меняем text / range / size / color, font остаётся от шаблона (Rubik Bold).
    Добавляем чёрную обводку (strokes).
    """
    stroke = _stroke_block()
    try:
        parsed = json.loads(template_content)
    except Exception:
        parsed = None

    if parsed is None:
        style_base = {
            "fill": {"alpha": 1.0, "content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": color}}},
            "range": [0, len(text)],
            "size": size,
            "useLetterColor": True,
        }
        if stroke:
            style_base["strokes"] = [stroke]
        return json.dumps({"text": text, "styles": [style_base]}, ensure_ascii=False)

    parsed["text"] = text
    styles = parsed.get("styles") or []
    if styles:
        st = styles[0]
        st["range"] = [0, len(text)]
        st["size"] = size
        fill = st.setdefault("fill", {})
        cc = fill.setdefault("content", {"render_type": "solid"})
        cc["solid"] = {"alpha": 1.0, "color": color}
        if stroke:
            st["strokes"] = [stroke]
        parsed["styles"] = [st]
    else:
        style_base = {
            "fill": {"alpha": 1.0, "content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": color}}},
            "range": [0, len(text)],
            "size": size,
            "useLetterColor": True,
        }
        if stroke:
            style_base["strokes"] = [stroke]
        parsed["styles"] = [style_base]
    return json.dumps(parsed, ensure_ascii=False)


def extract_font_info(template_mat: dict) -> dict | None:
    """Достаёт {id, path} Rubik-Bold из template material's content."""
    try:
        parsed = json.loads(template_mat.get("content", "{}"))
        styles = parsed.get("styles") or []
        if styles and "font" in styles[0]:
            return copy.deepcopy(styles[0]["font"])
    except Exception:
        pass
    return None


def _strip_trailing_punct(w: str) -> str:
    return re.sub(r"[.,!?;:]+$", "", w)


def build_intro_steps(intro_sentence: dict) -> list[tuple[int, int, str]]:
    """
    Накапливающиеся шаги интро из 4 whisper-слов sentence_001
    (Арахна. Миф за минуту.):
      шаг 1: «АРАХНА»                                       [t0..t1]
      шаг 2: «АРАХНА\\nМИФ»                                 [t1..t2]
      шаг 3: «АРАХНА\\nМИФ ЗА МИНУТУ»                       [t2..end]
    Тайминги t0..t3 — whisper-начала слов, end = конец голосового сегмента.
    Пунктуация на концах слов срезается, чтобы получилось «АРАХНА», а не «АРАХНА.».
    """
    words = intro_sentence.get("words") or []
    if len(words) < 4:
        return []
    base_us = intro_sentence["abs_start_us"]
    end_us = base_us + intro_sentence["duration_us"]
    ws = [_strip_trailing_punct(w["word"]) for w in words[:4]]
    ts = [base_us + int(w["start"] * 1_000_000) for w in words[:4]]
    # гарантируем монотонность (иногда whisper даёт next.start < prev.end)
    ts = [max(ts[0], ts[i] if i == 0 else max(ts[i], ts[i - 1] + 1000)) for i in range(4)]

    # Интро в верхнем регистре: «АРАХНА / МИФ ЗА МИНУТУ»
    u = [w.upper() for w in ws]
    # u = [АРАХНА, МИФ, ЗА, МИНУТУ]
    steps_text = [
        u[0],                                              # "АРАХНА"
        f"{u[0]}\n{u[1]}",                                 # "АРАХНА\nМИФ"
        f"{u[0]}\n{u[1]} {u[2]} {u[3]}",                   # "АРАХНА\nМИФ ЗА МИНУТУ"
    ]
    # Тайминги: переход между шагами на старте слова, добавляющего новый блок
    steps_starts = [ts[0], ts[1], ts[2]]
    steps_ends = [ts[1], ts[2], end_us]
    out = []
    for start, end, text in zip(steps_starts, steps_ends, steps_text):
        if end > start:
            out.append((start, end - start, text))
    return out


def build_intro_content_json(text: str, size: int,
                              white: list[float], red: list[float],
                              font_info: dict | None) -> str:
    """
    Content для интро-сегмента: если в тексте есть перенос строки — красим
    первую строку в white, вторую в red. Шрифт берём из template (Rubik-Bold).
    У каждого стиля — чёрная обводка.
    """
    nl_pos = text.find("\n")
    stroke = _stroke_block()

    def style(rng: list[int], color: list[float]) -> dict:
        s = {
            "fill": {"alpha": 1.0, "content": {"render_type": "solid",
                                                "solid": {"alpha": 1.0, "color": color}}},
            "range": rng,
            "size": size,
            "useLetterColor": True,
        }
        if font_info:
            s["font"] = copy.deepcopy(font_info)
        if stroke:
            s["strokes"] = [stroke]
        return s

    if nl_pos < 0:
        styles = [style([0, len(text)], white)]
    else:
        styles = [
            style([0, nl_pos], white),              # "АРАХНА"
            style([nl_pos + 1, len(text)], red),    # "МИФ ЗА МИНУТУ"
        ]
    return json.dumps({"text": text, "styles": styles}, ensure_ascii=False)


def make_intro_text_material(template_mat: dict, text: str) -> dict:
    """Material с мульти-стилем (белое/красное по строкам)."""
    font_info = extract_font_info(template_mat)
    m = copy.deepcopy(template_mat)
    m["id"] = gen_id_hex()
    m["content"] = build_intro_content_json(
        text, INTRO_FONT_SIZE, INTRO_COLOR_WHITE, INTRO_COLOR_RED, font_info,
    )
    m["base_content"] = m["content"]
    for k, v in {
        "type": "text",
        "line_spacing": -0.20,
        "recognize_task_id": "", "recognize_text": "", "recognize_model": "",
        "recognize_type": 0, "punc_model": "", "sub_type": 0, "add_type": 0,
        "operation_type": 0, "text_to_audio_ids": [], "check_flag": 15,
        "language": "ru", "tts_auto_update": False, "is_batch_replace": False,
        "text_preset_resource_id": "", "preset_id": "", "preset_name": "",
        "preset_category": "", "preset_category_id": "", "preset_index": 0,
        "preset_has_set_alignment": False, "sub_template_id": "",
        "font_size": INTRO_FONT_SIZE, "text_size": INTRO_FONT_SIZE,
        "text_color": "#ffffff", "source_from": "",
    }.items():
        m[k] = v
    m["words"] = {"text": [text], "start_time": [0], "end_time": [0]}
    if KARAOKE_BORDER_ENABLED:
        m["border_alpha"] = KARAOKE_BORDER_ALPHA
        m["border_color"] = KARAOKE_BORDER_COLOR
        m["border_width"] = KARAOKE_BORDER_WIDTH
    return m


def make_text_material(template_mat: dict, text: str,
                        size: int, color: list[float]) -> dict:
    m = copy.deepcopy(template_mat)
    m["id"] = gen_id_hex()
    m["content"] = build_content_json(text, template_mat.get("content", "{}"), size, color)
    m["base_content"] = m["content"]
    m["type"] = "text"
    m["recognize_task_id"] = ""
    m["recognize_text"] = ""
    m["recognize_model"] = ""
    m["recognize_type"] = 0
    m["punc_model"] = ""
    m["sub_type"] = 0
    m["add_type"] = 0
    m["operation_type"] = 0
    m["text_to_audio_ids"] = []
    m["check_flag"] = 15
    m["language"] = "ru"
    m["tts_auto_update"] = False
    m["is_batch_replace"] = False
    m["text_preset_resource_id"] = ""
    m["preset_id"] = ""
    m["preset_name"] = ""
    m["preset_category"] = ""
    m["preset_category_id"] = ""
    m["preset_index"] = 0
    m["preset_has_set_alignment"] = False
    m["sub_template_id"] = ""
    m["font_size"] = size
    m["text_size"] = size
    m["text_color"] = f"#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}"
    m["words"] = {"text": [text], "start_time": [0], "end_time": [0]}
    m["source_from"] = ""
    if KARAOKE_BORDER_ENABLED:
        m["border_alpha"] = KARAOKE_BORDER_ALPHA
        m["border_color"] = KARAOKE_BORDER_COLOR
        m["border_width"] = KARAOKE_BORDER_WIDTH
    return m


def make_text_segment(template_seg: dict, material_id: str,
                       start_us: int, duration_us: int, y: float) -> dict:
    s = copy.deepcopy(template_seg)
    s["id"] = gen_id_hex()
    s["material_id"] = material_id
    s["target_timerange"] = {"start": int(start_us), "duration": int(duration_us)}
    s["source_timerange"] = None
    clip = s.setdefault("clip", {})
    clip.setdefault("scale", {"x": 1.0, "y": 1.0})
    clip.setdefault("flip", {"vertical": False, "horizontal": False})
    clip["transform"] = {"x": 0.0, "y": y}
    clip["alpha"] = 1.0
    s["render_timerange"] = {"start": 0, "duration": 0}
    s["common_keyframes"] = []
    s["caption_info"] = None
    s["extra_material_refs"] = []
    s["source"] = ""
    s["raw_segment_id"] = ""
    s["group_id"] = ""
    s["template_id"] = ""
    s["visible"] = True   # шаблон мог прийти из спрятанного сегмента — форсим видимость
    return s


# ─────────────────────────────────────────────────────────────────────
# 4. Развёртка слов в временные интервалы
# ─────────────────────────────────────────────────────────────────────

def layout_words(sentences: list[dict]) -> list[tuple[int, int, str]]:
    """
    Возвращает [(abs_start_us, abs_end_us, word), ...].
    Каждое слово висит до старта следующего (внутри своего предложения),
    последнее слово — до конца голосового сегмента.
    """
    out: list[tuple[int, int, str]] = []
    for s in sentences:
        words = s.get("words") or []
        if not words:
            continue
        base_us = s["abs_start_us"]
        sentence_end_us = base_us + s["duration_us"]
        n = len(words)
        for i, w in enumerate(words):
            start_us = base_us + int(w["start"] * 1_000_000)
            if i < n - 1:
                end_us = base_us + int(words[i + 1]["start"] * 1_000_000)
            else:
                end_us = sentence_end_us
            end_us = min(end_us, sentence_end_us)
            start_us = max(start_us, base_us)
            if end_us - start_us < MIN_WORD_MS * 1000:
                end_us = start_us + MIN_WORD_MS * 1000
            out.append((start_us, end_us, w["word"]))
    out.sort(key=lambda x: x[0])
    return out


# ─────────────────────────────────────────────────────────────────────
# 5. Основная логика
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "medium"),
                   help="Whisper-модель: small / medium / large-v3 (default medium)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-transcribe", action="store_true")
    p.add_argument("--keep-existing", action="store_true",
                   help="Не удалять старые сценные субтитры, добавить караоке поверх")
    p.add_argument("--no-reference", action="store_true",
                   help="Не подставлять эталонный текст из voiceover/texts/*.txt; использовать чистый whisper")
    args = p.parse_args()

    if not DRAFT_FILE.is_file():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1

    ensure_ffmpeg_in_path()

    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой его полностью (включая трей), потом перезапусти скрипт.")
        return 1

    print(f"Читаю драфт: {DRAFT_FILE}")
    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))

    sentences = collect_voice_segments(draft)
    print(f"Голосовых сегментов: {len(sentences)}")

    transcribe_all(sentences, args.model, allow_whisper=not args.no_transcribe)

    if not args.no_reference:
        substitute_with_reference(sentences)

    words = layout_words(sentences)
    print(f"Слов для караоке: {len(words)}")
    if not words:
        print("Пусто, выходим.")
        return 1

    for ws, we, w in words[:10]:
        print(f"  {ws/1_000_000:6.2f}-{we/1_000_000:6.2f}  {w!r}")
    print(f"  … всего {len(words)}")

    if args.dry_run:
        print("--dry-run: драфт не трогаю.")
        return 0

    # --- бэкап
    bkp = DRAFT_FILE.with_suffix(".json.karaoke-backup")
    shutil.copy2(DRAFT_FILE, bkp)
    print(f"Бэкап: {bkp.name}")

    # --- шаблоны (из существующего субтитра)
    tmpl_seg, tmpl_mat = grab_template(draft)

    # --- Удаляем все прошлые попытки: karaoke-дорожки + text-дорожки,
    #     созданные/сохранённые CapCut'ом при реимпорте нашей предыдущей
    #     вставки.
    text_tracks_all = [t for t in draft["tracks"] if t.get("type") == "text"]
    to_remove = [t for t in text_tracks_all if t.get("name") in ("karaoke", "intro", "", None)]
    total_old_segs = 0
    removed_mat_ids: set[str] = set()
    for ok in to_remove:
        total_old_segs += len(ok.get("segments", []))
        for s in ok.get("segments", []):
            removed_mat_ids.add(s.get("material_id", ""))
        draft["tracks"].remove(ok)
    if removed_mat_ids:
        draft["materials"]["texts"] = [
            m for m in draft["materials"]["texts"] if m["id"] not in removed_mat_ids
        ]
    if total_old_segs:
        print(f"Удалено прошлых караоке-сегментов: {total_old_segs}.")

    # --- удаляем дорожку subtitles ЦЕЛИКОМ.
    # Шаблон font/style для караоке мы уже забрали выше через grab_template,
    # больше эта дорожка не нужна. Интро рендерится отдельно на дорожке
    # "intro" мульти-стилем (бело-красное накопительное), а сценные тексты
    # перекрывает пословное караоке. Любые «выключенные» или живые сегменты
    # на subtitles — мусор, который видно в CapCut над таймлайном.
    if not args.keep_existing:
        sub_track = find_subtitles_track(draft)
        if sub_track is not None:
            drop = sub_track.get("segments", [])
            drop_mat_ids = {s.get("material_id", "") for s in drop}
            if drop_mat_ids:
                draft["materials"]["texts"] = [
                    m for m in draft["materials"]["texts"]
                    if m["id"] not in drop_mat_ids
                ]
            draft["tracks"].remove(sub_track)
            print(f"Дорожка 'subtitles' удалена целиком ({len(drop)} сегментов).")
        else:
            print("Дорожки 'subtitles' нет — пропускаю чистку.")

    # --- Создаём две новые text-track: "intro" (поверх) и "karaoke" (под ним)
    intro_track = {
        "attribute": 0, "flag": 0, "id": gen_id_hex(),
        "is_default_name": True, "name": "intro",
        "segments": [], "type": "text",
    }
    karaoke_track = {
        "attribute": 0, "flag": 0, "id": gen_id_hex(),
        "is_default_name": True, "name": "karaoke",
        "segments": [], "type": "text",
    }
    draft["tracks"].append(karaoke_track)
    draft["tracks"].append(intro_track)

    # --- Диапазон интро (всё первое предложение, sentence_001_*.mp3)
    intro_sentence = next(
        (s for s in sentences if re.match(r"sentence_001", s["fname"])),
        None,
    )
    if intro_sentence:
        intro_start_us = intro_sentence["abs_start_us"]
        intro_end_us = intro_start_us + intro_sentence["duration_us"]
    else:
        intro_start_us, intro_end_us = 0, 0

    # --- Интро: накапливающийся текст, 3 шага
    intro_steps = build_intro_steps(intro_sentence) if intro_sentence else []
    for step_start_us, step_dur_us, step_text in intro_steps:
        intro_mat = make_intro_text_material(tmpl_mat, step_text)
        intro_seg = make_text_segment(
            tmpl_seg, intro_mat["id"],
            step_start_us, step_dur_us,
            INTRO_Y,
        )
        draft["materials"]["texts"].append(intro_mat)
        intro_track["segments"].append(intro_seg)
    if intro_steps:
        total_dur = sum(d for _, d, _ in intro_steps) / 1_000_000
        print(f"Интро: {len(intro_steps)} накапливающихся шагов на "
              f"{intro_start_us/1_000_000:.2f}–{(intro_start_us + int(total_dur*1_000_000))/1_000_000:.2f}s.")

    # --- Караоке: исключаем слова, которые попадают внутрь интро
    inserted_words = 0
    skipped_in_intro = 0
    for start_us, end_us, word in words:
        if intro_start_us <= start_us < intro_end_us:
            skipped_in_intro += 1
            continue
        mat = make_text_material(tmpl_mat, word.upper(), KARAOKE_FONT_SIZE, KARAOKE_COLOR)
        seg = make_text_segment(
            tmpl_seg, mat["id"],
            start_us, end_us - start_us,
            KARAOKE_Y,
        )
        draft["materials"]["texts"].append(mat)
        karaoke_track["segments"].append(seg)
        inserted_words += 1

    karaoke_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])
    if skipped_in_intro:
        print(f"Пропущено караоке-слов в зоне интро: {skipped_in_intro}.")

    # --- сохраняем основной json
    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    # --- синхронизируем CapCut-овские кэши
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = DRAFT_DIR / tgt_name
        try:
            shutil.copy2(DRAFT_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")
    print(f"Драфт сохранён + синхронизированы template-2.tmp и .bak. "
          f"Интро-сегментов: {len(intro_track['segments'])}, "
          f"караоке-слов: {inserted_words}")
    print("Открой CapCut → проект «Арахна» → проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
