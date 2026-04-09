import { chromium } from 'playwright';

const BASE = 'http://localhost:3000';
const OUT = '/Users/cheche/workspace/personal/redhackathon/screenshots';

async function run() {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 3,
  });

  // Create soul first if needed
  const page = await context.newPage();

  // Check if soul exists
  const soulResp = await page.request.get(`${BASE}/api/soul`);
  if (!soulResp.ok()) {
    // Create soul
    await page.request.post(`${BASE}/api/soul`, {
      data: { current_state_word: '焦虑', struggle: '不知道要不要换方向', bias: 'adventurous' }
    });
  }

  // Generate a note if none exist
  const notesResp = await page.request.get(`${BASE}/api/notes`);
  const notes = await notesResp.json();
  if (notes.length === 0) {
    await page.request.post(`${BASE}/api/notes/generate`);
  }

  // 1. Home page
  console.log('📸 Home page');
  await page.goto(`${BASE}/home`);
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${OUT}/fix-01-home.png` });

  // 2. Notes page with notes
  console.log('📸 Notes page');
  await page.goto(`${BASE}/notes`);
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${OUT}/fix-02-notes.png` });

  // 3. Write a note
  console.log('📸 Write note');
  await page.click('button:has-text("贴一张便签")');
  await page.waitForTimeout(800);
  await page.fill('.note-textarea', '今天做了一个很难的决定');
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT}/fix-03-write-note.png` });

  // Submit
  await page.click('button:has-text("贴上去")');
  await page.waitForTimeout(2000);
  // After sent feedback auto-closes, check notes list
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${OUT}/fix-04-notes-with-user.png` });

  // 4. Me page
  console.log('📸 Me page');
  await page.goto(`${BASE}/me`);
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${OUT}/fix-05-me.png` });

  await browser.close();
  console.log('✅ Done');
}

run().catch(e => { console.error(e); process.exit(1); });
