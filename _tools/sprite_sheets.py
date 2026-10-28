# -*- coding: utf-8 -*-
"""Turn the three celebration sprite sheets into the game's three Swifty animations.

    python _tools/sprite_sheets.py

The sheets (6 cols x 6 rows = 36 frames, 504x896 cells, transparent) arrive in assets/Images and
leave as animated WebP:
  swiftie_happy_idle.png -> last_swifty_happy.webp     once     (80 ms/frame, 2.9 s)  - before and after the line
  swiftie_shabaash.png   -> last_swifty_shabaash.webp  once     (40 ms/frame, 1.44 s) - on "शाबाश!" (0.28-1.09 s of vo_well_done)
  swiftie_talk.png       -> last_swifty_talk.webp      once     (60 ms/frame, 2.16 s) - "आपने सभी सही जोड़ियाँ पहचान लीं।" (1.45-3.66 s)
ONE CROP FOR ALL THREE: the union of every frame's opaque box across all 108 frames, so swapping
from one animation to the next never moves Swifty on the screen. Scaled to 400 px wide (he is drawn
330 px wide) and encoded lossy q78. The sheets themselves go to _masters/art/.
"""
import os, shutil, subprocess, sys, tempfile
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
PROJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
IMG = os.path.join(PROJ, "HI02H12_L02_S01", "assets", "Images")
MASTERS = os.path.join(PROJ, "_masters", "art")
IMG2WEBP = shutil.which("img2webp") or r"D:\anacodna\Library\bin\img2webp.exe"
SHEETS = [("swiftie_happy_idle", "last_swifty_happy", 80, 1),     # each plays ONCE and stops - asked for
          ("swiftie_shabaash", "last_swifty_shabaash", 40, 1),
          ("swiftie_talk", "last_swifty_talk", 60, 1)]
COLS, ROWS, OUT_W = 6, 6, 400


def frames(path):
    sh = Image.open(path).convert("RGBA"); cw, ch = sh.width // COLS, sh.height // ROWS
    return [sh.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)) for r in range(ROWS) for c in range(COLS)]


def find(name):
    for d in (IMG, MASTERS):
        p = os.path.join(d, name + ".png")
        if os.path.exists(p): return p
    raise SystemExit("missing " + name + ".png")


all_frames = {s: frames(find(s)) for s, _, _, _ in SHEETS}
box = None
for fr in all_frames.values():
    for f in fr:
        b = f.split()[3].getbbox()
        if b: box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
pad = 6; W, H = all_frames[SHEETS[0][0]][0].size
box = (max(0, box[0] - pad), max(0, box[1] - pad), min(W, box[2] + pad), min(H, box[3] + pad))
k = OUT_W / float(box[2] - box[0]); size = (OUT_W, round((box[3] - box[1]) * k))
print("crop", box, "->", size)
# the three separate clips are no longer used by the game ([H11-177] plays one clip cut to the line);
# they are only written when asked for with --clips
for src, out, ms, loop in (SHEETS if "--clips" in sys.argv else []):
    tmp = tempfile.mkdtemp(); args = [IMG2WEBP, "-loop", str(loop), "-lossy", "-q", "78", "-m", "6"]
    for i, f in enumerate(all_frames[src]):
        p = os.path.join(tmp, "f%02d.png" % i); f.crop(box).resize(size, Image.LANCZOS).save(p); args += ["-d", str(ms), p]
    dst = os.path.join(IMG, out + ".webp")
    subprocess.run(args + ["-o", dst], check=True, capture_output=True); shutil.rmtree(tmp)
    print("%-30s %4d KB  %d frames x %d ms, loop=%d" % (out + ".webp", os.path.getsize(dst) // 1024, len(all_frames[src]), ms, loop))
os.makedirs(MASTERS, exist_ok=True)
for src, _, _, _ in SHEETS:
    p = os.path.join(IMG, src + ".png")
    if os.path.exists(p): shutil.move(p, os.path.join(MASTERS, src + ".png"))


# ---- [H11-177] ONE CLIP, CUT TO THE LINE ---------------------------------------------------------
# vo_end_shabash ("शाबाश! आज तो कमाल कर दिया!", 3.28 s): शाबाश! 0.30-1.30, आज तो 1.62-2.01,
# कमाल कर दिया! 2.19-2.84 (measured with poem_cues.phrases). Asked for: Swifty jumps exactly on
# "शाबाश", the animation lasts exactly as long as the VO, and it plays ONCE - no loop at the end.
# So a single clip, its frame timings laid out against the line:
#   0.00-0.30  shabaash frames 0-5    the arms come up (anticipation)
#   0.30-1.30  shabaash frames 6-23   the jump / cheer, on the word
#   1.30-1.62  shabaash frames 24-35  settle
#   1.62-3.28  talk frames 0-35       "आज तो कमाल कर दिया!"
# plus a still of its first frame for the screen before the line starts.
VO_MS = 3280
plan = [("swiftie_shabaash", range(0, 6), 300), ("swiftie_shabaash", range(6, 24), 1000),
        ("swiftie_shabaash", range(24, 36), 320), ("swiftie_talk", range(0, 36), VO_MS - 1620)]
tmp = tempfile.mkdtemp(); args = [IMG2WEBP, "-loop", "1", "-lossy", "-q", "78", "-m", "6"]; k = 0; total = 0
for sheet, idxs, span in plan:
    idxs = list(idxs); base = span // len(idxs); extra = span - base * len(idxs)
    for j, fi in enumerate(idxs):
        d = base + (1 if j < extra else 0)
        p = os.path.join(tmp, "e%03d.png" % k); all_frames[sheet][fi].crop(box).resize(size, Image.LANCZOS).save(p)
        args += ["-d", str(d), p]; k += 1; total += d
dst = os.path.join(IMG, "last_swifty_end.webp")
subprocess.run(args + ["-o", dst], check=True, capture_output=True)
all_frames["swiftie_shabaash"][0].crop(box).resize(size, Image.LANCZOS).save(os.path.join(IMG, "last_swifty_still.webp"), "WEBP", quality=85, method=6)
shutil.rmtree(tmp)
print("last_swifty_end.webp  %d KB, %d frames, %d ms (VO %d ms), loop=1 | last_swifty_still.webp %d KB"
      % (os.path.getsize(dst) // 1024, k, total, VO_MS, os.path.getsize(os.path.join(IMG, "last_swifty_still.webp")) // 1024))
