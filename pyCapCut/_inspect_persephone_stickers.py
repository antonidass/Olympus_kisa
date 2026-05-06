"""Печать стикеров и оверлеев из живого драфта Персефоны + аудио рядом по времени."""
from __future__ import annotations
import json
import os
from pathlib import Path

BS = chr(92)
DRAFT = Path(os.path.expandvars(
    r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\Персефона и Аид\draft_content.json"
))


def fmt_time(us: int) -> str:
    return f"{us/1_000_000:.2f}s"


def basename(p: str) -> str:
    return p.replace(BS, "/").rsplit("/", 1)[-1]


def main() -> None:
    d = json.loads(DRAFT.read_text(encoding="utf-8"))
    mat = d["materials"]
    tracks = d["tracks"]

    videos = {v["id"]: v for v in mat.get("videos", [])}
    audios = {a["id"]: a for a in mat.get("audios", [])}
    stickers = {s["id"]: s for s in mat.get("stickers", [])}

    overlays: list[dict] = []  # все вставки-оверлеи (стикер + image-overlay)

    print("=== Track 1 (video overlay, 4 segs) ===")
    for seg in tracks[1]["segments"]:
        v = videos.get(seg["material_id"], {})
        path = v.get("path", "")
        bn = basename(path)
        tt = seg["target_timerange"]
        start_us = tt["start"]
        end_us = start_us + tt["duration"]
        print(f"  {fmt_time(start_us):>7} → {fmt_time(end_us):>7}  ({fmt_time(tt['duration']):>6})  {bn}")
        if path:
            print(f"          path: {path}")
        overlays.append({"track": 1, "start": start_us, "end": end_us, "name": bn, "path": path})

    print()
    print("=== Track 2 (video overlay, 1 seg) ===")
    for seg in tracks[2]["segments"]:
        v = videos.get(seg["material_id"], {})
        path = v.get("path", "")
        bn = basename(path)
        tt = seg["target_timerange"]
        start_us = tt["start"]
        end_us = start_us + tt["duration"]
        print(f"  {fmt_time(start_us):>7} → {fmt_time(end_us):>7}  ({fmt_time(tt['duration']):>6})  {bn}")
        if path:
            print(f"          path: {path}")
        overlays.append({"track": 2, "start": start_us, "end": end_us, "name": bn, "path": path})

    print()
    print("=== Track 5 (CapCut-стикер, 1 seg) ===")
    for seg in tracks[5]["segments"]:
        s = stickers.get(seg["material_id"], {})
        tt = seg["target_timerange"]
        start_us = tt["start"]
        end_us = start_us + tt["duration"]
        print(f"  {fmt_time(start_us):>7} → {fmt_time(end_us):>7}  ({fmt_time(tt['duration']):>6})  "
              f"{s.get('name')!r}  resource_id={s.get('resource_id')}  category={s.get('category_name')}")
        overlays.append({"track": 5, "start": start_us, "end": end_us, "name": s.get("name"), "kind": "capcut-sticker"})

    # Все audio-сегменты с временами
    audio_segs: list[dict] = []
    for ti, t in enumerate(tracks):
        if t["type"] != "audio":
            continue
        for seg in t["segments"]:
            a = audios.get(seg["material_id"], {})
            name = a.get("name") or ""
            tt = seg["target_timerange"]
            audio_segs.append({
                "track": ti,
                "track_name": t.get("name", ""),
                "start": tt["start"],
                "end": tt["start"] + tt["duration"],
                "name": name,
                "volume": seg.get("volume", 1.0),
            })

    # Для каждого оверлея ищем audio-сегменты, перекрывающиеся по времени
    print()
    print("=== Аудио, пересекающееся со стикерами/оверлеями ===")
    for ov in overlays:
        print(f"\n-- overlay: {ov['name']!r}  ({fmt_time(ov['start'])} → {fmt_time(ov['end'])})  track={ov['track']} --")
        # ищем audio-сегменты с пересечением (исключая основной voice/music)
        hits = []
        for a in audio_segs:
            if a["track_name"] in ("voice", "music"):
                continue
            # пересечение
            if a["end"] <= ov["start"] or a["start"] >= ov["end"]:
                continue
            hits.append(a)
        if not hits:
            print("    (нет SFX в это окно)")
        for a in hits:
            print(f"    track {a['track']}  {fmt_time(a['start']):>7} → {fmt_time(a['end']):>7}  "
                  f"vol={a['volume']:.3f}  {a['name']}")


if __name__ == "__main__":
    main()
