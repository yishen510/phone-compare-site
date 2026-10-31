/* 新功能回归：键盘快捷键（t/f/c/?）+ 表格批量选择（全选/批量对比/批量收藏/清空）
   验证的是「交互效率」功能的可观测结果，不依赖内部实现细节。 */
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
 const key=k=>document.dispatchEvent(new window.KeyboardEvent('keydown',{key:k,bubbles:true}));
 const toastText=()=>document.getElementById('toast').textContent;

 /* 1. 快捷键 t 切换视图 */
 key('t'); await sleep(450); await waitPaint();
 chk('按 t 切到表格视图', !!document.querySelector('#phoneGrid .phone-table'));
 key('t'); await sleep(450); await waitPaint();
 chk('再按 t 切回卡片视图', !!document.querySelector('#phoneGrid .phone-card'));

/* 2. 表格全选 → 批量栏（列表默认逐页，先确认标签写明范围，再展开全部验证全量语义） */
document.querySelector('[data-view="table"]').click();
await sleep(450); await waitPaint();
let all=document.getElementById('selectAllRows');
chk('表格有全选复选框', !!all);
chk('逐页时全选标签写明范围', /全选已显示/.test(all.getAttribute('aria-label')||''), all.getAttribute('aria-label'));
const expAll=document.querySelector('[data-pager="all"]');
if(expAll&&!expAll.hidden){expAll.click();await sleep(450);await waitPaint();}
all=document.getElementById('selectAllRows');   /* 展开全部会重建表格，旧引用已失效 */
chk('展开后全选标签改为全部', /全选全部/.test(all.getAttribute('aria-label')||''), all.getAttribute('aria-label'));
all.checked=true; all.dispatchEvent(new window.Event('change',{bubbles:true}));
await sleep(120);
chk('全选后批量栏显示 485', document.getElementById('batchCount').textContent==='485'&&!document.getElementById('batchBar').hidden, document.getElementById('batchCount').textContent);

 /* 3. 批量对比超 4 款：提示且不加入 */
 document.querySelector('[data-batch="compare"]').click(); await sleep(120);
 chk('超 4 款时提示「最多 4 款」', /最多 4 款/.test(toastText()), toastText());

 /* 4. 清空选择 */
 document.querySelector('[data-batch="clear"]').click(); await sleep(120);
 chk('清空后批量栏隐藏', document.getElementById('batchBar').hidden);

 /* 5. 勾 2 行 → 批量加入对比 */
 [...document.querySelectorAll('.row-check')].slice(0,2).forEach(c=>{c.checked=true;c.dispatchEvent(new window.Event('change',{bubbles:true}));});
 await sleep(120);
 chk('勾 2 行批量栏显示 2', document.getElementById('batchCount').textContent==='2', document.getElementById('batchCount').textContent);
 document.querySelector('[data-batch="compare"]').click(); await sleep(350); await waitPaint();
 chk('批量加入对比 2 款', document.getElementById('dockCount').textContent==='2', document.getElementById('dockCount').textContent);

 /* 6. 批量收藏 */
 const fav0=Number(document.getElementById('favCount').textContent)||0;
 [...document.querySelectorAll('.row-check')].slice(0,2).forEach(c=>{c.checked=true;c.dispatchEvent(new window.Event('change',{bubbles:true}));});
 document.querySelector('[data-batch="fav"]').click(); await sleep(350); await waitPaint();
 const fav1=Number(document.getElementById('favCount').textContent)||0;
 chk('批量收藏使收藏数 +2', fav1===fav0+2, `${fav0} → ${fav1}`);

 /* 7. 快捷键 f：详情页收藏开关 */
 key('t'); await sleep(400); await waitPaint();
 const detailBtn=document.querySelector('#phoneGrid [data-detail]');
 const did=detailBtn.getAttribute('data-detail');
 detailBtn.click(); await sleep(300);
 const favOn0=document.querySelector(`[data-fav="${did}"]`)?.classList.contains('is-on');
 key('f'); await sleep(220);
 const favOn1=document.querySelector(`[data-fav="${did}"]`)?.classList.contains('is-on');
 chk('详情页按 f 切换收藏', favOn0!==favOn1, `${favOn0} → ${favOn1}`);

 /* 8. 快捷键 c：详情页对比开关 */
 const dc0=Number(document.getElementById('dockCount').textContent)||0;
 key('c'); await sleep(350); await waitPaint();
 const dc1=Number(document.getElementById('dockCount').textContent)||0;
 chk('详情页按 c 切换对比', dc0!==dc1, `${dc0} → ${dc1}`);

 /* 9. 快捷键 ?：帮助弹窗 */
 key('?'); await sleep(220);
 const nm=document.getElementById('notesModal');
 chk('按 ? 打开快捷键说明', !!nm&&!nm.hidden&&/键盘快捷键/.test(nm.textContent), nm?nm.textContent.slice(0,24):'—');

 console.log(`\n${ok} 通过 / ${bad} 失败；脚本错误 ${errs.length}`);
 if(errs.length)console.log('错误:',errs.slice(0,5));
 process.exit(bad||errs.length?1:0);
})();
