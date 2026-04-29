"""
Цензура «бан-слов» в драфте «Сизифов труд» для TikTok-модерации.

Что делает:
  1. Берёт тот же whisper-кэш и эталонные тексты, что и karaoke_sisyphus.py
     (чтобы понять, где какое слово звучит).
  2. Для каждого слова, чей корень совпадает с BAN_ROOTS, делает две
     одновременные цензуры:
       а) на voice-сегменте — четыре volume-кейфрейма «нормально → 0 →
          0 → нормально» вокруг слова. Звук в этом окне глушится, всё
          остальное играет как было.
       б) на text-сегменте дорожки 'karaoke' (которая уже создана
          karaoke_sisyphus.py) — заменяет text материала на цензурную
          версию: первая и последняя буква оставлены, в середине ★.
          Например «УМИРАЛ» → «У****Л».

  3. Сохраняет драфт + синхронизирует .bak / template-2.tmp.

Запускать ПОСЛЕ karaoke_sisyphus.py (он создаёт текст-сегменты, которые
мы здесь правим). При повторном karaoke надо снова прогнать bleep —
потому что karaoke удаляет и пересоздаёт всё с нуля.

Запуск (CapCut должен быть закрыт):
    external\\CosyVoice\\.venv_cosyvoice\\Scripts\\python.exe pyCapCut\\bleep_sisyphus.py

Опции:
    --dry-run   только показать список «запиканных» слов, не трогать драфт
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import sys
import uuid
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ─────────────────────────────────────────────────────────────────────
# Бан-корни. Любое слово, чей нормализованный (lowercase, без
# не-word символов) текст начинается с одного из корней — пикается.
# Корни написаны в нижнем регистре.
# ─────────────────────────────────────────────────────────────────────

BAN_ROOTS = (
    "умира",     # умирал, умирали, умирающ-
    "умер",      # умер, умерли, умерла
    "битв",      # битв, битвы, битву, битвой
    "похити",    # похитил, похитили, похитила
    "похорон",   # похоронный, похоронные, похоронили
    "хоронил",   # хоронили, хоронить
    "убил",      # убил, убили
    "убива",     # убивал, убивали
)


# Padding вокруг слова (мс). 30 мс хватает чтобы не услышать «хвост»
# звука, и не слишком резко обрывалось.
BLEEP_PAD_MS = 30


# ─────────────────────────────────────────────────────────────────────
# Пути / импорт логики из karaoke_sisyphus
# ─────────────────────────────────────────────────────────────────────

sys.path.insert(0, str(Path(__file__).resolve().parent))
from karaoke_sisyphus import (  # type: ignore
    DRAFT_FILE, DRAFT_DIR,
    collect_voice_segments, transcribe_all,
    substitute_with_reference, layout_words,
    check_capcut_closed, ensure_ffmpeg_in_path,
    KARAOKE_FONT_SIZE, KARAOKE_COLOR,
    RUBIK_BOLD,
    KARAOKE_BORDER_ENABLED, KARAOKE_BORDER_ALPHA, KARAOKE_BORDER_WIDTH,
    KARAOKE_BORDER_COLOR_RGB,
)


# ─────────────────────────────────────────────────────────────────────
# Утилиты
# ─────────────────────────────────────────────────────────────────────

def gen_id_hex() -> str:
    return uuid.uuid4().hex


def gen_id_dashed_upper() -> str:
    return str(uuid.uuid4()).upper()


def normalize_word(w: str) -> str:
    """lowercase + только word-characters."""
    return re.sub(r"[^\w]", "", w, flags=re.UNICODE).lower()


def is_banned(word: str) -> bool:
    n = normalize_word(word)
    if not n:
        return False
    return any(n.startswith(root) for root in BAN_ROOTS)


def censor_text(word: str) -> str:
    """«УМИРАЛ» → «У★★★★Л». Первая и последняя буквы остаются,
    остальные word-characters заменяются на ★. Не-word (пунктуация)
    сохраняется как есть."""
    chars = list(word)
    # Индексы word-character'ов
    word_idx = [i for i, c in enumerate(chars) if re.match(r"\w", c, flags=re.UNICODE)]
    if len(word_idx) <= 2:
        # Слишком короткое — заменяем все буквы на ★ (но pad'им до min 2)
        for i in word_idx:
            chars[i] = "*"
        return "".join(chars)
    # Меняем средние буквы (между первой и последней)
    for i in word_idx[1:-1]:
        chars[i] = "*"
    return "".join(chars)


# ─────────────────────────────────────────────────────────────────────
# Mute-кейфреймы на audio-сегмент
# ─────────────────────────────────────────────────────────────────────

def add_mute_keyframes(seg: dict, word_start_us: int, word_end_us: int,
                        seg_volume: float = 1.0) -> None:
    """Добавляет 4 volume-кейфрейма ко common_keyframes сегмента,
    создавая mute-окно [word_start - pad .. word_end + pad].

    time_offset считается от начала сегмента (target_timerange.start)."""
    base_start_us = seg["target_timerange"]["start"]
    base_dur_us = seg["target_timerange"]["duration"]

    pad_us = BLEEP_PAD_MS * 1000
    a_us = max(0, word_start_us - base_start_us - pad_us)        # начало fade
    b_us = max(0, word_start_us - base_start_us + 1)             # 0
    c_us = min(base_dur_us, word_end_us - base_start_us - 1)     # 0
    d_us = min(base_dur_us, word_end_us - base_start_us + pad_us)  # restore

    # На случай если окно вырождено (слово на самой границе сегмента)
    if d_us <= a_us or c_us <= b_us:
        return

    # Найти или создать общий keyframe-канал по громкости.
    ck_list = seg.setdefault("common_keyframes", [])
    vol_block = next((b for b in ck_list if b.get("property_type") == "KFTypeVolume"), None)
    if vol_block is None:
        vol_block = {
            "id": gen_id_dashed_upper(),
            "keyframe_list": [],
            "material_id": "",
            "property_type": "KFTypeVolume",
        }
        ck_list.append(vol_block)

    # Добавляем 4 кейфрейма (кейфреймы CapCut автоматически сортируются
    # по time_offset при загрузке, но мы тоже отсортируем).
    for offset, val in ((a_us, seg_volume), (b_us, 0.0),
                         (c_us, 0.0), (d_us, seg_volume)):
        vol_block["keyframe_list"].append({
            "id": gen_id_dashed_upper(),
            "time_offset": int(offset),
            "values": [float(val)],
        })
    vol_block["keyframe_list"].sort(key=lambda k: k["time_offset"])


# ─────────────────────────────────────────────────────────────────────
# Цензура текст-материала (replace text + content)
# ─────────────────────────────────────────────────────────────────────

def _stroke_block() -> dict | None:
    if not KARAOKE_BORDER_ENABLED:
        return None
    return {
        "content": {"solid": {"alpha": KARAOKE_BORDER_ALPHA,
                              "color": list(KARAOKE_BORDER_COLOR_RGB)}},
        "width": KARAOKE_BORDER_WIDTH,
    }


def censor_text_material(mat: dict, new_text: str) -> None:
    """Перезаписывает content материала: один стиль на весь текст,
    Rubik-Bold, размер караоке, обводка. Сохраняет всю остальную
    инфраструктуру материала."""
    style = {
        "fill": {"alpha": 1.0, "content": {"render_type": "solid",
                                            "solid": {"alpha": 1.0,
                                                       "color": KARAOKE_COLOR}}},
        "font": {"id": RUBIK_BOLD["id"], "path": RUBIK_BOLD["path"]},
        "range": [0, len(new_text)],
        "size": KARAOKE_FONT_SIZE,
        "useLetterColor": True,
    }
    stroke = _stroke_block()
    if stroke:
        style["strokes"] = [stroke]
    mat["content"] = json.dumps({"text": new_text, "styles": [style]},
                                  ensure_ascii=False)
    mat["base_content"] = mat["content"]
    mat["words"] = {"text": [new_text], "start_time": [0], "end_time": [0]}


# ─────────────────────────────────────────────────────────────────────
# Поиск voice-сегмента и karaoke-text-сегмента по абсолютному времени
# ─────────────────────────────────────────────────────────────────────

def find_voice_segment_at(voice_track: dict, abs_us: int) -> dict | None:
    for seg in voice_track["segments"]:
        s = seg["target_timerange"]["start"]
        d = seg["target_timerange"]["duration"]
        if s <= abs_us < s + d:
            return seg
    return None


def find_karaoke_text_at(karaoke_track: dict, abs_us: int,
                          tolerance_us: int = 60_000) -> dict | None:
    """Ищем text-сегмент, чей старт максимально близок к abs_us.
    Tolerance ~60ms — на случай микрорассинхрона."""
    best = None
    best_d = tolerance_us + 1
    for seg in karaoke_track["segments"]:
        s = seg["target_timerange"]["start"]
        d = abs(s - abs_us)
        if d < best_d:
            best_d = d
            best = seg
    return best


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true",
                   help="Только показать список «запиканных» слов, ничего не писать.")
    args = p.parse_args()

    if not DRAFT_FILE.is_file():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1

    ensure_ffmpeg_in_path()

    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой его полностью (включая трей) и запусти снова.")
        return 1

    print(f"Читаю драфт: {DRAFT_FILE}")
    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))

    # 1. Получаем те же sentences/words, что и karaoke_sisyphus.
    sentences = collect_voice_segments(draft)
    transcribe_all(sentences, model_name="medium", allow_whisper=False)
    substitute_with_reference(sentences)
    words = layout_words(sentences)

    # 2. Отбираем бан-слова
    banned = [(s, e, w) for s, e, w in words if is_banned(w)]
    print(f"\nКандидатов на пик: {len(banned)}")
    for s, e, w in banned:
        print(f"  {s/1_000_000:6.2f}-{e/1_000_000:6.2f}  {w!r:25s} → {censor_text(w)!r}")

    if not banned:
        print("Ничего не нашёл — драфт не трогаю.")
        return 0

    if args.dry_run:
        print("\n--dry-run: ничего не пишу.")
        return 0

    # 3. Бэкап
    bkp = DRAFT_FILE.with_suffix(".json.bleep-backup")
    shutil.copy2(DRAFT_FILE, bkp)
    print(f"\nБэкап: {bkp.name}")

    # 4. Применяем
    voice_track = next(t for t in draft["tracks"]
                       if t["type"] == "audio" and t.get("name") == "voice")
    karaoke_track = next((t for t in draft["tracks"]
                          if t["type"] == "text" and t.get("name") == "karaoke"), None)
    if karaoke_track is None:
        print("⚠ дорожки 'karaoke' нет — сначала запусти karaoke_sisyphus.py")
        return 1

    texts_by_id = {m["id"]: m for m in draft["materials"]["texts"]}

    audio_done = 0
    text_done = 0
    for s, e, w in banned:
        # (a) mute-окно на голос
        vseg = find_voice_segment_at(voice_track, s)
        if vseg is not None:
            add_mute_keyframes(vseg, s, e, seg_volume=vseg.get("volume", 1.0))
            audio_done += 1
        else:
            print(f"  ⚠ не нашёл voice-сегмент для {w!r} @ {s/1_000_000:.2f}s")

        # (b) цензура караоке-текста
        tseg = find_karaoke_text_at(karaoke_track, s)
        if tseg is not None:
            mat = texts_by_id.get(tseg["material_id"])
            if mat is not None:
                # Берём текущий text из material content (он уже UPPERCASE,
                # как раз то, что мы и хотим зацензурить)
                try:
                    parsed = json.loads(mat.get("content", "{}"))
                    cur_text = parsed.get("text", "")
                except Exception:
                    cur_text = w.upper()
                new_text = censor_text(cur_text or w.upper())
                censor_text_material(mat, new_text)
                text_done += 1
        else:
            print(f"  ⚠ не нашёл karaoke text-сегмент для {w!r} @ {s/1_000_000:.2f}s")

    # 5. Сохраняем + sync
    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = DRAFT_DIR / tgt_name
        try:
            shutil.copy2(DRAFT_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    print(f"\n✓ Готово. Голос: {audio_done} mute-окон, "
          f"караоке: {text_done} цензур.")
    print("Открой CapCut → проект «Сизифов труд» → проверь.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
