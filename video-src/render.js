// Renders video.html frame by frame: node render.js <outDir> [fps] [onlyTimes,comma,separated]
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const [out, fpsArg, only] = process.argv.slice(2);
  const fps = +(fpsArg || 30);
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 360, height: 640 }, deviceScaleFactor: 2 });
  await p.goto('file://' + path.join(__dirname, 'video.html'), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  const dur = await p.evaluate(() => window.DURATION);
  const times = only ? only.split(',').map(Number) : Array.from({ length: Math.round(dur * fps) }, (_, i) => i / fps);
  for (let i = 0; i < times.length; i++) {
    await p.evaluate(t => seek(t), times[i]);
    await p.screenshot({ path: path.join(out, String(i).padStart(5, '0') + '.jpg'), type: 'jpeg', quality: 92 });
  }
  await b.close();
})();
