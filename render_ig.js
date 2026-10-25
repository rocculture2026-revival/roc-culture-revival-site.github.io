// 用法：node render_ig.js '[[src.html, out.jpg], ...]'（由 build.py 呼叫）
const { chromium } = require('playwright');
(async () => {
  const jobs = JSON.parse(process.argv[2]);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  for (const [src, out] of jobs) {
    await pg.goto('file://' + src, { waitUntil: 'networkidle' });
    await pg.evaluate(() => document.fonts.ready);
    await pg.screenshot({ path: out, type: 'jpeg', quality: 92 });
  }
  await b.close();
})();
