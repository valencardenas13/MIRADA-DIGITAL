# Motion studio rules

## Render contract
- Every film is a pure function of time: `window.seek(t)` paints frame t.
- No CSS transitions, no setTimeout, no requestAnimationFrame in render mode,
  no state carried between frames. Seeded noise only (mulberry32), never Math.random.
- Render with `node render.mjs`, encode H.264 yuv420p, CRF 16.

## Look
- Banned defaults: centered title on gradient, everything fading in,
  corner labels and frame borders, glow on UI chrome, generic particle bursts.
- One display face, one UI face. One accent color unless the brief says otherwise.
- Every 2 to 4 seconds something new must happen on screen.

## Sound
- Score and SFX are synthesized in code unless a track is supplied.
- Place hits on the measured beat grid (beats.json). Loudness -14 LUFS.

## Loop before you show me anything
1. Render one frame per beat as a contact sheet and LOOK at it.
2. Score it 1-10 on: hook in first 2s, readability at phone size,
   motion quality, variety, brand accuracy, sound sync.
3. Fix the 3 worst problems. Repeat until every score is 8+.
4. Only then do the full render.

---

## How the tooling enforces this

Layout: each film lives in `films/<name>/` (copy `films/_template/`).

| File | Role |
| --- | --- |
| `index.html` | The film. Sets `window.FILM = {fps, duration, width, height}` and `window.seek(t)`. |
| `sound.py` | Synthesized score (`score`) and SFX on the measured grid (`mix`). Uses `lib/dsp.py`. |
| `beats.json` / `beats.js` | Measured by `tools/beats.py` from `score.wav`. `beats.js` sets `window.BEATS`. |
| `audio.wav` | Final mix (score + SFX), loudness-normalized at mux time. |

Commands (from `motion-studio/`):

```bash
npm run sound -- films/<name>          # score.wav -> beats.json -> audio.wav
node render.mjs films/<name> --check   # lint + determinism check (seek out of order, compare)
node render.mjs films/<name> --sheet   # contact sheet, one frame per beat -> out/<name>-sheet.png
node render.mjs films/<name> --frame 3.2   # single frame -> out/<name>-3.20.png
node render.mjs films/<name>           # full render -> out/<name>.mp4 (H.264 yuv420p CRF 16, audio at -14 LUFS)
```

- `render.mjs` refuses to render if film code uses `Math.random`, `setTimeout`,
  `setInterval`, `requestAnimationFrame`, or CSS `transition`/`animation`.
- Shared helpers in `lib/film.js`: `mulberry32`, easings, `span(t, a, b)`, beat helpers
  (`beatAt`, `sinceBeat`, `beatTime`). Preview playback lives in `lib/preview.js` (inactive in render mode).
- Brand: Azul Noche `#0D1B2A` background, Eléctrico `#00D4FF` as the single accent,
  white text, `#8892A4` support grey. Display face: Space Grotesk. UI face: Inter.
  Fonts are local in `assets/fonts/` so renders don't depend on the network.
- In the cloud container set `CHROMIUM_PATH` to the preinstalled Chromium
  (`/opt/pw-browsers/chromium-*/chrome-linux/chrome`); locally use `npx playwright install chromium`.
- Sheet scoring goes in `films/<name>/NOTES.md`: one table per iteration with the six scores
  and the three fixes made.
