# -*- coding: utf-8 -*-
"""Cut the rise off the talking-peek animation, for the first transition.

    python _tools/peek_cut.py [start_ms]

peeking_talk10s.webp (115 frames, 16.1s, 1500x1500, lossy) spends its first ~3.3s bringing Swifty
up from below the edge - he peeks to his eyes by 0.9s, rises the rest of the way 2.65-3.3s, and is
settled at the top from ~3.8s. Asked for: on the first transition he is simply THERE, talking,
without the rise. So this writes assets/peeking_talk_up.webp: the same animation from `start_ms`
(default 3820, the first frame at the top) to the end, every later frame's own timing kept.

WHY NOT JUST DROP CHUNKS: the frames are deltas - each ANMF is a sub-rectangle blended onto the
previous canvas - so the first kept frame on its own is a fragment. Every frame is composited to
a full canvas (honouring each frame's blend and dispose flags), and the kept ones are re-encoded
with img2webp, which re-derives the deltas itself.
"""
import os, shutil, struct, subprocess, sys, tempfile
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "HI02H12_L02_S01", "assets")
SRC = os.path.join(ROOT, "peeking_talk10s.webp")
OUT = os.path.join(ROOT, "peeking_talk_up.webp")
START = int(sys.argv[1]) if len(sys.argv) > 1 else 3820
BIN = os.path.dirname(shutil.which("webpmux") or r"D:\anacodna\Library\bin\webpmux.exe")

b = open(SRC, "rb").read()
W = int.from_bytes(b[24:27], "little") + 1; H = int.from_bytes(b[27:30], "little") + 1
frames, i = [], 12
while i < len(b):
    t = b[i:i + 4]; n = struct.unpack("<I", b[i + 4:i + 8])[0]; p = b[i + 8:i + 8 + n]
    if t == b"ANMF":
        frames.append(dict(x=int.from_bytes(p[0:3], "little") * 2, y=int.from_bytes(p[3:6], "little") * 2,
                           d=int.from_bytes(p[12:15], "little"), nob=bool(p[15] & 2), disp=bool(p[15] & 1)))
    i += 8 + n + (n & 1)

tmp = tempfile.mkdtemp()
canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
t_ms, kept = 0, []
for k, f in enumerate(frames):
    fp = os.path.join(tmp, "f%03d.webp" % k)
    subprocess.run([os.path.join(BIN, "webpmux"), "-get", "frame", str(k + 1), SRC, "-o", fp],
                   check=True, capture_output=True)
    im = Image.open(fp).convert("RGBA")
    if f["nob"]:
        canvas.paste(im, (f["x"], f["y"]))
    else:
        canvas.alpha_composite(im, (f["x"], f["y"]))
    if t_ms >= START:
        png = os.path.join(tmp, "k%03d.png" % k); canvas.save(png); kept.append((png, f["d"]))
    if f["disp"]:
        canvas.paste(Image.new("RGBA", im.size, (0, 0, 0, 0)), (f["x"], f["y"]))
    t_ms += f["d"]

args = [os.path.join(BIN, "img2webp"), "-loop", "0", "-lossy", "-q", "82", "-m", "4"]
for png, d in kept:
    args += ["-d", str(d), png]
args += ["-o", OUT]
subprocess.run(args, check=True, capture_output=True)
shutil.rmtree(tmp, ignore_errors=True)
print("%s: %d of %d frames, from %.2fs, %.1fs long, %d KB"
      % (os.path.basename(OUT), len(kept), len(frames), START / 1000.0,
         sum(d for _, d in kept) / 1000.0, os.path.getsize(OUT) // 1024))
