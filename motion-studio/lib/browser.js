// Abre Chromium headless. Si CHROMIUM_PATH está definido (ej. en la nube),
// usa ese ejecutable; si no, usa el que instaló `npx playwright install chromium`.
const { chromium } = require("playwright");

function launch(options = {}) {
  const executablePath = process.env.CHROMIUM_PATH || undefined;
  return chromium.launch({ executablePath, ...options });
}

module.exports = { launch };
