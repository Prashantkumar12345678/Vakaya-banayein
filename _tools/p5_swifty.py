# -*- coding: utf-8 -*-
"""The talking Swifty for the swing game's opening (P5).

    python _tools/p5_swifty.py

From _masters/art/swiftie_talk.png (6x6 sheet, 504x896 cells, transparent) - the same sheet the end
screen is cut from - it writes:
  assets/UI/sw_explain_talk.webp   every 2nd frame (18), 120ms each, LOOPING: plays while the line is
                                   spoken - half the bytes of all 36 (360KB vs 720KB), mouth still moves
  assets/UI/sw_explain_still.webp  frame 0 alone: standing in the corner before / after he speaks
Cropped to the opaque box of all 36 frames (so the two never jump against each other) and scaled to
280px wide - he is drawn at most ~255px wide in the corner. Lossy q78, like the other Swifty clips.
"""
import os, shutil, subprocess, tempfile
from PIL import Image

PROJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
UI = os.path.join(PROJ, "HI02H12_L02_S01", "assets", "UI")
IMG2WEBP = shutil.which("img2webp") or r"D:\anacodna\Library\bin\img2webp.exe"
sh = Image.open(os.path.join(PROJ, "_masters", "art", "swiftie_talk.png")).convert("RGBA")
cw, ch = sh.width // 6, sh.height // 6
frames = [sh.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)) for r in range(6) for c in range(6)]
box = None
for f in frames:
    b = f.split()[3].getbbox()
    if b: box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
box = (max(0, box[0] - 4), max(0, box[1] - 4), min(cw, box[2] + 4), min(ch, box[3] + 4))
W = 280; size = (W, round((box[3] - box[1]) * W / (box[2] - box[0])))
tmp = tempfile.mkdtemp(); args = [IMG2WEBP, "-loop", "0", "-lossy", "-q", "78", "-m", "6"]
for i, f in enumerate(frames[::2]):
    p = os.path.join(tmp, "f%02d.png" % i); f.crop(box).resize(size, Image.LANCZOS).save(p); args += ["-d", "120", p]
subprocess.run(args + ["-o", os.path.join(UI, "sw_explain_talk.webp")], check=True, capture_output=True)
frames[0].crop(box).resize(size, Image.LANCZOS).save(os.path.join(UI, "sw_explain_still.webp"), "WEBP", quality=85, method=6)
shutil.rmtree(tmp)
for n in ("sw_explain_talk.webp", "sw_explain_still.webp"):
    print("%-24s %4d KB  %dx%d" % (n, os.path.getsize(os.path.join(UI, n)) // 1024, size[0], size[1]))
