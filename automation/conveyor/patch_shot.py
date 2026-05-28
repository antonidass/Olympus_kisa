"""
Точечный патч одного (или нескольких) видеошотов в уже собранном CapCut-проекте.

Зачем: после шага 1 пользователь открывает CapCut, видит что конкретную
сцену надо начать с другой секунды или замедлить — и хочет применить
правку ТОЛЬКО к ней, не пересобирая весь проект (иначе слетят переходы,
стикеры, караоке, добавленные руками).

Как это работает без разъезжания таймлайна:
  • target_timerange сегмента (позиция + длительность на таймлайне) НЕ
    трогается — голос, караоке, музыка, переходы остаются на местах.
  • Меняются только source_timerange (какой кусок исходника показывать) и
    speed (с какой скоростью). Длительность на таймлайне = const, поэтому
    соседние клипы не сдвигаются.

Источник правок — content/<миф>/montage/plan.json (тот же, что у шага 1).
Скрипт читает оттуда start_from / speed_override для запрошенных шотов.

CLI:
    python automation/conveyor/patch_shot.py --scenario "Аполлон и Кассандра" --shot scene_07_v1
    python automation/conveyor/patch_shot.py --scenario "..." --shot scene_07_v1 --shot scene_12_v1
    python automation/conveyor/patch_shot.py --scenario "..." --all   # все шоты из plan.json
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from shared import (  # noqa: E402
    CONTENT_DIR, US, load_plan, get_scene_override, plan_scene_key, VIDEO_EXTS,
    autodetect_drafts_folder, detect_capcut_versions, fix_project_versions,
)
import capcut_control  # noqa: E402


def check_capcut_closed() -> bool:
    try:
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
        text = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        if "CapCut.exe" in text or "JianyingPro" in text:
            return False
    except Exception:
        pass
    return True


def compute_source_and_speed(
    src_total_us: int, target_dur_us: int, start_from_s: float, speed_override: float | None
) -> tuple[int, int, float]:
    """(start_from_us, source_dur_us, speed) — та же логика, что в build_skeleton.

    target_dur_us берётся из ТЕКУЩЕГО сегмента (а не из голоса), чтобы патч
    уважал ручные правки длины, сделанные в CapCut.
    """
    start_from_us = int(start_from_s * US)
    start_from_us = max(0, min(start_from_us, max(0, src_total_us - 1)))
    avail_us = max(1, src_total_us - start_from_us)

    if speed_override is not None:
        source_dur_us = int(target_dur_us * speed_override)
        source_dur_us = max(1, min(source_dur_us, avail_us))
        speed = source_dur_us / target_dur_us
    else:
        if avail_us >= target_dur_us:
            source_dur_us = target_dur_us
            speed = 1.0
        else:
            source_dur_us = avail_us
            speed = avail_us / target_dur_us
    return start_from_us, source_dur_us, speed


def _material_scene_base(mat: dict) -> str:
    """scene_07 из material_name (scene_07_v2.mp4 → scene_07)."""
    name = mat.get("material_name") or Path(mat.get("path", "")).name
    return plan_scene_key(Path(name).stem)


def find_video_material_by_scene(draft: dict, scene_key: str) -> dict | None:
    """Ищет video material по БАЗЕ сцены (scene_07 — любая версия v1/v2/...)."""
    for mat in draft.get("materials", {}).get("videos", []):
        if _material_scene_base(mat) == scene_key:
            return mat
    return None


def find_segment_for_material(draft: dict, material_id: str) -> tuple[dict, dict] | tuple[None, None]:
    """Возвращает (track, segment) видеосегмента с данным material_id в треке main."""
    for track in draft.get("tracks", []):
        if track.get("type") != "video":
            continue
        for seg in track.get("segments", []):
            if seg.get("material_id") == material_id:
                return track, seg
    return None, None


def _make_video_material(video_dir: Path, scene_key: str, variant: str) -> dict | None:
    """Создаёт video-material для scene_NN_{variant} через pycapcut.

    Возвращает export_json материала (с id/duration/path) или None если файла нет.
    """
    for ext in VIDEO_EXTS:
        fp = video_dir / f"{scene_key}_{variant}{ext}"
        if fp.exists():
            try:
                import pycapcut as cc  # type: ignore
            except ImportError:
                return None
            return cc.VideoMaterial(str(fp)).export_json()
    return None


def patch_one_shot(draft: dict, scene_key: str, start_from_s: float,
                   speed_override: float | None, variant: str | None,
                   video_dir: Path) -> str:
    """Патчит один сегмент сцены. Возвращает строку-лог.

    Если `variant` задан и отличается от текущего материала — подменяет
    материал на новую версию (другой файл, другая длительность).
    """
    mat = find_video_material_by_scene(draft, scene_key)
    if mat is None:
        return f"  ⚠ {scene_key}: не нашёл video material в драфте — пропуск"
    _, seg = find_segment_for_material(draft, mat["id"])
    if seg is None:
        return f"  ⚠ {scene_key}: material есть, но сегмент на таймлайне не найден — пропуск"

    cur_name = mat.get("material_name") or Path(mat.get("path", "")).name
    cur_variant_m = re.search(r"_(v\d+)$", Path(cur_name).stem)
    cur_variant = cur_variant_m.group(1) if cur_variant_m else None
    variant_note = ""

    # Смена версии: создаём новый материал и подменяем material_id сегмента.
    if variant and variant != cur_variant:
        new_mat = _make_video_material(video_dir, scene_key, variant)
        if new_mat is None:
            return f"  ⚠ {scene_key}: версия {variant} не найдена в video/ — пропуск"
        draft["materials"].setdefault("videos", []).append(new_mat)
        seg["material_id"] = new_mat["id"]
        mat = new_mat
        variant_note = f"  [версия {cur_variant or '?'}→{variant}]"

    src_total_us = int(mat.get("duration", 0))
    target_dur_us = int(seg["target_timerange"]["duration"])
    start_from_us, source_dur_us, speed = compute_source_and_speed(
        src_total_us, target_dur_us, start_from_s, speed_override
    )

    # 1. source_timerange — какой кусок исходника показывать
    seg["source_timerange"] = {"start": start_from_us, "duration": source_dur_us}
    # 2. speed-поле сегмента
    seg["speed"] = speed
    # 3. speed-материал (extra_material_refs[0] обычно ссылается на него)
    speed_ids = {
        s["id"] for s in draft["materials"].get("speeds", [])
        if isinstance(s, dict)
    }
    updated_speed_mat = False
    for ref in seg.get("extra_material_refs", []):
        if ref in speed_ids:
            for s in draft["materials"]["speeds"]:
                if s.get("id") == ref:
                    s["speed"] = speed
                    updated_speed_mat = True
                    break
    if not updated_speed_mat:
        # Speed-материала нет в refs — создаём новый и подвязываем.
        import uuid
        new_id = uuid.uuid4().hex
        draft["materials"].setdefault("speeds", []).append({
            "curve_speed": None, "id": new_id, "mode": 0,
            "speed": speed, "type": "speed",
        })
        seg.setdefault("extra_material_refs", []).insert(0, new_id)

    mode = f"speed={speed:.3f}× (manual)" if speed_override is not None else (
        "обрезка 1.00×" if abs(speed - 1.0) < 1e-3 else f"замедление {speed:.3f}× (auto)"
    )
    return (f"  ✎ {scene_key:<12} start={start_from_s:.2f}s  "
            f"source={source_dur_us/US:.2f}s / target={target_dur_us/US:.2f}s  {mode}{variant_note}")


def main() -> int:
    p = argparse.ArgumentParser(description="Точечный патч видеошота в собранном CapCut-проекте.")
    p.add_argument("--scenario", required=True)
    p.add_argument("--shot", action="append", default=[],
                   help="shot_key (scene_07_v1). Можно указать несколько раз.")
    p.add_argument("--all", action="store_true", help="Патчить все шоты из plan.json.")
    p.add_argument("--drafts", help="Папка CapCut drafts (по умолчанию из conveyor_state.json).")
    p.add_argument("--no-capcut-manage", action="store_true",
                   help="Не управлять CapCut автоматически (не закрывать/перезапускать).")
    args = p.parse_args()

    scenario = args.scenario
    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.is_dir():
        print(f"Нет папки сценария: {scenario_dir}", file=sys.stderr)
        return 1

    # Где лежит собранный AUTO-драфт — берём из conveyor_state.json.
    state_file = scenario_dir / "montage" / "conveyor_state.json"
    if not state_file.is_file():
        print("Нет conveyor_state.json — сначала собери шаг 1.", file=sys.stderr)
        return 1
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception as ex:
        print(f"Не читается conveyor_state.json: {ex}", file=sys.stderr)
        return 1
    draft_dir_str = (state.get("step_1") or {}).get("draft_dir")
    if not draft_dir_str:
        print("В conveyor_state.json нет step_1.draft_dir.", file=sys.stderr)
        return 1
    draft_dir = Path(draft_dir_str)
    draft_file = draft_dir / "draft_content.json"
    if not draft_file.is_file():
        print(f"Не нашёл драфт: {draft_file}\nВозможно проект удалён из CapCut — пересобери шаг 1.",
              file=sys.stderr)
        return 1

    plan = load_plan(scenario)
    plan_shots = plan.get("shots") or {}
    video_dir = scenario_dir / "video"

    # Какие сцены патчим (ключи нормализуем к scene_NN).
    if args.all:
        targets = list(plan_shots.keys())
    else:
        targets = [plan_scene_key(s) for s in args.shot]
    if not targets:
        print("Не указаны сцены (--shot scene_NN ... или --all).", file=sys.stderr)
        return 1

    print(f"=== Точечный патч для «{scenario}» ===")
    print(f"Драфт: {draft_dir}")
    print(f"Сцен к патчу: {len(targets)} ({', '.join(targets)})")
    print()

    # Авто-управление CapCut: если проект открыт в редакторе — сохраняем
    # ручные правки (Ctrl+S) и закрываем приложение; после патча — перезапуск.
    guard = capcut_control.WriteGuard(auto=not args.no_capcut_manage)
    guard.__enter__()
    try:
        # Перечитываем драфт ВНУТРИ guard: если CapCut только что сохранил
        # проект (Ctrl+S перед закрытием), берём его свежее состояние.
        draft = json.load(open(draft_file, encoding="utf-8"))

        logs = []
        patched = 0
        for scene_key in targets:
            start_from, speed_override, variant = get_scene_override(plan, scene_key)
            line = patch_one_shot(draft, scene_key, start_from, speed_override, variant, video_dir)
            logs.append(line)
            if line.strip().startswith("✎"):
                patched += 1

        for line in logs:
            print(line)

        if patched == 0:
            print("\nНи одного шота не пропатчено — драфт не трогаю.", file=sys.stderr)
            return 1

        # Бэкап + сохранение + фикс версий + синхронизация CapCut-кэшей
        bkp = draft_file.with_suffix(".json.patch-backup")
        shutil.copy2(draft_file, bkp)
        json.dump(draft, open(draft_file, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))

        drafts_folder = autodetect_drafts_folder() or draft_dir.parent
        content_ver, last_app, meta_ver = detect_capcut_versions(drafts_folder, exclude=draft_dir.name)
        fix_project_versions(draft_dir, content_ver, last_app, meta_ver)

        for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
            tgt = draft_dir / tgt_name
            try:
                shutil.copy2(draft_file, tgt)
            except Exception:
                pass

        print()
        print(f"OK Пропатчено шотов: {patched}/{len(targets)}.")
        print(f"  Бэкап: {bkp.name}")
        print("  target-длительности не менялись — переходы/караоке/стикеры на месте.")
        return 0
    finally:
        guard.__exit__(None, None, None)


if __name__ == "__main__":
    sys.exit(main())
