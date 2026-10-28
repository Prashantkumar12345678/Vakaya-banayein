# -*- coding: utf-8 -*-
"""Build the game's card from the SME script, with placeholder VO.

    python _tools/build_card.py            (card + any missing VO clips)
    python _tools/build_card.py --tts-all  (re-synthesise every placeholder clip)

THE SCRIPT LIVES HERE, ONCE. Every screen of the SME review (HI02H12_L02_S01_SME_review, right-hand
"Recommendations" column only - the screenshots are the old WIP build and are NOT the spec) is one
entry in SLIDES below. From it this writes:
  HI02H12_L02_S01/card.json               the card
  HI02H12_L02_S01/index.html  #cardData   the same card, inlined (the page reads only this copy)
  HI02H12_L02_S01/assets/VO/<id>.wav      placeholder VO, macOS `say -v Lekha` (hi_IN)

PLACEHOLDER VO. Lekha is a stand-in so the build can be reviewed with sound. When the recorded batch
arrives, _tools/import_vo_batch.py replaces the clips by id and the *_cues_ms below must be re-measured
off the real recordings (they are estimated here from each clip's speech span, shared out by word
length). A clip that already exists is NOT re-synthesised, so recorded VO is never overwritten -
--tts-all is the only way to regenerate, and it skips nothing.

COMPOSED CLIPS. "शाबाश! सही वाक्य है— <वाक्य>" and the cloze stems ("मीरा पौधों को … दे रही है")
are built by joining clips with a measured silence, so the onset of every word is known from the
join points instead of guessed across the whole line.
"""
import array, json, os, re, subprocess, sys, wave

sys.stdout.reconfigure(encoding="utf-8")
PROJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GAME = os.path.join(PROJ, "HI02H12_L02_S01")
VO = os.path.join(GAME, "assets", "VO")
TMP = os.path.join(PROJ, "_backup", "_tts_parts")
TTS_ALL = "--tts-all" in sys.argv
RATE, VOICE, SR = 140, "Lekha", 22050

# ---------------------------------------------------------------- word clips (tap-speak + hint walk)
ROMAN = {
    "चिड़िया": "chidiya", "गाड़ी": "gaadi", "मछली": "machhli",
    "सुंदर": "sundar", "ठंडा": "thanda", "गंदा": "ganda",
    "पानी": "paani", "मिट्टी": "mitti", "फल": "phal",
    "दौड़ रही": "daud_rahi", "खा रही": "kha_rahi", "सो रही": "so_rahi",
    "पेंसिल": "pencil", "रोटी": "roti",
    "फूल": "phool", "पत्ते": "patte", "तारे": "taare",
    "बच्चे": "bachche", "मैदान": "maidan", "में": "mein", "खेल": "khel", "रहे": "rahe", "हैं": "hain",
    "लड़की": "ladki", "किताब": "kitaab", "पढ़": "padh", "रही": "rahi", "है": "hai",
    "कुत्ता": "kutta", "गेंद": "gend", "से": "se", "रहा": "raha",
    "पेड़": "ped", "पर": "par", "सेब": "seb", "लगे": "lage",
    "गाय": "gaay", "घास": "ghaas", "खा": "kha",
    "गाना": "gaana", "गा": "ga", "बकरी": "bakri", "गिर": "gir",
}
def bare(w): return w.replace("।", "").strip()
def word_id(w): return "vo_w_" + ROMAN[bare(w)]

# ---------------------------------------------------------------- the SME script
SAHI = "सही वाक्य है—"
SHABASH_SAHI = "शाबाश! सही वाक्य है—"
DEKHO = "आइए, दिए गए चित्र के लिए वाक्य बनाते हैं। ध्यान से देखिए, चित्र में क्या हो रहा है? "

