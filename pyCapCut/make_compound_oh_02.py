"""
make_compound_oh_02.py - оборачивает всё содержимое CapCut-проекта
'От Хаоса до Олимпа Ч.02 Власть Кроноса' в один Сборный клип (Compound Clip).

Делает то же, что в UI CapCut: Ctrl+A на таймлайне → ПКМ → 'Сборный клип',
только через прямую правку JSON-ов draft_content. CapCut должен быть закрыт,
иначе на следующем сохранении приложение перезапишет наши изменения.

Как это работает:
  - В CapCut сборный клип = одна запись в materials.drafts с type='combination',
    inline-копия исходного драфта внутри неё (ключ 'draft'), и единственный
    video-сегмент на главной дорожке, ссылающийся на этот combination через
    материал-видео + 7 вспомогательных материалов (canvas, speed, sound mapping
    и т.п.).
  - Скрипт берёт уже собранный руками сборный клип из проекта-шаблона
    'От Хаоса до Олимпа Ч.02 Власть Кроноса-копия' как референс правильной
    структуры и подставляет в него содержимое целевого проекта.

Использование:
    python make_compound_oh_02.py                          # выполнить
    python make_compound_oh_02.py --dry-run                # проверить, без записи
    python make_compound_oh_02.py --name 'Сборный клип v2' # имя сборного клипа
    python make_compound_oh_02.py --project "PATH"         # другой главный проект
    python make_compound_oh_02.py --template "PATH"        # другой шаблон

Безопасность:
  - draft_content.json перед перезаписью копируется в .compound-backup
  - чтобы откатить: переименовать .compound-backup → draft_content.json,
    а свежесозданную папку subdraft/<UUID>/ - удалить.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Tuple

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except (AttributeError, OSError):
    pass


# ─────────────────────────────────────────────────────────────────────
# Дефолты
# ─────────────────────────────────────────────────────────────────────

DEFAULT_DRAFTS_ROOT = (
    Path.home()
    / "AppData"
    / "Local"
    / "CapCut"
    / "User Data"
    / "Projects"
    / "com.lveditor.draft"
)

DEFAULT_PROJECT_NAME = "От Хаоса до Олимпа Ч.02 Власть Кроноса"
DEFAULT_TEMPLATE_NAME = "От Хаоса до Олимпа Ч.02 Власть Кроноса-копия"
DEFAULT_COMPOUND_NAME = "Сборный клип1"


# ─────────────────────────────────────────────────────────────────────
# Утилиты
# ─────────────────────────────────────────────────────────────────────

def gen_uuid() -> str:
    """UUID4 в верхнем регистре - так выглядят id у CapCut на Windows."""
    return str(uuid.uuid4()).upper()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


# ─────────────────────────────────────────────────────────────────────
# Поиск placeholder-токена ##_draftpath_placeholder_<UUID>_##
# в шаблоне - его нужно сохранить, CapCut на нём резолвит пути проекта.
# ─────────────────────────────────────────────────────────────────────

def extract_placeholder_token(tpl_video_path: str) -> str:
    """
    Возвращает '##_draftpath_placeholder_<UUID>_##' - префикс, по которому
    CapCut определяет корень текущего проекта.
    """
    marker = "##_draftpath_placeholder_"
    idx = tpl_video_path.find(marker)
    if idx == -1:
        raise ValueError(f"В шаблоне нет placeholder-токена: {tpl_video_path}")
    end = tpl_video_path.find("_##", idx) + len("_##")
    return tpl_video_path[idx:end]


def extract_template_subdraft_id(tpl_draft_file_path: str) -> str:
    """
    Извлекает UUID-имя папки subdraft/<UUID>/ из пути в шаблоне -
    нужно, чтобы потом подменить его на наш свежий.
    """
    parts = tpl_draft_file_path.replace("\\", "/").split("/")
    for i, part in enumerate(parts):
        if part == "subdraft" and i + 1 < len(parts):
            return parts[i + 1]
    raise ValueError(f"Не нашёл UUID подпапки subdraft в: {tpl_draft_file_path}")


# ─────────────────────────────────────────────────────────────────────
# Главное преобразование
# ─────────────────────────────────────────────────────────────────────

def build_compound(
    source_draft: dict,
    template_draft: dict,
    compound_name: str,
) -> Tuple[dict, str, str]:
    """
    Возвращает (new_main_draft, subdraft_folder_id, combination_id).

    new_main_draft - что писать в основной draft_content.json целевого проекта.
    subdraft_folder_id - имя папки subdraft/<UUID>/, которую нужно создать.
    combination_id - UUID комбинации (используется и в имени preview-MP4).
    """
    # ───────────── базовый каркас - копия главного драфта шаблона ─
    new_main = copy.deepcopy(template_draft)

    # Сохраняем метаданные ИСХОДНОГО проекта поверх шаблонных:
    for k in (
        "id", "name", "create_time", "fps", "canvas_config",
        "is_drop_frame_timecode", "color_space", "version", "new_version",
        "platform", "last_modified_platform", "mutable_config",
        "cover", "retouch_cover", "extra_info", "static_cover_image_path",
        "path",
    ):
        if k in source_draft:
            new_main[k] = copy.deepcopy(source_draft[k])

    duration_us = int(source_draft["duration"])
    width = int(source_draft["canvas_config"]["width"])
    height = int(source_draft["canvas_config"]["height"])

    new_main["duration"] = duration_us
    new_main["update_time"] = source_draft.get("update_time", 0)
    new_main["source"] = "default"

    # ───────────── inner draft (всё нынешнее содержимое таймлайна) ─
    inner = copy.deepcopy(source_draft)
    template_inner = template_draft["materials"]["drafts"][0]["draft"]
    # CapCut на уровне inner-драфта держит несколько доп. ключей -
    # подтягиваем дефолты из шаблона, если в исходнике их нет.
    for k in (
        "draft_type", "lyrics_effects", "uneven_animation_template_info",
        "smart_ads_info", "function_assistant_info",
    ):
        if k not in inner and k in template_inner:
            inner[k] = copy.deepcopy(template_inner[k])

    inner_draft_id = gen_uuid()
    inner["id"] = inner_draft_id
    inner["name"] = compound_name
    inner["source"] = "default"
    inner["duration"] = duration_us

    # ───────────── свежие UUID для всех материалов ─────────────────
    new_video_id = gen_uuid()
    new_combination_mat_id = gen_uuid()
    new_canvas_id = gen_uuid()
    new_placeholder_info_id = gen_uuid()
    new_speed_id = gen_uuid()
    new_sound_id = gen_uuid()
    new_color_id = gen_uuid()
    new_vocal_id = gen_uuid()
    new_segment_id = gen_uuid()
    new_track_id = gen_uuid()

    subdraft_folder_id = gen_uuid()
    combination_id = gen_uuid()

    tpl_mats = template_draft["materials"]

    # id_map для подмены extra_material_refs на сегменте
    id_map = {
        tpl_mats["videos"][0]["id"]:                  new_video_id,
        tpl_mats["drafts"][0]["id"]:                  new_combination_mat_id,
        tpl_mats["canvases"][0]["id"]:                new_canvas_id,
        tpl_mats["placeholder_infos"][0]["id"]:       new_placeholder_info_id,
        tpl_mats["speeds"][0]["id"]:                  new_speed_id,
        tpl_mats["sound_channel_mappings"][0]["id"]:  new_sound_id,
        tpl_mats["material_colors"][0]["id"]:         new_color_id,
        tpl_mats["vocal_separations"][0]["id"]:       new_vocal_id,
    }

    # ───────────── 8 материалов для главной дорожки ────────────────
    # 1) drafts[0] - сам combination
    combo_mat = copy.deepcopy(tpl_mats["drafts"][0])
    combo_mat["id"] = new_combination_mat_id
    combo_mat["combination_id"] = combination_id
    combo_mat["draft"] = inner

    placeholder_token = extract_placeholder_token(tpl_mats["videos"][0]["path"])
    tpl_sub_id = extract_template_subdraft_id(tpl_mats["drafts"][0]["draft_file_path"])
    # переподшиваем пути на свежий subdraft_folder_id
    combo_mat["draft_file_path"] = tpl_mats["drafts"][0]["draft_file_path"].replace(
        tpl_sub_id, subdraft_folder_id
    )
    combo_mat["draft_cover_path"] = tpl_mats["drafts"][0]["draft_cover_path"].replace(
        tpl_sub_id, subdraft_folder_id
    )
    combo_mat["draft_config_path"] = tpl_mats["drafts"][0]["draft_config_path"].replace(
        tpl_sub_id, subdraft_folder_id
    )

    # 2) videos[0] - материал-обёртка вокруг combination
    video_mat = copy.deepcopy(tpl_mats["videos"][0])
    video_mat["id"] = new_video_id
    video_mat["duration"] = duration_us
    video_mat["width"] = width
    video_mat["height"] = height
    video_mat["material_name"] = compound_name
    tpl_combo_id = tpl_mats["drafts"][0]["combination_id"]
    video_mat["path"] = tpl_mats["videos"][0]["path"].replace(tpl_combo_id, combination_id)

    # 3-8) служебные материалы - те же дефолты, новые id
    canvas_mat   = copy.deepcopy(tpl_mats["canvases"][0]);              canvas_mat["id"]   = new_canvas_id
    ph_mat       = copy.deepcopy(tpl_mats["placeholder_infos"][0]);     ph_mat["id"]       = new_placeholder_info_id
    speed_mat    = copy.deepcopy(tpl_mats["speeds"][0]);                speed_mat["id"]    = new_speed_id
    sound_mat    = copy.deepcopy(tpl_mats["sound_channel_mappings"][0]);sound_mat["id"]    = new_sound_id
    color_mat    = copy.deepcopy(tpl_mats["material_colors"][0]);       color_mat["id"]    = new_color_id
    vocal_mat    = copy.deepcopy(tpl_mats["vocal_separations"][0]);     vocal_mat["id"]    = new_vocal_id

    # ───────────── materials главного драфта ───────────────────────
    # Берём структуру категорий из шаблона (она уже "ужата" до 8 нужных),
    # а потом подсовываем наши свежие материалы.
    new_main["materials"] = copy.deepcopy(tpl_mats)
    new_main["materials"]["drafts"]                 = [combo_mat]
    new_main["materials"]["videos"]                 = [video_mat]
    new_main["materials"]["canvases"]               = [canvas_mat]
    new_main["materials"]["placeholder_infos"]      = [ph_mat]
    new_main["materials"]["speeds"]                 = [speed_mat]
    new_main["materials"]["sound_channel_mappings"] = [sound_mat]
    new_main["materials"]["material_colors"]        = [color_mat]
    new_main["materials"]["vocal_separations"]      = [vocal_mat]

    # ───────────── tracks: один video-сегмент ──────────────────────
    new_track = copy.deepcopy(template_draft["tracks"][0])
    new_track["id"] = new_track_id
    seg = copy.deepcopy(new_track["segments"][0])
    seg["id"] = new_segment_id
    seg["material_id"] = new_video_id
    seg["source_timerange"] = {"start": 0, "duration": duration_us}
    seg["target_timerange"] = {"start": 0, "duration": duration_us}
    seg["extra_material_refs"] = [id_map.get(r, r) for r in seg.get("extra_material_refs", [])]
    new_track["segments"] = [seg]
    new_main["tracks"] = [new_track]

    # ───────────── чистим вспомогательные коллекции ────────────────
    new_main["group_container"]   = None
    new_main["keyframes"]         = {
        "adjusts": [], "audios": [], "effects": [], "filters": [],
        "handwrites": [], "stickers": [], "texts": [], "videos": [],
    }
    new_main["keyframe_graph_list"] = []
    new_main["relationships"]       = []
    new_main["time_marks"]          = []

    return new_main, subdraft_folder_id, combination_id


# ─────────────────────────────────────────────────────────────────────
# Скелет standalone subdraft/<UUID>/draft_content.json
# (CapCut использует его, только если пользователь дабл-кликает по compound)
# ─────────────────────────────────────────────────────────────────────

def build_subdraft_skeleton(template_skeleton: dict) -> dict:
    sk = copy.deepcopy(template_skeleton)
    sk["id"] = gen_uuid()
    return sk


def build_sub_draft_config(
    folder_id: str,
    compound_name: str,
    duration_us: int,
    width: int,
    height: int,
    create_time_s: int,
) -> dict:
    return {
        "audio_path": "",
        "cover_height": height,
        "cover_path": "draft_cover.jpg",
        "cover_width": width,
        "create_time": create_time_s,
        "draft_json_file": "draft_content.json",
        "id": folder_id,
        "import_time_ms": create_time_s * 1000,
        "is_from_multi_timeline": False,
        "is_from_sub_draft": True,
        "name": compound_name,
        "project_id": folder_id,
        "rough_cut_duration": duration_us,
        "rough_cut_start": 0,
        "source": "timeline",
        "type": "video",
    }


# ─────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drafts", type=Path, default=DEFAULT_DRAFTS_ROOT,
                        help="Папка com.lveditor.draft с проектами CapCut")
    parser.add_argument("--project", default=DEFAULT_PROJECT_NAME,
                        help="Имя проекта, который нужно свернуть в сборный клип")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE_NAME,
                        help="Имя проекта-шаблона, где уже сделан сборный клип "
                             "(нужен для копирования структуры материалов)")
    parser.add_argument("--name", default=DEFAULT_COMPOUND_NAME,
                        help="Имя сборного клипа в UI CapCut")
    parser.add_argument("--dry-run", action="store_true",
                        help="Только напечатать план, ничего не писать")
    args = parser.parse_args()

    project_dir = args.drafts / args.project
    template_dir = args.drafts / args.template

    if not project_dir.is_dir():
        print(f"[ОШИБКА] Не найден проект: {project_dir}", file=sys.stderr)
        return 2
    if not template_dir.is_dir():
        print(f"[ОШИБКА] Не найден шаблон: {template_dir}", file=sys.stderr)
        return 2

    src_draft_path = project_dir / "draft_content.json"
    tpl_draft_path = template_dir / "draft_content.json"
    if not src_draft_path.exists():
        print(f"[ОШИБКА] Нет {src_draft_path}", file=sys.stderr)
        return 2
    if not tpl_draft_path.exists():
        print(f"[ОШИБКА] Нет {tpl_draft_path}", file=sys.stderr)
        return 2

    src_draft = load_json(src_draft_path)
    tpl_draft = load_json(tpl_draft_path)

    if not tpl_draft.get("materials", {}).get("drafts"):
        print(
            f"[ОШИБКА] В шаблоне '{args.template}' нет materials.drafts - "
            f"значит, там нет готового сборного клипа. Сначала сделай его в "
            f"CapCut руками: открой проект, Ctrl+A, ПКМ → Сборный клип.",
            file=sys.stderr,
        )
        return 2

    print(f"[i] Проект:  {project_dir}")
    print(f"[i] Шаблон:  {template_dir}")
    print(f"[i] Длина:   {src_draft['duration']/1_000_000:.2f} с")
    print(f"[i] Канва:   {src_draft['canvas_config']['width']}×{src_draft['canvas_config']['height']}")
    print(f"[i] Треков:  {len(src_draft.get('tracks', []))}")
    for i, t in enumerate(src_draft.get("tracks", [])):
        print(f"    └ #{i}: type={t.get('type'):<6} segments={len(t.get('segments', []))}")

    new_main, subdraft_folder_id, combination_id = build_compound(
        source_draft=src_draft,
        template_draft=tpl_draft,
        compound_name=args.name,
    )

    # Готовим скелет standalone-файла подпроекта из шаблона
    tpl_sub_id = extract_template_subdraft_id(
        tpl_draft["materials"]["drafts"][0]["draft_file_path"]
    )
    tpl_skeleton_path = template_dir / "subdraft" / tpl_sub_id / "draft_content.json"
    sub_skeleton = build_subdraft_skeleton(load_json(tpl_skeleton_path))

    width  = int(src_draft["canvas_config"]["width"])
    height = int(src_draft["canvas_config"]["height"])
    duration_us = int(src_draft["duration"])
    sub_config = build_sub_draft_config(
        folder_id=subdraft_folder_id,
        compound_name=args.name,
        duration_us=duration_us,
        width=width,
        height=height,
        create_time_s=int(src_draft.get("create_time") or 0) // 1_000_000 or
                      int(__import__("time").time()),
    )

    print()
    print(f"[+] Сборный клип:    {args.name}")
    print(f"[+] subdraft/<id>:   {subdraft_folder_id}")
    print(f"[+] combination_id:  {combination_id}")
    print(f"[+] inner draft id:  {new_main['materials']['drafts'][0]['draft']['id']}")
    print(f"[+] segments итог:   1 (был {sum(len(t.get('segments',[])) for t in src_draft.get('tracks',[]))})")
    print(f"[+] tracks итог:     1 (был {len(src_draft.get('tracks', []))})")

    if args.dry_run:
        print("\n[dry-run] Ничего не записал. Снимите --dry-run, чтобы применить.")
        return 0

    # Бэкап главного draft_content.json
    backup_path = project_dir / "draft_content.json.compound-backup"
    if not backup_path.exists():
        shutil.copy2(src_draft_path, backup_path)
        print(f"[бэкап] {backup_path.name}")
    else:
        print(f"[бэкап] уже есть, не перезаписываю: {backup_path.name}")

    # Перезаписываем главный draft_content.json
    save_json(src_draft_path, new_main)
    print(f"[write] {src_draft_path.name}")

    # Создаём папку subdraft/<UUID>/
    sub_dir = project_dir / "subdraft" / subdraft_folder_id
    sub_dir.mkdir(parents=True, exist_ok=True)
    save_json(sub_dir / "draft_content.json", sub_skeleton)
    save_json(sub_dir / "sub_draft_config.json", sub_config)
    print(f"[write] subdraft/{subdraft_folder_id}/draft_content.json")
    print(f"[write] subdraft/{subdraft_folder_id}/sub_draft_config.json")

    # Копируем обложку проекта в subdraft - чтобы превью сборного клипа было
    cover_src = project_dir / "draft_cover.jpg"
    if cover_src.exists():
        shutil.copy2(cover_src, sub_dir / "draft_cover.jpg")
        print(f"[copy ] draft_cover.jpg → subdraft/{subdraft_folder_id}/")

    print("\n[готово] Открой проект в CapCut и проверь таймлайн.")
    print("         Откат: переименуй .compound-backup → draft_content.json")
    print(f"         и удали subdraft/{subdraft_folder_id}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
