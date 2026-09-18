import { chromium } from 'playwright';
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
await page.goto('http://localhost:5183', { waitUntil: 'networkidle' });
await page.locator('#servicios').scrollIntoViewIfNeeded();
await page.waitForTimeout(700);
await page.screenshot({ path: '/tmp/services.png' });
await browser.close();

const page2 = await (await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' })).newPage({ viewport: { width: 375, height: 800 } });
await page2.goto('http://localhost:5183', { waitUntil: 'networkidle' });
await page2.waitForTimeout(600);
await page2.screenshot({ path: '/tmp/mobile.png', fullPage: true });
