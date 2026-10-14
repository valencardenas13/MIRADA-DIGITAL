"""Síntesis de score y SFX en código. Todo determinista: el ruido usa semillas fijas."""

import numpy as np
import soundfile as sf
from numba import njit

SR = 48000


def secs(n):
    return np.arange(int(n * SR)) / SR


def rng(seed):
    return np.random.default_rng(seed)


def env(n, attack=0.005, decay=0.3, sustain=0.0, release=0.0, dur=None):
    """Envolvente: ataque lineal, caída exponencial hacia `sustain`, release lineal al final."""
    dur = dur if dur is not None else attack + decay * 6
    t = secs(dur)
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    d = sustain + (1 - sustain) * np.exp(-np.maximum(t - attack, 0) / max(decay, 1e-4))
    e = a * d
    if release > 0:
        e *= np.clip((dur - t) / release, 0, 1)
    return e[: int(n * SR)] if n else e


def osc(freq, dur, wave="sine", phase=0.0):
    """Oscilador. `freq` puede ser un número o un array (barrido) del largo de la nota."""
    t = secs(dur)
    f = np.broadcast_to(freq, t.shape).astype(float)
    ph = 2 * np.pi * np.cumsum(f) / SR + phase
    if wave == "sine":
        return np.sin(ph)
    if wave == "square":
        return np.sign(np.sin(ph))
    if wave == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if wave == "tri":
        return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) - 1
    raise ValueError(wave)


@njit(cache=True)
def _onepole(x, a):
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def lowpass(x, cutoff):
    """Pasabajos de un polo. `cutoff` en Hz, número o array (barrido)."""
    c = np.broadcast_to(cutoff, x.shape).astype(float)
    return _onepole(np.ascontiguousarray(x, dtype=float), 1 - np.exp(-2 * np.pi * c / SR))


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def noise(dur, seed=0):
    return rng(seed).uniform(-1, 1, int(dur * SR))


def note_hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


# --- Percusión ---

def kick(dur=0.45, punch=1.0):
    t = secs(dur)
    f = 45 + 110 * np.exp(-t / 0.035)
    body = osc(f, dur) * np.exp(-t / 0.16)
    click = noise(0.004, seed=11) * punch * 0.5
    body[: len(click)] += click
    return np.tanh(body * 1.6)


def snare(dur=0.25, seed=3):
    t = secs(dur)
    tone = osc(190, dur) * np.exp(-t / 0.05) * 0.5
    n = highpass(noise(dur, seed), 1200) * np.exp(-t / 0.07)
    return tone + n * 0.8


def clap(dur=0.3, seed=5):
    t = secs(dur)
    n = highpass(noise(dur, seed), 900)
    e = np.zeros_like(t)
    for off in (0.0, 0.011, 0.022):
        e += np.where(t >= off, np.exp(-(t - off) / 0.012), 0) * 0.5
    e += np.where(t >= 0.03, np.exp(-(t - 0.03) / 0.09), 0)
    return n * e * 0.8


def hat(dur=0.06, seed=7, open_=False):
    d = 0.3 if open_ else dur
    t = secs(d)
    n = highpass(noise(d, seed), 7000)
    return n * np.exp(-t / (0.09 if open_ else 0.018)) * 0.5


# --- SFX ---

def tick(freq=2400, dur=0.03):
    t = secs(dur)
    return osc(freq, dur) * np.exp(-t / 0.006)


def blip(midi=84, dur=0.12):
    t = secs(dur)
    return osc(note_hz(midi), dur, "tri") * np.exp(-t / 0.04)


def whoosh(dur=0.6, seed=9, rising=True):
    t = secs(dur)
    k = t / dur
    sweep = 300 + 6000 * (k if rising else 1 - k) ** 2
    n = lowpass(noise(dur, seed), sweep)
    shape = np.sin(np.pi * k) ** 1.5
    return n * shape * 1.6


