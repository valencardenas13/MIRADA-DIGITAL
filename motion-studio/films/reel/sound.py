"""Score y SFX del reel "f(t)". 128 BPM, 8 compases = 15.0 s.

python3 sound.py score score.wav   -> música sola (de acá se mide beats.json)
python3 sound.py mix audio.wav     -> música + SFX sobre la grilla medida
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lib"))
import dsp  # noqa: E402

BPM = 128
BEAT = 60 / BPM
BARS = 8
DUR = 15.0
PAD = [[62, 65, 69], [58, 62, 65], [57, 60, 65], [55, 60, 64]]  # Dm Bb F C
ROOT = [38, 34, 41, 36]
LEAD = 0.025  # los sonidos arrancan apenas antes del contacto visual


def boop(f0=140, f1=48, dur=0.5):
    t = dsp.secs(dur)
    return dsp.osc(f1 + (f0 - f1) * np.exp(-t / 0.06), dur) * np.exp(-t / 0.18)


def score():
    drums, music = dsp.Track(DUR), dsp.Track(DUR)
    for b in range(BARS * 4):
        at = b * BEAT
        bar = b // 4
        drums.add(dsp.kick(punch=1.2), at, 0.95 if bar else 0.8)
        if b % 2 == 1 and bar >= 1:
            drums.add(dsp.clap(seed=b), at, 0.55)
        if bar >= 1:
            drums.add(dsp.hat(seed=b), at + BEAT / 2, 0.3, pan=0.25)
            if bar >= 3:
                drums.add(dsp.hat(seed=100 + b), at + BEAT / 4, 0.12, pan=-0.3)
                drums.add(dsp.hat(seed=200 + b), at + 3 * BEAT / 4, 0.12, pan=-0.3)
        else:
            drums.add(dsp.hat(seed=b, open_=True), at + BEAT / 2, 0.15)

    # Compás 7 (montaje): redoble que acelera.
    m0 = 6 * 4 * BEAT
    for i in range(8):
        drums.add(dsp.snare(seed=300 + i), m0 + i * BEAT / 2, 0.25 + i * 0.03)
    for i in range(4):
        drums.add(dsp.snare(seed=400 + i), m0 + 3 * BEAT + i * BEAT / 4, 0.45)

    for bar in range(BARS):
        c = bar % 4
        start = bar * 4 * BEAT
        cutoff = 900 if bar == 0 else (2600 if bar == 6 else 1600)
        music.add(dsp.pad(PAD[c], 4 * BEAT, cutoff=cutoff, seed=bar), start, 0.32)
        if bar >= 1:
            for i in range(8):
                note = ROOT[c] + (12 if i % 4 == 3 else 0)
                music.add(dsp.bass(note, BEAT * 0.42), start + i * BEAT / 2, 0.55)
        if 2 <= bar <= 5:
            arp = [PAD[c][0] + 12, PAD[c][1] + 12, PAD[c][2] + 12, PAD[c][1] + 24]
            for i in range(16):
                music.add(dsp.pluck(arp[i % 4], 0.22, cutoff=3200), start + i * BEAT / 4, 0.12, pan=0.35 if i % 2 else -0.35)
    # Drop: acorde grande sostenido en el último compás.
    music.add(dsp.pad([50, 57, 62, 65, 69], 4 * BEAT, cutoff=3000, seed=99), 7 * 4 * BEAT, 0.4)
    music.duck([b * BEAT for b in range(BARS * 4)], depth=0.4, release=0.18)
    drums.mix(music)
    return drums


def sfx(data):
    B = data["beats"]
    b = lambda i: B[i] if i < len(B) else B[-1] + (i - len(B) + 1) * BEAT  # noqa: E731
    mid = lambda i: (b(i) + b(i + 1)) / 2  # noqa: E731
    fx = dsp.Track(DUR)
    at = lambda t, s, g=1.0, pan=0.0: fx.add(s, t - LEAD, g, pan)  # noqa: E731

    # 1 · hook
    at(b(0), dsp.impact(), 0.9)
    at(b(1) - 0.18, dsp.whoosh(0.3), 0.35)
    for k in range(6):
        at(b(2) + k * 0.05, dsp.blip(76 + k * 2, 0.08), 0.18, pan=-0.4 + k * 0.16)
    at(b(3), dsp.whoosh(0.35, rising=False), 0.45)
    at(b(3) + 0.12, dsp.blip(88, 0.1), 0.35)

    # 2 · pelota
    for i, n in zip((5, 6, 7), (79, 76, 72)):
        at(b(i), dsp.kick(0.2, 0.6), 0.45)
        at(b(i), dsp.blip(n, 0.12), 0.35)
    at(b(8), dsp.blip(84, 0.15), 0.4)

    # 3 · curvas
    for j in range(4):
        at(b(8 + j), dsp.whoosh(0.3, seed=20 + j), 0.3, pan=-0.3 + j * 0.2)
        at(b(8 + j), dsp.tick(1800 + j * 300), 0.3)
    at(b(12) - 0.5, dsp.riser(0.5), 0.5)

    # 4 · grilla y datos
    for t in (b(12), b(13), mid(13)):
        at(t, boop(), 0.7)
    for c in range(9):
        at(b(14) + c * 0.035, dsp.tick(1600 + c * 160, 0.025), 0.22, pan=-0.6 + c * 0.15)
    at(b(15) + 0.5, dsp.whoosh(0.35, rising=False, seed=31), 0.35)

    # 5 · morph
    for j in range(4):
        at(b(17 + j), dsp.whoosh(0.28, rising=False, seed=40 + j), 0.3)
        at(b(17 + j), dsp.pluck(81 + [0, 3, 5, 7][j], 0.35, "tri", 4000), 0.25)

    # 6 · esfera
    for j in range(4):
        at(b(20 + j), dsp.pluck(86 + [0, 3, 7, 10][j], 0.5, "sine", 6000), 0.2, pan=[-0.4, 0.4, -0.2, 0.2][j])
    at(b(21), dsp.whoosh(0.5, seed=51), 0.3)
    at(b(23) + 0.25, dsp.whoosh(0.4, rising=False, seed=52), 0.35)

    # 7 · montaje
    for k in range(8):
        t = b(24 + k // 2) if k % 2 == 0 else mid(24 + k // 2)
        at(t, dsp.tick(2600 - k * 120, 0.03), 0.4)
        at(t, dsp.clap(0.15, seed=60 + k), 0.2)
    at(b(24), dsp.riser(b(28) - b(24), seed=61), 0.55)

    # 8 · firma
    at(b(28), dsp.impact(1.2, seed=70), 1.0)
    at(b(29), dsp.pluck(74, 0.6, "saw", 2000), 0.3)
    for k in range(7):
        at(b(30) + k * 0.045, dsp.tick(2200 + k * 90, 0.02), 0.18)
    at(b(31), dsp.impact(0.8, seed=71), 0.7)
    return fx


if __name__ == "__main__":
    mode, out = sys.argv[1], sys.argv[2]
    music = score()
    if mode == "mix":
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "beats.json")) as f:
            music.mix(sfx(json.load(f)), 1.0)
    music.write(out)
