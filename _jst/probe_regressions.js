/**
 * 拆分详情数据（data/detail/*.json）之后引入的两个回归，用运行时探针守住。
 *
 * 背景：规格与逐字段溯源从首屏拆成按需文件后，
 *  1) specHay() 在 specs 未加载时把空串写进 SPEC_HAY，warmSearchIndex 首屏给 488 台全写了一遍
 *     → 全库规格搜索永久失效（只在 card 字段里出现的词还能搜到，掩盖了问题）
 *  2) dataSummary() 直接读 p.specs，首屏未加载 → 「数据说明」面板显示「有完整参数 0」
 *
 * 用法：node _jst/probe_regressions.js [index.html]
 * 退出码非 0 表示有回归。
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const HTML = fs.readFileSync(process.argv[2] || 'index.html', 'utf8');
const DETAIL_DIR = path.join(process.cwd(), 'data', 'detail');

/* 只统计详情文件里真实含该词的机型数，作为期望值 */
function expectedCount(term) {
  if (!fs.existsSync(DETAIL_DIR)) return null;
  let n = 0;
  for (const f of fs.readdirSync(DETAIL_DIR)) {
    if (!f.endsWith('.json')) continue;
    try {
      const d = JSON.parse(fs.readFileSync(path.join(DETAIL_DIR, f), 'utf8'));
      if (JSON.stringify(d.specs || []).includes(term)) n++;
    } catch (e) { /* 坏文件跳过，别让探针自己崩 */ }
  }
  return n;
}

const dom = new JSDOM(HTML, {
  runScripts: 'dangerously', url: 'https://x.test/', pretendToBeVisual: true,
  beforeParse(w) {
    w.matchMedia = w.matchMedia || (q => ({
      matches: false, media: q,
      addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {},
    }));
    w.requestIdleCallback = cb => setTimeout(() => cb({ timeRemaining: () => 8 }), 0);
    w.scrollTo = () => {};
    w.HTMLElement.prototype.scrollIntoView = function () {};
    /* 故意不给 fetch：模拟首访 / 弱网，详情一个都拉不到。
       这正是回归暴露的条件——如果实现正确，搜索不该因此失效。 */
    w.fetch = () => Promise.reject(new Error('offline'));
  },
});

const sleep = ms => new Promise(r => setTimeout(r, ms));
let failed = 0;

(async () => {
  await sleep(2500);                       // 等首屏 warmSearchIndex 跑完
  const w = dom.window, doc = w.document;

  /* —— 检查 1：规格专有词能否搜到 —— */
  const type = async term => {
    const i = doc.getElementById('searchInput');
    i.value = term;
    i.dispatchEvent(new w.Event('input', { bubbles: true }));
    await sleep(320);
    return Number(doc.getElementById('resultCount').textContent);
  };
  for (const term of ['IP68', 'LTPO', '超声波']) {
    const got = await type(term);
    const want = expectedCount(term);
    const ok = want === null ? got > 0 : got >= Math.ceil(want * 0.95);
    if (!ok) failed++;
    console.log(`${ok ? 'PASS' : 'FAIL'} 搜「${term}」→ ${got} 条（规格库 ${want === null ? '?' : want} 台）`);
  }

  /* —— 检查 2：数据说明面板的统计值 —— */
  doc.getElementById('dataNotesBtn')?.click();
  await sleep(400);
  const modal = doc.getElementById('notesModal');
  const text = (modal && modal.textContent || '').replace(/\s+/g, ' ');
  const m = text.match(/有完整参数\s*(\d+)/);
  const mi = text.match(/参数条目\s*(\d+)/);
  const withSpecs = m ? Number(m[1]) : -1;
  const items = mi ? Number(mi[1]) : -1;
  const ok2 = withSpecs > 0 && items > 0;
  if (!ok2) failed++;
  console.log(`${ok2 ? 'PASS' : 'FAIL'} 数据说明「有完整参数」= ${withSpecs}、「参数条目」= ${items}（都应 > 0）`);

  /* —— 检查 3：按特征命中时，结果标签要解释原因 —— */
  modal?.querySelector('[data-close]')?.click();
  await sleep(200);
  const label = async t => { await type(t); return (doc.getElementById('currentFilterLabel').textContent || '').trim(); };
  const labFeat = await label('IP68');
  const labName = await label('小米');
  const ok3 = labFeat.includes('含「IP68」') && !labName.includes('含「');
  if (!ok3) failed++;
  console.log(`${ok3 ? 'PASS' : 'FAIL'} 搜「IP68」标签="${labFeat}"；搜「小米」标签="${labName}"`);

  dom.window.close();
  console.log(`\n${failed ? failed + ' 项回归' : '全部通过'}`);
  process.exit(failed ? 1 : 0);
})();
