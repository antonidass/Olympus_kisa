"""
Подмена 5 scene-mp3 в драфте «Сизифов труд» на свежие версии,
собранные из обновлённых approved_sentences (после правок текста).

Что делает:
  1. Собирает новые scene-mp3 (с ffmpeg-склейкой scene_04_05 = sent_005 + sent_006).
  2. Кладёт в content/Сизифов Труд/voiceover/audio/ поверх старых (с бэкапом
     .pre-swap-backup один раз).
  3. Открывает draft_content.json «Сизифов труд» и:
     • обновляет materials.audios[*].duration на реальную длину файла,
     • для каждого voice-сегмента из 5 затронутых сцен:
         – ставит новую duration в target_timerange/source_timerange,
         – сдвигает все последующие voice/video/sfx сегменты на дельту,
         – чистит volume-keyframes (mute-окна от bleep_sisyphus теряют
           смысл — они привязаны к старым позициям слов),
     • видео-сегменты той же сцены растягивает/сжимает (если 2 шота —
       делит новую длительность поровну),
     • music-сегмент удлиняет/сокращает до новой total-длительности.
  4. Удаляет 5 записей из _karaoke_cache_sisyphus.json (whisper заново
     перезаслушает обновлённые mp3 при следующем запуске karaoke_sisyphus).
  5. Сохраняет драфт + sync .bak / template-2.tmp.

После этого надо запустить karaoke_sisyphus.py — он подтянет новые
тексты и timing'и (whisper-кэш для 5 сцен очищен).

Запуск (CapCut должен быть закрыт):
    python pyCapCut/swap_audio_v2_sisyphus.py
    python pyCapCut/swap_audio_v2_sisyphus.py --dry-run   # только показать план
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

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
APPROVED_DIR = PROJECT_ROOT / "content" / "Сизифов Труд" / "voiceover" / "audio" / "approved_sentences"
SCENE_AUDIO_DIR = PROJECT_ROOT / "content" / "Сизифов Труд" / "voiceover" / "audio"
CACHE_FILE = Path(__file__).resolve().parent / "_karaoke_cache_sisyphus.json"

LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFT_DIR = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft" / "Сизифов труд"
DRAFT_FILE = DRAFT_DIR / "draft_content.json"


# ─────────────────────────────────────────────────────────────────────
# План замен: scene_NN.mp3 → список sentence-файлов и sid
# ─────────────────────────────────────────────────────────────────────

# (scene-mp3 имя, [sentence-файлы для склейки], sid в SCENE_LAYOUT)
PLAN: List[Tuple[str, List[str], str]] = [
    ("scene_04_05.mp3", ["sentence_005_v1.mp3", "sentence_006_v1.mp3"], "04-05"),
    ("scene_10.mp3",    ["sentence_010_v1.mp3"],                         "10"),
    ("scene_11.mp3",    ["sentence_011_v1.mp3"],                         "11"),
    ("scene_17.mp3",    ["sentence_016_v2.mp3"],                         "17"),
    ("scene_18_19.mp3", ["sentence_017_v1.mp3"],                         "18-19"),
]

# Соответствие sid → число шотов (= число video-сегментов в треке main).
# Должно совпадать с build_sisyphus.py / enrich_sisyphus.py.
SCENE_LAYOUT: List[Tuple[str, int]] = [
    ("01", 1), ("02", 2), ("03", 1), ("04-05", 2), ("06", 1), ("07", 1),
    ("08-09", 2), ("10", 1), ("11", 1), ("12", 1), ("13", 1), ("14-15", 2),
    ("16", 1), ("17", 1), ("18-19", 2), ("20", 1), ("21", 1), ("22", 1),
    ("23", 1), ("24", 1), ("25", 1), ("26", 1), ("27", 1),
]


# ─────────────────────────────────────────────────────────────────────
# Утилиты
# ─────────────────────────────────────────────────────────────────────

def find_ffmpeg() -> str:
    p = shutil.which("ffmpeg")
    if p:
        return p
    apps = LOCALAPPDATA / "CapCut" / "Apps"
    cands = sorted(apps.glob("*/ffmpeg.exe"), key=lambda x: x.parent.name, reverse=True)
    if cands:
        return str(cands[0])
    raise SystemExit("Не нашёл ffmpeg ни в PATH, ни в CapCut\\Apps.")


def mp3_duration_us(path: Path) -> int:
    from pymediainfo import MediaInfo
    mi = MediaInfo.parse(str(path))
    for t in mi.tracks:
        if t.track_type == "Audio" and t.duration is not None:
            return int(float(t.duration) * 1000)
    raise RuntimeError(f"Не нашёл audio-дорожку в {path}")


def check_capcut_closed() -> bool:
    try:
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
        text = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        if "CapCut.exe" in text or "JianyingPro" in text:
            return False
    except Exception:
        pass
    return True


def concat_or_copy(parts: List[Path], dst: Path, ffmpeg: str) -> None:
    """Если 1 файл — copy. Если несколько — concat через ffmpeg demuxer."""
    if len(parts) == 1:
        shutil.copy2(parts[0], dst)
        return
    # ffmpeg concat demuxer требует list-файл
    list_path = dst.parent / (dst.stem + ".concat.txt")
    list_path.write_text(
        "\n".join(f"file '{str(p).replace(chr(92), '/')}'" for p in parts),
        encoding="utf-8",
    )
    try:
        # -c copy — без re-encode, если параметры одинаковые. CosyVoice mp3
        # все одинаковые (44.1k stereo 192k), так что должно работать.
        subprocess.check_call([
            ffmpeg, "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_path), "-c", "copy", str(dst),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # Fallback: re-encode (медленнее, но надёжнее)
        subprocess.check_call([
            ffmpeg, "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_path), "-c:a", "libmp3lame", "-b:a", "192k",
            str(dst),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        list_path.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────
# Сборка новых scene-mp3
# ─────────────────────────────────────────────────────────────────────

def build_new_scene_mp3s(out_dir: Path, ffmpeg: str) -> List[dict]:
    """Возвращает список {scene, parts, dst, new_dur_us, old_dur_us, delta_us}."""
    info: List[dict] = []
    for scene, parts, sid in PLAN:
        srcs = [APPROVED_DIR / p for p in parts]
        for s in srcs:
            if not s.is_file():
                raise SystemExit(f"Не нашёл source: {s}")
        dst = out_dir / scene
        concat_or_copy(srcs, dst, ffmpeg)
        new_dur = mp3_duration_us(dst)
        old_path = SCENE_AUDIO_DIR / scene
        old_dur = mp3_duration_us(old_path) if old_path.is_file() else 0
        info.append({
            "scene": scene, "parts": parts, "sid": sid, "dst": dst,
            "new_dur_us": new_dur, "old_dur_us": old_dur,
            "delta_us": new_dur - old_dur,
        })
    return info


# ─────────────────────────────────────────────────────────────────────
# Применение к драфту
# ─────────────────────────────────────────────────────────────────────

def get_main_video_track(draft: dict) -> dict:
    return next(t for t in draft["tracks"]
                if t["type"] == "video" and t.get("name") == "main")


def get_voice_track(draft: dict) -> dict:
    return next(t for t in draft["tracks"]
                if t["type"] == "audio" and t.get("name") == "voice")


def get_music_track(draft: dict) -> dict | None:
    return next((t for t in draft["tracks"]
                 if t["type"] == "audio" and t.get("name") == "music"), None)


def get_sfx_track(draft: dict) -> dict | None:
    return next((t for t in draft["tracks"]
                 if t["type"] == "audio" and t.get("name") == "sfx"), None)


def shot_indexes_for_sid(sid: str) -> List[int]:
    out: List[int] = []
    cursor = 0
    for s, n in SCENE_LAYOUT:
        if s == sid:
            return list(range(cursor, cursor + n))
        cursor += n
    return out


def apply_shifts_in_track(track: dict, threshold_us: int, delta_us: int,
                           skip_segment_id: str | None = None) -> int:
    """Сдвигает все сегменты, чей start_us > threshold_us, на delta_us.
    Возвращает количество сдвинутых."""
    n = 0
    for seg in track["segments"]:
        if seg.get("id") == skip_segment_id:
            continue
        s = seg["target_timerange"]["start"]
        if s > threshold_us:
            seg["target_timerange"]["start"] = s + delta_us
            n += 1
    return n


def clear_volume_keyframes(seg: dict) -> None:
    """Снимает наши mute-окна (KFTypeVolume) с сегмента, не трогая
    остальные кейфреймы (KFTypePosition и т.п.)."""
    cks = seg.get("common_keyframes", [])
    seg["common_keyframes"] = [b for b in cks if b.get("property_type") != "KFTypeVolume"]


def apply_to_draft(draft: dict, info: List[dict]) -> List[str]:
    """Главная функция. Применяет дельты по timeline."""
    log: List[str] = []
    audios_by_id = {a["id"]: a for a in draft["materials"]["audios"]}
    main = get_main_video_track(draft)
    voice = get_voice_track(draft)
    music = get_music_track(draft)
    sfx = get_sfx_track(draft)

    # Сортируем voice-сегменты по таймлайну (на всякий случай)
    voice["segments"].sort(key=lambda s: s["target_timerange"]["start"])

    # Идём по 5 заменам в порядке таймлайна (sid → time)
    plan_sids = [item["sid"] for item in info]
    info_by_sid = {item["sid"]: item for item in info}

    cumulative_shift = 0
    sids_in_order = [s for s, _ in SCENE_LAYOUT]
    for sid in sids_in_order:
        if sid not in plan_sids:
            continue
        item = info_by_sid[sid]
        delta = item["delta_us"]
        if delta == 0:
            continue

        # Ищем voice-сегмент этой сцены — по имени файла материала.
        target_vseg = None
        for vseg in voice["segments"]:
            mat = audios_by_id.get(vseg["material_id"])
            if not mat:
                continue
            if Path(mat.get("path", "")).name == item["scene"]:
                target_vseg = vseg
                break
        if target_vseg is None:
            log.append(f"  ⚠ {item['scene']}: не нашёл voice-сегмент в треке")
            continue

        # Старая позиция voice-сегмента (после уже применённых сдвигов).
        v_start = target_vseg["target_timerange"]["start"]
        v_old_end = v_start + target_vseg["target_timerange"]["duration"]

        # 1. Обновляем длительность voice-сегмента и материала.
        target_vseg["target_timerange"]["duration"] = item["new_dur_us"]
        if target_vseg.get("source_timerange"):
            target_vseg["source_timerange"]["duration"] = item["new_dur_us"]
        # Чистим volume-keyframes (bleep-окна теряют смысл — позиции слов поменялись)
        clear_volume_keyframes(target_vseg)

        mat = audios_by_id.get(target_vseg["material_id"])
        if mat:
            mat["duration"] = item["new_dur_us"]

        # 2. Сдвигаем последующие voice-сегменты.
        moved_v = apply_shifts_in_track(voice, v_old_end - 1, delta,
                                          skip_segment_id=target_vseg["id"])

        # 3. Видеосегменты этой сцены — растягиваем/сжимаем + двигаем последующие.
        idxs = shot_indexes_for_sid(sid)
        if not idxs:
            log.append(f"  ⚠ {item['scene']}: не нашёл видеосегменты для sid={sid}")
        else:
            n_shots = len(idxs)
            base = item["new_dur_us"] // n_shots
            remainder = item["new_dur_us"] - base * n_shots

            # Стартовая позиция первого шота (= старая, не двигаем).
            cur_start = main["segments"][idxs[0]]["target_timerange"]["start"]
            for j, vi in enumerate(idxs):
                vseg = main["segments"][vi]
                new_dur = base + (remainder if j == n_shots - 1 else 0)
                vseg["target_timerange"]["start"] = cur_start
                vseg["target_timerange"]["duration"] = new_dur
                cur_start += new_dur

            # Сдвигаем последующие видеосегменты на delta
            last_video_end_old = (main["segments"][idxs[-1]]["target_timerange"]["start"]
                                   - delta + new_dur)  # пересчитаем threshold
            # Используем порог = старый конец последнего шота этой сцены
            old_last_end = (main["segments"][idxs[-1]]["target_timerange"]["start"]
                             + main["segments"][idxs[-1]]["target_timerange"]["duration"])
            # apply_shifts по индексу проще: всё что после idxs[-1]
            moved_main = 0
            for k in range(idxs[-1] + 1, len(main["segments"])):
                main["segments"][k]["target_timerange"]["start"] += delta
                moved_main += 1

        # 4. SFX-сегменты — двигаем все, чей start > v_old_end.
        moved_sfx = 0
        if sfx is not None:
            moved_sfx = apply_shifts_in_track(sfx, v_old_end - 1, delta)

        cumulative_shift += delta
        log.append(
            f"  → {item['scene']:<18} sid={sid:<6} "
            f"dur {item['old_dur_us']/1_000_000:.2f}s → {item['new_dur_us']/1_000_000:.2f}s "
            f"(Δ {delta/1_000_000:+.2f}s)  "
            f"сдвинуто: voice={moved_v} video={moved_main} sfx={moved_sfx}"
        )

    # 5. Music-сегмент — растягиваем до конца (cumulative_shift общий).
    if music and music.get("segments"):
        mseg = music["segments"][0]
        old_dur = mseg["target_timerange"]["duration"]
        mseg["target_timerange"]["duration"] = old_dur + cumulative_shift
        if mseg.get("source_timerange"):
            mseg["source_timerange"]["duration"] = old_dur + cumulative_shift
        log.append(f"  ♪ music: {old_dur/1_000_000:.2f}s → "
                   f"{(old_dur + cumulative_shift)/1_000_000:.2f}s")

    log.append(f"  Σ кумулятивный сдвиг конца таймлайна: {cumulative_shift/1_000_000:+.2f}s")
    return log


# ─────────────────────────────────────────────────────────────────────
# Очистка whisper-кэша по 5 файлам
# ─────────────────────────────────────────────────────────────────────

def clean_whisper_cache(scene_names: List[str]) -> int:
    if not CACHE_FILE.is_file():
        return 0
    cache = json.load(open(CACHE_FILE, encoding="utf-8"))
    removed = 0
    for name in scene_names:
        if name in cache:
            del cache[name]
            removed += 1
    json.dump(cache, open(CACHE_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return removed


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not DRAFT_FILE.is_file():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1
    if not args.dry_run and not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой его полностью (включая трей) и перезапусти.")
        return 1

    ffmpeg = find_ffmpeg()
    print(f"ffmpeg: {ffmpeg}")

    # Собираем новые mp3 во временную папку
    tmp_dir = Path(__file__).resolve().parent / "_tmp_swap_audio"
    tmp_dir.mkdir(exist_ok=True)
    print(f"\nСобираю новые scene-mp3 во {tmp_dir} …")
    info = build_new_scene_mp3s(tmp_dir, ffmpeg)
    print()
    print(f"  {'scene':<18} {'old':>8} {'new':>8} {'delta':>8}")
    for it in info:
        print(f"  {it['scene']:<18} "
              f"{it['old_dur_us']/1_000_000:>7.2f}s "
              f"{it['new_dur_us']/1_000_000:>7.2f}s "
              f"{it['delta_us']/1_000_000:>+7.2f}s")

    if args.dry_run:
        print("\n--dry-run: ничего не меняю.")
        return 0

    # Бэкап mp3 (один раз)
    print("\nКладу новые mp3 в content/Сизифов Труд/voiceover/audio/ (с бэкапом старых)…")
    for it in info:
        old = SCENE_AUDIO_DIR / it["scene"]
        bkp = old.with_suffix(".mp3.pre-swap-backup")
        if not bkp.exists() and old.is_file():
            shutil.copy2(old, bkp)
        shutil.copy2(it["dst"], old)
        print(f"  {it['scene']}  ✓")

    # Бэкап драфта
    print()
    bkp = DRAFT_FILE.with_suffix(".json.swapaudio-backup")
    shutil.copy2(DRAFT_FILE, bkp)
    print(f"Бэкап драфта: {bkp.name}")

    # Применяем изменения к драфту
    print()
    print("Обновляю драфт:")
    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))
    for line in apply_to_draft(draft, info):
        print(line)

    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = DRAFT_DIR / tgt_name
        try:
            shutil.copy2(DRAFT_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    # Чистим whisper-кэш
    removed = clean_whisper_cache([it["scene"] for it in info])
    print(f"\nWhisper-кэш: удалено записей {removed}/{len(info)}.")

    # Чистим tmp
    for it in info:
        try:
            it["dst"].unlink(missing_ok=True)
        except Exception:
            pass
    try:
        tmp_dir.rmdir()
    except Exception:
        pass

    print()
    print("✓ Готово. Дальше — запусти караоке, чтобы пересоздать субтитры")
    print("  под новые тексты:")
    print("    external/CosyVoice/.venv_cosyvoice/Scripts/python.exe pyCapCut/karaoke_sisyphus.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
