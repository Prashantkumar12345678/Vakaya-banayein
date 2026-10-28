# -*- coding: utf-8 -*-
"""Swifty talking, full body, on a TRANSPARENT ground - for the transition screen.

Same hinge as the head version: the red mouth band squashes, the lower beak rides up rigidly by
what the gap lost, and the strip it vacates is repainted from what is behind the beak.

TWO THINGS DIFFER HERE.

1. The plate cannot just blend left-to-right. On the head art both sides of the beak were clean
   cream; on the full body the jacket collar reaches in on the RIGHT at the rows just under the
   beak (sampled: y=300 gives (97,124,139) and (227,166,50) - outline and jacket, not face). A
   straight blend would have painted collar onto the chin. So each row checks both samples and
   falls back to the good one when the other is not face-coloured.

2. It has to sit on the gate's dark scrim, so the background must be transparent rather than a
   colour. GIF transparency is one index, all or nothing, so the alpha is cut hard at the
   halfway mark - which this art can take, because it is drawn with a white sticker outline that
   gives the silhouette its own edge.
"""
import os, math
from PIL import Image

SRC  = "HI02H12_L02_S01/assets/UI/start_mascot.png"
OUT  = "HI02H12_L02_S01/assets/UI/sw_talk_body.gif"
X0, X1  = 204, 326          # the beak, with a small margin into the face
MOUTH_T = 237               # the dark line where the mouth opens
MOUTH_B = 280               # bottom of the red interior
JAW_B   = 302               # bottom tip of the lower beak
OUT_H   = 560
FPS     = 20
KEY     = (255, 0, 255)     # nothing in this art is magenta, so it can stand for "transparent"

base = Image.open(SRC).convert("RGBA")

def _face(px):
    """is this pixel the cream face/chest, rather than jacket, strap or outline?"""
    r, g, b, a = px
    return a > 200 and min(r, g, b) > 195 and (max(r, g, b) - min(r, g, b)) < 45

def _plate():
    h = JAW_B + 8 - MOUTH_T
    pl = Image.new("RGBA", (X1 - X0, h))
    px, bp = pl.load(), base.load()
    for j in range(h):
        y = MOUTH_T + j
        L = next((bp[X0 - k, y] for k in range(3, 26) if _face(bp[X0 - k, y])), None)
        R = next((bp[X1 + k, y] for k in range(3, 26) if _face(bp[X1 + k, y])), None)
        if L is None and R is None: L = R = (249, 247, 230, 255)   # the face's own cream
        if L is None: L = R
        if R is None: R = L
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

# syllables with their own lengths and heights, and real pauses - an even open/close reads as a
# machine, and speech shuts between words
SPEECH = [(150,.85),(120,.55),(170,.95),(130,.45),(220,0),
          (140,.75),(150,.9),(120,.5),(160,.8),(280,0),
          (130,.6),(170,.95),(140,.7),(150,.85),(120,.45),(340,0)]

W = round(base.width * OUT_H / base.height)
frames, durs = [], []
step = 1000 // FPS
for ms, peak in SPEECH:
    n = max(1, round(ms / step))
    for i in range(n):
        if peak == 0:
            a = 0.06                                 # never quite locked shut
        else:
            t = (i + 0.5) / n
            a = 0.08 + peak * math.sin(math.pi * t) ** 0.7
        f = pose(min(1.0, a)).resize((W, OUT_H), Image.LANCZOS)
        r, g, b, al = f.split()
        mask = al.point(lambda v: 255 if v >= 128 else 0)     # GIF alpha is all or nothing
        flat = Image.new("RGB", (W, OUT_H), KEY)
        flat.paste(Image.merge("RGB", (r, g, b)), (0, 0), mask)
        frames.append(flat); durs.append(step)

# the palette is taken from OPEN-mouth frames plus a patch of the key colour, so the red interior
# survives and the key is guaranteed an index of its own
probe = Image.new("RGB", (W * 3 + 40, OUT_H), KEY)
for i, k in enumerate((2, len(frames) // 3, len(frames) // 2)):
    probe.paste(frames[k], (i * W, 0))
pal = probe.quantize(colors=64, method=Image.MEDIANCUT, dither=Image.NONE)
qs = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]

# THE KEY'S INDEX IS READ FROM THE FRAME THAT IS ACTUALLY BEING SAVED, AND optimize IS OFF.
# Taken from the quantiser's palette instead, it came out as 63 while Pillow's optimize pass
# quietly rebuilt the palette on write and left the magenta sitting at 56 - so the GIF declared
# the wrong index transparent and every viewer showed a solid magenta rectangle. The file is
# barely larger without it; frame differencing is separate from palette optimisation.
flat_pal = qs[0].getpalette()
key_idx = min(range(len(flat_pal) // 3),
              key=lambda i: sum((flat_pal[i*3+c] - KEY[c]) ** 2 for c in range(3)))
for q in qs: q.info["transparency"] = key_idx
qs[0].save(OUT, save_all=True, append_images=qs[1:], duration=durs, loop=0,
           transparency=key_idx, disposal=1, optimize=False)
chk = Image.open(OUT); chk.seek(0)
assert chk.getpixel((3, 3)) == chk.info.get("transparency"), "the corner is not the transparent index"
print("%s  %dx%d  %d frames  %.1fs  %d KB  (key index %d = %s)"
      % (OUT, W, OUT_H, len(qs), sum(durs) / 1000.0, round(os.path.getsize(OUT) / 1024),
         key_idx, tuple(flat_pal[key_idx*3:key_idx*3+3])))
