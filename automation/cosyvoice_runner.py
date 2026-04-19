"""
CosyVoice3 Runner — генерация 10 вариантов озвучки через локальную модель
Fun-CosyVoice3-0.5B с клонированием голоса (zero_shot режим).

Вызывается из webapp (`/api/regenerate-cosyvoice/<scenario>`) как subprocess,
чтобы UI не блокировался пока модель прогревается и генерирует варианты.

Использование (CLI):
    python automation/cosyvoice_runner.py \
        --scenario "Ящик Пандоры" \
        --base sentence_003 \
        --text "Он передал его людям и всё изменилось." \
        --variants 10 \
        --speed 1.1 \
        --prompt-wav "content/Ящик Пандоры/TTS.mp3" \
        --prompt-text "content/Ящик Пандоры/TTS.txt"

Выход:
    content/<scenario>/voiceover/audio/<base>/<base>_v1.mp3
    content/<scenario>/voiceover/audio/<base>/<base>_v2.mp3
    ...
    content/<scenario>/voiceover/audio/<base>/<base>_v10.mp3

Параллелизация:
    Модель загружается один раз, варианты генерируются последовательно
    (с разными seed). Конвертация WAV→MP3 идёт в ThreadPoolExecutor,
    чтобы не блокировать следующую инференс-итерацию.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = REPO_ROOT / "content"

COSYVOICE_REPO = REPO_ROOT / "external" / "CosyVoice"
COSYVOICE_MODEL_DIR = COSYVOICE_REPO / "pretrained_models" / "Fun-CosyVoice3-0.5B"

# Дефолтный prompt для клонирования — указан пользователем для всего проекта.
DEFAULT_PROMPT_WAV = CONTENT_DIR / "Ящик Пандоры" / "TTS.mp3"
DEFAULT_PROMPT_TXT = CONTENT_DIR / "Ящик Пандоры" / "TTS.txt"

DEFAULT_VARIANTS = 10
DEFAULT_SPEED = 1.1

# ffmpeg: сначала пробуем PATH, потом Remotion-бандл.
_REMOTION_FFMPEG = (
    REPO_ROOT / "remotion" / "node_modules" / "@remotion" /
    "compositor-win32-x64-msvc" / "ffmpeg.exe"
)


def find_ffmpeg() -> str | None:
    which = shutil.which("ffmpeg")
    if which:
        return which
    if _REMOTION_FFMPEG.exists():
        return str(_REMOTION_FFMPEG)
    return None


def load_cosyvoice_model():
    """Импортирует CosyVoice и грузит CosyVoice3 0.5B.

    Добавляет в sys.path сам репозиторий + Matcha-TTS, как рекомендовано
    в example.py. Явно логируем каждый шаг — если импорт падает, фронт
    покажет ошибку в tail лога.
    """
    sys.path.insert(0, str(COSYVOICE_REPO))
    sys.path.insert(0, str(COSYVOICE_REPO / "third_party" / "Matcha-TTS"))

    print(f"[cosyvoice] python={sys.executable}", flush=True)
    print(f"[cosyvoice] импортирую cosyvoice.cli.cosyvoice…", flush=True)
    from cosyvoice.cli.cosyvoice import AutoModel  # type: ignore
    from cosyvoice.utils.common import set_all_random_seed  # type: ignore

    print(f"[cosyvoice] загружаю модель из {COSYVOICE_MODEL_DIR}", flush=True)
    model = AutoModel(model_dir=str(COSYVOICE_MODEL_DIR))
    print(f"[cosyvoice] модель загружена, sample_rate={model.sample_rate}", flush=True)
    return model, set_all_random_seed


def _ensure_ascii_prompt_path(prompt_wav: Path) -> Path:
    """Возвращает путь к prompt-wav, гарантированно без не-ASCII символов.

    torchaudio/soundfile на Windows криво работают с путями, содержащими
    кириллицу и пробелы — они оборачивают вокруг C-библиотек, которые
    ожидают ASCII в file handle. Если в пути есть такое, копируем файл
    в короткий ASCII-путь и отдаём его.
    """
    path_str = str(prompt_wav)
    if path_str.isascii():
        return prompt_wav
    import hashlib  # noqa: PLC0415
    safe_dir = Path.home() / "cosyvoice-venv" / "prompts"
    safe_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.md5(path_str.encode("utf-8")).hexdigest()[:10]
    safe_path = safe_dir / f"prompt_{digest}{prompt_wav.suffix.lower()}"
    if not safe_path.exists() or safe_path.stat().st_mtime < prompt_wav.stat().st_mtime:
        shutil.copy2(prompt_wav, safe_path)
        print(f"[cosyvoice] prompt-wav скопирован в ASCII-путь: {safe_path}", flush=True)
    return safe_path


def save_wav_as_mp3(wav_path: Path, mp3_path: Path, ffmpeg: str | None) -> None:
    """Конвертирует WAV → MP3 через ffmpeg; при отсутствии ffmpeg оставляет WAV."""
    if ffmpeg is None:
        # Фолбэк: переименуем расширение, плеер в браузере всё равно умеет wav
        shutil.move(str(wav_path), str(mp3_path.with_suffix(".wav")))
        return
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(wav_path),
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(mp3_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode == 0:
        wav_path.unlink(missing_ok=True)
    else:
        print(f"[cosyvoice] ffmpeg fallback: {res.stderr.strip()[:200]}", flush=True)
        # Оставляем WAV рядом, чтобы не потерять результат
        shutil.move(str(wav_path), str(mp3_path.with_suffix(".wav")))


def generate_variants(
    scenario: str,
    base: str,
    text: str,
    variants: int,
    speed: float,
    prompt_wav: Path,
    prompt_text: str,
) -> dict:
    """Синхронная генерация N вариантов; сохраняет в content/<scenario>/voiceover/audio/<base>/.

    Примечание: сохраняем через soundfile, а не torchaudio — torchaudio.save()
    на Windows падает на путях с не-ASCII символами (в проекте папки типа
    «Ящик Пандоры»). soundfile/libsndfile корректно работает с UTF-8 путями.
    """
    import soundfile as sf  # type: ignore
    import numpy as np  # type: ignore

    scenario_dir = CONTENT_DIR / scenario
    # Все CosyVoice-генерации идут в review_sentences/<base>/. Это отделяет
    # свежесгенерированные варианты от legacy-файлов (scene_XX.mp3 из
    # ElevenLabs) и даёт аккуратное место под архив прежних попыток.
    out_dir = scenario_dir / "voiceover" / "audio" / "review_sentences" / base
    out_dir.mkdir(parents=True, exist_ok=True)

    # Если в этой папке уже лежат варианты от прошлого прогона — значит ни
    # один не подошёл (иначе пользователь не нажимал бы «Перегенерировать»).
    # Перемещаем их в outdated/<timestamp>/, чтобы сохранить историю попыток.
    existing = sorted(out_dir.glob(f"{base}_v*.mp3")) + sorted(out_dir.glob(f"{base}_v*.wav"))
    if existing:
        from datetime import datetime as _dt  # noqa: PLC0415
        ts = _dt.now().strftime("%Y%m%d_%H%M%S")
        outdated_dir = out_dir / "outdated" / ts
        outdated_dir.mkdir(parents=True, exist_ok=True)
        for old in existing:
            shutil.move(str(old), str(outdated_dir / old.name))
        print(
            f"[cosyvoice] перемещаю {len(existing)} старых вариантов в "
            f"outdated/{ts}/",
            flush=True,
        )

    ffmpeg = find_ffmpeg()
    model, set_all_random_seed = load_cosyvoice_model()
    sample_rate = model.sample_rate
    # CosyVoice3 frontend сам вызывает load_wav на prompt внутри инференса,
    # поэтому передаём ПУТЬ к файлу, а не предзагруженный тензор.
    # Путь может содержать не-ASCII (например, «Ящик Пандоры»), поэтому копируем
    # prompt в безопасную папку, если в исходном пути есть такие символы.
    prompt_path = _ensure_ascii_prompt_path(prompt_wav)

    # CosyVoice3 хочет text с префиксом инструкции для ассистента
    tts_text = text.strip()
    prompt_with_tag = f"You are a helpful assistant.<|endofprompt|>{prompt_text.strip()}"

    print(
        f"[cosyvoice] scenario={scenario!r} base={base!r} variants={variants} "
        f"speed={speed} sr={sample_rate}",
        flush=True,
    )

    results: list[str] = []
    errors: list[str] = []

    pool = ThreadPoolExecutor(max_workers=4)
    convert_futures = []

    for idx in range(1, variants + 1):
        seed = random.randint(1, 100_000_000)
        set_all_random_seed(seed)
        t0 = time.time()
        try:
            # inference_zero_shot отдаёт генератор; при stream=False — одна порция.
            first_chunk = None
            for j in model.inference_zero_shot(
                tts_text,
                prompt_with_tag,
                str(prompt_path),
                stream=False,
                speed=speed,
            ):
                first_chunk = j
                break
            if first_chunk is None:
                errors.append(f"v{idx}: пустой результат")
                continue

            wav_path = out_dir / f"{base}_v{idx}.wav"
            mp3_path = out_dir / f"{base}_v{idx}.mp3"
            # first_chunk["tts_speech"] — Tensor(channels, samples). soundfile
            # хочет (samples,) для моно или (samples, channels) для стерео.
            audio = first_chunk["tts_speech"].cpu().numpy()
            if audio.ndim == 2 and audio.shape[0] < audio.shape[1]:
                audio = audio.T  # (channels, samples) -> (samples, channels)
            if audio.ndim == 2 and audio.shape[1] == 1:
                audio = audio.squeeze(1)  # моно в 1D
            sf.write(str(wav_path), audio.astype(np.float32), sample_rate)
            dt = time.time() - t0
            print(f"[cosyvoice]   v{idx}: seed={seed} inf={dt:.1f}s", flush=True)

            convert_futures.append(
                pool.submit(save_wav_as_mp3, wav_path, mp3_path, ffmpeg)
            )
            results.append(mp3_path.name)
        except Exception as e:
            import traceback  # noqa: PLC0415
            tb = traceback.format_exc()
            errors.append(f"v{idx}: {type(e).__name__}: {e}")
            print(f"[cosyvoice]   v{idx} FAIL: {e}\n{tb}", flush=True)

    for fut in convert_futures:
        try:
            fut.result(timeout=60)
        except Exception as e:
            errors.append(f"mp3-convert: {e}")

    pool.shutdown(wait=True)

    report = {
        "scenario": scenario,
        "base": base,
        "variants_requested": variants,
        "variants_produced": len(results),
        "speed": speed,
        "sample_rate": sample_rate,
        "prompt_wav": str(prompt_wav),
        "prompt_text_preview": prompt_text.strip()[:120],
        "out_dir": str(out_dir.relative_to(REPO_ROOT)),
        "files": results,
        "errors": errors,
    }

    report_path = out_dir / "_cosyvoice_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[cosyvoice] DONE: {len(results)}/{variants} variants → {out_dir}", flush=True)
    return report


def resolve_prompt_text(arg_value: str | None, prompt_wav: Path) -> str:
    """Текст prompt: либо напрямую из CLI, либо читаем файл/сосед wav.txt."""
    if arg_value:
        candidate = Path(arg_value)
        if candidate.exists() and candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()
        return arg_value.strip()
    sibling = prompt_wav.with_suffix(".txt")
    if sibling.exists():
        return sibling.read_text(encoding="utf-8").strip()
    raise FileNotFoundError(
        f"Не задан prompt-text и рядом с {prompt_wav} нет файла .txt"
    )


def _preflight_check() -> list[str]:
    """Проверяет, что тяжёлые зависимости в Python есть. Возвращает список
    отсутствующих модулей — пустой значит всё ок.

    Важно: `matcha` сюда не включён — на Windows matcha-tts не ставится через
    pip (требует MSVC для C-extension). В CosyVoice-примерах matcha берётся
    через `sys.path.insert(third_party/Matcha-TTS)` — так и делаем в
    load_cosyvoice_model(). Preflight проверяет наличие matcha-папки ниже.
    """
    import importlib.util  # noqa: PLC0415
    required = ["torch", "torchaudio", "soundfile", "numpy", "librosa", "hyperpyyaml"]
    missing = []
    for name in required:
        if importlib.util.find_spec(name) is None:
            missing.append(name)
    # Папка Matcha-TTS должна физически присутствовать в репозитории
    matcha_dir = COSYVOICE_REPO / "third_party" / "Matcha-TTS" / "matcha"
    if not matcha_dir.exists():
        missing.append(f"matcha (папка {matcha_dir})")
    return missing


def main() -> int:
    # Самый первый вывод — до любых тяжёлых импортов. Это гарантирует, что лог
    # появится сразу, даже если дальше упадёт ModuleNotFoundError.
    import os  # noqa: PLC0415
    # Windows pipe по умолчанию в cp1251 — заставляем stdout/stderr писать UTF-8,
    # иначе русские кракозябры в логе webapp.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    print(
        f"[cosyvoice] runner старт pid={os.getpid()} python={sys.executable}",
        flush=True,
    )
    print(f"[cosyvoice] cwd={Path.cwd()}", flush=True)

    missing = _preflight_check()
    if missing:
        print(f"[cosyvoice] ОТСУТСТВУЮТ ЗАВИСИМОСТИ: {', '.join(missing)}", flush=True)
        print(
            "[cosyvoice] вариант 1 — поставить в текущий Python:\n"
            f"    {sys.executable} -m pip install -r "
            f"{COSYVOICE_REPO / 'requirements.txt'}\n"
            "[cosyvoice] вариант 2 — поднять отдельный venv с CosyVoice и указать его\n"
            "    Flask'у через переменную окружения COSYVOICE_PYTHON=C:\\path\\to\\python.exe",
            flush=True,
        )
        return 3
    print("[cosyvoice] preflight OK — все зависимости на месте", flush=True)
    parser = argparse.ArgumentParser(
        description="CosyVoice3 runner — 10 вариантов озвучки с клонированием голоса"
    )
    parser.add_argument("--scenario", required=True, help="Имя папки в content/")
    parser.add_argument("--base", required=True, help="База сцены, напр. sentence_003")
    parser.add_argument("--text", required=True, help="Текст для озвучки")
    parser.add_argument("--variants", type=int, default=DEFAULT_VARIANTS)
    parser.add_argument("--speed", type=float, default=DEFAULT_SPEED)
    parser.add_argument(
        "--prompt-wav",
        type=Path,
        default=DEFAULT_PROMPT_WAV,
        help="Референс-аудио для клонирования голоса",
    )
    parser.add_argument(
        "--prompt-text",
        default=None,
        help="Текст референс-аудио (файл или строка); по умолчанию — TTS.txt рядом с mp3",
    )
    args = parser.parse_args()

    if not args.prompt_wav.exists():
        print(f"[cosyvoice] ❌ не найден prompt-wav: {args.prompt_wav}", flush=True)
        return 2

    prompt_text = resolve_prompt_text(args.prompt_text, args.prompt_wav)

    report = generate_variants(
        scenario=args.scenario,
        base=args.base,
        text=args.text,
        variants=args.variants,
        speed=args.speed,
        prompt_wav=args.prompt_wav,
        prompt_text=prompt_text,
    )
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0 if report["variants_produced"] else 1


if __name__ == "__main__":
    sys.exit(main())
