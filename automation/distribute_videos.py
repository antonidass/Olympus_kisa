"""
Distribute Videos — переименование Flow-видео по сценам на основе первого кадра.

Сценарий использования:
1. В `content/<миф>/images/approved_images/` уже лежит по одному выбранному
   кадру на сцену (`scene_NN_vK.jpg|jpeg|png|webp`).
2. В `content/<миф>/video/` лежат сырые mp4 из Flow с произвольными именами.
3. Скрипт извлекает первый кадр из каждого видео, сравнивает его с approved
   image каждой сцены и переименовывает ролики в `scene_NN_vM.mp4`.

По умолчанию работает в dry-run режиме и только печатает план.
С `--execute` выполняет безопасное двухшаговое переименование.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
SCENE_RENAMED_PREFIX = "scene_"
SCENE_VIDEO_RE = re.compile(r"^scene_(?P<scene>\d+)_v(?P<variant>\d+)\.", re.IGNORECASE)


@dataclass(frozen=True)
class Fingerprint:
    color_pixels: tuple[int, ...]
    gray_pixels: tuple[int, ...]
    ahash_bits: int
    ahash_len: int


@dataclass(frozen=True)
class SceneImage:
    scene_num: int
    source_path: Path
    fingerprint: Fingerprint


@dataclass(frozen=True)
class VideoSample:
    video_path: Path
    frame_path: Path
    fingerprint: Fingerprint


@dataclass(frozen=True)
class MatchResult:
    scene_num: int
    score: float
    second_best_score: float

    @property
    def margin(self) -> float:
        return self.second_best_score - self.score


def find_ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def detect_myth_dir(path: Path) -> Path | None:
    candidates = [path]
    if path.is_file():
        candidates.append(path.parent)
    candidates.extend(path.parents)
    for candidate in candidates:
        if (candidate / "images" / "approved_images").exists():
            return candidate
    return None


def parse_scene_num(name: str) -> int | None:
    lower = name.lower()
    if not lower.startswith("scene_"):
        return None
    digits = []
    for ch in lower[6:]:
        if ch.isdigit():
            digits.append(ch)
        else:
            break
    if not digits:
        return None
    return int("".join(digits))


def collect_scene_images(approved_dir: Path) -> list[SceneImage]:
    scenes: dict[int, Path] = {}
    for path in sorted(approved_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue
        scene_num = parse_scene_num(path.stem)
        if scene_num is None:
            continue
        scenes.setdefault(scene_num, path)

    results: list[SceneImage] = []
    for scene_num, path in sorted(scenes.items()):
        results.append(
            SceneImage(
                scene_num=scene_num,
                source_path=path,
                fingerprint=build_fingerprint(path),
            )
        )
    return results


def collect_videos(video_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in video_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in VIDEO_EXTS
        and not path.name.lower().startswith(SCENE_RENAMED_PREFIX)
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def filter_duplicate_videos(
    video_dir: Path,
    video_paths: list[Path],
    execute: bool,
) -> tuple[list[Path], int]:
    raw_paths = {path.resolve() for path in video_paths}
    seen_hashes: set[str] = set()

    for path in sorted(video_dir.iterdir()):
        if (
            path.is_file()
            and path.suffix.lower() in VIDEO_EXTS
            and path.resolve() not in raw_paths
        ):
            seen_hashes.add(file_sha256(path))

    unique_paths: list[Path] = []
    skipped = 0
    for path in video_paths:
        digest = file_sha256(path)
        if digest in seen_hashes:
            skipped += 1
            if execute:
                path.unlink()
            continue
        seen_hashes.add(digest)
        unique_paths.append(path)

    return unique_paths, skipped


def next_scene_variants(video_dir: Path) -> dict[int, int]:
    max_variants: dict[int, int] = {}
    for path in video_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in VIDEO_EXTS:
            continue
        match = SCENE_VIDEO_RE.match(path.name)
        if not match:
            continue
        scene_num = int(match.group("scene"))
        variant_num = int(match.group("variant"))
        max_variants[scene_num] = max(max_variants.get(scene_num, 0), variant_num)
    return {scene_num: variant_num + 1 for scene_num, variant_num in max_variants.items()}


def build_fingerprint(image_path: Path) -> Fingerprint:
    with Image.open(image_path) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        fit_rgb = ImageOps.fit(img, (24, 42), method=Image.Resampling.LANCZOS)
        fit_gray = ImageOps.fit(img.convert("L"), (24, 42), method=Image.Resampling.LANCZOS)
        hash_img = ImageOps.fit(img.convert("L"), (16, 16), method=Image.Resampling.LANCZOS)

        color_pixels = tuple(fit_rgb.tobytes())
        gray_pixels = tuple(fit_gray.tobytes())
        ahash_bits = average_hash_bits(hash_img)
        return Fingerprint(
            color_pixels=color_pixels,
            gray_pixels=gray_pixels,
            ahash_bits=ahash_bits,
            ahash_len=16 * 16,
        )


def average_hash_bits(gray_img: Image.Image) -> int:
    pixels = list(gray_img.tobytes())
    threshold = sum(pixels) / len(pixels)
    bits = 0
    for idx, value in enumerate(pixels):
        if value >= threshold:
            bits |= 1 << idx
    return bits


def extract_first_frame(video_path: Path, dest_png: Path, ffmpeg: str) -> None:
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        str(dest_png),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not dest_png.exists():
        raise RuntimeError(
            f"ffmpeg не смог извлечь кадр из {video_path.name}: "
            f"{res.stderr.strip()[:300]}"
        )


def sample_videos(video_paths: list[Path], ffmpeg: str, frame_dir: Path) -> list[VideoSample]:
    samples: list[VideoSample] = []
    for idx, video_path in enumerate(video_paths, start=1):
        frame_path = frame_dir / f"frame_{idx:03d}.png"
        extract_first_frame(video_path, frame_path, ffmpeg)
        samples.append(
            VideoSample(
                video_path=video_path,
                frame_path=frame_path,
                fingerprint=build_fingerprint(frame_path),
            )
        )
    return samples


def normalized_mae(values_a: tuple[int, ...], values_b: tuple[int, ...], scale: int) -> float:
    total = 0
    for av, bv in zip(values_a, values_b):
        total += abs(av - bv)
    return total / (len(values_a) * scale)


def normalized_hamming(bits_a: int, bits_b: int, bit_count: int) -> float:
    return (bits_a ^ bits_b).bit_count() / bit_count


def compare_fingerprints(a: Fingerprint, b: Fingerprint) -> float:
    color_score = normalized_mae(a.color_pixels, b.color_pixels, 255)
    gray_score = normalized_mae(a.gray_pixels, b.gray_pixels, 255)
    hash_score = normalized_hamming(a.ahash_bits, b.ahash_bits, a.ahash_len)
    return color_score * 0.65 + gray_score * 0.25 + hash_score * 0.10


def match_video(sample: VideoSample, scenes: list[SceneImage]) -> MatchResult:
    ranked = sorted(
        (
            (compare_fingerprints(sample.fingerprint, scene.fingerprint), scene.scene_num)
            for scene in scenes
        ),
        key=lambda item: (item[0], item[1]),
    )
    best_score, best_scene = ranked[0]
    second_score = ranked[1][0] if len(ranked) > 1 else 1.0
    return MatchResult(
        scene_num=best_scene,
        score=best_score,
        second_best_score=second_score,
    )


def plan_renames(
    samples: list[VideoSample],
    matches: dict[Path, MatchResult],
    video_dir: Path,
) -> list[tuple[Path, Path, MatchResult]]:
    grouped: dict[int, list[tuple[VideoSample, MatchResult]]] = {}
    for sample in samples:
        match = matches[sample.video_path]
        grouped.setdefault(match.scene_num, []).append((sample, match))

    plan: list[tuple[Path, Path, MatchResult]] = []
    next_variants = next_scene_variants(video_dir)
    for scene_num, entries in sorted(grouped.items()):
        entries.sort(key=lambda item: (item[1].score, item[0].video_path.name.lower()))
        variant_idx = next_variants.get(scene_num, 1)
        for sample, match in entries:
            dst = sample.video_path.with_name(f"scene_{scene_num:02d}_v{variant_idx}.mp4")
            plan.append((sample.video_path, dst, match))
            variant_idx += 1
    return plan


def execute_renames(plan: list[tuple[Path, Path, MatchResult]]) -> None:
    temp_moves: list[tuple[Path, Path]] = []
    for idx, (src, _, _) in enumerate(plan, start=1):
        tmp = src.with_name(f"__tmp_rename_{idx:03d}{src.suffix.lower()}")
        if tmp.exists():
            raise RuntimeError(f"Временный файл уже существует: {tmp.name}")
        src.rename(tmp)
        temp_moves.append((tmp, src))

    try:
        for idx, (_, dst, _) in enumerate(plan, start=1):
            tmp, _old_src = temp_moves[idx - 1]
            if dst.exists():
                raise RuntimeError(f"Целевой файл уже существует: {dst.name}")
            tmp.rename(dst)
    except Exception:
        for tmp, original in reversed(temp_moves):
            if tmp.exists() and not original.exists():
                tmp.rename(original)
        raise


def print_plan(
    plan: list[tuple[Path, Path, MatchResult]],
    scene_count: int,
    sample_count: int,
) -> None:
    print(f"Сцен с approved image: {scene_count}")
    print(f"Видео для разметки:    {sample_count}")
    print()
    print("=== ПЛАН ПЕРЕИМЕНОВАНИЯ ===")
    for src, dst, match in plan:
        label = confidence_label(match.score, match.margin)
        print(
            f"{dst.name:16}  {label}  <=  {src.name}  "
            f"(score={match.score:.4f}, margin={match.margin:.4f})"
        )
    print()

    weak = [(src, dst, m) for src, dst, m in plan if confidence_label(m.score, m.margin) != "OK"]
    if weak:
        print("ПРОВЕРИТЬ ВРУЧНУЮ:")
        for src, dst, match in weak:
            print(
                f"  {dst.name} <= {src.name}  "
                f"(score={match.score:.4f}, margin={match.margin:.4f})"
            )
        print()


def confidence_label(score: float, margin: float) -> str:
    if score <= 0.090 and margin >= 0.020:
        return "OK"
    if score <= 0.140 and margin >= 0.010:
        return "WARN"
    return "CHECK"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Переименование Flow-видео по сценам через матч первого кадра к approved_images."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Папка video/ или любая папка внутри myth-dir, где лежат сырые видео",
    )
    parser.add_argument(
        "--myth-dir",
        type=Path,
        default=None,
        help="Папка мифа; по умолчанию определяется автоматически",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Выполнить переименование; без флага работает dry-run",
    )
    parser.add_argument(
        "--keep-frames",
        action="store_true",
        help="Не удалять временные PNG первых кадров",
    )
    args = parser.parse_args()

    input_path = args.input
    if not input_path.exists():
        print(f"ERROR: не найдено {input_path}", file=sys.stderr)
        return 1

    myth_dir = args.myth_dir or detect_myth_dir(input_path)
    if myth_dir is None:
        print(
            "ERROR: не удалось определить myth-dir. Укажи --myth-dir вручную.",
            file=sys.stderr,
        )
        return 1

    video_dir = input_path if input_path.is_dir() else input_path.parent
    approved_dir = myth_dir / "images" / "approved_images"
    if not approved_dir.exists():
        print(f"ERROR: не найдена папка {approved_dir}", file=sys.stderr)
        return 1

    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        print("ERROR: ffmpeg не найден в PATH", file=sys.stderr)
        return 1

    scenes = collect_scene_images(approved_dir)
    if not scenes:
        print(f"ERROR: нет approved images в {approved_dir}", file=sys.stderr)
        return 1

    videos = collect_videos(video_dir)
    if not videos:
        print(f"ERROR: нет сырых видео в {video_dir}", file=sys.stderr)
        return 1
    videos, skipped_duplicates = filter_duplicate_videos(
        video_dir,
        videos,
        execute=args.execute,
    )
    if skipped_duplicates:
        action = "удалено" if args.execute else "будет пропущено"
        print(f"Дубликатов видео по SHA256: {skipped_duplicates} ({action}).")
    if not videos:
        print("Нет новых уникальных видео для переименования.")
        return 0

    print(f"Папка мифа:     {myth_dir}")
    print(f"Approved image: {approved_dir}")
    print(f"Видео:          {video_dir}")
    print()

    with tempfile.TemporaryDirectory(prefix="bogi_video_match_") as temp_dir_str:
        frame_dir = Path(temp_dir_str)
        samples = sample_videos(videos, ffmpeg, frame_dir)
        matches = {sample.video_path: match_video(sample, scenes) for sample in samples}
        plan = plan_renames(samples, matches, video_dir)
        print_plan(plan, scene_count=len(scenes), sample_count=len(samples))

        if not args.execute:
            if args.keep_frames:
                debug_dir = video_dir / "_first_frames_debug"
                debug_dir.mkdir(parents=True, exist_ok=True)
                for sample in samples:
                    shutil.copy2(sample.frame_path, debug_dir / f"{sample.video_path.stem}.png")
                print(f"Сохранил debug-кадры в {debug_dir}")
            print("DRY-RUN. Запусти с --execute чтобы переименовать файлы.")
            return 0

        execute_renames(plan)

        if args.keep_frames:
            debug_dir = video_dir / "_first_frames_debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            for sample in samples:
                shutil.copy2(sample.frame_path, debug_dir / f"{sample.video_path.stem}.png")
            print(f"Сохранил debug-кадры в {debug_dir}")

    print("Готово: видео переименованы по сценам.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
