/**
 * 抓「等待过程」的时间序列截图：证明用户看到的是白屏还是骨架屏。
 * 用法：node _jst/shot_timeline.js [url] [毫秒,逗号分隔]
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const WebSocket = require('ws');

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const URL_ = process.argv[2] || 'http://127.0.0.1:8811/index.html';
const MS = (process.argv[3] || '300,700,1200,1800,2400').split(',').map(Number);
const PORT = 9800 + Math.floor(Math.random() * 150);
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'edgeline-'));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let seq = 0;
const rpc = (ws, id, m, p) => new Promise((res, rej) => {
  const on = raw => { const x = JSON.parse(raw); if (x.id === id) { ws.off('message', on); res(x.result); } };
  ws.on('message', on);
  ws.send(JSON.stringify({ id, method: m, params: p || {} }));
  setTimeout(() => rej(new Error('timeout ' + m)), 60000);
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
  await call('Page.enable'); await call('Runtime.enable'); await call('Network.enable');
  await call('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await call('Emulation.setCPUThrottlingRate', { rate: 4 });
  await call('Network.emulateNetworkConditions', {
    offline: false, latency: 100, downloadThroughput: Math.round(4 * 1024 * 1024 / 8), uploadThroughput: 131072
  });
  const t0 = Date.now();
  await call('Page.navigate', { url: URL_ });
  for (const target of MS) {
    const wait = target - (Date.now() - t0);
    if (wait > 0) await sleep(wait);
    const shot = await call('Page.captureScreenshot', { format: 'png' });
    const name = `_jst/line_${String(target).padStart(4, '0')}ms.png`;
    fs.writeFileSync(name, Buffer.from(shot.data, 'base64'));
    console.log('已保存', name);
  }
  ws.close(); child.kill(); process.exit(0);
})();
