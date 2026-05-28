"""Одноразовый патч: добавить переход «Бумажный шар» между сценой 15 и 16
в драфте «Цирцея и Одиссей» + crumpled_paper.mp3 SFX.

Точка вставки: scene 15 (idx 16) — это последний шот сцены 15 после раскола
сцены 01 на a/b. scene 16 = idx 17.

Параметры по канону CAPCUT.md §6.3 + memory feedback_paper_bag_sfx:
  - переход effect_id 7249296835204878850, dur 1.066667с
  - SFX crumpled_paper.mp3, vol 1.0, dur 0.866с, старт за 0.333с до
    начала следующей сцены
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
PERSEPHONE = os.path.join(LOCALAPPDATA, "CapCut", "User Data", "Projects",
                          "com.lveditor.draft", "Персефона и Аид", "draft_content.json")

PAPER_BAG_ID = "7249296835204878850"
TRANSITION_DUR_US = 1_066_666
CRUMPLED_FILE = r"C:\Users\Антон\Desktop\BOGI AI\assets\sfx\crumpled_paper.mp3"
CRUMPLED_FULL_DUR_US = 4_271_000
CRUMPLED_USE_DUR_US = 866_666
CRUMPLED_PRE_LEAD_US = 333_333
CRUMPLED_VOLUME = 1.0
# scene_01 разбит на a/b → idx 0,1. scene 15 = idx 16, scene 16 = idx 17.
SCENE_15_IDX = 16


def gen_hex() -> str:
    return uuid.uuid4().hex


def main() -> None:
    d = json.load(open(DRAFT, encoding="utf-8"))
    src = json.load(open(PERSEPHONE, encoding="utf-8"))
    paper_tmpl = next(t for t in src["materials"]["transitions"]
                      if str(t["effect_id"]) == PAPER_BAG_ID)

    main_track = next(t for t in d["tracks"]
                      if t["type"] == "video" and t.get("name") == "main")
    seg15 = main_track["segments"][SCENE_15_IDX]
    seg16 = main_track["segments"][SCENE_15_IDX + 1]
    next_scene_start = seg16["target_timerange"]["start"]

    # 1) Снять старый переход с seg15 (если есть)
    trans_by_id = {t["id"]: t for t in d["materials"]["transitions"]}
    old_refs = list(seg15.get("extra_material_refs", []))
    old_trans_ids = [r for r in old_refs if r in trans_by_id]
    seg15["extra_material_refs"] = [r for r in old_refs if r not in old_trans_ids]
    for tid in old_trans_ids:
        t = trans_by_id[tid]
        print(f'  снял со scene 15: {t.get("name")} (dur {t["duration"]/1e6:.3f}s)')
        d["materials"]["transitions"] = [t2 for t2 in d["materials"]["transitions"]
                                         if t2["id"] != tid]
    if not old_trans_ids:
        print("  у scene 15 не было перехода")

    # 2) Клонировать Бумажный шар и навесить на seg15
    new_trans = copy.deepcopy(paper_tmpl)
    new_trans["id"] = gen_hex()
    new_trans["duration"] = TRANSITION_DUR_US
    d["materials"]["transitions"].append(new_trans)
    seg15.setdefault("extra_material_refs", []).append(new_trans["id"])
    print(f"  добавил Бумажный шар (dur {TRANSITION_DUR_US/1e6:.3f}s) на scene 15 → scene 16")

    # 3) Добавить crumpled_paper.mp3 на трек sfx
    sfx_track = next((t for t in d["tracks"]
                      if t["type"] == "audio" and t.get("name") == "sfx"), None)
    if sfx_track is None:
        print("  WARN трек sfx не найден")
    else:
        aud_id = gen_hex()
        audio_mat = {
            "ai_music_enter_from": "", "ai_music_generate_scene": 0, "ai_music_type": 0,
            "aigc_history_id": "", "aigc_item_id": "", "app_id": 0,
            "category_id": "", "category_name": "local",
            "check_flag": 3, "cloned_model_type": "", "copyright_limit_type": "none",
            "duration": CRUMPLED_FULL_DUR_US, "effect_id": "", "formula_id": "",
            "id": aud_id, "intensifies_path": "",
            "is_ai_clone_tone": False, "is_ai_clone_tone_post": False,
            "is_text_edit_overdub": False, "is_ugc": False,
            "local_material_id": aud_id,
            "lyric_type": 0, "mock_tone_speaker": "", "moyin_emotion": "",
            "music_id": aud_id, "music_source": "",
            "name": "crumpled_paper.mp3", "path": CRUMPLED_FILE,
            "pgc_id": "", "pgc_name": "", "query": "", "request_id": "",
            "resource_id": "", "search_id": "",
            "similiar_music_info": {"original_song_id": "", "original_song_name": ""},
            "sound_separate_type": "", "source_from": "",
            "source_platform": 0, "team_id": "", "text_id": "", "third_resource_id": "",
            "tone_category_id": "", "tone_category_name": "",
            "tone_effect_id": "", "tone_effect_name": "", "tone_platform": "",
            "tone_second_category_id": "", "tone_second_category_name": "",
            "tone_speaker": "", "tone_type": "",
            "type": "extract_music", "video_id": "", "wave_points": [],
        }
        d["materials"]["audios"].append(audio_mat)
        sfx_start = next_scene_start - CRUMPLED_PRE_LEAD_US
        sfx_seg = {
            "caption_info": None, "cartoon": False, "clip": None,
            "color_correct_alg_result": "", "common_keyframes": [], "desc": "",
            "digital_human_template_group_id": "",
            "enable_adjust": False, "enable_adjust_mask": False,
            "enable_color_adjust_pro": False, "enable_color_correct_adjust": False,
            "enable_color_curves": True, "enable_color_match_adjust": False,
            "enable_color_wheels": True, "enable_hsl": False,
            "enable_hsl_curves": True, "enable_lut": False,
            "enable_mask_shadow": False, "enable_mask_stroke": False,
            "enable_smart_color_adjust": False, "enable_video_mask": True,
            "extra_material_refs": [], "group_id": "",
            "id": gen_hex(),
            "intensifies_audio": False, "is_loop": False, "is_placeholder": False,
            "is_tone_modify": False, "keyframe_refs": [],
            "last_nonzero_volume": CRUMPLED_VOLUME, "lyric_keyframes": None,
            "material_id": aud_id, "raw_segment_id": "",
            "render_index": 0, "render_timerange": {"duration": 0, "start": 0},
            "responsive_layout": {"enable": False, "horizontal_pos_layout": 0,
                                  "size_layout": 0, "target_follow": "",
                                  "vertical_pos_layout": 0},
            "reverse": False, "source_timerange": {"duration": CRUMPLED_USE_DUR_US, "start": 0},
            "speed": 1.0, "state": 0, "stretch_alg": "",
            "target_timerange": {"duration": CRUMPLED_USE_DUR_US, "start": sfx_start},
            "template_id": "", "template_scene": "default",
            "track_attribute": 0, "track_render_index": 0, "uniform_scale": None,
            "visible": True, "volume": CRUMPLED_VOLUME,
        }
        sfx_track["segments"].append(sfx_seg)
        sfx_track["segments"].sort(key=lambda s: s["target_timerange"]["start"])
        print(f"  добавил crumpled_paper.mp3 на sfx: start={sfx_start/1e6:.3f}s, "
              f"dur={CRUMPLED_USE_DUR_US/1e6:.3f}s, vol={CRUMPLED_VOLUME}")

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bkp = os.path.join(DRAFT_DIR, f"draft_content.json.paper-bag-{ts}")
    shutil.copy2(DRAFT, bkp)
    json.dump(d, open(DRAFT, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    for nm in ("template-2.tmp", "draft_content.json.bak"):
        try:
            shutil.copy2(DRAFT, os.path.join(DRAFT_DIR, nm))
        except Exception:
            pass
    print(f"Бэкап: {os.path.basename(bkp)}")


if __name__ == "__main__":
    main()
