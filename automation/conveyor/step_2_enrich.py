"""
Шаг 2 конвейера — «Переходы и звуки».

Раскладывает CapCut-переходы между сценами и канон-SFX (WHOOSH.mp3 /
crumpled_paper.mp3) в уже собранный драфт `AUTO <миф>`. План берётся из
content/<миф>/montage/transition_plan.json (его пишет редактор переходов
в webapp). Логика раскладки — в transitions.py (общая с webapp).

Поведение с CapCut — как у шага 1 (через capcut_control.WriteGuard):
  • CapCut закрыт / в галерее → пишем переходы в файл напрямую;
  • CapCut открыт в редакторе → Ctrl+S, закрываем приложение, пишем,
    затем перезапускаем CapCut и двойным кликом открываем первую плитку
    галереи (наш свежепропатченный проект — самый верхний).

Ручные онлайн-SFX (Swoosh/Swish на зум-семействе) НЕ трогаются — мы
управляем только локальными WHOOSH/crumpled.

CLI:
    python automation/conveyor/step_2_enrich.py --scenario "Аполлон и Кассандра"
    python automation/conveyor/step_2_enrich.py --scenario "..." --plan-file path.json
    python automation/conveyor/step_2_enrich.py --scenario "..." --dry-run
    python automation/conveyor/step_2_enrich.py --scenario "..." --no-capcut-manage
"""

from __future__ import annotations

import argparse
import io
import json
import shutil
import sys
import time
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
    CONTENT_DIR,
    autodetect_drafts_folder, detect_capcut_versions, fix_project_versions,
)
import capcut_control  # noqa: E402
import transitions as tio  # noqa: E402


def resolve_draft_dir(scenario_dir: Path) -> Path | None:
    """Папка собранного AUTO-драфта из conveyor_state.json (step_1.draft_dir)."""
    state_file = scenario_dir / "montage" / "conveyor_state.json"
    if not state_file.is_file():
        return None
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return None
    draft_dir_str = (state.get("step_1") or {}).get("draft_dir")
    if not draft_dir_str:
        return None
    d = Path(draft_dir_str)
    return d if (d / "draft_content.json").is_file() else None


def load_transition_plan(plan_file: Path) -> list[dict]:
    """Читает план переходов: [{index, effect_id|None, duration?}]."""
    if not plan_file.is_file():
        return []
    try:
        data = json.loads(plan_file.read_text(encoding="utf-8"))
    except Exception:
        return []
    items = data.get("transitions") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    plan: list[dict] = []
    for e in items:
        if not isinstance(e, dict):
            continue
        try:
            idx = int(e.get("index"))
        except (TypeError, ValueError):
            continue
        eid = e.get("effect_id")
        eid = None if eid in (None, "", "cut") else str(eid)
        dur = e.get("duration")
        try:
            dur = float(dur) if dur not in (None, "") else None
        except (TypeError, ValueError):
            dur = None
        plan.append({"index": idx, "effect_id": eid, "duration": dur})
    return plan


def touch_draft_modified(draft_dir: Path) -> None:
    """Ставит tm_draft_modified = сейчас в draft_meta_info.json.

    CapCut сортирует галерею по этому полю. Шаг 2 правит только
    draft_content.json, поэтому без обновления tm_draft_modified наш проект
    остаётся со старой меткой шага 1 и в галерее НЕ первый — авто-открытие
    (двойной клик по первой плитке) попадёт в чужой проект. Бамп метки
    гарантирует, что наш свежепропатченный проект — самый верхний.
    """
    dm_path = draft_dir / "draft_meta_info.json"
    if not dm_path.is_file():
        return
    try:
        dm = json.loads(dm_path.read_text(encoding="utf-8"))
        now_us = int(time.time() * 1_000_000)
        dm["tm_draft_modified"] = now_us
        dm_path.write_text(json.dumps(dm, ensure_ascii=False, separators=(",", ":")),
                           encoding="utf-8")
    except Exception:
        pass


def bump_conveyor_state(scenario_dir: Path, draft_dir: Path, n_tr: int) -> Path:
    """Поднимает step до 2 и пишет step_2-инфу в conveyor_state.json."""
    state_dir = scenario_dir / "montage"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "conveyor_state.json"
    try:
        existing = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}
    except Exception:
        existing = {}
    existing.update({
        "step": max(int(existing.get("step", 0)), 2),
        "step_2": {"draft_dir": str(draft_dir), "transitions": n_tr},
    })
    state_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    return state_file


