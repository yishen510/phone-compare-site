/**
 * 体验基准：真实 Edge（CPU 4× 降速 + 移动端视口）测关键交互耗时。
 * 用法：node _jst/ux_bench.js [--desktop] [文件路径]
 *   默认测工作区 index.html；传第二个文件名可做 A/B（如 _jst/_baseline_index.html）
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const WebSocket = require('ws');

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const MOBILE = !process.argv.includes('--desktop');
const TARGET = process.argv.slice(2).find(a => !a.startsWith('--')) || 'index.html';
const FILE = path.resolve(TARGET);
const PORT = 9400 + Math.floor(Math.random() * 200);
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'edgeux-'));
const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  '--window-size=1440,900', 'about:blank',
], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function target() {
  for (let i = 0; i < 80; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      const p = list.find(t => t.type === 'page');
      if (p && p.webSocketDebuggerUrl) return p.webSocketDebuggerUrl;
    } catch (e) {}
    await sleep(250);
  }
  throw new Error('CDP 未就绪');
}
let seq = 0;
const rpc = (ws, id, m, p) => new Promise((res, rej) => {
  const on = raw => { const x = JSON.parse(raw); if (x.id === id) { ws.off('message', on); res(x.result); } };
  ws.on('message', on);
  ws.send(JSON.stringify({ id, method: m, params: p || {} }));
  setTimeout(() => rej(new Error('timeout ' + m)), 60000);
});

(async () => {
  const ws = new WebSocket(await target());
  await new Promise(r => ws.on('open', r));
  const call = (m, p) => rpc(ws, ++seq, m, p);
  await call('Page.enable'); await call('Runtime.enable');
  if (MOBILE) {
    await call('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
    await call('Emulation.setCPUThrottlingRate', { rate: 4 });
  }
  const ev = async expr => {
    const r = await call('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    return r && r.result ? r.result.value : null;
  };
  console.log(MOBILE ? '【移动端模拟：390×844，CPU 4× 降速】' : '【桌面端：1440×900】');

  // 1) 首屏
  const t0 = Date.now();
  await call('Performance.enable');
  await call('Page.navigate', { url: 'file:///' + FILE.replace(/\\/g, '/') });
  /* 首张卡片出现 = 用户真正「看到内容」的时刻，比 painting=0（全部画完）更贴近感知 */
  await ev(`new Promise(r=>{const t=setInterval(()=>{const g=document.getElementById('phoneGrid');
    if(g&&g.querySelector('.phone-card')){clearInterval(t);r(1);}},10)})`);
  const tFirst = Date.now() - t0;
  await ev(`new Promise(r=>{const t=setInterval(()=>{const g=document.getElementById('phoneGrid');
    if(g&&g.dataset.painting==='0'){clearInterval(t);r(1);}},30)})`);
  console.log(`  首屏首张卡片可见          ${String(tFirst).padStart(5)} ms`);
  console.log(`  首屏到卡片画完            ${String(Date.now() - t0).padStart(5)} ms`);
  /* 真实渲染成本：painting=0 只代表 JS 插完 DOM，布局/样式重算才是浏览器侧大头 */
  try {
    const mt = (await call('Performance.getMetrics')).metrics || [];
    const gv = n => { const x = mt.find(i => i.name === n); return x ? x.value : 0; };
    console.log(`  首屏累计 Layout ${(gv('LayoutDuration')*1000).toFixed(0)}ms · RecalcStyle ${(gv('RecalcStyleDuration')*1000).toFixed(0)}ms · Script ${(gv('ScriptDuration')*1000).toFixed(0)}ms`);
  } catch (e) {}

  // 2) 切到表格视图（实测：一次渲染全部行）
  /* 页面内计时：从点击到 painting==='0' 都在渲染进程里量，
     不受 CDP 往返（几十 ms）干扰。否则同步完成的路径会被测成「往返延迟」。 */
  const inPage = (action, after) => ev(`new Promise(r=>{
    const g=document.getElementById('phoneGrid');
    const t0=performance.now();
    (${action})();
    const step=()=>{ if(${after}){r(performance.now()-t0);} else requestAnimationFrame(step); };
    step();
  })`);
  const tTable = await inPage(`()=>{const b=document.querySelector('[data-view="table"]');if(b)b.click();}`,
    `document.querySelectorAll('#phoneGrid tbody tr').length>0&&g.dataset.painting==='0'`);
  console.log(`  切换到表格视图            ${tTable.toFixed(0).padStart(5)} ms`);

  // 3) 表格排序
  const tSort = await inPage(`()=>{const th=document.querySelector('#phoneGrid th[data-sort-col]');if(th)th.click();}`,
    `g.dataset.painting==='0'`);
  console.log(`  表格点击排序              ${tSort.toFixed(0).padStart(5)} ms`);

  // 4) 搜索往返（含 200ms 防抖）
  /* 注意：只等 painting==='0' 会测到「上一轮渲染还停在那里」的假结果——
     防抖还没触发渲染，painting 本来就是 0。必须先等结果条数真的变了。 */
  /* 另：切回卡片视图的按钮是 data-view="cards"，旧版这里写成 "grid"（选择器不存在），
     导致步骤 4/5 一直在表格视图下测量。已改正，故这两个数字与旧报告不可比。 */
  await ev(`(()=>{const b=document.querySelector('[data-view="cards"]');if(b)b.click();})()`);
  await sleep(300);
  const total = await ev(`window.PHONE_DATA.length`);
  const waitCount = n => ev(`new Promise(r=>{const t=setInterval(()=>{const c=document.getElementById('resultCount');
    if(c&&c.textContent==='${n}'){clearInterval(t);r(1);}},20)})`);
  const t3 = Date.now();
  await ev(`(()=>{const i=document.getElementById('searchInput');i.value='骁龙';
    i.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await ev(`new Promise(r=>{const t=setInterval(()=>{const c=document.getElementById('resultCount');
    if(c&&c.textContent!=='${total}'){clearInterval(t);r(c.textContent);}},20)})`);
  await ev(`new Promise(r=>{const t=setInterval(()=>{const g=document.getElementById('phoneGrid');
    if(g&&g.dataset.painting==='0'){clearInterval(t);r(1);}},20)})`);
  console.log(`  搜索「骁龙」到结果画完    ${String(Date.now() - t3).padStart(5)} ms（含 200ms 防抖）`);

  // 5) 清空搜索恢复全部
  const t4 = Date.now();
  await ev(`(()=>{const i=document.getElementById('searchInput');i.value='';
    i.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await waitCount(total);
  await ev(`new Promise(r=>{const t=setInterval(()=>{const g=document.getElementById('phoneGrid');
    if(g&&g.dataset.painting==='0'){clearInterval(t);r(1);}},20)})`);
  console.log(`  清空搜索恢复全部          ${String(Date.now() - t4).padStart(5)} ms（含 200ms 防抖）`);

  // 6) 逐页展示：「加载更多」一页的成本 + 「全部展开」的成本（成本是被推迟，不是被消灭）
  const pager = await ev(`(()=>{const m=document.querySelector('[data-pager="more"]'),a=document.querySelector('[data-pager="all"]');
    return JSON.stringify({more:!!(m&&!m.hidden),all:!!(a&&!a.hidden)});})()`);
  let pagerState = { more: false, all: false };
  try { pagerState = JSON.parse(pager || '{}'); } catch (e) {}
  if (pagerState.more) {
    /* 「加载更多」不触发 paintGrid，painting 一直是 0，只能用同步计时 */
    const tm = await inPage(`()=>{const b=document.querySelector('[data-pager="more"]');if(b)b.click();}`, `true`);
    console.log(`  点「加载更多」追加一页    ${tm.toFixed(0).padStart(5)} ms（追加，不重建已加载卡片）`);
  }
  if (pagerState.all) {
    const ta = await inPage(`()=>{const b=document.querySelector('[data-pager="all"]');if(b)b.click();}`, `g.dataset.painting==='0'`);
    console.log(`  点「全部展开」到画完      ${ta.toFixed(0).padStart(5)} ms（用户显式要求时才付这份成本）`);
  }

  // 7) 资源体积
  const sz = fs.statSync(FILE).size;
  console.log(`  index.html 体积           ${(sz / 1024 / 1024).toFixed(2)} MB`);
  ws.close(); child.kill(); process.exit(0);
})();