def impact(dur=0.9, seed=13):
    t = secs(dur)
    sub = osc(42 + 30 * np.exp(-t / 0.05), dur) * np.exp(-t / 0.35)
    crack = lowpass(noise(dur, seed), 3000) * np.exp(-t / 0.06)
    return np.tanh((sub + crack * 0.6) * 1.4)


def riser(dur=2.0, seed=17):
    t = secs(dur)
    k = t / dur
    tone = osc(200 + 900 * k ** 2, dur, "saw") * 0.15
    n = lowpass(noise(dur, seed), 500 + 8000 * k ** 2) * 0.5
    return (tone + n) * k ** 2


# --- Tonal ---

def pluck(midi, dur=0.4, wave="saw", cutoff=2500):
    t = secs(dur)
    x = osc(note_hz(midi), dur, wave)
    x = lowpass(x, cutoff * np.exp(-t / 0.08) + 150)
    return x * np.exp(-t / (dur * 0.35))


def bass(midi, dur=0.4):
    t = secs(dur)
    x = osc(note_hz(midi), dur, "saw") * 0.6 + osc(note_hz(midi - 12), dur) * 0.6
    x = lowpass(x, 300 + 900 * np.exp(-t / 0.06))
    return x * env(dur, 0.004, dur * 0.5, 0.4, 0.03, dur)


def pad(midis, dur, cutoff=1400, seed=21):
    """Acorde con osciladores levemente desafinados (detune fijo por semilla)."""
    r = rng(seed)
    x = np.zeros(int(dur * SR))
    for m in midis:
        for _ in range(3):
            x += osc(note_hz(m) * (1 + r.uniform(-0.004, 0.004)), dur, "saw", r.uniform(0, 6.28))
    x = lowpass(x / (len(midis) * 3), cutoff)
    return x * env(dur, 0.3, dur, 0.85, 0.4, dur)


# --- Mezcla ---

class Track:
    """Buffer estéreo donde se colocan sonidos en segundos."""

    def __init__(self, dur):
        self.buf = np.zeros((int(dur * SR) + SR, 2))
        self.dur = dur

    def add(self, sig, at, gain=1.0, pan=0.0):
        i = int(round(at * SR))
        if i >= len(self.buf) or i + len(sig) <= 0:
            return
        if i < 0:
            sig, i = sig[-i:], 0
        n = min(len(sig), len(self.buf) - i)
        l = gain * np.cos((pan + 1) * np.pi / 4) * np.sqrt(2)
        r = gain * np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
        self.buf[i : i + n, 0] += sig[:n] * l
        self.buf[i : i + n, 1] += sig[:n] * r

    def mix(self, other, gain=1.0):
        n = min(len(self.buf), len(other.buf))
        self.buf[:n] += other.buf[:n] * gain

    def duck(self, times, depth=0.5, release=0.2):
        """Sidechain simple: baja el volumen en cada tiempo de `times` y se recupera."""
        t = np.arange(len(self.buf)) / SR
        g = np.ones_like(t)
        for at in times:
            m = t >= at
            g[m] = np.minimum(g[m], 1 - depth * np.exp(-(t[m] - at) / release))
        self.buf *= g[:, None]

    def write(self, path):
        out = self.buf[: int(self.dur * SR)]
        peak = np.max(np.abs(out)) or 1.0
        out = out / peak * 0.89  # headroom; la sonoridad final (-14 LUFS) se fija al mezclar
        sf.write(path, out, SR, subtype="PCM_24")


def reverb(x, decay=1.8, wet=0.35, seed=77):
    """Reverb por convolución con una respuesta de ruido que decae (determinista)."""
    from scipy.signal import fftconvolve

    n = int(decay * SR)
    t = np.arange(n) / SR
    ir = rng(seed).uniform(-1, 1, n) * np.exp(-t * 6.9 / decay)
    ir = lowpass(ir, 5000)
    ir /= np.sqrt(np.sum(ir**2)) or 1.0
    tail = fftconvolve(x, ir)[: len(x) + n]
    out = np.zeros(len(x) + n)
    out[: len(x)] += x * (1 - wet)
    return out + tail * wet
