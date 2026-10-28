# -*- coding: utf-8 -*-
"""Ship the game with WAV audio and WebM-only video.

    python _tools/to_wav_webm.py

Asked for on 30 Sep: WebP pictures (already), WebM video, WAV audio.
  AUDIO  every assets/VO and assets/SFX .ogg is decoded to PCM WAV, 16-bit mono 22.05 kHz - the
         smallest WAV that still carries speech cleanly (the recordings arrive at 24 kHz). Levels are
         whatever the OGG already had, so nothing gets louder or quieter. WAV has no compression:
         this takes the audio from ~2.4 MB to ~24 MB, which was said before it was asked for.
  VIDEO  the MP4s leave the game; the WebM next to each is all that ships. A browser that cannot
         play VP9 falls back to the still scene the slide already carries (the <video> error path).
  CARD   audio_ext -> "wav", every assets/VO|SFX/*.ogg path -> .wav, every video path -> .webm, in
         both card copies; the engine's two hard-coded ".ogg" loaders follow.
Nothing is deleted: the OGGs and MP4s go to HI02H12_L02_S01/_backup/pre_wav_webm_<date>/.
"""
import io, json, os, re, shutil, subprocess, sys, time
import imageio_ffmpeg

sys.stdout.reconfigure(encoding="utf-8")
FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "HI02H12_L02_S01")
os.chdir(ROOT)
BK = os.path.join("..", "_backup", "pre_wav_webm_" + time.strftime("%Y%m%d"))   # project root, not the shipped folder


def park(rel):
    dst = os.path.join(BK, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.move(rel, dst)


a_in = a_out = 0; n = 0
for d in ("assets/VO", "assets/SFX"):
    for f in sorted(os.listdir(d)):
        if not f.endswith(".ogg"): continue
        src = d + "/" + f; dst = src[:-4] + ".wav"
        subprocess.run([FF, "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le", dst], check=True)
        a_in += os.path.getsize(src); a_out += os.path.getsize(dst); n += 1
        park(src)
print("audio: %d clips  %.1f MB ogg -> %.1f MB wav" % (n, a_in / 1e6, a_out / 1e6))

v = 0
for f in sorted(os.listdir("assets/video")):
    if f.endswith(".mp4"):
        webm = "assets/video/" + f[:-4] + ".webm"
        assert os.path.exists(webm), "no WebM for " + f
        v += os.path.getsize("assets/video/" + f); park("assets/video/" + f)
print("video: %.1f MB of MP4 left the game" % (v / 1e6))


def fix_card(txt):
    txt = txt.replace('"audio_ext": "ogg"', '"audio_ext": "wav"')
    txt = re.sub(r'(assets/(?:VO|SFX)/[^"]+?)\.ogg"', r'\1.wav"', txt)
    txt = re.sub(r'(assets/video/[^"]+?)\.mp4"', r'\1.webm"', txt)
    return txt


t = fix_card(io.open("card.json", encoding="utf-8", newline="").read())
h = io.open("index.html", encoding="utf-8", newline="").read()
head, mid, tail = re.split(r'(?s)(<script type="application/json" id="cardData">.*?</script>)', h, maxsplit=1)
mid = fix_card(mid)
assert json.loads(t) == json.loads(re.search(r'(?s)id="cardData">(.*?)</script>', mid).group(1)), "card copies drifted"
h = head + mid + tail
for old, new in [
    ('var a = new Audio((typeof bustAudio==="function"?bustAudio(dir+f+".ogg"):dir+f+".ogg")); a.volume = 0.7;',
     'var a = new Audio((typeof bustAudio==="function"?bustAudio(dir+f+".wav"):dir+f+".wav")); a.volume = 0.7;   /* [H11-156] WAV now */'),
    ('try{ const a = new Audio(bustAudio(audioDir(name) + name + ".ogg")); a.volume = 0.7;',
     'try{ const a = new Audio(bustAudio(audioDir(name) + name + "." + AUDIO_EXT)); a.volume = 0.7;   /* [H11-156] follows the card */'),
    ('|| ("assets/video/" + d.video_id + ".mp4"));', '|| ("assets/video/" + d.video_id + ".webm"));   /* [H11-156] WebM only */'),
]:
    assert h.count(old) == 1, old[:60]
    h = h.replace(old, new)
io.open("card.json", "w", encoding="utf-8", newline="").write(t)
io.open("index.html", "w", encoding="utf-8", newline="").write(h)
left = [m for m in re.findall(r'assets/(?:VO|SFX)/[^"\']+?\.ogg', t)]
print("card: audio_ext wav, %d .ogg paths left, %d .mp4 paths left" % (len(left), len(re.findall(r'\.mp4"', t))))
