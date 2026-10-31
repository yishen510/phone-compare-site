/* 性能修复的「行为不变」回归：
   1) BRAND_COUNT 预计算后品牌数仍正确
   2) MutationObserver 改为只处理新增卡片后，data-motion/tabindex/--card-index 仍符合原语义
   3) 排序 key 预计算后，价格/电池/重量排序结果与缺值排序位置不变
   4) relScore 预计算后，搜索相关性（首条）不变
   5) ensureDetailList 复用 lastArr 后，详情翻页仍正常 */
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
 const data=window.PHONE_DATA||[];
 let ok=0,bad=0;
 const chk=(n,c,extra='')=>{c?ok++:bad++;console.log(`${c?'PASS':'FAIL'}  ${n}${extra?'  → '+extra:''}`);};
 async function waitPaint(){for(let i=0;i<400;i++){const g=document.getElementById('phoneGrid');if(g&&g.dataset.painting==='0')break;await sleep(20);}}
 const byName=new Map(data.map(p=>[p.name,p]));
 const priceNum=p=>{const v=p&&p.priceCN;return (v===null||v===undefined||v===''||!Number.isFinite(Number(v)))?null:Number(v);};
 const cardNames=()=>[...document.querySelectorAll('#phoneGrid .phone-card h3')].map(h=>h.textContent);
 /* 列表已改为可逐页展示（默认只画一页）。本文件验证的是「性能改动前后行为不变」，
    所有断言都必须在全量数据上跑，所以先点「全部展开」。 */
 const expandAll=async()=>{const b=document.querySelector('[data-pager="all"]');if(b&&!b.hidden){b.click();await sleep(200);await waitPaint();}};
 await expandAll();

 /* 1. 品牌统计 = 数据实际品牌数（BRAND_COUNT） */
 const brandText=document.getElementById('statBrands').textContent;
 chk('品牌统计 = 数据实际品牌数', Number(brandText)===new Set(data.map(p=>p.brand)).size, brandText);

 /* 2. 卡片 motion 语义（MutationObserver 只处理新增后仍要全部命中） */
 const cards=[...document.querySelectorAll('#phoneGrid .phone-card')];
 chk('首屏卡片已渲染', cards.length>0, cards.length+' 张');
 chk('卡片都带 data-motion 标记', cards.length>0&&cards.every(c=>c.getAttribute('data-motion')==='1'));
 chk('卡片 tabindex = -1', cards.every(c=>c.getAttribute('tabindex')==='-1'));
 chk('前 8 张入场序号递增 0…8', (()=>{const v=cards.slice(0,9).map(c=>c.style.getPropertyValue('--card-index'));return v[0]==='0'&&v[8]==='8';})());

 /* 3. 价格升序：非空单调不减、缺价最后（排序 key 预计算） */
 const sel=document.getElementById('sortSelect');
 function setSort(v){sel.value=v;sel.dispatchEvent(new window.Event('input',{bubbles:true}));}
 setSort('priceAsc'); await sleep(300); await waitPaint();
 let names=cardNames();
 let prices=names.map(n=>priceNum(byName.get(n)));
 let nn=prices.filter(x=>x!==null);
 chk('价格升序：非空价格单调不减', nn.length>0&&nn.every((v,i)=>i===0||nn[i-1]<=v), nn.slice(0,3).join(',')+' …');
 chk('价格升序：缺价排在最后', prices.slice(nn.length).every(x=>x===null), prices.slice(-3).join(','));

 /* 4. 电池降序：非空单调不增、缺值最后 */
 setSort('batteryDesc'); await sleep(300); await waitPaint();
 names=cardNames();
 const batNum=n=>{const p=byName.get(n);const m=String((p&&p.battery)||'').match(/(\d{3,5})\s*mAh/i);return m?Number(m[1]):null;};
 const bats=names.map(batNum); const bn=bats.filter(x=>x!==null);
 chk('电池降序：数值单调不增', bn.length>0&&bn.every((v,i)=>i===0||bn[i-1]>=v));
 chk('电池降序：缺值排在最后', bats.slice(bn.length).every(x=>x===null));

 /* 5. 搜索相关性（relScore 预计算后首条不变） */
 const q=document.getElementById('searchInput');
 q.value='小米15'; q.dispatchEvent(new window.Event('input',{bubbles:true}));
 await sleep(400); await waitPaint();
 names=cardNames();
 chk('搜「小米15」有结果', names.length>0, names.length+' 条');
 chk('搜「小米15」首条为「小米 15」', names[0]==='小米 15', names[0]||'—');
 q.value=''; q.dispatchEvent(new window.Event('input',{bubbles:true}));
 await sleep(300); await waitPaint();

 /* 6. 表格视图：行数 + 重量升序（reorderTableRows 未受影响） */
 document.querySelector('[data-view="table"]').click();
 await sleep(400); await waitPaint();
 let rows=document.querySelectorAll('.phone-table tbody tr');
 chk('切表格后行数 = 数据条数', rows.length===data.length, rows.length+' 行');
 setSort('weightAsc'); await sleep(400); await waitPaint();
 rows=document.querySelectorAll('.phone-table tbody tr');
 chk('表格排序后行数仍 = 数据条数', rows.length===data.length, rows.length+' 行');
 const wtNum=n=>{const p=byName.get(n);const m=String((p&&p.weight)||'').match(/(\d{2,3}(?:\.\d{1,2})?)\s*(?:g|克)/i);return m?Number(m[1]):null;};
 const rowNames=[...rows].map(tr=>tr.querySelector('td b').textContent);
 const wts=rowNames.map(wtNum); const wn=wts.filter(x=>x!==null);
 chk('表格重量升序：非空单调不减', wn.length>0&&wn.every((v,i)=>i===0||wn[i-1]<=v));
 chk('表格重量升序：缺值最后', wts.slice(wn.length).every(x=>x===null));

 /* 7. 详情翻页（ensureDetailList 复用 lastArr 后仍可前后翻） */
 document.querySelector('[data-view="cards"]').click();
 await sleep(300); await waitPaint();
 const firstBtn=document.querySelector('#phoneGrid [data-detail]');
 firstBtn.click();
 await sleep(300);
 const title1=document.getElementById('detailTitle').textContent;
 document.dispatchEvent(new window.KeyboardEvent('keydown',{key:'ArrowRight'}));
 await sleep(300);
 const title2=document.getElementById('detailTitle').textContent;
 chk('详情可打开', !!title1, title1);
 chk('详情 ArrowRight 可翻到下一台', title1!==title2, title1+' → '+title2);

 console.log(`\n${ok} 通过 / ${bad} 失败；脚本错误 ${errs.length}`);
 if(errs.length)console.log('错误:',errs.slice(0,5));
 process.exit(bad||errs.length?1:0);
})();