SLIDES = [
    # ---- I Do (tutorial): the engine answers, the child watches ----
    dict(id="T1", phase="tutorial", type="SENTENCE_CLOZE", prompt_hi="आइए वाक्य बनाएं।",
         image="pic_chidiya_udna", emoji="🐦", sentence="आसमान में ___ उड़ रही है।",
         options=["चिड़िया*", "गाड़ी", "मछली"], demo=True,
         say_prompt=DEKHO + "चित्र में एक चिड़िया आसमान में उड़ रही है। आइए देखते हैं, कौन-सा वाक्य चित्र के लिए सही है।"),
    dict(id="T2", phase="tutorial", type="SENTENCE_BUILD", prompt_hi="आइए वाक्य बनाएं।",
         image="pic_bachche_maidan", emoji="⚽", sentence="बच्चे मैदान में खेल रहे हैं।", demo=True,
         say_prompt=DEKHO + "चित्र में बच्चे मैदान में खेल रहे हैं। इसलिए हम वाक्य बनाएंगे—"),
    dict(id="T3", phase="tutorial", type="SENTENCE_BUILD", prompt_hi="आइए वाक्य बनाएं।",
         image="pic_ladki_kitab", emoji="📖", sentence="लड़की किताब पढ़ रही है।", demo=True,
         say_prompt=DEKHO + "चित्र में एक लड़की किताब पढ़ रही है। इसलिए हम वाक्य बनाएंगे—"),
    # ---- We Do (guided): hint 1 फिर से कोशिश, hint 2 the sentence read word by word, hint 3 glow ----
    dict(id="G1", phase="guided", type="SENTENCE_CLOZE", prompt_hi="आइए वाक्य बनाएं।",
         image="pic_sundar_bagicha", emoji="🌷", sentence="यह एक ___ बगीचा है।",
         options=["सुंदर*", "ठंडा", "गंदा"],
         say_prompt="दिए गए चित्र के लिए वाक्य बनाइए। देखिए, कौन-सा शब्द वाक्य के लिए सही है।"),
    dict(id="G2", phase="guided", type="SENTENCE_BUILD", prompt_hi="वाक्य बनाइए।",
         image="pic_kutta_gend", emoji="🐶", sentence="कुत्ता गेंद से खेल रहा है।",
         say_prompt="चित्र देखकर वाक्य बनाइए।"),
    dict(id="G3", phase="guided", type="SENTENCE_BUILD", prompt_hi="वाक्य बनाइए।",
         image="pic_ped_seb", emoji="🍎", sentence="पेड़ पर सेब लगे हैं।",
         say_prompt="चित्र देखकर वाक्य बनाइए।"),
    dict(id="G4", phase="guided", type="SENTENCE_BUILD", prompt_hi="वाक्य बनाइए।",
         image="pic_gaay_ghaas", emoji="🐄", sentence="गाय घास खा रही है।",
         say_prompt="चित्र देखकर वाक्य बनाइए।"),
    # ---- You Do (practice): hint 1 wiggle, hint 2 options read aloud, hint 3 glow ----
    dict(id="P1", phase="practice", type="SENTENCE_CLOZE", prompt_hi="आइए वाक्य बनाएं।",
         image="pic_meera_paani", emoji="🪴", sentence="मीरा पौधों को ___ दे रही है।",
         options=["पानी*", "मिट्टी", "फल"],
         say_prompt="आइए, दिए गए चित्र के लिए वाक्य बनाते हैं।"),
    dict(id="P2", phase="practice", type="SENTENCE_CLOZE", prompt_hi="आइए वाक्य बनाएं।",
         image="pic_billi_tokri", emoji="🐱", sentence="बिल्ली टोकरी में ___ है।",
         options=["दौड़ रही", "खा रही", "सो रही*"],
         say_prompt="आइए, दिए गए चित्र के लिए वाक्य बनाते हैं।"),
    dict(id="P3", phase="practice", type="SENTENCE_CLOZE", prompt_hi="आइए वाक्य बनाएं।",
         image="pic_bachcha_pyaasa", emoji="🥵", sentence="बच्चा प्यासा है, उसे ___ चाहिए।",
         options=["पेंसिल", "रोटी", "पानी*"],
         say_prompt="सही शब्द चुनकर वाक्य बनाइए।"),
    dict(id="P4", phase="practice", type="SENTENCE_CLOZE", prompt_hi="आइए वाक्य बनाएं।",
         image="pic_raat_taare", emoji="🌙", sentence="रात के समय आसमान में ___ चमकते हैं।",
         options=["फूल", "पत्ते", "तारे*"],
         say_prompt="सही शब्द चुनकर वाक्य बनाइए।"),
    dict(id="P5", phase="practice", type="SENTENCE_BUILD", prompt_hi="आइए वाक्य बनाएं।",
         image="pic_ladki_gaana", emoji="🎤", sentence="लड़की गाना गा रही है।",
         distractors=["खेल", "किताब", "रहा"],
         say_prompt="चित्र देखकर वाक्य बनाइए।"),
    dict(id="P6", phase="practice", type="SENTENCE_BUILD", prompt_hi="आइए वाक्य बनाएं।",
         image="pic_bakri_patte", emoji="🐐", sentence="बकरी पत्ते खा रही है।",
         distractors=["पेड़", "गिर", "रहे"],
         say_prompt="चित्र देखकर वाक्य बनाइए।"),
]

