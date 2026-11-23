# -*- coding: utf-8 -*-
"""WAV -> AAC .m4a (mono) for the shipped game; BGM re-encoded lighter. Originals -> _backup/pre_m4a_<date>/.
    python3 _tools/audio_to_m4a.py"""
import os, shutil, subprocess, time, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
G = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "HI02H12_L02_S01")
BK = os.path.join(G, "..", "_backup", "pre_m4a_" + time.strftime("%Y%m%d"))
a = b = 0
for sub, rate in (("VO", "48k"), ("SFX", "64k")):
    d = os.path.join(G, "assets", sub)
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f); stem, ext = os.path.splitext(f)
        if ext not in (".wav", ".m4a"): continue
        r = "32k" if stem.startswith("bgm_") else rate
        out = os.path.join(d, stem + ".m4a"); tmp = out + ".tmp.m4a"
        subprocess.run([FF, "-v", "error", "-y", "-i", p, "-ac", "1", "-c:a", "aac", "-b:a", r, "-movflags", "+faststart", tmp], check=True)
        a += os.path.getsize(p); b += os.path.getsize(tmp)
        os.makedirs(os.path.join(BK, sub), exist_ok=True); shutil.move(p, os.path.join(BK, sub, f))
        os.replace(tmp, out)
print("audio %.1f MB -> %.1f MB" % (a / 1e6, b / 1e6))
