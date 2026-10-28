# -*- coding: utf-8 -*-
"""Give every asset URL a fresh ?v= token, so a replaced file actually reaches the browser.

The token exists because assets live at fixed paths: re-recording a clip or redrawing a button
changes the FILE and not its URL, and a browser holding the old bytes never asks again. That cost
most of an afternoon - a corrected clip reported wrong three times while the server had the right
one - and then cost it AGAIN, because the token was written once and I kept editing assets
underneath it. A stamp that never changes is a stamp that stops working.

So: run this after ANY asset changes, before committing. It takes a second and it is the only
thing standing between a fixed asset and a child still getting the old one.
"""
import re, sys, time, os
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "HI02H12_L02_S01", "index.html")
raw = open(SRC, "rb").read()
crlf, lf = raw.count(b"\r\n"), raw.count(b"\n") - raw.count(b"\r\n")
t = raw.decode("utf-8")
m = re.search(r'const AUDIO_BUILD = "(\d+)"', t)
if not m:
    sys.exit("AUDIO_BUILD नहीं मिला — क्या cache-bust वाला हिस्सा हटा दिया गया?")
old = m.group(1); new = time.strftime("%Y%m%d%H%M%S")
n = t.count("?v=" + old)
t = t.replace('const AUDIO_BUILD = "%s"' % old, 'const AUDIO_BUILD = "%s"' % new)
t = t.replace("?v=" + old, "?v=" + new)
out = t.encode("utf-8")
assert out.count(b"\r\n") == crlf and out.count(b"\n") - out.count(b"\r\n") == lf, "line endings बदल गए"
open(SRC, "wb").write(out)
print("build %s -> %s   (+%d CSS asset paths)" % (old, new, n))

# the loading bar weighs each file by its real size - refresh that table whenever assets change
import subprocess
subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "asset_manifest.py")], check=True)
