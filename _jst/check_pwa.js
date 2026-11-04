/**
 * PWA 验证：Service Worker 是否注册成功、断网重载后列表还在不在。
 *
 * 为什么要真浏览器：jsdom 没有 service worker 与真实网络栈，
 * 离线能力只能在 Chromium 里通过 CDP 断网来验。
 *
 * 用法：node _jst/check_pwa.js [url]
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const WebSocket = require('ws');

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const URL_ = process.argv[2] || 'http://127.0.0.1:8816/index.html';
const PORT = 9600 + Math.floor(Math.random() * 120);
const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'pwa-'));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${prof}`, '--window-size=390,844', 'about:blank'],
  { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let seq = 0;
const rpc = (ws, id, m, p) => new Promise((res, rej) => {
  const on = raw => { const x = JSON.parse(raw); if (x.id === id) { ws.off('message', on); res(x.result); } };
  ws.on('message', on);
  ws.send(JSON.stringify({ id, method: m, params: p || {} }));
  setTimeout(() => rej(new Error('timeout ' + m)), 60000);
});

let ok = 0, bad = 0;
const chk = (name, cond, extra = '') => {
  cond ? ok++ : bad++;
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${extra ? '  → ' + extra : ''}`);
};

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

  await call('Page.enable'); await call('Runtime.enable'); await call('Network.enable');
  await call('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });

  await call('Page.navigate', { url: URL_ });
  await ev(`new Promise(r=>{const t=setInterval(()=>{const g=document.getElementById('phoneGrid');
    if(g&&g.dataset.painting==='0'&&g.querySelector('.phone-card')){clearInterval(t);r(1);}},40)})`);

  /* ready 在注册失败时永远不会 resolve，必须自己加超时，否则整个检查挂死 */
  const reg = await ev(`Promise.race([
    navigator.serviceWorker ? navigator.serviceWorker.ready.then(r=>!!r.active) : Promise.resolve('no-sw'),
    new Promise(r=>setTimeout(()=>r('timeout'),8000))
  ])`);
  chk('Service Worker 已激活', reg === true, String(reg));

  const cached = await ev(`caches.keys().then(k=>k.join(','))`);
  chk('已建立缓存', /shell-/.test(String(cached)), String(cached));

  /* 让 SW 接管当前页，然后断网重载 */
  await ev(`navigator.serviceWorker.ready.then(r=>r.active&&r.active.postMessage?1:1)`);
  await call('Page.reload', { ignoreCache: false });
  await sleep(1500);

  await call('Network.emulateNetworkConditions',
    { offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0 });
  await call('Page.reload', { ignoreCache: false });
  await sleep(3000);

  const offline = JSON.parse(await ev(`JSON.stringify({
    title: document.title,
    cards: document.querySelectorAll('#phoneGrid .phone-card').length,
    count: (document.getElementById('resultCount')||{}).textContent||'',
    online: navigator.onLine
  })`) || '{}');

  chk('断网后页面仍能打开（有标题）', !!offline.title, offline.title);
  chk('断网后列表仍有卡片', offline.cards > 0, `${offline.cards} 张 / 计数 ${offline.count}`);

  await call('Network.emulateNetworkConditions',
    { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });

  console.log(`\n${ok} 通过 / ${bad} 失败`);
  ws.close(); child.kill(); process.exit(bad ? 1 : 0);
})();
