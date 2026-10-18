// Run with Playwright available on NODE_PATH and the Flask app listening on port 8086.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const base = process.env.WATER_TEST_URL || 'http://127.0.0.1:8086';
(async () => {
  const browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH } : {}) });
  for (const mode of ['flask', 'static']) {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    let forestRequests = 0;
    if (mode === 'static') {
      await page.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (url.pathname === '/static/water.forest') {
          forestRequests += 1;
          if (forestRequests === 1) return route.fulfill({ status: 503, body: 'temporary outage' });
        }
        if (url.pathname === '/health') throw new Error('Static predictions should check their model asset directly.');
        const file = path.join(root, 'dist', url.pathname === '/' ? 'index.html' : url.pathname);
        return route.fulfill({ path: file });
      });
    }
    await page.goto(base);
    if (mode === 'static') await page.locator('#model-status').filter({ hasText: 'unavailable' }).waitFor();
    else await page.locator('#model-status').filter({ hasText: 'Model ready' }).waitFor();
    for (const width of [320, 375, 768, 1024, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${mode} overflow at ${width}`);
    }
    await page.setViewportSize({ width: 375, height: 812 });
    await page.locator('#analyze').click();
    assert.equal(await page.locator('#result-tag').innerText(), 'AWAITING SAMPLE');
    await page.locator('#example').click();
    assert.equal(await page.locator('#ph').inputValue(), '6.7');
    await page.locator('#analyze').click();
    await page.locator('#result-tag').filter({ hasText: 'RESEARCH PREDICTION' }).waitFor();
    assert.equal(await page.locator('#result-title').innerText(), 'Predicted potable');
    assert.equal(await page.locator('#model-status').innerText(), 'Model ready');
    if (mode === 'static') assert.equal(forestRequests, 2, 'failed model downloads must be retryable');
    for (const sample of await page.locator('.sample').all()) {
      await sample.click();
      await page.locator('#analyze:not([disabled])').waitFor();
      assert.equal(await page.locator('#result-title').innerText(), 'Predicted potable');
    }
    await page.locator('#ph').fill('15');
    await page.locator('#analyze').click();
    assert.equal(await page.locator('#result-tag').innerText(), 'AWAITING ASSESSMENT');
    await page.locator('button[type=reset]').click();
    assert.equal(await page.locator('#ph').inputValue(), '');
    assert.equal(await page.locator('#result-tag').innerText(), 'AWAITING SAMPLE');
    if (mode === 'flask') {
      await page.route('**/api/predict', async route => {
        await new Promise(resolve => setTimeout(resolve, 300));
        await route.fulfill({ json: { label: 'STALE RESULT', notice: 'must be ignored' } });
      });
      await page.locator('#example').click();
      await page.locator('#analyze').click();
      await page.locator('button[type=reset]').click();
      await page.locator('#analyze:not([disabled])').waitFor();
      assert.equal(await page.locator('#result-tag').innerText(), 'AWAITING SAMPLE');
      await page.unroute('**/api/predict');
    }
    assert.deepEqual(errors, [], `${mode} JavaScript errors`);
    await page.screenshot({ path: `/private/tmp/water-${mode}-mobile.png`, fullPage: true });
    console.log(`${mode}: validation, presets, predictions, reset, model status and 5 screen widths passed`);
    await page.close();
  }
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });
