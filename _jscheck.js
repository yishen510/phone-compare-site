
/* Phone Index front-end. All scoring/ranking and recommendations fail closed. */
(function(){
'use strict';
const phones=Array.isArray(window.PHONE_DATA)?window.PHONE_DATA:[];
const $=id=>document.getElementById(id);
const state={brands:new Set(),types:new Set(),compare:[],view:'cards',priorities:new Set(),recommendOnly:false,compareDiffOnly:false,detailId:null,favs:new Set(),favOnly:false,priceMin:null,priceMax:null,density:'roomy'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money=n=>n!==null&&n!==undefined&&n!==''&&Number.isFinite(Number(n))?'¥'+Number(n).toLocaleString('zh-CN'):'待核实';
const hasQuote=p=>!!p&&["verified","api_candidate"].includes(p.livePriceStatus)&&Number.isFinite(Number(p.livePrice));
function fmtCheckedAt(v){if(!v)return '时间待核验';const d=new Date(v);return Number.isNaN(d.getTime())?String(v):d.toLocaleString('zh-CN',{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});}
/* 渠道报价只作参考展示：不写入 priceCN、不改变任何审核/排名资格。 */
const QUOTE_BATCH_SIZE=5;
const QUOTE_BATCH_TIMEOUT_MS=35000;
let quoteRunToken=0;
let quoteRunning=false;
const quoteState=new Map();
const QUOTE_LABELS={
 idle:['未查询','尚未发起渠道报价查询'],
 loading:['查询中','正在请求渠道报价…'],
 none:['暂无报价','已查询，未找到型号与容量都匹配的商品'],
 error:['查询失败','请稍后重试'],
 skipped:['暂无报价','该机型尚未确定可报价容量'],
 unknown_phone:['暂无报价','后端机型库未同步该机型'],
 not_requested:['待查询','等待下一批请求'],
 needs_credentials:['未授权','服务端未配置报价 API Key'],
 rate_limited:['查询受限','请求过于频繁，请稍后重试']
};
const quoteShort=(s,n)=>String(s||'').length>n?String(s).slice(0,n)+'…':String(s||'');
function quoteTone(status){if(status==='loading')return 'is-loading';if(status==='error')return 'is-error';if(status==='needs_credentials'||status==='rate_limited')return 'is-warn';if(status==='none'||status==='skipped'||status==='unknown_phone')return 'is-none';return 'is-idle';}
function quoteBlock(p,compact){
 const cls=compact?' is-compact':'';
 if(hasQuote(p)){
  const sub=[p.livePriceChannel||'渠道待确认',p.livePriceSku||''].filter(Boolean).join(' · ');
  const link=p.livePriceSource?` · <a class="quote-mini-link" href="${esc(p.livePriceSource)}" target="_blank" rel="noopener nofollow">商品页 ↗</a>`:'';
  return `<small class="live-quote is-quoted${cls}" data-live-price="${esc(p.id)}"><span class="quote-main">渠道报价 ${money(p.livePrice)}</span><span class="quote-sub">${esc(sub)}${link}</span><span class="quote-status">查询成功 · ${esc(fmtCheckedAt(p.livePriceCheckedAt))} · 待人工核验</span></small>`;
 }
 const st=quoteState.get(p.id)||{status:'idle',message:''};
 const label=QUOTE_LABELS[st.status]||QUOTE_LABELS.idle;
 const message=quoteShort(st.message||label[1],compact?44:70);
 return `<small class="live-quote ${quoteTone(st.status)}${cls}" data-live-price="${esc(p.id)}"><span class="quote-main">${esc(label[0])}</span><span class="quote-sub">${esc(message)}</span></small>`;
}
function refreshQuoteSlots(id){
 const p=phones.find(x=>x.id===id);if(!p)return;
 document.querySelectorAll('[data-live-price]').forEach(el=>{
  if(el.dataset.livePrice!==id)return;
  el.outerHTML=quoteBlock(p,el.classList.contains('is-compact'));
 });
}
function setQuoteState(id,status,message){
 quoteState.set(id,{status,message:message||'',at:Date.now()});
 refreshQuoteSlots(id);
 refreshDetailIfOpen(id);
}
function refreshDetailIfOpen(id){
 if(state.detailId!==id)return;
 const modal=$('detailModal');if(!modal||modal.hidden)return;
 const top=modal.scrollTop;
 detail(id);
 modal.scrollTop=top;
}
function quoteDetailCard(p){
 const st=quoteState.get(p.id)||{status:'idle',message:''};
 const retryLabel=st.status==='loading'?'查询中…':'重新查询';
 if(hasQuote(p)){
  const sub=[p.livePriceChannel||'渠道待确认',p.livePriceSku||''].filter(Boolean).join(' · ');
  const link=p.livePriceSource?`<a class="quote-link" href="${esc(p.livePriceSource)}" target="_blank" rel="noopener nofollow">查看商品来源 ↗</a>`:'';
  return `<div class="price-card channel is-live"><span class="price-tag">渠道报价 · 参考</span><strong class="price-number">${money(p.livePrice)}</strong><span class="quote-verify">待人工核验</span><span class="price-sub">${esc(sub)}</span><div class="quote-meta"><div><span>查询状态</span><b>查询成功 · 待人工核验</b></div><div><span>报价时间</span><b>${esc(fmtCheckedAt(p.livePriceCheckedAt))}</b></div>${p.livePriceTitle?`<div><span>商品标题</span><b>${esc(p.livePriceTitle)}</b></div>`:''}<div><span>数据来源</span><b>${esc(p.livePriceProvider||'hainan_discount_v2')}</b></div></div>${link}<span class="quote-hint">${esc(p.livePriceNote||'检索报价不是订单结算承诺；购买前请打开商品页核对版本、新旧、库存与优惠资格。')}</span><button class="quote-one-btn" type="button" data-quote-one="${esc(p.id)}">${retryLabel}</button></div>`;
 }
 const label=QUOTE_LABELS[st.status]||QUOTE_LABELS.idle;
 const isBusy=st.status==='loading';
 return `<div class="price-card channel ${quoteTone(st.status)}"><span class="price-tag">渠道报价 · 参考</span><strong class="price-number">${esc(label[0])}</strong><span class="price-sub">${esc(st.message||label[1])}</span><span class="quote-hint">未取得精确匹配的报价时不会显示金额，也不代表该机型没有销售；这不影响官方首发价的展示。</span><button class="quote-one-btn" type="button" data-quote-one="${esc(p.id)}" ${isBusy?'disabled':''}>${isBusy?'查询中…':'查询本机报价'}</button></div>`;
}
const validDate=p=>p.launchMonth||`${p.year||''}`;
function setText(id,v){if($(id))$(id).textContent=v;}
function toast(msg){const el=$('toast');if(!el)return;el.textContent=msg;el.classList.add('show');clearTimeout(toast.t);toast.t=setTimeout(()=>el.classList.remove('show'),2300);}
/* fieldAudit 兼容两种形态：中文名数组（历史数据）与英文键对象。 */const AUDIT_FIELD_NAMES={display:'屏幕',chip:'处理器',camera:'影像',battery:'电池',charging:'充电',weight:'重量',storage:'容量组合',launchDate:'正式发布/开售日期',price:'官方首发起售价'};function auditEntry(p,k){const fa=p&&p.fieldAudit;if(!fa)return null;if(Array.isArray(fa)){const n=AUDIT_FIELD_NAMES[k];return fa.find(x=>x&&x.field===n)||null;}return fa[k]||null;}function field(p,k){const a=auditEntry(p,k);if(!a||!a.evidenceText||!a.sourceUrl)return '待核验';if(a.status==='verified_official_page_reviewed')return '已核验';if(a.status==='cross_checked_secondary_source')return '第三方核验';return '待核验';}
function pass(p){return !!(window.PhoneEligibility&&window.PhoneEligibility.modelPassed(p));}
function scoreLabel(p){return pass(p)&&Number.isFinite(p.score)?p.score:'未开放排名';}
function filtered(){const q=($('searchInput')?.value||'').trim().toLowerCase();let arr=phones.filter(p=>{
 const text=[p.name,p.brand,p.chip,p.camera,p.type].join(' ').toLowerCase();
 if(q&&!text.includes(q))return false;
 if(state.brands.size&&!state.brands.has(p.brand))return false;
 if(state.types.size&&!state.types.has(p.type))return false;
 const from=Number($('yearFrom')?.value||2021),to=Number($('yearTo')?.value||2026);if(p.year<Math.min(from,to)||p.year>Math.max(from,to))return false;
 if($('domesticOnly')?.checked&&!p.chinaOfficial)return false;
 if(state.favOnly&&!state.favs.has(p.id))return false;
 const __price=Number(p.priceCN);
 if(state.priceMin!=null&&(!Number.isFinite(__price)||__price<state.priceMin))return false;
 if(state.priceMax!=null&&(!Number.isFinite(__price)||__price>state.priceMax))return false;
 if(state.recommendOnly){if(!pass(p))return false;const tags=p.bestFor||[];if(state.priorities.size&&!Array.from(state.priorities).some(t=>tags.includes(t)))return false;const b=Number($('budgetSelect')?.value||0);if(b&&(p.livePriceStatus!=='verified'||!Number.isFinite(Number(p.livePrice))||Number(p.livePrice)>b))return false;}
 return true;
});const sort=$('sortSelect')?.value||'newest';arr.sort((a,b)=>{switch(sort){case'oldest':return a.year-b.year;case'priceAsc':return (a.priceCN||Infinity)-(b.priceCN||Infinity);case'priceDesc':return (b.priceCN||0)-(a.priceCN||0);case'weightAsc':return parseFloat(a.weight||999)-parseFloat(b.weight||999);case'screenAsc':return parseFloat(a.display||99)-parseFloat(b.display||99);case'scoreDesc':return pass(b)-pass(a);default:return (b.year-a.year)||String(b.launchMonth||'').localeCompare(a.launchMonth||'');}});return arr;}
function renderBrands(){const root=$('brandFilters');if(!root)return;const brands=[...new Set(phones.map(p=>p.brand))].sort();root.innerHTML=brands.map(b=>`<label class="brand-option"><input type="checkbox" value="${esc(b)}" ${state.brands.has(b)?'checked':''}><span>${esc(b)}</span></label>`).join('');root.querySelectorAll('input').forEach(i=>i.addEventListener('change',()=>{i.checked?state.brands.add(i.value):state.brands.delete(i.value);render();}));setText('brandCount',state.brands.size?`${state.brands.size} 已选`:'全部');}
function card(p){const chosen=state.compare.includes(p.id);return `<article class="phone-card"><div class="card-top"><span class="card-brand">${esc(p.brand)}</span><div class="card-top-right"><span class="card-year">${esc(validDate(p))}</span><button class="fav-btn${state.favs.has(p.id)?' is-on':''}" type="button" data-fav="${esc(p.id)}" aria-pressed="${state.favs.has(p.id)}" aria-label="收藏 ${esc(p.name)}">${state.favs.has(p.id)?'♥':'♡'}</button></div></div><h3>${esc(p.name)}</h3><p class="card-type">${esc(p.type||'旗舰手机')} · ${esc(p.market||'市场版本待核')}</p><div class="card-specs"><div><small>屏幕</small><strong>${esc((p.display||'—').split('；')[0])}</strong></div><div><small>处理器</small><strong>${esc(p.chip||'—')}</strong></div><div><small>电池</small><strong>${esc(p.battery||'—')}</strong></div><div><small>重量</small><strong>${esc(p.weight||'—')}</strong></div></div><div class="card-price"><div><small class="price-label">${p.priceType==='third_party_reference'?'参考价（第三方）':(p.priceType==='official_starting_price'?'官方起售价（容量待核）':'官方首发参考价')}</small><strong>${money(p.priceCN)}</strong>${quoteBlock(p)}</div><span class="audit-pill ${pass(p)?'audit-ok':'audit-pending'}">${pass(p)?'审核通过':'排名/推荐未开放'}</span></div><div class="card-actions"><button class="button button-dark button-small" data-detail="${esc(p.id)}">查看详情</button><button class="button button-light button-small" data-compare="${esc(p.id)}">${chosen?'已加入对比':'加入对比'}</button></div><p class="card-source"><a href="${esc(p.source||'#')}" target="_blank" rel="noopener">查看厂商来源 ↗</a></p></article>`;}
function renderTable(arr){return `<div class="table-wrap"><table class="phone-table"><thead><tr><th>机型</th><th>年份</th><th>屏幕</th><th>芯片</th><th>电池</th><th>重量</th><th>官方首发参考价</th><th>操作</th></tr></thead><tbody>${arr.map(p=>`<tr><td><b>${esc(p.name)}</b><small>${esc(p.brand)}</small></td><td>${esc(validDate(p))}</td><td>${esc(p.display||'—')}</td><td>${esc(p.chip||'—')}</td><td>${esc(p.battery||'—')}</td><td>${esc(p.weight||'—')}</td><td>${money(p.priceCN)}${quoteBlock(p,true)}</td><td><button class="text-button" data-detail="${esc(p.id)}">详情</button> <button class="text-button" data-compare="${esc(p.id)}">对比</button></td></tr>`).join('')}</tbody></table></div>`;}
function render(){renderBrands();const arr=filtered();setText('statModels',phones.length);setText('statBrands',new Set(phones.map(p=>p.brand)).size);setText('resultCount',arr.length);setText('currentFilterLabel',state.recommendOnly?'已通过准入的推荐候选':'全部代表机型');if($('phoneGrid'))$('phoneGrid').innerHTML=state.view==='table'?renderTable(arr):arr.map(card).join('');if($('emptyState')){ $('emptyState').hidden=arr.length!==0;const h=$('emptyState').querySelector('h3'),p=$('emptyState').querySelector('p');if(state.recommendOnly){if(h)h.textContent='暂无通过准入审核的推荐机型';if(p)p.textContent='当前机型库尚无同时通过整机审核、必需字段证据及推荐资格检查的机型，因此不会生成正式购买推荐。可继续浏览参数或手动对比。';}else{if(h)h.textContent='没有找到符合条件的机型';if(p)p.textContent='试着移除一项筛选，或扩大年份范围。';}}if($('phoneGrid'))$('phoneGrid').hidden=arr.length===0;if($('phoneGrid'))$('phoneGrid').classList.toggle('is-compact',state.density==='compact');updateCompare();syncUrlState();}
function openModal(id,html){const m=$(id);if(!m)return;m.innerHTML=html;m.hidden=false;if($('modalBackdrop'))$('modalBackdrop').hidden=false;document.body.classList.add('modal-open');}
function closeModal(){['detailModal','compareModal','modalBackdrop'].forEach(id=>{if($(id))$(id).hidden=true;});document.body.classList.remove('modal-open');state.detailId=null;}
function detail(id){
 const p=phones.find(x=>x.id===id);if(!p)return;
 state.detailId=id;
 const labels={display:'屏幕',chip:'处理器',camera:'影像',battery:'电池',charging:'充电',weight:'重量',storage:'存储',launchDate:'发布日期/开售日期'};
 const keys=Object.keys(labels);
 const official=Number.isFinite(Number(p.priceCN))?money(p.priceCN):'待核验';
 const channel=quoteDetailCard(p);
 const specGroups=Array.isArray(p.specs)?p.specs:[];
 const specTotal=Number(p.specFieldCount)||specGroups.reduce((n,g)=>n+((g.items||[]).length),0);
 const specBlock=specGroups.length?`<div class="spec-block"><div class="spec-head"><b>完整参数</b><span>${specTotal} 项 · ${esc(p.specSourceName||'第三方参数站')}</span></div>${specGroups.map((g,gi)=>`<details class="spec-group"${gi===0?' open':''}><summary>${esc(g.group)}<span>${(g.items||[]).length} 项</span></summary><div class="spec-rows">${(g.items||[]).map(it=>`<div class="spec-row"><span>${esc(it[0])}</span><b>${esc(it[1])}</b></div>`).join('')}</div></details>`).join('')}<p class="spec-note">参数来自 ${esc(p.specSourceName||'第三方参数站')}，仅供交叉参考；权威值以厂商官方规格页为准。${p.specSource?`<a href="${esc(p.specSource)}" target="_blank" rel="noopener">参数来源 ↗</a>`:''}</p></div>`:'';
 openModal('detailModal',`<button class="modal-close" data-close aria-label="关闭">×</button><p class="eyebrow">MODEL DETAILS</p><h2 id="detailTitle">${esc(p.name)}</h2><p>${esc(p.selling||'')}</p><div class="price-pair"><div class="price-card official"><span class="price-tag">官方首发价 · 非当前售价</span><strong class="price-number">${official}</strong><span class="price-sub">${esc(p.priceText||'官方首发起售价，不代表当前渠道成交价')}</span><span class="price-sub ${field(p,'price')==='已核验'?'verified':'pending'}">价格字段：${field(p,'price')}</span>${p.priceSource?`<a class="quote-link" href="${esc(p.priceSource)}" target="_blank" rel="noopener">价格来源 ↗</a>`:''}</div>${channel}</div><div class="detail-grid">${keys.map(k=>{const a=auditEntry(p,k);return `<div class="detail-row"><span>${labels[k]}</span><b>${esc(a?.valueAtAudit??(k==='launchDate'?(p.launchDateDisplay||p.launchMonth||'待核验'):(p[k]||'待核验')))}</b><small class="${field(p,k)==='已核验'?'verified':(field(p,k)==='第三方核验'?'secondary':'pending')}">${field(p,k)}${a?.evidenceText?' · '+esc(a.evidenceText):''}</small>${a?.sourceUrl?`<a href="${esc(a.sourceUrl)}" target="_blank" rel="noopener">字段来源 ↗</a>`:''}</div>`}).join('')}</div>${specBlock}<p class="modal-warning">${pass(p)?'该机型已通过准入审核。':'该机型尚未通过整机审核，不能参与排名或自动推荐。字段来源链接不等于整机审核通过。'} 渠道报价仅作参考，不会改变该机型的审核、排名或推荐状态。</p><p><a href="${esc(p.source||'#')}" target="_blank" rel="noopener">打开厂商页面 ↗</a></p>`);
}
function updateCompare(){const items=state.compare.map(id=>phones.find(p=>p.id===id)).filter(Boolean);setText('headerCompareCount',items.length);setText('dockCount',items.length);const dock=$('compareDock');if(dock)dock.hidden=!items.length;if($('dockItems'))$('dockItems').innerHTML=items.map(p=>`<span class="dock-item">${esc(p.name)} <button data-remove="${esc(p.id)}" aria-label="移除">×</button></span>`).join('');}
function toggleCompare(id){if(state.compare.includes(id)){state.compare=state.compare.filter(x=>x!==id);}else if(state.compare.length>=4){toast('最多同时对比 4 款手机');return;}else state.compare.push(id);render();}
function compare(){
 const items=state.compare.map(id=>phones.find(p=>p.id===id)).filter(Boolean);
 if(items.length<2){toast('至少加入 2 款手机再开始对比');return;}
 const rows=[['屏幕','display'],['处理器','chip'],['影像','camera'],['电池','battery'],['充电','charging'],['重量','weight'],['存储','storage'],['首发参考价','priceCN']];
 const value=(p,key)=>key==='priceCN'?(Number.isFinite(Number(p[key]))?money(p[key]):'待核验'):(p[key]||'待核验');
 const normalize=v=>String(v??'').trim().replace(/\s+/g,' ').toLowerCase();
 const differs=key=>new Set(items.map(p=>normalize(value(p,key)))).size>1;
 const shown=rows.filter(([label,key])=>!state.compareDiffOnly||differs(key));
 const specSections=(()=>{const map=new Map();items.forEach(p=>(p.specs||[]).forEach(g=>{if(!map.has(g.group))map.set(g.group,new Set());(g.items||[]).forEach(it=>map.get(g.group).add(it[0]));}));return [...map.entries()].map(([group,set])=>({group,labels:[...set]}));})();
 const specVal=(p,g,l)=>{const grp=(p.specs||[]).find(x=>x.group===g);const it=grp&&(grp.items||[]).find(x=>x[0]===l);return it?it[1]:'—';};
 const specDiffers=(g,l)=>{const vals=items.map(p=>specVal(p,g,l)).filter(v=>v&&v!=='—');return new Set(vals.map(normalize)).size>1;};
 const specRowsHtml=specSections.map(sec=>{const labels=state.compareDiffOnly?sec.labels.filter(l=>specDiffers(sec.group,l)):sec.labels;if(!labels.length)return '';return `<tr class="compare-group-row"><th colspan="${items.length+1}">${esc(sec.group)}</th></tr>`+labels.map(l=>`<tr class="${specDiffers(sec.group,l)?'is-different':'is-same'}"><th>${esc(l)}${specDiffers(sec.group,l)?'<span class="difference-tag">有差异</span>':'<span class="same-tag">相同/一致</span>'}</th>${items.map(p=>`<td>${esc(specVal(p,sec.group,l))}<small class="compare-evidence secondary">第三方参数站</small></td>`).join('')}</tr>`).join('');}).join('');
 const specCount=specSections.reduce((n,s)=>n+s.labels.length,0);
 const diffTotal=rows.filter(([l,k])=>differs(k)).length+specSections.reduce((n,s)=>n+s.labels.filter(l=>specDiffers(s.group,l)).length,0);
 const bestFor=p=>Array.isArray(p.bestFor)&&p.bestFor.length?p.bestFor.join('、'):'暂无经过审核的用途标签';
 const fitText=p=>p.selling||'请结合预算、尺寸、影像、续航等实际需求判断；当前数据不自动生成胜负结论。';
 openModal('compareModal',`
 <button class="modal-close" data-close aria-label="关闭">×</button>
 <p class="eyebrow">SIDE-BY-SIDE · 差异优先</p>
 <h2 id="compareTitle">选机对比</h2>
 <p class="compare-lead">先看不同点，再按自己的使用场景做决定。绿色标记表示数值/描述存在差异，不代表哪款更强。</p>
 <div class="compare-toolbar"><span class="compare-summary">已选 ${items.length} 款 · ${diffTotal} 项存在差异${specCount?'（含 '+specCount+' 项完整参数）':''}</span><button class="button button-light button-small" data-diff-only="true">${state.compareDiffOnly?'显示全部参数':'仅看差异'}</button></div>
 <div class="compare-product-grid">${items.map(p=>`<article class="compare-product"><span class="compare-brand">${esc(p.brand)}</span><h3>${esc(p.name)}</h3><p>${esc(p.type||'旗舰手机')} · ${esc(validDate(p))}</p><strong class="compare-price">${esc(value(p,'priceCN'))}</strong><small>官方首发参考价，非实时售价</small><button class="text-button" data-remove="${esc(p.id)}">从对比中移除 ×</button></article>`).join('')}</div>
 <div class="table-wrap compare-table-wrap"><table class="compare-table"><thead><tr><th>对比项目</th>${items.map(p=>`<th>${esc(p.name)}</th>`).join('')}</tr></thead><tbody><tr class="compare-group-row"><th colspan="${items.length+1}">核心参数</th></tr>${shown.map(([label,key])=>`<tr class="${differs(key)?'is-different':'is-same'}"><th>${label}${differs(key)?'<span class="difference-tag">有差异</span>':'<span class="same-tag">相同/一致</span>'}</th>${items.map(p=>`<td>${esc(value(p,key))}${field(p,key==='priceCN'?'price':key)==='已核验'?'<small class="compare-evidence">字段已核验</small>':(field(p,key==='priceCN'?'price':key)==='第三方核验'?'<small class="compare-evidence secondary">第三方核验 · 仅供参考</small>':'<small class="compare-evidence pending">待核验 · 仅供参考</small>')}</td>`).join('')}</tr>`).join('')}${specRowsHtml}${(shown.length||specRowsHtml)?'':'<tr><td colspan="'+(items.length+1)+'" class="compare-empty">这几款手机在当前展示字段上没有可见差异。</td></tr>'}</tbody></table></div>
 <p class="spec-note">「—」表示该机型尚未收录该项；完整参数来自中关村在线参数页，仅供交叉参考。</p>
 <div class="fit-guide"><div><span class="fit-kicker">HOW TO CHOOSE</span><h3>哪款更适合你？</h3><p>不凭单一参数判定“赢家”。根据你最在意的需求，优先核对下列用途说明和已核验字段。</p></div>${items.map(p=>`<article class="fit-card"><h4>${esc(p.name)}</h4><p>${esc(fitText(p))}</p><div class="fit-tags">${(Array.isArray(p.bestFor)?p.bestFor:[]).slice(0,4).map(x=>`<span>${esc(x)}</span>`).join('')||'<span>用途标签待核验</span>'}</div><p class="fit-caution">${pass(p)?'整机审核已通过':'整机审核未通过：不生成排名或自动推荐'}</p></article>`).join('')}</div>
 <p class="modal-warning">价格为官方首发参考价，不代表当前渠道价。差异高亮仅提示字段不同，不代表优劣；未通过审核的机型不会被授予排名或推荐资格。</p>`);
}
function setApiStatus(headline,message,tone){
 const el=$('priceApiStatus');if(!el)return;
 el.className='price-api-status '+(tone||'is-neutral');
 el.innerHTML='<strong>'+esc(headline)+'</strong><span>'+esc(message)+'</span>';
}
function setQuoteRunning(running){
 quoteRunning=running;
 const btn=$('quoteQueryBtn');
 if(btn){btn.textContent=running?'停止查询':'批量查询报价';btn.classList.toggle('is-running',running);}
}
function setQuoteProgress(text){setText('quoteProgress',text);}
function apiBaseUrl(){return String(window.PHONE_API_BASE_URL||'').replace(/\/+$/,'');}
/* 后端是否可用：显式配置了域名，或本机同源运行（python price_server.py 托管本页）。
   纯静态托管（GitHub Pages）且未配置域名时不发请求，避免每次打开都 404。 */
function apiConfigured(){const b=apiBaseUrl();if(b)return true;const h=String(location.hostname||'');return h==='127.0.0.1'||h==='localhost'||h==='[::1]'||location.protocol==='file:';}
async function fetchJson(url,timeoutMs){
 const controller=typeof AbortController!=='undefined'?new AbortController():null;
 const timer=setTimeout(()=>{if(controller)controller.abort();},timeoutMs);
 try{
  const res=await fetch(url,{cache:'no-store',signal:controller?controller.signal:undefined});
  let data=null;
  try{data=await res.json();}catch(e){data=null;}
  return {res,data};
 }finally{clearTimeout(timer);}
}
function applyQuote(phoneId,item,asOf){
 const p=phones.find(x=>x.id===phoneId);if(!p)return false;
 const price=Number(item.price);
 if(!Number.isFinite(price))return false;
 p.livePrice=price;
 p.livePriceStatus='api_candidate';
 p.livePriceCheckedAt=item.checkedAt||asOf;
 p.livePriceSource=item.url;
 p.livePriceChannel=item.channel;
 p.livePriceSku=item.sku;
 p.livePriceTitle=item.offerTitle;
 p.livePriceNote=item.note;
 p.livePriceProvider=item.provider||'hainan_discount_v2';
 quoteState.set(phoneId,{status:'ok',message:'',at:Date.now()});
 refreshQuoteSlots(phoneId);
 refreshDetailIfOpen(phoneId);
 return true;
}
/* Batch query: every item is attached strictly by the phoneId echoed by the backend. */
async function queryQuotes(ids,opts){
 const options=opts||{};
 const queue=[...new Set(ids)].filter(id=>phones.some(p=>p.id===id));
 if(!queue.length)return {ok:0,none:0,fail:0,total:0,done:0};
 const token=++quoteRunToken;
 setQuoteProgress('已查 0/'+queue.length+' · 准备查询…');
 setQuoteRunning(true);
 let done=0,ok=0,none=0,fail=0;
 const total=queue.length;
 const update=()=>setQuoteProgress(`已查 ${done}/${total} · 有报价 ${ok} · 无报价 ${none}${fail?` · 失败 ${fail}`:''}`);
 update();
 let stopReason='';
 try{
  while(queue.length){
   if(token!==quoteRunToken)break;
   const batch=queue.splice(0,QUOTE_BATCH_SIZE);
   batch.forEach(id=>setQuoteState(id,'loading','正在请求渠道报价…'));
   let data=null,failure='';
   try{
    const r=await fetchJson(apiBaseUrl()+'/api/prices?ids='+encodeURIComponent(batch.join(',')),QUOTE_BATCH_TIMEOUT_MS);
    if(r.res.status===429){
     data={status:'rate_limited',message:(r.data&&r.data.message)||'请求过于频繁，请稍后重试。'};
    }else if(!r.res.ok){
     failure='后端返回 HTTP '+r.res.status;
    }else if(!r.data||typeof r.data!=='object'){
     failure='后端返回格式异常';
    }else data=r.data;
   }catch(err){
    failure=err&&err.name==='AbortError'?'请求超时（'+Math.round(QUOTE_BATCH_TIMEOUT_MS/1000)+' 秒）':'网络错误：'+((err&&err.message)||'无法连接后端');
   }
   if(failure){
    batch.forEach(id=>setQuoteState(id,'error',failure));
    fail+=batch.length;done+=batch.length;
    if(!stopReason)stopReason=failure;
    update();
    if(!options.continueOnError)break;
    continue;
   }
   if(data.status==='needs_credentials'){
    batch.forEach(id=>setQuoteState(id,'needs_credentials',data.message||'服务端未配置报价 API Key'));
    stopReason=data.message||'服务端未配置报价 API Key';
    fail+=batch.length;update();break;
   }
   if(data.status==='rate_limited'){
    batch.forEach(id=>setQuoteState(id,'rate_limited',data.message||'请求过于频繁'));
    stopReason=data.message||'请求过于频繁';
    fail+=batch.length;update();break;
   }
   const items=new Map();
   for(const item of (Array.isArray(data.items)?data.items:[])){
    if(item&&item.phoneId&&phones.some(p=>p.id===item.phoneId))items.set(item.phoneId,item);
   }
   const statuses=data.statuses&&typeof data.statuses==='object'?data.statuses:{};
   for(const id of batch){
    const item=items.get(id);
    if(item&&applyQuote(id,item,data.asOf)){ok++;done++;continue;}
    const s=statuses[id]||{};
    const status=s.status==='error'?'error':(s.status==='skipped'||s.status==='unknown_phone'||s.status==='not_requested')?'skipped':'none';
    setQuoteState(id,status,s.message||'已查询，未找到匹配型号与容量的商品');
    if(status==='error')fail++;else none++;
    done++;
   }
   update();
   if(data.status==='upstream_error'){stopReason=data.message||'上游查询失败';break;}
   await new Promise(resolve=>setTimeout(resolve,320));
  }
 }finally{
  if(token===quoteRunToken)setQuoteRunning(false);
 }
 if(stopReason)toast(stopReason);
 return {ok,none,fail,total,done,stopped:stopReason};
}
async function initQuoteApi(){
 if(!apiConfigured()){
  setApiStatus('报价 API 状态：未接入','未配置后端地址，当前只显示官方首发价与第三方参考价；渠道报价需部署 price_server.py 后在 api-config.js 填入域名。','is-warn');
  return;
 }
 let health=null;
 let lastErr=null;
 /* Render 免费实例空闲后会休眠，首次请求可能要等 30-60 秒冷启动，因此给两次机会。 */
 for(let attempt=0;attempt<2;attempt++){
  try{
   const r=await fetchJson(apiBaseUrl()+'/api/health',25000);
   if(!r.res.ok)throw new Error('HTTP '+r.res.status);
   health=r.data||{};
   lastErr=null;
   break;
  }catch(err){
   lastErr=err;
   if(attempt===0)await new Promise(resolve=>setTimeout(resolve,2500));
  }
 }
 if(!health){
  const reason=String((lastErr&&lastErr.message)||'无法连接后端');
  setApiStatus('报价 API 状态：后端未连接',reason+'；页面仍可浏览官方首发价。','is-error');
  return;
 }
 if(!health.credentialsConfigured){
  setApiStatus('报价 API 状态：等待服务端授权','后端已响应，但没有检测到 HAINAN_API_KEY；当前只显示官方首发价，不显示未核实的渠道价。','is-warn');
  return;
 }
 setApiStatus('报价 API 状态：服务已就绪','后端已配置密钥；正在查询当前列表前 10 款机型，型号与容量精确匹配后才显示渠道报价。','is-neutral');
 const ids=filtered().slice(0,10).map(p=>p.id);
 const result=await queryQuotes(ids,{continueOnError:false});
 if(result&&result.total){
  if(result.stopped){
   setApiStatus('报价 API 状态：查询中断',String(result.stopped)+`（已查 ${result.done}/${result.total} 款，有报价 ${result.ok} 款）`,'is-warn');
  }else{
   setApiStatus('报价 API 状态：查询完成',`本轮查询 ${result.done} 款：有精确报价 ${result.ok} 款，暂无报价 ${result.none} 款${result.fail?`，失败 ${result.fail} 款`:''}。渠道报价均需人工核验。`,'is-ok');
  }
 }
}
function reset(){state.brands.clear();state.types.clear();state.priorities.clear();state.recommendOnly=false;state.favOnly=false;state.priceMin=null;state.priceMax=null;if($('favOnly'))$('favOnly').checked=false;if($('priceMin'))$('priceMin').value='';if($('priceMax'))$('priceMax').value='';document.querySelectorAll('[data-price]').forEach(x=>x.classList.remove('active'));if(typeof updatePriceLabel==='function')updatePriceLabel();if($('searchInput'))$('searchInput').value='';if($('yearFrom'))$('yearFrom').value='2021';if($('yearTo'))$('yearTo').value='2026';if($('domesticOnly'))$('domesticOnly').checked=false;document.querySelectorAll('input[name="type"]').forEach(i=>i.checked=false);document.querySelectorAll('[data-years]').forEach(i=>i.classList.toggle('active',i.dataset.years==='all'));document.querySelectorAll('[data-priority]').forEach(i=>i.classList.remove('selected'));render();}
document.addEventListener('click',e=>{const t=e.target.closest('button');if(!t)return;if(t.id==='quoteQueryBtn'){if(quoteRunning){quoteRunToken++;setQuoteRunning(false);toast('已停止本轮报价查询');}else{const ids=filtered().map(p=>p.id);if(!ids.length)toast('当前筛选没有机型');else{setApiStatus('报价 API 状态：批量查询中','正在按 5 款一批查询当前筛选结果；精确匹配型号与容量后才显示渠道报价。','is-neutral');queryQuotes(ids,{continueOnError:true}).then(r=>{if(!r||!r.total)return;if(r.stopped){setApiStatus('报价 API 状态：查询中断',String(r.stopped)+`（已查 ${r.done}/${r.total} 款）`,'is-warn');return;}setApiStatus('报价 API 状态：批量查询完成',`本轮查询 ${r.done} 款：有精确报价 ${r.ok} 款，暂无报价 ${r.none} 款${r.fail?`，失败 ${r.fail} 款`:''}。渠道报价均需人工核验。`,'is-ok');});}}return;}if(t.dataset.quoteOne){if(quoteRunning){toast('请先等待当前查询结束');return;}const p=phones.find(x=>x.id===t.dataset.quoteOne);if(p)queryQuotes([p.id],{continueOnError:false});return;}if(t.dataset.detail)detail(t.dataset.detail);if(t.dataset.compare)toggleCompare(t.dataset.compare);if(t.dataset.remove){toggleCompare(t.dataset.remove);if(!$('compareModal')?.hidden){if(state.compare.length>=2)compare();else closeModal();}}if(t.dataset.diffOnly){state.compareDiffOnly=!state.compareDiffOnly;compare();}if(t.hasAttribute('data-close')||t.id==='modalBackdrop')closeModal();if(t.dataset.view){state.view=t.dataset.view;document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b===t));render();}if(t.dataset.years){const y=t.dataset.years;const now=2026;if(y==='all'){if($('yearFrom'))$('yearFrom').value='2021';if($('yearTo'))$('yearTo').value='2026';}else{if($('yearFrom'))$('yearFrom').value=String(now-Number(y)+1);if($('yearTo'))$('yearTo').value='2026';}document.querySelectorAll('[data-years]').forEach(b=>b.classList.toggle('active',b===t));render();}if(t.dataset.priority){const p=t.dataset.priority;if(state.priorities.has(p))state.priorities.delete(p);else if(state.priorities.size<3)state.priorities.add(p);else toast('最多选择 3 项优先需求');t.classList.toggle('selected',state.priorities.has(p));}if(t.id==='resetFilters'||t.id==='emptyReset')reset();if(t.id==='heroRecommend'){if($('recommendPanel'))$('recommendPanel').hidden=false;$('recommendPanel')?.scrollIntoView({behavior:'smooth',block:'center'});}if(t.id==='closeRecommend'){if($('recommendPanel'))$('recommendPanel').hidden=true;state.recommendOnly=false;render();}if(t.id==='applyRecommend'){state.recommendOnly=true;render();$('phoneGrid')?.scrollIntoView({behavior:'smooth',block:'start'});}if(t.id==='headerCompare'||t.id==='openCompare')compare();if(t.id==='clearCompare'){state.compare=[];render();}});
['yearFrom','yearTo','sortSelect','domesticOnly','budgetSelect'].forEach(id=>$(id)?.addEventListener('input',render));document.querySelectorAll('input[name="type"]').forEach(i=>i.addEventListener('change',()=>{i.checked?state.types.add(i.value):state.types.delete(i.value);render();}));$('modalBackdrop')?.addEventListener('click',closeModal);document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();if(e.key==='/'&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();$('searchInput')?.focus();}});

