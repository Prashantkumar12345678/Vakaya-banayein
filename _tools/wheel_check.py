# -*- coding: utf-8 -*-
"""Render the wheel slide as a flat board and measure it against the supplied reference.

    python _tools/wheel_check.py

Renders a temporary copy of index.html with the focus scale, the blur, the riders and the
nameplates suppressed - so what is on screen is the same neutral board the reference shows - then
compares the hub, the six cushions and the blue frame. Everything is reported in the stage's own
1920x1080 coordinates, so a number here can be pasted straight into the CSS.
"""
import io, os, re, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from PIL import Image
from scipy import ndimage

GAME = "HI02H12_L02_S01"
REF = os.path.join(os.environ.get("REFDIR", ""), "36.png")
SHOT = os.path.join(os.environ.get("SHOTDIR", "."), "board.png")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# The transform on a seat carries its POSITION now, so the old rule that zeroed it on the
# focused bucket parked that bucket on the axle. Only the scale factor is stripped, and only
# once the opening has finished - the reference is a flat board with all six the same size.
INJECT = """<style id="cmpOnly">
.fw-seat{opacity:1 !important;filter:none !important;}
.fw-disc,.fw-frame{filter:none !important;}
.fw-swing{animation:none !important;transform:none !important;}
.fw-name,.fw-riders,.fw-listen,.dev-banner,.dev-nav{display:none !important;}
.fw-ask{opacity:1 !important;transform:none !important;}
.fw-opt{color:transparent !important;}
</style>
<script>setTimeout(function(){
  document.querySelectorAll(".fw-seat").forEach(function(el){
    var m = /translate\([-0-9.]+px, [-0-9.]+px\)/.exec(el.style.transform || "");
    if(m) el.style.transform = m[0];
  });
}, 4200);</script></head>"""

tmp = os.path.join(GAME, "_cmp.html")
io.open(tmp, "w", encoding="utf-8", newline="").write(
    io.open(os.path.join(GAME, "index.html"), encoding="utf-8").read().replace("</head>", INJECT, 1))
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--allow-file-access-from-files", "--force-device-scale-factor=1",
                "--window-size=1920,1080", "--virtual-time-budget=9000",
                "--screenshot=" + SHOT,
                "file:///" + os.path.abspath(tmp).replace("\\", "/") + "?slide=17&still=1"],
               capture_output=True)
os.remove(tmp)


def measure(path):
    a = np.array(Image.open(path).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    out = {}
    m = (r > 150) & (g < 70) & (b < 70) & (r > g + 90)
    lab, n = ndimage.label(ndimage.binary_closing(m, np.ones((5, 5))))
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        cx, cy = (xs.min() + xs.max()) / 2., (ys.min() + ys.max()) / 2.
        w, h = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        if abs(cx - 965) < 90 and 60 < w < 160 and 60 < h < 160:
            out["hub"] = (cx, cy, w, h)
    m = (b > 150) & (b > r + 55) & (b > g + 90) & (r > 70) & (r < 170)
    lab, n = ndimage.label(ndimage.binary_closing(m, np.ones((7, 7))))
    cu = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) < 2500: continue
        w = xs.max() - xs.min() + 1
        if not (120 < w < 260): continue
        cu.append(((xs.min() + xs.max()) / 2., (ys.min() + ys.max()) / 2., w))
    out["cush"] = sorted(cu, key=lambda t: (round(t[1] / 40), t[0]))
    m = (b > 170) & (b > r + 70) & (g > 60) & (g < 150) & (r < 120)
    ys, xs = np.nonzero(m)
    out["frame"] = (xs.min(), xs.max(), ys.min(), ys.max())
    return out


R, M = measure(REF), measure(SHOT)
print("            %-28s %-28s" % ("संदर्भ", "अभी"))
print("हब        : %-28s %-28s" % ("%.1f,%.1f  %dx%d" % R["hub"], "%.1f,%.1f  %dx%d" % M["hub"]))
print("           Δ %+.1f , %+.1f" % (M["hub"][0] - R["hub"][0], M["hub"][1] - R["hub"][1]))
print("ढाँचा     : %-28s %-28s" % ("x%d-%d y%d-%d" % R["frame"], "x%d-%d y%d-%d" % M["frame"]))
print("           Δ बायाँ %+d  दायाँ %+d  ऊपर %+d  नीचे %+d"
      % tuple(M["frame"][i] - R["frame"][i] for i in range(4)))
print("गद्दियाँ (%d बनाम %d):" % (len(R["cush"]), len(M["cush"])))
if len(R["cush"]) == len(M["cush"]):
    worst = 0
    for (ax, ay, aw), (bx, by, bw) in zip(R["cush"], M["cush"]):
        d = max(abs(bx - ax), abs(by - ay))
        worst = max(worst, d)
        print("   संदर्भ %7.1f,%7.1f w%3d   अभी %7.1f,%7.1f w%3d    Δ %+5.1f , %+5.1f  Δw %+d"
              % (ax, ay, aw, bx, by, bw, bx - ax, by - ay, bw - aw))
    print("\nसबसे बड़ा खिसकाव: %.1f px" % worst)
else:
    for c in M["cush"]: print("   अभी %7.1f,%7.1f w%3d" % c)
