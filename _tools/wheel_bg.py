# -*- coding: utf-8 -*-
"""Rebuild the ferris-wheel background exactly as the SVG places it.

    python _tools/wheel_bg.py

THE FIRST EXTRACTION GOT TWO THINGS WRONG. It took image0 whole and it baked in a Gaussian
blur. Reading the file properly: the rect is 1920x1094 at the origin and the pattern transform
is matrix(0.000784029 0 0 0.00137638 -0.351456 -0.543669) in objectBoundingBox units, which
means the 2172x1223 source is drawn at 3269x1841 and panned - so only x 448..1724, y 395..1122
of it is ever on screen. And filter0_f is feGaussianBlur stdDeviation="0", i.e. no blur at all.
The supplied reference shows a crisp fence and crisp trees, which is why it did not match.
"""
import base64, io, os, re
from PIL import Image

SVG = os.path.join("HI02H12_L02_S01", "assets", "Images", "wheel svg.svg")
OUT = os.path.join("HI02H12_L02_S01", "assets", "Images", "wheel_bg.webp")
RW, RH = 1920, 1094                     # the rect the pattern fills
SX, SY, TX, TY = 0.000784029, 0.00137638, -0.351456, -0.543669

raw = io.open(SVG, encoding="utf-8", errors="replace").read()
m = re.search(r'<image id="image0_[^"]*"[^>]*?xlink:href="data:image/(\w+);base64,([^"]+)"', raw)
assert m, "image0 not found"
src = Image.open(io.BytesIO(base64.b64decode(m.group(2)))).convert("RGB")
iw, ih = src.size
print("source image0: %dx%d (%s)" % (iw, ih, m.group(1)))

# the source pixels that land inside the rect: solve  stage = RW*(SX*u + TX)  for stage 0..RW
u0, u1 = (-TX) / SX, (1 - TX) / SX
v0, v1 = (-TY) / SY, (1 - TY) / SY
print("visible crop: x %.1f..%.1f  y %.1f..%.1f  of %dx%d" % (u0, u1, v0, v1, iw, ih))
out = src.crop((round(u0), round(v0), round(u1), round(v1))).resize((RW, RH), Image.LANCZOS)
out.save(OUT, "WEBP", quality=86, method=6)
print("-> %s  %dx%d  %d KB  (no blur: filter0_f is stdDeviation=0)"
      % (OUT, RW, RH, os.path.getsize(OUT) // 1024))
