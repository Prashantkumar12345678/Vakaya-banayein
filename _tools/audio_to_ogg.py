# -*- coding: utf-8 -*-
"""WAV/M4A -> Ogg Opus for the shipped game. Every output is verified SMALLER than its source;
if not, it is re-encoded at ~70% of the source bitrate; if still not, the source is kept (reported).
Originals -> _backup/pre_ogg_<date>/.   python3 _tools/audio_to_ogg.py"""
import os, shutil, subprocess, time, json, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
G = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "HI02H02_L02_S01")
BK = os.path.join(G, "..", "_backup", "pre_ogg_" + time.strftime("%Y%m%d"))
def dur(p):
    out = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
    import re; m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0
def enc(src, out, kbps):
    subprocess.run([FF, "-v", "error", "-y", "-i", src, "-vn", "-c:a", "libopus", "-b:a", "%dk" % kbps,
                    "-vbr", "constrained", "-application", "audio", "-map_metadata", "-1", out], check=True)
rep = {"ok": [], "kept": []}; a = b = 0
for sub in ("VO", "SFX"):
    d = os.path.join(G, "assets", sub)
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f); stem, ext = os.path.splitext(f)
        if ext not in (".wav", ".m4a"): continue
        src_kbps = os.path.getsize(p) * 8 / 1000 / max(0.05, dur(p))
        rate = 64 if ext == ".wav" else max(16, int(min(64, src_kbps * 0.75)))
        tmp = os.path.join(d, stem + ".tmp.ogg")
        enc(p, tmp, rate)
        if os.path.getsize(tmp) >= os.path.getsize(p):
            enc(p, tmp, max(8, int(src_kbps * 0.70)))
        if os.path.getsize(tmp) >= os.path.getsize(p):
            os.remove(tmp); rep["kept"].append(f); continue
        a += os.path.getsize(p); b += os.path.getsize(tmp)
        rep["ok"].append([f, os.path.getsize(p), os.path.getsize(tmp)])
        os.makedirs(os.path.join(BK, sub), exist_ok=True); shutil.move(p, os.path.join(BK, sub, f))
        os.replace(tmp, os.path.join(d, stem + ".ogg"))
print("converted %d files: %.2f MB -> %.2f MB; kept (ogg not smaller): %s" % (len(rep["ok"]), a / 1e6, b / 1e6, rep["kept"]))
json.dump(rep, open(os.path.join(BK, "report.json"), "w"), indent=1)
