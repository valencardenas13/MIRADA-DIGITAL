"""Score y SFX del pitch Mirada Digital × Tasker. 120 BPM, 15 compases = 30 s.

Música: kick en negras, hats en corcheas, bajo y acordes en La menor (Am–F–C–G, un compás
cada 2 s). El gancho (0–3 s) es solo kick; el drop completo entra a los 3 s.

python3 sound.py score score.wav   -> música sola (de acá se mide beats.json)
python3 sound.py mix audio.wav     -> música + SFX en los cues de timeline.js (compartido con el film)
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lib"))
import dsp  # noqa: E402

BPM = 120
BEAT = 60 / BPM
DUR = 30.0
DROP = 3.0
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
ROOTS = [45, 41, 36, 43]
HERE = os.path.dirname(os.path.abspath(__file__))


def score():
    drums, music = dsp.Track(DUR), dsp.Track(DUR)
    nbeats = int(DUR / BEAT)
    for b in range(nbeats):
        at = b * BEAT
        drums.add(dsp.kick(punch=1.2), at, 0.95)
        if at >= DROP:
            drums.add(dsp.hat(seed=b), at, 0.18, pan=0.2)
            drums.add(dsp.hat(seed=500 + b), at + BEAT / 2, 0.28, pan=-0.2)
            if b % 2 == 1:
                drums.add(dsp.clap(seed=b), at, 0.45)
    for bar in range(int(DUR / (4 * BEAT))):
        start = bar * 4 * BEAT
        c = bar % 4
        for i in range(8):
            t = start + i * BEAT / 2
            if t < DROP:
                continue
            note = ROOTS[c] + (12 if i % 4 == 3 else 0)
            music.add(dsp.bass(note, BEAT * 0.42), t, 0.55)
        if start + 4 * BEAT > DROP:
            pad = dsp.pad(CHORDS[c], 4 * BEAT, cutoff=1800, seed=bar)
            skip = int(max(0, DROP - start) * dsp.SR)
            music.add(pad[skip:], max(start, DROP), 0.3)
    music.duck([b * BEAT for b in range(nbeats)], depth=0.4, release=0.18)
    drums.mix(music)
    return drums


EMAIL = "agenciamiradadigital@gmail.com"


def timeline():
    with open(os.path.join(HERE, "timeline.js")) as f:
        src = f.read()
    return json.loads(src[src.index("{") : src.rindex("}") + 1])


def sfx(data):
    """SFX en los cues de timeline.js, más los ticks del contador (0→30) y del tipeo del mail."""
    tl = timeline()
    cues = list(tl["cues"])
    cues += [{"kind": "tick", "beat": 40 + 3 * (k / 15) ** 0.5, "freq": 1400 + k * 60, "gain": 0.16} for k in range(15)]
    cues += [{"kind": "type", "beat": 56 + k * 0.06} for k in range(len(EMAIL))]
    B = data["beats"]
    fx = dsp.Track(DUR + 3)
    lead = 0.02

    def at_time(c):
        if "beat" in c:
            i, frac = int(c["beat"]), c["beat"] - int(c["beat"])
            t0 = B[i] if i < len(B) else B[-1] + (i - len(B) + 1) * BEAT
            return t0 + frac * BEAT + c.get("offset", 0)
        return c["t"]

    for c in cues:
        t = at_time(c) - lead
        kind = c["kind"]
        if kind == "riser":
            d = c.get("dur", 1.5)
            fx.add(dsp.riser(d, seed=int(t * 100)), t - d + lead, 0.45)
        elif kind == "whoosh":
            fx.add(dsp.whoosh(0.32, seed=int(t * 100)), t - 0.2, 0.4, pan=c.get("pan", 0))
        elif kind == "impact":
            fx.add(dsp.impact(0.8, seed=int(t * 100)), t, c.get("gain", 0.7))
        elif kind == "flash":
            fx.add(dsp.impact(0.5, seed=int(t * 100)), t, 0.45)
            fx.add(dsp.hat(seed=int(t * 10), open_=True), t, 0.35)
        elif kind == "click":
            fx.add(dsp.tick(3200, 0.012), t, 0.5)
            fx.add(dsp.tick(1400, 0.02), t + 0.004, 0.35)
        elif kind == "tick":
            fx.add(dsp.tick(c.get("freq", 2200), 0.02), t, c.get("gain", 0.2))
        elif kind == "pop":
            fx.add(dsp.blip(c.get("note", 84), 0.1), t, 0.3)
        elif kind == "type":
            fx.add(dsp.tick(1800 + (int(t * 1000) % 7) * 90, 0.015), t, 0.12)
    return fx


def final_hit(track, t_hit):
    """Golpe final con cola de reverb que sigue después de cortar la música."""
    parts = [dsp.impact(1.0, seed=99), dsp.kick(0.6, 1.4) * 0.8,
             dsp.pad([45, 52, 57, 60, 64], 1.2, cutoff=2500, seed=98) * 0.6]
    sig = np.zeros(max(len(p) for p in parts))
    for p in parts:
        sig[: len(p)] += p
    track.add(dsp.reverb(sig, decay=2.5, wet=0.45), t_hit, 0.9)


if __name__ == "__main__":
    mode, out = sys.argv[1], sys.argv[2]
    music = score()
    if mode == "mix":
        with open(os.path.join(HERE, "beats.json")) as f:
            data = json.load(f)
        B = data["beats"]
        t_hit = B[timeline()["final_hit"]]
        # La música se corta en el golpe final y queda sonando la cola de reverb.
        i = int(t_hit * dsp.SR)
        fade = int(0.03 * dsp.SR)
        music.buf[i : i + fade] *= np.linspace(1, 0, fade)[:, None]
        music.buf[i + fade :] = 0
        music.mix(sfx(data), 1.0)
        final_hit(music, t_hit)
    music.write(out)
