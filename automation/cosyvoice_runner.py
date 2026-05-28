"""
CosyVoice3 Runner — генерация 10 вариантов озвучки через локальную модель
Fun-CosyVoice3-0.5B с клонированием голоса (zero_shot режим).

Вызывается из webapp как subprocess, чтобы UI не блокировался пока модель
прогревается и генерирует варианты.

Два режима:

1) Одиночный (`/api/regenerate-cosyvoice/<scenario>`):
       python automation/cosyvoice_runner.py \
           --scenario "Ящик Пандоры" \
           --base sentence_003 \
           --text "Он передал его людям и всё изменилось." \
           --variants 10 --speed 1.1 \
           --prompt-wav "content/Ящик Пандоры/TTS.mp3" \
           --prompt-text "content/Ящик Пандоры/TTS.txt"

2) Batch / `--auto` (`/api/cosyvoice-batch-start/<scenario>`):
       python automation/cosyvoice_runner.py --auto \
           --scenario "Персефона и Аид" \
           --bases sentence_001,sentence_002,sentence_003 \
           --variants 10 --speed 1.1 \
           --prompt-wav "content/Ящик Пандоры/TTS.mp3" \
           --prompt-text "content/Ящик Пандоры/TTS.txt"
   В этом режиме модель грузится ОДИН РАЗ и обходит все сцены по очереди.
   Текст каждой сцены читается из content/<scenario>/voiceover/texts/<base>.txt.
   Прогресс пишется в content/<scenario>/voiceover/audio/_cosyvoice_batch.json,
   общий лог — _cosyvoice_batch.log рядом.

Выход (одинаковый для обоих режимов):
    content/<scenario>/voiceover/audio/review_sentences/<base>/<base>_v{1..10}.mp3
    content/<scenario>/voiceover/audio/review_sentences/<base>/_cosyvoice_report.json
    content/<scenario>/voiceover/audio/review_sentences/<base>/_cosyvoice_runner.log

Параллелизация:
    Модель загружается один раз (в auto-режиме — на весь батч),
    варианты внутри сцены генерируются последовательно с разными seed.
    Конвертация WAV→MP3 идёт в ThreadPoolExecutor, чтобы не блокировать
    следующую инференс-итерацию.
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

# Дефолтный prompt — Макс Энергичный из assets/TTS/Макс/. Раньше дефолт
# тянулся из content/Ящик Пандоры/, но теперь голоса живут в общем каталоге
# assets/TTS/<voice>/{TTS.mp3,TTS.txt}, и webapp передаёт runner'у конкретный
# выбранный голос через --prompt-wav / --prompt-text. Дефолт нужен только для
# вызовов без флагов.
DEFAULT_VOICE_DIR = REPO_ROOT / "assets" / "TTS" / "Макс"
DEFAULT_PROMPT_WAV = DEFAULT_VOICE_DIR / "TTS.mp3"
DEFAULT_PROMPT_TXT = DEFAULT_VOICE_DIR / "TTS.txt"

DEFAULT_VARIANTS = 10
DEFAULT_SPEED = 1.1

# ffmpeg — берётся из системного PATH (на рабочей машине лежит в
# external/ffmpeg/ffmpeg-8.1-full_build-shared/bin/ и добавлен в PATH).


def find_ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


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
    t0 = time.time()
    model = AutoModel(model_dir=str(COSYVOICE_MODEL_DIR))
    print(
        f"[cosyvoice] модель загружена за {time.time() - t0:.1f}s, "
        f"sample_rate={model.sample_rate}",
        flush=True,
    )
    return model, set_all_random_seed


def _shatter_determinism(model) -> None:
    """Разрушает детерминизм, внесённый CosyVoice при загрузке модели.

    CosyVoice в конструкторе CausalConditionalCFM делает set_all_random_seed(0)
    и кеширует `self.rand_noise` — фиксированный гауссовский тензор. Из-за
    этого:
      (а) первый random.randint(...) всегда возвращает одно и то же значение
          (Python random был только что сброшен на seed(0)), поэтому и все
          последующие — тоже; seeds для вариантов повторяются между запусками
          и каждый запуск даёт побайтово ИДЕНТИЧНЫЕ mp3;
      (б) диффузионный шум `z` в flow_matching — это срез закешированного
          тензора, одинаковый при каждом инференсе.

    Фикс: (1) реседим Python random из системной энтропии, чтобы seed-ы
    реально различались между запусками; (2) перегенерируем rand_noise
    на каждый старт runner'а, чтобы акустические детали отличались.

    Вызывается ОДИН РАЗ после загрузки модели — для batch-режима этого
    достаточно: внутри одного процесса random.randint() даст разные seed-ы
    для всех сцен, а rand_noise остаётся свежим тензором (но фиксированным
    на весь батч — это нормально, варьируется через seed).
    """
    import torch as _torch  # noqa: PLC0415
    random.seed()  # no-arg → os.urandom
    try:
        cfm = None
        for attr in ("model", "flow"):
            obj = model
            for step in attr.split("."):
                obj = getattr(obj, step, None)
                if obj is None:
                    break
            if obj is not None and hasattr(obj, "decoder") and hasattr(obj.decoder, "rand_noise"):
                cfm = obj.decoder
                break
            if obj is not None and hasattr(obj, "rand_noise"):
                cfm = obj
                break
        if cfm is not None:
            old_shape = cfm.rand_noise.shape
            cfm.rand_noise = _torch.randn(old_shape)
            print(
                f"[cosyvoice] пересоздал rand_noise {tuple(old_shape)} — "
                f"разрушаю детерминизм",
                flush=True,
            )
        else:
            print(
                "[cosyvoice] не нашёл CausalConditionalCFM.rand_noise — "
                "варианты могут звучать похоже",
                flush=True,
            )
    except Exception as e:
        print(f"[cosyvoice] не удалось подменить rand_noise: {e}", flush=True)


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
    *,
    model=None,
    set_seed_fn=None,
    progress_cb=None,
) -> dict:
    """Синхронная генерация N вариантов; сохраняет в
    content/<scenario>/voiceover/audio/review_sentences/<base>/.

    Параметры `model` / `set_seed_fn` опциональны — если переданы (auto-режим
    с переиспользованием уже прогретой модели), функция НЕ грузит её заново
    и НЕ дёргает _shatter_determinism (это уже было сделано после первого
    load в run_batch). Если не переданы (одиночный режим) — грузим и
    разрушаем детерминизм здесь, как раньше.

    `progress_cb(produced_count)` вызывается после каждого готового варианта —
    auto-режим использует это для обновления общего batch-статус-файла.

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
    if model is None:
        # Одиночный режим: грузим модель и разрушаем детерминизм здесь.
        # В auto-режиме это уже сделано в run_batch ОДИН раз на весь батч.
        model, set_seed_fn = load_cosyvoice_model()
        _shatter_determinism(model)
    elif set_seed_fn is None:
        raise ValueError("если передан model, нужен и set_seed_fn")
    set_all_random_seed = set_seed_fn
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
            # Прогресс-колбэк: auto-режим обновит общий batch-статус, чтобы
            # фронт видел движение пипсов даже внутри одной сцены.
            if progress_cb is not None:
                try:
                    progress_cb(len(results))
                except Exception as cb_err:  # noqa: BLE001
                    print(f"[cosyvoice] progress_cb error: {cb_err}", flush=True)
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


