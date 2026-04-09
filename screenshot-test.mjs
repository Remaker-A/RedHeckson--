import { chromium } from 'playwright';

const BASE = 'http://localhost:3000';
const OUT = '/Users/cheche/workspace/personal/redhackathon/screenshots';

async function run() {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 }, // iPhone 14 Pro
    deviceScaleFactor: 3,
  });

  // --- 1. Soul Creation (Onboarding) ---
  console.log('📸 Screenshot: Onboarding intro');
  const page1 = await context.newPage();
  await page1.goto(`${BASE}/soul`);
  await page1.waitForTimeout(4500); // Wait for text animations
  await page1.screenshot({ path: `${OUT}/01-onboarding-intro.png`, fullPage: false });

  // Click continue to go to Step 1
  await page1.click('button:has-text("继续")');
  await page1.waitForTimeout(1000);
  await page1.screenshot({ path: `${OUT}/02-onboarding-step1.png`, fullPage: false });

  // Fill step 1 and continue
  await page1.fill('input.soul-input', '焦虑');
  await page1.waitForTimeout(500);
  await page1.screenshot({ path: `${OUT}/03-onboarding-step1-filled.png`, fullPage: false });

  await page1.click('button:has-text("下一步")');
  await page1.waitForTimeout(1000);

  // Step 2
  await page1.fill('textarea.soul-textarea', '不知道要不要换一个方向');
  await page1.waitForTimeout(500);
  await page1.screenshot({ path: `${OUT}/04-onboarding-step2.png`, fullPage: false });

  await page1.click('button:has-text("下一步")');
  await page1.waitForTimeout(1000);

  // Step 3 - select personality
  await page1.screenshot({ path: `${OUT}/05-onboarding-step3.png`, fullPage: false });

  // Select first bias option
  await page1.click('.bias-card:first-child');
  await page1.waitForTimeout(500);
  await page1.screenshot({ path: `${OUT}/06-onboarding-step3-selected.png`, fullPage: false });

  // Complete
  await page1.click('button:has-text("完成")');
  await page1.waitForTimeout(3500);
  await page1.screenshot({ path: `${OUT}/07-onboarding-done.png`, fullPage: false });

  // Enter tent
  await page1.click('button:has-text("走进它的家")');
  await page1.waitForTimeout(2000);

  // --- 2. Home page (Tent scene) ---
  console.log('📸 Screenshot: Home page');
  const page2 = await context.newPage();
  await page2.goto(`${BASE}/home`);
  await page2.waitForTimeout(3000);
  await page2.screenshot({ path: `${OUT}/08-home-scene.png`, fullPage: false });

  // --- 3. Notes page ---
  console.log('📸 Screenshot: Notes page');
  await page2.goto(`${BASE}/notes`);
  await page2.waitForTimeout(2000);
  await page2.screenshot({ path: `${OUT}/09-notes-page.png`, fullPage: false });

  // --- 4. Me page ---
  console.log('📸 Screenshot: Me page');
  await page2.goto(`${BASE}/me`);
  await page2.waitForTimeout(2000);
  await page2.screenshot({ path: `${OUT}/10-me-page.png`, fullPage: false });

  // --- 5. Me page scroll ---
  await page2.evaluate(() => window.scrollTo(0, 400));
  await page2.waitForTimeout(500);
  await page2.screenshot({ path: `${OUT}/11-me-page-scroll.png`, fullPage: false });

  await browser.close();
  console.log(`✅ All screenshots saved to ${OUT}/`);
}

run().catch(e => { console.error(e); process.exit(1); });
