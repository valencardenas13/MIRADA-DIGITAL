"""SFX del Reel 01 (pista aparte, sin música). Sintetizados en código: sin derechos de terceros.
Uso: python3 reel01_sfx.py organico|pauta salida.wav"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "motion-studio", "lib"))
import dsp

cta, out = sys.argv[1], sys.argv[2]
tr = dsp.Track(17.0)

def click(t, g=0.5):
    tr.add(dsp.tick(3200, 0.012), t, g); tr.add(dsp.tick(1400, 0.02), t + 0.004, g * 0.6)

def ding(t, g=0.45, midi=88):
    tr.add(dsp.reverb(dsp.pluck(midi, 0.9, "sine", 8000) + dsp.pluck(midi + 7, 0.9, "sine", 8000) * 0.5, 1.2, 0.35), t, g)

# contador subiendo: ticks cada vez más rápidos
for k in range(28):
    t = 1.8 * (k / 28) ** 0.85
    tr.add(dsp.tick(1500 + k * 45, 0.015), t, 0.16)
ding(1.8, 0.55)
tr.add(dsp.impact(0.6, seed=3), 1.8, 0.35)
tr.add(dsp.whoosh(0.35, seed=4), 1.9, 0.35)              # estallido
tr.add(dsp.whoosh(0.45, seed=5, rising=False), 2.25, 0.3) # se arma el 10k
tr.add(dsp.blip(84, 0.12), 2.74, 0.3)
for i, t in enumerate([2.8, 4.5, 4.74, 5.0]):
    tr.add(dsp.blip(76 + i * 3, 0.08), t, 0.18)
tr.add(dsp.blip(91, 0.12), 5.35, 0.3)
for t in (7.0, 10.0, 13.0):                               # cortes secos
    tr.add(dsp.whoosh(0.3, seed=int(t * 10)), t - 0.22, 0.3)
for i in range(3):                                        # tachados + x
    at = 7.75 + i * 0.7
    tr.add(dsp.whoosh(0.22, seed=20 + i), at - 0.02, 0.28)
    click(at + 0.2, 0.4)
for t in (11.1, 11.28):
    tr.add(dsp.blip(81, 0.1), t, 0.25)
if cta == "organico":
    tr.add(dsp.whoosh(0.25, seed=30), 14.85, 0.2)
    ding(15.6, 0.4, 91)
else:
    ding(14.6, 0.4, 91)
tr.write(out)
print(out)
