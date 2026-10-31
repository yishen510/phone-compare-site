/**
 * URL 参数健壮性探针：共享链接被改坏 / 过期时，站点会不会崩、会不会出现「看不见的筛选」。
 * 用法：node _jst/probe_url.js
 */
const fs = require('fs');
const { JSDOM } = require('jsdom');
const H = fs.readFileSync('index.html', 'utf8');

const CASES = [
  ['正常', '?q=骁龙'],
  ['不存在的品牌', '?brand=NotABrand'],
  ['不存在的机型定位', '?type=不存在的定位'],
  ['非法排序值', '?sort=bogus'],
  ['非法年份', '?from=abc&to=99999'],
  ['对比里是不存在的机型', '?compare=badid1,badid2'],
  ['详情指向不存在机型', '?model=notexist'],
  ['对比超上限(6个)', '?compare=a1,b2,c3,d4,e5,f6'],
  ['XSS 尝试', '?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E'],
];

function mk(url) {
  const errs = [];
  const dom = new JSDOM(H, {
    runScripts: 'dangerously', url: 'https://x.test/' + url, pretendToBeVisual: true,
    beforeParse(w) {
      w.matchMedia = w.matchMedia || (q => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }));
      w.requestIdleCallback = cb => setTimeout(() => cb({ timeRemaining: () => 8 }), 0);
      w.scrollTo = () => {}; w.HTMLElement.prototype.scrollIntoView = function () {};
      w.alert = () => { errs.push('alert 被调用'); };
      w.addEventListener('error', x => errs.push(String(x.message)));
    },
  });
  return { dom, errs };
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  for (const [label, qs] of CASES) {
    const { dom, errs } = mk(qs);
    await sleep(1500);
    const { window } = dom; const { document } = window;
    for (let i = 0; i < 200; i++) {
      const g = document.getElementById('phoneGrid');
      if (g && g.dataset.painting === '0') break; await sleep(20);
    }
    const cards = document.querySelectorAll('#phoneGrid .phone-card').length;
    const empty = document.getElementById('emptyState');
    const emptyShown = empty && !empty.hidden;
    // 「看不见的筛选」：结果为空，但筛选面板里没有可取消的勾选、也没有对应提示条
    const chips = [...document.querySelectorAll('#activeFilters .chip, #activeFilters button, #activeFilters span')]
      .map(e => e.textContent.replace(/\s+/g, ' ').trim()).filter(Boolean);
    const checkedBrands = [...document.querySelectorAll('#brandFilters input:checked')].map(i => i.value);
    const checkedTypes = [...document.querySelectorAll('input[name="type"]:checked')].map(i => i.value);
    let compareRows = -1;
    try {
      const openBtn = document.getElementById('openCompare') || document.getElementById('headerCompare');
      if (openBtn) { openBtn.click(); await sleep(300); }
      compareRows = document.querySelectorAll('#compareModal tbody tr').length;
    } catch (e) { errs.push('对比打开异常: ' + e.message); }
    const state = window.__STATE_SNAPSHOT || {};
    console.log(`\n[${label}] ${qs}`);
    console.log(`   卡片 ${cards}  空状态=${emptyShown}  已勾品牌=${JSON.stringify(checkedBrands)}  已勾定位=${JSON.stringify(checkedTypes)}`);
    console.log(`   筛选提示条=${JSON.stringify(chips.slice(0, 4))}  对比表行数=${compareRows}  错误=${errs.length ? errs.slice(0, 2) : '无'}`);
    window.close();
  }
  process.exit(0);
})();
