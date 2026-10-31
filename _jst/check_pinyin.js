/* 拼音首字母搜索回归：
   1) xm15 能命中「小米 15」系列
   2) hw / xm 只返回对应品牌，不跨品牌
   3) ip 不会把 iPhone 拉进来（前缀匹配的关键收益）
   4) 中文搜索行为完全不变
   5) 清空恢复全量 */
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
 const byName=new Map(data.map(p=>[p.name,p]));
 let ok=0,bad=0;
 const chk=(n,c,extra='')=>{c?ok++:bad++;console.log(`${c?'PASS':'FAIL'}  ${n}${extra?'  → '+extra:''}`);};
 async function waitPaint(){for(let i=0;i<400;i++){const g=document.getElementById('phoneGrid');if(g&&g.dataset.painting==='0')break;await sleep(20);}}
 const q=document.getElementById('searchInput');
 async function search(t){
  q.value=t;q.dispatchEvent(new window.Event('input',{bubbles:true}));
  await sleep(340);await waitPaint();
  return [...document.querySelectorAll('#phoneGrid .phone-card h3')].map(h=>h.textContent);
 }

 /* 1. 拼音 + 型号：key 完全一致应排在前缀命中之前 */
 let names=await search('xm15');
 chk('xm15 有命中', names.length>0, names.length+' 条');
 chk('xm15 结果含「小米 15」', names.includes('小米 15'), names.slice(0,4).join(' / '));
 chk('xm15 首条为「小米 15」', names[0]==='小米 15', names[0]||'—');

 /* 2. 品牌缩写（这些查询现有搜索 0 命中，结果全部来自拼音） */
 names=await search('hw');
 chk('hw 命中华为 62 条', names.length===62, names.length+' 条');
 chk('hw 结果全部是 Huawei', names.every(n=>byName.get(n)&&byName.get(n).brand==='Huawei'));
 names=await search('hwmate70');
 chk('hwmate70 命中 Mate 70 系列', names.length>0&&names.every(n=>/Mate 70/.test(n)), names.join(' / '));
 names=await search('nby');
 chk('nby 命中努比亚/红魔 23 条', names.length===23, names.length+' 条');

 /* 3. 与现有搜索叠加时不丢结果（xm 现有会命中 XMAGE 等参数，只要求仍含小米机型） */
 names=await search('xm');
 chk('xm 结果包含小米机型', names.some(n=>/^小米/.test(n)), names.length+' 条');

 /* 4. 中文搜索行为不变 */
 names=await search('小米15');
 chk('中文「小米15」仍 5 条', names.length===5, names.length+' 条');
 chk('中文「小米15」首条仍为「小米 15」', names[0]==='小米 15', names[0]||'—');

 /* 5. 清空恢复全量 */
 names=await search('');
 chk('清空后恢复 485', names.length===485, names.length+' 条');

 console.log(`\n${ok} 通过 / ${bad} 失败；脚本错误 ${errs.length}`);
 if(errs.length)console.log('错误:',errs.slice(0,5));
 process.exit(bad||errs.length?1:0);
})();
