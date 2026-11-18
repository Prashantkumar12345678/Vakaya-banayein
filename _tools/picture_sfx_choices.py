# -*- coding: utf-8 -*-
"""Three candidate sounds per picture, side by side, for the SME to pick by ear (2026-11-18: "picture sounds achhe nahi").

    python3 _tools/picture_sfx_choices.py      -> _previews/picture_sfx/index.html

Each candidate is cut to its clear part (from where it first gets loud, at most MAX seconds), faded and levelled
like make_action_sfx.py. Option A of every row is what plays in the game today only where noted.
"""
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_action_sfx as m   # noqa: E402  (also rebuilds the game sfx - harmless, same output)
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "_previews", "picture_sfx"); os.makedirs(OUT, exist_ok=True)
MAX = 2.6

clear, soft = m.clear, m.soft
SOFT = {"P1": 0.10, "P3": 0.10}

def plinks(times, rate=1.35):   # small, light water drops - a sink drip sped up into cartoon "plink"s
    d = m.speed(clear(1879, length=.5), rate); return [(d, t, .8 + .1 * k) for k, t in enumerate(times)]

# Round 3 (SME 2026-11-18): G3, G4, P2 picked; P1 and P3 still "not right - too adult" -> lighter, cartoon-style ideas.
# T2 is the round-2 row again (no pick yet).
C = {  # slide: (sentence, [(label, signal), ...])
 "T2": ("बच्चे मैदान में खेल रहे हैं।", [("ball kick + kids laughing", m.mix((clear(2099, length=.6), 0, 1), (clear(2263, length=1.4), .35, .9))),
        ("happy child laughing", clear(2265, length=2.0)), ("playground with kids", clear(2266, length=2.4)), ("park, kids playing", clear(372, length=2.4))]),
 "P1": ("मीरा पौधों को पानी दे रही है।", [("water plinks + a happy sparkle (plants)", m.mix(*plinks((0, .3, .6, .9)), (clear(871, length=1.0), 1.25, .5))),
        ("cartoon splash", clear(2884, length=1.4)), ("short sprinkle + twinkle", m.mix((soft(clear(2393, length=1.2)), 0, .8), (clear(3108, length=1.2), .9, .5)))]),
 "P3": ("बच्चा प्यासा है, उसे पानी चाहिए।", [("cartoon gulp-gulp", clear(2828, length=1.6)), ("glass ting + little pour", m.mix((clear(2836, length=.5), 0, 1), (clear(2826, length=1.3), .4, .7))),
        ("water plinks + refresh sparkle", m.mix(*plinks((0, .3)), (clear(2837, length=1.3), .65, .6))), ("magic drink (game style)", clear(2830, length=1.6))]),
}
card = json.load(open(os.path.join(ROOT, "HI02H12_L02_S01", "card.json")))
img = {s["id"]: s["data"].get("image_id") for s in card["slides"]}
rows = []
for sid, (sent, opts) in C.items():
    cells = []
    for k, (label, sig) in enumerate(opts):
        name = "%s_%s.wav" % (sid.lower(), "ABCD"[k])
        d = (np.clip(m.level(sig, SOFT.get(sid, 0.14)), -1, 1) * 32767).astype(np.int16)
        import wave
        with wave.open(os.path.join(OUT, name), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(m.SR); w.writeframes(d.tobytes())
        cells.append('<button onclick="new Audio(\'%s\').play()"><b>%s</b> %s</button>' % (name, "ABCD"[k], label))
    pic = "../../HI02H12_L02_S01/assets/Images/%s.webp" % img.get(sid)
    rows.append('<tr><td><img src="%s"></td><td><b>%s</b><br>%s</td><td>%s</td></tr>' % (pic, sid, sent, "".join(cells)))
open(os.path.join(OUT, "index.html"), "w").write('''<!doctype html><meta charset="utf-8"><title>Picture sounds</title>
<style>body{font:16px system-ui;margin:16px;background:#fffaf2}td{padding:8px;border-bottom:1px solid #eee;vertical-align:middle}
img{width:150px;border-radius:8px}button{display:block;margin:4px 0;padding:8px 14px;font-size:15px;border-radius:8px;border:1px solid #d9a35a;background:#fff;cursor:pointer;text-align:left;width:280px}
button:hover{background:#ffe9c7}</style><h2>Picture sounds - pick A, B or C for each picture</h2><table>''' + "".join(rows) + "</table>")
print("ok", OUT)
