/**
 * 功能冒烟：覆盖此前断言没测到的交互（收藏、对比、导出、推荐、详情导航、密度、主题、搜索、URL 状态）。
 * 用法：node _jst/smoke_func.js [file]
 */
const fs = require('fs');
const { JSDOM } = require('jsdom');

const file = process.argv[2] || 'D:/Codex/_deploy_phone/index.html';
const html = fs.readFileSync(file, 'utf8');
const errs = [];
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  url: 'https://yishen510.github.io/phone-compare-site/',
  pretendToBeVisual: true,
  beforeParse(w) {
    w.matchMedia = w.matchMedia || (q => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }));
    w.requestIdleCallback = cb => setTimeout(() => cb({ timeRemaining: () => 8 }), 0);
    w.scrollTo = () => {};
    w.HTMLElement.prototype.scrollIntoView = function () {};
    w.URL.createObjectURL = () => 'blob:mock';
    w.URL.revokeObjectURL = () => {};
    w.addEventListener('error', e => errs.push(String(e.message)));
  },
});
const { window } = dom;
const { document } = window;
const q = s => document.querySelector(s);
const qa = s => [...document.querySelectorAll(s)];
const sleepRaw = ms => new Promise(r => setTimeout(r, ms));
const settle = async () => {
  const g = document.getElementById('phoneGrid');
  for (let i = 0; i < 150; i++) {
    if (!g || g.dataset.painting === '0') return;
    await sleepRaw(20);
  }
};
const sleep = async ms => { await sleepRaw(ms); await settle(); };

const out = [];
const check = (name, ok, detail) => out.push({ ok: !!ok, name, detail });
/* 列表默认逐页展示；验证「全量渲染完整性」前先点一次「全部展开」 */
const expandAll = async () => {
  const bar = document.getElementById('pagerBar');
  const btn = q('[data-pager="all"]');
  if (bar && !bar.hidden && btn) { btn.click(); await sleep(150); }
};

