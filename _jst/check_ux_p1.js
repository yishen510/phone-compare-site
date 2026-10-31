/* UX 改进回归：空状态量化 + 定向清除、表格横滑提示、toast 撤销、卡片补充电、审核标签文案 */
const fs=require('fs');const {JSDOM}=require('jsdom');
const html=fs.readFileSync('index.html','utf8');
const errs=[];
const dom=new JSDOM(html,{runScripts:'dangerously',url:'https://x.test/',pretendToBeVisual:true,
 beforeParse(w){
  w.matchMedia=w.matchMedia||(q=>({matches:false,media:q,addEventListener(){},removeEventListener(){}}));
  w.requestIdleCallback=cb=>setTimeout(()=>cb({timeRemaining:()=>8}),0);
  w.scrollTo=()=>{};
  w.HTMLElement.prototype.scrollIntoView=function(){};
  w.URL.revokeObjectURL=()=>{};
  w.addEventListener('error',e=>errs.push(String(e.message)));
 }});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 await sleep(1800);
 const {window}=dom,{document}=window;
 let ok=0,bad=0;
 const chk=(n,c,extra='')=>{c?ok++:bad++;console.log(`${c?'PASS':'FAIL'}  ${n}${extra?'  → '+extra:''}`);};
 async function waitPaint(){for(let i=0;i<400;i++){const g=document.getElementById('phoneGrid');if(g&&g.dataset.painting==='0')break;await sleep(20);}}
 const q=document.getElementById('searchInput');

 /* 1. 卡片补充电 + 审核标签文案 */
 const specs=[...document.querySelectorAll('#phoneGrid .phone-card .card-specs small')].slice(0,6).map(s=>s.textContent);
 chk('卡片补充「充电」字段', specs.includes('充电'), specs.join('/'));
 const pill=document.querySelector('#phoneGrid .audit-pill');
 chk('审核标签文案可读', !!pill&&/审核通过|未通过整机审核/.test(pill.textContent), pill?pill.textContent:'—');

 /* 2. 表格横滑提示 */
 document.querySelector('[data-view="table"]').click();
 await sleep(400); await waitPaint();
 chk('表格有横滑提示元素', !!document.querySelector('#phoneGrid .table-hint'));
 document.querySelector('[data-view="cards"]').click();
 await sleep(300); await waitPaint();

 /* 3. 空状态量化 + 定向清除 */
 q.value='zzzznotexist'; q.dispatchEvent(new window.Event('input',{bubbles:true}));
 await sleep(400); await waitPaint();
 const es=document.getElementById('emptyState');
 chk('无结果时空状态可见', !!es&&!es.hidden);
 chk('空状态文案给出总数', es&&/共 \d+ 款/.test(es.textContent), es?(es.textContent.match(/共 \d+ 款[^。]*/)||['—'])[0]:'—');
 const chips=[...document.querySelectorAll('#emptyChips .af-chip')];
 chk('空状态列出可移除的筛选', chips.length>0, chips.map(c=>c.textContent.trim()).join(' | '));
 if(chips.length){chips[0].click();await sleep(400);await waitPaint();}
 chk('点「移除」后结果恢复', document.querySelectorAll('#phoneGrid .phone-card').length>0, document.querySelectorAll('#phoneGrid .phone-card').length+' 张');

 /* 4. 收藏撤销 */
 await waitPaint();
 const fav=()=>document.querySelector('#phoneGrid [data-fav]');
 const first=fav();
 chk('可找到收藏按钮', !!first);
 if(first){
  const fid=first.dataset.fav;
  fav().click(); await sleep(200); await waitPaint();
  fav().click(); await sleep(200); await waitPaint();
  const undo=document.querySelector('.toast-undo');
  chk('取消收藏后出现「撤销」', !!undo, undo?undo.textContent:'—');
  if(undo){undo.click();await sleep(300);await waitPaint();}
  const back=document.querySelector('[data-fav="'+fid+'"]');
  chk('撤销后收藏已恢复', !!back&&(back.classList.contains('is-on')||back.textContent==='♥'), back?back.textContent:'—');
 }

 console.log(`\n${ok} 通过 / ${bad} 失败；脚本错误 ${errs.length}`);
 if(errs.length)console.log('错误:',errs.slice(0,5));
 process.exit(bad||errs.length?1:0);
})();
