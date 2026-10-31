/**
 * 截图核对配色：node _jst/shot_theme.js <url> <dark|light|auto> <输出.png> [视口高] [滚动到的选择器]
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const WebSocket = require('ws');

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
/* 按「非 -- 开头」取位置参数：否则 --desktop 会被当成滚动选择器（踩过） */
const args = process.argv.slice(2).filter(a => !a.startsWith('--'));
const [url, theme, out, hRaw, scrollSel] = args;
const DESKTOP = process.argv.includes('--desktop');
const PORT = 9850 + Math.floor(Math.random() * 100);
const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'shot-'));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--no-first-run',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${prof}`, '--window-size=1440,900',
  'about:blank'], { stdio: 'ignore' });
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
  const ev = async e => {
    const r = await call('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true });
    return r && r.result ? r.result.value : null;
  };
  await call('Page.enable'); await call('Runtime.enable');
  await call('Emulation.setDeviceMetricsOverride',
    { width: DESKTOP?1280:390, height: Number(hRaw) || (DESKTOP?820:844), deviceScaleFactor: DESKTOP?1:2, mobile: !DESKTOP });
  if (theme && theme !== 'auto') {
    await call('Page.addScriptToEvaluateOnNewDocument',
      { source: `try{localStorage.setItem('phoneindex.theme.v1','${theme}')}catch(e){}` });
  }
  await call('Page.navigate', { url });
  /* 等列表就绪，但设上限：对比页之类没有卡片，死等会一直挂到超时 */
  await ev(`new Promise(r=>{const t0=performance.now();
    const t=setInterval(()=>{const g=document.getElementById('phoneGrid');
    const done=g&&g.dataset.painting==='0'&&g.querySelector('.phone-card');
    if(done||performance.now()-t0>12000){clearInterval(t);r(1);}},40)})`);
  if (scrollSel) {
    await ev(`(()=>{const el=document.querySelector('${scrollSel}');
      if(el){const y=el.getBoundingClientRect().top+(window.scrollY||0)-40;
      (document.scrollingElement||document.documentElement).scrollTop=y;window.scrollTo(0,y);}})()`);
    await sleep(900);
  }
  /* 字体是 load 后才注入的，等它落定再拍，否则拍到的是系统字体 */
  await sleep(2000);
  const shot = await call('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(out, Buffer.from(shot.data, 'base64'));
  console.log('已保存', out);
  ws.close(); child.kill(); process.exit(0);
})();