/* ================= 新增交互层（收藏 / 价格区间 / 密度 / 主题 / URL / 指针光斑） ================= */
const FAV_KEY='phoneindex.favs.v1',THEME_KEY='phoneindex.theme.v1',DENSITY_KEY='phoneindex.density.v1';
try{const raw=JSON.parse(localStorage.getItem(FAV_KEY)||'[]');if(Array.isArray(raw))state.favs=new Set(raw.filter(x=>typeof x==='string'));}catch(e){}
try{const d=localStorage.getItem(DENSITY_KEY);if(d==='compact'||d==='roomy')state.density=d;}catch(e){}
let themeMode='dark';
try{themeMode=localStorage.getItem(THEME_KEY)||'dark';}catch(e){}
function applyTheme(){
 const light=themeMode==='light'||(themeMode==='auto'&&window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)').matches);
 const theme=light?'light':'dark';
 document.documentElement.setAttribute('data-theme',theme);
 const btn=$('themeToggle');
 if(btn){btn.textContent=light?'☀':'☾';btn.setAttribute('aria-label',light?'切换到深色主题':'切换到浅色主题');}
 const meta=document.querySelector('meta[name="theme-color"]');
 if(meta)meta.setAttribute('content',light?'#eaeef7':'#05070d');
}
applyTheme();
$('themeToggle')?.addEventListener('click',()=>{
 themeMode=(document.documentElement.getAttribute('data-theme')==='light')?'dark':'light';
 try{localStorage.setItem(THEME_KEY,themeMode);}catch(e){}
 applyTheme();toast(themeMode==='light'?'已切换到浅色主题':'已切换到深色主题');
});
if(window.matchMedia){
 const mq=window.matchMedia('(prefers-color-scheme: light)');
 if(mq.addEventListener)mq.addEventListener('change',()=>{if(themeMode==='auto')applyTheme();});
}