COMMON_TEXT = {
    "vo_landing": "नमस्ते दोस्त, मैं हूँ स्विफ्टी। आज हम शब्दों से वाक्य बनाना सीखेंगे।",
    "vo_pt_tutorial": "चलिए, शुरू करें!",
    "vo_pt_guided": "चलिए, साथ में करें।",
    "vo_pt_practice": "वाह! अब आपकी बारी।",
    "vo_try_again": "फिर से कोशिश कीजिए।",
    "vo_reveal": "सही शब्द चमक रहा है, उस पर टैप कीजिए।",
    "vo_celebrate": "बहुत बढ़िया, दोस्त! तुमने कमाल कर दिया!",
    "vo_sahi": SAHI,
    "vo_shabash_sahi": SHABASH_SAHI,
}

# ---------------------------------------------------------------- audio helpers
def tts(clip_id, text, force=False):
    out = os.path.join(VO, clip_id + ".wav")
    if os.path.exists(out) and not (force or TTS_ALL): return out
    subprocess.run(["say", "-v", VOICE, "-r", str(RATE), "--file-format=WAVE",
                    "--data-format=LEI16@%d" % SR, "-o", out, text], check=True)
    return out

def read(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1 and w.getsampwidth() == 2, path
        a = array.array("h"); a.frombytes(w.readframes(w.getnframes()))
    return a

def speech_span(a, thr=600):
    """(first, last) sample above the threshold - the clip's speech, without say's padding."""
    i = next((k for k, v in enumerate(a) if abs(v) > thr), 0)
    j = next((k for k in range(len(a) - 1, -1, -1) if abs(a[k]) > thr), len(a) - 1)
    return i, j

def est_cues(words, a, offset_ms=0):
    """Onset of each word, shared out over the speech span by word length (+2 for the gap)."""
    i, j = speech_span(a)
    wts = [len(bare(w)) + 2 for w in words]
    tot, acc, out = float(sum(wts)), 0, []
    for wt in wts:
        out.append(int(offset_ms + (i + (j - i) * acc / tot) * 1000 / SR))
        acc += wt
    return out

def silence(ms): return array.array("h", [0] * int(SR * ms / 1000))

def compose(clip_id, parts):
    """parts: list of (array | ms-of-silence). Writes the joined clip, returns each part's start ms."""
    out, starts = array.array("h"), []
    for p in parts:
        starts.append(int(len(out) * 1000 / SR))
        out.extend(silence(p) if isinstance(p, int) else p)
    with wave.open(os.path.join(VO, clip_id + ".wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
    return starts

def part(name, text):
    os.makedirs(TMP, exist_ok=True)
    p = os.path.join(TMP, name + ".wav")
    if not os.path.exists(p) or TTS_ALL:
        subprocess.run(["say", "-v", VOICE, "-r", str(RATE), "--file-format=WAVE",
                        "--data-format=LEI16@%d" % SR, "-o", p, text], check=True)
    return read(p)

# ---------------------------------------------------------------- build
def main():
    os.makedirs(VO, exist_ok=True)
    audio_text, used = dict(COMMON_TEXT), set(COMMON_TEXT)
    for k, t in COMMON_TEXT.items(): tts(k, t)
    sahi, shabash = part("sahi", SAHI), part("shabash_sahi", SHABASH_SAHI)

    def word_clip(w):
        cid = word_id(w); tts(cid, bare(w)); audio_text[cid] = bare(w); used.add(cid); return cid

    slides = []
    for s in SLIDES:
        sid, low = s["id"], s["id"].lower()
        pid = "vo_%s_prompt" % low
        tts(pid, s["say_prompt"]); audio_text[pid] = s["say_prompt"]
        d = {"image_id": s["image"], "emoji": s["emoji"]}
        audio = {"prompt": pid}
        if s["type"] == "SENTENCE_CLOZE":
            before, after = [x.strip() for x in s["sentence"].split("___")]
            answer = next(o.rstrip("*") for o in s["options"] if o.endswith("*"))
            full = (before + " " + answer + " " + after).strip()
            # the landed answer is ONE unit on screen even when it is two words ("सो रही")
            words = before.split() + [answer] + after.split()
            sent = part(low + "_sent", full)
            pre = sahi if s.get("demo") else shabash
            st = compose("vo_%s_c" % low, [pre, 250, sent])
            audio_text["vo_%s_c" % low] = ("" if s.get("demo") else "शाबाश! ") + SAHI + " " + full
            d.update(sentence=s["sentence"],
                     options=[{"label": o.rstrip("*"), "audio": word_clip(o.rstrip("*")),
                               **({"correct": True} if o.endswith("*") else {})} for o in s["options"]],
                     correct_cues_ms=est_cues(words, sent, st[2]))
            audio["correct"] = "vo_%s_c" % low
            # the stem with a pause where the blank is: hint 2 (guided) and the question read (practice)
            a_b, a_a = part(low + "_b", before), part(low + "_a", after)
            st2 = compose("vo_%s_stem" % low, [a_b, 700, a_a])
            audio_text["vo_%s_stem" % low] = before + " … " + after
            stem_cues = est_cues(before.split(), a_b, st2[0]) + [st2[1]] + est_cues(after.split(), a_a, st2[2])
            if s.get("demo"):
                d["demo"] = True
                reads = []
                for o in s["options"]:
                    w = o.rstrip("*"); rid = "vo_%s_o_%s" % (low, ROMAN[w])
                    line = (before + " " + w + " " + after).strip()
                    tts(rid, line); audio_text[rid] = line; reads.append(rid)
                for o, rid in zip(d["options"], reads): o["say"] = rid
            elif s["phase"] == "guided":
                d.update(max_attempts=3, hint2_cues_ms=stem_cues)
                audio.update(hint1="vo_try_again", hint2="vo_%s_stem" % low, reveal="vo_reveal")
            else:
                d.update(max_attempts=3, hint2_walk=True, shuffle=False)
                audio["prompt"] = [pid, "vo_%s_stem" % low]
                d["stem_cues_ms"] = stem_cues
                audio.update(hint1="vo_try_again", reveal="vo_reveal")
        else:   # SENTENCE_BUILD
            words = s["sentence"].split()
            sent = part(low + "_sent", s["sentence"])
            sid_s = "vo_%s_s" % low
            st = compose(sid_s, [sent]); audio_text[sid_s] = s["sentence"]
            tiles = [{"word": w, "audio": word_clip(w)} for w in words] + \
                    [{"word": w, "audio": word_clip(w), "distractor": True} for w in s.get("distractors", [])]
            d.update(sentence=s["sentence"], tiles=tiles, sentence_cues_ms=est_cues(words, sent, st[0]))
            audio["sentence"] = sid_s
            if s.get("demo"):
                d["demo"] = True
            else:
                st = compose("vo_%s_c" % low, [shabash, 250, sent])
                audio_text["vo_%s_c" % low] = "शाबाश! " + SAHI + " " + s["sentence"]
                d.update(max_attempts=3, correct_cues_ms=est_cues(words, sent, st[2]))
                audio.update(correct="vo_%s_c" % low, hint1="vo_try_again", reveal="vo_reveal")
                if s["phase"] == "guided": audio["hint2"] = sid_s
                else: d["hint2_walk"] = True
        for v in audio.values():
            for x in (v if isinstance(v, list) else [v]): used.add(x)
        for o in d.get("options", []):
            if o.get("say"): used.add(o["say"])
        slides.append({"id": sid, "phase": s["phase"], "eis": "iconic", "type": s["type"],
                       "prompt_hi": s["prompt_hi"], "audio": audio, "data": d,
                       "signals": {"on_complete": ["sentence_first_try"] if s["phase"] != "tutorial" else []}})
    slides.append({"id": "CEL", "phase": "practice", "eis": "enactive", "type": "CELEBRATION", "prompt_hi": "",
                   "audio": {"prompt": "vo_celebrate", "sfx": "sfx_celebrate"}, "data": {},
                   "signals": {"on_complete": ["lesson_completed"]}})

    ids = sorted(set(audio_text) | used)
    sfx = ["sfx_correct", "sfx_wrong", "sfx_burst", "sfx_celebrate", "sfx_tap"]
    card = {
        "version": "0.2", "skill_code": "HI02H12_L02_S01", "lo_code": "HI02H12_L02", "grade": "G2",
        "attribute": "H12", "skill_type": "CORE", "part_label": "", "theme": "toybox",
        "title": {"hi": "सही शब्द चुनकर वाक्य बनाओ", "en": "Pick the right words to make a sentence"},
        "subtitle_hi": "",
        "skill_description_hi": "चित्र देखकर सिखाए गए शब्दों से वाक्य के लिए सही शब्द चुनता है और शब्दों को क्रम से जोड़कर वाक्य बनाता है।",
        "dt_fallback": None,
        "landing_hero": {"kind": "concept_strip", "cells": [
            {"type": "image", "src": "assets/Images/title_words.webp", "emoji": "🧩", "label": "शब्द"},
            {"type": "image", "src": "assets/Images/title.webp", "emoji": "🐥", "label": "सही शब्द चुनकर वाक्य बनाओ"},
            {"type": "image", "src": "assets/Images/title_sentence.webp", "emoji": "⭐", "label": "वाक्य"}]},
        "phase_gate_caption": {"tutorial": {"text": "चलिए, शुरू करें!", "at_ms": 0},
                               "guided": {"text": "चलिए, साथ में करें!", "at_ms": 0},
                               "practice": {"text": "वाह! अब आपकी बारी।", "at_ms": 0}},
        "landing_nudge": False, "landing_vo_on_tap": False, "audio_chip_on_mascot_foot": True,
        "phase_distribution": {"tutorial": 3, "guided": 4, "practice": 6},
        "scaffold_rules": {"nudge_timeout_ms": {"guided": 5000, "practice": 8000}, "max_attempts": 3},
        "signals_expected": ["slide_entered", "slide_completed", "phase_transition_shown", "sentence_first_try",
                             "sentence_word_placed", "answer_wrong", "answer_revealed", "lesson_completed"],
        "slides": slides,
        "assets": {
            "audio_ext": "wav", "img_ext": "webp",
            "audio": dict({i: "assets/VO/%s.wav" % i for i in ids}, **{x: "assets/SFX/%s.wav" % x for x in sfx}),
            "audio_text": {i: audio_text[i] for i in ids if i in audio_text},
            "image": {s["image"]: "assets/Images/%s.webp" % s["image"] for s in SLIDES},
            "video": {},
        },
    }
    js = json.dumps(card, ensure_ascii=False, indent=1)
    open(os.path.join(GAME, "card.json"), "w", encoding="utf-8").write(js + "\n")

    html_p = os.path.join(GAME, "index.html")
    html = open(html_p, encoding="utf-8").read()
    inline = json.dumps(card, ensure_ascii=False).replace("</", "<\\/")
    html, n = re.subn(r'(<script type="application/json" id="cardData">\n).*?(\n</script>)',
                      lambda m: m.group(1) + inline + m.group(2), html, count=1, flags=re.S)
    assert n == 1, "cardData block not found"
    open(html_p, "w", encoding="utf-8").write(html)
    missing = [i for i in ids if not os.path.exists(os.path.join(VO, i + ".wav"))]
    print("slides:", len(slides), "| clips:", len(ids), "| missing:", missing or "none")


if __name__ == "__main__":
    main()
