"""Раскатка папочной структуры и шаблонов промптов для нового сценария.

Один источник правды для двух потребителей:
  - webapp (`webapp/app.py`, эндпоинт `POST /api/scenarios/create`)
  - CLI    (`automation/create_scenario.py`, шаг 2 пайплайна)

Шаблоны соответствуют правилам канала, описанным в CONTEXT.md:
интро-карточка идёт ПОСЛЕ кликбейтного хука (hook=sentence_001,
title=sentence_002), уникальный subject-маркер в каждом промпте,
обязательный негатив в video.md.
"""

from __future__ import annotations

from pathlib import Path

# ── Структура папок сценария ───────────────────────────────────────────────
# Внутри каждой папки `content/<Название мифа>/` создаём этот набор подпапок.
SCENARIO_SUBDIRS: tuple[str, ...] = (
    "prompts",
    "voiceover/audio",
    "voiceover/texts",
    "images",
    "images/stickers",  # шаг 9: распакованные стикеры scene_NN_<маркер>.jpeg
    "video",
    "music",
    "final",
)


# ── Валидация имени ────────────────────────────────────────────────────────


def validate_scenario_name(name: str) -> tuple[bool, str]:
    """Имя папки нового сценария: непустое, без слешей, без `..`, ≤100 символов."""
    if not name or not name.strip():
        return False, "Имя не может быть пустым"
    name = name.strip()
    if any(ch in name for ch in ("/", "\\", "\0")):
        return False, "Имя не может содержать слеш"
    if name in (".", ".."):
        return False, "Недопустимое имя"
    if len(name) > 100:
        return False, "Имя слишком длинное (максимум 100 символов)"
    return True, ""


# ── Шаблоны промптов ───────────────────────────────────────────────────────


def voiceover_template(name: str) -> str:
    """Шаблон `prompts/voiceover.md`.

    Жёсткий порядок (с 2026-05-06):
      1. Кликбейтный хук (sentence_001) — 1–2 предложения, удерживают
         зрителя в первые 3 секунды. БЕЗ него ретеншн рассыпается на
         2-й секунде. Эталон — Персефона и Аид.
      2. Интро-титул «<Имя>. Миф за минуту.» (sentence_002) — звучит
         ПОСЛЕ хука. Озвучивается одним TTS-запросом.
      3. Основной текст истории (~150–200 слов).
    """
    return (
        f"# {name}\n"
        f"\n"
        f"<!-- ШАГ 1 — КЛИКБЕЙТНЫЙ ХУК (ОБЯЗАТЕЛЕН, sentence_001).\n"
        f"     Идёт ПЕРВЫМ, до титула. 1–2 предложения, которые удерживают\n"
        f"     зрителя в первые 3 секунды: интрига, вопрос, ошарашивающая\n"
        f"     ставка, конфликт сразу. Эталон — Персефона и Аид:\n"
        f"\n"
        f"       «Её украл владыка мёртвых — и мир впервые увидел зиму.»\n"
        f"\n"
        f"     Удалить эту инструкцию и заменить строку ниже на свой хук. -->\n"
        f"<КЛИКБЕЙТНЫЙ ХУК — заменить, 1–2 предложения, см. инструкцию выше>\n"
        f"\n"
        f"<!-- ШАГ 2 — ТИТУЛ-ИНТРО (sentence_002). Звучит ПОСЛЕ хука.\n"
        f"     Озвучивается одним TTS-запросом — два коротких предложения\n"
        f"     читаются как единая титульная фраза. -->\n"
        f"{name}. Миф за минуту.\n"
        f"\n"
        f"<!-- ШАГ 3 — ОСНОВНОЙ ТЕКСТ (~150–200 слов, 7–10 предложений).\n"
        f"     Правила: ударения только на именах собственных, без триггерных\n"
        f"     слов (убил→сразил, смерть→гибель), живой ритм без канцелярита.\n"
        f"     После готового текста разбить на предложения и положить\n"
        f"     каждое в voiceover/texts/sentence_NNN.txt\n"
        f"     (хук → sentence_001.txt, титул → sentence_002.txt, дальше +1). -->\n"
        f"<ОСНОВНОЙ ТЕКСТ — заменить>\n"
    )


