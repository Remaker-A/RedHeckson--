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
  const soulResp = await page.request.get(`${BASE}/api/soul`);
  if (!soulResp.ok()) {
    await page.request.post(`${BASE}/api/soul`, {
      data: { current_state_word: '焦虑', struggle: '不知道要不要换方向', bias: 'adventurous' }
    });
  }

  // Home with video
  await page.goto(`${BASE}/home`);
  await page.waitForTimeout(4000); // Let video load and play a bit
  await page.screenshot({ path: `${OUT}/video-01-home.png` });

  await browser.close();
  console.log('✅ Done');
}
run().catch(e => { console.error(e); process.exit(1); });
