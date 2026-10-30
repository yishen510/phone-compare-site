/** 校验详情页「缺失文案」按查证原因区分是否正确显示。 */
const fs = require('fs');
const { JSDOM } = require('jsdom');

const H = fs.readFileSync('index.html', 'utf8');
const errs = [];
const dom = new JSDOM(H, {
  runScripts: 'dangerously', url: 'https://x.test/', pretendToBeVisual: true,
  beforeParse(w) {
    w.matchMedia = w.matchMedia || (q => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }));
    w.requestIdleCallback = cb => setTimeout(() => cb({ timeRemaining: () => 8 }), 0);
    w.scrollTo = () => {};
    w.HTMLElement.prototype.scrollIntoView = function () {};
    w.addEventListener('error', x => errs.push(String(x.message)));
  },
});
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  await sleep(1500);
  const { document } = dom.window;
  for (let i = 0; i < 100; i++) {
    const g = document.getElementById('phoneGrid');
    if (g && g.dataset.painting === '0') break;
    await sleep(30);
  }
  const CASES = [
    ['zte-axon-60-ultra', '重量', '厂商规格页未列重量'],
    ['samsung-galaxy-a55', '充电', '厂商规格页未列充电功率'],
    ['samsung-galaxy-c55', '充电', '厂商规格页未列充电功率'],
    ['hua-pura80u', '处理器', '麒麟 9020'],
  ];
  const input = document.getElementById('searchInput');
  let ok = 0, bad = 0;
  for (const [id, label, want] of CASES) {
    // 先按机型名过滤，避免卡片落在分批绘制的后续批次里
    const name = (dom.window.PHONE_DATA || []).find(x => x.id === id)?.name || '';
    if (input) {
      input.value = name;
      input.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
      await sleep(320);
      for (let i = 0; i < 60; i++) {
        const g = document.getElementById('phoneGrid');
        if (g && g.dataset.painting === '0') break;
        await sleep(30);
      }
    }
    const btn = document.querySelector(`#phoneGrid [data-detail="${id}"]`);
    if (!btn) { console.log(`  x ${id} 卡片不存在（可能在表格视图）`); bad++; continue; }
    btn.click();
    await sleep(80);
    const rows = [...document.querySelectorAll('#detailModal .detail-row')];
    const row = rows.find(r => r.querySelector('span') && r.querySelector('span').textContent.trim() === label);
    const got = row ? row.querySelector('b').textContent.trim() : 'NONE';
    const pass = got.includes(want);
    console.log(`  ${pass ? 'PASS' : 'FAIL'} ${id} ${label}: ${got}${pass ? '' : `（期望包含 ${want}）`}`);
    pass ? ok++ : bad++;
    document.querySelector('[data-close]')?.click();
    await sleep(30);
  }
  console.log(`\n${ok} 通过 / ${bad} 失败；脚本错误 ${errs.length}`);
  process.exit(bad ? 1 : 0);
})();
