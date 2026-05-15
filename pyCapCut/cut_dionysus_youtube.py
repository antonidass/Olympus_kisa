"""
Вырезает три сцены из YouTube-версии «Дионис и Ариадна» в CapCut,
чтобы итоговое видео уложилось в 60 секунд (Shorts с музыкой).

Удаляем sentence_010, sentence_012, sentence_016 (атмосферные/декоративные
сцены без потери сюжета). На таймлайне это:
  cut A: 26_816_666 .. 28_916_666  (Δ = 2 100 000 мкс)
  cut B: 30_850_000 .. 32_233_333  (Δ = 1 383 333 мкс)
  cut C: 39_900_000 .. 42_416_666  (Δ = 2 516 666 мкс)

Скрипт обрабатывает резы с конца к началу, иначе сдвиги ломают индексы.
На каждом резе для каждого трека:
  • сегмент полностью внутри реза  → удаляем;
  • сегмент начинается после реза   → start -= Δ;
  • сегмент пересекает рез          → не должно случаться по построению
    (резы попадают на границы voice-сегментов), но если попадётся —
    укорачиваем длительность.

Музыка покрывает весь ролик одним сегментом — её длительность тоже
сокращаем на суммарную Δ.
"""

from __future__ import annotations

import json
import os
import shutil
import datetime

DRAFT_DIR = os.path.expandvars(
    r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\Дионис и АриаднаЮТУБ"
)
DRAFT = os.path.join(DRAFT_DIR, "draft_content.json")

CUTS = [
    (46_850_000, 48_500_000),  # sentence_021 «Прошли годы счастья» (тайминги уже после первого реза)
]


def apply_cut(d: dict, cut_start: int, cut_end: int) -> None:
    delta = cut_end - cut_start
    for track in d["tracks"]:
        new_segments = []
        for seg in track.get("segments", []):
            tr = seg.get("target_timerange") or {}
            s = tr.get("start", 0)
            dur = tr.get("duration", 0)
            e = s + dur

            if s >= cut_end:
                tr["start"] = s - delta
                new_segments.append(seg)
            elif e <= cut_start:
                new_segments.append(seg)
            elif s >= cut_start and e <= cut_end:
                continue
            elif s < cut_start and e > cut_end:
                tr["duration"] = dur - delta
                new_segments.append(seg)
            elif s < cut_start and cut_start < e <= cut_end:
                tr["duration"] = cut_start - s
                new_segments.append(seg)
            elif cut_start <= s < cut_end and e > cut_end:
                tr["start"] = cut_start
                tr["duration"] = e - cut_end
                new_segments.append(seg)
            else:
                new_segments.append(seg)
        track["segments"] = new_segments

    total_duration = d.get("duration")
    if isinstance(total_duration, int):
        d["duration"] = max(0, total_duration - delta)


def main() -> None:
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(DRAFT_DIR, f"draft_content.json.bak.cut-21-{ts}")
    shutil.copy(DRAFT, backup)
    print(f"Backup: {backup}")

    with open(DRAFT, "r", encoding="utf-8") as f:
        d = json.load(f)

    before = d.get("duration", 0)

    for cut_start, cut_end in sorted(CUTS, reverse=True):
        apply_cut(d, cut_start, cut_end)

    after = d.get("duration", 0)
    print(f"Total duration: {before/1e6:.2f}s -> {after/1e6:.2f}s")

    voice = next(t for t in d["tracks"] if t.get("name") == "voice")
    voice_end = max(
        s["target_timerange"]["start"] + s["target_timerange"]["duration"]
        for s in voice["segments"]
    )
    print(f"Voice ends at: {voice_end/1e6:.2f}s ({len(voice['segments'])} segments)")

    with open(DRAFT, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)

    for name in ("draft_content.json.bak", "template-2.tmp"):
        p = os.path.join(DRAFT_DIR, name)
        if os.path.exists(p):
            shutil.copy(DRAFT, p)
    print("Done.")


if __name__ == "__main__":
    main()
