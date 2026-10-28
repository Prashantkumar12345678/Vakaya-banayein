# -*- coding: utf-8 -*-
"""Bring a recorded VO batch into the game, retiring the clips it replaces.

    python _tools/import_vo_batch.py "<batch>.zip" [--dry]

For every WAV in the batch:
  1. the clip it replaces is MOVED, never deleted:
       assets/VO/<id>.ogg           -> _backup/VO_retired_<date>/<id>.ogg
       _masters/voiceovers/<id>.wav -> _masters/voiceovers/retired_<date>/<id>.wav
  2. the new WAV becomes the master:  _masters/voiceovers/<id>.wav
  3. it is levelled and encoded for the game:  assets/VO/<id>.ogg  (Opus, 48kHz mono, 32kbps -
     the format every clip already in the game uses)

LEVELLING. The clips already in the game sit at about -14.5 dB speech RMS with peaks near
-1.5 dBFS; the batch that arrived on 2026-09-29 ranged from -20 to -14. Played side by side,
a hint 5 dB quieter than the question before it reads as the game going quiet. So each clip
is brought to the same -14.5 speech RMS, capped so no peak goes above -1.5 dBFS.

WORD CLIPS arrive named by the word itself (मोर.wav). They map to vo_name_<romanised> - the ids
the card already uses for the eight that exist, and new ids for the seven that do not.
"""
import io, os, shutil, subprocess, sys, tempfile, time, unicodedata, zipfile
import numpy as np
import imageio_ffmpeg

sys.stdout.reconfigure(encoding="utf-8")
FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
GAME = os.path.join(ROOT, "HI02H12_L02_S01")
VO = os.path.join(GAME, "assets", "VO")
MASTERS = os.path.join(ROOT, "_masters", "voiceovers")
DATE = time.strftime("%Y%m%d")
TARGET_RMS, PEAK_CAP = -14.5, -1.5

WORDS = {
    "मोर": "vo_name_mor", "मुर्गी": "vo_name_murgi", "घोड़ा": "vo_name_ghoda", "बकरी": "vo_name_bakri",
    "घोड़ी": "vo_name_ghodi", "शेरनी": "vo_name_sherni", "गाय": "vo_name_gaay", "मुर्गा": "vo_name_murga",
    "बिल्ली": "vo_name_billi", "भेड़": "vo_name_bhed", "हथिनी": "vo_name_hathini", "चूहा": "vo_name_chuha",
    "खरगोश": "vo_name_khargosh", "घोड़नी": "vo_name_ghodni", "तोता": "vo_name_tota",
    # 29 Sep batch 23 - P3/P4: the sentence stem, and each option said on its own
    "शेरनी मेले में": "vo_stem_sherni", "बंदर पेड़ पर": "vo_stem_bandar",
    "जाता है ।": "vo_opt_jata", "जाती है ।": "vo_opt_jati",
    "चढ़ता है ।": "vo_opt_chadhta", "चढ़ती है ।": "vo_opt_chadhti",
}


WORDS_NFC = {unicodedata.normalize("NFC", k): v for k, v in WORDS.items()}


def pcm(path, sr=48000):
    raw = subprocess.run([FF, "-v", "quiet", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
                         stdout=subprocess.PIPE).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0


def speech_rms_db(x, sr=48000):
    f = x[:len(x) // (sr // 40) * (sr // 40)].reshape(-1, sr // 40)
    e = np.sqrt((f ** 2).mean(1) + 1e-12)
    v = e[20 * np.log10(e) > -45]
    return 20 * np.log10(np.sqrt((v ** 2).mean()) + 1e-12) if len(v) else -99.0


def main():
    zpath = sys.argv[1]; dry = "--dry" in sys.argv
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(zpath) as z:
        z.extractall(tmp)
    wavs = []
    for d, _, fs in os.walk(tmp):
        for f in fs:
            if f.lower().endswith(".wav"):
                # ड़ arrives both as one code point (U+095C) and as ड + nukta; NFC makes them equal
                stem = unicodedata.normalize("NFC", os.path.splitext(f)[0])
                wavs.append((WORDS_NFC.get(stem, stem), os.path.join(d, f), stem))
    unknown = [s for i, _, s in wavs if not i.startswith("vo_")]
    assert not unknown, "no id for: %s" % unknown
    ret_vo = os.path.join(ROOT, "_backup", "VO_retired_" + DATE)   # project-root _backup: the game folder ships as-is
    ret_m = os.path.join(MASTERS, "retired_" + DATE)
    for d in (ret_vo, ret_m):
        if not dry: os.makedirs(d, exist_ok=True)
    for vid, src, stem in sorted(wavs):
        x = pcm(src)
        rms = speech_rms_db(x); peak = 20 * np.log10(np.abs(x).max() + 1e-9)
        gain = min(TARGET_RMS - rms, PEAK_CAP - peak)
        old = os.path.join(VO, vid + ".wav")   # [H11-156] the game ships WAV
        tag = "replace" if os.path.exists(old) else "NEW    "
        print("%s %-24s %-8s rms %6.1f -> %6.1f  (gain %+5.1f dB)" % (tag, vid, stem if stem != vid else "", rms, rms + gain, gain))
        if dry: continue
        if os.path.exists(old):
            shutil.move(old, os.path.join(ret_vo, vid + ".wav"))
        om = os.path.join(MASTERS, vid + ".wav")
        if os.path.exists(om):
            shutil.move(om, os.path.join(ret_m, vid + ".wav"))
        shutil.copy2(src, om)
        subprocess.run([FF, "-v", "error", "-y", "-i", src, "-af", "volume=%.2fdB" % gain,
                        "-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le", old], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d clips. Retired copies: %s" % (len(wavs), "(dry run)" if dry else ret_vo))


if __name__ == "__main__":
    main()
