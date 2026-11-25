/**
 * 体验补丁回归：① 待核机型提示与纳入开关 ② 详情加载失败可重试 ③ 弹层焦点管理。
 *
 * 为什么单独一个文件：这三项都不是"数据对不对"，而是"用户会不会被卡住"——
 * 价格筛选静默吃掉 26% 机型、弱网下详情永远空白、键盘用户 Tab 跑到遮罩后面，
 * 任何一个回退都不报错、只是悄悄变难用，必须靠断言守住。
 *
 * 用法：node _jst/check_ux_p2.js [index.html]
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const HTML = fs.readFileSync(process.argv[2] || 'index.html', 'utf8');
const DETAIL_DIR = path.join(process.cwd(), 'data', 'detail');
const sleep = ms => new Promise(r => setTimeout(r, ms));
let pass = 0, fail = 0;
const ok = (cond, label, extra = '') => {
  if (cond) { pass++; console.log(`  PASS ${label}${extra ? '  → ' + extra : ''}`); }
  else { fail++; console.log(`  FAIL ${label}${extra ? '  → ' + extra : ''}`); }
};

function makeDom(opts = {}) {
  return new JSDOM(HTML, {
    runScripts: 'dangerously', url: 'https://x.test/', pretendToBeVisual: true,
    beforeParse(w) {
      w.matchMedia = w.matchMedia || (q => ({
        matches: false, media: q,
        addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {},
      }));
      w.requestIdleCallback = cb => setTimeout(() => cb({ timeRemaining: () => 8 }), 0);
      w.scrollTo = () => {};
      w.HTMLElement.prototype.scrollIntoView = function () {};
      /* 详情请求可控：failDetail=true 时一律失败，用来模拟弱网 */
      w.fetch = function (url) {
        const m = String(url).match(/data\/detail\/([^/?#]+)\.json/);
        if (!m) return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve(null) });
        if (w.__failDetail) return Promise.reject(new Error('offline'));
        try {
          const d = JSON.parse(fs.readFileSync(path.join(DETAIL_DIR, decodeURIComponent(m[1]) + '.json'), 'utf8'));
          return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(d) });
        } catch (e) {
          return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve(null) });
        }
      };
    },
  });
}