(async () => {
  await sleep(300);
  const data = window.PHONE_DATA || [];

  /* 1. 卡片渲染完整性（先展开全部：分页模式下 DOM 只有第一页） */
  await expandAll();
  check('卡片全部绘制完成', qa('.phone-card').length === data.length,
    { cards: qa('.phone-card').length, data: data.length });

  /* 2. 收藏：点一次收藏，再点取消 */
  const favBtn = q('#phoneGrid [data-fav]');
  const favId = favBtn && favBtn.dataset.fav;
  favBtn.click(); await sleep(40);
  const saved = window.localStorage.getItem('phoneindex.favs.v1') || '';
  check('点击收藏后写入 localStorage', saved.includes(favId), { id: favId, key: saved.slice(0, 40) });
  const favBtn2 = q(`#phoneGrid [data-fav="${favId}"]`);
  check('收藏后按钮变为已选状态', !!favBtn2 && favBtn2.getAttribute('aria-pressed') === 'true',
    { pressed: favBtn2 && favBtn2.getAttribute('aria-pressed') });
  favBtn2.click(); await sleep(40);

  /* 3. 对比：加两台后打开对比面板 */
  const cmpA = q('#phoneGrid [data-compare]');
  cmpA.click(); await sleep(30);
  const cmpBtns = qa('#phoneGrid [data-compare]');
  cmpBtns[1].click(); await sleep(50);
  const cmpModal = q('#compareModal');
  q('#headerCompare')?.click(); await sleep(80);
  check('加入两台后可打开对比面板', !!cmpModal && !cmpModal.hidden,
    { hidden: cmpModal && cmpModal.hidden });
  check('对比面板含两列机型', qa('#compareModal .compare-col, #compareModal th').length >= 2,
    { cols: qa('#compareModal .compare-col').length });

  /* 4. 导出 CSV */
  let csvName = null;
  const origCreate = document.createElement.bind(document);
  document.createElement = function (tag, ...rest) {
    const el = origCreate(tag, ...rest);
    if (String(tag).toLowerCase() === 'a') {
      const origClick = el.click.bind(el);
      el.click = function () { csvName = el.getAttribute('download'); };
      el.__isDownload = true;
    }
    return el;
  };
  q('#compareModal [data-export="csv"]')?.click(); await sleep(60);
  check('对比面板可导出 CSV', !!csvName && /compare-\d{8}\.csv/.test(csvName), { csvName });
  document.createElement = origCreate;
  q('#compareModal [data-close]')?.click(); await sleep(40);

  /* 5. 推荐：选一个优先级后出结果 */
  const pri = q('[data-priority]');
  if (pri) {
    pri.click(); await sleep(30);
    q('#applyRecommend')?.click(); await sleep(120);
    const cards = qa('#recommendResults .rec-card').length;
    check('推荐面板能给出候选机型', cards > 0, { cards });
    q('#closeRecommend')?.click(); await sleep(30);
  } else {
    check('推荐面板能给出候选机型', false, { reason: 'no priority button' });
  }

  /* 6. 搜索 */
  const search = q('#searchInput');
  search.value = 'Mate';
  search.dispatchEvent(new window.Event('input', { bubbles: true }));
  await sleepRaw(260);           // 搜索有 160ms 防抖
  await settle();
  const searched = qa('.phone-card').length;
  check('搜索能过滤结果', searched > 0 && searched < data.length, { cards: searched, total: data.length });
  search.value = '';
  search.dispatchEvent(new window.Event('input', { bubbles: true }));
  await sleepRaw(260); await settle();

  /* 7. 详情导航：打开详情后用 → 切换下一台 */
  const firstDetail = q('#phoneGrid [data-detail]');
  firstDetail.click(); await sleep(60);
  const title1 = q('#detailTitle')?.textContent;
  q('#detailModal [data-nav="1"]')?.click(); await sleep(60);
  const title2 = q('#detailTitle')?.textContent;
  check('详情页可切换到下一台', !!title1 && !!title2 && title1 !== title2, { title1, title2 });
  check('详情页参数分组已渲染', qa('#detailModal .spec-group').length > 0,
    { groups: qa('#detailModal .spec-group').length });
  q('#detailModal [data-close]')?.click(); await sleep(30);

  /* 8. 参数搜索框（详情内） */
  firstDetail.click(); await sleep(60);
  const specSearch = q('#detailModal .spec-search-input');
  if (specSearch) {
    specSearch.value = '电池';
    specSearch.dispatchEvent(new window.Event('input', { bubbles: true }));
    await sleep(50);
    const cnt = q('#detailModal .spec-search-count');
    check('详情参数搜索有反馈', !!cnt, { shown: cnt && !cnt.hidden, text: cnt && cnt.textContent });
  } else {
    check('详情参数搜索有反馈', false, { reason: 'no spec search' });
  }
  q('#detailModal [data-close]')?.click(); await sleep(30);

  /* 9. 视图切换与密度 */
  q('[data-view="table"]')?.click(); await sleep(60);
  check('表格视图行数与数据一致（已展开全部）', qa('.phone-table tbody tr').length === data.length,
    { rows: qa('.phone-table tbody tr').length });
  q('[data-view="cards"]')?.click(); await sleep(60);
  const densityBtn = qa('[data-density]').find(b => b.dataset.density === 'compact');
  if (densityBtn) {
    densityBtn.click(); await sleep(60);
    check('密度切换加上 is-compact', q('#phoneGrid')?.classList.contains('is-compact'),
      { cls: q('#phoneGrid')?.className });
    qa('[data-density]').find(b => b.dataset.density !== 'compact')?.click(); await sleep(40);
  } else {
    check('密度切换加上 is-compact', false, { reason: 'no density button' });
  }

  /* 10. URL 状态：筛选后地址栏应带上参数 */
  const box = q('input[name="type"][value="中端影像"]');
  box.checked = true;
  box.dispatchEvent(new window.Event('change', { bubbles: true }));
  await sleep(80);
  check('筛选状态写入地址栏', /type=/.test(window.location.search), { search: window.location.search });
  box.checked = false;
  box.dispatchEvent(new window.Event('change', { bubbles: true }));
  await sleep(60);

  check('全程无脚本报错', errs.length === 0, errs.slice(0, 3));

  const failed = out.filter(x => !x.ok);
  for (const r of out) console.log((r.ok ? 'PASS' : 'FAIL') + '  ' + r.name + (r.detail ? '  → ' + JSON.stringify(r.detail).slice(0, 140) : ''));
  console.log(`\n${out.length - failed.length}/${out.length} 通过`);
  process.exit(failed.length ? 1 : 0);
})().catch(e => { console.log('FATAL', e.message, e.stack && e.stack.slice(0, 300)); process.exit(2); });
