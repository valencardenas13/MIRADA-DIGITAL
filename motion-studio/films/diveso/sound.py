"""Score y SFX del video Diveso (Mirada Digital). 120 BPM, 33 s.

Música suave y cálida: kick liviano, hats, pad y bajo en Re menor (Dm–Bb–F–C), arpegio en la
escena de la cata. Funciona sin sonido: el audio acompaña, no explica.

python3 sound.py score score.wav   -> música sola (de acá se mide beats.json)
python3 sound.py mix audio.wav     -> música + SFX en los cues de timeline.js
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lib"))
import dsp  # noqa: E402

BPM = 120
BEAT = 60 / BPM
DUR = 33.0
CHORDS = [[62, 65, 69], [58, 62, 65], [57, 60, 65], [55, 60, 64]]  # Dm Bb F C
ROOTS = [38, 34, 41, 36]
HERE = os.path.dirname(os.path.abspath(__file__))


def timeline():
    with open(os.path.join(HERE, "timeline.js")) as f:
        src = f.read()
    return json.loads(src[src.index("{") : src.rindex("}") + 1])


def score():
    drums, music = dsp.Track(DUR), dsp.Track(DUR)
    nbeats = int(DUR / BEAT)
    for b in range(nbeats):
        at = b * BEAT
        drums.add(dsp.kick(punch=0.7), at, 0.7)
        if b >= 4:
            drums.add(dsp.hat(seed=b), at + BEAT / 2, 0.2, pan=0.2)
        if b >= 12 and b % 2 == 1:
            drums.add(dsp.clap(seed=b), at, 0.3)
    for bar in range(int(np.ceil(DUR / (4 * BEAT)))):
        start = bar * 4 * BEAT
        c = bar % 4
        music.add(dsp.pad(CHORDS[c], 4 * BEAT, cutoff=1500, seed=bar), start, 0.32)
        if start >= 2.0:
            for i in range(8):
                music.add(dsp.bass(ROOTS[c] + (12 if i % 4 == 3 else 0), BEAT * 0.4), start + i * BEAT / 2, 0.42)
        if 17.0 <= start < 27.0:
            arp = [CHORDS[c][0] + 12, CHORDS[c][1] + 12, CHORDS[c][2] + 12, CHORDS[c][1] + 24]
            for i in range(8):
                music.add(dsp.pluck(arp[i % 4], 0.3, "tri", 3500), start + i * BEAT / 2, 0.1, pan=0.3 if i % 2 else -0.3)
    music.duck([b * BEAT for b in range(nbeats)], depth=0.3, release=0.18)
    drums.mix(music)
    return drums


def sfx(data):
    tl = timeline()
    B = data["beats"]
    cues = list(tl["cues"])
    cues += [{"kind": "page", "beat": p} for p in tl["pages"]]
    cues += [{"kind": "tick", "beat": 8 + 1.5 * (k / 12) ** 0.6, "freq": 1500 + k * 50} for k in range(12)]
    cues += [{"kind": "tick", "beat": 40.5 + 1.8 * (k / 12) ** 0.6, "freq": 1700 + k * 50} for k in range(12)]
    fx = dsp.Track(DUR + 3)
    lead = 0.02

    def at_time(c):
        i, frac = int(c["beat"]), c["beat"] - int(c["beat"])
        t0 = B[i] if i < len(B) else B[-1] + (i - len(B) + 1) * BEAT
        return t0 + frac * BEAT

    for c in cues:
        t = at_time(c) - lead
        k = c["kind"]
        seed = abs(int(t * 100))
        if k == "riser":
            d = c["dur"]
            fx.add(dsp.riser(d, seed=seed), t - d + lead, 0.35)
        elif k == "whoosh":
            fx.add(dsp.whoosh(0.32, seed=seed), t - 0.2, 0.32, pan=c.get("pan", 0))
        elif k == "impact":
            fx.add(dsp.impact(0.8, seed=seed), t, c.get("gain", 0.6))
        elif k == "pop":
            fx.add(dsp.blip(c.get("note", 84), 0.12), t, 0.28)
        elif k == "tick":
            fx.add(dsp.tick(c.get("freq", 2000), 0.02), t, 0.14)
        elif k == "page":
            fx.add(dsp.highpass(dsp.noise(0.06, seed), 2500) * np.exp(-dsp.secs(0.06) / 0.015), t, 0.35)
        elif k == "seat":
            fx.add(dsp.kick(0.15, 0.5), t, 0.35)
            fx.add(dsp.blip(81, 0.1), t, 0.25)
    return fx


def final_hit(track, t_hit):
    parts = [dsp.impact(1.0, seed=99) * 0.7, dsp.pad([50, 57, 62, 65, 69], 1.5, cutoff=2600, seed=98) * 0.6]
    sig = np.zeros(max(len(p) for p in parts))
    for p in parts:
        sig[: len(p)] += p
    track.add(dsp.reverb(sig, decay=2.8, wet=0.5), t_hit, 0.8)


if __name__ == "__main__":
    mode, out = sys.argv[1], sys.argv[2]
    music = score()
    if mode == "mix":
        with open(os.path.join(HERE, "beats.json")) as f:
            data = json.load(f)
        t_hit = data["beats"][timeline()["final_hit"]]
        i, fade = int(t_hit * dsp.SR), int(0.04 * dsp.SR)
        music.buf[i : i + fade] *= np.linspace(1, 0, fade)[:, None]
        music.buf[i + fade :] = 0
        music.mix(sfx(data), 1.0)
        final_hit(music, t_hit)
    music.write(out)
