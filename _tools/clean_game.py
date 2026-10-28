# -*- coding: utf-8 -*-
"""Leave the game folder holding the game and nothing else.

    python _tools/clean_game.py [--dry]

vercel.json serves HI02H12_L02_S01/ as the site, so everything in it is either the game or dead
weight on every deploy - and its _backup/ alone was ~400 MB. After this the folder is exactly
    index.html   card.json   assets/
and everything else is MOVED (never deleted) to the project-root _backup/ (gitignored):
    _backup/HI02H11_L03_S02_backup/    the game's own old _backup/, whole
    _backup/docs_<date>/               VO manifests, CHANGES/README, _handoff/
    _backup/unused_assets_<date>/      assets no slide, gate or engine code plays or shows
    _backup/_server_HI02H11_L03_S02/   the older duplicate of the game at the project root
UNUSED is decided strictly - audio by whether a SLIDE (or the engine's code, comments stripped)
names it, not by the audio_text / assets maps, which list every clip ever recorded; pictures by
a quoted name or path anywhere in the card or engine; the Swifty mood sets are always kept, as
they are named at runtime. Clips that leave are also dropped from both card copies' audio maps,
or the landing's audio warm-up would ask for them and 404.
"""
import io, json, os, re, shutil, sys, time

sys.stdout.reconfigure(encoding="utf-8")
DRY = "--dry" in sys.argv
PROJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GAME = os.path.join(PROJ, "HI02H12_L02_S01")
BK = os.path.join(PROJ, "_backup")
DATE = time.strftime("%Y%m%d")
KEEP_TOP = {"index.html", "card.json", "assets"}
LOCKED = []


def move(src, dst):
    print("   %s  ->  %s" % (os.path.relpath(src, PROJ), os.path.relpath(dst, PROJ)))
    if DRY: return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.isdir(src) and os.path.isdir(dst):          # merge into an existing backup folder
        for name in os.listdir(src): move(os.path.join(src, name), os.path.join(dst, name))
        os.rmdir(src)
    else:
        try:
            shutil.move(src, dst)
        except PermissionError:
            # a file open in another program (Excel keeps its workbook locked) cannot move;
            # it is left where it is and named, rather than stopping the whole clean-up
            print("   !! LOCKED, left in place (close it and run again):", os.path.relpath(src, PROJ))
            LOCKED.append(src)


os.chdir(GAME)
card_txt = io.open("card.json", encoding="utf-8").read()
card = json.loads(card_txt)
card_use = json.dumps(card["slides"], ensure_ascii=False) + json.dumps(
    {k: v for k, v in card.items() if k not in ("slides", "assets")}, ensure_ascii=False)
eng = re.sub(r'(?s)<script type="application/json" id="cardData">.*?</script>', "",
             io.open("index.html", encoding="utf-8").read())
code = re.sub(r"(?m)//.*$", "", re.sub(r"/\*.*?\*/", "", eng, flags=re.S))


def q(txt, name):
    return re.search(r"""["'`/(]""" + re.escape(name) + r"""(["'`.?)\s]|$)""", txt) is not None


# ---- 1. unused assets
unused = []
for d, _, fs in os.walk("assets"):
    for f in fs:
        rel = os.path.join(d, f).replace(os.sep, "/"); stem = os.path.splitext(f)[0]
        if rel.startswith(("assets/VO/", "assets/SFX/")):
            used = ('"%s"' % stem in card_use) or q(code, stem) or q(code, f)
        elif re.match(r"assets/UI/sw_(head|lg)_", rel):
            used = True
        elif rel == "assets/swiftpal_buttons/index.html":
            used = False                                      # the button pack's own demo page
        else:
            used = q(card_txt, stem) or q(card_txt, f) or q(eng, stem) or q(eng, f)
        if not used: unused.append(rel)
gone_ids = {os.path.splitext(os.path.basename(r))[0] for r in unused if r.startswith(("assets/VO/", "assets/SFX/"))}
print("1. unused assets: %d files, %.1f MB" % (len(unused), sum(os.path.getsize(r) for r in unused) / 1e6))
for r in sorted(unused): move(os.path.join(GAME, r), os.path.join(BK, "unused_assets_" + DATE, r))
if not DRY:
    for d, _, _ in sorted(os.walk("assets"), key=lambda t: -len(t[0])):
        if not os.listdir(d): os.rmdir(d); print("   removed empty folder", d)


# ---- 2. drop the moved clips from both card copies' audio maps
def prune(txt, multiline):
    for key in ("audio", "audio_text"):
        a = txt.index('"assets": {'); k = txt.index('"%s": {' % key, a); s0 = txt.index("{", k)
        d, e = json.JSONDecoder().raw_decode(txt, s0)
        for i in gone_ids: d.pop(i, None)
        r = json.dumps(d, ensure_ascii=False) if not multiline else "{\n" + ",\n".join(
            "   %s: %s" % (json.dumps(x, ensure_ascii=False), json.dumps(y, ensure_ascii=False)) for x, y in d.items()) + "\n  }"
        txt = txt[:s0] + r + txt[e:]
    return txt


if gone_ids:
    t = prune(io.open("card.json", encoding="utf-8", newline="").read(), True)
    h = io.open("index.html", encoding="utf-8", newline="").read()
    head, mid, tail = re.split(r'(?s)(<script type="application/json" id="cardData">.*?</script>)', h, maxsplit=1)
    mid = prune(mid, False)
    assert json.loads(t) == json.loads(re.search(r'(?s)id="cardData">(.*?)</script>', mid).group(1))
    print("2. %d clip ids dropped from the card's audio maps" % len(gone_ids))
    if not DRY:
        io.open("card.json", "w", encoding="utf-8", newline="").write(t)
        io.open("index.html", "w", encoding="utf-8", newline="").write(head + mid + tail)

# ---- 3. everything at the top of the game folder that is not the game
print("3. game folder top level:")
for name in sorted(os.listdir(GAME)):
    if name in KEEP_TOP: continue
    src = os.path.join(GAME, name)
    dst = os.path.join(BK, "HI02H11_L03_S02_backup") if name == "_backup" else os.path.join(BK, "docs_" + DATE, name)
    move(src, dst)

# ---- 4. the old duplicate at the project root, and the empty root _handoff
print("4. project root:")
if os.path.isdir(os.path.join(PROJ, "_server_HI02H11_L03_S02")):
    move(os.path.join(PROJ, "_server_HI02H11_L03_S02"), os.path.join(BK, "_server_HI02H11_L03_S02"))
h = os.path.join(PROJ, "_handoff")
if os.path.isdir(h) and not os.listdir(h):
    print("   removed empty _handoff/")
    if not DRY: os.rmdir(h)
print("\n%s" % ("(dry run - nothing moved)" if DRY else "done. game folder: " + ", ".join(sorted(os.listdir(GAME)))))
