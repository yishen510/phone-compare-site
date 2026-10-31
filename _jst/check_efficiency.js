/* 提效功能回归：搜索历史（记录/聚焦展示/点击复用/清空）+ 筛选方案（保存/重置/恢复/删除）
   全部按「用户可见结果」断言，不依赖内部变量。 */
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
 const cardCount=()=>document.querySelectorAll('#phoneGrid .phone-card').length;

 /* 1. 搜索历史：记录 */
 q.value='小米15'; q.dispatchEvent(new window.Event('input',{bubbles:true}));
 await sleep(320); await waitPaint();
 q.dispatchEvent(new window.Event('change',{bubbles:true}));
 await sleep(120);
 q.value=''; q.dispatchEvent(new window.Event('input',{bubbles:true}));
 await sleep(320); await waitPaint();
 q.focus(); await sleep(120);
 const sh=document.getElementById('searchHistory');
 chk('聚焦空输入时显示最近搜索', !sh.hidden&&/小米15/.test(sh.textContent), (sh.textContent||'').trim().slice(0,36));

 /* 2. 搜索历史：点击复用 */
 const chip=sh.querySelector('[data-search]');
 chk('历史里有可点 chip', !!chip, chip?chip.dataset.search:'—');
 if(chip){
  chip.dispatchEvent(new window.MouseEvent('mousedown',{bubbles:true}));
  await sleep(420); await waitPaint();
  chk('点历史 chip 填入搜索框', q.value==='小米15', q.value);
  chk('点历史 chip 后结果生效（非全量）', cardCount()>0&&cardCount()<485, cardCount()+' 张');
 }

 /* 3. 清空搜索历史 */
 q.value=''; q.dispatchEvent(new window.Event('input',{bubbles:true}));
 await sleep(320); await waitPaint();
 q.focus(); await sleep(120);
 const clr=document.querySelector('#searchHistory [data-search-clear]');
 chk('历史里有「清空」', !!clr);
 if(clr){clr.click();await sleep(120);}
 chk('清空后历史隐藏', document.getElementById('searchHistory').hidden);

 /* 4. 筛选方案：保存 */
 const brandInput=[...document.querySelectorAll('#brandFilters input')].find(i=>i.value==='华为')||document.querySelector('#brandFilters input');
 chk('品牌筛选存在', !!brandInput, brandInput?brandInput.value:'—');
 brandInput.checked=true; brandInput.dispatchEvent(new window.Event('change',{bubbles:true}));
 await sleep(350); await waitPaint();
 const narrowed=cardCount();
 chk('勾选品牌后结果收窄', narrowed>0&&narrowed<485, narrowed+' 张');

 document.getElementById('savePreset').click();
 await sleep(150);
 const pl=document.getElementById('presetList');
 chk('保存后出现「我的筛选」', !pl.hidden&&pl.querySelectorAll('[data-preset]').length>0, (pl.textContent||'').trim().slice(0,36));

 /* 5. 重置后应用方案 */
 document.getElementById('resetFilters').click();
 await sleep(350); await waitPaint();
 chk('重置后恢复全量 485', cardCount()===485, cardCount()+' 张');
 const pchip=document.querySelector('#presetList [data-preset]');
 chk('方案 chip 仍在（重置不清方案）', !!pchip);
 if(pchip){pchip.click();await sleep(420);await waitPaint();}
 chk('点方案恢复筛选结果', cardCount()===narrowed, cardCount()+' 张（期望 '+narrowed+'）');

 /* 6. 删除方案 */
 const del=document.querySelector('#presetList [data-preset-del]');
 chk('方案带删除按钮', !!del);
 if(del){del.click();await sleep(150);}
 chk('删除后方案列表隐藏', document.getElementById('presetList').hidden);

 console.log(`\n${ok} 通过 / ${bad} 失败；脚本错误 ${errs.length}`);
 if(errs.length)console.log('错误:',errs.slice(0,5));
 process.exit(bad||errs.length?1:0);
})();
