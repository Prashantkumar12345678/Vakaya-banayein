# -*- coding: utf-8 -*-
"""Synthesise the background music and the extra sound effects.

    python _tools/make_audio.py

EVERYTHING HERE IS GENERATED, NOT DOWNLOADED, so there is no licence to track and nothing to
attribute. The brief was "kids friendly and relatable": the lesson is a जंगल का मेला, so the music
is a small fair-ground tune - marimba over a soft bass and a shaker, major pentatonic (no note can
sound wrong or sad), 104 BPM (walking pace, not hurried). The effects are wooden and round -
no harsh buzzers, nothing sudden or loud.

  assets/SFX/bgm_mela.ogg     ~18.5s, loops seamlessly (the last bar resolves into the first)
  assets/SFX/sfx_tap.ogg      option tap        - a soft wooden "tok"
  assets/SFX/sfx_whoosh.ogg   transition opens  - a gentle swish
  assets/SFX/sfx_seat.ogg     rider sits down   - a springy "boing"
  assets/SFX/sfx_wheel.ogg    (retired from the wheel - kept for reference)
  assets/SFX/sfx_spin.ogg       wheel turns ONE notch in 1.15s  (between questions)
  assets/SFX/sfx_spin_slow.ogg  wheel turns ONE notch in 1.5s   (the opening)
  assets/SFX/sfx_spin_lap.ogg   wheel turns SIX notches in 2.6s (the final lap)

THE SPIN FOLLOWS THE WHEEL. ride() eases in and out (easeInOutQuad), so the ratchet ticks are
placed where the wheel actually is: slow clicks as it starts, fast in the middle, slow again as it
stops - five ticks per notch - over a low wooden rumble whose loudness follows the speed, then a
small bell as it settles. A fixed tick rate over an easing wheel sounds like a recording laid on
top; this sounds like the wheel.
"""
import os
import numpy as np
import subprocess, tempfile
import soundfile as sf
import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SR = 44100
OUT = os.path.join("HI02H12_L02_S01", "assets", "SFX")
rng = np.random.default_rng(7)


def t_(dur): return np.arange(int(dur * SR)) / SR


def env(n, a=0.005, d=0.3):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * np.exp(-t / d)
    return e


def marimba(f, dur=0.5, amp=0.5):
    t = t_(dur)
    s = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t / 0.04)
         + 0.12 * np.sin(2 * np.pi * f * 10 * t) * np.exp(-t / 0.01))
    return amp * s * env(len(t), 0.002, 0.18)


def bass(f, dur=0.5, amp=0.35):
    t = t_(dur)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    return amp * s * env(len(t), 0.01, 0.35)


def shaker(dur=0.08, amp=0.08):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    x = np.diff(x, prepend=0)                          # brighten
    return amp * x * env(n, 0.003, 0.025)


def note(name):
    names = {"C": 0, "D": 2, "E": 4, "G": 7, "A": 9}
    return 440.0 * 2 ** ((names[name[0]] + 12 * (int(name[1]) - 4) - 9) / 12)


def mix_into(buf, sig, at):
    i = int(at * SR)
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i]


def norm(x, peak):
    return x / (np.abs(x).max() + 1e-9) * peak


def fade(x, a=0.004, b=0.02):
    n = len(x); x = x.copy()
    ia, ib = int(a * SR), int(b * SR)
    x[:ia] *= np.linspace(0, 1, ia); x[n - ib:] *= np.linspace(1, 0, ib)
    return x


def save(name, x):
    # libsndfile's own Vorbis writer dies without a word on anything longer than a couple of
    # seconds (the BGM came out as a 0-second file), so WAV goes through ffmpeg instead.
    wav = os.path.join(tempfile.gettempdir(), name + ".wav")
    sf.write(wav, x.astype(np.float32), SR, subtype="PCM_16")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le",   # [H11-156] WAV
                    os.path.join(OUT, name)], check=True)
    os.remove(wav)
    print("%-16s %.2fs" % (name, len(x) / SR))


# ---- BGM: 8 bars of 4/4, 104 BPM, eighth-note grid -------------------------------------------
BPM = 104; E8 = 60 / BPM / 2; BAR = E8 * 8
MEL = [  # (eighth index within 8 bars, note, length in eighths); '.' = rest
    "E5 . G5 . A5 G5 E5 .", "D5 . E5 . G5 . . .",
    "C5 . D5 . E5 G5 E5 .", "D5 . C5 . D5 . . .",
    "E5 . G5 . A5 . C6 .", "A5 G5 E5 . G5 . . .",
    "C5 D5 E5 . G5 . E5 .", "D5 . E5 . C5 . . .",
]
CHORD_ROOTS = ["C3", "G2", "A2", "G2", "C3", "A2", "D3", "G2"]   # I V vi V I vi ii V -> loops to I
total = BAR * 8
buf = np.zeros(int(total * SR) + SR)                              # tail room, folded back below
for b, line in enumerate(MEL):
    for k, tok in enumerate(line.split()):
        if tok != ".":
            mix_into(buf, marimba(note(tok), 0.6, 0.42), b * BAR + k * E8)
