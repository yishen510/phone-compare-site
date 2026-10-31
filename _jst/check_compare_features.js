/* 对比页新功能回归：页内添加机型、d 切换只看差异、最优值标记（含充电最快） */
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

 /* 1. 加入 2 款对比（每次点击后会重渲染，必须重新查询按钮） */
 document.querySelector('#phoneGrid [data-compare]').click();
 await sleep(400); await waitPaint();
 const second=[...document.querySelectorAll('#phoneGrid [data-compare]')].find(b=>!/已加入对比/.test(b.textContent));
 chk('可找到第二款加入对比的按钮', !!second);
 if(second){second.click();await sleep(400);await waitPaint();}
 chk('对比坞出现', !document.getElementById('compareDock').hidden);

 /* 2. 打开对比弹窗 */
 document.getElementById('openCompare').click();
 await sleep(420);
 const cm=document.getElementById('compareModal');
 chk('对比弹窗打开', !!cm&&!cm.hidden);
 chk('对比页有「添加机型」输入', !!document.getElementById('compareAdd'));

 /* 3. 最优值标记（价格/电池/重量/充电，任一命中即说明 bestTag 工作） */
 const tags=[...document.querySelectorAll('#compareModal .best-tag')].map(t=>t.textContent.trim());
 chk('对比表有最优值标记', tags.length>0, [...new Set(tags)].join(' / '));

 /* 4. 页内输入品牌 → 建议 */
 const add=document.getElementById('compareAdd');
 add.value='小米'; add.dispatchEvent(new window.Event('input',{bubbles:true}));
 await sleep(220);
 const list=document.getElementById('compareAddList');
 const items=[...list.querySelectorAll('[data-cmp-add]')];
 chk('输入后出现机型建议', !list.hidden&&items.length>0, items.length+' 条');

 /* 5. 点建议 → 对比变 3 款 */
 if(items.length){
  items[0].click(); await sleep(450);
  const n=document.querySelectorAll('#compareModal .compare-product').length;
  chk('页内添加后对比变 3 款', n===3, n+' 款');
 }

 /* 6. 按 d 切换「只看差异」 */
 const beforeRows=document.querySelectorAll('#compareModal .compare-table tbody tr').length;
 document.dispatchEvent(new window.KeyboardEvent('keydown',{key:'d',bubbles:true}));
 await sleep(450);
 const afterRows=document.querySelectorAll('#compareModal .compare-table tbody tr').length;
 chk('按 d 切换只看差异（行数不增）', afterRows<=beforeRows, `${beforeRows} → ${afterRows}`);

 console.log(`\n${ok} 通过 / ${bad} 失败；脚本错误 ${errs.length}`);
 if(errs.length)console.log('错误:',errs.slice(0,5));
 process.exit(bad||errs.length?1:0);
})();
