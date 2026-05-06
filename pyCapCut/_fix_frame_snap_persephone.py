"""
In-place фикс артефакта «робовойс / как из ведра» в драфте Персефоны.

Выравнивает source_timerange.duration и target_timerange.duration к
границе кадра проекта (60fps), чтобы CapCut не включал таймстретч.

См. CAPCUT.md § 7.2.

Запуск (CapCut должен быть закрыт):
    python pyCapCut/_fix_frame_snap_persephone.py
"""
from __future__ import annotations

import datetime
import json
import os
import shutil
import sys
from pathlib import Path

DRAFT_DIR = Path(os.environ["LOCALAPPDATA"]) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft" / "Персефона и Аид"
VOICE_DIR = Path(__file__).resolve().parent.parent / "content" / "Персефона и Аид" / "voiceover" / "audio" / "approved_sentences"
DRAFT = DRAFT_DIR / "draft_content.json"

US = 1_000_000
FPS = 60


def floor_to_frame_us(us: int) -> int:
    frames = (us * FPS) // US
    return (frames * US) // FPS


def main() -> int:
    if not DRAFT.is_file():
        print(f"Не нашёл драфт: {DRAFT}")
        return 1

    try:
        from mutagen.mp3 import MP3
    except ImportError:
        print("Не установлен mutagen. pip install mutagen")
        return 1

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DRAFT.with_name(f"draft_content.json.frame-snap-fix-{ts}")
    shutil.copy(DRAFT, backup)
    print(f"Бэкап:   {backup.name}")

    with open(DRAFT, "r", encoding="utf-8") as f:
        draft = json.load(f)

    audios_by_id = {a["id"]: a for a in draft["materials"]["audios"]}
    mp3_us = {
        f.name: int(MP3(str(f)).info.length * 1_000_000)
        for f in VOICE_DIR.iterdir()
        if f.suffix.lower() == ".mp3"
    }

    voice_track = next(
        t for t in draft["tracks"] if t.get("type") == "audio" and t.get("name") == "voice"
    )

    fixed = 0
    skipped = 0
    print()
    print(f"{'idx':>3} | {'sentence':<22} | {'src':>9} | {'tgt':>9} | action")
    print("-" * 72)

    for i, seg in enumerate(voice_track["segments"]):
        a = audios_by_id.get(seg["material_id"])
        if a is None:
            skipped += 1
            continue
        name = a.get("name", "")
        real_us = mp3_us.get(name)
        if real_us is None:
            skipped += 1
            continue

        cur_src = seg["source_timerange"]["duration"]
        cur_tgt = seg["target_timerange"]["duration"]

        # Берём минимум из реального mp3 и текущего src (на случай если уже обрезано вручную).
        upper = min(real_us, cur_src)
        snapped = floor_to_frame_us(upper)
        # Защита от уползания на 0 (не должно случаться, но):
        if snapped < US // FPS:
            snapped = floor_to_frame_us(real_us)

        if cur_src == snapped and cur_tgt == snapped:
            print(f"{i:>3} | {name:<22} | {cur_src:>9} | {cur_tgt:>9} | ok")
            continue

        seg["source_timerange"]["duration"] = snapped
        seg["target_timerange"]["duration"] = snapped
        if a["duration"] > real_us:
            a["duration"] = real_us
        fixed += 1
        print(f"{i:>3} | {name:<22} | {snapped:>9} | {snapped:>9} | snapped (was src={cur_src} tgt={cur_tgt})")

    with open(DRAFT, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False)

    print()
    print(f"Готово: исправлено {fixed} сегмент(ов), пропущено {skipped}.")
    print(f"Если что — откат: copy /Y \"{backup}\" \"{DRAFT}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
