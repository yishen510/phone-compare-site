/**
 * 无头 Edge 渲染抓页：官方站多为 JS 渲染，纯 HTTP 抓不到，这里用 CDP 取渲染后的文本。
 * 用法：node _jst/render.js（读 _jst/render_urls.json，输出 _jst/render_out.json）
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const WebSocket = require('ws');

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const JOBS = JSON.parse(fs.readFileSync(path.join(__dirname, 'render_urls.json'), 'utf8'));
const PORT = 9600 + Math.floor(Math.random() * 300);
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'edgerender-'));
const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  '--window-size=1440,2400', '--lang=zh-CN', 'about:blank',
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
function rpc(ws, id, method, params) {
  return new Promise((resolve, reject) => {
    const on = raw => { const m = JSON.parse(raw); if (m.id === id) { ws.off('message', on); resolve(m.result); } };
    ws.on('message', on);
    ws.send(JSON.stringify({ id, method, params: params || {} }));
    setTimeout(() => reject(new Error('timeout ' + method)), 60000);
  });
}

(async () => {
  const ws = new WebSocket(await target());
  await new Promise(r => ws.on('open', r));
  const call = (m, p) => rpc(ws, ++seq, m, p);
  await call('Page.enable');
  await call('Runtime.enable');
  const out = [];
  for (const job of JOBS) {
    try {
      await call('Page.navigate', { url: job.url });
      await sleep(job.wait || 6000);
      const r = await call('Runtime.evaluate', {
        returnByValue: true,
        expression: `(() => {
          const t = document.body ? document.body.innerText : '';
          let links = [];
          if (${job.links ? 'true' : 'false'}) {
            const pat = ${JSON.stringify(job.linkFilter || '')};
            links = Array.from(document.querySelectorAll('a[href]'))
              .map(a => ({ u: a.href, t: (a.innerText || '').trim().slice(0, 40) }))
              .filter(x => !pat || x.u.includes(pat) || x.t.includes(pat))
              .slice(0, 60);
          }
          return { title: document.title, len: t.length, text: t.slice(0, 60000), links };
        })()`,
      });
      const v = (r && r.result && r.result.value) || {};
      out.push({ ...job, title: v.title, len: v.len, text: v.text, links: v.links || [] });
      console.log(`${job.name}: ${v.len} 字符 | ${v.title || ''}`);
    } catch (e) {
      out.push({ ...job, err: String(e).slice(0, 120), links: [] });
      console.log(`${job.name}: ERR ${String(e).slice(0, 80)}`);
    }
  }
  fs.writeFileSync(path.join(__dirname, 'render_out.json'), JSON.stringify(out, null, 1));
  ws.close();
  child.kill();
  process.exit(0);
})();
