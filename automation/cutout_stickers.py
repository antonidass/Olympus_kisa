"""
Cutout Stickers — обрезка фона у стикеров через rembg (U²-Net и др.).

Шаг между 9 (distribute_stickers.py) и enrich-стадиями pyCapCut.
Flow генерирует стикеры как JPG со сплошным/градиентным фоном, а в CapCut
нужны PNG с альфой, чтобы класть стикер поверх кадра без рамки.

Скрипт:
  1. Читает все `scene_NN_*.jpg/png/webp` из `images/stickers/`.
  2. Прогоняет каждый через rembg, получает PNG с прозрачным фоном.
  3. Складывает результат в `images/stickers/cutout/scene_NN_*.png`
     (оригиналы JPG остаются на месте — обратимо).

Поведение по умолчанию — превью: обрабатывает 2 первые сцены и кладёт
их в `cutout/_preview/`. Пользователь смотрит PNG в проводнике, если
ок — запускает с `--execute` для полной партии.

Использование:
    # Превью на первых 2 сценах:
    python automation/cutout_stickers.py "content/<миф>/images/stickers/"

    # Полный прогон:
    python automation/cutout_stickers.py "content/<миф>/images/stickers/" --execute

    # Только конкретные сцены:
    python automation/cutout_stickers.py "content/<миф>/images/stickers/" --execute --scene 3,7,9

    # Пропустить сцены где фон — часть смысла:
    python automation/cutout_stickers.py "content/<миф>/images/stickers/" --execute --skip 5,11

    # Другая модель (isnet-general-use лучше для рисованных UI-плашек):
    python automation/cutout_stickers.py "content/<миф>/images/stickers/" --execute --model isnet-general-use

    # Один конкретный файл:
    python automation/cutout_stickers.py "content/<миф>/images/stickers/scene_03_*.jpg" --execute

Зависимости: rembg[cpu]>=2.0.75 (см. requirements.txt). При первом запуске
rembg скачает ONNX-модель (~170 МБ для u2net) в ~/.u2net/.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
SCENE_RE = re.compile(r"^scene_(\d{1,3})_", re.IGNORECASE)

# Модели rembg по убыванию универсальности.
# u2net — дефолт, годится для большинства стикеров (персонажи, объекты).
# isnet-general-use — точнее на резких краях UI-плашек, HUD-окон.
# silueta — лёгкая, быстрее, но грубее.
KNOWN_MODELS = ("u2net", "isnet-general-use", "u2netp", "silueta", "u2net_human_seg")


@dataclass
class Sticker:
    path: Path
    scene_num: int


# ─── Сбор файлов ───────────────────────────────────────────────────────────


def _scene_num(path: Path) -> int | None:
    m = SCENE_RE.match(path.name)
    return int(m.group(1)) if m else None


def collect_stickers(stickers_dir: Path) -> list[Sticker]:
    """Собрать все `scene_NN_*.{jpg,png,webp}` прямо из stickers/ (без cutout/)."""
    out: list[Sticker] = []
    for p in sorted(stickers_dir.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in IMAGE_EXTS:
            continue
        num = _scene_num(p)
        if num is None:
            continue
        out.append(Sticker(path=p, scene_num=num))
    return out


def _parse_scene_list(value: str | None) -> set[int]:
    if not value:
        return set()
    return {int(x) for x in re.split(r"[,\s]+", value.strip()) if x}


def _resolve_target_dir(input_path: Path) -> Path:
    """Папка images/stickers/ для входа (файл или папка)."""
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
        "Скрипт ожидает вход внутри content/<миф>/images/stickers/."
    )


# ─── Обработка ─────────────────────────────────────────────────────────────


def _output_path(stick: Sticker, target_dir: Path) -> Path:
    """images/stickers/cutout/scene_NN_xxx.png."""
    stem = stick.path.stem
    return target_dir / f"{stem}.png"


def process_one(
    stick: Sticker,
    target_dir: Path,
    session,
    force: bool,
) -> tuple[Path, str]:
    """Обработать один стикер. Возвращает (output_path, status)."""
    from rembg import remove

    dst = _output_path(stick, target_dir)
    if dst.exists() and not force:
        return dst, "skip-exists"

    input_bytes = stick.path.read_bytes()
    output_bytes = remove(input_bytes, session=session)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(output_bytes)
    return dst, "ok"


# ─── Основной поток ────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Обрезка фона у стикеров через rembg (PNG с альфой в images/stickers/cutout/)."
    )
    parser.add_argument(
        "input",
        help="Папка images/stickers/, отдельный файл или glob внутри stickers/.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Обработать все стикеры. Без флага — превью на первых 2 сценах в cutout/_preview/.",
    )
    parser.add_argument(
        "--scene",
        default=None,
        metavar="N,M",
        help="Только указанные сцены (например '3,7,9').",
    )
    parser.add_argument(
        "--skip",
        default=None,
        metavar="N,M",
        help="Пропустить указанные сцены (например '5,11' — там фон часть смысла).",
    )
    parser.add_argument(
        "--model",
        default="u2net",
        choices=KNOWN_MODELS,
        help="Модель rembg (u2net по умолчанию; isnet-general-use лучше для UI-плашек).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Перезаписать существующие PNG в cutout/.",
    )
    args = parser.parse_args()

    # ─── Определяем вход ───────────────────────────────────────────────────
    input_path = Path(args.input).expanduser()

    # Allow glob like "scene_03_*.jpg"
    if "*" in str(input_path) or "?" in str(input_path):
        candidates = sorted(input_path.parent.glob(input_path.name))
        if not candidates:
            print(f"ERROR: glob {input_path} ничего не нашёл", file=sys.stderr)
            return 2
        # Берём общий родитель — папка stickers/
        stickers_dir = _resolve_target_dir(candidates[0])
        stickers: list[Sticker] = []
        for c in candidates:
            num = _scene_num(c)
            if num is None:
                print(f"  WARN пропускаю файл без scene_NN префикса: {c.name}", file=sys.stderr)
                continue
            stickers.append(Sticker(path=c, scene_num=num))
    elif input_path.is_file():
        stickers_dir = _resolve_target_dir(input_path)
        num = _scene_num(input_path)
        if num is None:
            print(f"ERROR: файл {input_path.name} не начинается с scene_NN_", file=sys.stderr)
            return 2
        stickers = [Sticker(path=input_path, scene_num=num)]
    elif input_path.is_dir():
        stickers_dir = _resolve_target_dir(input_path)
        stickers = collect_stickers(stickers_dir)
        if not stickers:
            print(f"ERROR: в {stickers_dir} нет scene_NN_*.{{jpg,png,webp}}", file=sys.stderr)
            return 1
    else:
        print(f"ERROR: не найден {input_path}", file=sys.stderr)
        return 2

    # ─── Фильтры --scene / --skip ──────────────────────────────────────────
    only = _parse_scene_list(args.scene)
    skip = _parse_scene_list(args.skip)
    if only:
        stickers = [s for s in stickers if s.scene_num in only]
    if skip:
        stickers = [s for s in stickers if s.scene_num not in skip]
    if not stickers:
        print("ERROR: после фильтрации не осталось ни одного стикера.", file=sys.stderr)
        return 1

    # ─── Превью vs полный прогон ───────────────────────────────────────────
    if args.execute:
        target_dir = stickers_dir / "cutout"
        mode = "execute"
        batch = stickers
    else:
        target_dir = stickers_dir / "cutout" / "_preview"
        mode = "preview"
        # Берём первые 2 уникальные сцены
        seen: set[int] = set()
        batch = []
        for s in stickers:
            if s.scene_num in seen:
                continue
            seen.add(s.scene_num)
            batch.append(s)
            if len(batch) >= 2:
                break

    print(f"stickers dir: {stickers_dir}")
    print(f"target dir:   {target_dir}  ({mode})")
    print(f"модель:       {args.model}")
    print(f"стикеров:     {len(batch)} из {len(stickers)}"
          + (f", всего в папке {len(collect_stickers(stickers_dir))}" if input_path.is_dir() else ""))
    print()

    # ─── Прогрев модели ────────────────────────────────────────────────────
    print(f"Загружаю модель rembg '{args.model}' (первый запуск качает ~170 МБ в ~/.u2net/)...")
    t0 = time.time()
    from rembg import new_session
    session = new_session(args.model)
    print(f"  модель загружена за {time.time() - t0:.1f}s")
    print()

    # ─── Обработка ─────────────────────────────────────────────────────────
    ok = 0
    skipped = 0
    failed = 0
    total_t0 = time.time()
    for stick in batch:
        t = time.time()
        try:
            dst, status = process_one(stick, target_dir, session=session, force=args.force)
        except Exception as exc:
            print(f"  FAIL scene_{stick.scene_num:02d}: {stick.path.name} — {exc}", file=sys.stderr)
            failed += 1
            continue
        elapsed = time.time() - t
        if status == "skip-exists":
            print(f"  SKIP scene_{stick.scene_num:02d}: {dst.name} уже существует (--force чтобы перезаписать)")
            skipped += 1
        else:
            rel = dst.relative_to(stickers_dir)
            print(f"  OK   scene_{stick.scene_num:02d}: {stick.path.name} -> {rel}  ({elapsed:.1f}s)")
            ok += 1

    total = time.time() - total_t0
    print()
    print(f"Готово: {ok} обработано, {skipped} пропущено, {failed} ошибок. Всего {total:.1f}s.")

    if mode == "preview":
        print()
        print(f"Превью лежит в {target_dir}.")
        print("Посмотри PNG в проводнике — если контуры выглядят чисто, запусти с --execute "
              "для полной партии. Папку _preview/ можно удалить вручную или она будет "
              "переиспользована при следующем превью.")
    else:
        print()
        print(f"PNG-стикеры с альфой готовы в {target_dir}.")
        print("Дальше enrich_<миф>.py должен ссылаться на cutout/scene_NN_*.png "
              "вместо оригинальных JPG.")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
