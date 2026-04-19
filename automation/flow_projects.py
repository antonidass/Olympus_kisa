"""
Общий резолвер Flow-проектов для imagefx_runner и video_runner.

Хранит маппинг «имя сценария → flow_id» в automation/flow_projects.json.
При первом запуске для нового сценария спрашивает flow_id у пользователя
и сохраняет его в JSON — повторно уже не спросит.

flow_id берётся из URL: labs.google/fx/.../flow/project/<flow_id>
"""

from __future__ import annotations

import json
import re
from pathlib import Path

FLOW_BASE_URL = "https://labs.google/fx/ru/tools/flow/project"
PROJECTS_JSON = Path(__file__).parent / "flow_projects.json"

# Имена папок, которые нужно «прокинуть» — это подпапки внутри сценария,
# а не сам сценарий. Например: content/икар_и_дедал/prompts/video.md.
_PASSTHROUGH_FOLDERS = {"prompts", "video", "images", "voiceover", "music", "final"}

_FLOW_ID_PATTERN = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def _scenario_key(markdown_path: Path) -> str:
    """Находит имя сценария по пути к markdown-файлу.

    Ищем первую папку-предка, имя которой НЕ входит в список служебных
    (prompts/video/images/…). Это и есть имя сценария.

    Возвращаем имя В ОРИГИНАЛЬНОМ РЕГИСТРЕ — папки сценариев теперь называются
    «Икар и Дедал», «Сизифов Труд» и т.п., и именно так они хранятся в
    flow_projects.json. Никакой нормализации.
    """
    for parent in markdown_path.resolve().parents:
        name = parent.name
        if not name:
            continue
        low = name.lower()
        if low in _PASSTHROUGH_FOLDERS:
            continue
        # content/automation/scripts — тоже не сценарии
        if low in {"content", "automation", "scripts", "output"}:
            break
        return name
    raise ValueError(f"Не удалось определить имя сценария из пути: {markdown_path}")


def _load() -> dict[str, str]:
    if not PROJECTS_JSON.exists():
        return {}
    try:
        return json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Повреждён {PROJECTS_JSON}: {e}") from e


def _save(projects: dict[str, str]) -> None:
    PROJECTS_JSON.write_text(
        json.dumps(projects, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _extract_flow_id(raw: str) -> str:
    """Принимает либо сам flow_id, либо полный URL — возвращает чистый id."""
    raw = raw.strip()
    match = _FLOW_ID_PATTERN.search(raw)
    if not match:
        raise ValueError(f"Не удалось извлечь flow_id из «{raw}». Ожидаю UUID.")
    return match.group(0)


def resolve_flow_url(markdown_path: Path) -> str:
    """Возвращает URL Flow-проекта для сценария.

    Если проект для сценария ещё не зарегистрирован — спрашивает у пользователя
    flow_id (или URL) и сохраняет маппинг в flow_projects.json.
    """
    key = _scenario_key(markdown_path)
    projects = _load()

    if key in projects:
        flow_id = projects[key]
        print(f"🔗 Flow-проект: {key} → {flow_id}")
        return f"{FLOW_BASE_URL}/{flow_id}"

    print(f"\n🆕 Новый сценарий: «{key}» — Flow-проект ещё не зарегистрирован.")
    print("   Открой labs.google/fx/tools/flow, создай новый проект и скопируй")
    print("   его URL (или только flow_id). Пример URL:")
    print(f"   {FLOW_BASE_URL}/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\n")

    while True:
        raw = input(f"   flow_id или URL для «{key}»: ").strip()
        if not raw:
            raise ValueError("flow_id не указан — невозможно продолжить")
        try:
            flow_id = _extract_flow_id(raw)
            break
        except ValueError as e:
            print(f"   ⚠ {e} Попробуй ещё раз.")

    projects[key] = flow_id
    _save(projects)
    print(f"   ✓ Сохранено в {PROJECTS_JSON.name}: {key} → {flow_id}\n")

    return f"{FLOW_BASE_URL}/{flow_id}"
