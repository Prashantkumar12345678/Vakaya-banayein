# -*- coding: utf-8 -*-
"""Swifty talking - a GIF built from ONE still (assets/UI/sw_head_talking.webp).

No text anywhere.

THE JAW IS CUT OUT AND HINGED. The two head poses that exist - neutral and talking - are framed
differently (different zoom, one hand up), so cutting between them reads as a jump rather than as
speech. So one image is used and the mouth is worked inside it:
  the red mouth band is squashed vertically  -> the gap closes,
  the lower beak below it is carried up rigidly by exactly what the gap lost -> a real jaw keeps
  its shape, it does not shrink,
  and the strip the jaw vacates is repainted from what is BEHIND the beak.

That last part took three goes. A patch lifted from a strip further down painted chest onto face;
a patch taken from the rows just below the beak tip dragged a fragment of the chest's V-line up
with it. Both left a pale rectangle under the jaw. The honest source is sideways: at any row
through the beak, the pixels just outside it left and right ARE the surface it sits on.

The RHYTHM is syllables, not a sine. A mouth opening and closing evenly reads as a machine; real
speech is uneven, and it SHUTS between words. So the timeline is a list of syllables with their
own lengths and heights, with real pauses written in.
"""
import os, math
from PIL import Image

SRC  = "HI02H12_L02_S01/assets/UI/sw_head_talking.webp"
OUT  = "_masters/art/swifty_talking.gif"
X0, X1  = 226, 338          # the beak's own width plus a hair
MOUTH_T = 269               # the dark hinge where the upper beak ends
MOUTH_B = 303               # bottom of the red interior
JAW_B   = 330               # bottom tip of the lower beak
SIZE    = 300
BG      = (233, 243, 253)
FPS     = 20

base = Image.open(SRC).convert("RGBA")

def _plate():
    h = JAW_B + 6 - MOUTH_T
    pl = Image.new("RGBA", (X1 - X0, h))
    px, bp = pl.load(), base.load()
    for j in range(h):
        y = MOUTH_T + j
        L, R = bp[X0 - 4, y], bp[X1 + 3, y]
        for i in range(X1 - X0):
            t = i / float(X1 - X0 - 1)
            px[i, j] = tuple(round(L[k] + (R[k] - L[k]) * t) for k in range(4))
    return pl
PLATE = _plate()

def pose(openness):
    im = base.copy()
    mh = MOUTH_B - MOUTH_T
    new_mh = max(1, round(mh * openness))
    lift = mh - new_mh
    mouth = base.crop((X0, MOUTH_T, X1, MOUTH_B)).resize((X1 - X0, new_mh), Image.LANCZOS)
    jaw   = base.crop((X0, MOUTH_B, X1, JAW_B))
    if lift:
        im.paste(PLATE.crop((0, JAW_B - lift - MOUTH_T, X1 - X0, JAW_B - MOUTH_T)),
                 (X0, JAW_B - lift))
    im.paste(mouth, (X0, MOUTH_T))
    im.paste(jaw,   (X0, MOUTH_B - lift))
    return im

# (length in ms, how wide it opens) - 0 height is a pause with the beak shut
SPEECH = [(150,.85),(120,.55),(170,.95),(130,.45),(210,0),          # a phrase, then a breath
          (140,.75),(150,.9),(120,.5),(160,.8),(280,0),             # second phrase, longer rest
          (130,.6),(170,.95),(140,.7),(150,.85),(120,.45),(340,0)]  # third, then the loop's rest

frames, durs = [], []
step = 1000 // FPS
for ms, peak in SPEECH:
    n = max(1, round(ms / step))
    for i in range(n):
        if peak == 0:
            a = 0.06                                   # never quite locked shut - he is still alive
        else:
            t = (i + 0.5) / n
            a = 0.08 + peak * math.sin(math.pi * t) ** 0.7
        f = pose(min(1.0, a))
        # THE HEAD DOES NOT MOVE. A bob and a sway were tried and cost twice over: rotating left
        # bare wedges in the corners, and moving the whole head meant every frame differed from
        # the last across the entire canvas - 1.37 MB for two and a half seconds. With only the
        # jaw moving, the frame-to-frame difference is a patch the size of a beak, and a talking
        # head that holds still while it speaks is the more natural thing anyway.
        canvas = Image.new("RGB", (SIZE, SIZE), BG)
        sm = f.resize((SIZE, SIZE), Image.LANCZOS)
        canvas.paste(sm, (0, 0), sm)
        frames.append(canvas); durs.append(step)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
# the palette comes from frames where the mouth is OPEN, so the red interior survives it - the
# arrival GIF lost all its colour by taking a palette from a frame the bird was not even in yet
probe = Image.new("RGB", (SIZE * 3, SIZE))
for i, k in enumerate((2, len(frames) // 3, len(frames) // 2)):
    probe.paste(frames[k], (i * SIZE, 0))
pal = probe.quantize(colors=64, method=Image.MEDIANCUT, dither=Image.NONE)
qs = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
qs[0].save(OUT, save_all=True, append_images=qs[1:], duration=durs, loop=0, optimize=True)
print("%s  %dx%d  %d frames  %.1fs  %d KB"
      % (OUT, SIZE, SIZE, len(qs), sum(durs) / 1000.0, round(os.path.getsize(OUT) / 1024)))
