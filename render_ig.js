// 用法：node render_ig.js '[[src.html, out.jpg], ...]' [寬 高]（由 build.py、reels.py 呼叫）
const { chromium } = require('playwright');
(async () => {
  const jobs = JSON.parse(process.argv[2]);
  const width = +(process.argv[3] || 1080), height = +(process.argv[4] || 1350);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width, height } });
  for (const [src, out] of jobs) {
    await pg.goto('file://' + src, { waitUntil: 'networkidle' });
    await pg.evaluate(() => document.fonts.ready);
    await pg.screenshot({ path: out, type: 'jpeg', quality: 92 });
  }
  await b.close();
})();
