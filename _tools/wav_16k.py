# -*- coding: utf-8 -*-
"""Make the shipped WAVs smaller and keep them WAV.

    python _tools/wav_16k.py [--dry]

Every clip goes from 22.05kHz to 16kHz mono 16-bit PCM - 27% fewer bytes. Measured first: the VO
carries a median 0.33% of its energy above 8kHz (the most a 16kHz file can hold), the SFX 0.006%,
so almost nothing is lost. The few clips with real sibilance up there (more than 2% above 8kHz -
vo_h1_sherni's "श" is 8.9%) are left at 22.05kHz. Length is preserved to the sample, so every
caption / highlight cue measured in ms still lands on its word, and the level is untouched.
The originals go to _backup/pre_wav16k_<date>/ (nothing is deleted).
"""
import os, shutil, subprocess, sys, time, wave
import numpy as np, imageio_ffmpeg

sys.stdout.reconfigure(encoding="utf-8")
DRY = "--dry" in sys.argv
PROJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GAME = os.path.join(PROJ, "HI02H12_L02_S01")
BK = os.path.join(PROJ, "_backup", "pre_wav16k_" + time.strftime("%Y%m%d"))
FF = imageio_ffmpeg.get_ffmpeg_exe()
KEEP_ABOVE = 0.02          # share of energy above 8kHz that keeps a clip at its own rate


def read(p):
    w = wave.open(p); sr, n = w.getframerate(), w.getnframes()
    x = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float32) / 32768; w.close()
    return sr, x


def hi_share(sr, x):
    X = np.abs(np.fft.rfft(x)) ** 2; f = np.fft.rfftfreq(len(x), 1 / sr)
    return X[f > 8000].sum() / max(X.sum(), 1e-12)


tot_a = tot_b = 0; kept = []
for sub in ("VO", "SFX"):
    d = os.path.join(GAME, "assets", sub)
    for f in sorted(os.listdir(d)):
        if not f.endswith(".wav"): continue
        p = os.path.join(d, f); sr, x = read(p); a = os.path.getsize(p); tot_a += a
        if sr <= 16000: tot_b += a; continue
        share = hi_share(sr, x)
        if share > KEEP_ABOVE: kept.append("%s (%.1f%%)" % (f, share * 100)); tot_b += a; continue
        if DRY: tot_b += int(a * 16000 / sr); continue
        tmp = p + ".16k.wav"
        subprocess.run([FF, "-v", "error", "-y", "-i", p, "-af", "aresample=16000:filter_size=64:cutoff=0.97",
                        "-ac", "1", "-c:a", "pcm_s16le", tmp], check=True)
        sr2, y = read(tmp)
        dur_a, dur_b = len(x) / sr, len(y) / sr2
        rms = lambda v: 20 * np.log10(np.sqrt((v ** 2).mean()) + 1e-12)
        assert abs(dur_a - dur_b) < 0.002, (f, dur_a, dur_b)                    # cues stay on their words
        assert abs(rms(x) - rms(y)) < 0.5, (f, rms(x), rms(y))                   # same loudness
        b = os.path.getsize(tmp); assert b < a, f                               # never ship a bigger file
        os.makedirs(os.path.join(BK, "assets", sub), exist_ok=True)
        shutil.move(p, os.path.join(BK, "assets", sub, f)); shutil.move(tmp, p); tot_b += b
print("kept at 22.05kHz:", ", ".join(kept) or "none")
print("WAV total %.2f MB -> %.2f MB%s" % (tot_a / 1e6, tot_b / 1e6, " (dry run)" if DRY else "  originals in " + BK))
