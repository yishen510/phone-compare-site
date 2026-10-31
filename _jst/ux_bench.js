/**
 * 体验基准：真实 Edge（CPU 4× 降速 + 移动端视口）测关键交互耗时。
 * 用法：node _jst/ux_bench.js [--desktop]
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const WebSocket = require('ws');

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const MOBILE = !process.argv.includes('--desktop');
const FILE = path.resolve('index.html');
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
  await call('Page.navigate', { url: 'file:///' + FILE.replace(/\\/g, '/') });
  await ev(`new Promise(r=>{const t=setInterval(()=>{const g=document.getElementById('phoneGrid');
    if(g&&g.dataset.painting==='0'){clearInterval(t);r(1);}},30)})`);
  console.log(`  首屏到卡片画完            ${String(Date.now() - t0).padStart(5)} ms`);

  // 2) 切到表格视图（442 行一次性渲染）
  const t1 = Date.now();
  await ev(`(()=>{const b=document.querySelector('[data-view="table"]');if(b)b.click();})()`);
  await ev(`new Promise(r=>{const t=setInterval(()=>{const n=document.querySelectorAll('#phoneGrid tbody tr').length;
    if(n>0){clearInterval(t);r(n);}},30)})`);
  console.log(`  切换到表格视图            ${String(Date.now() - t1).padStart(5)} ms`);

  // 3) 表格排序
  const t2 = Date.now();
  await ev(`(()=>{const th=document.querySelector('#phoneGrid th[data-sort-col]');if(th)th.click();})()`);
  await ev(`new Promise(r=>{setTimeout(()=>r(1),50)})`);
  await ev(`new Promise(r=>{const t=setInterval(()=>{const g=document.getElementById('phoneGrid');
    if(g&&g.dataset.painting==='0'){clearInterval(t);r(1);}},30)})`);
  console.log(`  表格点击排序              ${String(Date.now() - t2).padStart(5)} ms`);

  // 4) 搜索往返（含 200ms 防抖）
  await ev(`(()=>{const b=document.querySelector('[data-view="grid"]');if(b)b.click();})()`);
  await sleep(300);
  const t3 = Date.now();
  await ev(`(()=>{const i=document.getElementById('searchInput');i.value='骁龙';
    i.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await ev(`new Promise(r=>{const t=setInterval(()=>{const g=document.getElementById('phoneGrid');
    if(g&&g.dataset.painting==='0'){clearInterval(t);r(1);}},30)})`);
  console.log(`  搜索「骁龙」到结果画完    ${String(Date.now() - t3).padStart(5)} ms（含 200ms 防抖）`);

  // 5) 清空搜索恢复 442 张
  const t4 = Date.now();
  await ev(`(()=>{const i=document.getElementById('searchInput');i.value='';
    i.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await ev(`new Promise(r=>{const t=setInterval(()=>{const g=document.getElementById('phoneGrid');
    if(g&&g.dataset.painting==='0'){clearInterval(t);r(1);}},30)})`);
  console.log(`  清空搜索恢复全部          ${String(Date.now() - t4).padStart(5)} ms（含 200ms 防抖）`);

  // 6) 资源体积
  const sz = fs.statSync(FILE).size;
  console.log(`  index.html 体积           ${(sz / 1024 / 1024).toFixed(2)} MB`);
  ws.close(); child.kill(); process.exit(0);
})();