def main() -> int:
    p = argparse.ArgumentParser(description="Шаг 2 конвейера — переходы и SFX.")
    p.add_argument("--scenario", required=True)
    p.add_argument("--plan-file", help="JSON-план переходов (по умолчанию montage/transition_plan.json).")
    p.add_argument("--no-capcut-manage", action="store_true",
                   help="Не закрывать/перезапускать CapCut автоматически.")
    p.add_argument("--dry-run", action="store_true", help="Показать план, ничего не писать.")
    args = p.parse_args()

    scenario = args.scenario
    scenario_dir = CONTENT_DIR / scenario
    if not scenario_dir.is_dir():
        print(f"Нет папки сценария: {scenario_dir}", file=sys.stderr)
        return 1

    draft_dir = resolve_draft_dir(scenario_dir)
    if draft_dir is None:
        print("Нет собранного драфта (conveyor_state.json / step_1.draft_dir). "
              "Сначала запусти шаг 1.", file=sys.stderr)
        return 1
    draft_file = draft_dir / "draft_content.json"

    plan_file = Path(args.plan_file) if args.plan_file else (
        scenario_dir / "montage" / "transition_plan.json")
    plan = load_transition_plan(plan_file)

    print(f"=== Шаг 2 (переходы) для «{scenario}» ===")
    print(f"Драфт:     {draft_dir}")
    print(f"План:      {plan_file}")
    picked = sum(1 for e in plan if e.get("effect_id"))
    print(f"Стыков в плане: {len(plan)} ({picked} переходов, {len(plan) - picked} cut)")

    if not plan:
        print("План пуст — нечего раскладывать.", file=sys.stderr)
        return 1

    if args.dry_run:
        for e in plan:
            eid = e.get("effect_id")
            cat = tio.CATALOG_BY_ID.get(eid) if eid else None
            label = cat["name"] if cat else ("Cut" if not eid else f"?{eid}")
            print(f"  стык {e['index'] + 1:02d}: {label}")
        print("\n--dry-run: драфт не трогаю.")
        return 0

    # Авто-управление CapCut: открыт в редакторе → Ctrl+S + закрыть; после
    # записи — перезапуск и двойной клик по первой плитке галереи.
    guard = capcut_control.WriteGuard(auto=not args.no_capcut_manage)
    guard.__enter__()
    try:
        # Перечитываем драфт внутри guard — вдруг CapCut только что сохранил
        # ручные правки перед закрытием.
        draft = json.load(open(draft_file, encoding="utf-8"))

        library = tio.build_template_library()
        print()
        print("Раскладка переходов и SFX:")
        for line in tio.apply_transition_plan(draft, plan, library):
            print(line)

        bkp = draft_file.with_suffix(".json.step2-backup")
        shutil.copy2(draft_file, bkp)
        json.dump(draft, open(draft_file, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))

        # Чиним версию проекта (как шаг 1 / patch_shot), иначе CapCut попросит
        # обновление при открытии.
        drafts_folder = autodetect_drafts_folder() or draft_dir.parent
        content_ver, last_app, meta_ver = detect_capcut_versions(drafts_folder, exclude=draft_dir.name)
        fix_project_versions(draft_dir, content_ver, last_app, meta_ver)
        # Свежая метка модификации → наш проект первый в галерее CapCut,
        # чтобы авто-открытие (двойной клик по первой плитке) попало в него.
        touch_draft_modified(draft_dir)

        for tgt_name in ("template-2.tmp", "draft_content.json.bak"):
            tgt = draft_dir / tgt_name
            try:
                shutil.copy2(draft_file, tgt)
            except Exception:
                pass

        n_tr = len(tio.read_transitions(draft))
        n_picked = sum(1 for r in tio.read_transitions(draft) if r["effect_id"])
        state_file = bump_conveyor_state(scenario_dir, draft_dir, n_picked)

        print()
        print(f"OK Шаг 2 завершён. Переходов: {n_picked}/{n_tr} стыков.")
        print(f"  Бэкап: {bkp.name}")
        print(f"  State: {state_file}")
        return 0
    finally:
        guard.__exit__(None, None, None)


if __name__ == "__main__":
    sys.exit(main())
