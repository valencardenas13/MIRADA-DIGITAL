# Motion Studio

Espacio de trabajo para animaciones renderizadas con un navegador headless (Playwright + ffmpeg).

```bash
cd motion-studio
npm install
npx playwright install chromium   # en tu compu; en la nube se usa CHROMIUM_PATH
```

`lib/browser.js` abre Chromium: si `CHROMIUM_PATH` está definido usa ese ejecutable,
si no, el que descargó Playwright.

Análisis de audio (beats, tempo) con Python: `pip install numpy librosa soundfile`.

Skills disponibles en el proyecto (`.claude/skills/`): `remotion-*` y `hyperframes-*`.
Plugin de animación hecha a mano: `claude-animation@claude-animation-skill` (declarado en `.claude/settings.json`).