/* —— 收藏 —— */
function persistFavs(){try{localStorage.setItem(FAV_KEY,JSON.stringify([...state.favs]));}catch(e){}}
function syncFavCount(){setText('favCount',state.favs.size);}
document.addEventListener('click',e=>{
 const b=e.target.closest('[data-fav]');if(!b)return;
 e.preventDefault();e.stopPropagation();
 const id=b.dataset.fav;
 const on=state.favs.has(id);
 if(on){state.favs.delete(id);b.classList.remove('is-on');b.textContent='♡';b.setAttribute('aria-pressed','false');}
 else{state.favs.add(id);b.classList.add('is-on');b.textContent='♥';b.setAttribute('aria-pressed','true');}
 persistFavs();syncFavCount();
 if(state.favOnly)render();else toast(on?'已取消收藏':'已收藏，可在左侧「我的收藏」筛选');
});
$('favOnly')?.addEventListener('change',e=>{state.favOnly=e.target.checked;render();});

/* —— 价格区间 —— */
let priceTimer=0;
function updatePriceLabel(){
 const el=$('priceRangeLabel');if(!el)return;
 const a=state.priceMin,b=state.priceMax;
 const f=v=>'¥'+Number(v).toLocaleString('zh-CN');
 el.textContent=(a==null&&b==null)?'不限':`${a==null?'不限':f(a)} — ${b==null?'不限':f(b)}`;
}
function readPriceRange(){
 const rawMin=$('priceMin')?.value.trim(),rawMax=$('priceMax')?.value.trim();
 const a=rawMin===''?null:Number(rawMin),b=rawMax===''?null:Number(rawMax);
 state.priceMin=Number.isFinite(a)?Math.max(0,a):null;
 state.priceMax=Number.isFinite(b)?Math.max(0,b):null;
 if(state.priceMin!=null&&state.priceMax!=null&&state.priceMin>state.priceMax){
  const t=state.priceMin;state.priceMin=state.priceMax;state.priceMax=t;
 }
 updatePriceLabel();
}
['priceMin','priceMax'].forEach(id=>$(id)?.addEventListener('input',()=>{
 clearTimeout(priceTimer);priceTimer=setTimeout(()=>{readPriceRange();render();},200);
}));
document.querySelectorAll('[data-price]').forEach(btn=>btn.addEventListener('click',()=>{
 const parts=String(btn.dataset.price||'').split('-');
 const lo=parts[0],hi=parts[1];
 const already=btn.classList.contains('active');
 document.querySelectorAll('[data-price]').forEach(x=>x.classList.remove('active'));
 if(already){if($('priceMin'))$('priceMin').value='';if($('priceMax'))$('priceMax').value='';}
 else{
  if($('priceMin'))$('priceMin').value=(lo==='0'?'':lo);
  if($('priceMax'))$('priceMax').value=(hi==='999999'?'':hi);
  btn.classList.add('active');
 }
 readPriceRange();render();
}));

