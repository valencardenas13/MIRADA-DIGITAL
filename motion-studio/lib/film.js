// Helpers compartidos para films. Todo es función pura del tiempo: nada guarda estado entre frames.
(function () {
  // PRNG con semilla. Mismo seed => misma secuencia, en cualquier orden de render.
  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // Valor aleatorio estable para una clave entera (no depende de cuántas veces se llamó antes).
  function hash(n, seed = 1) {
    return mulberry32((n * 2654435761) ^ seed)();
  }

  // Ruido 1D suave, determinista.
  function noise1(x, seed = 1) {
    const i = Math.floor(x);
    const f = x - i;
    const u = f * f * (3 - 2 * f);
    return hash(i, seed) * (1 - u) + hash(i + 1, seed) * u;
  }

  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, k) => a + (b - a) * k;

  // Progreso 0..1 de t dentro de [a, b]. Una ventana vacía o invertida se comporta como un corte en a.
  const span = (t, a, b) => (b <= a ? (t >= a ? 1 : 0) : clamp((t - a) / (b - a)));

  const ease = {
    linear: (k) => k,
    out: (k) => 1 - Math.pow(1 - k, 3),
    in: (k) => k * k * k,
    inOut: (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
    expoOut: (k) => (k === 1 ? 1 : 1 - Math.pow(2, -10 * k)),
    back: (k) => {
      const c = 1.70158;
      return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2);
    },
    // Resorte amortiguado sin estado: posición analítica en función de k.
    spring: (k, damping = 6, freq = 12) => 1 - Math.exp(-damping * k) * Math.cos(freq * k),
  };

  // --- Grilla de beats medida (window.BEATS lo carga beats.js) ---
  const B = () => window.BEATS || { tempo: 120, beats: [], bars: [] };

  // Tiempo del beat i (extrapola con el tempo fuera del rango medido).
  function beatTime(i) {
    const { beats, tempo } = B();
    if (!beats.length) return (i * 60) / tempo;
    if (i < beats.length) return beats[Math.max(0, i)];
    return beats[beats.length - 1] + ((i - beats.length + 1) * 60) / tempo;
  }

  // Índice del último beat en o antes de t (-1 antes del primero).
  function beatAt(t) {
    const { beats, tempo } = B();
    if (!beats.length) return Math.floor((t * tempo) / 60);
    let lo = 0, hi = beats.length - 1, ans = -1;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      if (beats[mid] <= t + 1e-6) { ans = mid; lo = mid + 1; } else hi = mid - 1;
    }
    if (ans === beats.length - 1) {
      ans += Math.floor(((t - beats[ans]) * tempo) / 60);
    }
    return ans;
  }

  // Segundos desde el último beat (útil para golpes que decaen).
  const sinceBeat = (t) => {
    const i = beatAt(t);
    return i < 0 ? Infinity : t - beatTime(i);
  };

  // Golpe que decae: 1 en el beat, ~0 tras `len` segundos.
  const hit = (t, at, len = 0.25) => (t < at ? 0 : Math.exp((-(t - at) * 5) / len));

  window.F = { mulberry32, hash, noise1, clamp, lerp, span, ease, beatTime, beatAt, sinceBeat, hit };
})();
