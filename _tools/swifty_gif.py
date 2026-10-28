# -*- coding: utf-8 -*-
"""Swifty arrives - a GIF built from ONE still (assets/UI/start_mascot.png).

Nothing is drawn that is not already in the picture: the bird is moved, turned, squashed and
scaled, which is all a still can honestly give. He runs in from the left on an arc, lands with a
squash, and then sways on the spot as if waving - the wave reads because the arm is ALREADY up in
the source art, so the sway carries it.
No text anywhere, as asked.
"""
import os, math
from PIL import Image

SRC  = "HI02H12_L02_S01/assets/UI/start_mascot.png"
OUT  = "_masters/art/swifty_arrives.gif"
W, H = 380, 320
FPS  = 20
BG   = (233, 243, 253)          # the game's own pale stage blue, so the edges stay clean
# FLAT, no grid: a drawn grid costs nothing to look at and a great deal to store - every frame
# then differs from the last across the whole canvas instead of only where the bird moved. The
# grid the game shows is the stage's own, behind wherever this lands.

bird = Image.open(SRC).convert("RGBA")
TARGET_H = 252
bird = bird.resize((round(bird.width * TARGET_H / bird.height), TARGET_H), Image.LANCZOS)

BASE = Image.new("RGB", (W, H), BG)
FLOOR = H - 22                                     # where his feet come to rest
REST_X = W // 2

def ease_out(t):  return 1 - (1 - t) ** 3
def ease_io(t):   return 0.5 - 0.5 * math.cos(math.pi * t)

def frame(x, y, sx, sy, deg):
    """place the bird with his FEET at (x, y), scaled and tilted about that point"""
    w, h = max(1, round(bird.width * sx)), max(1, round(bird.height * sy))
    b = bird.resize((w, h), Image.LANCZOS)
    if deg:
        b = b.rotate(deg, resample=Image.BICUBIC, expand=True,
                     center=(w / 2, h))             # turn about the feet, not the middle
    f = BASE.copy()
    f.paste(b, (round(x - b.width / 2), round(y - b.height)), b)
    return f

frames, durs = [], []
RUN, LAND, SWAY = 0.62, 0.22, 1.30                 # seconds
def add(f, ms): frames.append(f); durs.append(ms)

n = int(RUN * FPS)
for i in range(n):
    t = ease_out(i / (n - 1))
    x = -bird.width * 0.6 + (REST_X + 26 - (-bird.width * 0.6)) * t   # overshoots by 26px
    hop = math.sin(math.pi * (i / (n - 1))) * 34                      # one arc through the air
    s = 0.88 + 0.12 * t
    add(frame(x, FLOOR - hop, s, s, -7 * (1 - t)), 1000 // FPS)

n = int(LAND * FPS)
for i in range(n):                                  # squash, settle back to centre
    t = i / (n - 1)
    sq = math.sin(math.pi * t)
    add(frame(REST_X + 26 * (1 - ease_io(t)), FLOOR, 1 + 0.07 * sq, 1 - 0.09 * sq, 0), 1000 // FPS)

n = int(SWAY * FPS)
for i in range(n):                                  # on the spot: two easy sways, a little bob
    t = i / n
    add(frame(REST_X, FLOOR - 5 * abs(math.sin(2 * math.pi * t)),
              1, 1, 3.2 * math.sin(2 * math.pi * t)), 1000 // FPS)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
# ONE shared palette for every frame - re-quantising per frame makes the bird's yellow crawl.
# It must be built from frames where he is actually ON SCREEN: taking it from frame 0, where he
# is still off the left edge, gave a palette of nothing but background blue, and every frame
# quantised against it came out as grey line art with the yellow gone.
probe = Image.new("RGB", (W * 3, H))
for i, k in enumerate((len(frames) // 2, len(frames) - 12, len(frames) - 1)):
    probe.paste(frames[k], (i * W, 0))
pal = probe.quantize(colors=64, method=Image.MEDIANCUT, dither=Image.NONE)
qs = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
qs[0].save(OUT, save_all=True, append_images=qs[1:], duration=durs, loop=0, optimize=True)
print("%s  %dx%d  %d frames  %.1fs  %d KB"
      % (OUT, W, H, len(qs), sum(durs) / 1000.0, round(os.path.getsize(OUT) / 1024)))
