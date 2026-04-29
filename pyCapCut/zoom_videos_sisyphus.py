"""
Лёгкий зум всех видео-сегментов главной дорожки «Сизифов труд» —
чтобы за границу кадра уехал Veo-watermark, впечатанный в правый-нижний
угол сгенерированных через Veo mp4.

При scale = 1.10 видимая область сжимается на 5% с каждой стороны:
  • 5% от 1080 = 54 px по горизонтали
  • 5% от 1920 = 96 px по вертикали

Veo-логотип ~60×30 px в углу с отступом 15 px полностью скрывается.

Скрипт идемпотентен — можно запускать сколько угодно раз, всегда
ставит одно и то же значение.

Запуск (CapCut должен быть закрыт):
    python pyCapCut/zoom_videos_sisyphus.py
    python pyCapCut/zoom_videos_sisyphus.py --scale 1.12
    python pyCapCut/zoom_videos_sisyphus.py --reset      # вернуть scale 1.0
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

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFT_DIR = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft" / "Сизифов труд"
DRAFT_FILE = DRAFT_DIR / "draft_content.json"

DEFAULT_SCALE = 1.10


def check_capcut_closed() -> bool:
    try:
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
        text = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        if "CapCut.exe" in text or "JianyingPro" in text:
            return False
    except Exception:
        pass
    return True


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--scale", type=float, default=DEFAULT_SCALE)
    p.add_argument("--reset", action="store_true", help="Сбросить scale до 1.0.")
    args = p.parse_args()

    scale = 1.0 if args.reset else args.scale

    if not DRAFT_FILE.is_file():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1
    if not check_capcut_closed():
        print("⚠ CapCut запущен. Закрой его полностью (включая трей) и перезапусти.")
        return 1

    bkp = DRAFT_FILE.with_suffix(".json.zoom-backup")
    shutil.copy2(DRAFT_FILE, bkp)
    print(f"Бэкап: {bkp.name}")

    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))
    main_track = next(t for t in draft["tracks"]
                       if t["type"] == "video" and t.get("name") == "main")

    n = 0
    for seg in main_track["segments"]:
        clip = seg.setdefault("clip", {})
        clip.setdefault("alpha", 1.0)
        clip.setdefault("flip", {"horizontal": False, "vertical": False})
        clip.setdefault("rotation", 0.0)
        clip.setdefault("transform", {"x": 0.0, "y": 0.0})
        clip["scale"] = {"x": scale, "y": scale}
        n += 1

    json.dump(draft, open(DRAFT_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
        tgt = DRAFT_DIR / tgt_name
        try:
            shutil.copy2(DRAFT_FILE, tgt)
        except Exception as ex:
            print(f"  ⚠ не удалось синхронизировать {tgt_name}: {ex}")

    print(f"\n✓ Поставил scale={scale} на {n} видео-сегментов главной дорожки.")
    if scale > 1.0:
        crop_h = (1 - 1/scale) / 2 * 100
        print(f"  Скрыто примерно по {crop_h:.1f}% с каждой стороны кадра.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
