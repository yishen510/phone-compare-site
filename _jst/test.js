/* 用 jsdom 跑真实页面，验证表格表头排序与详情「同价位还有」（无浏览器环境下的替代验证） */
const fs = require('fs');
const { JSDOM } = require('jsdom');

const PAGE = process.env.PAGE || 'D:/Codex/_deploy_phone/index.html';
const html = fs.readFileSync(PAGE, 'utf8');
const errors = [];

const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  url: 'https://yishen510.github.io/phone-compare-site/',
  pretendToBeVisual: true,
  beforeParse(window) {
    window.matchMedia = window.matchMedia || function (q) {
      return { matches: false, media: q, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} };
    };
    window.requestIdleCallback = cb => window.setTimeout(() => cb({ timeRemaining: () => 8 }), 0);
    window.scrollTo = () => {};
    window.HTMLElement.prototype.scrollIntoView = function () {};
    window.addEventListener('error', e => errors.push(String(e.message)));
  }
});

const { window } = dom;
const { document } = window;

const q = sel => document.querySelector(sel);
const qa = sel => [...document.querySelectorAll(sel)];
const sleepRaw = ms => new Promise(r => setTimeout(r, ms));
/* 卡片改成分批绘制后，sleep 结束不代表 DOM 已经画完；统一等到 painting=0 再断言 */
const settle = async () => {
  const g = document.getElementById('phoneGrid');
  for (let i = 0; i < 150; i++) {
    if (!g || g.dataset.painting === '0') return;
    await sleepRaw(20);
  }
};
const sleep = async ms => { await sleepRaw(ms); await settle(); };

const results = [];
const check = (name, ok, detail) => results.push({ ok: !!ok, name, detail });

/* ---- 表格读取助手 ---- */
const rows = () => qa('.phone-table tbody tr');
const colText = (colIdx, limit) => rows().slice(0, limit || rows().length).map(tr => tr.children[colIdx].textContent.trim());
const btnOf = col => q(`.phone-table .th-sort-btn[data-sort-col="${col}"]`);
const thOf = col => { const b = btnOf(col); return b ? b.closest('th') : null; };
const ariaOf = col => { const t = thOf(col); return t ? t.getAttribute('aria-sort') : null; };
const COLS = ['year', 'screen', 'battery', 'weight', 'price'];
const ariaAll = () => Object.fromEntries(COLS.map(c => [c, ariaOf(c)]));

/* 从一列文本里抽数字，没数字的记为 null */
const nums = (texts, re) => texts.map(t => { const m = t.match(re); return m ? Number(m[1].replace(/,/g, '')) : null; });
/* 未知值（null）必须全部排在已知值之后，且已知值按 dir 单调 */
function sortedWell(list, dir) {
  const firstNull = list.indexOf(null);
  const known = list.filter(v => v !== null);
  const nullTail = firstNull === -1 || list.slice(firstNull).every(v => v === null);
  const mono = known.every((v, i) => i === 0 || (dir > 0 ? v >= known[i - 1] : v <= known[i - 1]));
  return { ok: nullTail && mono, nullTail, mono, knownCount: known.length };
}

const BAT_RE = /(\d{3,5})\s*mAh/i;
const WT_RE = /(\d{2,3}(?:\.\d{1,2})?)\s*(?:g|克)/i;
const PRICE_RE = /¥([\d,]+)/;

