/* 纯 Node 微基准：只验证 esc / money 两个热点的算法级差异（不依赖浏览器与布局，波动小）。
   用途：系统级 bench 波动大时，用这组数字证明「优化本身有效」，避免把噪声当收益。 */
const N=200000;
const base=['iPhone 17 Pro','小米 15','三星 Galaxy S25+','HUAWEI Mate 70 RS 非凡大师','ROG 游戏手机 9','vivo X300 Ultra','魅族 Lucky 08'];
const pool=[];
for(let i=0;i<2000;i++){
 /* 约 1/7 带需要转义的字符，更接近真实混合样本 */
 pool.push(i%7===0?base[i%base.length]+' & <test> "x"' : base[i%base.length]);
}

/* ---------- esc ---------- */
const escOld=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ESC_MAP={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'};
const ESC_TEST=/[&<>"']/;
const escNew=s=>{const t=String(s??'');return ESC_TEST.test(t)?t.replace(/[&<>"']/g,c=>ESC_MAP[c]):t;};

function run(fn,label,n){
 for(let i=0;i<20000;i++)fn(pool[i%pool.length]);           // warmup
 const t0=process.hrtime.bigint();
 let sink=0;
 for(let i=0;i<n;i++)sink+=fn(pool[i%pool.length]).length;   // 防止被优化掉
 const t1=process.hrtime.bigint();
 const ms=Number(t1-t0)/1e6;
 console.log(`  ${label}: ${ms.toFixed(1)} ms / ${n} 次  (${(n/ms*1000).toFixed(0)}k ops/s)  sink=${sink%1000}`);
 return ms;
}

console.log('=== esc 新旧对比（20 万次） ===');
const e1=run(escOld,'旧实现',N);
const e2=run(escNew,'新实现',N);
console.log(`  → 提速 ${((e1/e2-1)*100).toFixed(1)}%`);

/* ---------- money ---------- */
const prices=[];
for(let i=0;i<2000;i++)prices.push(999+((i*137)%9000));     // 取值集合有限，接近真实价格分布
const moneyOld=n=>n!==null&&n!==undefined&&n!==''&&Number.isFinite(Number(n))?'¥'+Number(n).toLocaleString('zh-CN'):'待核实';
const MONEY_CACHE=new Map();
const moneyNew=n=>{
 if(n===null||n===undefined||n==='')return '待核实';
 const v=Number(n);
 if(!Number.isFinite(v))return '待核实';
 let s=MONEY_CACHE.get(v);
 if(s===undefined){s='¥'+v.toLocaleString('zh-CN');MONEY_CACHE.set(v,s);}
 return s;
};

console.log('\n=== money 新旧对比（20 万次） ===');
const m1=run(moneyOld,'旧实现',N);
const m2=run(moneyNew,'新实现',N);
console.log(`  → 提速 ${((m1/m2-1)*100).toFixed(1)}%`);

console.log('\n=== 换算到一次整页渲染的节省（按实测调用量） ===');
const escCalls=7275+5335;   // 卡片 15×485 + 表格 11×485
const moneyCalls=485+485;
console.log(`  esc  ${escCalls} 次：${(escCalls*(e1-e2)/N).toFixed(1)} ms`);
console.log(`  money ${moneyCalls} 次：${(moneyCalls*(m1-m2)/N).toFixed(1)} ms`);
