"""Música + SFX de los reels de Mirada Digital, sintetizados en código (sin derechos de terceros).

Uso: python3 audio.py <reel> <organico|pauta> <salida.wav>
     reel: 01 | 02 | 03

120 BPM en los tres: cada corte de escena cae sobre un beat (0,5 s).
La mezcla final se normaliza a -14 LUFS al muxear (mux.sh).
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "motion-studio", "lib"))
import dsp  # noqa: E402

BEAT = 0.5


# ---------------- música ----------------

def music(dur, chords, roots, level, cutoff=lambda t: 2200, arp=lambda t: False, end=None, seed=0):
    """level(t): 0 silencio, 1 liviano (pad + hats + kick a medio tiempo), 2 completo, 3 completo + clap fuerte."""
    drums, mus = dsp.Track(dur), dsp.Track(dur)
    nb = int(dur / BEAT)
    for b in range(nb):
        t = b * BEAT
        if end is not None and t >= end:
            break
        lv = level(t)
        if lv == 0:
            continue
        if lv >= 2 or b % 2 == 0:
            drums.add(dsp.kick(punch=1.1), t, 0.85 if lv >= 2 else 0.6)
        drums.add(dsp.hat(seed=seed + b), t + BEAT / 2, 0.22 if lv >= 2 else 0.14, pan=0.2)
        if lv >= 2:
            drums.add(dsp.hat(seed=seed + 300 + b), t + BEAT / 4, 0.08, pan=-0.3)
            drums.add(dsp.hat(seed=seed + 600 + b), t + 3 * BEAT / 4, 0.08, pan=-0.3)
            if b % 2 == 1:
                drums.add(dsp.clap(seed=seed + b), t, 0.5 if lv >= 3 else 0.38)
    for bar in range(int(np.ceil(dur / (4 * BEAT)))):
        start = bar * 4 * BEAT
        if end is not None and start >= end:
            break
        c = bar % len(chords)
        lv = level(start + 0.01)
        seg = 4 * BEAT if end is None else min(4 * BEAT, end - start)
        if lv >= 1:
            mus.add(dsp.pad(chords[c], seg, cutoff=cutoff(start), seed=seed + bar), start, 0.3 if lv >= 2 else 0.22)
        for i in range(8):
            t = start + i * BEAT / 2
            if (end is not None and t >= end) or level(t) < 2:
                continue
            mus.add(dsp.bass(roots[c] + (12 if i % 4 == 3 else 0), BEAT * 0.42), t, 0.5)
        if arp(start):
            notes = [chords[c][0] + 12, chords[c][1] + 12, chords[c][2] + 12, chords[c][1] + 24]
            for i in range(16):
                t = start + i * BEAT / 4
                if end is not None and t >= end:
                    break
                mus.add(dsp.pluck(notes[i % 4], 0.22, "tri", 3600), t, 0.09, pan=0.35 if i % 2 else -0.35)
    mus.duck([b * BEAT for b in range(nb)], depth=0.35, release=0.17)
    drums.mix(mus)
    return drums


def final_chord(track, t, chord, gain=0.6):
    sig = dsp.pad(chord, 1.6, cutoff=2600, seed=77) * 0.7
    k = dsp.kick(0.5, 1.3)
    sig[: len(k)] += k * 0.6
    track.add(dsp.reverb(sig, decay=2.0, wet=0.4), t, gain)


# ---------------- SFX ----------------

class Fx:
    def __init__(self, dur):
        self.t = dsp.Track(dur)

    def click(self, t, g=0.5):
        self.t.add(dsp.tick(3200, 0.012), t, g)
        self.t.add(dsp.tick(1400, 0.02), t + 0.004, g * 0.6)

    def ding(self, t, g=0.45, midi=88):
        s = dsp.pluck(midi, 0.9, "sine", 8000) + dsp.pluck(midi + 7, 0.9, "sine", 8000) * 0.5
        self.t.add(dsp.reverb(s, 1.2, 0.35), t, g)

    def whoosh(self, t, g=0.3, d=0.3, seed=1, rising=True):
        self.t.add(dsp.whoosh(d, seed=seed, rising=rising), t - d * 0.7, g)

    def pop(self, t, midi=84, g=0.25):
        self.t.add(dsp.blip(midi, 0.1), t, g)

    def tick(self, t, f=2000, g=0.15):
        self.t.add(dsp.tick(f, 0.015), t, g)

    def hit(self, t, g=0.4, seed=3):
        self.t.add(dsp.impact(0.6, seed=seed), t, g)

    def key(self, t, g=0.12):
        self.t.add(dsp.highpass(dsp.noise(0.03, int(t * 1000)), 3000) * np.exp(-dsp.secs(0.03) / 0.006), t, g)


AM = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
AR = [45, 41, 36, 43]
DM = [[62, 65, 69], [58, 62, 65], [57, 60, 65], [55, 60, 64]]  # Dm Bb F C
DR = [38, 34, 41, 36]


def reel01(cta):
    dur = 17.0
    m = music(dur, AM, AR, level=lambda t: 1 if t < 2.5 else 3 if 10 <= t < 13 else 2,
              arp=lambda t: 7 <= t < 13, end=16.5, seed=10)
    final_chord(m, 16.5 if cta == "organico" else 16.0, [57, 64, 69, 72, 76])
    f = Fx(dur)
    for k in range(28):
        f.tick(1.8 * (k / 28) ** 0.85, 1500 + k * 45, 0.16)
    f.ding(1.8, 0.55)
    f.hit(1.8, 0.35)
    f.whoosh(1.95, 0.35, 0.35, 4)
    f.whoosh(2.5, 0.3, 0.45, 5, False)
    f.pop(2.74, 84, 0.3)
    for i, t in enumerate([2.8, 4.5, 4.74, 5.0]):
        f.pop(t, 76 + i * 3, 0.18)
    f.pop(5.35, 91, 0.3)
    for t in (7.0, 10.0, 13.0):
        f.whoosh(t, 0.3, 0.3, int(t * 10))
    for i in range(3):
        at = 7.75 + i * 0.7
        f.whoosh(at + 0.1, 0.28, 0.22, 20 + i)
        f.click(at + 0.2, 0.4)
    f.pop(11.1, 81)
    f.pop(11.28, 84)
    if cta == "organico":
        f.whoosh(15.0, 0.2, 0.25, 30)
        f.ding(15.6, 0.4, 91)
    else:
        f.pop(13.9, 86, 0.3)
        f.ding(14.6, 0.4, 91)
    return m, f.t


def reel02(cta):
    dur = 18.0
    # 0–2 gancho liviano; 2–6 cuenta regresiva: solo kick por beat y pad filtrado (tensión);
    # 6–8 "comentá": medio; 8+ reveal con drop completo.
    def lv(t):
        if t < 2:
            return 1
        if t < 8:
            return 1
        return 3 if t < 13.5 else 2
    m = music(dur, DM, DR, level=lv, cutoff=lambda t: 700 if 2 <= t < 8 else 2400,
              arp=lambda t: 8 <= t < 13.5, end=17.5, seed=20)
    final_chord(m, 17.5, [50, 57, 62, 65, 69])
    f = Fx(dur)
    f.pop(0.05, 84, 0.25)
    for i, t in enumerate((2.5, 3.5, 4.5)):  # 3 · 2 · 1
        f.hit(t, 0.35, 40 + i)
        f.tick(t, 2400 - i * 200, 0.3)
    for k in range(24):  # el anillo se cierra: tic-tac
        f.tick(2.5 + k * 0.125, 1800, 0.07)
    f.ding(5.5, 0.45, 86)
    f.whoosh(6.0, 0.25, 0.3, 50)
    f.whoosh(8.0, 0.35, 0.4, 51)
    f.hit(8.0, 0.4, 52)
    f.click(8.35, 0.45)  # x sobre A
    f.whoosh(8.7, 0.3, 0.35, 53)  # flip de B
    for i, t in enumerate((10.0, 10.8, 11.6)):
        f.whoosh(t, 0.2, 0.2, 60 + i)
        f.pop(t + 0.25, 81 + i * 3, 0.25)
    f.whoosh(13.5, 0.25, 0.3, 70)
    f.pop(14.6, 91, 0.3)
    f.whoosh(15.5, 0.25, 0.3, 71)
    f.ding(16.2, 0.4, 91)
    return m, f.t


def reel03(cta):
    dur = 16.0
    # 0–3 formulario (liviano); 3–6 espera: se apaga y se filtra; 6–6.2 negro (silencio); ding; 8+ cálido completo.
    def lv(t):
        if t < 3:
            return 1
        if t < 6:
            return 1
        if t < 8:
            return 0
        return 3 if t < 14 else 2
    m = music(dur, AM, AR, level=lv, cutoff=lambda t: 2200 if t < 3 else (max(300, 1600 - (t - 3) * 450) if t < 6 else 2400),
              arp=lambda t: 8 <= t < 14, end=15.5, seed=30)
    # fade de la espera: baja el volumen entre 3 y 6 s y corta en seco en 6
    sr = dsp.SR
    a, b = int(3 * sr), int(6 * sr)
    m.buf[a:b] *= np.linspace(1, 0.25, b - a)[:, None]
    m.buf[b:int(6.2 * sr)] = 0
    final_chord(m, 15.5, [57, 64, 69, 72, 76])
    f = Fx(dur)
    # tipeo del formulario + click en Enviar
    for i in range(30):
        f.key(0.15 + i * 0.075)
    f.click(2.55, 0.55)
    f.whoosh(3.0, 0.2, 0.3, 80)
    for t in (3.9, 4.6, 5.3):  # 1 día · 3 días · 1 semana
        f.tick(t, 900, 0.25)
    # negro total y ding del timbre
    f.ding(6.2, 0.7, 84)
    f.ding(6.45, 0.5, 79)
    f.whoosh(8.0, 0.3, 0.35, 81)
    for i, t in enumerate((11.0, 12.0, 13.0)):
        f.pop(t, 79 + i * 3, 0.3)
    f.whoosh(14.0, 0.25, 0.3, 82)
    f.ding(14.6, 0.4, 91)
    return m, f.t


if __name__ == "__main__":
    reel, cta, out = sys.argv[1], sys.argv[2], sys.argv[3]
    m, fx = {"01": reel01, "02": reel02, "03": reel03}[reel](cta)
    m.buf *= 0.75
    m.mix(fx, 1.0)
    m.write(out)
    print(out)
