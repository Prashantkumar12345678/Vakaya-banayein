# -*- coding: utf-8 -*-
"""Build the action and picture SFX (SME review 2026-11-18: "the SFX should match the action").

    python3 _tools/make_action_sfx.py

Sources are Mixkit free-licence previews kept in _masters/sfx/mixkit/src/<id>.mp3 (downloaded from
https://assets.mixkit.co/active_storage/sfx/<id>/<id>-preview.mp3). Each output is cut, faded and
levelled to sit with the existing effects, then written as 16-bit mono 22.05 kHz WAV to assets/SFX.

  footsteps   one step cut from a real recording, laid every 0.45s for 10 steps (the pace of the
              current grass loop) - wood for Game 1's bridge, stone in the cave, gravel at the railway
  actions     hammer on the plank, key into the lock + lock turning, gears turning, the barrier
              lifting, the big wooden gate of the last level
  pictures    sfx_pic_<slide>: what the picture shows, played once its sentence is complete
"""
import os, subprocess, wave
import numpy as np, imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe(); SR = 22050
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "_masters", "sfx", "mixkit", "src")
OUT = os.path.join(HERE, "..", "HI02H12_L02_S01", "assets", "SFX")


def load(i):
    p = os.path.join(SRC, "%s.mp3" % i)
    raw = subprocess.run([FF, "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def cut(x, a, b, fi=0.01, fo=0.25):
    y = x[int(a * SR):int(b * SR)].copy(); n = len(y)
    i, o = min(int(fi * SR), n // 2), min(int(fo * SR), n // 2)
    if i: y[:i] *= np.linspace(0, 1, i)
    if o: y[-o:] *= np.linspace(1, 0, o)
    return y


def speed(x, r):            # r < 1: slower and deeper (a bigger object)
    idx = np.arange(0, len(x) - 1, r); return np.interp(idx, np.arange(len(x)), x).astype(np.float32)


def lowpass(x, hz):
    a = np.exp(-2 * np.pi * hz / SR); y = np.empty_like(x); s = 0.0
    for k, v in enumerate(x): s = (1 - a) * v + a * s; y[k] = s
    return y


def level(x, rms):          # active RMS (the louder 50ms frames) to the target; peak kept under 0.95
    n = int(SR * 0.05); m = len(x) // n
    e = np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)); act = e[e > e.max() * 0.1]
    y = x * (rms / max(np.sqrt((act ** 2).mean()), 1e-6))
    pk = np.abs(y).max(); return y * (0.95 / pk) if pk > 0.95 else y


def mix(*parts):            # (signal, start_seconds, gain)
    n = max(int(t * SR) + len(s) for s, t, g in parts); y = np.zeros(n, np.float32)
    for s, t, g in parts: k = int(t * SR); y[k:k + len(s)] += s * g
    return y


def save(name, x):
    d = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d.tobytes())
    print("%-22s %.2fs" % (name, len(x) / SR))


def steps(step_list, n=10, gap=0.45, rms=0.035):
    parts = [(step_list[k % len(step_list)], k * gap, 0.88 if k % 2 else 1.0) for k in range(n)]
    y = mix(*parts)[:int(n * gap * SR)]; y = np.pad(y, (0, int(n * gap * SR) - len(y)))   # loops on the beat
    return level(y, rms)


# ---- footsteps -------------------------------------------------------------------------------------
knock = load(2182)                                     # "Wood hard hit"
w1 = lowpass(cut(knock, 0.03, 0.30, 0.003, 0.12), 1800)          # a dull, hollow plank thud
w2 = lowpass(speed(w1, 0.92), 1600)
creak = cut(load(176), 0.10, 0.70, 0.05, 0.25)          # "Short creaking floorboard"
wood = steps([w1, w2])
cr = mix((creak, 1.40, 0.18), (creak, 3.20, 0.14)); wood[:len(cr)] += cr[:len(wood)]
save("sfx_steps_wood", level(wood, 0.035))

tunnel = load(543)                                     # "Footsteps in a tunnel loop" - a step with its echo
save("sfx_steps_stone", steps([cut(tunnel, t - 0.03, t + 0.40, 0.005, 0.15) for t in (1.49, 3.41, 4.36)]))
stones = load(1269)                                    # "Walking on stones loop"
save("sfx_steps_gravel", steps([cut(stones, t - 0.03, t + 0.36, 0.005, 0.12) for t in (1.89, 3.74, 5.16)]))

