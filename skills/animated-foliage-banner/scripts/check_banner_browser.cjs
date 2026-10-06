const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const { setTime } = require('./render_svg.cjs');

// Check the documented scene contract. Requires Playwright and installed Chrome.
(async () => {
  assert(process.argv.length === 4 || (process.argv.length === 5 && process.argv[4] === '--self-test'),
    'Usage: node check_banner_browser.cjs input.svg output-dir [--self-test]');
  const svg = fs.readFileSync(path.resolve(process.argv[2]));
  const out = path.resolve(process.argv[3]);
  fs.mkdirSync(out, { recursive: true });
  const probe = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><style>rect{fill:red}@media(prefers-reduced-motion:reduce){rect{fill:blue}}</style><rect width="10" height="10"/></svg>';
  const html = '<!doctype html><meta charset="utf-8"><style>html,body{margin:0}img{display:block;width:100%;height:auto}</style><img id="banner" alt="Animated foliage banner" src="/hero.svg">';
  const server = http.createServer((req, res) => {
    res.setHeader('Content-Type', req.url.endsWith('.svg') ? 'image/svg+xml' : 'text/html');
    res.end(req.url === '/hero.svg' ? svg : req.url === '/probe.svg' ? probe : html);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    const origin = `http://127.0.0.1:${server.address().port}`;
    const report = { sha256: createHash('sha256').update(svg).digest('hex'), image: [], inline: {} };
    for (const motion of ['no-preference', 'reduce']) {
      browser = await chromium.launch({ channel: 'chrome', headless: true, args: motion === 'reduce' ? ['--force-prefers-reduced-motion'] : [] });
      report.browser = browser.version();
      for (const width of [1024, 375]) {
        const context = await browser.newContext({ viewport: { width, height: 700 }, deviceScaleFactor: 1, reducedMotion: motion });
        await context.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
        const page = await context.newPage();
        await page.goto(origin);
        await page.emulateMedia({ reducedMotion: motion });
        assert.equal(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches), motion === 'reduce', 'Media emulation was not applied');
        const probeColor = await page.evaluate(async () => {
          const img = new Image(); img.src = '/probe.svg'; await img.decode();
          const canvas = document.createElement('canvas'); canvas.width = canvas.height = 10;
          const ctx = canvas.getContext('2d'); ctx.drawImage(img, 0, 0);
          return [...ctx.getImageData(5, 5, 1, 1).data];
        });
        assert.deepEqual(probeColor, motion === 'reduce' ? [0, 0, 255, 255] : [255, 0, 0, 255], 'Image-mode media control failed');
        await page.locator('#banner').evaluate(img => img.decode());
        const name = `${width}-${motion}`;
        await page.waitForTimeout(300);
        const first = await page.locator('#banner').screenshot({ path: path.join(out, `${name}-a.png`), animations: 'allow' });
        await page.waitForTimeout(1100);
        const second = await page.locator('#banner').screenshot({ path: path.join(out, `${name}-b.png`), animations: 'allow' });
        const equal = first.equals(second);
        assert.equal(equal, motion === 'reduce', `${name}: unexpected image motion`);
        const dimensions = await page.locator('#banner').evaluate(img => [img.naturalWidth, img.naturalHeight]);
        assert(dimensions.every(value => value > 0), 'Image has no intrinsic dimensions');
        report.image.push({ width, motion, equal, dimensions, probeColor, waitBetweenCapturesMs: 1100 });
        await context.close();
      }
      await browser.close();
    }
    browser = await chromium.launch({ channel: 'chrome', headless: true });
    const context = await browser.newContext({ viewport: { width: 1024, height: 700 }, deviceScaleFactor: 1, reducedMotion: 'no-preference' });
    await context.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
    const page = await context.newPage();
    await page.goto(origin + '/hero.svg');
    const sites = await page.evaluate(() => {
      const parents = [...new Set([...document.querySelectorAll('use.motion-contour, use.still-contour')].map(e => e.parentElement))];
      return parents.map((parent, i) => {
        parent.setAttribute('data-contour-check', String(i));
        return `[data-contour-check="${i}"]`;
      });
    });
    assert(sites.length > 0, 'No animated/static contour pairs');
    const period = await page.locator('#fur-outline > animate').evaluate(e => e.getSimpleDuration());
    assert(Number.isFinite(period) && period > 0, 'Contour needs a finite positive period');
    const checkSelection = async reducedMotion => {
      const selections = await page.evaluate(sites => {
        const snapshot = element => {
          const style = getComputedStyle(element);
          return { href: element.getAttribute('href'), display: style.display, visibility: style.visibility, opacity: Number(style.opacity) };
        };
        return sites.map(site => ({
          site,
          dynamic: [...document.querySelectorAll(`${site} > use.motion-contour`)].map(snapshot),
          still: [...document.querySelectorAll(`${site} > use.still-contour`)].map(snapshot)
        }));
      }, sites);
      for (const { site, dynamic, still } of selections) {
        const message = `${reducedMotion ? 'Reduced' : 'Normal'} visible fur selection at ${site}`;
        assert.equal(dynamic.length, 1, message);
        assert.equal(still.length, 1, message);
        assert.equal(dynamic[0].href, '#fur-outline', message);
        assert.equal(still[0].href, '#fur-still', message);
        const active = reducedMotion ? still[0] : dynamic[0];
        const inactive = reducedMotion ? dynamic[0] : still[0];
        assert(active.display !== 'none' && active.visibility === 'visible' && active.opacity > 0, message);
        assert.equal(inactive.display, 'none', message);
      }
      return selections;
    };
    const normalSelection = await checkSelection(false);
    const rejectedMutations = [];
    if (process.argv[4] === '--self-test') {
      for (const targets of [sites, ...sites.map(site => [site])]) {
        const style = await page.evaluateHandle(targets => {
          const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
          style.textContent = targets.map(site => `${site} > .motion-contour { display: none !important; } ${site} > .still-contour { display: inline !important; }`).join('\n');
          document.documentElement.append(style);
          return style;
        }, targets);
        try {
          await assert.rejects(() => checkSelection(false), /Normal visible fur selection/);
          rejectedMutations.push(targets);
        } finally {
          await style.evaluate(element => element.remove());
          await style.dispose();
        }
        await checkSelection(false);
      }
    }
    const sample = () => page.evaluate(() => ({
      roots: [...document.querySelectorAll('.leaf')].map(e => {
        const m = e.getCTM(); return [m.a,m.b,m.c,m.d,m.e,m.f];
      }),
      active: document.getAnimations().length,
      time: performance.now(),
      svgTime: document.documentElement.getCurrentTime()
    }));
    const a = await sample();
    await page.waitForTimeout(700);
    const b = await sample();
    await page.waitForTimeout(1100);
    const c = await sample();
    const movement = (first, second) => first.roots.map((m,i) => Math.hypot(100*(m[0]-second.roots[i][0]),100*(m[1]-second.roots[i][1])));
    const ab = movement(a,b), ac = movement(a,c);
    const motionSamples = {a,b,c,unchangedAB:ab.flatMap((v,i)=>v <= 1e-5 ? [i] : []),unchangedAC:ac.flatMap((v,i)=>v <= 1e-5 ? [i] : [])};
    fs.writeFileSync(path.join(out, 'motion-samples.json'), JSON.stringify(motionSamples));
    assert(a.roots.length > 0, 'No leaves to check');
    assert.equal(a.active, 2 * a.roots.length, 'Expected one branch and one leaf animation per leaf');
    assert([b,c].every(s => a.roots.every((m,i) => Math.abs(m[4]-s.roots[i][4]) < 1e-6 && Math.abs(m[5]-s.roots[i][5]) < 1e-6)), 'Leaf roots moved');
    assert(ab.every((v,i) => Math.max(v,ac[i]) > 1e-5), 'A non-root leaf point did not move across three samples');
    // Freeze CSS foliage so hidden SMIL geometry alone cannot satisfy the painted-fur check.
    await page.evaluate(() => {
      document.documentElement.style.cssText = 'width:100vw;height:auto';
    });
    const furFrames = [];
    for (const time of [0, period / 4, period / 2]) {
      await setTime(page, time, 0);
      const frame = await page.locator('svg').screenshot({ path: path.join(out, `fur-${time}.png`), animations: 'allow' });
      furFrames.push({ time, sha256: createHash('sha256').update(frame).digest('hex') });
    }
    assert(new Set(furFrames.map(frame => frame.sha256)).size > 1, 'Visible fur is static with CSS foliage frozen');
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const reducedSelection = await checkSelection(true);
    const reduced = await page.evaluate(() => ({
      cssAnimations: document.getAnimations().length,
      staticChildren: document.querySelector('#fur-still').children.length
    }));
    assert.equal(reduced.cssAnimations, 0);
    assert.equal(reduced.staticChildren, 0);
    report.inline = { fixedRoots: a.roots.length, swayingLeaves: a.roots.length, furMoved: true, period,
      normalSelection, reducedSelection, furFrames, rejectedMutations,
      sampleTimes: [a.time,b.time,c.time], unchangedFirstPair: motionSamples.unchangedAB,
      minNonRootMovement: Math.min(...ab.map((v,i) => Math.max(v,ac[i]))), reduced };
    fs.writeFileSync(path.join(out, 'browser-results.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
    await context.close();
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
