"""Одноразовый патч: добавить стикер SUBSCRIBE в сцену 18 драфта
«Цирцея и Одиссей». Без подпрыгивания (первый проход).

Сцена 18 = idx 18 в main-треке (после раскола scene_01 на a/b).
Старт 59.917с, длительность 4.717с.

Никаких других треков (sticker_sfx, audio, transitions, halftone и т.п.)
не трогает — только добавляет один video-сегмент на трек `stickers`.
"""

from __future__ import annotations

import copy
import datetime
import io
import json
import os
import shutil
import sys
import uuid

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

LOCALAPPDATA = os.environ["LOCALAPPDATA"]
DRAFT_DIR = os.path.join(LOCALAPPDATA, "CapCut", "User Data", "Projects",
                         "com.lveditor.draft", "Цирцея и Одиссей")
DRAFT = os.path.join(DRAFT_DIR, "draft_content.json")

STICKER_PATH = r"C:\Users\Антон\Desktop\BOGI AI\content\Цирцея и Одиссей\images\stickers\cutout\scene_18_circe_subscribe.png"
SCENE_18_IDX = 18  # после раскола scene_01 на a/b

# Нейтральная позиция первого прохода (пользователь поправит руками)
X = -0.50
Y = 0.40
SCALE = 0.245


def gen_hex() -> str:
    return uuid.uuid4().hex


def gen_uuid_upper() -> str:
    return str(uuid.uuid4()).upper()


def get_image_size(path: str) -> tuple[int, int]:
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        return (1024, 1024)


def main() -> None:
    d = json.load(open(DRAFT, encoding="utf-8"))
    main_track = next(t for t in d["tracks"]
                      if t["type"] == "video" and t.get("name") == "main")
    scene = main_track["segments"][SCENE_18_IDX]
    scene_start = int(scene["target_timerange"]["start"])
    scene_dur = int(scene["target_timerange"]["duration"])
    print(f"scene 18: start={scene_start/1e6:.3f}s, dur={scene_dur/1e6:.3f}s")

    # Поиск существующего video-материала-донора (взять любой видео-материал с пути,
    # содержащим stickers/cutout, чтобы клонировать поля). Иначе создаём новый.
    vids = d["materials"]["videos"]
    donor = None
    for v in vids:
        if "stickers" in v.get("path", "").replace("\\", "/").lower():
            donor = v
            break
    if donor is None:
        donor = vids[0]

    w, h = get_image_size(STICKER_PATH)
    print(f"image size: {w}x{h}")

    new_mat = copy.deepcopy(donor)
    new_mat["id"] = gen_hex()
    new_mat["local_material_id"] = gen_hex()
    new_mat["path"] = STICKER_PATH
    new_mat["media_path"] = STICKER_PATH
    new_mat["material_name"] = os.path.basename(STICKER_PATH)
    new_mat["duration"] = 10_800_000_000  # как для PNG-стикеров
    new_mat["width"] = w
    new_mat["height"] = h
    new_mat["has_audio"] = False
    new_mat["type"] = "photo"
    d["materials"]["videos"].append(new_mat)

    # Берём существующий стикер-сегмент как шаблон для всех служебных полей
    stk_track = next(t for t in d["tracks"] if t.get("name") == "stickers")
    template_seg = stk_track["segments"][0]
    seg = copy.deepcopy(template_seg)
    seg["id"] = gen_hex()
    seg["material_id"] = new_mat["id"]
    seg["target_timerange"] = {"start": scene_start, "duration": scene_dur}
    seg["source_timerange"] = {"start": 0, "duration": scene_dur}
    seg["speed"] = 1.0
    seg["common_keyframes"] = []   # без подпрыгивания
    seg["volume"] = 0.0
    seg["last_nonzero_volume"] = 0.0
    seg["clip"] = {
        "scale": {"x": SCALE, "y": SCALE},
        "rotation": 0.0,
        "transform": {"x": X, "y": Y},
        "flip": {"vertical": False, "horizontal": False},
        "alpha": 1.0,
    }
    # extra_material_refs скопированы из template_seg — пусть будут (служебные).
    # Если хочешь чистый сегмент без рефов — раскомментируй:
    # seg["extra_material_refs"] = []
    stk_track["segments"].append(seg)
    stk_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bkp = os.path.join(DRAFT_DIR, f"draft_content.json.subscribe-sticker-{ts}")
    shutil.copy2(DRAFT, bkp)
    json.dump(d, open(DRAFT, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for nm in ("template-2.tmp", "draft_content.json.bak"):
        try:
            shutil.copy2(DRAFT, os.path.join(DRAFT_DIR, nm))
        except Exception:
            pass

    print(f"  стикер: {os.path.basename(STICKER_PATH)}")
    print(f"  позиция: x={X}, y={Y}, scale={SCALE}  (пользователь подвинет руками)")
    print(f"  длительность: вся сцена 18 ({scene_dur/1e6:.3f}s), без подпрыгивания")
    print(f"Бэкап: {os.path.basename(bkp)}")


if __name__ == "__main__":
    main()
