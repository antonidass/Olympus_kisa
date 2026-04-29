"""Разбирает draft_content.json проекта «Мидас» из CapCut и печатает,
что там по факту: переходы, видеоэффекты, анимации, фейды.
Запуск: python pyCapCut/_inspect_midas.py"""
import json
import os
import sys

# Принудительно UTF-8 stdout на Windows
sys.stdout.reconfigure(encoding="utf-8")

p = os.path.expandvars(
    r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\Мидас и золотое прикосновение\draft_content.json"
)
with open(p, encoding="utf-8") as f:
    d = json.load(f)

mats = d["materials"]
tracks = d.get("tracks", [])

# ── Собираем map id → имя для переходов, эффектов, анимаций
tr_by_id = {t["id"]: t for t in mats["transitions"]}
eff_by_id = {e["id"]: e for e in mats["video_effects"]}
anim_by_id = {a["id"]: a for a in mats["material_animations"]}
vid_by_id = {v["id"]: v for v in mats["videos"]}

print("=" * 70)
print(f"TRANSITIONS ({len(mats['transitions'])})")
print("=" * 70)
for t in mats["transitions"]:
    dur_s = t.get("duration", 0) / 1_000_000
    print(f"  {t.get('name'):<35} {dur_s:5.2f}s  overlap={t.get('is_overlap')}")

print()
print("=" * 70)
print(f"VIDEO EFFECTS ({len(mats['video_effects'])})")
print("=" * 70)
for e in mats["video_effects"]:
    print(f"  name={e.get('name')!r}")
    print(f"    type={e.get('type')}  category={e.get('category_name')}")
    print(f"    effect_id={e.get('effect_id')}  apply_target_type={e.get('apply_target_type')}")

print()
print("=" * 70)
print(f"MATERIAL ANIMATIONS ({len(mats['material_animations'])})")
print("=" * 70)
all_anim_names = []
for a in mats["material_animations"]:
    for an in a.get("animations", []):
        all_anim_names.append((an.get("type"), an.get("name"), an.get("duration", 0)))
# Уникальные + счётчики
from collections import Counter

c = Counter((t, n) for t, n, _ in all_anim_names)
for (tp, name), cnt in c.most_common():
    print(f"  [{tp:<8}] {name:<35} x{cnt}")

print()
print("=" * 70)
print("TRACKS")
print("=" * 70)
for tr in tracks:
    name = tr.get("name") or "(без имени)"
    tp = tr.get("type")
    segs = tr.get("segments", [])
    print(f"  track={name!r:<15} type={tp}  segments={len(segs)}")

# ── Сопоставление «сцена → переход»
print()
print("=" * 70)
print("ПЕРЕХОДЫ ПО СЦЕНАМ (main-трек)")
print("=" * 70)
main_track = None
for tr in tracks:
    if tr.get("type") == "video" and (tr.get("name") in ("main", "") or main_track is None):
        main_track = tr
        if tr.get("name") == "main":
            break

if main_track:
    for i, seg in enumerate(main_track["segments"], 1):
        vid_id = seg.get("material_id")
        vid = vid_by_id.get(vid_id, {})
        vid_name = vid.get("material_name") or vid.get("path", "").split("\\")[-1]

        # Переход привязан к segment через extra_material_refs
        tr_name = "—"
        for ref in seg.get("extra_material_refs", []):
            if ref in tr_by_id:
                t = tr_by_id[ref]
                dur = t.get("duration", 0) / 1_000_000
                tr_name = f"{t.get('name')} ({dur:.2f}s)"
                break

        # Эффекты, привязанные к сегменту
        seg_effects = []
        for ref in seg.get("extra_material_refs", []):
            if ref in eff_by_id:
                seg_effects.append(eff_by_id[ref].get("name"))
        eff_str = f"  эффекты: {', '.join(seg_effects)}" if seg_effects else ""

        # Анимации
        seg_anims = []
        for ref in seg.get("extra_material_refs", []):
            if ref in anim_by_id:
                for an in anim_by_id[ref].get("animations", []):
                    seg_anims.append(f"{an.get('type')}:{an.get('name')}")
        anim_str = f"  анимации: {', '.join(seg_anims)}" if seg_anims else ""

        print(f"  scene {i:02d}  {vid_name:<25}  →  {tr_name}{eff_str}{anim_str}")

# ── Эффекты, привязанные к отдельным сегментам/тракам (не к видеосегментам)
print()
print("=" * 70)
print("ЭФФЕКТЫ-ОВЕРЛЕИ (на отдельных effect-дорожках)")
print("=" * 70)
for tr in tracks:
    if tr.get("type") == "effect":
        for seg in tr.get("segments", []):
            mid = seg.get("material_id")
            e = eff_by_id.get(mid)
            if not e:
                continue
            tr_rng = seg.get("target_timerange", {})
            start = tr_rng.get("start", 0) / 1_000_000
            dur = tr_rng.get("duration", 0) / 1_000_000
            print(
                f"  {e.get('name'):<30} [{e.get('category_name')}]  "
                f"start={start:.2f}s  dur={dur:.2f}s"
            )
