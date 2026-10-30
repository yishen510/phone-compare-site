/** 搜索相关性探针：看每个查询的前 5 条结果是不是用户最想要的。 */
const fs = require('fs');
const { JSDOM } = require('jsdom');
const H = fs.readFileSync('index.html', 'utf8');
const dom = new JSDOM(H, {
  runScripts: 'dangerously', url: 'https://x.test/', pretendToBeVisual: true,
  beforeParse(w) {
    w.matchMedia = w.matchMedia || (q => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }));
    w.requestIdleCallback = cb => setTimeout(() => cb({ timeRemaining: () => 8 }), 0);
    w.scrollTo = () => {}; w.HTMLElement.prototype.scrollIntoView = function () {};
  },
});
const sleep = ms => new Promise(r => setTimeout(r, ms));
const QUERIES = process.argv.slice(2).length ? process.argv.slice(2)
  : ['小米15', 'X300', 'nova 14', '荣耀Magic8', '骁龙8至尊版', 'K90', '折叠屏', '6000mAh'];

(async () => {
  await sleep(1500);
  const { window } = dom; const { document } = window;
  const settle = async () => {
    for (let i = 0; i < 150; i++) {
      const g = document.getElementById('phoneGrid');
      if (g && g.dataset.painting === '0') return; await sleep(30);
    }
  };
  await settle();
  const si = document.getElementById('searchInput');
  for (const q of QUERIES) {
    si.value = q;
    si.dispatchEvent(new window.Event('input', { bubbles: true }));
    await sleep(420); await settle();
    const names = [...document.querySelectorAll('#phoneGrid .phone-card .card-name, #phoneGrid .phone-card h3, #phoneGrid .phone-card')]
      .slice(0, 6)
      .map(n => (n.querySelector('.card-name, h3') || n).textContent.replace(/\s+/g, ' ').trim().slice(0, 22));
    const total = document.getElementById('resultCount')?.textContent || '';
    console.log(`\n查询「${q}」 结果${total}`);
    names.forEach((n, i) => console.log(`   ${i + 1}. ${n}`));
  }
  process.exit(0);
})();
