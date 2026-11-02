/**
 * 滚动帧率基准：模拟手指连续滚动，采每帧间隔，看有没有掉帧。
 *
 * 为什么要单独测：毛玻璃（backdrop-filter）的成本不在 Layout/Script 指标里，
 * 而是每一帧都要重新采样背景并模糊——只有滚动时用 rAF 采样才看得见。
 *
 * 用法：node _jst/scroll_bench.js <url> [--desktop]
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const WebSocket = require('ws');

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const args = process.argv.slice(2).filter(a => !a.startsWith('--'));
const URL_ = args[0] || 'http://127.0.0.1:8815/index.html';
const DESKTOP = process.argv.includes('--desktop');
const PORT = 9700 + Math.floor(Math.random() * 120);
const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'scroll-'));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${prof}`, '--window-size=1440,900', 'about:blank'],
  { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let seq = 0;
const rpc = (ws, id, m, p) => new Promise((res, rej) => {
  const on = raw => { const x = JSON.parse(raw); if (x.id === id) { ws.off('message', on); res(x.result); } };
  ws.on('message', on);
  ws.send(JSON.stringify({ id, method: m, params: p || {} }));
  setTimeout(() => rej(new Error('timeout ' + m)), 90000);
});

(async () => {
  let u = null;
  for (let i = 0; i < 80 && !u; i++) {
    try {
      const l = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      const p = l.find(t => t.type === 'page');
      if (p) u = p.webSocketDebuggerUrl;
    } catch (e) {}
    if (!u) await sleep(250);
  }
  const ws = new WebSocket(u);
  await new Promise(r => ws.on('open', r));
  const call = (m, p) => rpc(ws, ++seq, m, p);
  const ev = async e => {
    const r = await call('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true });
    return r && r.result ? r.result.value : null;
  };

  await call('Page.enable'); await call('Runtime.enable');
  await call('Emulation.setDeviceMetricsOverride',
    { width: DESKTOP ? 1280 : 390, height: DESKTOP ? 900 : 844, deviceScaleFactor: DESKTOP ? 1 : 2, mobile: !DESKTOP });
  await call('Emulation.setCPUThrottlingRate', { rate: 4 });
  await call('Page.navigate', { url: URL_ });
  await ev(`new Promise(r=>{const t0=performance.now();const t=setInterval(()=>{const g=document.getElementById('phoneGrid');
    if((g&&g.dataset.painting==='0'&&g.querySelector('.phone-card'))||performance.now()-t0>20000){clearInterval(t);r(1);}},40)})`);
  await sleep(1200);

  /* 连续滚 3 秒，逐帧记录间隔。用原生滚动（scrollBy）而不是动画，避免把动画成本算进来。 */
  const res = await ev(`new Promise(resolve=>{
    const se=document.scrollingElement||document.documentElement;
    se.scrollTop=0;
    const frames=[]; let last=performance.now(); let stop=false;
    const tick=()=>{const now=performance.now();frames.push(now-last);last=now;if(!stop)requestAnimationFrame(tick);};
    requestAnimationFrame(tick);
    let step=0;
    const iv=setInterval(()=>{
      se.scrollTop += 60; step++;
      if(step>50){stop=true;clearInterval(iv);
        frames.shift();
        const sorted=[...frames].sort((a,b)=>a-b);
        const pct=p=>sorted[Math.min(sorted.length-1,Math.floor(sorted.length*p))];
        resolve(JSON.stringify({frames:frames.length,
          avg:+(frames.reduce((a,b)=>a+b,0)/frames.length).toFixed(1),
          p50:+pct(.5).toFixed(1), p95:+pct(.95).toFixed(1), max:+sorted[sorted.length-1].toFixed(1),
          over32:frames.filter(f=>f>32).length, over50:frames.filter(f=>f>50).length}));
      }
    },16);
  })`);
  const r = JSON.parse(res);
  const fps = (1000 / r.avg).toFixed(0);
  console.log(`【${DESKTOP ? '桌面 1280' : '移动 390'} · CPU×4】 ${URL_}`);
  console.log(`  采样帧数 ${r.frames}  平均 ${r.avg}ms (≈${fps}fps)`);
  console.log(`  p50 ${r.p50}ms   p95 ${r.p95}ms   最长 ${r.max}ms`);
  console.log(`  掉帧(>32ms) ${r.over32} 帧，严重掉帧(>50ms) ${r.over50} 帧`);
  console.log('JSON ' + JSON.stringify(r));
  ws.close(); child.kill(); process.exit(0);
})();
