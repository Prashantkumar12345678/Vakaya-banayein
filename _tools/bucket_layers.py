# -*- coding: utf-8 -*-
"""Split the supplied Buket.svg into the two layers the wheel needs.

    python _tools/bucket_layers.py

THE BUCKET ARRIVED AS ONE FLAT PICTURE and everything since has been working around that. To make
an animal look like it is sitting IN the gondola rather than on it, something has to be drawn in
FRONT of its legs - and with one flat image there was nothing to draw, so the front was faked by
clipping a second copy of the same picture along a polygon traced from the cushion. That polygon
had to be positioned by eye against the animal, and it went wrong in both directions several
times: too high and the cushion covered the bird's breast, too low and its legs hung out.

Buket.svg is the same bucket with its layers kept apart, which removes the guesswork entirely:

  image0  1327x1186 -> rect (0,0,271,242)      the hanger and the purple seat   = BACK
  image1  2168x725  -> rect (14,154,243,83)    the red basket                   = FRONT
  image2  718x194   -> rect (50.4,179.6,...)   the nameplate (already shipped)

So the rider simply goes between them. The red basket is in front of its legs because the artist
drew it that way, not because of a number I chose.

The rects are read off the file, including the pattern transforms - image1's is
matrix(0.000471122 0 0 0.00137931 -0.0106968 0), which draws it 248.2 wide starting 2.6px left of
its rect, not 243 wide at x=14.
"""
import base64, io, os, re, sys
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")

IM = os.path.join("HI02H12_L02_S01", "assets", "Images")
SVG = os.path.join(IM, "Buket.svg")
BW, BH = 271.0, 242.0            # the bucket's own coordinate space in the SVG

raw = io.open(SVG, encoding="utf-8", errors="replace").read()
layer = {}
for m in re.finditer(r'<image id="(image(\d+)_[^"]*)"[^>]*?xlink:href="data:image/\w+;base64,([^"]+)"', raw):
    layer[int(m.group(2))] = Image.open(io.BytesIO(base64.b64decode(m.group(3)))).convert("RGBA")
assert 0 in layer and 1 in layer, "expected image0 and image1 in Buket.svg"

# ---- BACK: the hanger and the seat, filling the bucket rect ---------------------------------
back = layer[0].resize((340, 304), Image.LANCZOS)      # same render size the CSS already uses
back.save(os.path.join(IM, "wheel_bucket.webp"), "WEBP", quality=92, method=6)
print("wheel_bucket.webp  (back: hanger + seat)  %dx%d  %d KB"
      % (back.size[0], back.size[1], os.path.getsize(os.path.join(IM, "wheel_bucket.webp")) // 1024))

# ---- FRONT: the red basket -------------------------------------------------------------------
# rect (14,154,243,83) with matrix(0.000471122 0 0 0.00137931 -0.0106968 0) in objectBoundingBox
sx, sy, tx, ty = 0.000471122, 0.00137931, -0.0106968, 0.0
rx, ry, rw, rh = 14.0, 154.0, 243.0, 83.0
w_bucket = layer[1].size[0] * sx * rw          # drawn width in bucket units
h_bucket = layer[1].size[1] * sy * rh
x_bucket = rx + tx * rw
y_bucket = ry + ty * rh
print("front layer sits at (%.1f, %.1f) size %.1f x %.1f in the bucket's own 271x242"
      % (x_bucket, y_bucket, w_bucket, h_bucket))

SEAT_W, SEAT_H = 249.0, 222.0                  # what a seat renders at in the game
kx, ky = SEAT_W / BW, SEAT_H / BH
box = dict(left=x_bucket * kx, top=y_bucket * ky, width=w_bucket * kx, height=h_bucket * ky)
print("  -> in seat units: left %.1f  top %.1f  width %.1f  height %.1f"
      % (box["left"], box["top"], box["width"], box["height"]))

front = layer[1].resize((int(round(box["width"] * 2)), int(round(box["height"] * 2))), Image.LANCZOS)
front.save(os.path.join(IM, "wheel_bucket_front.webp"), "WEBP", quality=92, method=6)
print("wheel_bucket_front.webp  %dx%d  %d KB"
      % (front.size[0], front.size[1],
         os.path.getsize(os.path.join(IM, "wheel_bucket_front.webp")) // 1024))

print("\nCSS for .fw-front:")
print("  left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;"
      % (box["left"], box["top"], box["width"], box["height"]))
