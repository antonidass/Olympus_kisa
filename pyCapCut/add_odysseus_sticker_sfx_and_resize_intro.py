"""
Доводка драфта «Одиссей и Пенелопа» 2026-05-16:

1. Уменьшаем размер интро-титула «ОДИССЕЙ И ПЕНЕЛОПА / МИФ ЗА МИНУТУ»
   с raw 22.75 (≈23 в UI CapCut) до 17.0 — большой шрифт перекрывал
   halftone-вспышку зелёных точек.

2. Добавляем дорожку `sticker_sfx` с SFX на каждый из 13 стикеров.
   Файлы и громкости взяты из эталона «Дионис и Ариадна»:
     * Pac (e7a6cec88...mp3, 0.45s) — vol 0.395, базовый щелчок
     * Tone (f4d76f47351...mp3, 0.78s) — vol 0.28, мягкий тон вариации
     * Ding (ab140124...mp3 / CapCut «Ding», 2.02s) — vol 1.0, акцент

   Раскладка: Pac на большинстве, Tone на чётных вариациях, Ding —
   три «панчевых» момента (медаль «лучшая жена», легендарный лук,
   финальный Tinder match).

Запуск (CapCut обязательно закрыт):
    python pyCapCut/add_odysseus_sticker_sfx_and_resize_intro.py
"""

from __future__ import annotations

import datetime
import io
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFTS = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
DRAFT_DIR = DRAFTS / "Одиссей и Пенелопа"
DRAFT_FILE = DRAFT_DIR / "draft_content.json"

CAPCUT_MUSIC_CACHE = LOCALAPPDATA / "CapCut" / "User Data" / "Cache" / "music"

NEW_INTRO_FONT_SIZE = 17.0

# Три SFX-источника, как в Дионисе.
SFX_PAC = {
    "name": "e7a6cec88ef0921b00a416c9bed90074.mp3",
    "path": CAPCUT_MUSIC_CACHE / "e7a6cec88ef0921b00a416c9bed90074.mp3",
    "duration_us": 450_000,
    "volume": 0.39506328105926514,
    "type": "extract_music",
    "category_name": "local",
    "label": "Pac",
}
SFX_TONE = {
    "name": "f4d76f47351109ffb8b5068c2a5dbe71.mp3",
    "path": CAPCUT_MUSIC_CACHE / "f4d76f47351109ffb8b5068c2a5dbe71.mp3",
    # В Дионисе источник пишет 833333, target 783333 — берём 783333.
    "duration_us": 783_333,
    "volume": 0.28,
    "type": "extract_music",
    "category_name": "local",
    "label": "tone",
}
SFX_DING = {
    "name": "Ding",
    "path": CAPCUT_MUSIC_CACHE / "ab1401246f23f83ab8520ee839a50eb9.mp3",
    "duration_us": 2_016_666,
    "volume": 1.0,
    "type": "sound",
    "category_name": "В тренде",
    "effect_id": "6990639268369385474",
    "category_id": "7313817165235243777",
    "app_id": 1775,
    "label": "Ding",
}

# Раскладка SFX по 13 стикерам (порядок = sticker_plan из add_odysseus_stickers.py).
STICKER_SFX_PLAN = [
    SFX_PAC,    # 0  scene_02  Троя
    SFX_TONE,   # 1  scene_03  не вернулся
    SFX_PAC,    # 2  scene_04  часы
    SFX_TONE,   # 3  scene_05  108 женихов
    SFX_DING,   # 4  scene_09  «лучшая жена» — комический акцент
    SFX_PAC,    # 5  scene_10  Ctrl+Z распускает
    SFX_TONE,   # 6  scene_13  GPS Одиссей плывёт
    SFX_PAC,    # 7  scene_16  квестовый свиток состязания
    SFX_DING,   # 8  scene_17  легендарный лук Одиссея — акцент
    SFX_PAC,    # 9  scene_20  5 звёзд за выстрел
    SFX_TONE,   # 10 scene_21  замок-проверка узнавания
    SFX_PAC,    # 11 scene_23  печать verified
    SFX_DING,   # 12 scene_24  Tinder match — финальный панч
]


def gen_id_hex() -> str:
    return uuid.uuid4().hex


def check_capcut_closed() -> bool:
    try:
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
        text = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        if "CapCut.exe" in text or "JianyingPro" in text:
            return False
    except Exception:
        pass
    return True


# ─────────────────────────────────────────────────────────────────────
# Resize intro
# ─────────────────────────────────────────────────────────────────────

