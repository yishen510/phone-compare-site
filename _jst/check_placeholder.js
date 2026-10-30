/**
 * 防回归：页面上不能出现「整个字段值就是占位文案」的情况。
 *
 * 起因：占位措辞有多个变体（以官方页面为准 / 以官方大陆版页面为准 …），
 * 扫描只认「以官方规格页为准」一种，导致 62 条占位值被当正常值显示。
 *
 * 判定范围只限「整段取值等于占位文案」；「麒麟 9030 系列（以官方型号页为准）」
 * 这类「正常值 + 括号限定」属于正常表述，不算漏网。
 */
const fs = require('fs');
const { JSDOM } = require('jsdom');

const H = fs.readFileSync(process.argv[2] || 'index.html', 'utf8');
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
// 与前端 PLACEHOLDER_RE 一致：整段取值命中才算占位
const WHOLE = /^(以.{0,12}为准|.{0,6}(待核验|待录入|暂缺|未公布|未收录).{0,8}|.{0,4}待复核.{0,6})$/;
const FIELDS = ['display', 'chip', 'camera', 'battery', 'charging', 'weight', 'storage', 'os'];

(async () => {
  await sleep(1500);
  const { document } = dom.window;
  const settle = async () => {
    for (let i = 0; i < 150; i++) {
      const g = document.getElementById('phoneGrid');
      if (g && g.dataset.painting === '0') return;
      await sleep(30);
    }
  };
  await settle();

  const data = dom.window.PHONE_DATA || [];
  // 1) 数据层：还有哪些取值本身就是占位文案
  const ph = [];
  for (const p of data) {
    for (const k of FIELDS) {
      const v = String(p[k] || '').trim();
      if (v && WHOLE.test(v)) ph.push({ id: p.id, name: p.name, field: k, text: v });
    }
  }
  console.log(`数据层占位取值 ${ph.length} 处（这些在页面上应被渲染成「缺失说明」而非原文）`);

  const problems = [];
  const has = (text, needle) => text.includes(needle);

  // 2) 卡片 / 表格：占位原文不能出现
  for (const view of ['grid', 'table']) {
    const btn = document.querySelector(`[data-view="${view}"]`);
    if (btn) { btn.click(); await sleep(500); await settle(); }
    const nodes = [...document.querySelectorAll('#phoneGrid .phone-card, #phoneGrid tbody tr')];
    for (const n of nodes) {
      const t = n.textContent.replace(/\s+/g, ' ');
      for (const x of ph) {
        // 只有当这张卡片/这行确实属于该机型时，出现占位原文才算问题
        if (t.includes(x.name) && has(t, x.text)) {
          problems.push(`[${view}] ${x.name} ${x.field}: 显示原文「${x.text}」`);
        }
      }
    }
    console.log(`  ${view} 视图扫描 ${nodes.length} 条`);
  }

  // 3) 详情：对每条占位机型逐个打开确认
  const ids = [...new Set(ph.map(x => x.id))];
  for (const id of ids) {
    const btn = document.querySelector(`#phoneGrid [data-detail="${id}"]`) || document.querySelector(`[data-detail="${id}"]`);
    if (!btn) continue;
    btn.click();
    await sleep(45);
    const modal = document.querySelector('#detailModal');
    const t = modal ? modal.textContent.replace(/\s+/g, ' ') : '';
    for (const x of ph.filter(y => y.id === id)) {
      if (has(t, x.text)) problems.push(`[详情 ${x.name}] ${x.field}: 显示原文「${x.text}」`);
    }
    document.querySelector('[data-close]')?.click();
    await sleep(25);
  }
  console.log(`  详情扫描 ${ids.length} 台`);

  if (problems.length) {
    console.log(`\n发现 ${problems.length} 处占位原文漏网：`);
    [...new Set(problems)].slice(0, 15).forEach(x => console.log('   ' + x));
  } else {
    console.log('\n0 处占位原文漏网');
  }
  console.log(`脚本错误 ${errs.length}`);
  process.exit(problems.length || errs.length ? 1 : 0);
})();

function escapeRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
