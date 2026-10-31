const fs=require('fs');const {JSDOM}=require('jsdom');
const html=fs.readFileSync('index.html','utf8');
const errs=[];
const dom=new JSDOM(html,{runScripts:'dangerously',url:'https://x.test/',pretendToBeVisual:true,
 beforeParse(w){w.matchMedia=w.matchMedia||(q=>({matches:false,media:q,addEventListener(){},removeEventListener(){}}));
 w.requestIdleCallback=cb=>setTimeout(()=>cb({timeRemaining:()=>8}),0);w.scrollTo=()=>{};
 w.HTMLElement.prototype.scrollIntoView=function(){};w.URL.revokeObjectURL=()=>{};
 w.addEventListener('error',e=>errs.push(String(e.message)));}});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 await sleep(1600);
 const {window}=dom,{document}=window;
 const data=window.PHONE_DATA||[];
 const NEW=['hua-mate70air','red-k100','oppo-findn6','vivo-x300s','honor-500p','xia-17max','apple-17e','moto-razrfold'];
 let ok=0,bad=0;
 const chk=(n,c,extra='')=>{ c?ok++:bad++; console.log(`${c?'PASS':'FAIL'}  ${n}${extra?'  → '+extra:''}`); };
 // 1) 新机型都在数据里且字段齐
 for(const id of NEW){
  const p=data.find(x=>x.id===id);
  chk(`新机型存在 ${id}`, !!p, p?p.name:'');
 }
 const p1=data.find(x=>x.id==='vivo-x300s');
 chk('vivo X300s 影像已修正「亿像素」笔误', !/亿像素超广角/.test(p1.camera), p1.camera.slice(0,40));
 const p2=data.find(x=>x.id==='red-k100');
 chk('REDMI K100 系统取 HyperOS 4', p2.os==='Xiaomi HyperOS 4', p2.os);
 const p3=data.find(x=>x.id==='honor-100');
 chk('荣耀 100 无价时价格类型为 price_pending', p3.priceType==='price_pending'&&p3.priceCN===null, p3.priceType);
 const p4=data.find(x=>x.id==='hua-changxiang80');
 chk('畅享 80 处理器写「厂商未公布…」而非编造型号', /未公布/.test(p4.chip), p4.chip);
 // 2) 首页搜索能搜到新机型
 const q=document.getElementById('searchInput');
 async function search(t){q.value=t;q.dispatchEvent(new window.Event('input',{bubbles:true}));
  await sleep(320);
  for(let i=0;i<300;i++){const g=document.getElementById('phoneGrid');if(g&&g.dataset.painting==='0')break;await sleep(20);}
  return [...document.querySelectorAll('#phoneGrid .phone-card')].length;}
 window.scrollTo=()=>{};
 for(const t of ['Mate 70 Air','K100','Find N6','X300s','500 Pro']){
  const n=await search(t); chk(`搜「${t}」有结果且不是全量`, n>0&&n<485, n+' 张卡片');
 }
 q.value='';q.dispatchEvent(new window.Event('input',{bubbles:true}));
 await sleep(400);
 for(let i=0;i<300;i++){const g=document.getElementById('phoneGrid');if(g&&g.dataset.painting==='0')break;await sleep(20);}
 // 3) 详情页：官方未公布徽标 + 缺价文案
 await search('畅享 80');   // 卡片分批绘制，先筛到目标，否则详情按钮还没画出来
 const btn=document.querySelector('#phoneGrid [data-detail="hua-changxiang80"]');
 if(btn)btn.click();
 await sleep(400);
 const rows=[...document.querySelectorAll('#detailModal .detail-row')];
 chk('详情已渲染出参数行', rows.length>0, rows.length+' 行');
 const chipRow=rows.find(r=>r.querySelector('span')&&r.querySelector('span').textContent.trim()==='处理器');
 chk('详情里处理器显示「厂商未公开…」而不是空白或占位原文',
     !!chipRow&&/厂商未公[开布]处理器型号/.test(chipRow.querySelector('b').textContent),
     chipRow?chipRow.querySelector('b').textContent.trim():'NONE');
 chk('处理器这一行的状态徽标是「官方未公布」',
     !!chipRow&&/官方未公布/.test(chipRow.querySelector('small').textContent),
     chipRow?chipRow.querySelector('small').textContent.trim():'NONE');
 // 4) 容量组合修复：不再有「>」结尾
 const junk=data.filter(p=>/[>＞]\s*$/.test(String(p.storage||'')));
 chk('容量组合不再带「>」', junk.length===0, junk.map(p=>p.name).join(','));
 const k70=data.find(p=>p.id==='xiaomi-z20992098425');
 chk('K70 至尊版容量组合保留 1TB 事实', /1TB/.test(k70.storage), k70.storage);
 console.log(`\n${ok} 通过 / ${bad} 失败；脚本错误 ${errs.length}`);
 process.exit(bad||errs.length?1:0);
})();
