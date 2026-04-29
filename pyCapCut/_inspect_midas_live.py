"""
Инспектор живого CapCut-драфта «Мидас и золотое прикосновение».

Цель: вытянуть всё, что пользователь правил руками в CapCut и что НЕ
попало в наш build_midas.py: переходы (имена/типы/длительности), видео-
эффекты, аудио-эффекты на дорожках, точные стили текстов (шрифт, размер,
цвет, обводка, положение), громкости, кейфреймы.

Запуск:
    PYTHONIOENCODING=utf-8 python pyCapCut/_inspect_midas_live.py
"""

from __future__ import annotations

import io
import json
import os
import sys
from collections import Counter, OrderedDict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
DRAFTS = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"

PROJECT = sys.argv[1] if len(sys.argv) > 1 else "Мидас и золотое прикосновение"
DRAFT = DRAFTS / PROJECT / "draft_content.json"

US = 1_000_000


def main() -> int:
    if not DRAFT.is_file():
        print(f"Не нашёл {DRAFT}")
        return 1

    print(f"Читаю: {DRAFT}")
    print(f"Размер: {DRAFT.stat().st_size/1024:.1f} KB")
    draft = json.load(open(DRAFT, encoding="utf-8"))

    print()
    print("=== ДОРОЖКИ ===")
    for i, t in enumerate(draft.get("tracks", [])):
        ttype = t.get("type")
        tname = t.get("name", "")
        n = len(t.get("segments", []))
        attr = t.get("attribute", 0)
        print(f"  [{i}] type={ttype:<6} name={tname!r:<22} segs={n} attr={attr}")

    print()
    print("=== МАТЕРИАЛЫ ===")
    mats = draft.get("materials", {})
    for k in [
        "videos", "audios", "texts", "transitions", "video_effects",
        "audio_effects", "audio_fades", "speeds", "canvases",
        "material_animations", "audio_balances", "tail_leaders",
    ]:
        if k in mats:
            print(f"  {k}: {len(mats[k])}")

    # ── Переходы ──
    print()
    print("=== ПЕРЕХОДЫ (materials.transitions) ===")
    trans = mats.get("transitions", [])
    by_name = Counter()
    samples_by_name: dict[str, dict] = {}
    for tr in trans:
        nm = tr.get("name") or tr.get("effect_id") or "?"
        by_name[nm] += 1
        if nm not in samples_by_name:
            samples_by_name[nm] = tr
    for nm, cnt in by_name.most_common():
        sample = samples_by_name[nm]
        keys_summary = {
            k: sample.get(k) for k in [
                "name", "effect_id", "resource_id", "category_id", "category_name",
                "duration", "is_overlap", "platform", "type", "request_id",
            ] if k in sample
        }
        print(f"  ×{cnt}  {nm}")
        for k, v in keys_summary.items():
            if k == "duration" and v:
                print(f"        {k}: {v} ({v/US:.2f}s)")
            else:
                print(f"        {k}: {v}")

    # ── Какой переход на какой видео-сегмент ──
    print()
    print("=== ПЕРЕХОДЫ ПО ВИДЕО-СЕГМЕНТАМ (track 'main') ===")
    trans_by_id = {tr["id"]: tr for tr in trans}
    for t in draft.get("tracks", []):
        if t.get("type") == "video" and t.get("name") in ("main", "video", ""):
            for seg in sorted(t["segments"], key=lambda s: s["target_timerange"]["start"]):
                trans_refs = []
                for ref in seg.get("extra_material_refs", []):
                    if ref in trans_by_id:
                        trans_refs.append(trans_by_id[ref])
                start_s = seg["target_timerange"]["start"] / US
                dur_s = seg["target_timerange"]["duration"] / US
                vid_id = seg.get("material_id")
                # имя файла из materials.videos
                fname = ""
                for v in mats.get("videos", []):
                    if v["id"] == vid_id:
                        fname = os.path.basename(v.get("path") or v.get("material_name") or "")
                        break
                trans_str = ""
                if trans_refs:
                    trans_str = ", ".join(
                        f"{tr.get('name')}({tr.get('duration', 0)/US:.2f}s)"
                        for tr in trans_refs
                    )
                if trans_str:
                    print(f"  [{start_s:6.2f}+{dur_s:5.2f}] {fname:<22} → {trans_str}")
            break

    # ── Видео-эффекты ──
    print()
    print("=== ВИДЕО-ЭФФЕКТЫ (materials.video_effects) ===")
    veffs = mats.get("video_effects", [])
    eff_by_name = Counter()
    eff_samples: dict[str, dict] = {}
    for e in veffs:
        nm = e.get("name") or e.get("effect_id") or "?"
        eff_by_name[nm] += 1
        if nm not in eff_samples:
            eff_samples[nm] = e
    for nm, cnt in eff_by_name.most_common():
        s = eff_samples[nm]
        print(f"  ×{cnt}  {nm}")
        for k in ["effect_id", "resource_id", "category_name", "type", "apply_target_type"]:
            if k in s:
                print(f"        {k}: {s[k]}")

    # ── Аудио-эффекты ──
    print()
    print("=== АУДИО-ЭФФЕКТЫ (materials.audio_effects) ===")
    aeffs = mats.get("audio_effects", [])
    if aeffs:
        for e in aeffs[:10]:
            nm = e.get("name") or "?"
            print(f"  {nm}  effect_id={e.get('effect_id')}")
    else:
        print("  (нет)")

    # ── Аудио-fades ──
    print()
    print("=== АУДИО-FADES (materials.audio_fades) ===")
    afades = mats.get("audio_fades", [])
    if afades:
        for f in afades:
            print(f"  fade_in_us={f.get('fade_in_duration')}  fade_out_us={f.get('fade_out_duration')}")
    else:
        print("  (нет)")

    # ── Тексты — стиль интро и обычного субтитра ──
    print()
    print("=== ТЕКСТЫ — выборка стилей ===")
    texts = mats.get("texts", [])
    print(f"всего text-материалов: {len(texts)}")
    # покажем уникальные сочетания шрифт+цвет+размер
    style_signatures = OrderedDict()
    for m in texts:
        try:
            cnt = json.loads(m.get("content") or "{}")
        except Exception:
            cnt = {}
        text = (cnt.get("text") or "")[:40].replace("\n", "\\n")
        styles = cnt.get("styles") or []
        if not styles:
            sig = ("(no-style)", "", "", "")
        else:
            st0 = styles[0]
            font_path = ""
            font_id = ""
            if isinstance(st0.get("font"), dict):
                font_path = os.path.basename(st0["font"].get("path", ""))
                font_id = st0["font"].get("id", "")
            color = st0.get("fill", {}).get("content", {}).get("solid", {}).get("color")
            size = st0.get("size")
            stroke = st0.get("strokes", [])
            sig = (font_path or m.get("text_color", ""), str(size), str(color), str(len(stroke)))
        style_signatures.setdefault(sig, []).append(text)
    print(f"уникальных стилей: {len(style_signatures)}")
    for sig, samples in style_signatures.items():
        print(f"  font={sig[0]}  size={sig[1]}  color={sig[2]}  strokes={sig[3]}")
        for s in samples[:3]:
            print(f"      {s!r}")
        if len(samples) > 3:
            print(f"      … ещё {len(samples)-3}")

    # Полный дамп первого text-материала каждого уникального стиля для копирования в build_theseus
    print()
    print("=== ПОЛНЫЕ ОБРАЗЦЫ TEXT-MATERIAL (один на каждый уникальный шрифт+размер) ===")
    seen_sigs: set[tuple] = set()
    for m in texts:
        try:
            cnt = json.loads(m.get("content") or "{}")
        except Exception:
            continue
        styles = cnt.get("styles") or []
        if not styles:
            continue
        st0 = styles[0]
        font_id = ""
        if isinstance(st0.get("font"), dict):
            font_id = st0["font"].get("id", "")
        sig = (font_id, st0.get("size"), len(st0.get("strokes", [])))
        if sig in seen_sigs:
            continue
        seen_sigs.add(sig)
        text_preview = (cnt.get("text") or "")[:50]
        print(f"--- {text_preview!r}  font_id={font_id} size={st0.get('size')} strokes={len(st0.get('strokes', []))} ---")
        print(json.dumps(st0, ensure_ascii=False, indent=2)[:1500])
        print()

    # ── Громкости/кейфреймы на музыке ──
    print()
    print("=== АУДИО-СЕГМЕНТЫ — громкости и кейфреймы ===")
    audios_by_id = {a["id"]: a for a in mats.get("audios", [])}
    for t in draft.get("tracks", []):
        if t.get("type") != "audio":
            continue
        nm = t.get("name", "")
        for seg in t.get("segments", []):
            vol = seg.get("volume", 1.0)
            kfs = seg.get("common_keyframes", [])
            kf_count = sum(len(g.get("keyframe_list", [])) for g in kfs)
            aid = seg.get("material_id")
            apath = audios_by_id.get(aid, {}).get("path", "")
            apath_short = os.path.basename(apath) if apath else ""
            ts = seg["target_timerange"]
            if vol != 1.0 or kf_count:
                print(f"  [{nm:<8}] {apath_short:<60} vol={vol} kf={kf_count} "
                      f"start={ts['start']/US:.2f}s dur={ts['duration']/US:.2f}s")

    # ── Сегменты видео — громкость, скорость, кейфреймы клипа ──
    print()
    print("=== ВИДЕО-СЕГМЕНТЫ — громкость / скорость / клип-кейфреймы ===")
    for t in draft.get("tracks", []):
        if t.get("type") != "video":
            continue
        for seg in t.get("segments", []):
            vol = seg.get("volume", 1.0)
            speed = seg.get("speed", 1.0)
            clip = seg.get("clip", {}) or {}
            kfs = seg.get("common_keyframes", []) or []
            kf_count = sum(len(g.get("keyframe_list", [])) for g in kfs)
            if vol != 1.0 or speed != 1.0 or kf_count:
                ts = seg["target_timerange"]
                vid_id = seg.get("material_id")
                fname = ""
                for v in mats.get("videos", []):
                    if v["id"] == vid_id:
                        fname = os.path.basename(v.get("path") or "")
                        break
                print(f"  {fname:<24} vol={vol} speed={speed} kf={kf_count} "
                      f"start={ts['start']/US:.2f}s dur={ts['duration']/US:.2f}s")

    return 0


if __name__ == "__main__":
    sys.exit(main())
