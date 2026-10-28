# -*- coding: utf-8 -*-
"""Take the export checkerboard off a supplied PNG and ship it as a trimmed WebP.

    python _tools/dekey_art.py "<src>.png" <out-name> [target-height]

THE CHECKERBOARD IS REAL PIXELS, NOT TRANSPARENCY. The four animals arrived as RGB PNGs with
the transparency grid baked in, so there is no alpha to use - it has to be keyed. The two grid
greys are read off the border rather than assumed, and the key is FLOOD-FILLED FROM THE BORDER:
only grid-coloured pixels reachable from outside go. That matters here more than usual, because
the elephants and the mice are themselves grey - a plain colour key would eat holes in them,
while anything the silhouette encloses survives whatever colour it is. Same approach as
dekey_last_page.py and the walking-animal GIFs.
"""
import os, sys
from collections import deque
import numpy as np
from PIL import Image

SRC, NAME = sys.argv[1], sys.argv[2]
TARGET_H = int(sys.argv[3]) if len(sys.argv) > 3 else 420
TOL = 12
OUT = os.path.join("HI02H12_L02_S01", "assets", "Images", NAME + ".webp")

rgb = np.array(Image.open(SRC).convert("RGB")).astype(int)
h, w, _ = rgb.shape

border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
keys = []
for px in border:
    if not any(abs(px - np.array(k)).max() <= TOL for k in keys):
        keys.append(tuple(int(v) for v in px))
print("%s: %dx%d, grid colours %s" % (os.path.basename(SRC), w, h, keys[:6]))

d = np.stack([np.abs(rgb - np.array(k)).max(axis=2) for k in keys]).min(axis=0)
keyed = d <= TOL
seen = np.zeros((h, w), bool)
q = deque()
for x in range(w):
    for y in (0, h - 1):
        if keyed[y, x] and not seen[y, x]: seen[y, x] = True; q.append((y, x))
for y in range(h):
    for x in (0, w - 1):
        if keyed[y, x] and not seen[y, x]: seen[y, x] = True; q.append((y, x))
while q:
    y, x = q.popleft()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < h and 0 <= nx < w and keyed[ny, nx] and not seen[ny, nx]:
            seen[ny, nx] = True; q.append((ny, nx))

im = Image.fromarray(np.dstack([rgb, np.where(seen, 0, 255)]).astype(np.uint8), "RGBA")
al = np.array(im)[..., 3]
ys, xs = np.nonzero(al > 8)
box = (max(0, xs.min() - 2), max(0, ys.min() - 2), min(w, xs.max() + 3), min(h, ys.max() + 3))
im = im.crop(box)
sc = TARGET_H / float(im.size[1])
im = im.resize((max(1, round(im.size[0] * sc)), TARGET_H), Image.LANCZOS)
im.save(OUT, "WEBP", quality=88, method=6)
print("  -> %s  %dx%d  %d KB" % (OUT, im.size[0], im.size[1], os.path.getsize(OUT) // 1024))
