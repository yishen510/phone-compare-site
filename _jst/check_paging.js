/* 逐页展示（分页）回归：
   1) 结果超过阈值时默认只画一页，并给出「已显示 N / 总数」+ 三个操作
   2) 「加载更多」是追加而不是重建（已加载卡片节点不被替换，滚动位置不跳）
   3) 「全部展开」（用户显式要求）能拿到全量
   4) 「改为逐页加载」能退回分页
   5) 结果不多时不分页（搜索 5 条不该让用户再点一次）
   6) 排序/筛选变化回到第一页；收藏不重置（否则点个收藏就跳回顶部）
   7) 模式写入 localStorage，下次访问沿用
   8) 表格视图下同样分页，且表头「全选」标签写明只覆盖已显示行 */
const fs = require('fs');
const { JSDOM } = require('jsdom');
const html = fs.readFileSync('index.html', 'utf8');
const sleep = ms => new Promise(r => setTimeout(r, ms));
let ok = 0, bad = 0;
const chk = (n, c, extra = '') => { c ? ok++ : bad++; console.log(`${c ? 'PASS' : 'FAIL'}  ${n}${extra ? '  → ' + extra : ''}`); };

function boot(pre) {
  const errs = [];
  const dom = new JSDOM(html, {
    runScripts: 'dangerously', url: 'https://x.test/', pretendToBeVisual: true,
    beforeParse(w) {
      w.matchMedia = w.matchMedia || (q => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {} }));
      w.requestIdleCallback = cb => setTimeout(() => cb({ timeRemaining: () => 8 }), 0);
      w.scrollTo = () => {};
      w.HTMLElement.prototype.scrollIntoView = function () {};
      w.URL.revokeObjectURL = () => {};
      if (pre) pre(w);
      w.addEventListener('error', e => errs.push(String(e.message)));
    }
  });
  return { dom, errs };
}

(async () => {
  const { dom, errs } = boot();
  await sleep(1800);
  const { window } = dom, { document } = window;
  const total = (window.PHONE_DATA || []).length;
  const waitPaint = async () => { for (let i = 0; i < 400; i++) { const g = document.getElementById('phoneGrid'); if (g && g.dataset.painting === '0') break; await sleep(20); } };
  const cards = () => document.querySelectorAll('#phoneGrid .phone-card');
  const info = () => (document.getElementById('pagerInfo') || {}).textContent || '';
  const pagerVisible = () => { const b = document.getElementById('pagerBar'); return !!b && !b.hidden; };
  const btn = k => { const b = document.querySelector(`[data-pager="${k}"]`); return b && !b.hidden ? b : null; };

  /* 1. 默认逐页 */
  chk('结果超过阈值时默认只画一页', cards().length > 0 && cards().length < total, `${cards().length} / ${total} 张`);
  chk('分页条可见', pagerVisible());
  chk('分页条写明已显示与总数', new RegExp(`已显示 ${cards().length} / ${total} 款`).test(info()), info());
  chk('提供「加载更多」与「全部展开」', !!btn('more') && !!btn('all'));
  chk('分页时不显示「改为逐页加载」', !btn('paged'));

  /* 2. 加载更多 = 追加 */
  const firstCard = cards()[0];
  const before = cards().length;
  btn('more').click();
  await sleep(150);
  chk('加载更多后条数增加一页', cards().length > before, `${before} → ${cards().length} 张`);
  chk('已加载卡片未被重建（节点仍在文档里）', firstCard.isConnected && cards()[0] === firstCard);
  chk('分页条同步更新', new RegExp(`已显示 ${cards().length} / ${total} 款`).test(info()), info());

  /* 6a. 收藏不重置分页 */
  const favBtn = cards()[0].querySelector('[data-fav]');
  const keep = cards().length;
  if (favBtn) { favBtn.click(); await sleep(300); await waitPaint(); }
  chk('收藏后仍是已展开的条数（不重置回第一页）', cards().length === keep, `${cards().length} 张`);

  /* 3. 全部展开 */
  btn('all').click();
  await sleep(200); await waitPaint();
  chk('全部展开后拿到全量', cards().length === total, `${cards().length} / ${total} 张`);
  chk('全部展开后文案改为「已展开全部」', /已展开全部/.test(info()), info());
  chk('全部展开后提供「改为逐页加载」', !!btn('paged'));
  chk('全部展开后隐藏「加载更多」', !btn('more'));

  /* 4. 改回逐页 */
  btn('paged').click();
  await sleep(200); await waitPaint();
  chk('改为逐页后回到一页', cards().length > 0 && cards().length < total, `${cards().length} 张`);

  /* 5. 结果不多时不分页 */
  const q = document.getElementById('searchInput');
  q.value = '小米15'; q.dispatchEvent(new window.Event('input', { bubbles: true }));
  await sleep(400); await waitPaint();
  const few = cards().length;
  chk('搜索出少量结果时不分页', few > 0 && few < total && !pagerVisible(), `${few} 张，分页条隐藏=${!pagerVisible()}`);

  /* 6b. 清空搜索 → 回到分页第一页 */
  q.value = ''; q.dispatchEvent(new window.Event('input', { bubbles: true }));
  await sleep(400); await waitPaint();
  chk('清空搜索后回到分页第一页', cards().length > 0 && cards().length < total, `${cards().length} 张`);

  /* 6c. 排序变化 → 回到第一页 */
  btn('more').click(); await sleep(120);
  const expanded = cards().length;
  const sel = document.getElementById('sortSelect');
  sel.value = 'priceAsc'; sel.dispatchEvent(new window.Event('input', { bubbles: true }));
  await sleep(400); await waitPaint();
  chk('换排序后回到第一页', cards().length < expanded, `${expanded} → ${cards().length} 张`);

  /* 8. 表格视图下的分页 */
  document.querySelector('[data-view="table"]').click();
  await sleep(400); await waitPaint();
  const rows = document.querySelectorAll('.phone-table tbody tr').length;
  chk('表格视图同样逐页', rows > 0 && rows < total, `${rows} / ${total} 行`);
  const sa = document.getElementById('selectAllRows');
  chk('表格「全选」标签写明只覆盖已显示行', !!sa && /全选已显示/.test(sa.getAttribute('aria-label') || ''), sa ? sa.getAttribute('aria-label') : '—');
  const moreInTable = btn('more');
  if (moreInTable) { moreInTable.click(); await sleep(200); }
  chk('表格里「加载更多」也能追加行', document.querySelectorAll('.phone-table tbody tr').length > rows,
    `${rows} → ${document.querySelectorAll('.phone-table tbody tr').length} 行`);

  /* 9. 无脚本错误 */
  chk('全程无脚本报错', errs.length === 0, JSON.stringify(errs.slice(0, 3)));

  /* 7. 模式持久化：预置 all 后新实例首屏即全量 */
  const p = boot(w => { try { w.localStorage.setItem('phoneindex.pagemode.v1', 'all'); } catch (e) {} });
  await sleep(1600);
  const w2 = p.dom.window;
  for (let i = 0; i < 400; i++) { const g = w2.document.getElementById('phoneGrid'); if (g && g.dataset.painting === '0') break; await sleep(20); }
  const n2 = w2.document.querySelectorAll('#phoneGrid .phone-card').length;
  chk('记住「全部展开」选择，下次访问首屏即全量', n2 === total, `${n2} / ${total} 张`);

  console.log(`\n${ok} 通过 / ${bad} 失败`);
  process.exit(bad ? 1 : 0);
})();
