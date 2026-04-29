"""
Караоке-субтитры + интро для драфта «Сизифов труд».

Аналог karaoke_midas.py, адаптированный под другую структуру ассетов:
  • аудио лежит в content/Сизифов Труд/voiceover/audio/scene_NN.mp3
    (одна сцена = один mp3, без _vN-вариантов),
  • интро — это самый первый voice-сегмент по таймлайну,
    с текстом «СИЗИФОВ ТРУД / МИФ ЗА МИНУТУ» (5 whisper-слов
    «Сизифов труд. Миф за минуту.», как у Мидаса).
  • эталонных voiceover/texts/sentence_NNN.txt у Сизифа нет, поэтому
    substitute_with_reference пропускается — текст слов берём
    как услышал whisper.

Что делает: то же, что karaoke_midas.py:
  1. Читает draft_content.json «Сизифов труд» (твои переходы и эффекты
     остаются — мы трогаем только text-материалы и text-треки).
  2. Транскрибирует каждое scene_NN.mp3 через whisper (CUDA, model
     medium по умолчанию) с word_timestamps=True. Кэш в pyCapCut/
     _karaoke_cache_sisyphus.json.
  3. Удаляет старые karaoke/intro/безымянные text-треки и прячет
     старые сценные субтитры из 'subtitles' (кроме первого).
  4. Кладёт интро (4 накапливающихся шага) и караоке (по слову)
     поверх видео.
  5. Сохраняет драфт + синхронизирует .bak / template-2.tmp.

Запуск (CapCut должен быть закрыт):
    external\\CosyVoice\\.venv_cosyvoice\\Scripts\\python.exe pyCapCut\\karaoke_sisyphus.py

Опции:
    --model small|medium|large-v3   (по умолчанию medium)
    --dry-run                       (только транскрипция + отчёт)
    --no-transcribe                 (только из кэша, не звать whisper)
    --keep-existing                 (не удалять старую subtitles-дорожку)
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

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ─────────────────────────────────────────────────────────────────────
# Пути
# ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SISYPHUS_NAME = "Сизифов труд"
AUDIO_DIR = PROJECT_ROOT / "content" / "Сизифов Труд" / "voiceover" / "audio"
CACHE_FILE = Path(__file__).resolve().parent / "_karaoke_cache_sisyphus.json"

LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFT_DIR = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft" / SISYPHUS_NAME
DRAFT_FILE = DRAFT_DIR / "draft_content.json"


# ─────────────────────────────────────────────────────────────────────
# Стиль караоке-слова (один-в-один с Мидасом)
# ─────────────────────────────────────────────────────────────────────

# Размеры/позиции
KARAOKE_FONT_SIZE = 14
KARAOKE_Y = 0.75
KARAOKE_COLOR = [1.0, 1.0, 1.0]
KARAOKE_LINE_SPACING = 0.02         # как у Мидаса (карaoke)

# Обводка: чёрная, толщина как у Мидаса. border_color оставляем
# пустой строкой — у Мидаса именно так (цвет обводки задаётся
# через strokes[].content.solid.color, а это поле legacy).
KARAOKE_BORDER_ENABLED = True
KARAOKE_BORDER_COLOR = ""
KARAOKE_BORDER_COLOR_RGB = [0.0, 0.0, 0.0]
KARAOKE_BORDER_ALPHA = 1.0
KARAOKE_BORDER_WIDTH = 0.08

# Шрифт — Rubik-Bold. ID и путь те же, что в Мидас-драфте; файл
# уже скачан в CapCut Cache (effect 7517472189348695297), поэтому
# Сизиф подхватит его без перезагрузки.
RUBIK_BOLD = {
    "id": "7517472189348695297",
    "path": "C:/Users/Антон/AppData/Local/CapCut/User Data/Cache/effect/7517472189348695297/d9b01b0f3c2256a42fbf4ba926aaeeb8/Rubik-Bold.ttf",
}

# Интро: «СИЗИФОВ ТРУД / МИФ ЗА МИНУТУ»
INTRO_FONT_SIZE = 20
INTRO_Y = 0.0
INTRO_LINE_SPACING = -0.40          # сильнее чем у Мидаса (-0.20),
INTRO_COLOR_WHITE = [1.0, 1.0, 1.0]
INTRO_COLOR_RED = [0.949, 0.0, 0.0]   # #F20000

MIN_WORD_MS = 120


# ─────────────────────────────────────────────────────────────────────
# Эталонные тексты сцен — для DP-выравнивания (whisper иногда
# коверкает слова; берём «Сизифов» вместо «Сезивов» и т.п.).
# ─────────────────────────────────────────────────────────────────────

# Импортируем SCENE_TEXTS из scene_structure (он рядом, в pyCapCut/).
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from scene_structure import SCENE_TEXTS as _SISYPHUS_SCENE_TEXTS  # type: ignore
except Exception:
    _SISYPHUS_SCENE_TEXTS = {}

# Интро (sid=01) у нас в SCENE_TEXTS пустой — текст «Сизифов труд. Миф за
# минуту.» произносится в озвучке, но в SCENE_TEXTS его нет. Подкладываем
# его сюда, чтобы DP заменил «Сезивов» → «Сизифов».
SCENE_TEXTS_FOR_REF = dict(_SISYPHUS_SCENE_TEXTS)
SCENE_TEXTS_FOR_REF["01"] = "Сизифов труд. Миф за минуту."


# ─────────────────────────────────────────────────────────────────────
# ffmpeg в PATH (whisper зовёт его как внешний процесс)
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
# Утилиты
# ─────────────────────────────────────────────────────────────────────

def gen_id_hex() -> str:
    return uuid.uuid4().hex


def check_capcut_closed() -> bool:
    try:
        import subprocess
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
        text = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        if "CapCut.exe" in text or "JianyingPro" in text:
            return False
    except Exception:
        pass
    return True


def strip_stresses(text: str) -> str:
    nfd = unicodedata.normalize("NFD", text)
    return unicodedata.normalize("NFC", nfd.replace("́", ""))


# ─────────────────────────────────────────────────────────────────────
# Сбор voice-сегментов
# ─────────────────────────────────────────────────────────────────────

def collect_voice_segments(draft: dict) -> list[dict]:
    audios_by_id = {a["id"]: a for a in draft.get("materials", {}).get("audios", [])}
    voice_tracks = [t for t in draft["tracks"] if t.get("type") == "audio" and t.get("name") == "voice"]
    if not voice_tracks:
        raise RuntimeError("Не нашёл audio-дорожку 'voice' в драфте.")
    segs = sorted(voice_tracks[0]["segments"], key=lambda s: s["target_timerange"]["start"])
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
# Транскрипция через whisper + кэш
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
            "Не импортируется openai-whisper. Запусти из CosyVoice venv:\n"
            r"  external\CosyVoice\.venv_cosyvoice\Scripts\python.exe pyCapCut\karaoke_sisyphus.py"
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
            str(local), language="ru", word_timestamps=True,
            fp16=False, condition_on_previous_text=False,
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
# Шаблон TextSegment / Material из существующего сегмента
# ─────────────────────────────────────────────────────────────────────

def find_subtitles_track(draft: dict) -> dict | None:
    for t in draft["tracks"]:
        if t.get("type") == "text" and t.get("name") == "subtitles":
            return t
    return None


def grab_template(draft: dict) -> tuple[dict, dict]:
    texts = {m["id"]: m for m in draft["materials"]["texts"]}
    sub = find_subtitles_track(draft)
    if sub and sub["segments"]:
        segs = sorted(sub["segments"], key=lambda s: s["target_timerange"]["start"])
        for seg in segs[1:] + [segs[0]]:
            mat = texts.get(seg["material_id"])
            if mat is not None:
                return copy.deepcopy(seg), copy.deepcopy(mat)
    for tr in draft["tracks"]:
        if tr.get("type") != "text":
            continue
        for seg in tr.get("segments", []):
            mat = texts.get(seg.get("material_id"))
            if mat is not None:
                return copy.deepcopy(seg), copy.deepcopy(mat)
    raise RuntimeError("В драфте нет ни одного текстового сегмента — шаблон взять неоткуда.")


def _stroke_block() -> dict | None:
    if not KARAOKE_BORDER_ENABLED:
        return None
    return {
        "content": {"solid": {"alpha": KARAOKE_BORDER_ALPHA, "color": list(KARAOKE_BORDER_COLOR_RGB)}},
        "width": KARAOKE_BORDER_WIDTH,
    }


def _font_block() -> dict:
    return copy.deepcopy(RUBIK_BOLD)


def build_content_json(text: str, _template_content: str, size: int, color: list[float]) -> str:
    """Один стиль на весь текст: цвет, размер, Rubik-Bold, чёрная обводка.
    Шаблон (_template_content) больше не используется — всё захардкожено
    под Мидас-стиль."""
    style = {
        "fill": {"alpha": 1.0, "content": {"render_type": "solid",
                                            "solid": {"alpha": 1.0, "color": color}}},
        "font": _font_block(),
        "range": [0, len(text)],
        "size": size,
        "useLetterColor": True,
    }
    stroke = _stroke_block()
    if stroke:
        style["strokes"] = [stroke]
    return json.dumps({"text": text, "styles": [style]}, ensure_ascii=False)


def _strip_trailing_punct(w: str) -> str:
    return re.sub(r"[.,!?;:]+$", "", w)


# ─────────────────────────────────────────────────────────────────────
# Подстановка эталонного текста (DP-выравнивание словами)
# Перенесено один-в-один из karaoke_midas.py.
# ─────────────────────────────────────────────────────────────────────

def tokenize_reference(text: str) -> list[str]:
    """Делит эталон на слова так, как их увидел бы whisper:
    разбиваем по пробелам и обычным дефисам, оставляем только токены,
    содержащие word-character (\\w), пунктуация-only выкидываем."""
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


def _word_key(w: str) -> str:
    return re.sub(r"[^\w]", "", w, flags=re.UNICODE).lower()


def align_whisper_to_reference(whisper_words: list[dict], ref_words: list[str]) -> list[dict]:
    """DP-выравнивание whisper-слов с эталоном (Левенштейн по словам).
    Возвращает список с текстом из эталона и таймингами whisper."""
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
            ops.append(("sub", i - 1, j - 1)); i -= 1; j -= 1
        elif i > 0 and D[i][j] == D[i - 1][j] + 1:
            ops.append(("del_wh", i - 1, -1)); i -= 1
        else:
            ops.append(("ins_ref", -1, j - 1)); j -= 1
    ops.reverse()

    out: list[dict] = []
    for kind, wi, ri in ops:
        if kind == "sub":
            w = whisper_words[wi]
            out.append({"word": ref_words[ri], "start": w["start"], "end": w["end"]})
        elif kind == "del_wh":
            continue
        else:  # ins_ref — эталон есть, whisper пропустил, делим соседа пополам
            ref_text = ref_words[ri]
            if out:
                prev = out[-1]
                mid = (prev["start"] + prev["end"]) / 2
                out[-1] = {"word": prev["word"], "start": prev["start"], "end": mid}
                out.append({"word": ref_text, "start": mid,
                            "end": max(mid + 0.15, prev["end"])})
            elif whisper_words:
                w0 = whisper_words[0]
                out.append({"word": ref_text, "start": max(0.0, w0["start"] - 0.2),
                            "end": w0["start"]})
    return out


def _sid_for_audio_filename(fname: str) -> str | None:
    """scene_NN.mp3 → 'NN'; scene_NN_NN.mp3 → 'NN-NN'."""
    m = re.match(r"scene_(\d+)(?:_(\d+))?\.mp3$", fname)
    if not m:
        return None
    a, b = m.group(1), m.group(2)
    return f"{a}-{b}" if b else a


def load_reference_words(fname: str) -> list[str] | None:
    sid = _sid_for_audio_filename(fname)
    if sid is None:
        return None
    text = SCENE_TEXTS_FOR_REF.get(sid)
    if not text:
        return None
    text = strip_stresses(text)
    return tokenize_reference(text)


def substitute_with_reference(sentences: list[dict]) -> None:
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


def build_intro_steps(intro_sentence: dict) -> list[tuple[int, int, str]]:
    """
    Накапливающиеся шаги интро для «Сизифов труд. Миф за минуту.»
    из 5 whisper-слов: «Сизифов», «труд.», «Миф», «за», «минуту.»
      шаг 1: «СИЗИФОВ»                                [t1..t2]
      шаг 2: «СИЗИФОВ ТРУД»                           [t2..t3]
      шаг 3: «СИЗИФОВ ТРУД\\nМИФ»                     [t3..t4]
      шаг 4: «СИЗИФОВ ТРУД\\nМИФ ЗА МИНУТУ»           [t4..end]
    """
    words = intro_sentence.get("words") or []
    if len(words) < 5:
        return []
    base_us = intro_sentence["abs_start_us"]
    end_us = base_us + intro_sentence["duration_us"]
    ws = [_strip_trailing_punct(w["word"]) for w in words[:5]]
    ts = [base_us + int(w["start"] * 1_000_000) for w in words[:5]]
    ts = [max(ts[0], ts[i] if i == 0 else max(ts[i], ts[i - 1] + 1000)) for i in range(5)]

    u = [w.upper() for w in ws]
    steps_text = [
        u[0],
        f"{u[0]} {u[1]}",
        f"{u[0]} {u[1]}\n{u[2]}",
        f"{u[0]} {u[1]}\n{u[2]} {u[3]} {u[4]}",
    ]
    steps_starts = [ts[0], ts[1], ts[2], ts[3]]
    steps_ends = [ts[1], ts[2], ts[3], end_us]
    out = []
    for start, end, text in zip(steps_starts, steps_ends, steps_text):
        if end > start:
            out.append((start, end - start, text))
    return out


def build_intro_content_json(text: str, size: int, white: list[float],
                              red: list[float]) -> str:
    """Двухстилевой контент: первая строка белая, вторая красная.
    Шрифт Rubik-Bold + чёрная обводка применяются к каждому стилю."""
    nl_pos = text.find("\n")
    stroke = _stroke_block()

    def style(rng: list[int], color: list[float]) -> dict:
        s = {
            "fill": {"alpha": 1.0, "content": {"render_type": "solid",
                                                "solid": {"alpha": 1.0, "color": color}}},
            "font": _font_block(),
            "range": rng,
            "size": size,
            "useLetterColor": True,
        }
        if stroke:
            s["strokes"] = [stroke]
        return s

    if nl_pos < 0:
        styles = [style([0, len(text)], white)]
    else:
        styles = [
            style([0, nl_pos], white),                      # «СИЗИФОВ ТРУД»
            style([nl_pos + 1, len(text)], red),            # «МИФ ЗА МИНУТУ»
        ]
    return json.dumps({"text": text, "styles": styles}, ensure_ascii=False)


def make_intro_text_material(template_mat: dict, text: str) -> dict:
    m = copy.deepcopy(template_mat)
    m["id"] = gen_id_hex()
    m["content"] = build_intro_content_json(
        text, INTRO_FONT_SIZE, INTRO_COLOR_WHITE, INTRO_COLOR_RED,
    )
    m["base_content"] = m["content"]
    for k, v in {
        "type": "text", "line_spacing": INTRO_LINE_SPACING,
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


def make_text_material(template_mat: dict, text: str, size: int, color: list[float]) -> dict:
    m = copy.deepcopy(template_mat)
    m["id"] = gen_id_hex()
    m["content"] = build_content_json(text, template_mat.get("content", "{}"), size, color)
    m["base_content"] = m["content"]
    m["type"] = "text"
    for k, v in {
        "line_spacing": KARAOKE_LINE_SPACING,
        "recognize_task_id": "", "recognize_text": "", "recognize_model": "",
        "recognize_type": 0, "punc_model": "", "sub_type": 0, "add_type": 0,
        "operation_type": 0, "text_to_audio_ids": [], "check_flag": 15,
        "language": "ru", "tts_auto_update": False, "is_batch_replace": False,
        "text_preset_resource_id": "", "preset_id": "", "preset_name": "",
        "preset_category": "", "preset_category_id": "", "preset_index": 0,
        "preset_has_set_alignment": False, "sub_template_id": "",
        "font_size": size, "text_size": size,
        "text_color": f"#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}",
        "source_from": "",
    }.items():
        m[k] = v
    m["words"] = {"text": [text], "start_time": [0], "end_time": [0]}
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
    # ВАЖНО: шаблон мы могли взять из subtitles-сегмента, который сами
    # же спрятали (visible=False) на прошлом проходе. deepcopy это
    # унаследовал — принудительно показываем караоке/интро.
    s["visible"] = True
    return s


# ─────────────────────────────────────────────────────────────────────
# Развёртка слов в интервалы
# ─────────────────────────────────────────────────────────────────────

def layout_words(sentences: list[dict]) -> list[tuple[int, int, str]]:
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
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "medium"))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-transcribe", action="store_true")
    p.add_argument("--keep-existing", action="store_true",
                   help="Не удалять старую subtitles-дорожку, добавить караоке поверх.")
    p.add_argument("--no-reference", action="store_true",
                   help="Не подставлять эталонный текст из SCENE_TEXTS; использовать чистый whisper.")
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

    bkp = DRAFT_FILE.with_suffix(".json.karaoke-backup")
    shutil.copy2(DRAFT_FILE, bkp)
    print(f"Бэкап: {bkp.name}")

    tmpl_seg, tmpl_mat = grab_template(draft)

    # Удаляем «наши» прежние text-дорожки (karaoke / intro / безымянные)
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

    # Удаляем дорожку subtitles ЦЕЛИКОМ. Шаблон font/style для караоке
    # мы уже забрали выше через grab_template, больше эта дорожка не нужна.
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

    # Создаём новые text-треки
    intro_track = {"attribute": 0, "flag": 0, "id": gen_id_hex(),
                   "is_default_name": True, "name": "intro",
                   "segments": [], "type": "text"}
    karaoke_track = {"attribute": 0, "flag": 0, "id": gen_id_hex(),
                     "is_default_name": True, "name": "karaoke",
                     "segments": [], "type": "text"}
    draft["tracks"].append(karaoke_track)
    draft["tracks"].append(intro_track)

    # Интро = первый voice-сегмент по таймлайну (sentences уже отсортированы)
    intro_sentence = sentences[0] if sentences else None
    if intro_sentence:
        intro_start_us = intro_sentence["abs_start_us"]
        intro_end_us = intro_start_us + intro_sentence["duration_us"]
    else:
        intro_start_us, intro_end_us = 0, 0

    intro_steps = build_intro_steps(intro_sentence) if intro_sentence else []
    for step_start_us, step_dur_us, step_text in intro_steps:
        intro_mat = make_intro_text_material(tmpl_mat, step_text)
        intro_seg = make_text_segment(
            tmpl_seg, intro_mat["id"], step_start_us, step_dur_us, INTRO_Y,
        )
        draft["materials"]["texts"].append(intro_mat)
        intro_track["segments"].append(intro_seg)
    if intro_steps:
        total_dur = sum(d for _, d, _ in intro_steps) / 1_000_000
        print(f"Интро: {len(intro_steps)} шагов на "
              f"{intro_start_us/1_000_000:.2f}–{(intro_start_us + int(total_dur*1_000_000))/1_000_000:.2f}s.")

    # Караоке (исключая зону интро)
    inserted_words = 0
    skipped_in_intro = 0
    for start_us, end_us, word in words:
        if intro_start_us <= start_us < intro_end_us:
            skipped_in_intro += 1
            continue
        mat = make_text_material(tmpl_mat, word.upper(), KARAOKE_FONT_SIZE, KARAOKE_COLOR)
        seg = make_text_segment(
            tmpl_seg, mat["id"], start_us, end_us - start_us, KARAOKE_Y,
        )
        draft["materials"]["texts"].append(mat)
        karaoke_track["segments"].append(seg)
        inserted_words += 1
    karaoke_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])
    if skipped_in_intro:
        print(f"Пропущено караоке-слов в зоне интро: {skipped_in_intro}.")

    # Сохраняем + синхронизация .bak / template-2.tmp
    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = DRAFT_DIR / tgt_name
        try:
            shutil.copy2(DRAFT_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    print(f"Драфт сохранён + синхронизированы template-2.tmp и .bak. "
          f"Интро-сегментов: {len(intro_track['segments'])}, "
          f"караоке-слов: {inserted_words}.")
    print("Открой CapCut → проект «Сизифов труд» → проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
