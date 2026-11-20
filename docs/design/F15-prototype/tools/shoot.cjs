const { chromium } = require('@playwright/test');
const out = process.argv[2];
const base = 'http://127.0.0.1:8095';
(async () => {
  const browser = await chromium.launch();
  const problems = [];
  const dirs = [['a', 'a-morning-paper', 'Nunito Variable'], ['b', 'b-instrument', 'IBM Plex Sans Variable']];
  const shots = [];
  for (const [d] of dirs) for (const s of ['today', 'planner']) for (const w of [390, 1440]) for (const t of ['light', 'dark']) shots.push([d, s, w, t, 'en']);
  for (const [d] of dirs) for (const s of ['today', 'planner']) for (const l of ['uz', 'ru']) shots.push([d, s, 390, 'light', l]);
  for (const [d, s, w, t, l] of shots) {
    const [, file, font] = dirs.find(x => x[0] === d);
    const page = await browser.newPage({ viewport: { width: w, height: w === 390 ? 844 : 900 }, deviceScaleFactor: 1, colorScheme: t });
    page.on('pageerror', e => problems.push(`${d} ${s} ${w} ${t} ${l}: ${e}`));
    page.on('requestfailed', r => problems.push(`${d} ${s}: failed ${r.url()}`));
    await page.goto(`${base}/${file}.html?screen=${s}&theme=${t}&lang=${l}&chrome=0`);
    await page.evaluate(() => document.fonts.ready);
    // Load the subsets for Uzbek and Russian letters, then check that the face covers them.
    const ok = await page.evaluate(async f => { await document.fonts.load(`16px "${f}"`, 'oʻgʻʼ Жж Ўў Ққ Ғғ Ҳҳ'); return document.fonts.check(`16px "${f}"`, 'oʻgʻʼ Жж Ўў Ққ Ғғ Ҳҳ'); }, font);
    if (!ok) problems.push(`${d} ${s} ${w} ${t} ${l}: font ${font} not loaded`);
    const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    if (over > 0) problems.push(`${d} ${s} ${w} ${t} ${l}: ${over}px sideways overflow`);
    const small = await page.evaluate(() => [...document.querySelectorAll('.btn:not(.btn-xs), .pill, .bottom-link, .side-link, .seg button')]
      .filter(e => e.offsetParent).map(e => e.getBoundingClientRect()).filter(r => r.height < 44 && r.height > 0 && !(r.height >= 40)).length);
    if (small) problems.push(`${d} ${s} ${w} ${t} ${l}: ${small} controls under 40px`);
    const name = `${d}-${s}-${w}-${t}${l === 'en' ? '' : '-' + l}.png`;
    await page.screenshot({ path: `${out}/${name}`, fullPage: true });
    await page.close();
  }
  await browser.close();
  console.log(problems.length ? problems.join('\n') : 'no problems', `\n${shots.length} screenshots`);
})();
