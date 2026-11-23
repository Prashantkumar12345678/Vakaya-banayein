# -*- coding: utf-8 -*-
"""Move assets nothing in the game names to _backup/unused_assets_<date>/ (Jodi Milaya's clean_game rule).
The /*@ASSET_MANIFEST*/ list is ignored when deciding (it names every file), and is rebuilt afterwards
by asset_manifest.py. Clips that leave are dropped from both card copies' audio maps.
    python3 _tools/clean_unused.py [--dry]"""
import json, os, re, shutil, sys, time
DRY = "--dry" in sys.argv
PROJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GAME = os.path.join(PROJ, "HI02H12_L02_S01"); BK = os.path.join(PROJ, "_backup", "unused_assets_" + time.strftime("%Y%m%d"))
os.chdir(GAME)
h = open("index.html", encoding="utf-8").read()
i = h.index('{"version": "0.2"'); card, e = json.JSONDecoder().raw_decode(h, i)
eng = re.sub(r"/\*@ASSET_MANIFEST\*/\[.*?\]\];?", "", h[:i] + h[e:], flags=re.S)
slides_txt = json.dumps(card["slides"], ensure_ascii=False) + json.dumps({k: v for k, v in card.items() if k not in ("slides", "assets")}, ensure_ascii=False)
img_txt = json.dumps(card["assets"].get("image", {}), ensure_ascii=False)
# names built at runtime ("bgm_"+key+".m4a", 'vo_map_intro'+n, "swifty_walk_"+dir): a quoted literal followed by + is a PREFIX
PREFIXES = {x for x in re.findall(r"""["'`/]([A-Za-z][\w-]{3,})["'`]\s*\+""", eng)}
def q(txt, name): return re.search(r"""["'`/(]""" + re.escape(name) + r"""(["'`.?)\s]|$)""", txt) is not None
unused = []
for d, _, fs in os.walk("assets"):
    for f in fs:
        rel = os.path.join(d, f).replace(os.sep, "/"); stem = os.path.splitext(f)[0]
        if f == ".DS_Store": used = False
        elif any(stem.startswith(p) for p in PREFIXES): used = True
        elif rel.startswith(("assets/VO/", "assets/SFX/")): used = ('"%s"' % stem in slides_txt) or q(eng, stem) or q(eng, f)
        elif re.match(r"assets/UI/sw_(head|lg)_", rel): used = True
        else: used = q(slides_txt + img_txt, stem) or q(eng, stem) or q(eng, f) or q(eng, rel)
        if not used: unused.append(rel)
mb = sum(os.path.getsize(r) for r in unused) / 1e6
print("prefixes kept:", sorted(PREFIXES)[:40]); print("unused: %d files, %.1f MB" % (len(unused), mb))
for r in sorted(unused): print("  ", r, "%.0f KB" % (os.path.getsize(r) / 1024))
if DRY: sys.exit()
for r in unused:
    dst = os.path.join(BK, r); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.move(r, dst)
for d, _, _ in sorted(os.walk("assets"), key=lambda t: -len(t[0])):
    if not os.listdir(d): os.rmdir(d)
gone = {os.path.splitext(os.path.basename(r))[0] for r in unused if r.startswith(("assets/VO/", "assets/SFX/"))}
for k in ("audio", "audio_text"):
    for g in gone: card["assets"].get(k, {}).pop(g, None)
open("index.html", "w", encoding="utf-8").write(h[:i] + json.dumps(card, ensure_ascii=False) + h[e:])
open("card.json", "w", encoding="utf-8").write(json.dumps(card, ensure_ascii=False, indent=1))
print("moved; %d clip ids dropped from the card" % len(gone))
