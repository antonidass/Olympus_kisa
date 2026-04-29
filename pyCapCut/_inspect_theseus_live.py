"""
Инспектор живого CapCut-драфта «Тесей и Минотавр» — печатает все эталонные
параметры монтажа канала (зум, шрифты, переходы, эффекты, SFX, громкости).

Запускать после ручных правок в CapCut, чтобы:
  1. Сверить — соответствует ли драфт зафиксированному `template_theseus.py`
  2. Получить актуальные значения для обновления `template_theseus.py`
  3. Подобрать `effect_id` нового перехода / эффекта для нового мифа

Использование:
    PYTHONIOENCODING=utf-8 python pyCapCut/_inspect_theseus_live.py

CapCut закрывать НЕ обязательно — скрипт только читает draft_content.json.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

BS = chr(92)  # backslash, чтобы избежать SyntaxError в строках

DRAFT_PATH = Path(
    os.path.expandvars(
        r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\Тесей и Минотавр\draft_content.json"
    )
)


def _basename(name: str) -> str:
    """Вытащить имя файла из строки (поддержка Windows и Unix разделителей)."""
    return name.replace(BS, "/").rsplit("/", 1)[-1]


def section(title: str) -> None:
    print()
    print("=" * 70)
    print(f" {title}")
    print("=" * 70)


def main() -> int:
    if not DRAFT_PATH.exists():
        print(f"ERROR: не найден драфт {DRAFT_PATH}")
        print("       Проверь что проект «Тесей и Минотавр» существует в CapCut")
        return 1

    print(f"Читаю: {DRAFT_PATH}")
    d = json.loads(DRAFT_PATH.read_text(encoding="utf-8"))
    mat = d["materials"]
    tracks = d["tracks"]

    # ─── 1. Зум видео-сегментов ─────────────────────────────────────────
    section("1. ЗУМ ВИДЕО-СЕГМЕНТОВ (масштаб + Y-смещение)")
    video_track = next(t for t in tracks if t["type"] == "video")
    scales_x = Counter()
    scales_y = Counter()
    y_offsets = Counter()
    for seg in video_track["segments"]:
        cs = seg.get("clip", {}).get("scale", {})
        tr = seg.get("clip", {}).get("transform", {})
        scales_x[round(cs.get("x", 1.0), 4)] += 1
        scales_y[round(cs.get("y", 1.0), 4)] += 1
        y_offsets[round(tr.get("y", 0.0), 4)] += 1
    print(f"   видео-сегментов: {len(video_track['segments'])}")
    print(f"   scale.x:      {dict(scales_x)}")
    print(f"   scale.y:      {dict(scales_y)}")
    print(f"   transform.y:  {dict(y_offsets)}")
    print(f"   → эталон:     scale={list(scales_x)[0]}  transform.y={list(y_offsets)[0]}")

    # ─── 2. Шрифты караоке-субтитров ────────────────────────────────────
    section("2. ШРИФТЫ И СУБТИТРЫ")
    texts = mat["texts"]
    print(f"   текстовых материалов: {len(texts)}")
    font_size_combos = Counter()
    for t in texts:
        try:
            c = json.loads(t.get("content", ""))
            for st in c.get("styles", []):
                font = st.get("font", {})
                fid = font.get("id") or font.get("path") or "?"
                size = st.get("size", "?")
                bold = st.get("useFontBold") or st.get("bold", False)
                # для путей оставляем только хвост (имя файла шрифта)
                if isinstance(fid, str) and (BS in fid or "/" in fid):
                    fid = _basename(fid)
                font_size_combos[(str(fid), size, bool(bold))] += 1
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
    print()
    for (font, size, bold), n in font_size_combos.most_common():
        kind = "интро" if "Forum" in font else ("основной караоке" if size == 12 else "?")
        print(f"   {font:35s}  size={size:3}  bold={bold}  ×{n}  ({kind})")

    # ─── 3. Переходы между сценами ──────────────────────────────────────
    section("3. ПЕРЕХОДЫ МЕЖДУ СЦЕНАМИ")
    trans_list = mat.get("transitions", [])
    trans_by_id = {t["id"]: t for t in trans_list}
    used = []
    for i, seg in enumerate(video_track["segments"]):
        for ref in seg.get("extra_material_refs", []):
            if ref in trans_by_id:
                tr = trans_by_id[ref]
                used.append(
                    (
                        i,
                        tr.get("name", "?"),
                        tr.get("effect_id", "?"),
                        tr.get("duration", 0) / 1_000_000,
                    )
                )
    print(f"   стыков с переходами: {len(used)}")
    summary = Counter()
    for _, name, eid, dur in used:
        summary[(name, eid, round(dur, 3))] += 1
    print()
    print("   Уникальные переходы (имя, effect_id, длительность, кол-во):")
    for (name, eid, dur), n in summary.most_common():
        print(f"     {name!r:30s}  effect_id={eid}  dur={dur}s  ×{n}")
    print()
    print("   Точная привязка (стык_сцен → переход):")
    for i, name, _, dur in used:
        print(f"     стык {i+1:02d}-{i+2:02d}  →  {name!r:30s}  ({dur}s)")

    # ─── 4. Видео-эффекты ────────────────────────────────────────────────
    section("4. ВИДЕО-ЭФФЕКТЫ (плёнка, виньетки, финальный круг)")
    veffects = mat.get("video_effects", [])
    print(f"   объектов в materials.video_effects: {len(veffects)}")
    for ve in veffects:
        print(
            f"     name={ve.get('name')!r}  effect_id={ve.get('effect_id')}  "
            f"category={ve.get('category_name')}  apply_target_type={ve.get('apply_target_type')}"
        )
    effect_tracks = [t for t in tracks if t["type"] == "effect"]
    if effect_tracks:
        print()
        for et in effect_tracks:
            print(f"   effect-track сегментов: {len(et['segments'])}")
            for seg in et["segments"]:
                mid = seg.get("material_id")
                ts = seg.get("target_timerange", {})
                start = ts.get("start", 0) / 1_000_000
                dur = ts.get("duration", 0) / 1_000_000
                ve = next((v for v in veffects if v["id"] == mid), None)
                vname = ve.get("name") if ve else "?"
                print(f"     start={start:.2f}s  dur={dur:.2f}s  →  {vname!r}")

    # ─── 5. Громкости и SFX ──────────────────────────────────────────────
    section("5. ГРОМКОСТИ И SFX")
    audios = mat.get("audios", [])
    audio_by_id = {a["id"]: a for a in audios}
    audio_tracks = [t for t in tracks if t["type"] == "audio"]
    print(f"   аудио-материалов: {len(audios)}, audio-дорожек: {len(audio_tracks)}")

    for ti, at in enumerate(audio_tracks):
        vols = Counter()
        kinds = Counter()
        for seg in at["segments"]:
            vols[round(seg.get("volume", 1.0), 4)] += 1
            a = audio_by_id.get(seg.get("material_id"), {})
            bn = _basename(a.get("name") or "")
            if "sentence" in bn.lower():
                kinds["voice (sentence_*)"] += 1
            elif bn.endswith(".mp4") or "scene_" in bn.lower():
                kinds["video-audio"] += 1
            elif bn:
                kinds[bn[:50]] += 1
        print()
        print(f"   --- Audio-track #{ti}  ({len(at['segments'])} сегм.) ---")
        print(f"      громкости: {dict(vols)}")
        print(f"      типы материалов:")
        for cat, n in kinds.most_common(8):
            print(f"        {cat}  ×{n}")

    # Громкость самого видео-трека
    vols = Counter()
    for seg in video_track["segments"]:
        vols[round(seg.get("volume", 1.0), 4)] += 1
    print()
    print(f"   Видео-track громкости: {dict(vols)}")

    # Fades
    fades = mat.get("audio_fades", [])
    if fades:
        print()
        print("   Audio fades (затухания):")
        for f in fades:
            fin = f.get("fade_in_duration", 0) / 1_000_000
            fout = f.get("fade_out_duration", 0) / 1_000_000
            if fin or fout:
                print(f"     fade_in={fin:.3f}s  fade_out={fout:.3f}s")

    # Список всех уникальных SFX/музыкальных файлов
    print()
    print("   Уникальные SFX/музыка (всё что не sentence/scene):")
    sfx = set()
    for a in audios:
        name = a.get("name") or ""
        path = a.get("path") or ""
        bn = _basename(name).lower()
        if "sentence" not in bn and "scene_" not in bn and not bn.endswith(".mp4"):
            sfx.add((name, path))
    for name, path in sorted(sfx):
        print(f"     {name!r}")
        print(f"       └ {path}")

    print()
    print("=" * 70)
    print(" Если значения здесь отличаются от pyCapCut/template_theseus.py —")
    print(" обнови template_theseus.py чтобы синхронизировать эталон.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