(async () => {
  await sleep(800);
  const TOTAL = (window.PHONE_DATA || []).length;
  check('页面无脚本报错', errors.length === 0, errors);
  check('卡片数与数据条数一致', qa('.phone-card').length === TOTAL && rows().length === 0, { cards: qa('.phone-card').length, data: TOTAL });

  /* ---------- A. 表格排序 ---------- */
  q('[data-view="table"]').click();
  check(`表格渲染 ${TOTAL} 行`, rows().length === TOTAL, rows().length);
  check('5 个可排序列齐全', COLS.every(c => btnOf(c)), qa('.phone-table .th-sort-btn').map(b => b.dataset.sortCol));
  check('默认按最新发布排序 → 年份列为 descending', ariaOf('year') === 'descending', ariaAll());
  check('其余列默认 aria-sort=none', ['screen', 'battery', 'weight', 'price'].every(c => ariaOf(c) === 'none'), ariaAll());

  btnOf('battery').click();
  const batDesc = nums(colText(4), BAT_RE);
  check('点电池列 → 排序值 batteryDesc、aria=descending', q('#sortSelect').value === 'batteryDesc' && ariaOf('battery') === 'descending', { select: q('#sortSelect').value, aria: ariaOf('battery') });
  check('电池降序：已知值单调不增、未知值全在末尾', sortedWell(batDesc, -1).ok, sortedWell(batDesc, -1));
  check('电池降序：只有当前列带方向、其余为 none', ['year', 'screen', 'weight', 'price'].every(c => ariaOf(c) === 'none'), ariaAll());

  btnOf('battery').click();
  const batAsc = nums(colText(4), BAT_RE);
  check('再点一次 → batteryAsc、aria=ascending', q('#sortSelect').value === 'batteryAsc' && ariaOf('battery') === 'ascending', { select: q('#sortSelect').value, aria: ariaOf('battery') });
  check('电池升序：已知值单调不减、未知值全在末尾', sortedWell(batAsc, 1).ok, sortedWell(batAsc, 1));

  btnOf('price').click();
  const prices = nums(colText(6), PRICE_RE);
  const colMin = Math.min(...prices.filter(v => v !== null));
  check('点价格列 → priceAsc、aria=ascending', q('#sortSelect').value === 'priceAsc' && ariaOf('price') === 'ascending', { select: q('#sortSelect').value, aria: ariaOf('price') });
  check(`价格升序：首行即当前结果最低价 ${colMin} 且整体不降`, prices[0] === colMin && sortedWell(prices, 1).ok, prices.slice(0, 5));

  btnOf('weight').click();
  const wts = nums(colText(5), WT_RE);
  check('点重量列 → weightAsc、aria=ascending', q('#sortSelect').value === 'weightAsc' && ariaOf('weight') === 'ascending', { select: q('#sortSelect').value });
  check('重量升序：单调不减、未知值在末尾', sortedWell(wts, 1).ok, sortedWell(wts, 1));

  /* ---------- B. 键盘可达性 ---------- */
  const kb = btnOf('year');
  kb.focus();
  const focusBefore = document.activeElement && document.activeElement.dataset.sortCol;
  kb.dispatchEvent(new window.MouseEvent('click', { bubbles: true, cancelable: true, detail: 0 }));
  await sleep(30);
  check('键盘触发（Enter/Space 等价 click detail=0）能排序', q('#sortSelect').value === 'newest' && ariaOf('year') === 'descending', { select: q('#sortSelect').value, aria: ariaOf('year') });
  check('键盘触发后有播报文案', /已按「年份」从新到旧排列/.test(q('#toast').textContent), q('#toast').textContent);
  check('重渲染后焦点仍在该列（可连续操作）', document.activeElement && document.activeElement.dataset.sortCol === 'year', { before: focusBefore, after: document.activeElement && document.activeElement.dataset.sortCol });

  q('#toast').classList.remove('show'); q('#toast').textContent = '';
  btnOf('screen').dispatchEvent(new window.MouseEvent('click', { bubbles: true, cancelable: true, detail: 1 }));
  await sleep(30);
  check('鼠标点击不弹 toast（只留箭头反馈）', q('#toast').textContent === '' && !q('#toast').classList.contains('show'), q('#toast').textContent);

  check('排序状态写进地址栏', /sort=screenAsc/.test(window.location.search), window.location.search);

  /* ---------- C. 同价位还有 ---------- */
  q('[data-view="cards"]').click();
  await settle();   /* 卡片是分批画的，切回卡片视图后要等画完才能按 id 找按钮 */
  const phones = window.PHONE_DATA || [];
  const capOf = p => {
    const open = q(`#phoneGrid [data-detail="${p.id}"]`);
    if (!open) return { name: p.name, missing: true };
    open.click();
    const block = q('#detailModal .peer-block');
    return {
      name: p.name,
      price: p.priceCN,
      title: (q('#detailTitle') || {}).textContent,
      caption: block ? block.querySelector('.peer-head span').textContent.trim() : null,
      count: qa('#detailModal .peer-card').length,
      peers: qa('#detailModal .peer-card').map(b => ({
        name: b.querySelector('.peer-name').textContent,
        price: Number((b.querySelector('.peer-price').textContent.match(/¥([\d,]+)/) || [])[1].replace(/,/g, ''))
      }))
    };
  };
  // 「价格待核」机型的 priceCN 是 null，不能混进最低价/最高价的取样里
  const priced = phones.filter(p => p.priceCN !== null && p.priceCN !== undefined && p.priceCN !== '' && Number.isFinite(Number(p.priceCN)));
  const byPrice = priced.slice().sort((a, b) => Number(a.priceCN) - Number(b.priceCN));
  const cheapest = byPrice[0], priciest = byPrice[byPrice.length - 1];
  const mid = phones.find(p => p.name.includes('Galaxy S25'));

  const c1 = capOf(cheapest);
  const band1 = Number((c1.caption || '').match(/(\d+)%/)?.[1] || 0);
  check('最低价机型也能给出 ≥2 个候选，且区间文案与实现一致', c1.count >= 2 && [35, 50].includes(band1), { name: c1.name, price: c1.price, caption: c1.caption, count: c1.count });
  check('最低价机型的候选都落在标注区间内且不含自身', band1 > 0 && c1.peers.every(x => x.name !== c1.name && Math.abs(x.price - c1.price) / c1.price <= band1 / 100), c1.peers);

  const c2 = capOf(mid);
  check('常规价位仍按 35% 且候选充足', c2.count === 3 && /35%/.test(c2.caption || ''), { name: c2.name, caption: c2.caption, count: c2.count });

  const c3 = capOf(priciest);
  check('最高价机型也有候选', c3.count >= 2 && /35%/.test(c3.caption || ''), { name: c3.name, caption: c3.caption, count: c3.count });

  const before = (q('#detailTitle') || {}).textContent;
  const card = qa('#detailModal .peer-card')[0];
  const target = card && card.querySelector('.peer-name').textContent;
  if (card) { card.click(); await sleep(60); }
  check('点候选卡可跳到该机型详情', target && (q('#detailTitle') || {}).textContent === target, { from: before, clicked: target, now: (q('#detailTitle') || {}).textContent });

  const fail = results.filter(r => !r.ok);
  console.log(JSON.stringify({ total: results.length, passed: results.length - fail.length, failed: fail.length, failures: fail, results }, null, 1));
  dom.window.close();
  process.exit(fail.length ? 1 : 0);
})().catch(e => { console.log('FATAL', e.message, e.stack); process.exit(2); });
