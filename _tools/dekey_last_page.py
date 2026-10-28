# -*- coding: utf-8 -*-
"""Take the flat background off the end-screen clip and ship it with real alpha.

Run from the repo root:  python _tools/dekey_last_page.py

THE BACKGROUND IS NOT A SCENE. Both versions that have arrived carry a stand-in for
transparency: the GIF had the export's checkerboard baked in ((252,252,255) / (252,252,170)),
the video has a near-white sweep of neutral greys (241-255). Either is keyable exactly - but a
plain colour key would also eat the bird, whose own white is (255,255,255), the brightest colour
in the frame. So the key is FLOOD-FILLED FROM THE BORDER: only background-coloured pixels
reachable from outside go, and whatever the silhouette encloses survives, whatever colour it is.
Same reasoning as the walking-animal GIFs earlier in this project.

OUTPUT IS WEBP, NOT GIF. GIF alpha is one all-or-nothing index and this art has soft edges, which
cut hard fringe against the sunburst behind them. Pillow in this environment cannot WRITE an
animated WebP (no SAVE_ALL handler), so the frames go out as PNGs and ffmpeg assembles them.

AND IT IS HALVED. The first pass, 156 frames at 344x460, came to 4.6MB - more than the rest of
the game's art together, for a screen the child sees once. Every second frame at 12fps still
reads as a cheer; this is a bounce loop, not a mouth that has to stay in sync.
"""
import os, shutil, subprocess, tempfile
from collections import deque
import numpy as np
from PIL import Image, ImageSequence
import imageio_ffmpeg

GAME = "HI02H12_L02_S01"
SRC  = os.path.join(GAME, "assets", "video", "last  page video.mp4")   # two spaces, as supplied
OUT  = os.path.join(GAME, "assets", "Images", "last_page_anim.webp")
TARGET_H = 392
TOL      = 14          # how far a pixel may sit from a background colour and still count as one
KEEP     = 2           # keep every KEEP-th frame
FF = imageio_ffmpeg.get_ffmpeg_exe()


def load_frames(path):
    """frames as RGB arrays, plus the source's frame interval in ms"""
    if path.lower().endswith((".gif", ".webp", ".png")):
        im = Image.open(path)
        out, durs, canvas = [], [], None
        for f in ImageSequence.Iterator(im):
            r = f.convert("RGBA")
            canvas = r.copy() if canvas is None else canvas
            if out: canvas.alpha_composite(r)
            out.append(np.array(canvas.convert("RGB")).astype(int))
            durs.append(f.info.get("duration", 60) or 60)
        return out, sum(durs) / len(durs)
    tmp = tempfile.mkdtemp()
    subprocess.run([FF, "-v", "error", "-y", "-i", path,
                    os.path.join(tmp, "f%05d.png")], check=True)
    names = sorted(os.listdir(tmp))
    out = [np.array(Image.open(os.path.join(tmp, n)).convert("RGB")).astype(int) for n in names]
    # the interval, read off the file rather than assumed
    r = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True)
    fps = 24.0
    for tok in r.stderr.replace(",", " ").split():
        if tok == "fps": pass
    import re
    m = re.search(r"(\d+(?:\.\d+)?) fps", r.stderr)
    if m: fps = float(m.group(1))
    shutil.rmtree(tmp, ignore_errors=True)
    return out, 1000.0 / fps


frames, interval = load_frames(SRC)
h, w, _ = frames[0].shape
print("source: %d frames, %dx%d, %.1fms apart" % (len(frames), w, h, interval))

# the background's own colours, taken off the border rather than assumed
border = np.concatenate([frames[0][0], frames[0][-1], frames[0][:, 0], frames[0][:, -1]])
keys = []
for px in border:
    if not any(abs(px - np.array(k)).max() <= TOL for k in keys):
        keys.append(tuple(px))
print("background colours on the border:", keys[:8], "..." if len(keys) > 8 else "")


def key_mask(rgb):
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
    return seen


frames = frames[::KEEP]
cut = []
for rgb in frames:
    a = np.dstack([rgb, np.where(key_mask(rgb), 0, 255)]).astype(np.uint8)
    cut.append(Image.fromarray(a, "RGBA"))

# ONE bounding box for the whole clip, so the bird does not jitter against its own crop
ys, xs = [], []
for c in cut:
    al = np.array(c)[..., 3]
    yy, xx = np.nonzero(al > 8)
    if len(yy): ys += [yy.min(), yy.max()]; xs += [xx.min(), xx.max()]
box = (max(0, min(xs) - 2), max(0, min(ys) - 2), min(w, max(xs) + 3), min(h, max(ys) + 3))
sc = TARGET_H / (box[3] - box[1])
size = (round((box[2] - box[0]) * sc), TARGET_H)
print("crop:", box, "->", size)
out = [c.crop(box).resize(size, Image.LANCZOS) for c in cut]

tmp = tempfile.mkdtemp()
for i, f in enumerate(out):
    f.save(os.path.join(tmp, "f%04d.png" % i))
fps = max(1, round(1000.0 / (interval * KEEP)))
subprocess.run([FF, "-v", "error", "-y", "-framerate", str(fps),
                "-i", os.path.join(tmp, "f%04d.png"),
                # ONCE, NOT FOREVER. In WebP's animation header 0 means infinite and N means
                # play N times, so this is 1. Asked for: the celebration should finish and stay
                # finished - a bird cheering on a loop behind a child who has already moved on
                # reads as the screen being stuck.
                "-loop", "1", "-c:v", "libwebp_anim", "-lossless", "0",
                "-q:v", "62", "-pix_fmt", "yuva420p", OUT], check=True)
shutil.rmtree(tmp, ignore_errors=True)
print("%s  %dx%d  %d frames  %d fps  %.1fs  %d KB"
      % (OUT, size[0], size[1], len(out), fps, len(out) / float(fps),
         os.path.getsize(OUT) // 1024))
