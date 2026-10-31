/**
 * 搜索回归：重点守住「不带空格也能搜到」和「精确命中排最前」。
 * 起因：库里写作「小米 15」「荣耀 Magic8」，用户打字不带空格时原本搜不到（0 条）。
 */
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
  const search = async q => {
    si.value = q;
    si.dispatchEvent(new window.Event('input', { bubbles: true }));
    await sleep(320); await settle();
    const cards = [...document.querySelectorAll('#phoneGrid .phone-card')];
    const nameOf = c => {
      const el = c.querySelector('.card-name, h3');
      return (el ? el.textContent : c.textContent).replace(/\s+/g, ' ').trim();
    };
    /* 分页后 DOM 卡片数只是第一页；结果总数看 #resultCount */
    const total = Number((document.getElementById('resultCount') || {}).textContent) || 0;
    return { n: cards.length, total, first: cards.length ? nameOf(cards[0]) : '' };
  };

  let ok = 0, bad = 0;
  const check = (name, cond, detail) => {
    console.log(`  ${cond ? 'PASS' : 'FAIL'} ${name}${detail ? ' → ' + detail : ''}`);
    cond ? ok++ : bad++;
  };

  // 1. 不带空格必须能搜到（这是本轮修的核心缺陷）
  for (const [q, want] of [['小米15', '小米 15'], ['荣耀Magic8', '荣耀 Magic8']]) {
    const r = await search(q);
    check(`搜「${q}」有结果`, r.n > 0, `${r.n} 条`);
    check(`搜「${q}」首条为「${want}」`, r.first === want, `实际 ${JSON.stringify(r.first)}`);
  }
  // 2. 近似机型不能压过精确命中
  const r2 = await search('X300');
  check('搜「X300」首条为 vivo X300（而非 Ultra/Pro）', r2.first === 'vivo X300', `实际 ${JSON.stringify(r2.first)}`);
  // 3. 常规查询不回归
  const r3 = await search('骁龙');
  check('搜「骁龙」结果充足', r3.total > 50, `${r3.total} 条（当前页 ${r3.n} 张）`);
  // 4. 无意义查询应为 0
  const r4 = await search('zzzz不存在的机型zzzz');
  check('无意义查询返回 0 条', r4.n === 0, `${r4.n} 条`);
  // 5. 清空恢复全部（条数跟着数据走，别写死，否则每次补机型都要改测试）
  const total = (dom.window.PHONE_DATA || []).length;
  const r5 = await search('');
  check(`清空后恢复全部 ${total} 条`, r5.total === total, `${r5.total} 条（当前页 ${r5.n} 张）`);

  console.log(`\n${ok} 通过 / ${bad} 失败`);
  process.exit(bad ? 1 : 0);
})();
