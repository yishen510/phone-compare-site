/**
 * 加载时间线测量：把「用户等多久」拆成可归因的几段。
 *
 * 用法：node _jst/load_bench.js <url> [profile]
 *   profile: fast（无限速）| 4g（4Mbps/100ms）| slow（1.5Mbps/200ms）默认 4g
 *
 * 与 ux_bench.js 的分工：那个测“交互有多快”，这个测“从点开链接到能看/能用”的全程，
 * 并且走真实 HTTP（本地 gzip 服务），file:// 是没有网络耗时的，测不出真实等待。
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const WebSocket = require('ws');

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const URL_ = process.argv[2] || 'http://127.0.0.1:8811/index.html';
const PROFILE = process.argv[3] || '4g';
const MOBILE = !process.argv.includes('--desktop');
const NET = {
  fast: null,
  '4g': { latency: 100, download: 4 * 1024 * 1024 / 8, upload: 1024 * 1024 / 8 },
  slow: { latency: 200, download: 1.5 * 1024 * 1024 / 8, upload: 512 * 1024 / 8 },
}[PROFILE];

const PORT = 9500 + Math.floor(Math.random() * 200);
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'edgeload-'));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let seq = 0;
const rpc = (ws, id, m, p) => new Promise((res, rej) => {
  const on = raw => { const x = JSON.parse(raw); if (x.id === id) { ws.off('message', on); res(x.result); } };
  ws.on('message', on);
  ws.send(JSON.stringify({ id, method: m, params: p || {} }));
  setTimeout(() => rej(new Error('timeout ' + m)), 90000);
});

/* 在页面任何脚本之前埋点：首卡出现 / 网格画完 / DCL / load / LCP 都取页面内时间，
   不受 CDP 往返和轮询间隔影响。
   注意 MutationObserver 必须节流到每帧一次：4MB 文档解析期间会产生上万次变更，
   原实现在每次回调里 querySelector('.phone-card') 是 O(n) 扫描，埋点本身能把页面拖慢几百 ms。 */
const BOOT = `
window.__m={};
try{new PerformanceObserver(l=>{for(const e of l.getEntries()){window.__m.lcp=e.startTime;}})
  .observe({type:'largest-contentful-paint',buffered:true});}catch(e){}
document.addEventListener('gridpainted',()=>{if(window.__m.gridpainted==null)window.__m.gridpainted=performance.now();},true);
(function(){
  var pending=false;
  var mo=new MutationObserver(function(){
    if(pending||window.__m.firstCard!=null)return;
    pending=true;
    requestAnimationFrame(function(){pending=false;
      if(window.__m.firstCard==null&&document.querySelector('.phone-card'))window.__m.firstCard=performance.now();});
  });
  mo.observe(document,{childList:true,subtree:true});
})();
document.addEventListener('DOMContentLoaded',()=>{window.__m.dcl=performance.now();});
window.addEventListener('load',()=>{window.__m.load=performance.now();});
`;

