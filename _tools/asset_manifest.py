# -*- coding: utf-8 -*-
"""Write the loading bar's size table into index.html, from the files actually on disk.

    python _tools/asset_manifest.py        (restamp.py runs this too)

The table sits between the markers  /*@ASSET_MANIFEST*/ ... /*@END_ASSET_MANIFEST*/  as
[["assets/…/file.ext", bytes], …], smallest first - the order the preloader fetches in, so the
pictures land in the first seconds and never wait behind a video. Every file under assets/ is
listed: the game folder holds only what the game uses (_tools/clean_game.py keeps it that way).
"""
import json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
GAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "HI02H12_L02_S01")
SRC = os.path.join(GAME, "index.html")


def build():
    rows = []
    for d, _, fs in os.walk(os.path.join(GAME, "assets")):
        for f in fs:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, GAME).replace(os.sep, "/")
            if f.startswith(".") or f.lower() in ("thumbs.db", "readme.txt"): continue
            rows.append([rel, os.path.getsize(p)])
    rows.sort(key=lambda r: (r[1], r[0]))
    return rows


def main():
    raw = open(SRC, "rb").read(); t = raw.decode("utf-8")
    rows = build()
    js = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    new, n = re.subn(r"/\*@ASSET_MANIFEST\*/.*?/\*@END_ASSET_MANIFEST\*/",
                     lambda m: "/*@ASSET_MANIFEST*/" + js + "/*@END_ASSET_MANIFEST*/", t, flags=re.S)
    if n != 1: sys.exit("asset manifest markers not found in index.html")
    if new != t: open(SRC, "wb").write(new.encode("utf-8"))
    print("asset manifest: %d files, %.1f MB" % (len(rows), sum(r[1] for r in rows) / 1e6))


if __name__ == "__main__":
    main()