# ── Batch / auto-режим ──────────────────────────────────────────────────────

def batch_status_path(scenario: str) -> Path:
    """Где лежит общий статус-файл прогона: read'ит фронт через
    /api/cosyvoice-batch-status."""
    return CONTENT_DIR / scenario / "voiceover" / "audio" / "_cosyvoice_batch.json"


def batch_log_path(scenario: str) -> Path:
    """Лог batch-прогона: один общий файл на весь auto-запуск, отдельно
    от per-scene логов (review_sentences/<base>/_cosyvoice_runner.log)."""
    return CONTENT_DIR / scenario / "voiceover" / "audio" / "_cosyvoice_batch.log"


def read_sentence_text(scenario: str, base: str) -> str:
    """Читает текст сцены из voiceover/texts/<base>.txt.
    В одиночном режиме текст приходит CLI-параметром, в auto-режиме —
    тянется из файла, чтобы не передавать гигабайт через argparse."""
    txt_path = CONTENT_DIR / scenario / "voiceover" / "texts" / f"{base}.txt"
    if not txt_path.exists():
        raise FileNotFoundError(f"нет текста сцены: {txt_path}")
    text = txt_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"пустой файл текста: {txt_path}")
    return text


def write_batch_status(path: Path, payload: dict) -> None:
    """Атомарный writer статуса: пишем во временный файл рядом и переименовываем,
    чтобы фронт никогда не прочитал полупустой JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = {**payload, "updated_at": time.time()}
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    # На Windows os.replace атомарен и поверх существующего файла.
    import os as _os  # noqa: PLC0415
    _os.replace(tmp, path)


def run_batch(args, prompt_text: str) -> int:
    """Auto-режим: грузим модель ОДИН раз и идём по списку сцен из --bases.

    Любая сцена может упасть — продолжаем со следующей; финальный exit-code
    — 1, если был хотя бы один failure (но файлы успешных сцен останутся
    на диске, фронт сможет их использовать)."""
    bases = [b.strip() for b in (args.bases or "").split(",") if b.strip()]
    if not bases:
        print("[cosyvoice-batch] ❌ список --bases пуст", flush=True)
        return 2

    status_path = batch_status_path(args.scenario)
    started_at = time.time()
    base_status = {
        "scenario": args.scenario,
        "model": "Fun-CosyVoice3-0.5B",
        "speed": args.speed,
        "variants": args.variants,
        "total": len(bases),
        "queue": bases,
        "started_at": started_at,
        "active": True,
        "done": False,
        "current_base": None,
        "current_index": 0,
        "current_produced": 0,
        "completed_bases": [],
        "failed": [],
        "error": None,
    }
    write_batch_status(status_path, base_status)

    # ── Прогрев модели ──
    try:
        model, set_seed_fn = load_cosyvoice_model()
        _shatter_determinism(model)
    except Exception as e:
        import traceback as _tb  # noqa: PLC0415
        tb = _tb.format_exc()
        print(f"[cosyvoice-batch] ❌ load_cosyvoice_model упал: {e}\n{tb}", flush=True)
        write_batch_status(status_path, {
            **base_status,
            "active": False,
            "done": True,
            "error": f"load_model: {type(e).__name__}: {e}",
        })
        return 3

    completed: list[str] = []
    failed: list[dict] = []

    print(
        f"[cosyvoice-batch] старт: scenario={args.scenario!r} bases={len(bases)} "
        f"speed={args.speed} variants={args.variants}",
        flush=True,
    )

    for i, base in enumerate(bases):
        # Обновляем общий статус ДО старта сцены — фронт сразу увидит,
        # на какой строчке pip-индикатор должен крутиться.
        write_batch_status(status_path, {
            **base_status,
            "current_base": base,
            "current_index": i,
            "current_produced": 0,
            "completed_bases": list(completed),
            "failed": list(failed),
        })

        def _on_progress(produced: int, _b=base, _i=i) -> None:
            write_batch_status(status_path, {
                **base_status,
                "current_base": _b,
                "current_index": _i,
                "current_produced": produced,
                "completed_bases": list(completed),
                "failed": list(failed),
            })

        try:
            text = read_sentence_text(args.scenario, base)
            print(
                f"[cosyvoice-batch] [{i + 1}/{len(bases)}] {base}: "
                f"{text[:60]!r}…",
                flush=True,
            )
            generate_variants(
                scenario=args.scenario,
                base=base,
                text=text,
                variants=args.variants,
                speed=args.speed,
                prompt_wav=args.prompt_wav,
                prompt_text=prompt_text,
                model=model,
                set_seed_fn=set_seed_fn,
                progress_cb=_on_progress,
            )
            completed.append(base)
        except Exception as e:
            import traceback as _tb  # noqa: PLC0415
            tb = _tb.format_exc()
            print(f"[cosyvoice-batch] FAIL {base}: {e}\n{tb}", flush=True)
            failed.append({"base": base, "error": f"{type(e).__name__}: {e}"})

    elapsed = time.time() - started_at
    print(
        f"[cosyvoice-batch] DONE: ok={len(completed)} fail={len(failed)} "
        f"за {elapsed:.1f}s",
        flush=True,
    )

    write_batch_status(status_path, {
        **base_status,
        "active": False,
        "done": True,
        "current_base": None,
        "current_index": len(bases),
        "current_produced": 0,
        "completed_bases": completed,
        "failed": failed,
        "elapsed_sec": elapsed,
    })

    return 0 if not failed else 1


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
        description="CosyVoice3 runner — генерация вариантов озвучки с клонированием голоса"
    )
    parser.add_argument("--scenario", required=True, help="Имя папки в content/")
    # В одиночном режиме --base/--text обязательны; в --auto обязателен --bases.
    # Делаем required=False и проверяем вручную ниже, чтобы дать понятные ошибки.
    parser.add_argument("--base", help="База сцены (одиночный режим), напр. sentence_003")
    parser.add_argument("--text", help="Текст для озвучки (одиночный режим)")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Batch-режим: загружаем модель один раз и обходим список --bases",
    )
    parser.add_argument(
        "--bases",
        default=None,
        help="Запятыми разделённый список баз сцен для --auto, напр. "
             "sentence_001,sentence_002,sentence_003. Тексты тянутся из "
             "content/<scenario>/voiceover/texts/<base>.txt.",
    )
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

    if args.auto:
        if not args.bases:
            print("[cosyvoice] ❌ режим --auto требует --bases <список через запятую>", flush=True)
            return 2
        return run_batch(args, prompt_text)

    if not args.base or not args.text:
        print("[cosyvoice] ❌ одиночный режим требует --base и --text (или используй --auto)", flush=True)
        return 2

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
