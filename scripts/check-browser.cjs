/* Optional development check: npm install --no-save --package-lock=false playwright
   Then: node scripts/check-browser.cjs. No dependency is used by the website.
   Pages are served over HTTP (built-in server below) because the language links
   point at folders ("nl/", "../"), which only resolve to index.html on a web server. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const screenshotDirectory = path.join(root, 'screenshots');
fs.mkdirSync(screenshotDirectory, { recursive: true });

const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.png': 'image/png' };
function serve() {
  const server = http.createServer((request, response) => {
    let file = path.join(root, decodeURIComponent(new URL(request.url, 'http://x').pathname));
    if (!file.startsWith(root)) { response.writeHead(403).end(); return; }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    if (!fs.existsSync(file)) { response.writeHead(404).end(); return; }
    response.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(response);
  });
  return new Promise(resolve => server.listen(0, '127.0.0.1', () => resolve(server)));
}

const NB = ' ';
const LANGUAGES = {
  en: {
    path: '/', other: 'nl', otherPath: '/nl/',
    prices: ['$219', '$729', '$1,109', '$2,029'],
    industry: 'Hotels & resorts', previewChecks: [/form is complete/, /no booking has been sent/],
  },
  nl: {
    path: '/nl/', other: 'en', otherPath: '/',
    prices: [`$${NB}219`, `$${NB}729`, `$${NB}1.109`, `$${NB}2.029`],
    industry: 'Hotels en resorts', previewChecks: [/volledig ingevuld/, /geen afspraak verstuurd/],
  },
};
// Phrases that would betray untranslated copy on the Dutch page (visible text, labels, JS messages).
const ENGLISH = /\b(the|and|your|you|with|for|our|please|enter|book|free|per user|month|night watch|always|monitoring, nights|services|packages|how it works|who we help|about|contact us|open menu|close menu|choose|thank)\b/i;
const NL_ALLOWED = /^(Acseda( One| Essentials| Aware| Browse| Desk| Scan)?|Essentials|One|Secure Check|Managed SOC|Agent|Inbox|Web|Servers|Resort|Contact|EN|NL|EN, English|ACSEDA|CYBERSECURITY|ACSEDA DESK|COMPLIANCE|Week .*|Privacy · Voorwaarden · Responsible disclosure|© 2026 Acseda Cybersecurity)$/;

(async () => {
  const server = await serve();
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.BROWSER_EXECUTABLE ? { executablePath: process.env.BROWSER_EXECUTABLE } : {}),
  });
  const errors = [];
  try {
    for (const [lang, config] of Object.entries(LANGUAGES)) {
      const url = base + config.path;
      const page = await browser.newPage({ reducedMotion: 'reduce' });
      page.on('pageerror', error => errors.push(`${lang}: ${error.message}`));
      async function settleImages() {
        await page.evaluate(async () => {
          await document.fonts.ready;
          // Instant jumps: with motion allowed, the page's smooth scrolling would otherwise skip sections.
          for (let y = 0; y < document.body.scrollHeight; y += innerHeight * .8) {
            scrollTo({ top: y, behavior: 'instant' });
            await new Promise(resolve => setTimeout(resolve, 40));
          }
          await Promise.all([...document.images].map(img => img.decode().catch(() => {})));
          scrollTo({ top: 0, behavior: 'instant' });
        });
      }
      for (const width of [1440, 1250, 1100, 1024, 768, 390]) {
        await page.setViewportSize({ width, height: 1000 });
        await page.goto(url);
        await settleImages();
        assert.equal(await page.evaluate(() => document.documentElement.lang), lang);
        assert.equal(await page.locator('h1').count(), 1);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `${lang} ${width}px horizontal overflow`);
        assert.equal(await page.locator('img').evaluateAll(imgs => imgs.every(img => img.naturalWidth > 0)), true, 'Broken photo');
        assert.equal(await page.evaluate(() => document.documentElement.classList.contains('motion')), false, 'Reduced motion preference ignored');
        // Longer Dutch words must not spill out of buttons, chips, tabs, nav or the language switch.
        const spills = await page.evaluate(() => [...document.querySelectorAll('.button, .chip, .badge, .package-tabs button, .nav-links a, .languages a, .nav-wrap, .cost, .quote-total, h1, h2, h3, h4')]
          .filter(el => el.offsetParent && el.scrollWidth > el.clientWidth + 1)
          .map(el => `${el.className || el.tagName}: ${el.textContent.trim().slice(0, 40)}`));
        assert.deepEqual(spills, [], `${lang} ${width}px text overflow`);
        if (width > 980) {
          // Desktop: the switch sits in the header, on one row with the call to action.
          const header = await page.locator('.site-header').boundingBox();
          assert.ok(header.height < 100, `${lang} ${width}px header wraps (${header.height}px)`);
          assert.equal(await page.locator('.languages').isVisible(), true, `${lang} ${width}px language switch hidden`);
        }
        await page.screenshot({ path: path.join(screenshotDirectory, `${lang}-${width}.png`), fullPage: true });
        console.log(`PASS ${lang}: ${width}px, no horizontal overflow or text spill, photos, reduced motion; screenshot saved`);
      }

      if (lang === 'nl') {
        const leftovers = await page.evaluate(() => {
          const out = [];
          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          while (walker.nextNode()) {
            const node = walker.currentNode;
            if (node.parentElement.closest('svg, script, noscript, [lang="en"]')) continue;
            const text = node.textContent.replace(/\s+/g, ' ').trim();
            if (text) out.push(text);
          }
          document.querySelectorAll('[alt], [aria-label], [placeholder], [title]').forEach(el => {
            if (el.closest('[lang="en"]')) return;
            ['alt', 'aria-label', 'placeholder', 'title'].forEach(name => el.hasAttribute(name) && out.push(el.getAttribute(name)));
          });
          document.querySelectorAll('meta[content]').forEach(el => out.push(el.content));
          out.push(document.title);
          return out;
        });
        const english = leftovers.filter(text => !/^(width=|#|\.\.\/|nl_NL|en_US|website)/.test(text) && !NL_ALLOWED.test(text) && ENGLISH.test(text));
        assert.deepEqual(english, [], 'English text on the Dutch page');
        console.log(`PASS nl: ${leftovers.length} text nodes, labels and meta values checked, no English left`);
      }

      // Language switch, desktop: the other language is a link; the current one is marked.
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.goto(url);
      assert.equal(await page.locator(`.languages a[hreflang="${lang}"]`).getAttribute('aria-current'), 'true');
      assert.equal(await page.locator(`.languages a[hreflang="${config.other}"]`).getAttribute('aria-current'), null);
      await page.locator(`.languages a[hreflang="${config.other}"]`).click();
      await page.waitForURL(base + config.otherPath);
      assert.equal(await page.evaluate(() => document.documentElement.lang), config.other);
      await page.goBack();
      // Mobile: the switch is reachable inside the menu.
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto(url);
      await page.locator('.menu-toggle').click();
      assert.equal(await page.locator('.languages').isVisible(), true);
      const linkBox = await page.locator(`.languages a[hreflang="${config.other}"]`).boundingBox();
      assert.ok(linkBox.width >= 44 && linkBox.height >= 44, 'Language link touch target below 44px');
      await page.locator(`.languages a[hreflang="${config.other}"]`).click();
      await page.waitForURL(base + config.otherPath);
      assert.equal(await page.evaluate(() => document.documentElement.lang), config.other);
      console.log(`PASS ${lang}: language switch to ${config.other} on desktop and in the mobile menu`);

      await page.setViewportSize({ width: 390, height: 1000 });
      await page.goto(url);
      const toggle = page.locator('.menu-toggle');
      const closedLabel = await toggle.getAttribute('aria-label');
      await toggle.click();
      assert.equal(await toggle.getAttribute('aria-expanded'), 'true');
      assert.notEqual(await toggle.getAttribute('aria-label'), closedLabel);
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
      console.log(`PASS ${lang}: menu focus trap, Escape, link close and active-section navigation`);

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
      await checkPrice('essentials', 8, 0, config.prices[0]);
      assert.equal(await page.locator('#calc-servers').isDisabled(), true);
      await checkPrice('one', 10, 1, config.prices[1]);
      await checkPrice('one', 20, 2, config.prices[2]);
      await checkPrice('one', 45, 4, config.prices[3]);
      await page.locator('#calc-users').fill('-1');
      assert.equal(await page.locator('#calc-total').textContent(), '—');
      await checkPrice('essentials', 8, 0, config.prices[0]);
      // Park the pointer on the sticky header: otherwise focus() scrolls a diagram layer under it,
      // and that layer's mouseenter (correctly) takes over the highlight.
      await page.mouse.move(5, 5);
      await page.locator('.legend-row[data-layer="desk"]').focus();
      assert.equal(await page.locator('.stack-desk').evaluate(el => el.classList.contains('layer-highlight')), true);
      await page.locator('.stack-pill[data-layer="aware"]').focus();
      assert.equal(await page.locator('.legend-row[data-layer="aware"]').evaluate(el => el.classList.contains('layer-highlight')), true);
      console.log(`PASS ${lang}: package switching, all four quote calculations (${config.prices.join(', ')}), invalid quantities, layer highlighting`);

      const messages = [];
      const collect = async () => messages.push(...(await page.locator('.field-error, #form-status').allTextContents()).filter(Boolean));
      await page.locator('#secure-check button').click();
      assert.equal(await page.locator('#secure-check [aria-invalid="true"]').count(), 6);
      assert.equal(await page.locator('#contact-name').evaluate(el => el === document.activeElement), true);
      await collect();
      await page.locator('#contact-name').fill('Test Person');
      await page.locator('#contact-company').fill('Test Company');
      await page.locator('#contact-email').fill('invalid');
      await page.locator('#contact-phone').fill('invalid');
      await page.locator('#contact-users').fill('1.5');
      await page.locator('#contact-industry').selectOption({ label: config.industry });
      await page.locator('#secure-check button').click();
      assert.equal(await page.locator('#secure-check [aria-invalid="true"]').count(), 3);
      await collect();
      await page.locator('#contact-users').fill('10');
      await page.locator('#contact-email').fill('test@example.com');
      await page.locator('#contact-phone').fill('+297 123 4567');
      const submissions = [];
      page.on('request', request => { if (request.method() === 'POST') submissions.push(request.url()); });
      await page.locator('#secure-check button').click();
      for (const pattern of config.previewChecks) assert.match(await page.locator('#form-status').textContent(), pattern);
      await collect();
      assert.deepEqual(submissions, []);
      if (lang === 'nl') {
        const english = messages.filter(text => ENGLISH.test(text.replace(/hello@acsedasec\.com|naam@bedrijf\.com/g, '')));
        assert.deepEqual(english, [], 'English validation or status message on the Dutch page');
      }
      console.log(`PASS ${lang}: required fields, email/phone/users errors, preview success, no form transmission; ${messages.length} messages checked`);

      await page.emulateMedia({ reducedMotion: 'no-preference' });
      await page.goto(url);
      await page.waitForTimeout(2700);
      assert.equal(await page.locator('.event-shown').count() > 0, true);
      await settleImages();
      await page.waitForTimeout(1300);
      assert.equal(await page.locator('.reveal:not(.is-visible)').count(), 0);
      if (lang === 'nl') {
        const counted = await page.locator('[data-count="1109"], [data-count="2029"]').allTextContents();
        assert.deepEqual(counted, ['1.109', '2.029'], 'Dutch thousands separator after count-up');
      }
      await page.locator('#services').scrollIntoViewIfNeeded();
      await page.locator('.service-card').first().hover();
      await page.waitForTimeout(400);
      assert.notEqual(await page.locator('.service-card').first().evaluate(el => getComputedStyle(el).transform), 'none');
      await page.emulateMedia({ reducedMotion: 'reduce' });
      assert.equal(await page.locator('.event-pending').count(), 0);
      assert.equal(await page.locator('html').evaluate(el => el.classList.contains('motion')), false);
      console.log(`PASS ${lang}: timeline sequence, scroll reveals, count-ups, hover lift, live reduced-motion changes`);
      await page.close();

      const noJS = await browser.newPage({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
      await noJS.goto(url);
      assert.equal(await noJS.locator('#package-essentials').isVisible(), true);
      assert.equal(await noJS.locator('#package-one').isVisible(), true);
      assert.equal(await noJS.locator('#navigation').isVisible(), true);
      assert.equal(await noJS.locator('.languages').isVisible(), true);
      assert.equal(await noJS.locator('#secure-check button').isDisabled(), true);
      assert.equal(await noJS.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await noJS.close();
      console.log(`PASS ${lang}: no-JS content, navigation and language switch fallback`);
    }
    assert.deepEqual(errors, []);
    console.log('PASS: no JavaScript runtime errors on either page');
  } finally { await browser.close(); server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
