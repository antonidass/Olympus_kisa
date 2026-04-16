from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_QWEN_REPO = REPO_ROOT / "external" / "Qwen3-TTS"
if LOCAL_QWEN_REPO.exists():
    sys.path.insert(0, str(LOCAL_QWEN_REPO))

import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel


MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "output" / "qwen3_tts_voice_clone"


def choose_file_via_dialog() -> Optional[Path]:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    file_path = filedialog.askopenfilename(
        title="Select reference mp3/wav for Qwen3-TTS",
        filetypes=[
            ("Audio", "*.mp3 *.wav *.flac *.m4a *.ogg"),
            ("MP3", "*.mp3"),
            ("WAV", "*.wav"),
            ("All files", "*.*"),
        ],
    )
    root.destroy()
    return Path(file_path) if file_path else None


def prompt_audio_path(cli_value: Optional[str]) -> Path:
    if cli_value:
        audio_path = Path(cli_value).expanduser().resolve()
        if not audio_path.exists():
            raise FileNotFoundError(f"Reference audio not found: {audio_path}")
        return audio_path

    selected = choose_file_via_dialog()
    if selected:
        return selected.resolve()

    typed = input("Path to mp3/wav: ").strip().strip('"')
    if not typed:
        raise ValueError("Reference audio path is required.")
    audio_path = Path(typed).expanduser().resolve()
    if not audio_path.exists():
        raise FileNotFoundError(f"Reference audio not found: {audio_path}")
    return audio_path


def detect_reference_text(audio_path: Path, cli_value: Optional[str], xvec_only: bool) -> Optional[str]:
    if cli_value is not None:
        return cli_value.strip() or None

    sibling_txt = audio_path.with_suffix(".txt")
    if sibling_txt.exists():
        text = sibling_txt.read_text(encoding="utf-8").strip()
        if text:
            print(f"Using reference transcript from: {sibling_txt}")
            return text

    if xvec_only:
        return None

    print("No transcript was found next to the audio file.")
    print("Paste the exact transcript of the reference clip for better voice cloning.")
    print("Leave it empty to fall back to x_vector_only_mode=True.")
    typed = input("ref_text: ").strip()
    return typed or None


def collect_sentences_from_file(path: Path) -> List[str]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line]


def collect_sentences_interactive() -> List[str]:
    print("Enter sentences to synthesize, one per line.")
    print("Submit an empty line to finish.")
    items: List[str] = []
    while True:
        line = input("> ").strip()
        if not line:
            break
        items.append(line)
    if not items:
        raise ValueError("At least one sentence is required.")
    return items


def choose_dtype() -> torch.dtype:
    if not torch.cuda.is_available():
        return torch.float32
    if hasattr(torch.cuda, "is_bf16_supported") and torch.cuda.is_bf16_supported():
        return torch.bfloat16
    return torch.float16


def choose_device(cli_value: Optional[str]) -> str:
    if cli_value:
        return cli_value
    return "cuda:0" if torch.cuda.is_available() else "cpu"


def choose_ffmpeg() -> Optional[str]:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def sanitize_filename(text: str, index: int) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_", " ") else "_" for ch in text)
    cleaned = "_".join(cleaned.split())
    cleaned = cleaned[:48].strip("_") or f"line_{index:02d}"
    return f"{index:02d}_{cleaned}"


