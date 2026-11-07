/* Optional development check: npm install --no-save --package-lock=false playwright
   Then: node scripts/check-browser.cjs. No dependency is used by the website. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const url = pathToFileURL(path.join(root, 'index.html')).href;
const screenshotDirectory = path.join(root, 'screenshots');
fs.mkdirSync(screenshotDirectory, { recursive: true });

(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.BROWSER_EXECUTABLE ? { executablePath: process.env.BROWSER_EXECUTABLE } : {}),
  });
  const errors = [];
  const page = await browser.newPage({ reducedMotion: 'reduce' });
  page.on('pageerror', error => errors.push(error.message));
  async function settleImages() {
    await page.evaluate(async () => {
      await document.fonts.ready;
      for (let y = 0; y < document.body.scrollHeight; y += innerHeight * .8) {
        scrollTo(0, y);
        await new Promise(resolve => setTimeout(resolve, 40));
      }
      await Promise.all([...document.images].map(img => img.decode().catch(() => {})));
      scrollTo(0, 0);
    });
  }
  try {
    for (const width of [1440, 1024, 768, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(url);
      await settleImages();
      assert.equal(await page.locator('h1').count(), 1);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `${width}px horizontal overflow`);
      assert.equal(await page.locator('img').evaluateAll(imgs => imgs.every(img => img.naturalWidth > 0)), true, 'Broken photo');
      assert.equal(await page.evaluate(() => document.documentElement.classList.contains('motion')), false, 'Reduced motion preference ignored');
      await page.screenshot({ path: path.join(screenshotDirectory, `${width === 390 ? 'mobile' : 'desktop'}-${width}.png`), fullPage: true });
      console.log(`PASS: ${width}px, local-file rendering, no horizontal overflow, photos, reduced motion; screenshot saved`);
    }
    const toggle = page.locator('.menu-toggle');
    await toggle.click();
    assert.equal(await toggle.getAttribute('aria-expanded'), 'true');
    assert.equal(await page.locator('main').evaluate(el => el.inert), true);
    await toggle.focus();
    await page.keyboard.press('Shift+Tab');
    assert.equal(await page.locator('.nav-actions .button').evaluate(el => el === document.activeElement), true);
    await page.keyboard.press('Tab');
    assert.equal(await toggle.evaluate(el => el === document.activeElement), true);
    await page.keyboard.press('Escape');
    assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
    await toggle.click();
    await page.locator('.nav-links a[href="#services"]').click();
    assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
    await page.waitForFunction(() => document.querySelector('.nav-links a[href="#services"]').getAttribute('aria-current') === 'location');
    console.log('PASS: menu focus trap, Escape, link close and active-section navigation');

    await page.locator('.package-tabs [data-package="one"]').click();
    assert.equal(await page.locator('#package-one').isVisible(), true);
    assert.equal(await page.locator('#package-essentials').isVisible(), false);
    await page.setViewportSize({ width: 1440, height: 1000 });
    assert.equal(await page.locator('#package-essentials').isVisible(), true);
    const checkPrice = async (pkg, users, servers, expected) => {
      await page.locator('#calc-package').selectOption(pkg);
      await page.locator('#calc-users').fill(String(users));
      if (pkg === 'one') await page.locator('#calc-servers').fill(String(servers));
      assert.equal(await page.locator('#calc-total').textContent(), expected);
    };
    await checkPrice('essentials', 8, 0, '$219');
    assert.equal(await page.locator('#calc-servers').isDisabled(), true);
    await checkPrice('one', 10, 1, '$679');
    await checkPrice('one', 20, 2, '$1,059');
    await checkPrice('one', 45, 4, '$1,979');
    await page.locator('#calc-users').fill('-1');
    assert.equal(await page.locator('#calc-total').textContent(), '—');
    await checkPrice('essentials', 8, 0, '$219');
    await page.locator('.legend-row[data-layer="desk"]').focus();
    assert.equal(await page.locator('.stack-desk').evaluate(el => el.classList.contains('layer-highlight')), true);
    await page.locator('.stack-pill[data-layer="aware"]').focus();
    assert.equal(await page.locator('.legend-row[data-layer="aware"]').evaluate(el => el.classList.contains('layer-highlight')), true);
    console.log('PASS: package switching, all four quote calculations, invalid quantities, two-way keyboard layer highlighting');

    await page.locator('#secure-check button').click();
    assert.equal(await page.locator('#secure-check [aria-invalid="true"]').count(), 6);
    assert.equal(await page.locator('#contact-name').evaluate(el => el === document.activeElement), true);
    await page.locator('#contact-name').fill('Test Person');
    await page.locator('#contact-company').fill('Test Company');
    await page.locator('#contact-email').fill('invalid');
    await page.locator('#contact-phone').fill('invalid');
    await page.locator('#contact-users').fill('10');
    await page.locator('#contact-industry').selectOption({ label: 'Hotels & resorts' });
    await page.locator('#secure-check button').click();
    assert.equal(await page.locator('#secure-check [aria-invalid="true"]').count(), 2);
    await page.locator('#contact-email').fill('test@example.com');
    await page.locator('#contact-phone').fill('+297 123 4567');
    const submissions = [];
    page.on('request', request => { if (request.method() === 'POST') submissions.push(request.url()); });
    await page.locator('#secure-check button').click();
    assert.match(await page.locator('#form-status').textContent(), /form is complete/);
    assert.match(await page.locator('#form-status').textContent(), /no booking has been sent/);
    assert.deepEqual(submissions, []);
    console.log('PASS: required fields, email and phone errors, preview success, no form transmission');

    await page.emulateMedia({ reducedMotion: 'no-preference' });
    await page.goto(url);
    await page.waitForTimeout(2700);
    assert.equal(await page.locator('.event-shown').count() > 0, true);
    await settleImages();
    await page.waitForTimeout(1300);
    assert.equal(await page.locator('.reveal:not(.is-visible)').count(), 0);
    await page.locator('#services').scrollIntoViewIfNeeded();
    await page.locator('.service-card').first().hover();
    await page.waitForTimeout(400);
    assert.notEqual(await page.locator('.service-card').first().evaluate(el => getComputedStyle(el).transform), 'none');
    await page.emulateMedia({ reducedMotion: 'reduce' });
    assert.equal(await page.locator('.event-pending').count(), 0);
    assert.equal(await page.locator('html').evaluate(el => el.classList.contains('motion')), false);
    console.log('PASS: timeline sequence, scroll reveals, hover lift, live reduced-motion changes');

    const noJS = await browser.newPage({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
    await noJS.goto(url);
    assert.equal(await noJS.locator('#package-essentials').isVisible(), true);
    assert.equal(await noJS.locator('#package-one').isVisible(), true);
    assert.equal(await noJS.locator('#navigation').isVisible(), true);
    assert.equal(await noJS.locator('#secure-check button').isDisabled(), true);
    assert.equal(await noJS.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await noJS.close();
    assert.deepEqual(errors, []);
    console.log('PASS: no-JS content/navigation fallback; no JavaScript runtime errors');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
