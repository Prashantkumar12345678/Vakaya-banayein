# -*- coding: utf-8 -*-
"""Make the shipped game as small as it can be without changing what anyone sees or hears.

    python _tools/optimize_assets.py [--dry]

Nothing is deleted. Every file this moves or replaces goes to
    HI02H12_L02_S01/_backup/pre_optimize_<date>/<its path under the game>
so any step can be undone by copying it back.

  1. UNUSED FILES LEAVE THE GAME FOLDER. The list is decided the strict way: a file stays if the
     running game was seen requesting it (every slide, the landing, the three gates, the end), OR
     its name appears in index.html / card.json as a quoted token or a path - a loose "the name
     is somewhere in the text" match kept files like chuha.png alive only because vo_name_chuha
     exists. The Swifty head/large sets are always kept: they are named at runtime from a mood
     ("sw_head_" + expr + ".webp"), so no quote of the full name exists.
  2. STILLS TO WEBP. The PNG and GIF art the game still names by extension is converted and the
     references in both card copies and the engine follow it.
  3. ANIMATIONS LIGHTER. Each animated WebP is re-encoded lossy at q80, composited frame by frame
     (the frames are deltas); the transition Swifty also comes down from a 1500px canvas to 500px -
     it is never drawn taller than 250px. A result is kept only if it is smaller.
  4. VIDEOS TO WEBM. VP9 + Opus next to each MP4; the engine asks the browser which it can play
     and takes the WebM when it can, so the MP4 stays only as the fallback.
"""
import io, json, os, re, shutil, struct, subprocess, sys, tempfile, time
from PIL import Image
import imageio_ffmpeg

sys.stdout.reconfigure(encoding="utf-8")
DRY = "--dry" in sys.argv
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "HI02H12_L02_S01")
BK = os.path.join(ROOT, "..", "_backup", "pre_optimize_" + time.strftime("%Y%m%d"))   # project root, not the shipped folder
FF = imageio_ffmpeg.get_ffmpeg_exe()
BIN = os.path.dirname(shutil.which("webpmux") or r"D:\anacodna\Library\bin\webpmux.exe")
os.chdir(ROOT)


def kb(p): return os.path.getsize(p) / 1024.0


def backup(rel):
    dst = os.path.join(BK, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst): shutil.copy2(rel, dst)


def move_out(rel):
    dst = os.path.join(BK, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(rel, dst)


# ------------------------------------------------------------------------------------ 1. unused
UNUSED_EXTRA = ["assets/peeking_talk10s.webp", "assets/Images/pic_hathini.png"]   # superseded sources
KEEP_ALWAYS = re.compile(r"assets/UI/sw_(head|lg)_")
used_runtime = set(json.load(io.open(sys.argv[sys.argv.index("--runtime") + 1], encoding="utf-8"))) \
    if "--runtime" in sys.argv else set()
text = io.open("index.html", encoding="utf-8").read() + io.open("card.json", encoding="utf-8").read()


def quoted(name):
    return re.search(r"""["'`/(]""" + re.escape(name) + r"""(["'`.?)\s]|$)""", text) is not None


STILL_SOURCES = {"assets/images/title.png", "assets/images/mor title image.png", "assets/images/morni title image.png",
                 "assets/ui/hint.png", "assets/ui/hint_active.png", "assets/ui/loader.gif"}
unused = []
for d, _, fs in os.walk("assets"):
    for f in fs:
        rel = os.path.join(d, f).replace(os.sep, "/")
        if "Voiceovers Updated" in rel or rel in UNUSED_EXTRA:
            unused.append(rel); continue
        if KEEP_ALWAYS.match(rel) or rel in used_runtime: continue
        if rel.lower() in STILL_SOURCES: continue   # converted in step 2, under whatever case it has
        if quoted(os.path.splitext(f)[0]) or quoted(f): continue
        if f == "README.txt" or rel.startswith("assets/swiftpal_buttons/"): continue
        unused.append(rel)
tot = sum(os.path.getsize(r) for r in unused)
print("1. unused: %d files, %.1f MB" % (len(unused), tot / 1e6))
for r in sorted(unused): print("     ", r)
if not DRY:
    for r in unused: move_out(r)
    try: os.rmdir("assets/Voiceovers Updated")
    except OSError: pass

# ------------------------------------------------------------------------------------ 2. stills
STILLS = {   # old path -> new path; every quoted occurrence of the old path follows it
    "assets/Images/title.png": "assets/Images/title.webp",
    "assets/Images/mor title image.png": "assets/Images/mor_title.webp",
    "assets/Images/morni title image.png": "assets/Images/morni_title.webp",
    "assets/UI/hint.png": "assets/UI/hint.webp",
    "assets/UI/hint_active.png": "assets/UI/hint_active.webp",
}


def rewrite_refs(pairs):
    for fn in ("index.html", "card.json"):
        raw = open(fn, "rb").read(); s = raw.decode("utf-8")
        for a, b in pairs:
            s = s.replace(a, b)
        if not DRY: open(fn, "wb").write(s.encode("utf-8"))


done = []
for old, new in STILLS.items():
    src = old if os.path.exists(old) else None
    if not src:   # the file may exist under another case (Title.png) - Windows hides that, Linux will not
        d, f = os.path.split(old)
        hit = [x for x in os.listdir(d) if x.lower() == f.lower()]
        src = os.path.join(d, hit[0]).replace(os.sep, "/") if hit else None
    if not src: print("2. missing", old); continue
    a = kb(src)
    if not DRY:
        backup(src)
        Image.open(src).save(new, "WEBP", quality=88, method=6)
        move_out(src)
    print("2. %-38s %6.0f KB -> %-32s %s" % (src, a, new, "" if DRY else "%6.0f KB" % kb(new)))
    done.append((old, new))
# the loader GIF animates - ffmpeg writes animated WebP
if os.path.exists("assets/UI/loader.gif"):
    a = kb("assets/UI/loader.gif")
    if not DRY:
        backup("assets/UI/loader.gif")
        subprocess.run([FF, "-v", "error", "-y", "-i", "assets/UI/loader.gif", "-c:v", "libwebp_anim", "-lossless", "0",
                        "-q:v", "80", "-loop", "0", "assets/UI/loader.webp"], check=True)
        move_out("assets/UI/loader.gif")
    print("2. %-38s %6.0f KB -> assets/UI/loader.webp %s" % ("assets/UI/loader.gif", a, "" if DRY else "%6.0f KB" % kb("assets/UI/loader.webp")))
    done.append(("assets/UI/loader.gif", "assets/UI/loader.webp"))
rewrite_refs(done)

# ------------------------------------------------------------------------------------ 3. animations
def frames_of(path):
    b = open(path, "rb").read(); fr, i = [], 12
    W = int.from_bytes(b[24:27], "little") + 1; H = int.from_bytes(b[27:30], "little") + 1
    while i < len(b):
        t = b[i:i + 4]; n = struct.unpack("<I", b[i + 4:i + 8])[0]; p = b[i + 8:i + 8 + n]
        if t == b"ANMF":
            fr.append(dict(x=int.from_bytes(p[0:3], "little") * 2, y=int.from_bytes(p[3:6], "little") * 2,
                           d=int.from_bytes(p[12:15], "little"), nob=bool(p[15] & 2), disp=bool(p[15] & 1)))
        i += 8 + n + (n & 1)
    return W, H, fr


def reencode_anim(path, max_side=None, q=80):
    W, H, fr = frames_of(path)
    if not fr: return None
    tmp = tempfile.mkdtemp(); canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0)); outs = []
    k = 1.0 if not max_side else min(1.0, max_side / float(max(W, H)))
    size = (max(1, round(W * k)), max(1, round(H * k)))
    for j, f in enumerate(fr):
        fp = os.path.join(tmp, "f%03d.webp" % j)
        subprocess.run([os.path.join(BIN, "webpmux"), "-get", "frame", str(j + 1), path, "-o", fp], check=True, capture_output=True)
        im = Image.open(fp).convert("RGBA")
        if f["nob"]: canvas.paste(im, (f["x"], f["y"]))
        else: canvas.alpha_composite(im, (f["x"], f["y"]))
        png = os.path.join(tmp, "k%03d.png" % j)
        (canvas if k == 1.0 else canvas.resize(size, Image.LANCZOS)).save(png); outs.append((png, f["d"]))
        if f["disp"]: canvas.paste(Image.new("RGBA", im.size, (0, 0, 0, 0)), (f["x"], f["y"]))
    out = os.path.join(tmp, "out.webp")
    # KEEP THE FILE'S OWN LOOP COUNT. Writing "-loop 0" turned two play-once animations (landing
    # Swifty, celebrating Swifty: loop=1) into endless loops - reported as the landing gif that
    # "never stops". The ANIM chunk's count is read back and reused.
    ab = open(path, "rb").read(); ai = ab.find(b"ANIM")
    loops = struct.unpack("<H", ab[ai + 12:ai + 14])[0] if ai >= 0 else 0
    args = [os.path.join(BIN, "img2webp"), "-loop", str(loops), "-lossy", "-q", str(q), "-m", "6"]
    for png, d in outs: args += ["-d", str(d), png]
    subprocess.run(args + ["-o", out], check=True, capture_output=True)
    return out, tmp, size


