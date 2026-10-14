# Motion Studio

Espacio de trabajo para animaciones renderizadas con un navegador headless (Playwright + ffmpeg).

```bash
cd motion-studio
npm install
npx playwright install chromium   # en tu compu; en la nube se usa CHROMIUM_PATH
```

Las reglas de trabajo están en [`CLAUDE.md`](CLAUDE.md). Flujo de un film nuevo:

```bash
cp -r films/_template films/mi-film
npm run sound -- films/mi-film          # score sintetizado -> beats.json -> audio.wav
node render.mjs films/mi-film --check   # contrato + determinismo
node render.mjs films/mi-film --sheet   # hoja de contactos (un frame por beat)
node render.mjs films/mi-film           # out/mi-film.mp4 (H.264 CRF 16, -14 LUFS)
```

`lib/browser.js` abre Chromium: si `CHROMIUM_PATH` está definido usa ese ejecutable,
si no, el que descargó Playwright.

Análisis de audio (beats, tempo) con Python: `pip install numpy librosa soundfile`.

Skills disponibles en el proyecto (`.claude/skills/`): `remotion-*` y `hyperframes-*`.
Plugin de animación hecha a mano: `claude-animation@claude-animation-skill` (declarado en `.claude/settings.json`).
