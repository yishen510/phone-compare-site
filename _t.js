
const phones=JSON.parse(process.argv[2]);
const esc=s=>String(s??'');
const toast=m=>console.log('TOAST:',m);
/* ===== 参数工具层（详情 / 对比 / 筛选共用，消除重复实现） ===== */
function specList(p){return Array.isArray(p&&p.specs)?p.specs.filter(g=>g&&Array.isArray(g.items)):[];}
function specValueOf(p,group,label){const g=specList(p).find(x=>x.group===group);if(!g)return '—';const it=g.items.find(x=>Array.isArray(x)&&x[0]===label);return it?String(it[1]??''):'—';}
function specFind(p,label){for(const g of specList(p)){const it=g.items.find(x=>Array.isArray(x)&&x[0]===label);if(it)return String(it[1]??'');}return '';}
function specNum(text,re){const m=String(text||'').match(re);return m?Number(m[1]):null;}
function specUnion(items){const map=new Map();(items||[]).forEach(p=>specList(p).forEach(g=>{if(!map.has(g.group))map.set(g.group,new Set());g.items.forEach(it=>{if(Array.isArray(it)&&it[0])map.get(g.group).add(it[0]);});}));return [...map.entries()].map(([group,set])=>({group,labels:[...set]}));}
function specGroupDiffers(items,g,l){const norm=v=>String(v||'').trim().replace(/\s+/g,' ').toLowerCase();const vals=(items||[]).map(p=>specValueOf(p,g,l)).filter(v=>v&&v!=='—');return new Set(vals.map(norm)).size>1;}
const SPEC_BLOCK_CACHE=new Map();
function buildSpecBlockHtml(p){
 const key=(p&&p.id)||'';
 if(key&&SPEC_BLOCK_CACHE.has(key))return SPEC_BLOCK_CACHE.get(key);
 const groups=specList(p);
 if(!groups.length)return '';
 const total=Number(p.specFieldCount)||groups.reduce((n,g)=>n+g.items.length,0);
 const html=`<div class="spec-block"><div class="spec-head"><b>完整参数</b><span>${total} 项 · ${esc(p.specSourceName||'第三方参数站')}</span></div><label class="spec-search"><span>⌕</span><input type="search" class="spec-search-input" placeholder="搜索参数（如 电池 / 重量 / WiFi）" autocomplete="off"><em class="spec-search-count" hidden></em></label>${groups.map((g,gi)=>`<details class="spec-group"${gi===0?' open':''}><summary>${esc(g.group)}<span>${g.items.length} 项</span></summary><div class="spec-rows">${g.items.map(it=>`<div class="spec-row"><span>${esc(it[0])}</span><b>${esc(it[1])}</b></div>`).join('')}</div></details>`).join('')}<p class="spec-note">参数来自 ${esc(p.specSourceName||'第三方参数站')}，仅供交叉参考；权威值以厂商官方规格页为准。${p.specSource?`<a href="${esc(p.specSource)}" target="_blank" rel="noopener">参数来源 ↗</a>`:''}</p></div>`;
 if(key)SPEC_BLOCK_CACHE.set(key,html);
 return html;
}
function buildSpecRowsHtml(items,sections,diffOnly){return (sections||[]).map(sec=>{const labels=diffOnly?sec.labels.filter(l=>specGroupDiffers(items,sec.group,l)):sec.labels;if(!labels.length)return '';return `<tr class="compare-group-row"><th colspan="${(items||[]).length+1}">${esc(sec.group)}</th></tr>`+labels.map(l=>`<tr class="${specGroupDiffers(items,sec.group,l)?'is-different':'is-same'}"><th>${esc(l)}${specGroupDiffers(items,sec.group,l)?'<span class="difference-tag">有差异</span>':'<span class="same-tag">相同/一致</span>'}</th>${items.map(p=>`<td>${esc(specValueOf(p,sec.group,l))}<small class="compare-evidence secondary">第三方参数站</small></td>`).join('')}</tr>`).join('');}).join('');}
function csvCell(v){const s=String(v??'').replace(/\r?\n/g,' ');return /[",]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;}
function buildCompareCsv(items){const base=[['屏幕','display'],['处理器','chip'],['影像','camera'],['电池','battery'],['充电','charging'],['重量','weight'],['存储','storage'],['首发参考价','priceCN']];const lines=[['对比项目',...items.map(p=>p.name)]];base.forEach(([label,key])=>lines.push([label,...items.map(p=>key==='priceCN'?(Number.isFinite(Number(p.priceCN))?String(p.priceCN):'待核验'):String(p[key]??''))]));specUnion(items).forEach(sec=>{lines.push([`【${sec.group}】`,...items.map(()=>'')]);sec.labels.forEach(l=>lines.push([l,...items.map(p=>specValueOf(p,sec.group,l))]));});return lines.map(r=>r.map(csvCell).join(',')).join('\r\n');}
function downloadText(filename,text){try{const blob=new Blob(['\ufeff'+text],{type:'text/csv;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}catch(e){toast('导出失败：'+e.message);}}
const HW_CACHE=new Map();
function hwOf(p){
 const k=(p&&p.id)||'';
 if(k&&HW_CACHE.has(k))return HW_CACHE.get(k);
 const bat=specNum(specFind(p,'电池容量'),/(\d{3,5})\s*mAh/i)??specNum(p&&p.battery,/(\d{3,5})\s*mAh/i);
 const wt=specNum(specFind(p,'重量'),/(\d{2,3}(?:\.\d)?)\s*g/i)??specNum(p&&p.weight,/(\d{2,3}(?:\.\d)?)\s*g/i);
 const hz=specNum(specFind(p,'屏幕刷新率'),/(\d{2,3})\s*Hz/i)??specNum(p&&p.display,/(\d{2,3})\s*Hz/i);
 const st=String((p&&p.storage)||specFind(p,'ROM容量')||'');
 const gbs=(st.match(/(\d{2,4})\s*GB/gi)||[]).map(x=>Number(String(x).replace(/\D/g,'')));
 const tbs=(st.match(/(\d)\s*TB/gi)||[]).map(x=>Number(String(x).replace(/\D/g,''))*1024);
 const all=[...gbs,...tbs].filter(Number.isFinite);
 const out={bat,wt,hz,storage:all.length?Math.max(...all):null};
 if(k)HW_CACHE.set(k,out);
 return out;
}

const items=phones;
console.log('unionGroups=',specUnion(items).length);
console.log('hw0=',JSON.stringify(hwOf(items[0])));
console.log('hw1=',JSON.stringify(hwOf(items[1])));
const csv=buildCompareCsv(items);
console.log('csvLines=',csv.split('\r\n').length,'| header=',csv.split('\r\n')[0]);
console.log('hasGroupMarker=',csv.includes('【屏幕】'),'| hasQuoted=',/"/.test(csv));
console.log('specBlockLen=',buildSpecBlockHtml(items[0]).length,'| cacheHit=',buildSpecBlockHtml(items[0])===buildSpecBlockHtml(items[0]));
