# -*- coding: utf-8 -*-
"""Re-encode every WebP lossy (stills q70, animations q60), from the ORIGINAL when a backup exists.
Stills wider than the 1333px stage come down to it; big animations come down to ~2x their drawn size.
Sprite strips/atlases keep their pixel size (their frame maths). A result is kept ONLY if smaller than
the original. Originals -> _backup/pre_webp_<date>/.   python3 _tools/webp_recompress.py"""
import os, shutil, time, io, re
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageSequence
G = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "HI02H12_L02_S01")
BK = os.path.join(G, "..", "_backup", "pre_webp_20261123")
QS, QA, STAGE_W = 64, 50, 1333
ANIM_CAP = {"peeking_talk_up.webp": 540, "new_landing_swiftee_anim.webp": 416, "sw_head_hint_anim.webp": 264, "sw_head_tryagain_anim.webp": 264, "sw_head_celebrate_anim.webp": 264,
            "last_swifty_end.webp": 465, "swifty_home_jump.webp": 465}   # end-mascot is drawn 330px wide
# every 2nd frame dropped, the kept frame shown for both (same total time, so VO sync holds)
HALVE = set(ANIM_CAP)
FIXED = re.compile(r"strip|atlas|walk|sheet", re.I)
def job(p):
    rel = os.path.relpath(p, G); orig = os.path.join(BK, rel)
    if not os.path.exists(orig):
        os.makedirs(os.path.dirname(orig), exist_ok=True); shutil.copy2(p, orig)
    src = os.path.getsize(orig); im = Image.open(orig); f = os.path.basename(p); buf = io.BytesIO()
    if getattr(im, "n_frames", 1) > 1:
        cap = ANIM_CAP.get(f); k = min(1, cap / max(im.size)) if cap else 1
        size = (round(im.size[0] * k), round(im.size[1] * k))
        frames, durs = [], []
        for i, fr in enumerate(ImageSequence.Iterator(im)):
            d = fr.info.get("duration", im.info.get("duration", 80))
            if f in HALVE and i % 2: durs[-1] += d; continue
            fr = fr.convert("RGBA"); frames.append(fr if k == 1 else fr.resize(size, Image.LANCZOS)); durs.append(d)
        frames[0].save(buf, "WEBP", save_all=True, append_images=frames[1:], duration=durs,
                       loop=im.info.get("loop", 0), quality=QA, method=4, allow_mixed=False)
    else:
        im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
        if im.size[0] > STAGE_W and not FIXED.search(f) and f != "title_screen.webp":   # title art fills a 16:9 card, keep it full size
            im = im.resize((STAGE_W, round(im.size[1] * STAGE_W / im.size[0])), Image.LANCZOS)
        im.save(buf, "WEBP", quality=QS, method=6, alpha_quality=75)
    out = buf.getvalue(); cur = os.path.getsize(p)
    if len(out) < min(src, cur):
        open(p, "wb").write(out); return rel, src, len(out)
    return rel, src, cur
if __name__ == "__main__":
    ps = [os.path.join(r, f) for r, _, fs in os.walk(os.path.join(G, "assets")) for f in fs if f.endswith(".webp")]
    with ProcessPoolExecutor() as ex: res = list(ex.map(job, ps))
    a = sum(r[1] for r in res); b = sum(r[2] for r in res)
    bad = [r for r in res if r[2] > r[1]]
    print("webp: %.2f MB (originals) -> %.2f MB; larger than original: %s" % (a / 1e6, b / 1e6, bad))
