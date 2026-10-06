// Fixed-time diagnostics for self-contained SVGs. Node.js 20+, Playwright, Chrome.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const { parseArgs } = require('node:util');

// Shared with the scene playback check; keep CSS and SMIL clocks explicit.
async function setTime(page, svgTime, cssTime = 0) {
  await page.evaluate(({ svgTime, cssTime }) => {
    const root = document.documentElement;
    root.pauseAnimations();
    root.setCurrentTime(svgTime);
    for (const animation of document.getAnimations()) {
      animation.pause();
      animation.currentTime = cssTime * 1000;
    }
  }, { svgTime, cssTime });
}

async function render(input, output, options = {}) {
  const { chromium } = require('playwright');
  const svg = fs.readFileSync(input);
  const time = options.time ?? 0, cssTime = options.cssTime ?? time, scale = options.scale ?? 1;
  for (const value of [time, cssTime]) assert(Number.isFinite(value) && value >= 0, 'Times must be finite and nonnegative');
  assert(Number.isFinite(scale) && scale > 0, 'Scale must be positive');
  const motion = options.motion ?? 'no-preference';
  assert(['reduce', 'no-preference'].includes(motion), 'Motion must be reduce or no-preference');
  for (const value of [options.width, options.height].filter(v => v !== undefined)) {
    assert(Number.isInteger(value) && value > 0, 'Dimensions must be positive integers');
  }
  // A new directory prevents accidentally overwriting an input or earlier evidence.
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.mkdirSync(output);
  const server = http.createServer((req, res) => {
    if (req.url !== '/image.svg') { res.writeHead(404); res.end(); return; }
    res.setHeader('Content-Type', 'image/svg+xml');
    res.setHeader('Content-Security-Policy', "default-src 'none'; img-src data:; style-src 'unsafe-inline'; font-src data:");
    res.end(svg);
  });
  let browser;
  try {
    await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
    const origin = `http://127.0.0.1:${server.address().port}`;
    browser = await chromium.launch({ channel: 'chrome', headless: true });
    const context = await browser.newContext({ deviceScaleFactor: scale, reducedMotion: motion, serviceWorkers: 'block' });
    const blocked = [];
    await context.route('**/*', route => {
      if (route.request().url() === origin + '/image.svg' && route.request().isNavigationRequest()) return route.continue();
      blocked.push(route.request().url()); return route.abort();
    });
    const page = await context.newPage();
    const warnings = [];
    page.on('console', message => { if (message.type() === 'error') warnings.push(message.text()); });
    await page.goto(origin + '/image.svg');
    const natural = await page.evaluate(() => {
      const root = document.documentElement;
      if (!(root instanceof SVGSVGElement)) throw new Error('Input is not an SVG document');
      const vb = root.viewBox.baseVal;
      const absolute = name => root.hasAttribute(name) && root[name].baseVal.unitType !== 2 && root[name].baseVal.value > 0;
      const size = absolute('width') && absolute('height') ? [root.width.baseVal.value, root.height.baseVal.value]
        : vb.width > 0 && vb.height > 0 ? [vb.width, vb.height]
        : [root.getBoundingClientRect().width, root.getBoundingClientRect().height];
      return { size, viewBox: [vb.x, vb.y, vb.width, vb.height] };
    });
    const width = options.width ?? Math.ceil(options.height ? options.height * natural.size[0] / natural.size[1] : natural.size[0]);
    const height = options.height ?? Math.ceil(width * natural.size[1] / natural.size[0]);
    assert([width, height].every(v => Number.isInteger(v) && v > 0), 'Invalid SVG dimensions');
    // ponytail: one PNG up to 64 MP; tile larger artwork in a dedicated export workflow.
    assert(width * height * scale * scale <= 64_000_000, 'Capture exceeds 64 megapixels');
    const crop = options.crop;
    if (crop) {
      assert(crop.length === 4 && crop.every(Number.isFinite), 'Crop is x,y,width,height in CSS pixels');
      assert(crop[0] >= 0 && crop[1] >= 0 && crop[2] > 0 && crop[3] > 0 && crop[0]+crop[2] <= width && crop[1]+crop[3] <= height, 'Crop must fit the rendered canvas');
    }
    await page.setViewportSize({ width, height });
    await page.evaluate(({ width, height }) => {
      const root = document.documentElement;
      root.style.setProperty('width', `${width}px`, 'important');
      root.style.setProperty('height', `${height}px`, 'important');
      root.style.setProperty('display', 'block', 'important');
      root.style.setProperty('margin', '0', 'important');
    }, { width, height });
    await setTime(page, time, cssTime);
    const frame = await page.screenshot({ path: path.join(output, 'frame.png'), animations: 'allow', omitBackground: true });
    if (crop) {
      await page.screenshot({ path: path.join(output, 'crop.png'), animations: 'allow', omitBackground: true,
        clip: { x: crop[0], y: crop[1], width: crop[2], height: crop[3] } });
    }
    const report = { source_sha256: createHash('sha256').update(svg).digest('hex'), browser: browser.version(),
      mode: 'direct-svg', width, height, scale, viewBox: natural.viewBox, svg_time_seconds: time, css_time_seconds: cssTime,
      motion, crop: crop ?? null, blocked_requests: blocked, warnings, frame_sha256: createHash('sha256').update(frame).digest('hex'),
      limits: 'Diagnostic rendering with scripts and external resources blocked; not an image-embedding or host compatibility test.' };
    fs.writeFileSync(path.join(output, 'render.json'), JSON.stringify(report, null, 2) + '\n');
    return report;
  } finally {
    try { if (browser) await browser.close(); }
    finally { if (server.listening) await new Promise(resolve => server.close(resolve)); }
  }
}