(async () => {
  let wsUrl = null;
  for (let i = 0; i < 80 && !wsUrl; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      const p = list.find(t => t.type === 'page');
      if (p) wsUrl = p.webSocketDebuggerUrl;
    } catch (e) {}
    if (!wsUrl) await sleep(250);
  }
  const ws = new WebSocket(wsUrl);
  await new Promise(r => ws.on('open', r));
  const call = (m, p) => rpc(ws, ++seq, m, p);
  const ev = async e => { const r = await call('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true }); return r && r.result ? r.result.value : null; };

  await call('Page.enable'); await call('Runtime.enable'); await call('Network.enable'); await call('Performance.enable');
  if (MOBILE) await call('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  const cpuArg = process.argv.find(a => a.startsWith('--cpu='));
  const CPU = cpuArg ? Number(cpuArg.split('=')[1]) : 0;
  if (CPU > 1) await call('Emulation.setCPUThrottlingRate', { rate: CPU });
  if (NET) {
    await call('Network.emulateNetworkConditions', {
      offline: false, latency: NET.latency, downloadThroughput: Math.round(NET.download), uploadThroughput: Math.round(NET.upload)
    });
  }
  let encoded = 0, totalBytes = 0, reqCount = 0;
  ws.on('message', raw => {
    try {
      const x = JSON.parse(raw);
      if (x.method === 'Network.loadingFinished' && x.params) {
        encoded = Math.max(encoded, x.params.encodedDataLength || 0);
        totalBytes += x.params.encodedDataLength || 0;
        reqCount++;
      }
    } catch (e) {}
  });
  await call('Page.addScriptToEvaluateOnNewDocument', { source: BOOT });

  await call('Page.navigate', { url: URL_ });
  await ev(`new Promise(r=>{const t=setInterval(()=>{const g=document.getElementById('phoneGrid');
    if(g&&g.dataset.painting==='0'&&g.querySelector('.phone-card')){clearInterval(t);r(1);}},25)})`);
  /* load 事件可能晚于「列表画完」，测之前要明确等到 complete（最多 8s），
     否则会把「还没到」误报成「永不触发」。 */
  await ev(`new Promise(r=>{const t0=performance.now();const t=setInterval(()=>{
    if(document.readyState==='complete'||performance.now()-t0>8000){clearInterval(t);r(document.readyState);}},50)})`);
  await sleep(300);

  const m = JSON.parse(await ev(`JSON.stringify(window.__m)`) || '{}');
  const nav = JSON.parse(await ev(`JSON.stringify((()=>{const n=performance.getEntriesByType('navigation')[0]||{};
    const p=performance.getEntriesByType('paint')||[];
    return {ttfb:n.responseStart||0, responseEnd:n.responseEnd||0, requestStart:n.requestStart||0,
      dcl:n.domContentLoadedEventEnd||0, load:n.loadEventEnd||0, transferred:n.transferSize||0, decoded:n.decodedBodySize||0,
      fcp:(p.find(x=>x.name==='first-contentful-paint')||{}).startTime||0,
      fp:(p.find(x=>x.name==='first-paint')||{}).startTime||0};})())`) || '{}');
  /* 资源总账：文档之外还有多少东西在抢同一条链路（字体 CSS + woff2 都在这里） */
  const res = JSON.parse(await ev(`JSON.stringify(performance.getEntriesByType('resource')
    .filter(r=>!/^data:/.test(r.name))
    .map(r=>({n:r.name.split('/')[2]||r.name.slice(0,40),kb:Math.round((r.transferSize||0)/1024),ms:Math.round(r.duration)})).sort((a,b)=>b.kb-a.kb))`) || '[]');
  const mt = (await call('Performance.getMetrics')).metrics || [];
  const gv = n => { const x = mt.find(i => i.name === n); return x ? x.value : 0; };

  /* 交互节点：打开详情 / 打开对比页 —— 也是“等待”，但属于响应类。
     两个测量都必须在页面内加超时兜底：弹层没弹出时 rAF 轮询会一直转，
     整个脚本就挂在这里（踩过一次）。 */
  const detailMs = await ev(`new Promise(r=>{
    const btn=document.querySelector('#phoneGrid [data-detail]');
    if(!btn)return r(-1);
    const t0=performance.now();
    btn.click();
    const m=document.getElementById('detailModal');
    const check=()=>{
      if(m&&!m.hidden)return r(performance.now()-t0);
      if(performance.now()-t0>5000)return r(-2);
      requestAnimationFrame(check);
    };
    check();
  })`);
  await sleep(250);
  await ev(`(()=>{const c=document.querySelector('#detailModal .modal-close');if(c)c.click();})()`);
  await sleep(200);
  /* 对比页要先有内容：先勾两台。
     注意每次点击都会让 render() 重建整个网格，旧节点上的第二次点击不会冒泡到 document，
     所以必须「点一个 → 重新取节点 → 再点下一个」，不能一次性 forEach。 */
  for (let k = 0; k < 2; k++) {
    await ev(`(()=>{const b=[...document.querySelectorAll('#phoneGrid [data-compare]')].find(x=>!x.disabled&&!/已加入/.test(x.textContent));if(b)b.click();})()`);
    await sleep(220);
  }
  const dockN = await ev(`(()=>{const d=document.getElementById('dockCount');return d?Number(d.textContent):-1;})()`);
  const compareMs = await ev(`new Promise(r=>{
    const btn=document.getElementById('openCompare');
    if(!btn)return r(-1);
    const t0=performance.now(); btn.click();
    const m=document.getElementById('compareModal');
    const check=()=>{
      if(m&&!m.hidden)return r(performance.now()-t0);
      if(performance.now()-t0>8000)return r(-2);
      requestAnimationFrame(check);
    };
    check();
  })`);

  /* 回访场景：同一个浏览器再打开一次（命中 ETag/缓存），等待通常和首次完全不同 */
  let warm = null;
  try {
    await call('Page.navigate', { url: URL_ });
    await ev(`new Promise(r=>{const t=setInterval(()=>{const g=document.getElementById('phoneGrid');
      if(g&&g.dataset.painting==='0'&&g.querySelector('.phone-card')){clearInterval(t);r(1);}},25)})`);
    const w = JSON.parse(await ev(`JSON.stringify(window.__m)`) || '{}');
    const wnav = JSON.parse(await ev(`JSON.stringify((()=>{const n=performance.getEntriesByType('navigation')[0]||{};
      return {responseEnd:n.responseEnd||0, requestStart:n.requestStart||0, transferred:n.transferSize||0};})())`) || '{}');
    warm = {
      transferKB: Math.round((wnav.transferred || 0) / 1024),
      downloadMs: Math.round((wnav.responseEnd || 0) - (wnav.requestStart || 0)),
      firstCard: Math.round(w.firstCard || 0),
      fcp: Math.round((JSON.parse(await ev(`JSON.stringify((()=>{const p=performance.getEntriesByType('paint')||[];return {v:(p.find(x=>x.name==='first-contentful-paint')||{}).startTime||0};})())`) || '{}').v) || 0),
    };
  } catch (e) { warm = null; }

  const out = {
    profile: PROFILE,
    cpu: CPU > 1 ? CPU : 1,
    transferKB: Math.round(nav.transferred / 1024) || Math.round(encoded / 1024),
    totalKB: Math.round(totalBytes / 1024),
    reqCount,
    decodedKB: Math.round(nav.decoded / 1024),
    ttfb: Math.round(nav.ttfb),
    downloadMs: Math.round(nav.responseEnd - nav.requestStart),
    fp: Math.round(nav.fp),
    fcp: Math.round(nav.fcp),
    lcp: Math.round(m.lcp || 0),
    firstCard: Math.round(m.firstCard || 0),
    gridPainted: Math.round(m.gridpainted || m.load || 0),
    dcl: Math.round(nav.dcl),
    load: Math.round(nav.load),
    detailOpen: Math.round(detailMs),
    compareOpen: Math.round(compareMs),
    scriptMs: Math.round(gv('ScriptDuration') * 1000),
    layoutMs: Math.round(gv('LayoutDuration') * 1000),
    styleMs: Math.round(gv('RecalcStyleDuration') * 1000),
    taskMs: Math.round(gv('TaskDuration') * 1000),
    layoutCount: gv('LayoutCount'),
    styleCount: gv('RecalcStyleCount'),
    layoutPer: gv('LayoutCount') ? Math.round(gv('LayoutDuration') * 1000 / gv('LayoutCount')) : 0,
    heapMB: +(gv('JSHeapUsedSize') / 1048576).toFixed(1),
    resCount: res.length,
    resKB: res.reduce((a, b) => a + b.kb, 0),
    resTop: res.slice(0, 4),
  };
  const pad = s => String(s).padStart(6);
  console.log(`【${PROFILE} · CPU×${out.cpu}${MOBILE ? ' · 移动端 390×844' : ''}】 ${URL_}`);
  console.log(`  文档传输          ${pad(out.transferKB)} KB   ← 解压后 ${out.decodedKB} KB`);
  console.log(`  全站总传输        ${pad(out.totalKB)} KB / ${out.reqCount} 个请求`);
  console.log(`  首字节 TTFB       ${pad(out.ttfb)} ms`);
  console.log(`  文档下载完成      ${pad(out.downloadMs)} ms`);
  console.log(`  首次绘制 FP       ${pad(out.fp)} ms`);
  console.log(`  首次内容 FCP      ${pad(out.fcp)} ms`);
  console.log(`  最大内容 LCP      ${pad(out.lcp)} ms`);
  console.log(`  首张卡片可见      ${pad(out.firstCard)} ms   ← 用户"看到列表"`);
  console.log(`  列表画完          ${pad(out.gridPainted)} ms   ← 用户"能滚动浏览"`);
  console.log(`  DOMContentLoaded  ${pad(out.dcl)} ms`);
  console.log(`  load 事件         ${pad(out.load || '未完成').toString()} ms${out.load ? '' : '   ← 仍有子资源挂着（外部字体）'}`);
  console.log(`  ── 归因（累计）──`);
  console.log(`  Script            ${pad(out.scriptMs)} ms`);
  console.log(`  Layout            ${pad(out.layoutMs)} ms`);
  console.log(`  RecalcStyle       ${pad(out.styleMs)} ms`);
  console.log(`  Task 合计         ${pad(out.taskMs)} ms`);
  console.log(`  Layout 次数       ${pad(out.layoutCount)} 次 · 平均 ${out.layoutPer} ms/次`);
  console.log(`  Style 重算次数    ${pad(out.styleCount)} 次`);
  console.log(`  堆内存            ${String(out.heapMB).padStart(6)} MB`);
  console.log(`  其它资源          ${pad(out.resKB)} KB / ${out.resCount} 个   ← 与文档抢同一条链路`);
  out.resTop.forEach(r => console.log(`    · ${String(r.kb).padStart(4)} KB ${String(r.ms).padStart(5)}ms  ${r.n}`));
  console.log(`  ── 响应类 ──`);
  console.log(`  打开详情          ${pad(out.detailOpen)} ms`);
  console.log(`  打开对比页        ${pad(out.compareOpen)} ms   （对比坞已有 ${dockN} 台）`);
  if (warm) {
    console.log(`  ── 回访（同浏览器再开一次）──`);
    console.log(`  传输              ${pad(warm.transferKB)} KB · 下载 ${warm.downloadMs} ms`);
    console.log(`  FCP               ${pad(warm.fcp)} ms`);
    console.log(`  首张卡片可见      ${pad(warm.firstCard)} ms`);
    out.warm = warm;
  }
  console.log('JSON ' + JSON.stringify(out));
  ws.close(); child.kill(); process.exit(0);
})();
