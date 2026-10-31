# -*- coding: utf-8 -*-
"""针对剩余占位字段，去太平洋电脑网按「精确机型名」找对应参数。"""
import sys,json,re
sys.path.insert(0,'_jst')
from pc_fill import build_pool, grab, norm, BRAND_SLUG

TARGET=[
 ('Huawei','HUAWEI Pocket 2',['chip']),
 ('Huawei','HUAWEI nova Flip',['chip']),
 ('Huawei','HUAWEI nova Flip S',['chip','battery','charging']),
 ('Huawei','HUAWEI 畅享 70X活力版',['chip']),
 ('Huawei','HUAWEI nova 14 活力版',['chip']),
 ('Honor','荣耀 500 Pro MOLLY 20 周年限定版',['weight']),
 ('Honor','荣耀 畅玩 60A',['charging']),
 ('ZTE','中兴 远航 41S',['charging','weight']),
 ('ZTE','中兴 Axon 60 Ultra',['weight']),
 ('ZTE','中兴 Axon 60 Ultra 天通版',['weight']),
 ('Coolpad','酷派 COOL 60',['weight']),
 ('Samsung','Galaxy A55',['charging']),
 ('Samsung','三星Galaxy C55',['charging']),
 ('Samsung','三星Galaxy Z Flip7 FE',['charging']),
 ('realme','真我 V60s',['charging']),
]
cache={}
for brand,name,want in TARGET:
    slug=BRAND_SLUG.get(brand)
    if not slug: print('NO SLUG',brand); continue
    if slug not in cache: cache[slug]=build_pool(slug)
    pool=cache[slug]
    tgt=norm(name)
    hits=[(pid,n) for pid,n in pool.items() if norm(n)==tgt]
    print(f'{name:34s} 池{len(pool):3d} 精确命中 {len(hits)} -> {hits[:2]}')
    if hits:
        got=grab(slug,hits[0][0])
        print('      ',{k:got.get(k) for k in want})
json.dump({},open('/dev/null','w'))