def export_mp3(wav_path: Path, mp3_path: Path) -> bool:
    ffmpeg_exe = choose_ffmpeg()
    if not ffmpeg_exe:
        return False
    subprocess.run(
        [
            ffmpeg_exe,
            "-y",
            "-i",
            str(wav_path),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(mp3_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def write_manifest(
    out_dir: Path,
    ref_audio: Path,
    ref_text: Optional[str],
    sentences: Iterable[str],
    language: str,
    device: str,
    dtype: torch.dtype,
    xvec_only: bool,
) -> None:
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "model_id": MODEL_ID,
        "ref_audio": str(ref_audio),
        "ref_text": ref_text,
        "language": language,
        "device": device,
        "dtype": str(dtype),
        "x_vector_only_mode": xvec_only,
        "sentences": list(sentences),
    }
    (out_dir / "manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Voice clone script for Qwen3-TTS-12Hz-1.7B-Base using a reference mp3/wav."
    )
    parser.add_argument("--ref-audio", help="Path to reference mp3/wav.")
    parser.add_argument("--ref-text", help="Transcript of the reference audio.")
    parser.add_argument("--sentences-file", help="Text file with one sentence per line.")
    parser.add_argument("--language", default="Auto", help="Target language, e.g. Auto, Russian, English.")
    parser.add_argument("--device", help="Force model device, e.g. cuda:0 or cpu.")
    parser.add_argument("--output-dir", help="Directory for generated files.")
    parser.add_argument("--xvec-only", action="store_true", help="Clone using speaker embedding only.")
    parser.add_argument("--flash-attn", action="store_true", help="Enable flash_attention_2 when installed.")
    parser.add_argument("--skip-mp3", action="store_true", help="Only save WAV outputs.")
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-new-tokens", type=int, default=2048)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    ref_audio = prompt_audio_path(args.ref_audio)
    ref_text = detect_reference_text(ref_audio, args.ref_text, args.xvec_only)
    xvec_only = args.xvec_only or not ref_text

    if xvec_only and not args.xvec_only:
        print("ref_text was not provided, switching to x_vector_only_mode=True.")

    if args.sentences_file:
        sentences = collect_sentences_from_file(Path(args.sentences_file).expanduser().resolve())
        if not sentences:
            raise ValueError("The sentences file does not contain any non-empty lines.")
    else:
        sentences = collect_sentences_interactive()

    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else DEFAULT_OUTPUT_ROOT / datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    device = choose_device(args.device)
    dtype = choose_dtype()
    attn_impl = "flash_attention_2" if args.flash_attn else None

    print(f"Loading model {MODEL_ID}")
    print(f"Device: {device}, dtype: {dtype}, flash_attn: {bool(attn_impl)}")
    model = Qwen3TTSModel.from_pretrained(
        MODEL_ID,
        device_map=device,
        dtype=dtype,
        attn_implementation=attn_impl,
    )

    prompt_items = model.create_voice_clone_prompt(
        ref_audio=str(ref_audio),
        ref_text=ref_text,
        x_vector_only_mode=xvec_only,
    )

    wavs, sr = model.generate_voice_clone(
        text=sentences,
        language=[args.language] * len(sentences),
        voice_clone_prompt=prompt_items,
        max_new_tokens=args.max_new_tokens,
        do_sample=True,
        top_k=args.top_k,
        top_p=args.top_p,
        temperature=args.temperature,
        repetition_penalty=1.05,
        subtalker_dosample=True,
        subtalker_top_k=args.top_k,
        subtalker_top_p=args.top_p,
        subtalker_temperature=args.temperature,
    )

    mp3_supported = False
    for index, (sentence, wav) in enumerate(zip(sentences, wavs), start=1):
        stem = sanitize_filename(sentence, index)
        wav_path = output_dir / f"{stem}.wav"
        sf.write(wav_path, wav, sr)
        print(f"Saved WAV: {wav_path}")

        if not args.skip_mp3:
            mp3_path = output_dir / f"{stem}.mp3"
            try:
                mp3_supported = export_mp3(wav_path, mp3_path) or mp3_supported
                if mp3_supported:
                    print(f"Saved MP3: {mp3_path}")
            except Exception as exc:
                print(f"Could not create MP3 for {wav_path.name}: {exc}")

    write_manifest(output_dir, ref_audio, ref_text, sentences, args.language, device, dtype, xvec_only)

    if not args.skip_mp3 and not mp3_supported:
        print("MP3 export skipped: ffmpeg/imageio-ffmpeg is not available. WAV files were still created.")

    print(f"Done. Outputs are in: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