def resize_intro(draft: dict) -> str:
    """Уменьшаем интро-карточку до 17.0 (обе строки)."""
    target_size = NEW_INTRO_FONT_SIZE
    patched = 0

    for m in draft["materials"].get("texts", []):
        fp = (m.get("font_path") or "").lower()
        if "stromtrial" not in fp.replace("strome", "strome").replace("trial", "trial"):
            # точное сравнение тоже допустимо
            if "strome" not in fp:
                continue
        m["font_size"] = target_size
        m["text_size"] = target_size
        # patch content JSON (styles[*].size)
        try:
            c = json.loads(m.get("content", "{}"))
            for st in c.get("styles", []):
                if "size" in st:
                    st["size"] = target_size
            m["content"] = json.dumps(c, ensure_ascii=False)
            m["base_content"] = m["content"]
        except Exception as e:
            return f"⚠ не смог распарсить content для {m.get('id','?')[:8]}: {e}"
        patched += 1

    if patched == 0:
        return "⚠ не нашёл интро-материала на STRomeTrial — пропуск"
    return f"✓ интро-шрифт 22.75 → {target_size} (материалов обновлено: {patched})"


# ─────────────────────────────────────────────────────────────────────
# Sticker SFX
# ─────────────────────────────────────────────────────────────────────

def make_audio_material(sfx: dict) -> dict:
    mid = gen_id_hex()
    mat = {
        "id": mid,
        "unique_id": "",
        "type": sfx["type"],
        "name": sfx["name"],
        "duration": sfx["duration_us"],
        "path": str(sfx["path"]).replace("\\", "/"),
        "category_name": sfx["category_name"],
        "wave_points": [],
        "music_id": "",
        "app_id": sfx.get("app_id", 0),
        "text_id": "",
        "tone_type": "",
        "source_platform": 0,
        "video_id": "",
        "effect_id": sfx.get("effect_id", ""),
        "resource_id": "",
        "third_resource_id": "",
        "category_id": sfx.get("category_id", ""),
        "intensifies_path": "",
        "formula_id": "",
        "check_flag": 1 if sfx["type"] == "sound" else 3,
        "team_id": "",
        "local_material_id": mid if sfx["type"] == "extract_music" else "",
        "tone_speaker": "",
        "mock_tone_speaker": "",
        "tone_effect_id": "",
        "tone_effect_name": "",
        "tone_platform": "",
        "cloned_model_type": "",
        "tone_category_id": "",
        "tone_category_name": "",
        "tone_second_category_id": "",
        "tone_second_category_name": "",
        "tone_emotion_name_key": "",
        "tone_emotion_style": "",
        "tone_emotion_role": "",
        "tone_emotion_selection": "",
        "tone_emotion_scale": 0.0,
        "moyin_emotion": "",
        "request_id": "",
        "query": "",
        "search_id": "",
        "sound_separate_type": "",
        "is_text_edit_overdub": False,
        "is_ugc": False,
        "is_ai_clone_tone": False,
        "is_ai_clone_tone_post": False,
        "source_from": "",
        "copyright_limit_type": "none",
        "aigc_history_id": "",
        "aigc_item_id": "",
        "music_source": "",
        "pgc_id": "",
        "pgc_name": "",
        "similiar_music_info": {"original_song_id": "", "original_song_name": ""},
        "ai_music_type": 0,
        "ai_music_enter_from": "",
        "lyric_type": 0,
        "tts_task_id": "",
        "tts_generate_scene": "",
        "ai_music_generate_scene": 0,
        "tts_benefit_info": {
            "benefit_type": "none",
            "benefit_log_id": "",
            "benefit_log_extra": "",
            "benefit_amount": -1,
        },
    }
    if sfx["type"] == "extract_music":
        mat["music_id"] = mid  # extract_music = music_id == own id
    return mat


def make_support_materials(draft: dict) -> tuple[str, str, str, str]:
    """Создаёт 4 вспомогательных материала для одного audio-сегмента."""
    speed = {"id": gen_id_hex(), "type": "speed", "mode": 0, "speed": 1.0, "curve_speed": None}
    placeholder = {
        "id": gen_id_hex(), "type": "placeholder_info", "meta_type": "none",
        "res_path": "", "res_text": "", "error_path": "", "error_text": "",
    }
    sound_ch = {
        "id": gen_id_hex(), "type": "none",
        "audio_channel_mapping": 0, "is_config_open": False,
    }
    vocal = {
        "id": gen_id_hex(), "type": "vocal_separation", "choice": 0,
        "removed_sounds": [], "time_range": None, "production_path": "",
        "final_algorithm": "", "enter_from": "",
    }
    draft["materials"].setdefault("speeds", []).append(speed)
    draft["materials"].setdefault("placeholder_infos", []).append(placeholder)
    draft["materials"].setdefault("sound_channel_mappings", []).append(sound_ch)
    draft["materials"].setdefault("vocal_separations", []).append(vocal)
    return speed["id"], placeholder["id"], sound_ch["id"], vocal["id"]


