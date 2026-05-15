"""
Distribute Stickers — раскладка ZIP-архива со стикерами из Google Flow.

Шаг 9 пайплайна (см. CONTEXT.md). Используется после того как Claude
написал `prompts/stickers.md` (шаг 8) и пользователь сгенерировал
картинки в Flow вручную, скачав их одним архивом «Download all».

Скрипт:
  1. Читает `prompts/stickers.md` → собирает scene_num ↔ subject-маркер.
  2. Распаковывает архив (или берёт уже распакованную папку).
  3. Сопоставляет имя файла из Flow (`Cat_goddess_marriage_order_<дата>.jpeg`)
     с соответствующей сценой через первые 3-4 слова промпта.
  4. Раскладывает картинки в `images/stickers/scene_<NN>_<маркер>.<ext>`.

Условие работы: первые 3-4 слова каждого `**Промпт:**` в stickers.md
должны быть уникальной фразой между сценами (см. CONTEXT.md
«Уникальный subject-маркер в начале каждого промпта»).

В отличие от distribute_images.py:
  - один стикер на сцену (нет вариантов v1/v2/v3),
  - результат — плоская папка `images/stickers/`, без подпапок по сценам,
  - имя выходного файла включает scene_NN и маркер, чтобы
    `enrich_<миф>.py` потом находил стикер по имени.

Использование:
    python automation/distribute_stickers.py "content/<миф>/images/stickers/<archive>.zip"
    python automation/distribute_stickers.py "content/<миф>/images/stickers/<archive>.zip" --execute
    python automation/distribute_stickers.py "content/<миф>/images/stickers/_unpacked/"
    python automation/distribute_stickers.py "<archive>.zip" --execute --map "marriage_order=5"

По умолчанию — dry-run: показывает план раскладки и список несопоставленных
файлов, но ничего не двигает. С `--execute` физически переименовывает.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Имя файла из Flow: <prefix>_<8-14 цифр даты>(_<idx>)?.<ext>
FILENAME_RE = re.compile(
    r"^(?P<prefix>.+?)_(?P<date>\d{8,14})(?:_(?P<idx>\d+))?\.(?P<ext>jpe?g|png|webp)$",
    re.IGNORECASE,
)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass
class Scene:
    num: int
    marker: str  # первая фраза промпта, lowercase
    marker_words: tuple[str, ...]


@dataclass
class FileEntry:
    path: Path
    prefix_words: tuple[str, ...]
    variant_idx: int  # 1 для файла без `_N`, иначе N
    archive_pos: int = 0


@dataclass
class Match:
    file: FileEntry
    scene: Scene
    level: int  # 1=strict, 2=substring, 3=fuzzy, 4=manual map
    score: int


# ─── Парсинг stickers.md ───────────────────────────────────────────────────


def _tokenize(s: str) -> list[str]:
    s = s.lower()
    s = re.sub(r"[_,.;:!?'\"()]", " ", s)
    return s.split()


def parse_stickers_md(path: Path) -> dict[int, Scene]:
    """Извлекает первую фразу `**Промпт:**` для каждой `## Сцена N`."""
    text = path.read_text(encoding="utf-8")
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
        if not words:
            continue
        scenes[scene_num] = Scene(num=scene_num, marker=marker_raw, marker_words=words)

    return scenes


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


# ─── Парсинг файлов ────────────────────────────────────────────────────────


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


# ─── Сопоставление ─────────────────────────────────────────────────────────


MATCH_STRICT = 1
MATCH_SUBSTR = 2
MATCH_FUZZY = 3
MATCH_MANUAL = 4


def _common_prefix_len(a: tuple[str, ...], b: tuple[str, ...]) -> int:
    n = 0
    for x, y in zip(a, b):
        if x == y:
            n += 1
        else:
            break
    return n


def match_file_to_scene(
    entry: FileEntry,
    scenes: dict[int, Scene],
    allow_fuzzy: bool,
    manual_map: dict[tuple[str, ...], int],
) -> Match | None:
    # 1) ручной маппинг — высший приоритет
    for key_words, scene_num in manual_map.items():
        if not key_words:
            continue
        n = _common_prefix_len(entry.prefix_words, key_words)
        if n == len(key_words) or n == len(entry.prefix_words):
            sc = scenes.get(scene_num)
            if sc:
                return Match(file=entry, scene=sc, level=MATCH_MANUAL, score=n)

    # 2) автоматический матч по префиксу / подстроке / fuzzy
    best: Match | None = None
    fwords = entry.prefix_words
    for sc in scenes.values():
        mwords = sc.marker_words

        # strict prefix
        pref = _common_prefix_len(fwords, mwords)
        if pref >= 3 or (pref >= 2 and len(fwords) <= 3):
            cand = Match(file=entry, scene=sc, level=MATCH_STRICT, score=pref)
            if best is None or (cand.level, -cand.score) < (best.level, -best.score):
                best = cand
            continue

        # substring (Flow съел первые слова)
        sub_best = 0
        for k in range(1, len(mwords)):
            sub = _common_prefix_len(fwords, mwords[k:])
            if sub > sub_best:
                sub_best = sub
        if sub_best >= 3 or (sub_best >= 2 and len(fwords) <= 3):
            cand = Match(file=entry, scene=sc, level=MATCH_SUBSTR, score=sub_best)
            if best is None or (cand.level, -cand.score) < (best.level, -best.score):
                best = cand
            continue

        # fuzzy bag-of-words
        if allow_fuzzy:
            fset = set(fwords)
            mset = set(mwords)
            overlap = len(fset & mset)
            if overlap >= 2 and overlap >= len(fwords) - 1:
                cand = Match(file=entry, scene=sc, level=MATCH_FUZZY, score=overlap)
                if best is None or (cand.level, -cand.score) < (best.level, -best.score):
                    best = cand

    return best


# ─── Основной поток ────────────────────────────────────────────────────────


def _level_glyph(level: int) -> str:
    return {MATCH_STRICT: "OK", MATCH_SUBSTR: "~", MATCH_FUZZY: "?", MATCH_MANUAL: "M"}[level]


def _output_name(scene: Scene, entry: FileEntry) -> str:
    """Имя файла назначения: scene_<NN>_<marker_joined>.<ext>."""
    marker_joined = "_".join(scene.marker_words[:6])  # ограничим до 6 слов чтобы имя не было кошмарным
    marker_joined = re.sub(r"[^a-z0-9_]+", "", marker_joined)
    ext = entry.path.suffix.lower()
    if ext == ".jpeg":
        ext = ".jpg"  # унифицируем
    return f"scene_{scene.num:02d}_{marker_joined}{ext}"


def _output_path(target_dir: Path, scene: Scene, entry: FileEntry, scene_folders: bool) -> Path:
    out_name = _output_name(scene, entry)
    if scene_folders:
        return target_dir / f"scene_{scene.num:02d}" / out_name
    return target_dir / out_name


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_existing_hashes(root: Path, exclude: set[Path] | None = None) -> set[str]:
    exclude = exclude or set()
    hashes: set[str] = set()
    if not root.exists():
        return hashes
    for path in root.rglob("*"):
        if path.resolve() in exclude:
            continue
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
            hashes.add(file_sha256(path))
    return hashes


def _resolve_stickers_md(input_path: Path) -> Path:
    """Найти `prompts/stickers.md` относительно входа.

    Если вход — путь внутри `content/<миф>/...`, ищем рядом
    `content/<миф>/prompts/stickers.md`.
    """
    p = input_path.resolve()
    # Поднимаемся, пока не найдём content/<myth>/
    cur = p if p.is_dir() else p.parent
    for _ in range(8):
        candidate = cur / "prompts" / "stickers.md"
        if candidate.exists():
            return candidate
        if cur.parent == cur:
            break
        cur = cur.parent
    raise FileNotFoundError(
        f"Не нашёл prompts/stickers.md рядом с {input_path}. "
        "Скрипт ожидает что вход лежит внутри content/<миф>/images/stickers/."
    )


def _resolve_target_dir(input_path: Path) -> Path:
    """Целевая папка для разложенных стикеров — `images/stickers/`."""
    p = input_path.resolve()
    cur = p if p.is_dir() else p.parent
    for _ in range(8):
        if cur.name == "stickers" and cur.parent.name == "images":
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise FileNotFoundError(
        f"Не нашёл папку images/stickers/ выше {input_path}. "
        "Положи архив в content/<миф>/images/stickers/<archive>.zip."
    )


def _unpack_input(input_path: Path) -> tuple[Path, bool]:
    """Если вход — zip, распаковать в _unpacked/. Возвращает (папка, нужно_удалить)."""
    if input_path.is_dir():
        return input_path, False

    if input_path.suffix.lower() != ".zip":
        raise ValueError(f"Ожидаю .zip или папку, получил: {input_path}")

    target_dir = _resolve_target_dir(input_path)
    unpack_dir = target_dir / "_unpacked"
    if unpack_dir.exists():
        shutil.rmtree(unpack_dir)
    unpack_dir.mkdir(parents=True)

    with zipfile.ZipFile(input_path) as zf:
        zf.extractall(unpack_dir)

    return unpack_dir, True


def _collect_files(folder: Path) -> list[FileEntry]:
    """Собрать все картинки из папки (рекурсивно), сохраняя порядок."""
    paths = sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    entries: list[FileEntry] = []
    for pos, p in enumerate(paths):
        e = parse_filename(p, archive_pos=pos)
        if e is None:
            print(f"  WARN пропускаю файл с нестандартным именем: {p.name}", file=sys.stderr)
            continue
        entries.append(e)
    return entries


def _parse_manual_map(items: list[str]) -> dict[tuple[str, ...], int]:
    """`--map "marriage_order=5"` → {('marriage', 'order'): 5}."""
    out: dict[tuple[str, ...], int] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"--map ожидает формат 'prefix=N', получил: {item}")
        key, num = item.rsplit("=", 1)
        out[tuple(_tokenize(key))] = int(num)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Раскладка стикеров из Flow-архива по content/<миф>/images/stickers/",
    )
    parser.add_argument("input", help="ZIP-архив из Flow или уже распакованная папка")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Действительно переместить файлы (по умолчанию dry-run)",
    )
    parser.add_argument(
        "--fuzzy",
        action="store_true",
        help="Разрешить fuzzy-совпадение по пересечению слов (если в Flow редактировал промпт)",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Разрешить частичный набор: сцены без файла-сцены не считаются ошибкой.",
    )
    parser.add_argument(
        "--scene-folders",
        action="store_true",
        help="Класть результат в подпапки scene_NN внутри images/stickers/.",
    )
    parser.add_argument(
        "--map",
        action="append",
        default=[],
        metavar="PREFIX=N",
        help="Ручной override: префикс файла → номер сцены. Можно повторять.",
    )
    args = parser.parse_args()

    input_path = Path(args.input).expanduser()
    if not input_path.exists():
        print(f"ERROR: не найден {input_path}", file=sys.stderr)
        return 2

    stickers_md = _resolve_stickers_md(input_path)
    target_dir = _resolve_target_dir(input_path)
    print(f"stickers.md:  {stickers_md}")
    print(f"target dir:   {target_dir}")
    print()

    scenes = parse_stickers_md(stickers_md)
    if not scenes:
        print(f"ERROR: в {stickers_md} не найдено ни одного `## Сцена N` с **Промпт:**", file=sys.stderr)
        return 1

    print(f"Сцены со стикерами в stickers.md ({len(scenes)}):")
    for sc in sorted(scenes.values(), key=lambda s: s.num):
        print(f"  scene_{sc.num:02d}: {sc.marker}")
    print()

    errors = validate_unique_markers(scenes)
    if errors:
        print("ERROR: маркеры не уникальны:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    # Распаковка
    src_dir, cleanup = _unpack_input(input_path)
    try:
        entries = _collect_files(src_dir)
        if not entries:
            print(f"ERROR: в {src_dir} нет подходящих картинок (.jpg/.png/.webp)", file=sys.stderr)
            return 1

        manual_map = _parse_manual_map(args.map)

        matched: list[Match] = []
        unmatched: list[FileEntry] = []
        for e in entries:
            m = match_file_to_scene(e, scenes, allow_fuzzy=args.fuzzy, manual_map=manual_map)
            if m is None:
                unmatched.append(e)
            else:
                matched.append(m)

        # Не должно быть двух файлов на одну сцену — если есть, оставляем самый сильный
        by_scene: dict[int, Match] = {}
        duplicates: list[tuple[Match, Match]] = []
        for m in matched:
            prev = by_scene.get(m.scene.num)
            if prev is None:
                by_scene[m.scene.num] = m
            else:
                if (m.level, -m.score) < (prev.level, -prev.score):
                    duplicates.append((prev, m))
                    by_scene[m.scene.num] = m
                else:
                    duplicates.append((m, prev))

        # ─── План ──────────────────────────────────────────────────────────
        print("План раскладки:")
        for scene_num in sorted(by_scene):
            m = by_scene[scene_num]
            dst = _output_path(target_dir, m.scene, m.file, args.scene_folders)
            out_rel = dst.relative_to(target_dir)
            glyph = _level_glyph(m.level)
            print(
                f"  {glyph} scene_{scene_num:02d}: {m.file.path.name}\n"
                f"       -> {target_dir.name}/{out_rel}"
            )

        missing = [sc for sc in scenes.values() if sc.num not in by_scene]
        if missing:
            print()
            print(f"WARN Не нашёл стикер для {len(missing)} сцен:")
            for sc in missing:
                print(f"  scene_{sc.num:02d}: {sc.marker}")

        if unmatched:
            print()
            print(f"WARN Не сопоставлено с какой-либо сценой ({len(unmatched)} файлов):")
            for e in unmatched:
                print(f"  {e.path.name}  (prefix words: {' '.join(e.prefix_words[:6])})")
            print("  Используй --map 'prefix_words=N' для ручного override или --fuzzy.")

        if duplicates:
            print()
            print(f"WARN Несколько файлов на одну сцену (выбран более сильный матч):")
            for losing, winning in duplicates:
                print(
                    f"  scene_{winning.scene.num:02d}: "
                    f"победил {winning.file.path.name} ({_level_glyph(winning.level)}); "
                    f"проиграл {losing.file.path.name} ({_level_glyph(losing.level)})"
                )

        has_blocking_errors = bool(unmatched) or (bool(missing) and not args.allow_missing)
        if has_blocking_errors:
            print()
            print("ERROR: остались несопоставленные файлы / сцены без стикеров. "
                  "Исправь и перезапусти. Без --execute ничего не двигалось.", file=sys.stderr)
            if not args.execute:
                return 1
            return 1

        if missing and args.allow_missing:
            print()
            print(f"Partial mode: пропускаю {len(missing)} сцен без стикеров.")

        # ─── Выполнение ────────────────────────────────────────────────────
        if not args.execute:
            print()
            print(f"Dry-run: ничего не двигаю. Добавь --execute чтобы переименовать "
                  f"{len(by_scene)} файлов в {target_dir}.")
            return 0

        print()
        print(f"Переименовываю {len(by_scene)} файлов в {target_dir}...")
        source_paths = {e.path.resolve() for e in entries}
        existing_hashes = collect_existing_hashes(target_dir, exclude=source_paths)
        moved_count = 0
        skipped_duplicates = 0
        already_placed = 0
        for scene_num in sorted(by_scene):
            m = by_scene[scene_num]
            src_hash = file_sha256(m.file.path)
            dst = _output_path(target_dir, m.scene, m.file, args.scene_folders)

            if m.file.path.resolve() == dst.resolve():
                already_placed += 1
                existing_hashes.add(src_hash)
                print(f"  OK already placed: {m.file.path.name}")
                continue

            if src_hash in existing_hashes:
                skipped_duplicates += 1
                m.file.path.unlink()
                print(f"  SKIP duplicate: {m.file.path.name}")
                continue

            if dst.exists():
                print(f"  WARN уже существует, перезаписываю: {dst.name}")
                dst.unlink()
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(m.file.path), str(dst))
            existing_hashes.add(src_hash)
            moved_count += 1
            print(f"  {m.file.path.name} -> {dst.relative_to(target_dir)}")

        print()
        print(
            f"Готово: {moved_count} стикеров в {target_dir}, "
            f"уже лежали на месте {already_placed}, "
            f"дубликатов пропущено {skipped_duplicates}."
        )
        return 0

    finally:
        if cleanup and src_dir.exists() and src_dir.name == "_unpacked":
            try:
                shutil.rmtree(src_dir)
            except OSError as exc:
                print(f"  WARN не смог удалить {src_dir}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