# ---- actions -----------------------------------------------------------------------------------------
ham = cut(load(830), 0.08, 0.40, 0.002, 0.12)          # "Hammer hit on wood": tok - tok - TOK
save("sfx_plank_hammer", level(mix((ham, 0, 0.75), (ham, 0.22, 0.85), (ham, 0.44, 1.0)), 0.30))
save("sfx_key_insert", level(cut(load(2842), 0.0, 1.05, 0.01, 0.2), 0.16))    # "Door key in door lock"
save("sfx_lock_open", level(cut(load(187), 0.05, 1.90, 0.01, 0.35), 0.18))    # "Old medieval door lock"
save("sfx_gears_turn", level(mix((cut(load(2856), 0, 0.62, 0.005, 0.1), 0, 1), (cut(load(2858), 0, 0.32, 0.005, 0.1), 0.55, 0.9),
                                 (cut(load(2856), 0, 0.62, 0.005, 0.1), 0.80, 0.8)), 0.15))     # gear ratchet + lock clunk
save("sfx_barrier_lift", level(cut(load(3117), 0.0, 1.40, 0.01, 0.35), 0.16))  # "Mechanical technology movements"
save("sfx_gate_open", level(speed(cut(load(193), 0.10, 3.20, 0.02, 0.6), 0.85), 0.12))   # "Old church door open", deeper = bigger

# ---- pictures: what the picture shows, once the sentence is done -------------------------------------
def clear(i, start=None, length=2.6):     # the clear part of a clip: from where it first gets loud, at most `length`s
    x = load(i)
    if start is None:
        n = int(SR * 0.02); e = np.sqrt((x[:len(x) // n * n].reshape(-1, n) ** 2).mean(1))
        start = max(0, np.argmax(e > e.max() * 0.08) * 0.02 - 0.03)
    return cut(x, start, min(start + length, len(x) / SR), 0.01, 0.35)


def soft(x):                              # rounder: the high hiss taken off
    return lowpass(x, 5000)


# SME picks 2026-11-18 from _previews/picture_sfx (T1 A, T3 C, G1 B, G2 C; P4 kept as it was; round 2: G3, G4, P2).
# The rows marked "not liked" are placeholders until the next round of choices is picked.
P = {
 "T1": (soft(mix((clear(2694, length=1.6), 0, 1), (clear(21, length=1.0), 0.6, .7))), 0.08),   # soft small flutter + double chirp
 "T2": (mix((clear(2099, length=.6), 0, 1), (cut(load(2261), 0.30, 2.6), .25, 1)), 0.14),   # a football kick, then the kids playing and laughing (SME: the old sound + a kick)
 "T3": (clear(1099), 0.14),                                                          # leafing through the book's pages
 "G1": (clear(2472), 0.14),                                                          # morning birds in the garden
 "G2": (mix((clear(2089, 0, 1.35), 0, .8), (clear(741, 2.75, .9), .55, 1)), 0.14),   # ball bounces, puppy barks
 "G3": (mix((clear(2430, length=1.2), 0, .8), *[(clear(2925, length=.4), 1.0 + .3 * k, .75 + .08 * k) for k in range(4)]), 0.10),   # leaves rustle + 4 soft pops (the apples)
 "G4": (mix((clear(2241, length=1.3), 0, 1), (soft(clear(1748, length=1.8)), 1.3, .6)), 0.14),   # munching grass + one soft moo
 "P1": (mix(*[(speed(clear(1879, length=.5), 1.35), t, .8 + .1 * k) for k, t in enumerate((0, .3, .6, .9))], (clear(871, length=1.0), 1.25, .5)), 0.10),   # water plinks + a happy sparkle (round 3 pick A)
 "P2": (mix((soft(clear(3091, length=2.4)), 0, .7), (soft(clear(700, length=2.4)), .2, .5)), 0.08),   # sleepy lullaby + a soft purr
 "P3": (mix((cut(load(2826), 0.55, 2.6, 0.02, 0.3), 0, 1), (cut(load(1307), 0.10, 0.80, 0.01, 0.1), 2.15, 1)), 0.14),   # not liked
 "P4": (mix((cut(load(1783), 1.0, 3.2, 0.3, 0.6), 0, 0.8), (cut(load(3062), 0.0, 0.9), 0.3, 0.6)), 0.14),   # night crickets + a twinkle (liked)
 "P5": (cut(load(700), 0.0, 2.6, 0.01, 0.5), 0.14),                                  # a little tune
 "P6": (mix((cut(load(2241), 0.10, 1.40, 0.01, 0.15), 0, 1), (cut(load(1760), 0.10, 0.95, 0.01, 0.15), 1.45, 0.55)), 0.14),   # goat munching, then a baa
}
if __name__ == "__main__":
    for sid, (sig, rms) in P.items():
        save("sfx_pic_" + sid.lower(), level(sig, rms))
