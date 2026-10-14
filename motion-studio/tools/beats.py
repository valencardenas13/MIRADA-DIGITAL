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

# El tracker llega tarde unos ms: cada beat se ajusta al inicio de onset más cercano (backtrack).
onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=HOP, units="time", backtrack=True)
if len(onsets) and len(beats):
    near = onsets[np.abs(onsets[None, :] - beats[:, None]).argmin(axis=1)]
    beats = np.where(np.abs(near - beats) < 0.07, near, beats)

# El tracker suele saltear los primeros beats: se completan hacia atrás con el período medido.
period = float(np.median(np.diff(beats))) if len(beats) > 1 else 60 / float(np.atleast_1d(tempo)[0])
while len(beats) and beats[0] - period > -0.03:
    t = max(0.0, beats[0] - period)
    if len(onsets):
        o = onsets[np.abs(onsets - t).argmin()]
        t = o if abs(o - t) < 0.07 else t
    beats = np.insert(beats, 0, t)

# Y hacia adelante hasta el final del audio.
duration = len(y) / sr
while len(beats) and beats[-1] + period < duration - 0.05:
    t = beats[-1] + period
    if len(onsets):
        o = onsets[np.abs(onsets - t).argmin()]
        t = o if abs(o - t) < 0.07 else t
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
