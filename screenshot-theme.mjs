import { chromium } from 'playwright';
const BASE = 'http://localhost:3000';
const OUT = '/Users/cheche/workspace/personal/redhackathon/screenshots';

async function run() {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 3,
  });
  const page = await context.newPage();

  // Ensure soul exists
  const sr = await page.request.get(`${BASE}/api/soul`);
  if (!sr.ok()) {
    await page.request.post(`${BASE}/api/soul`, {
      data: { current_state_word: '焦虑', struggle: '不知道要不要换方向', bias: 'adventurous' }
    });
  }

  // Clear last_visit to trigger birth activity
  await page.goto(`${BASE}/home`);
  await page.evaluate(() => localStorage.removeItem('last_visit'));

  // DAY MODE — Home
  await page.goto(`${BASE}/home`);
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${OUT}/theme-day-home.png` });

  // DAY MODE — Notes
  await page.goto(`${BASE}/notes`);
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${OUT}/theme-day-notes.png` });

  // DAY MODE — Me
  await page.goto(`${BASE}/me`);
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${OUT}/theme-day-me.png` });

  // Switch to night mode via store
  await page.evaluate(() => localStorage.setItem('theme_mode', 'night'));

  // NIGHT MODE — Home
  await page.goto(`${BASE}/home`);
  await page.evaluate(() => localStorage.removeItem('last_visit'));
  await page.goto(`${BASE}/home`);
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${OUT}/theme-night-home.png` });

  // NIGHT MODE — Notes
  await page.goto(`${BASE}/notes`);
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${OUT}/theme-night-notes.png` });

  // NIGHT MODE — Me
  await page.goto(`${BASE}/me`);
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${OUT}/theme-night-me.png` });

  // Reset to auto
  await page.evaluate(() => localStorage.setItem('theme_mode', 'auto'));

  await browser.close();
  console.log('✅ Done');
}
run().catch(e => { console.error(e); process.exit(1); });
