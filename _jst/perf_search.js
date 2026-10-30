/** 搜索性能探针：重点看「新增紧凑索引」后，最坏情况（无结果查询）会不会变慢。 */
const fs = require('fs');
const { JSDOM } = require('jsdom');
const H = fs.readFileSync(process.argv[2] || 'index.html', 'utf8');
const dom = new JSDOM(H, {
  runScripts: 'dangerously', url: 'https://x.test/', pretendToBeVisual: true,
  beforeParse(w) {
    w.matchMedia = w.matchMedia || (q => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }));
    w.requestIdleCallback = cb => setTimeout(() => cb({ timeRemaining: () => 8 }), 0);
    w.scrollTo = () => {}; w.HTMLElement.prototype.scrollIntoView = function () {};
  },
});
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  await sleep(1600);
  const { window } = dom; const { document } = window;
  const settle = async () => {
    for (let i = 0; i < 300; i++) {
      const g = document.getElementById('phoneGrid');
      if (g && g.dataset.painting === '0') return; await sleep(20);
    }
  };
  await settle();
  const si = document.getElementById('searchInput');
  const runs = [
    ['首次无结果(建全量紧凑索引)', 'zzzzz不存在zzzzz'],
    ['第二次无结果(索引已缓存)', 'qqqqq不存在qqqqq'],
    ['常见词 骁龙', '骁龙'],
    ['精确 小米15', '小米15'],
    ['清空', ''],
  ];
  for (const [label, q] of runs) {
    si.value = q;
    const t0 = process.hrtime.bigint();
    si.dispatchEvent(new window.Event('input', { bubbles: true }));
    await sleep(200); await settle();
    const ms = Number(process.hrtime.bigint() - t0) / 1e6;
    const n = document.querySelectorAll('#phoneGrid .phone-card').length;
    console.log(`  ${label.padEnd(26)} 往返 ${ms.toFixed(0).padStart(5)} ms（含 200ms 防抖）  卡片 ${n}`);
  }
  process.exit(0);
})();