for b, r in enumerate(CHORD_ROOTS):
    f = note(r)
    mix_into(buf, bass(f, BAR / 2, 0.30), b * BAR)
    mix_into(buf, bass(f * 1.5, BAR / 2, 0.22), b * BAR + BAR / 2)   # root - fifth bounce
    for k in range(8):                                               # soft offbeat chord "plink"
        if k % 2 == 1:
            for m in (2, 2.52, 3):                                   # root, third-ish, fifth an octave up
                mix_into(buf, marimba(f * m * 2, 0.25, 0.05), b * BAR + k * E8)
for k in range(64):                                                  # shaker on every eighth
    mix_into(buf, shaker(0.08, 0.05 if k % 2 == 0 else 0.03), k * E8)
n = int(total * SR)
loop = buf[:n].copy(); loop[:len(buf) - n] += buf[n:]                # fold the tail onto the start
loop = norm(loop, 0.6)
save("bgm_mela.wav", loop)

# ---- tap: a hollow wooden tok ---------------------------------------------------------------
t = t_(0.12)
tap = np.sin(2 * np.pi * (900 * np.exp(-t / 0.03) + 500) * t) * env(len(t), 0.001, 0.03)
save("sfx_tap.wav", fade(norm(tap, 0.5)))

# ---- whoosh: band-passed noise sweeping up then down ------------------------------------------
n = int(0.7 * SR); x = rng.standard_normal(n)
spec = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
spec *= np.exp(-((fr - 1200) / 900) ** 2)
x = np.fft.irfft(spec, n)
shape = np.sin(np.linspace(0, np.pi, n)) ** 2
save("sfx_whoosh.wav", fade(norm(x * shape, 0.35)))

# ---- seat: a springy boing (pitch wobble falling into place) -----------------------------------
t = t_(0.45)
f = 330 + 160 * np.exp(-t / 0.08) * np.cos(2 * np.pi * 14 * t)
ph = 2 * np.pi * np.cumsum(f) / SR
boing = (np.sin(ph) + 0.3 * np.sin(2 * ph)) * env(len(t), 0.004, 0.16)
save("sfx_seat.wav", fade(norm(boing, 0.5)))

# ---- wheel: six soft ratchet ticks then a small bell --------------------------------------------
w = np.zeros(int(1.3 * SR))
for k in range(6):
    tk = t_(0.03)
    mix_into(w, np.sin(2 * np.pi * 2200 * tk) * env(len(tk), 0.0005, 0.006) * 0.4, k * 0.13)
tb = t_(0.8)
bell = sum(a * np.sin(2 * np.pi * 1318.5 * m * tb) for a, m in ((1, 1), (.4, 2.76), (.2, 5.4)))
mix_into(w, bell * env(len(tb), 0.002, 0.3) * 0.5, 0.8)
save("sfx_wheel.wav", fade(norm(w, 0.45)))


# ---- spin: ticks + rumble that follow ride()'s easing -------------------------------------------
def spin(ms, notches, name, bell=True):
    T = ms / 1000.0
    tail = 0.9 if bell else 0.2
    out = np.zeros(int((T + tail) * SR))
    ease = lambda r: 2 * r * r if r < .5 else 1 - (-2 * r + 2) ** 2 / 2
    # tick times: invert the easing numerically
    rs = np.linspace(0, 1, 4000); pos = np.array([ease(r) for r in rs]) * notches * 5
    for k in range(1, int(notches * 5) + 1):
        tk_t = rs[np.searchsorted(pos, k)] * T if k < pos[-1] else T
        n = int(0.025 * SR); tt = np.arange(n) / SR
        click = (np.sin(2 * np.pi * 1700 * tt) * 0.6 + rng.standard_normal(n) * 0.4) * np.exp(-tt / 0.004)
        mix_into(out, click * 0.30, tk_t)
    # rumble: low-passed noise, loudness = angular speed
    n = int(T * SR); x = rng.standard_normal(n)
    sp = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR); sp *= 1 / (1 + (fr / 220) ** 4); x = np.fft.irfft(sp, n)
    tt = np.arange(n) / n
    speed = np.where(tt < .5, 4 * tt, 4 * (1 - tt))          # derivative of easeInOutQuad, peak 2 -> scaled
    x = x / (np.abs(x).max() + 1e-9) * speed * 0.35
    mix_into(out, x, 0)
    if bell:
        tb = t_(0.8)
        b = sum(a * np.sin(2 * np.pi * 1568 * m * tb) for a, m in ((1, 1), (.35, 2.76), (.15, 5.4)))
        mix_into(out, b * env(len(tb), 0.002, 0.28) * 0.28, T - 0.02)
    save(name, fade(norm(out, 0.5), 0.004, 0.08))

spin(1150, 1, "sfx_spin.wav")
spin(1500, 1, "sfx_spin_slow.wav")
spin(2600, 6, "sfx_spin_lap.wav")
