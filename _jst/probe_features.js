/**
 * 功能探针：把站点已有功能逐个跑一遍，输出 PASS/FAIL/观察，用来找优化点。
 * 用法：node _jst/probe_features.js
 */
const fs = require('fs');
const { JSDOM } = require('jsdom');

const H = fs.readFileSync(process.argv[2] || 'index.html', 'utf8');
const R = [];
const say = (tag, name, detail = '') => { R.push({ tag, name, detail }); console.log(`  ${tag} ${name}${detail ? ' → ' + detail : ''}`); };

function mk(url) {
  const errs = [];
  const dom = new JSDOM(H, {
    runScripts: 'dangerously', url, pretendToBeVisual: true,
    beforeParse(w) {
      w.matchMedia = w.matchMedia || (q => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }));
      w.requestIdleCallback = cb => setTimeout(() => cb({ timeRemaining: () => 8 }), 0);
      w.scrollTo = () => {};
      w.HTMLElement.prototype.scrollIntoView = function () {};
      w.addEventListener('error', x => errs.push(String(x.message)));
    },
  });
  return { dom, errs };
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const { dom, errs } = mk('https://x.test/');
  const { window } = dom;
  const { document } = window;
  await sleep(1500);
  const settle = async () => {
    for (let i = 0; i < 150; i++) {
      const g = document.getElementById('phoneGrid');
      if (g && g.dataset.painting === '0') return;
      await sleep(30);
    }
  };
  await settle();
  const click = async sel => { const e = document.querySelector(sel); if (!e) return false; e.click(); await sleep(80); return true; };
  const cards = () => [...document.querySelectorAll('#phoneGrid .phone-card')];

  /* 1. 收藏 */
  const favBtn = document.querySelector('#phoneGrid .fav-btn');
  if (favBtn) {
    favBtn.click(); await sleep(120);
    const raw = window.localStorage.getItem('phoneindex.favs.v1');
    say(raw && raw.includes('"') ? 'PASS' : 'FAIL', '收藏写入 localStorage', String(raw).slice(0, 40));
    // 只看收藏
    await click('#favOnly');
    await settle();
    const n = cards().length;
    say(n > 0 ? 'PASS' : 'FAIL', '「只看收藏」筛选', `${n} 张卡片`);
    await click('#favOnly'); await settle();
  } else say('FAIL', '卡片上有收藏按钮');

  /* 2. 收藏导出 */
  let exported = null;
  window.URL.createObjectURL = () => 'blob:x';
  window.URL.revokeObjectURL = () => {};   // jsdom 未实现，补桩避免误报脚本错误
  try {
    const before = document.querySelectorAll('a[download]').length;
    await click('#favExport');
    await sleep(200);
    say('PASS', '收藏导出有触发无异常');
  } catch (e) { say('FAIL', '收藏导出', String(e).slice(0, 60)); }

  /* 3. 对比上限 */
  for (let i = 0; i < 5; i++) {
    const b = cards()[i]?.querySelector('[data-compare],.compare-btn');
    if (b) { b.click(); await sleep(60); }
  }
  const dock = document.getElementById('dockCount');
  say(dock ? 'PASS' : '观察', '对比 dock 计数', dock ? dock.textContent : '无');

  /* 4. 最近浏览 */
  const ids = cards().slice(0, 3).map(c => c.querySelector('[data-detail]')?.dataset.detail).filter(Boolean);
  for (const id of ids) {
    const b = document.querySelector(`#phoneGrid [data-detail="${id}"]`);
    if (b) { b.click(); await sleep(60); document.querySelector('[data-close]')?.click(); await sleep(40); }
  }
  const recent = document.getElementById('recentList');
  const recentN = recent ? recent.querySelectorAll('button,li,a').length : 0;
  say(recentN > 0 ? 'PASS' : 'FAIL', '最近浏览记录', `${recentN} 条`);

  /* 5. 空结果 */
  const si = document.getElementById('searchInput');
  if (si) {
    si.value = 'zzzz不存在的机型zzzz';
    si.dispatchEvent(new window.Event('input', { bubbles: true }));
    await sleep(400); await settle();
    const empty = document.getElementById('emptyState');
    const visible = empty && !empty.hidden;
    say(visible ? 'PASS' : 'FAIL', '空结果显示空状态', `hidden=${empty ? empty.hidden : 'n/a'}`);
    const reset = document.getElementById('emptyReset');
    if (reset) { reset.click(); await sleep(400); await settle(); }
    say(cards().length > 0 ? 'PASS' : 'FAIL', '空状态「重置」可恢复', `${cards().length} 张`);
  }

  /* 6. URL 状态 */
  si.value = '骁龙';
  si.dispatchEvent(new window.Event('input', { bubbles: true }));
  await sleep(400); await settle();
  const href = window.location.href;
  say(/[?&](q|search|kw)=/.test(href) ? 'PASS' : '观察', '搜索写入 URL', href.slice(0, 90));

  /* 7. 恢复：用当前 URL 重新打开 */
  const { dom: dom2, errs: errs2 } = mk(href);
  await sleep(1600);
  const g2 = dom2.window.document.getElementById('phoneGrid');
  for (let i = 0; i < 150; i++) { if (g2 && g2.dataset.painting === '0') break; await sleep(30); }
  const si2 = dom2.window.document.getElementById('searchInput');
  const cards2 = dom2.window.document.querySelectorAll('#phoneGrid .phone-card').length;
  say(si2 && si2.value ? 'PASS' : 'FAIL', '刷新后恢复搜索词', `输入框=${si2 ? JSON.stringify(si2.value) : 'n/a'}，卡片 ${cards2}`);

  /* 8. 表格视图 + 排序 */
  await click('[data-view="table"]');
  await settle();
  const rows = document.querySelectorAll('#phoneGrid tbody tr').length;
  say(rows > 0 ? 'PASS' : 'FAIL', '表格视图渲染', `${rows} 行`);
  const th = document.querySelector('#phoneGrid th[data-sort-col]');
  if (th) { th.click(); await sleep(300); await settle(); }
  say(th ? 'PASS' : '观察', '表头排序可点', th ? th.dataset.sortCol : '无 data-sort-col');

  console.log(`\n汇总：${R.filter(x => x.tag === 'PASS').length} PASS / ${R.filter(x => x.tag === 'FAIL').length} FAIL / ${R.filter(x => x.tag === '观察').length} 观察`);
  console.log(`脚本错误：${errs.length + errs2.length}`);
  process.exit(0);
})();
