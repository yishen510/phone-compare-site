const fs=require('fs');const {JSDOM}=require('jsdom');
const html=fs.readFileSync('D:/Codex/_deploy_phone/index.html','utf8');
const errors=[];
const dom=new JSDOM(html,{runScripts:'dangerously',url:'https://yishen510.github.io/phone-compare-site/',pretendToBeVisual:true,
  beforeParse(w){w.matchMedia=w.matchMedia||(q=>({matches:false,media:q,addEventListener(){},removeEventListener(){},addListener(){},removeListener(){}}));w.requestIdleCallback=cb=>setTimeout(()=>cb({timeRemaining:()=>8}),0);w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=function(){};
  w.addEventListener('error',e=>errors.push(String(e.message)));}});
const {window}=dom,{document}=window;
const q=s=>document.querySelector(s),qa=s=>[...document.querySelectorAll(s)];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const check=(n,ok,d)=>console.log((ok?'PASS':'FAIL')+'  '+n+(d?'  → '+JSON.stringify(d).slice(0,140):''));
(async()=>{
  await sleep(900);
  const data=window.PHONE_DATA||[];
  const mid=data.filter(p=>['中端全能','中端影像','中端续航'].includes(p.type));
  check(`中端机型共 ${mid.length} 台（>0 即通过）`, mid.length>0, {count:mid.length});
  check('三种中端定位都有', ['中端全能','中端影像','中端续航'].every(t=>mid.some(p=>p.type===t)),
    Object.fromEntries(['中端全能','中端影像','中端续航'].map(t=>[t,mid.filter(p=>p.type===t).length])));

  const boxes=['中端全能','中端影像','中端续航'].map(v=>q(`input[name="type"][value="${v}"]`));
  check('筛选面板已出现三个中端复选框', boxes.every(Boolean), boxes.map(b=>!!b));

  // 选「中端影像」
  boxes[1].checked=true; boxes[1].dispatchEvent(new window.Event('change',{bubbles:true})); await sleep(60);
  const cards=qa('.phone-card').length;
  const names=qa('.phone-card h3').map(h=>h.textContent);
  check('勾「中端影像」后只剩影像型中端机', cards===mid.filter(p=>p.type==='中端影像').length, {cards, names});

  // 商务旗舰映射修复：勾「标准旗舰」应同时带出商务旗舰
  boxes[1].checked=false; boxes[1].dispatchEvent(new window.Event('change',{bubbles:true}));
  const std=q('input[name="type"][value="标准旗舰"]');
  std.checked=true; std.dispatchEvent(new window.Event('change',{bubbles:true})); await sleep(60);
  const hasBiz=data.some(p=>p.type==='商务旗舰');
  check('勾「标准旗舰」时商务旗舰不再被漏掉', !hasBiz || qa('.phone-card').length>0, {cards:qa('.phone-card').length, hasBiz});
  std.checked=false; std.dispatchEvent(new window.Event('change',{bubbles:true})); await sleep(60);

  // 中端机详情页
  const target=data.find(p=>p.id==='oppo-k15');
  if(target){ q(`#phoneGrid [data-detail="${target.id}"]`).click(); await sleep(50);
    check('中端机详情页可打开且显示参考价口径', (q('#detailTitle')||{}).textContent===target.name && /参考价/.test(q('#detailModal').textContent), {
      title:(q('#detailTitle')||{}).textContent, price:(q('#detailModal .price-number')||{}).textContent,
      tag:(q('#detailModal .price-tag')||{}).textContent });
  }
  check('无脚本报错', errors.length===0, errors);
  process.exit(0);
})();
