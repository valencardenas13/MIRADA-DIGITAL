"""Score y SFX sintetizados para este film.

python3 sound.py score score.wav   -> música sola (de acá se mide beats.json)
python3 sound.py mix audio.wav     -> música + SFX colocados sobre la grilla medida
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lib"))
import dsp  # noqa: E402

BPM = 112
BARS = 8
BEAT = 60 / BPM
DUR = BARS * 4 * BEAT
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
ROOTS = [45, 41, 36, 43]


def score():
    drums, music = dsp.Track(DUR), dsp.Track(DUR)
    for b in range(BARS * 4):
        at = b * BEAT
        if b % 2 == 0:
            drums.add(dsp.kick(), at, 0.9)
        else:
            drums.add(dsp.clap(seed=b), at, 0.5)
        for half in (0, 0.5):
            drums.add(dsp.hat(seed=b * 2 + int(half * 2)), at + half * BEAT, 0.25, pan=0.3)
    for bar in range(BARS):
        c = bar % 4
        music.add(dsp.pad(CHORDS[c], 4 * BEAT, seed=bar), bar * 4 * BEAT, 0.35)
        for i in range(8):
            music.add(dsp.bass(ROOTS[c] + (12 if i % 4 == 3 else 0), BEAT * 0.45), bar * 4 * BEAT + i * BEAT / 2, 0.5)
    music.duck([b * BEAT for b in range(0, BARS * 4, 2)], depth=0.45)
    drums.mix(music)
    return drums


def sfx(beats):
    """SFX sobre los tiempos medidos. Cambiar según los momentos del film."""
    fx = dsp.Track(DUR)
    for t in beats["bars"]:
        fx.add(dsp.whoosh(0.35, rising=True), t - 0.35, 0.35)
        fx.add(dsp.blip(88), t, 0.25)
    for i, t in enumerate(beats["beats"][:8]):
        fx.add(dsp.tick(2000 + i * 120), t, 0.3)
    return fx


if __name__ == "__main__":
    mode, out = sys.argv[1], sys.argv[2]
    music = score()
    if mode == "mix":
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "beats.json")) as f:
            music.mix(sfx(json.load(f)))
    music.write(out)
