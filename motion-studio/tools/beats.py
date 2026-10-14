"""Mide la grilla de beats de un audio y escribe beats.json + beats.js (window.BEATS).

Uso: python3 tools/beats.py <audio.wav> <film_dir> [--bpm 112] [--bar-offset 0]
--bpm es la pista de tempo esperada (ayuda a librosa a no medir el doble o la mitad).
--bar-offset N: el primer compás empieza en el beat N (por defecto el primer beat es el 1).
"""

import argparse
import json
import os

import librosa
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("audio")
ap.add_argument("film_dir")
ap.add_argument("--bpm", type=float, default=None)
ap.add_argument("--bar-offset", type=int, default=0)
args = ap.parse_args()

SR, HOP = 44100, 256  # ~5.8 ms de resolución
y, sr = librosa.load(args.audio, sr=SR, mono=True)
onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP)
tempo, frames = librosa.beat.beat_track(
    onset_envelope=onset_env, sr=sr, hop_length=HOP,
    start_bpm=args.bpm or 120, tightness=400 if args.bpm else 100,
)
beats = librosa.frames_to_time(frames, sr=sr, hop_length=HOP)

# Ajuste fino: cada beat se mueve al inicio del ataque más fuerte de la banda grave (bombo)
# cerca de él. Envolvente de Hilbert (suave, sin la ondulación del propio bombo) y cruce del
# 20% entre el piso y el pico local. Si no hay un ataque claro, queda el tiempo del tracker.
from scipy.signal import butter, hilbert, sosfiltfilt

low = sosfiltfilt(butter(4, 150, "low", fs=sr, output="sos"), y)
env = np.abs(hilbert(low))
env = np.convolve(env, np.ones(32) / 32, mode="same")
peak_floor = np.percentile(env, 60)


def refine(t):
    i0 = max(0, int((t - 0.06) * sr))
    i1 = min(len(env), int((t + 0.06) * sr))
    if i1 - i0 < 10:
        return t
    # pico: el máximo poco después de la subida más grande de la ventana
    step = 64
    seg = env[i0 : i1 + int(0.03 * sr)]
    jump = seg[step:] - seg[:-step]
    k = int(np.argmax(jump[: i1 - i0]))
    pk = seg[k : k + int(0.03 * sr)].max()
    base = seg[max(0, k - int(0.02 * sr)) : k + 1].min()
    if pk - base < peak_floor * 0.5:
        return t
    above = np.nonzero(seg[max(0, k - int(0.02 * sr)) :] > base + 0.2 * (pk - base))[0]
    return (i0 + max(0, k - int(0.02 * sr)) + above[0]) / sr if len(above) else t


onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=HOP, units="time", backtrack=True)
beats = np.array([refine(t) for t in beats])

# El tracker suele saltear los primeros beats: se completan hacia atrás con el período medido.
period = float(np.median(np.diff(beats))) if len(beats) > 1 else 60 / float(np.atleast_1d(tempo)[0])
while len(beats) and beats[0] - period > -0.03:
    t = max(0.0, refine(beats[0] - period))
    beats = np.insert(beats, 0, t)

# Y hacia adelante hasta el final del audio.
duration = len(y) / sr
while len(beats) and beats[-1] + period < duration - 0.05:
    t = refine(beats[-1] + period)
    beats = np.append(beats, t)

tempo = 60 / period
bars = beats[args.bar_offset :: 4]

data = {
    "source": os.path.basename(args.audio),
    "tempo": round(tempo, 3),
    "duration": round(duration, 3),
    "beats": [round(float(b), 4) for b in beats],
    "bars": [round(float(b), 4) for b in bars],
    "onsets": [round(float(o), 4) for o in onsets],
}

with open(os.path.join(args.film_dir, "beats.json"), "w") as f:
    json.dump(data, f, indent=1)
with open(os.path.join(args.film_dir, "beats.js"), "w") as f:
    f.write("window.BEATS = " + json.dumps(data) + ";\n")

print(f"tempo {tempo:.2f} BPM, {len(beats)} beats, {len(bars)} compases, {len(onsets)} onsets")