def make_audio_segment(material_id: str, sfx: dict, start_us: int,
                       supports: tuple[str, str, str, str]) -> dict:
    return {
        "id": gen_id_hex(),
        "source_timerange": {"start": 0, "duration": int(sfx["duration_us"])},
        "target_timerange": {"start": int(start_us), "duration": int(sfx["duration_us"])},
        "render_timerange": {"start": 0, "duration": 0},
        "desc": "",
        "state": 0,
        "speed": 1.0,
        "is_loop": False,
        "is_tone_modify": False,
        "reverse": False,
        "intensifies_audio": False,
        "cartoon": False,
        "volume": float(sfx["volume"]),
        "last_nonzero_volume": 1.0,
        "clip": None,
        "uniform_scale": None,
        "material_id": material_id,
        "extra_material_refs": list(supports),
        "render_index": 0,
        "keyframe_refs": [],
        "enable_lut": False,
        "enable_adjust": False,
        "enable_hsl": False,
        "visible": True,
        "group_id": "",
        "enable_color_curves": True,
        "enable_hsl_curves": True,
        "track_render_index": 0,
        "hdr_settings": None,
        "enable_color_wheels": True,
        "track_attribute": 0,
        "is_placeholder": False,
        "template_id": "",
        "enable_smart_color_adjust": False,
        "template_scene": "default",
        "common_keyframes": [],
        "caption_info": None,
        "responsive_layout": {
            "enable": False, "target_follow": "",
            "size_layout": 0, "horizontal_pos_layout": 0, "vertical_pos_layout": 0,
        },
        "enable_color_match_adjust": False,
        "enable_color_correct_adjust": False,
        "enable_adjust_mask": False,
        "raw_segment_id": "",
        "lyric_keyframes": None,
        "enable_video_mask": True,
        "digital_human_template_group_id": "",
        "color_correct_alg_result": "",
        "source": "segmentsourcenormal",
        "enable_mask_stroke": False,
        "enable_mask_shadow": False,
        "enable_color_adjust_pro": False,
    }


def make_audio_track(name: str, segments: list[dict]) -> dict:
    return {
        "id": gen_id_hex(),
        "type": "audio",
        "segments": segments,
        "flag": 0,
        "attribute": 0,
        "name": name,
        "is_default_name": False,
    }


def apply_sticker_sfx(draft: dict) -> list[str]:
    log: list[str] = []
    stickers_track = next(
        (t for t in draft["tracks"]
         if t.get("name") == "stickers" or t.get("type") == "sticker"),
        None,
    )
    if not stickers_track:
        log.append("⚠ трек 'stickers' не найден — SFX пропущены")
        return log

    sticker_segs = stickers_track.get("segments", [])
    if len(sticker_segs) != len(STICKER_SFX_PLAN):
        log.append(
            f"⚠ стикеров {len(sticker_segs)}, а раскладка под {len(STICKER_SFX_PLAN)} — "
            f"проверь STICKER_SFX_PLAN. Использую min."
        )

    # Уже есть sticker_sfx? Если да — снести, чтобы не дублировать.
    existing = next(
        (t for t in draft["tracks"] if t.get("type") == "audio" and t.get("name") == "sticker_sfx"),
        None,
    )
    if existing:
        draft["tracks"].remove(existing)
        log.append("  · удалил старый трек sticker_sfx (пересоздаю)")

    # Проверяем, что cache-файлы существуют.
    for sfx in {SFX_PAC["name"]: SFX_PAC, SFX_TONE["name"]: SFX_TONE, SFX_DING["name"]: SFX_DING}.values():
        if not sfx["path"].exists():
            log.append(f"⚠ нет файла {sfx['path']} — открой Дионис в CapCut один раз, чтобы он скачался")
            return log

    new_segments: list[dict] = []
    for i, (seg, sfx) in enumerate(zip(sticker_segs, STICKER_SFX_PLAN)):
        sticker_start = int(seg["target_timerange"]["start"])
        mat = make_audio_material(sfx)
        draft["materials"]["audios"].append(mat)
        supports = make_support_materials(draft)
        audio_seg = make_audio_segment(mat["id"], sfx, sticker_start, supports)
        new_segments.append(audio_seg)
        log.append(
            f"  seg{i:>2}: t={sticker_start/1e6:6.2f}s  "
            f"{sfx['label']:<5} dur={sfx['duration_us']/1e6:.2f}s vol={sfx['volume']:.3f}"
        )

    draft["tracks"].append(make_audio_track("sticker_sfx", new_segments))
    log.append(f"✓ добавлен трек sticker_sfx с {len(new_segments)} SFX-сегментами")
    return log


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    if not DRAFT_FILE.exists():
        print(f"Не нашёл драфт: {DRAFT_FILE}")
        return 1
    if not check_capcut_closed():
        print("⛔ CapCut запущен — закрой его.")
        return 1

    with open(DRAFT_FILE, "r", encoding="utf-8") as f:
        draft = json.load(f)

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DRAFT_DIR / f"draft_content.json.intro-sfx-{ts}"
    shutil.copy(DRAFT_FILE, backup)
    print(f"Бекап: {backup.name}")

    print()
    print("Интро-шрифт:")
    print(f"  {resize_intro(draft)}")

    print()
    print("Sticker SFX:")
    for line in apply_sticker_sfx(draft):
        print(line)

    with open(DRAFT_FILE, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False)

    print()
    print("✓ готово. Открой CapCut, проверь:")
    print("   — интро-карточка стала компактнее (новый размер 17)")
    print("   — у каждого стикера на дорожке sticker_sfx звучит щелчок/тон/Ding")
    return 0


if __name__ == "__main__":
    sys.exit(main())