ANIMS = {"assets/peeking_talk_up.webp": 500, "assets/UI/new_landing_swiftee_anim.webp": None,
         "assets/Images/last_page_anim.webp": None, "assets/UI/sw_lg_hint_anim.webp": None,
         "assets/UI/sw_lg_celebrating_anim.webp": None, "assets/UI/sw_head_celebrate_anim.webp": None,
         "assets/UI/sw_head_hint_anim.webp": None, "assets/UI/sw_head_tryagain_anim.webp": None}
for rel, side in ANIMS.items():
    if not os.path.exists(rel): continue
    a = kb(rel)
    if DRY: print("3. %-42s %6.0f KB (would re-encode%s)" % (rel, a, ", max %dpx" % side if side else "")); continue
    got = reencode_anim(rel, side)
    if not got: continue
    out, tmp, size = got; b = kb(out)
    if b < a * 0.95:
        backup(rel); shutil.copy2(out, rel)
        print("3. %-42s %6.0f KB -> %6.0f KB  %dx%d" % (rel, a, b, size[0], size[1]))
    else:
        print("3. %-42s %6.0f KB   kept (re-encode was %.0f KB)" % (rel, a, b))
    shutil.rmtree(tmp, ignore_errors=True)

# ------------------------------------------------------------------------------------ 4. video
for f in sorted(os.listdir("assets/video")):
    if not f.endswith(".mp4"): continue
    src = "assets/video/" + f; dst = src[:-4] + ".webm"
    a = kb(src)
    if DRY: print("4. %-32s %6.0f KB -> webm" % (src, a)); continue
    # 960 wide: the poem frame is drawn ~570 design px (~750 real px on a 1920 screen) wide, so 1280
    # was paying for pixels nobody sees. crf 38 + 48k Opus - about half the MP4.
    subprocess.run([FF, "-v", "error", "-y", "-i", src, "-vf", "scale=960:-2", "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "38",
                    "-row-mt", "1", "-deadline", "good", "-cpu-used", "2", "-c:a", "libopus", "-b:a", "48k", dst], check=True)
    print("4. %-32s %6.0f KB -> %6.0f KB webm" % (src, a, kb(dst)))
print("\ndone%s" % (" (dry run)" if DRY else " - originals in " + BK))