/* —— 密度 —— */
function syncDensityButtons(){document.querySelectorAll('[data-density]').forEach(x=>x.classList.toggle('active',x.dataset.density===state.density));}
document.querySelectorAll('[data-density]').forEach(btn=>btn.addEventListener('click',()=>{
 state.density=btn.dataset.density;
 try{localStorage.setItem(DENSITY_KEY,state.density);}catch(e){}
 syncDensityButtons();render();
}));
syncDensityButtons();

/* —— URL 状态（可分享 / 刷新保留） —— */
function syncUrlState(){
 try{
  const p=new URLSearchParams();
  const q=$('searchInput')?.value.trim();if(q)p.set('q',q);
  if(state.brands.size)p.set('brand',[...state.brands].join(','));
  if(state.types.size)p.set('type',[...state.types].join(','));
  const from=$('yearFrom')?.value,to=$('yearTo')?.value;
  if(from&&from!=='2021')p.set('from',from);
  if(to&&to!=='2026')p.set('to',to);
  const sort=$('sortSelect')?.value;if(sort&&sort!=='newest')p.set('sort',sort);
  if(state.view==='table')p.set('view','table');
  if(state.favOnly)p.set('fav','1');
  if(state.priceMin!=null)p.set('min',String(state.priceMin));
  if(state.priceMax!=null)p.set('max',String(state.priceMax));
  const qs=p.toString();
  history.replaceState(null,'',qs?('?'+qs):location.pathname+location.hash);
 }catch(e){}
}
function restoreUrlState(){
 try{
  const p=new URLSearchParams(location.search);
  if(![...p.keys()].length)return;
  if(p.get('q')&&$('searchInput'))$('searchInput').value=p.get('q');
  if(p.get('brand'))p.get('brand').split(',').filter(Boolean).forEach(b=>state.brands.add(b));
  if(p.get('type'))p.get('type').split(',').filter(Boolean).forEach(t=>state.types.add(t));
  if(p.get('from')&&$('yearFrom'))$('yearFrom').value=p.get('from');
  if(p.get('to')&&$('yearTo'))$('yearTo').value=p.get('to');
  if(p.get('sort')&&$('sortSelect'))$('sortSelect').value=p.get('sort');
  if(p.get('view')==='table')state.view='table';
  if(p.get('fav')==='1'){state.favOnly=true;if($('favOnly'))$('favOnly').checked=true;}
  if(p.get('min')&&$('priceMin'))$('priceMin').value=p.get('min');
  if(p.get('max')&&$('priceMax'))$('priceMax').value=p.get('max');
  readPriceRange();
  document.querySelectorAll('input[name="type"]').forEach(i=>{i.checked=state.types.has(i.value);});
  document.querySelectorAll('.view-btn').forEach(b=>b.classList.toggle('active',b.dataset.view===state.view));
  if(state.view==='table'){const g=$('phoneGrid');if(g)g.dataset.forceView='table';}
 }catch(e){}
}

