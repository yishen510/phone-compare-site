/* 详情页新功能回归：收藏/对比按钮（就地切换并刷新文案）+ 同价位替代（3 款、可跳转） */
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

 /* 1. 打开详情 */
 const detailBtn=document.querySelector('#phoneGrid [data-detail]');
 chk('可找到详情按钮', !!detailBtn);
 detailBtn.click(); await sleep(380);
 const dm=document.getElementById('detailModal');
 chk('详情已打开', !!dm&&!dm.hidden);
 const favBtn=dm.querySelector('[data-dfav]');
 const cmpBtn=dm.querySelector('[data-dcmpr]');
 chk('详情页有「收藏」按钮', !!favBtn, favBtn?favBtn.textContent.trim():'—');
 chk('详情页有「加入对比」按钮', !!cmpBtn, cmpBtn?cmpBtn.textContent.trim():'—');

 /* 2. 点收藏：文案就地切换（refreshDetailIfOpen 重渲染后仍是同一 modal） */
 const fav0=favBtn.textContent.trim();
 favBtn.click(); await sleep(320);
 const favNow=document.querySelector('#detailModal [data-dfav]');
 const fav1=favNow.textContent.trim();
 chk('点收藏后按钮文案切换', fav0!==fav1, `${fav0} → ${fav1}`);
 chk('收藏后按钮为「已收藏」态', /已收藏/.test(fav1), fav1);

 /* 3. 点对比：文案就地切换 */
 const cmp0=document.querySelector('#detailModal [data-dcmpr]').textContent.trim();
 document.querySelector('#detailModal [data-dcmpr]').click(); await sleep(380); await waitPaint();
 const cmp1=document.querySelector('#detailModal [data-dcmpr]').textContent.trim();
 chk('点对比后按钮文案切换', cmp0!==cmp1, `${cmp0} → ${cmp1}`);
 chk('对比后按钮为「已加入对比」态', /已加入对比/.test(cmp1), cmp1);

 /* 4. 同价位替代 */
 const alts=[...document.querySelectorAll('#detailModal .alt-card')];
 chk('详情页有「同价位还可以看」', !!document.querySelector('#detailModal .alt-block'));
 chk('替代机型为 3 款', alts.length===3, alts.length+' 款');
 chk('替代卡片展示名称与价格', alts.length>0&&/¥|待核实/.test(alts[0].textContent), alts[0]?alts[0].textContent.trim().slice(0,32):'—');

 /* 5. 点替代卡片跳转详情 */
 if(alts.length){
  const targetName=alts[0].querySelector('strong').textContent;
  alts[0].click(); await sleep(380);
  const title=document.getElementById('detailTitle').textContent;
  chk('点替代卡片切到该机型', title===targetName, `${targetName} → ${title}`);
 }

 console.log(`\n${ok} 通过 / ${bad} 失败；脚本错误 ${errs.length}`);
 if(errs.length)console.log('错误:',errs.slice(0,5));
 process.exit(bad||errs.length?1:0);
})();