(async () => {
  /* ================= ① 未知值提示 ================= */
  console.log('\n① 待核机型提示');
  {
    const dom = makeDom();
    await sleep(2300);
    const { window } = dom, doc = window.document;
    const cnt = () => Number(doc.getElementById('resultCount').textContent);
    const hintEl = doc.getElementById('unknownHint');

    ok(hintEl && hintEl.hidden, '未开筛选时不显示提示');

    const mn = doc.getElementById('priceMin'), mx = doc.getElementById('priceMax');
    mn.value = '3000'; mn.dispatchEvent(new window.Event('input', { bubbles: true }));
    mx.value = '4000'; mx.dispatchEvent(new window.Event('input', { bubbles: true }));
    await sleep(400);

    const base = cnt();
    const shown = hintEl && !hintEl.hidden;
    const num = shown ? Number((hintEl.textContent.match(/(\d+)\s*台/) || [])[1]) : 0;
    ok(shown, '设价格区间后出现提示', hintEl ? hintEl.textContent.trim().slice(0, 40) : '无节点');
    ok(num > 0, '提示里给出了被挡掉的台数', String(num));

    const btn = hintEl.querySelector('button');
    btn.click();
    await sleep(400);
    ok(cnt() === base + num, '点「一并纳入」后结果数正好加上该台数', `${base} + ${num} → ${cnt()}`);
    ok(/已纳入/.test(hintEl.textContent) && hintEl.querySelector('button'), '纳入后仍可撤销');

    hintEl.querySelector('button').click();
    await sleep(400);
    ok(cnt() === base, '点「只看有数据的」后回到原结果数', String(cnt()));
    dom.window.close();
  }

  /* ================= ② 详情失败可重试 ================= */
  console.log('\n② 详情加载失败与重试');
  {
    const dom = makeDom();
    await sleep(2300);
    const { window } = dom, doc = window.document;
    window.__failDetail = true;                     // 先让所有详情请求失败

    const first = doc.querySelector('#phoneGrid [data-detail]');
    const id = first.getAttribute('data-detail');
    first.click();
    await sleep(900);

    const modal = doc.getElementById('detailModal');
    ok(modal && !modal.hidden, '弱网下详情仍能打开（不卡死）');
    const retry = modal.querySelector('[data-dl-retry]');
    ok(!!retry, '出现「重新载入规格」按钮');

    window.__failDetail = false;                    // 网络恢复
    retry.click();
    await sleep(900);
    const groups = doc.querySelectorAll('#detailModal .spec-group').length;
    ok(groups > 0, '点重试后规格成功渲染', `${groups} 组`);
    ok(!doc.querySelector('#detailModal [data-dl-retry]'), '成功后重试按钮消失', id);
    dom.window.close();
  }

  /* ================= ③ 弹层焦点 ================= */
  console.log('\n③ 弹层焦点管理');
  {
    const dom = makeDom();
    await sleep(2300);
    const { window } = dom, doc = window.document;
    const trigger = doc.querySelector('#phoneGrid [data-detail]');
    trigger.focus();
    trigger.click();
    await sleep(700);

    const modal = doc.getElementById('detailModal');
    const inside = modal.contains(doc.activeElement);
    ok(inside, '打开后焦点进入弹层', doc.activeElement.className || doc.activeElement.tagName);

    /* 把焦点放到最后一个可聚焦元素，按 Tab 应回到第一个（不跑出弹层） */
    const sel = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';
    const items = [...modal.querySelectorAll(sel)].filter(el => !el.hasAttribute('hidden') && !el.closest('[hidden]'));
    const lastEl = items[items.length - 1], firstEl = items[0];
    lastEl.focus();
    doc.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Tab', bubbles: true }));
    ok(doc.activeElement === firstEl, 'Tab 从最后一项回到第一项（焦点不逃出弹层）');

    doc.getElementById('detailModal').querySelector('[data-close]').click();
    await sleep(300);
    ok(doc.activeElement === trigger, '关闭后焦点回到触发按钮');
    dom.window.close();
  }

  /* ================= ④ 输入防抖与列表一致性 ================= */
  console.log('\n④ 输入防抖 / 列表一致性');
  {
    const dom = makeDom();
    await sleep(2300);
    const { window } = dom, doc = window.document;
    const cnt = () => Number(doc.getElementById('resultCount').textContent);
    const total = cnt();

    const yf = doc.getElementById('yearFrom');
    yf.value = '2024'; yf.dispatchEvent(new window.Event('input', { bubbles: true }));
    await sleep(60);
    yf.value = '2025'; yf.dispatchEvent(new window.Event('input', { bubbles: true }));  // 连打两位
    await sleep(450);                                                    // 等防抖落地
    const after = cnt();
    ok(after < total && after > 0, '年份输入防抖后仍正确生效', `${total} → ${after}`);

    /* 列表与计数必须一致：签名算错时会出现「计数变了但卡片没换」的假象 */
    const cards = doc.querySelectorAll('#phoneGrid .phone-card').length;
    const shown = Math.min(Number(doc.getElementById('resultCount').textContent), 24);
    ok(cards === shown, '首屏卡片数与「应显示数」严格相等', `${cards} 张 / 期望 ${shown}`);
    dom.window.close();
  }

  /* ================= ⑤ 全局错误兜底 ================= */
  console.log('\n⑤ 运行时错误兜底');
  {
    const dom = makeDom();
    await sleep(2300);
    const { window } = dom, doc = window.document;
    const toastEl = doc.getElementById('toast');
    window.dispatchEvent(new window.Event('error'));
    await sleep(200);
    ok(toastEl && /没成功|刷新/.test(toastEl.textContent), '脚本异常时给出可见提示', toastEl ? toastEl.textContent.trim() : '无 toast 节点');
    dom.window.close();
  }

  console.log(`\n${pass} 通过 / ${fail} 失败`);
  process.exit(fail ? 1 : 0);
})();