def images_template(name: str) -> str:
    """Заготовка `prompts/images.md` с напоминанием про правила канала."""
    return (
        f"<!-- {name} — промпты для генерации картинок (Google Flow / ImageFX).\n"
        f"\n"
        f"     Маппинг sentence ↔ scene_NN заполнить здесь после написания\n"
        f"     основного текста и разбиения на предложения. Пример:\n"
        f"       sentence_001 (хук)   → scene_01 (1 шот, картинка-крючок)\n"
        f"       sentence_002 (титул) → scene_01 (тот же кадр + караоке-титул сверху)\n"
        f"       sentence_003         → scene_02 (1 шот)\n"
        f"       sentence_004         → scene_03 + scene_04 (2 шота, длинная фраза)\n"
        f"\n"
        f"     Правила канала, обязательны в каждом промпте:\n"
        f"       - Уникальный subject-маркер 3–4 английских слова в начале\n"
        f"         (например: persephone gathering spring flowers)\n"
        f"       - anthropomorphic bipedal cat character, standing upright\n"
        f"         on two legs like a human, humanoid body proportions\n"
        f"       - NO humans, NO people, NO real four-legged cats\n"
        f"       - Стилевой каркас: highly detailed pixel art, 9:16 vertical,\n"
        f"         ancient Greek setting, warm cinematic lighting,\n"
        f"         no text, no letters, no camera movement -->\n"
        f"\n"
        f"<!-- Карточка персонажей (для консистентности между сценами):\n"
        f"     <ОПИСАНИЕ ГЕРОЕВ — окрас, возраст, одежда, цвет глаз — заменить> -->\n"
        f"\n"
        f"## Сцена 1\n"
        f"\n"
        f"**Промпт:** <уникальный маркер 3-4 слова>, highly detailed pixel art, "
        f"9:16 vertical composition, ancient Greek setting, anthropomorphic "
        f"bipedal cat character, standing upright on two legs like a human, "
        f"humanoid body proportions, modern detailed pixel art style, warm "
        f"cinematic lighting, no text, no letters, no camera movement, "
        f"NO humans, NO people, NO real four-legged cats, "
        f"only anthropomorphic bipedal cat characters\n"
    )


def video_template(name: str) -> str:
    """Заготовка `prompts/video.md` для image-to-video (Veo / LTX)."""
    return (
        f"<!-- {name} — промпты image-to-video (Veo / LTX) по картинкам,\n"
        f"     прошедшим ревью.\n"
        f"\n"
        f"     Правила канала:\n"
        f"       - Уникальный subject-маркер 3–4 английских слова в начале\n"
        f"       - Обязательный негатив в каждом промпте:\n"
        f"         No speech, no dialogue, no talking, no voices,\n"
        f"         no mouth movement, no music\n"
        f"       - Без зумов и панорамирования камеры (если не попросили)\n"
        f"       - no blood, no gore, no wounds (модерация TikTok/Shorts)\n"
        f"       - Имена греческих богов заменять на descriptive\n"
        f"         (Hades → the somber dark-charcoal-gray regal cat king,\n"
        f"          Persephone → the calico queen, и т.п.) — IP-фильтр Veo. -->\n"
        f"\n"
        f"## Сцена 1\n"
        f"\n"
        f"**Промпт:** <уникальный маркер 3-4 слова>, slight motion, "
        f"ancient Greek setting, anthropomorphic bipedal cat character, "
        f"No speech, no dialogue, no talking, no voices, no mouth movement, no music, "
        f"no blood, no gore\n"
    )


# ── Раскатка ───────────────────────────────────────────────────────────────


class ScenarioExistsError(FileExistsError):
    """Папка сценария уже есть в content/ — не перезаписываем."""


def create_scenario(name: str, content_dir: Path, *, root: Path | None = None) -> list[str]:
    """Создать всю папочную структуру и шаблоны промптов для сценария.

    Args:
        name: имя мифа («Персефона и Аид»). Не валидируется — вызывающий код
              должен сначала прогнать через `validate_scenario_name()`.
        content_dir: путь к `content/` (обычно `ROOT / "content"`).
        root: корень репозитория для красивых относительных путей в логе.
              Если None — пути будут абсолютными.

    Returns:
        Список созданных путей (относительно `root` если он задан, иначе
        абсолютных), для лога/UI.

    Raises:
        ScenarioExistsError: если `content_dir / name` уже существует.
    """
    target = content_dir / name
    if target.exists():
        raise ScenarioExistsError(f"Сценарий «{name}» уже существует: {target}")

    def _rel(p: Path) -> str:
        if root is None:
            return str(p)
        return str(p.relative_to(root)).replace("\\", "/")

    created: list[str] = []
    target.mkdir(parents=True, exist_ok=False)
    created.append(_rel(target))

    for sub in SCENARIO_SUBDIRS:
        p = target / sub
        p.mkdir(parents=True, exist_ok=True)
        created.append(_rel(p))

    files = (
        ("prompts/voiceover.md", voiceover_template(name)),
        ("prompts/images.md", images_template(name)),
        ("prompts/video.md", video_template(name)),
    )
    for rel, content in files:
        fp = target / rel
        fp.write_text(content, encoding="utf-8")
        created.append(_rel(fp))

    return created
