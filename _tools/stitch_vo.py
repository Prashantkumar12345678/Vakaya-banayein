# -*- coding: utf-8 -*-
"""Build the four P3/P4 clips that were never recorded, out of recorded human speech.

    python _tools/stitch_vo.py

P3 (शेरनी मेले में……) and P4 (बंदर पेड़ पर……) ask a question and praise a right answer, but those
four lines were not in Review 2, so no batch ever carried them and both slides were silent at
exactly those two moments. The game never falls back to TTS (ruled out, see [30o]), so until they
are recorded they are CUT FROM CLIPS WE HAVE - the same voice saying the same words:

  vo_q_sentence_sherni / _bandar   "सही शब्द चुनकर वाक्य पूरा कीजिए।"   vo_q_sentence 0.46-2.84s
  vo_c_sentence_sherni             "शाबाश! सही वाक्य है—"              vo_c_sentence 0.32-2.47s
                                 + "शेरनी मेले में जाती है।"           vo_h2_sentence_sherni 2.26-4.42s
  vo_c_sentence_bandar             "शाबाश! सही वाक्य है—"              vo_c_sentence 0.32-2.47s
                                 + "बंदर पेड़ पर चढ़ता है।"            vo_h2_sentence_bandar 2.00-3.85s

The cut points are the silences _tools/poem_cues.phrases() finds in each source clip. PLACEHOLDERS:
when the real lines are recorded, import_vo_batch.py replaces these like any other clip.
"""
import os, subprocess, sys
import numpy as np
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000
VO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "HI02H12_L02_S01", "assets", "VO")
PAD, FADE, GAP, LEAD, TAIL = 0.06, 0.02, 0.22, 0.25, 0.30
TARGET_RMS, PEAK_CAP = -14.5, -1.5

RECIPES = {
    "vo_q_sentence_sherni": [("vo_q_sentence", 0.46, 2.84)],
    "vo_q_sentence_bandar": [("vo_q_sentence", 0.46, 2.84)],
    "vo_c_sentence_sherni": [("vo_c_sentence", 0.32, 2.47), ("vo_h2_sentence_sherni", 2.26, 4.42)],
    "vo_c_sentence_bandar": [("vo_c_sentence", 0.32, 2.47), ("vo_h2_sentence_bandar", 2.00, 3.85)],
    # the झूला's praise when a rider sits: just the word, so the wheel can move on straight after
    "vo_wheel_shabash":     [("vo_correct_pair", 0.24, 1.19)],   # vo_shabash is the end-screen line now
}


def pcm(path):
    raw = subprocess.run([FF, "-v", "quiet", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         stdout=subprocess.PIPE).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0


def piece(src, a, b):
    x = pcm(os.path.join(VO, src + ".wav"))
    y = x[max(0, int((a - PAD) * SR)):int((b + PAD) * SR)].copy()
    n = int(FADE * SR); r = np.linspace(0, 1, n)
    y[:n] *= r; y[-n:] *= r[::-1]
    return y


def level(y):
    f = y[:len(y) // 1200 * 1200].reshape(-1, 1200); e = np.sqrt((f ** 2).mean(1) + 1e-12)
    v = e[20 * np.log10(e) > -45]; rms = 20 * np.log10(np.sqrt((v ** 2).mean()))
    peak = 20 * np.log10(np.abs(y).max() + 1e-9)
    return y * 10 ** (min(TARGET_RMS - rms, PEAK_CAP - peak) / 20)


for out, parts in RECIPES.items():
    segs = [np.zeros(int(LEAD * SR), np.float32)]
    for i, (src, a, b) in enumerate(parts):
        if i: segs.append(np.zeros(int(GAP * SR), np.float32))
        segs.append(level(piece(src, a, b)))
    segs.append(np.zeros(int(TAIL * SR), np.float32))
    y = np.concatenate(segs)
    pcm16 = (np.clip(y, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run([FF, "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-ar", "22050", "-c:a", "pcm_s16le", os.path.join(VO, out + ".wav")]   # [H11-156] WAV, input=pcm16, check=True)
    print("%-22s %.2fs  <- %s" % (out, len(y) / SR, " + ".join("%s[%.2f-%.2f]" % p for p in parts)))
