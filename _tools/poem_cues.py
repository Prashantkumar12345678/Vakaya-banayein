# -*- coding: utf-8 -*-
"""Word onset times for the poem clips, measured off the audio itself.

WHY NOT AN EVEN SPLIT: [H11-60] already learned this on the sentence re-read - words are not
evenly spaced in speech and a flat cadence drifts off the voice within two words. A poem is
worse: it is read in phrases with a real breath between the lines.

WHY NOT PURE SILENCE DETECTION EITHER: in a sung-ish reading "shern aayi" has no gap in it at
all, so silences find PHRASES, not words. So: silence gives us the phrase boundaries, which are
the honest part of the measurement, and inside a phrase the words are laid out by WEIGHT - the
count of aksharas, which is what actually takes time to say in Devanagari.
"""
import subprocess, sys, json, re, io, os
import numpy as np
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 16000

def pcm(path):
    raw = subprocess.run([FF,"-v","quiet","-i",path,"-f","s16le","-ac","1","-ar",str(SR),"-"],
                         stdout=subprocess.PIPE).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float32)/32768.0

def phrases(x, hop=0.010, win=0.025, gap=0.16, floor_db=-42.0):
    """speech runs, as (start_s, end_s), split on gaps of >= `gap` seconds of near-silence"""
    h, w = int(SR*hop), int(SR*win)
    n = max(1,(len(x)-w)//h)
    e = np.array([np.sqrt(np.mean(x[i*h:i*h+w]**2)+1e-12) for i in range(n)])
    db = 20*np.log10(e+1e-12)
    thr = max(floor_db, db.max()-28.0)          # relative to THIS clip's own peak
    voiced = db > thr
    out, i = [], 0
    while i < n:
        if voiced[i]:
            j = i
            while j < n and voiced[j]: j += 1
            out.append([i*hop, j*hop]); i = j
        else: i += 1
    merged = []
    for s,e2 in out:
        if merged and s - merged[-1][1] < gap: merged[-1][1] = e2
        else: merged.append([s,e2])
    return [(s,e2) for s,e2 in merged if e2-s > 0.08]

# an akshara is a consonant (optionally with its matra/halant tail) or a standalone vowel; that
# is the unit a Hindi speaker spends time on, so it is what the word's share of a phrase is
# bought with.
_AK = re.compile(u'[क-हक़-य़ऄ-औ]')
def weight(word):
    w = len(_AK.findall(word))
    return max(1, w)

def cues_for(words_by_line, path, lead=0.0, skip=0):
    """-> flat list of ms offsets, one per word, in reading order.
    `skip` drops that many leading phrases first - speech in the clip that is NOT the verse on
    screen, e.g. T1's spoken intro "पहले हम एक कविता पढ़ेंगे - जंगल का मेला।" (2 phrases)."""
    x = pcm(path)
    ph = phrases(x)[skip:]
    lines = [l for l in words_by_line if l]
    # a clip that did not split into as many phrases as the verse has lines is not a failure:
    # fold the extra phrases together, or split the single long one by weight across the lines.
    if len(ph) > len(lines):
        while len(ph) > len(lines):
            gaps = [ph[i+1][0]-ph[i][1] for i in range(len(ph)-1)]
            k = int(np.argmin(gaps)); ph[k] = (ph[k][0], ph[k+1][1]); ph.pop(k+1)
    elif len(ph) < len(lines):
        big = ph[0] if ph else (0.0, len(x)/SR)
        tot = sum(sum(weight(w) for w in l) for l in lines)
        t, ph = big[0], []
        for l in lines:
            share = (big[1]-big[0]) * sum(weight(w) for w in l)/tot
            ph.append((t, t+share)); t += share
    cues = []
    for words, (s,e) in zip(lines, ph):
        tot = sum(weight(w) for w in words); t = s
        for w in words:
            cues.append(int(round(max(0.0, t-lead)*1000)))
            t += (e-s)*weight(w)/tot
    return cues, ph, len(x)/SR

def envelope(x, hop=0.005, win=0.025):
    h, w = int(SR*hop), int(SR*win)
    n = max(1,(len(x)-w)//h)
    e = np.array([np.sqrt(np.mean(x[i*h:i*h+w]**2)+1e-12) for i in range(n)])
    return 20*np.log10(e+1e-12), hop

def snap(cues, x, span=0.10, need_db=3.0):
    """pull each onset to a nearby dip in the envelope.

    Weight-sharing gives the RIGHT ORDER but a smooth cadence; real speech has a small dip at most
    word boundaries even when there is no true silence. So each predicted onset looks +-100ms for
    the quietest frame, and moves only if that frame is at least 3 dB below the local average -
    otherwise the word runs into its neighbour and the prediction is as good as it gets."""
    db, hop = envelope(x)
    out, moved = [], []
    for t in cues:
        i = int(round((t/1000.0)/hop)); r = int(span/hop)
        a, b = max(0,i-r), min(len(db),i+r+1)
        if b-a < 3: out.append(t); moved.append(0); continue
        seg = db[a:b]; k = a+int(np.argmin(seg))
        if seg.mean()-db[k] >= need_db:
            out.append(int(round(k*hop*1000))); moved.append(out[-1]-t)
        else:
            out.append(t); moved.append(0)
    return out, moved


# --------------------------------------------------------------------------------------------
# RUN ME after any poem clip is re-recorded:  python _tools/poem_cues.py --write
# Without --write it only prints, so the cues can be read before they are trusted.
# A clip that has been re-cut moves every word after the edit; the card then points the verse at
# the wrong syllables and nobody notices until a child watches it. One command, both copies.
GAME = "HI02H12_L02_S01"
_TAG = re.compile(r'<[^>]+>')
_GW  = re.compile(r'<span class="gw">[^<]*</span>')
MIN_GAP = 130          # two cues closer than this read as one flash, not two words

def measure(slide):
    cap = slide["data"]["caption_hi"]
    # THE DOM MUST SPLIT INTO THE SAME UNITS THIS COUNTS. A .gw span touching punctuation would be
    # one token here and two nodes in the browser, and every cue after it would land on the wrong
    # word. Checked, not assumed.
    for m in _GW.finditer(cap):
        before = cap[m.start()-1] if m.start() else " "
        after  = cap[m.end()] if m.end() < len(cap) else " "
        assert before.isspace() and after.isspace(), (slide["id"], repr(cap[m.start()-2:m.end()+2]))
    lines = [[w for w in _TAG.sub("", l).split() if w] for l in cap.split("\n")]
    nar = slide["audio"]["narration"]
    assert isinstance(nar, str), (slide["id"], "a LIST narration would need cues per clip")
    path = os.path.join(GAME, "assets", "VO", nar + ".wav")   # [H11-156] the game ships WAV
    # [H11-139] a clip may open with speech that is not the caption (T1's intro). The card says
    # how many leading phrases to leave out, so the verse is measured from where it is SAID.
    pred, ph, dur = cues_for(lines, path, skip=int(slide["data"].get("caption_skip_phrases", 0)))
    x = pcm(path)
    c, _ = snap(pred, x)
    k = 0
    for L, (ps, pe) in zip(lines, ph):
        c[k] = int(round(ps*1000)); k += len(L)      # a phrase start is measured, not guessed
    for i in range(1, len(c)):
        if c[i]-c[i-1] < MIN_GAP: c[i] = pred[i]     # a snap that crowds its neighbour is worse
        if c[i]-c[i-1] < MIN_GAP: c[i] = c[i-1]+MIN_GAP
    assert all(c[i] > c[i-1] for i in range(1, len(c))) and c[-1] < dur*1000, slide["id"]
    return c, [w for L in lines for w in L]

def _put(txt, sid, arr):
    m = re.search(r'(?s)"id":\s*"%s".*?"data":\s*\{' % sid, txt)
    assert m, sid
    body = txt[m.end():]
    old = re.match(r'\s*"caption_cues_ms":\s*\[[^\]]*\],', body)
    keep = body[old.end():] if old else body
    nl = "\n" in (old.group(0) if old else body[:3])
    ind = re.match(r'\s*', body).group(0)
    ins = (ind if nl else " ") + '"caption_cues_ms": ' + json.dumps(arr) + ","
    return txt[:m.end()] + ins + keep

if __name__ == "__main__":
    import os
    write = "--write" in sys.argv
    card = json.load(io.open(os.path.join(GAME, "card.json"), encoding="utf-8"))
    got = {}
    for s in card["slides"]:
        if s.get("type") != "STORY_SCENE" or not s.get("data", {}).get("caption_hi"): continue
        c, words = measure(s)
        got[s["id"]] = c
        print(s["id"], " ".join("%s@%.2f" % (w, c[i]/1000.0) for i, w in enumerate(words)))
    if not write:
        print("\n(print only - pass --write to put these in the card)"); sys.exit(0)

    # both copies, byte-for-byte consistent: the ENGINE reads the embedded one, card.json is
    # what everyone else reads, and a drift between them is invisible until it is expensive.
    idx = os.path.join(GAME, "index.html")
    d = open(idx, "rb").read(); lf = d.count(b"\n") - d.count(b"\r\n")
    head, mid, tail = re.split(r'(?s)(<script type="application/json" id="cardData">.*?</script>)',
                               d.decode("utf-8"), maxsplit=1)
    for sid, arr in got.items(): mid = _put(mid, sid, arr)
    d = (head + mid + tail).encode("utf-8")
    assert d.count(b"\n") - d.count(b"\r\n") == lf, "line endings moved"
    open(idx, "wb").write(d)

    p = os.path.join(GAME, "card.json")
    t = io.open(p, encoding="utf-8").read()
    for sid, arr in got.items(): t = _put(t, sid, arr)
    io.open(p, "w", encoding="utf-8", newline="").write(t)

    emb = json.loads(re.search(r'(?s)<script type="application/json" id="cardData">(.*?)</script>',
                               io.open(idx, encoding="utf-8").read()).group(1))
    assert emb == json.load(io.open(p, encoding="utf-8")), "the two card copies have drifted"
    for s in emb["slides"]:
        if s.get("type") != "STORY_SCENE": continue
        assert len(_TAG.sub("", s["data"]["caption_hi"]).split()) == len(s["data"]["caption_cues_ms"])
    print("\n%d slides written to both copies. Now run _tools/restamp.py." % len(got))
