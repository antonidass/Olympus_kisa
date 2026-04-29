"""
Distribute Images — раскладка ZIP-архива из Google Flow по review_images/scene_NN/vN.jpg.

Используется когда картинки сгенерированы вручную в Flow (не через
imagefx_runner.py) и экспортированы одним архивом «Download all». Скрипт
читает соответствующий `prompts/images.md`, сопоставляет имена файлов из
архива со сценами по уникальному subject-маркеру (первые 3-4 слова промпта,
которые Google Flow автоматически записывает в имя экспортируемого файла),
и раскладывает их в стандартную структуру `images/review_images/scene_NN/vN.jpg`.

Условие работы: первые 3-4 слова каждого `**Промпт:**` в images.md должны
быть уникальной фразой между сценами (см. CONTEXT.md «Уникальный subject-
маркер в начале каждого промпта»). Без этого правила сопоставление
неоднозначное и скрипт остановится с предупреждением.

Использование:
    python automation/distribute_images.py "content/<миф>/images/<archive>.zip"
    python automation/distribute_images.py "content/<миф>/images/<archive>.zip" --execute
    python automation/distribute_images.py "content/<миф>/images/_unpacked/"  # уже распаковано

По умолчанию — dry-run: показывает план раскладки и список несопоставленных
файлов, но ничего не двигает. С `--execute` физически переносит файлы (mv).
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

# Имя файла из Flow: <prefix>_<8-14 цифр даты>(_<idx>)?.jpeg
# Например: Persephone_gathering_spring_flowers_202604262319_2.jpeg
FILENAME_RE = re.compile(
    r"^(?P<prefix>.+?)_(?P<date>\d{8,14})(?:_(?P<idx>\d+))?\.(?P<ext>jpe?g|png|webp)$",
    re.IGNORECASE,
)

# Поддерживаемые расширения (lowercase)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass
class Scene:
    num: int
    marker: str  # первая фраза промпта, lowercase, без запятой и пробелы между словами
    marker_words: tuple[str, ...]


@dataclass
class FileEntry:
    path: Path
    prefix_words: tuple[str, ...]  # имя файла без даты, lowercase, расщеплённое на слова
    variant_idx: int  # 1 для файла без `_N`, иначе N
    archive_pos: int = 0  # 0-based позиция файла в архиве (= порядок генерации в Flow)


# ─── Парсинг images.md ─────────────────────────────────────────────────────


def parse_images_md(path: Path) -> dict[int, Scene]:
    """Извлекает первую фразу каждого `**Промпт:**` для каждой `## Сцена N`."""
    text = path.read_text(encoding="utf-8")

    # Разбиваем по заголовкам сцен. Захватываем номер.
    parts = re.split(r"^## Сцена (\d+)[^\n]*\n", text, flags=re.MULTILINE)
    # parts = [preamble, '1', body1, '2', body2, ...]

    scenes: dict[int, Scene] = {}
    for i in range(1, len(parts), 2):
        scene_num = int(parts[i])
        body = parts[i + 1]
        m = re.search(r"^\*\*Промпт:\*\*\s+([^,\n]+)", body, re.MULTILINE)
        if not m:
            continue
        marker_raw = m.group(1).strip().lower()
        words = tuple(_tokenize(marker_raw))
        scenes[scene_num] = Scene(num=scene_num, marker=marker_raw, marker_words=words)

    return scenes


def _tokenize(s: str) -> list[str]:
    """Лёгкая токенизация: lowercase, выкидываем пунктуацию, оставляем дефисы внутри слов."""
    s = s.lower()
    # заменяем _ и пунктуацию на пробелы
    s = re.sub(r"[_,.;:!?'\"()]", " ", s)
    return s.split()


def validate_unique_markers(scenes: dict[int, Scene]) -> list[str]:
    """Проверяет что первые 3 слова маркеров уникальны между сценами."""
    seen: dict[tuple[str, ...], list[int]] = {}
    for sc in scenes.values():
        key = sc.marker_words[:3]
        seen.setdefault(key, []).append(sc.num)

    errors: list[str] = []
    for key, scene_nums in seen.items():
        if len(scene_nums) > 1:
            phrase = " ".join(key)
            errors.append(
                f"Маркер '{phrase}' повторяется в сценах {scene_nums} — "
                "переименуй первые 3-4 слова промптов чтобы были уникальны."
            )
    return errors


# ─── Парсинг файлов из архива ──────────────────────────────────────────────


def parse_filename(path: Path, archive_pos: int = 0) -> FileEntry | None:
    m = FILENAME_RE.match(path.name)
    if not m:
        return None
    prefix = m.group("prefix")
    idx = int(m.group("idx")) if m.group("idx") else 1
    return FileEntry(
        path=path,
        prefix_words=tuple(_tokenize(prefix)),
        variant_idx=idx,
        archive_pos=archive_pos,
    )


# ─── Сопоставление файлов ↔ сцен ───────────────────────────────────────────

# Уровни уверенности матча (меньше = сильнее)
MATCH_STRICT = 1   # filename — точный префикс маркера
MATCH_SUBSTR = 2   # filename — непрерывная подпоследовательность маркера (Flow съел первые слова)
MATCH_FUZZY = 3    # пересечение слов (bag of words) — юзер менял промпт в Flow


def match_file_to_scene(
    entry: FileEntry, scenes: dict[int, Scene], allow_fuzzy: bool = False
) -> tuple[int, int, Scene] | None:
    """
    Возвращает (level, score, scene) где level ∈ {1,2,3} — степень доверия,
    score — сколько слов совпало. Чем меньше level, тем строже совпадение.
    Если allow_fuzzy=False, level 3 не возвращается.
    """
    best: tuple[int, int, Scene] | None = None
    for sc in scenes.values():
        candidate = _score_against(entry.prefix_words, sc, allow_fuzzy=allow_fuzzy)
        if candidate is None:
            continue
        level, score = candidate
        if best is None or (level, -score) < (best[0], -best[1]):
            best = (level, score, sc)
    return best


def _score_against(
    fwords: tuple[str, ...], sc: Scene, allow_fuzzy: bool
) -> tuple[int, int] | None:
    """Находит лучший уровень и счёт совпадения filename ↔ marker сцены."""
    mwords = sc.marker_words

    # Уровень 1: filename — префикс маркера (≥3 слов, или ≥2 если filename короткий)
    pref = _common_prefix_len(fwords, mwords)
    if pref >= 3 or (pref >= 2 and len(fwords) <= 3):
        return (MATCH_STRICT, pref)

    # Уровень 2: filename — префикс marker[k:] для какого-то k (Flow съел первое слово)
    for k in range(1, len(mwords)):
        sub = _common_prefix_len(fwords, mwords[k:])
        if sub >= 3 or (sub >= 2 and len(fwords) <= 3):
            return (MATCH_SUBSTR, sub)

    # Уровень 3: bag of words — пересечение множеств
    if allow_fuzzy:
        fset = set(fwords)
        mset = set(mwords)
        overlap = len(fset & mset)
        # Нужно: (а) совпало ≥2 слов, (б) почти все слова filename присутствуют в маркере
        if overlap >= 2 and overlap >= len(fwords) - 1:
            return (MATCH_FUZZY, overlap)

    return None


def _common_prefix_len(a: tuple[str, ...], b: tuple[str, ...]) -> int:
    n = 0
    for x, y in zip(a, b):
        if x == y:
            n += 1
        else:
            break
    return n


def _check_manual_map(
    fwords: tuple[str, ...],
    manual_map: dict[tuple[str, ...], int],
    scenes: dict[int, Scene],
) -> Scene | None:
    """
    Проверяет соответствие ручному --map маппингу.
    Совпадение: ключ маппинга — точный префикс имени файла (все слова ключа
    идут в начале имени файла), либо наоборот (имя файла — префикс ключа).
    """
    for key_words, scene_num in manual_map.items():
        if not key_words:
            continue
        n = _common_prefix_len(fwords, key_words)
        if n == len(key_words) or n == len(fwords):
            return scenes[scene_num]
    return None


# ─── Подсказки по позиции в архиве (Flow генерит в порядке сцен) ───────────


def compute_position_anchors(
    plan: dict[int, list[tuple[int, "FileEntry"]]],
) -> list[tuple[float, int]]:
    """
    Из уже сопоставленного плана строит «якоря» — пары (средняя_позиция, scene_num).
    Если пользователь генерил сцены по порядку, то и якоря тоже отсортированы.
    """
    anchors: list[tuple[float, int]] = []
    for scene_num, entries in plan.items():
        positions = [e.archive_pos for _, e in entries]
        if not positions:
            continue
        anchors.append((sum(positions) / len(positions), scene_num))
    anchors.sort()
    return anchors


def suggest_scene_by_position(
    archive_pos: float,
    anchors: list[tuple[float, int]],
    all_scene_nums: list[int],
    occupied_scenes: set[int],
) -> int | None:
    """
    Для несопоставленного префикса возвращает наиболее вероятный номер сцены,
    основываясь на его позиции в архиве относительно якорей.
    Логика: ищет недостающие сцены между ближайшим якорем-до и якорем-после
    данной позиции. Если ровно одна — возвращает её.
    """
    before_scene: int | None = None
    after_scene: int | None = None
    for pos, sn in anchors:
        if pos < archive_pos:
            before_scene = sn  # последний из тех что до позиции
        elif pos > archive_pos and after_scene is None:
            after_scene = sn
            break

    # Кандидаты: сцены которые лежат между якорями и ещё не заняты
    candidates = [
        sn
        for sn in all_scene_nums
        if (before_scene is None or sn > before_scene)
        and (after_scene is None or sn < after_scene)
        and sn not in occupied_scenes
    ]
    if len(candidates) == 1:
        return candidates[0]
    # Если несколько кандидатов — выбираем ближайший к интерполированной позиции
    if len(candidates) > 1 and before_scene is not None and after_scene is not None:
        # Линейная интерполяция scene_num по позиции
        # ищем якоря с известными позициями
        before_pos = next(p for p, s in anchors if s == before_scene)
        after_pos = next(p for p, s in anchors if s == after_scene)
        if after_pos > before_pos:
            frac = (archive_pos - before_pos) / (after_pos - before_pos)
            target = before_scene + frac * (after_scene - before_scene)
            candidates.sort(key=lambda sn: abs(sn - target))
            return candidates[0]
    return None


# ─── Вспомогательное: распаковка / чтение имён ─────────────────────────────


def list_zip_names(archive: Path) -> list[str]:
    """Возвращает имена файлов внутри zip (без распаковки)."""
    with zipfile.ZipFile(archive) as zf:
        return [
            n
            for n in zf.namelist()
            if Path(n).suffix.lower() in IMAGE_EXTS and not n.endswith("/")
        ]


def extract_archive(archive: Path, dest: Path) -> list[Path]:
    """Распаковывает zip в dest, возвращает список путей к картинкам."""
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest)
    return collect_images(dest)


def collect_images(folder: Path) -> list[Path]:
    return sorted(
        p
        for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def detect_myth_dir(input_path: Path) -> Path | None:
    """
    По пути к архиву/папке определяет корень мифа (где лежит prompts/images.md).
    Поднимается вверх от input_path пока не найдёт.
    """
    candidates = [input_path]
    if input_path.is_file():
        candidates.append(input_path.parent)
    candidates.extend(input_path.parents)

    for c in candidates:
        if (c / "prompts" / "images.md").exists():
            return c
    return None


# ─── Основная логика ────────────────────────────────────────────────────────


_LEVEL_LABELS = {
    MATCH_STRICT: "✓",   # строгий префикс
    MATCH_SUBSTR: "~",   # Flow съел первые слова маркера
    MATCH_FUZZY:  "?",   # пересечение слов — нужно подтвердить визуально
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Раскладка архива Flow по review_images/scene_NN/vN.jpg",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input",
        type=Path,
        help="ZIP-архив или папка с уже распакованными картинками",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Выполнить раскладку (без флага — dry-run без распаковки)",
    )
    parser.add_argument(
        "--fuzzy",
        action="store_true",
        help="Включить fuzzy-сопоставление (bag of words) для случаев когда в Flow редактировался промпт",
    )
    parser.add_argument(
        "--map",
        action="append",
        default=[],
        metavar="PREFIX=SCENE",
        help='Ручной маппинг префикса файла на сцену (повторяемый). Пример: --map "withered_wheat_field=15" --map "demeter_in_frozen=27"',
    )
    parser.add_argument(
        "--myth-dir",
        type=Path,
        default=None,
        help="Папка мифа (по умолчанию определяется по пути архива)",
    )
    parser.add_argument(
        "--keep-unpacked",
        action="store_true",
        help="Не удалять папку _unpacked после раскладки",
    )
    args = parser.parse_args()

    input_path: Path = args.input
    if not input_path.exists():
        print(f"ERROR: не найдено {input_path}", file=sys.stderr)
        return 1

    # Определяем папку мифа
    myth_dir: Path | None = args.myth_dir or detect_myth_dir(input_path)
    if myth_dir is None:
        print(
            f"ERROR: не нашёл prompts/images.md рядом с {input_path}. "
            "Укажи --myth-dir вручную.",
            file=sys.stderr,
        )
        return 1

    images_md = myth_dir / "prompts" / "images.md"
    review_dir = myth_dir / "images" / "review_images"

    print(f"Папка мифа:  {myth_dir}")
    print(f"Промпты:     {images_md}")
    print(f"Цель:        {review_dir}")
    print()

    # Парсим images.md
    scenes = parse_images_md(images_md)
    if not scenes:
        print(f"ERROR: не нашёл ни одной сцены в {images_md}", file=sys.stderr)
        return 1
    print(f"Сцен в images.md: {len(scenes)}")

    # Проверка уникальности маркеров
    errors = validate_unique_markers(scenes)
    if errors:
        print()
        print("ERROR: subject-маркеры не уникальны:")
        for e in errors:
            print(f"  • {e}")
        print()
        print("См. CONTEXT.md, раздел «Уникальный subject-маркер в начале каждого промпта».")
        return 1

    # Чтение имён файлов: для dry-run — без распаковки, для execute — с распаковкой.
    cleanup_unpacked: Path | None = None
    is_zip = input_path.is_file() and input_path.suffix.lower() == ".zip"

    if not args.execute:
        # Dry-run: читаем имена прямо из zip без extract, или сканируем папку
        if is_zip:
            print(f"Читаю имена из {input_path.name} (без распаковки)")
            names = list_zip_names(input_path)
            file_paths = [Path(n) for n in names]
        elif input_path.is_dir():
            file_paths = collect_images(input_path)
        else:
            print(f"ERROR: ожидался ZIP или папка, получен {input_path}", file=sys.stderr)
            return 1
    else:
        # Execute: реально распаковываем (или используем существующую папку)
        if is_zip:
            unpack_dir = myth_dir / "images" / "_unpacked"
            print(f"Распаковываю {input_path.name} → {unpack_dir}")
            file_paths = extract_archive(input_path, unpack_dir)
            cleanup_unpacked = unpack_dir
        elif input_path.is_dir():
            file_paths = collect_images(input_path)
            if not file_paths:
                print(f"ERROR: нет картинок в папке {input_path}", file=sys.stderr)
                return 1
        else:
            print(f"ERROR: ожидался ZIP или папка, получен {input_path}", file=sys.stderr)
            return 1

    print(f"Файлов в источнике: {len(file_paths)}")

    # Парсим --map "prefix=scene_num" → {tuple_of_words: scene_num}
    # Уровень MATCH_MANUAL — самый сильный (0 < MATCH_STRICT)
    manual_map: dict[tuple[str, ...], int] = {}
    for spec in args.map:
        if "=" not in spec:
            print(f"ERROR: неверный --map '{spec}', ожидался 'prefix=scene_num'", file=sys.stderr)
            return 1
        prefix_str, scene_str = spec.rsplit("=", 1)
        try:
            scene_num = int(scene_str)
        except ValueError:
            print(f"ERROR: --map '{spec}': scene_num должен быть числом", file=sys.stderr)
            return 1
        if scene_num not in scenes:
            print(f"ERROR: --map '{spec}': scene_{scene_num:02d} не найдена в images.md", file=sys.stderr)
            return 1
        manual_map[tuple(_tokenize(prefix_str))] = scene_num

    if manual_map:
        print(f"Ручных маппингов: {len(manual_map)}")
    print()

    # Сопоставление
    # plan: scene_num → [(level, entry), ...]
    plan: dict[int, list[tuple[int, FileEntry]]] = {}
    unparseable: list[tuple[Path, str]] = []  # имя не подошло под паттерн
    unmatched: list[FileEntry] = []  # имя распознано, но сцена не найдена

    for archive_pos, f in enumerate(file_paths):
        entry = parse_filename(f, archive_pos=archive_pos)
        if entry is None:
            unparseable.append((f, "не распознан паттерн <prefix>_<date>(_N)?.<ext>"))
            continue

        # 1) Сначала ищем точный override в --map
        manual_scene = _check_manual_map(entry.prefix_words, manual_map, scenes)
        if manual_scene is not None:
            plan.setdefault(manual_scene.num, []).append((MATCH_STRICT, entry))
            continue

        # 2) Иначе — обычный matcher
        result = match_file_to_scene(entry, scenes, allow_fuzzy=args.fuzzy)
        if result is None:
            unmatched.append(entry)
            continue
        level, _, scene = result
        plan.setdefault(scene.num, []).append((level, entry))

    # Печать плана
    print("=== ПЛАН РАСКЛАДКИ ===")
    print("    Уровни доверия: ✓ строгий / ~ Flow обрезал маркер / ? fuzzy bag-of-words")
    print()
    for scene_num in sorted(plan.keys()):
        files_for_scene = sorted(plan[scene_num], key=lambda x: x[1].variant_idx)
        sc = scenes[scene_num]
        # Худший уровень в группе = общий уровень доверия группы
        worst_level = max(level for level, _ in files_for_scene)
        head_mark = _LEVEL_LABELS[worst_level]
        print(f"scene_{scene_num:02d}  {head_mark}  ({len(files_for_scene)} файл.)  · «{sc.marker}»")
        for new_v, (level, entry) in enumerate(files_for_scene, start=1):
            mark = _LEVEL_LABELS[level]
            print(f"   v{new_v}.jpg  {mark}  ←  {entry.path.name}")
    print()

    fuzzy_files = sum(1 for files in plan.values() for level, _ in files if level == MATCH_FUZZY)
    substr_files = sum(1 for files in plan.values() for level, _ in files if level == MATCH_SUBSTR)
    if substr_files or fuzzy_files:
        print(f"Совпадений с пометкой: ~ (Flow обрезал) {substr_files},  ? (fuzzy) {fuzzy_files}")
        if fuzzy_files:
            print("  ? — рекомендую открыть по одной картинке из такой группы и сверить с маркером сцены.")
        print()

    # Несопоставленные — группируем по префиксу, считаем подсказку по позиции в архиве
    if unmatched or unparseable:
        print(f"=== НЕ СОПОСТАВЛЕНЫ: {len(unmatched) + len(unparseable)} файл(ов) ===")

        # Сначала те где даже имя не парсится
        for path, reason in unparseable:
            print(f"   {path.name}  —  {reason}")

        # Группируем оставшиеся по prefix_words
        groups: dict[tuple[str, ...], list[FileEntry]] = {}
        for entry in unmatched:
            groups.setdefault(entry.prefix_words, []).append(entry)

        # Якоря из плана для подсказки по позиции
        anchors = compute_position_anchors(plan)
        all_scene_nums = sorted(scenes.keys())
        occupied = set(plan.keys())

        suggested_maps: list[str] = []
        for prefix_words, entries in groups.items():
            mean_pos = sum(e.archive_pos for e in entries) / len(entries)
            min_pos = min(e.archive_pos for e in entries)
            max_pos = max(e.archive_pos for e in entries)
            prefix_str = "_".join(prefix_words)
            phrase = " ".join(prefix_words[:4])
            suggestion = suggest_scene_by_position(mean_pos, anchors, all_scene_nums, occupied)

            print(
                f"   {prefix_str}  ({len(entries)} файл., позиции {min_pos}-{max_pos} из {len(file_paths)})"
            )
            print(f'      нет сцены с маркером для "{phrase}"')
            if suggestion is not None:
                sc_marker = scenes[suggestion].marker
                print(
                    f"      → по порядку в архиве вероятно scene_{suggestion:02d}  «{sc_marker}»"
                )
                suggested_maps.append(f'--map "{prefix_str}={suggestion}"')
            else:
                print("      по порядку в архиве однозначно определить не удалось")
        print()

        if suggested_maps:
            print("Готовая команда для раскладки (проверь визуально перед --execute):")
            print(
                "   python automation/distribute_images.py <архив> --execute \\\n     "
                + " \\\n     ".join(suggested_maps)
            )
            print()

    # Сцены без файлов
    missing = sorted(set(scenes.keys()) - set(plan.keys()))
    if missing:
        print(f"=== СЦЕНЫ БЕЗ КАРТИНОК: {len(missing)} ===")
        for n in missing:
            print(f"   scene_{n:02d}  ·  «{scenes[n].marker}»")
        print()

    # Группы с нестандартным числом файлов (≠4) — предупреждение
    odd_counts = [
        (n, len(plan[n])) for n in sorted(plan.keys()) if len(plan[n]) != 4
    ]
    if odd_counts:
        print("ВНИМАНИЕ: сцены с нестандартным числом файлов (обычно 4 варианта):")
        for n, cnt in odd_counts:
            print(f"   scene_{n:02d}  ·  {cnt} файл(ов)")
        print()

    # Dry-run останавливается тут
    if not args.execute:
        print("DRY-RUN. Запусти с --execute чтобы выполнить раскладку.")
        return 0

    # Если есть несопоставленные — не выполняем
    total_unmatched = len(unmatched) + len(unparseable)
    if total_unmatched:
        print(
            f"СТОП: {total_unmatched} файл(ов) не сопоставлены. "
            "Раскладка не выполнена. Используй подсказки по позиции выше для --map, "
            "или попробуй --fuzzy."
        )
        return 1

    # Выполнение
    print("=== ВЫПОЛНЕНИЕ ===")
    for scene_num in sorted(plan.keys()):
        files_for_scene = sorted(plan[scene_num], key=lambda x: x[1].variant_idx)
        scene_dir = review_dir / f"scene_{scene_num:02d}"
        scene_dir.mkdir(parents=True, exist_ok=True)
        # Если в папке уже есть файлы — добавляем номера дальше последнего v_N
        existing = sorted(scene_dir.glob("v*.jpg"))
        offset = len(existing)
        for new_v, (level, entry) in enumerate(files_for_scene, start=offset + 1):
            dst = scene_dir / f"v{new_v}.jpg"
            shutil.move(str(entry.path), str(dst))
            print(f"   scene_{scene_num:02d}/v{new_v}.jpg  ←  {entry.path.name}")
    print()

    # Очистка пустой _unpacked
    if cleanup_unpacked is not None and cleanup_unpacked.exists() and not args.keep_unpacked:
        try:
            cleanup_unpacked.rmdir()
            print(f"Удалена пустая {cleanup_unpacked.name}/")
        except OSError:
            print(f"Папка {cleanup_unpacked.name}/ не пустая — оставляю как есть.")

    print()
    total_moved = sum(len(v) for v in plan.values())
    print(f"ГОТОВО: разложено {total_moved} файл(ов) по {len(plan)} сценам.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
