# -*- coding: utf-8 -*-
import json,sys,time,re
sys.path.insert(0,'scripts')
from import_zol_params import fetch, parse_specs
from backfill_summary_from_specs import derive, pick, naive_clean

T=json.load(open('_jst/target_batch.json',encoding='utf-8'))
res={}
for i,t in enumerate(T):
    pid=t['pid']
    url=f'https://detail.zol.com.cn/{pid[:4]}/{pid}/param.shtml'
    specs=None
    for attempt in range(4):
        try:
            h=fetch(url)
            specs=parse_specs(h)
            title=re.search(r'<title>(.*?)</title>',h,re.S)
            title=title.group(1).strip() if title else ''
            if len(specs)>=3:
                break
        except Exception as e:
            title=f'ERR {type(e).__name__}'
        time.sleep(1.5*(attempt+1))
    n=sum(len(g['items']) for g in specs) if specs else 0
    t['url']=url; t['title']=title; t['nfields']=n
    t['specs']=specs or []
    t['derived']=derive(specs) if specs else {}
    print(f"[{i+1}/{len(T)}] {t['brand']} {t['model']}: {n} 字段 | {title[:36]}")
    time.sleep(0.8)
json.dump(T,open('_jst/target_specs.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('done',sum(1 for t in T if t['nfields']>=3),'/',len(T))