async function selfTest() {
  const folder = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'svg-test-'));
  try {
    const input = path.join(folder, 'neutral.svg');
    fs.writeFileSync(input, '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 60"><style>@keyframes slide{to{transform:translateX(30px)}}.leaf{animation:slide 2s linear infinite}</style><rect class="leaf" y="5" width="15" height="15" fill="green"/><circle cy="40" r="7"><animate attributeName="cx" values="10;90;10" dur="2s" repeatCount="indefinite"/></circle><script>document.documentElement.remove()</script></svg>');
    const a = await render(input, path.join(folder, 'first'), { width: 240, scale: 2, crop: [0, 0, 20, 10] });
    const b = await render(input, path.join(folder, 'repeat'), { width: 240, scale: 2 });
    assert.equal(a.frame_sha256, b.frame_sha256, 'Fixed-time captures differ');
    const smil = await render(input, path.join(folder, 'smil'), { width: 240, scale: 2, time: .5, cssTime: 0 });
    const css = await render(input, path.join(folder, 'css'), { width: 240, scale: 2, time: 0, cssTime: .5 });
    assert.notEqual(a.frame_sha256, smil.frame_sha256, 'SMIL clock did not move the rendered shape');
    assert.notEqual(a.frame_sha256, css.frame_sha256, 'CSS clock did not move the rendered shape');
    const crop = fs.readFileSync(path.join(folder, 'first', 'crop.png'));
    assert.deepEqual([crop.readUInt32BE(16), crop.readUInt32BE(20)], [40, 20]);
    assert.equal(a.height, 120, 'ViewBox aspect ratio was lost');
    await assert.rejects(() => render(input, path.join(folder, 'first')), /EEXIST/);
    console.log('OK: generic SVG, fixed clocks, independent CSS/SMIL motion, scaling, crop, blocked script, no overwrite');
  } finally { fs.rmSync(folder, { recursive: true, force: true }); }
}

async function main() {
  const { values, positionals } = parseArgs({ allowPositionals: true, options: {
    width: { type: 'string' }, height: { type: 'string' }, time: { type: 'string' }, 'css-time': { type: 'string' },
    scale: { type: 'string' }, motion: { type: 'string' }, crop: { type: 'string' }, help: { type: 'boolean' }, 'self-test': { type: 'boolean' },
  } });
  if (values.help) {
    console.log('node render_svg.cjs input.svg new-output-dir [--width N] [--height N] [--time SECONDS] [--css-time SECONDS] [--scale N] [--motion reduce|no-preference] [--crop X,Y,WIDTH,HEIGHT]\nnode render_svg.cjs --self-test');
    return;
  }
  if (values['self-test']) { await selfTest(); return; }
  assert.equal(positionals.length, 2, 'Provide an SVG path and a new output directory; see --help');
  const options = Object.fromEntries(['width', 'height', 'time', 'scale'].filter(k => values[k] !== undefined).map(k => [k, Number(values[k])]));
  if (values['css-time'] !== undefined) options.cssTime = Number(values['css-time']);
  if (values.motion !== undefined) options.motion = values.motion;
  if (values.crop !== undefined) options.crop = values.crop.split(',').map(Number);
  console.log(JSON.stringify(await render(path.resolve(positionals[0]), path.resolve(positionals[1]), options), null, 2));
}

module.exports = { render, setTime };
if (require.main === module) main().catch(error => { console.error(error.message); process.exitCode = 1; });
