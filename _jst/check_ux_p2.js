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
      w.__apiHits = [];
      w.fetch = function (url) {
        if (String(url).includes('/api/')) w.__apiHits.push(String(url));
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

  /* ================= ⑥ 价格口径标签 ================= */
  console.log('\n⑥ 价格口径标签');
  {
    const dom = makeDom();
    await sleep(2300);
    const { window } = dom, doc = window.document;
    const search = async q => {
      const i = doc.getElementById('searchInput');
      i.value = q; i.dispatchEvent(new window.Event('input', { bubbles: true }));
      await sleep(450);
    };
    const labelOf = async (q, id) => {
      await search(q);
      const el = doc.querySelector(`[data-detail="${id}"]`);
      if (!el) return '';
      el.click(); await sleep(800);
      const m = doc.getElementById('detailModal');
      const tag = m.querySelector('.price-tag');
      return tag ? tag.textContent.trim() : '';
    };
    /* 价格只留一个口径：官方起售价。不再按 priceType 分多种标签。 */
    const startLabel = await labelOf('Mate 90 Air', 'hua-mate90air');
    ok(startLabel === '官方起售价', 'official_starting_price 显示「官方起售价」', startLabel);
    const msrpLabel = await labelOf('Mate X8', 'hua-matex8');
    ok(msrpLabel === '官方起售价', 'official_launch_msrp 同样显示「官方起售价」', msrpLabel);
    const noneLabel = await labelOf('iPhone 13', 'apple-13');
    ok(noneLabel === '官方起售价', '第三方参考价机型同样标「官方起售价」，数值位显示未公布', noneLabel);

    /* 字段级「待核验」不再逐行出现，改为顶部一句汇总 */
    const openDetail = async (name, id) => {
      const i = doc.getElementById('searchInput');
      i.value = name; i.dispatchEvent(new window.Event('input', { bubbles: true }));
      await sleep(450);
      const el = doc.querySelector(`[data-detail="${id}"]`);
      if (!el) return null;
      el.click(); await sleep(800);
      return doc.getElementById('detailModal');
    };
    const m1 = await openDetail('iPhone 13', 'apple-13');
    const t1 = m1.textContent.replace(/\s+/g, '');
    ok(!t1.includes('待核验'), '未核验字段不再逐行显示「待核验」');
    ok((m1.querySelector('.price-number') || { textContent: '' }).textContent.trim() === '未公布',
      '没有官方定价时数值位写「未公布」而非破折号');
    ok(!!m1.querySelector('.detail-audit-note'), '改为顶部一句汇总提示',
      (m1.querySelector('.detail-audit-note') || { textContent: '' }).textContent.slice(0, 22));
    m1.querySelector('[data-close]').click(); await sleep(250);

    const m2 = await openDetail('Magic9', 'honor-magic9');
    ok(!m2.querySelector('.detail-audit-note'), '九字段全核验的机型不显示汇总提示');
    dom.window.close();
  }

  /* ================= ⑦ 报价层收缩 ================= */
  console.log('\n⑦ 报价层收缩');
  {
    const dom = makeDom();
    await sleep(2400);
    const { window } = dom, doc = window.document;

    const btn = doc.getElementById('quoteQueryBtn');
    ok(btn && btn.style.display === 'none', '批量查询报价按钮已隐藏', btn ? btn.style.display : '无节点');
    ok(!doc.getElementById('phoneGrid').textContent.includes('未查询'), '卡片不再出现「未查询」占位');

    const st = doc.getElementById('priceApiStatus');
    const stText = st ? st.textContent.replace(/\s+/g, '') : '';
    ok(/当前不提供渠道报价/.test(stText), '状态块改为实话实说', stText.slice(0, 24));
    ok(!/等待服务器响应|连不上服务/.test(stText), '状态块不再显示「等待/连不上」');

    await sleep(200);
    ok(window.__apiHits.length === 0, '首屏后不再探测报价后端', `${window.__apiHits.length} 次请求`);

    /* 透明度区不能还写着「会显示人工快照」——库里唯一的快照缺 SKU 和来源，达不到展示标准 */
    const src = doc.getElementById('sources');
    const srcText = src ? src.textContent.replace(/\s+/g, '') : '';
    ok(!/会显示少量限期的公开商品页人工快照/.test(srcText), '透明度段落不再承诺展示人工快照');
    dom.window.close();
  }

  /* ================= ⑧ 准入样本与推荐面板 ================= */
  console.log('\n⑧ 准入样本');
  {
    const dom = makeDom();
    await sleep(2400);
    const { window } = dom, doc = window.document;
    const ids = ['honor-magic9', 'honor-magic9pm', 'honor-magic9-ultra', 'honor-win2'];

    const cands = window.PhoneEligibility.recommendationCandidates(window.PHONE_DATA || []);
    const gotIds = cands.map(p => p.id);
    ok(ids.every(id => gotIds.includes(id)), '四款样本通过九字段准入', `候选 ${cands.length} 台`);
    ok(cands.every(p => p.auditStatus === 'verified' && p.eligibleForRanking && p.eligibleForRecommendation),
      '准入记录的状态与双资格一致');

    const cardPill = async id => {
      const i = doc.getElementById('searchInput');
      i.value = 'Magic9'; i.dispatchEvent(new window.Event('input', { bubbles: true }));
      await sleep(450);
      const el = doc.querySelector(`[data-detail="${id}"]`);
      return el ? el.closest('.phone-card').querySelector('.audit-pill').textContent.trim() : '';
    };
    ok((await cardPill('honor-magic9')) === '审核通过', '卡片显示「审核通过」');

    /* 默认年份：只有合格样本进入正式推荐；换成 2024（无样本）必须退回参考排序并改口 */
    doc.querySelector('[data-priority="拍照视频"]').click();
    await sleep(120);
    doc.getElementById('applyRecommend').click();
    await sleep(600);
    const box = doc.getElementById('recommendResults');
    const head1 = (box.querySelector('.rec-head') || { textContent: '' }).textContent.replace(/\s+/g, '');
    const n1 = box.querySelectorAll('.rec-card').length;
    /* 两段式：正式候选只装准入样本，参考排序保留全库——否则选什么需求都是同几台 */
    const g1 = box.querySelector('.rec-group');
    const g1Names = g1 ? [...g1.querySelectorAll('h4')].map(h => h.textContent) : [];
    ok(g1 && /正式候选/.test(g1.querySelector('h5').textContent), '第一段是「正式候选」');
    /* 同系列会折叠：展示数 + 折叠数 必须等于准入样本总数，一台都不能凭空消失 */
    const foldN = Number((g1.querySelector('h5 span').textContent.match(/另有\s*(\d+)\s*款/) || [])[1] || 0);
    ok(g1Names.length + foldN === cands.length, '正式候选 = 展示 + 同系列折叠', `${g1Names.length}+${foldN}`);
    ok(g1Names.every(n => cands.some(p => p.name === n)), '展示的都是准入样本');
    ok(box.querySelectorAll('.rec-group').length === 2, '第二段是参考排序');

    const restNames = box.querySelectorAll('.rec-group')[1]
      ? [...box.querySelectorAll('.rec-group')[1].querySelectorAll('h4')].map(h => h.textContent) : [];
    ok(restNames.length > 0 && !restNames.some(n => g1Names.includes(n)), '参考排序不会重复正式候选', `${restNames.length} 款`);

    /* 换一个需求，参考段必须换人——这条直接盯着用户报的 bug */
    doc.querySelector('[data-priority="拍照视频"]').click();
    doc.querySelector('[data-priority="续航"]').click();
    await sleep(100);
    doc.getElementById('applyRecommend').click();
    await sleep(600);
    const rest2 = [...box.querySelectorAll('.rec-group')[1].querySelectorAll('h4')].map(h => h.textContent);
    ok(rest2[0] !== restNames[0], '换需求后参考排序会变化', `${restNames[0]} → ${rest2[0]}`);

    /* 打分要真的分得开：同系列三台的差异在潜望/电池/芯片代际上，
       如果权重只认"最大像素"或芯片名只认英文，这里就会并列或乱序 */
    const topOf = async need => {
      [...doc.querySelectorAll('[data-priority].selected')].forEach(b => b.click());
      await sleep(60);
      doc.querySelector(`[data-priority="${need}"]`).click();
      await sleep(80);
      doc.getElementById('applyRecommend').click();
      await sleep(500);
      const g = box.querySelector('.rec-group h4');
      return g ? g.textContent : '';
    };
    ok(/Pro Max/.test(await topOf('拍照视频')), '拍照首位是潜望长焦那台');
    ok(/WIN2/.test(await topOf('游戏性能')), '游戏首位是第六代骁龙那台');
    ok(/超能版/.test(await topOf('续航')), '续航首位是 11000mAh 那台');

    const yf = doc.getElementById('recYearFrom'), yt = doc.getElementById('recYearTo');
    yf.value = '2024'; yt.value = '2024';
    yf.dispatchEvent(new window.Event('change', { bubbles: true }));
    await sleep(500);
    const foot2 = (box.querySelector('.rec-foot') || { textContent: '' }).textContent.replace(/\s+/g, '');
    ok(!box.querySelector('.rec-group h5')
        || !/正式候选/.test(box.querySelector('.rec-group h5').textContent), '无样本年份不出现正式候选段');
    ok(/该年份区间暂无通过九字段核验的机型/.test(foot2), '无样本年份明确说明原因', foot2.slice(0, 30));

    /* 数据说明里要能直接看到是哪几台通过，否则「3 台」是个无法核对的数字 */
    const notesBtn = [...doc.querySelectorAll('button,a')].find(b => /数据说明/.test(b.textContent));
    notesBtn.click();
    await sleep(400);
    const nt = doc.getElementById('notesModal').textContent.replace(/\s+/g, '');
    ok(new RegExp(`${cands.length}台通过九字段官方核验`).test(nt), '数据说明给出通过台数');
    ok(ids.every(id => {
      const p = (window.PHONE_DATA || []).find(x => x.id === id);
      /* nt 已去掉所有空白，机型名也要同样处理再比，否则「荣耀 Magic9」永远匹配不上 */
      return p && nt.includes(String(p.name).replace(/\s+/g, ''));
    }), '数据说明列出通过机型名称');

    /* 有了准入样本之后，「不输出正式排名」这类旧口径必须改口，否则和面板自相矛盾 */
    ok(!nt.includes('不输出正式排名'), '数据说明不再声称"不输出正式排名"');
    ok(nt.includes('正式候选仅限通过九字段核验'), '数据说明改为"正式候选仅限已核验机型"');
    const disc = doc.querySelector('.recommend-disclaimer');
    ok(disc && /正式候选/.test(disc.textContent), '推荐区免责声明同步改口');
    dom.window.close();
  }

  /* ================= ⑨ 导出只认官方口径 ================= */
  console.log('\n⑨ 导出');
  {
    const dom = makeDom();
    await sleep(2400);
    const { window } = dom, doc = window.document;
    let blob = null;
    window.URL.createObjectURL = b => { blob = b; return 'blob:x'; };
    window.URL.revokeObjectURL = () => {};

    doc.getElementById('exportCatalogBtn').click();
    await sleep(400);
    const csv = blob && blob.text ? await blob.text() : '';
    ok(/官方起售价\(元\)/.test(csv), '导出表头写「官方起售价(元)」');

    /* 列名叫官方起售价，就不能把第三方参考价塞进来：apple-13 是 third_party_reference */
    const line = csv.split('\r\n').find(l => l.startsWith('iPhone 13,'));
    const priceCell = line ? line.split(',')[12] : 'no-row';
    ok(priceCell === '', '第三方参考价机型导出价格留空', `"${priceCell}"`);
    dom.window.close();
  }

  console.log(`\n${pass} 通过 / ${fail} 失败`);
  process.exit(fail ? 1 : 0);
})();