/* —— 移动端筛选折叠 —— */
const filtersPanel=$('filtersPanel'),filtersToggle=$('filtersToggle');
if(filtersToggle&&filtersPanel){
 filtersToggle.addEventListener('click',()=>{
  const open=filtersPanel.classList.toggle('is-open');
  filtersToggle.setAttribute('aria-expanded',String(open));
  filtersToggle.textContent=open?'收起 ▴':'展开 ▾';
 });
}

/* —— 搜索防抖 —— */
let searchTimer=0;
$('searchInput')?.addEventListener('input',()=>{
 clearTimeout(searchTimer);
 searchTimer=setTimeout(()=>render(),160);
});

/* —— 卡片指针光斑（华为式沉浸光感） —— */
const gridEl=$('phoneGrid');
if(gridEl){
 let raf=0,last=null;
 gridEl.addEventListener('pointermove',e=>{
  if(e.pointerType&&e.pointerType!=='mouse')return;
  last=e;
  if(raf)return;
  raf=requestAnimationFrame(()=>{
   raf=0;
   const card=last.target&&last.target.closest?last.target.closest('.phone-card'):null;
   if(!card)return;
   const r=card.getBoundingClientRect();
   card.style.setProperty('--mx',(((last.clientX-r.left)/Math.max(1,r.width))*100).toFixed(1)+'%');
   card.style.setProperty('--my',(((last.clientY-r.top)/Math.max(1,r.height))*100).toFixed(1)+'%');
  });
 },{passive:true});
}

/* —— 顶栏收缩 / 回到顶部 —— */
const headerEl=document.querySelector('.site-header');
const toTop=$('backToTop');
let scrollQueued=false;
function onScroll(){
 const y=window.scrollY||0;
 if(headerEl)headerEl.classList.toggle('is-stuck',y>12);
 if(toTop)toTop.classList.toggle('is-on',y>620);
 scrollQueued=false;
}
window.addEventListener('scroll',()=>{if(!scrollQueued){scrollQueued=true;requestAnimationFrame(onScroll);}},{passive:true});
onScroll();
toTop?.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));

/* —— 初始化顺序：恢复 URL → 同步收藏计数 → 首屏渲染 —— */
restoreUrlState();
syncFavCount();
readPriceRange();

render();
initQuoteApi();
})();

