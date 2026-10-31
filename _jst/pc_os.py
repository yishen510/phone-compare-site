# -*- coding: utf-8 -*-
import sys,json,re
sys.path.insert(0,'_jst')
from pc_fill import build_pool, grab, norm, BRAND_SLUG
TARGET=[
 ('Xiaomi','Xiaomi 18 Pro',['os']),
 ('Xiaomi','Xiaomi 17 Pro',['os']),
 ('Xiaomi','Xiaomi 17 Pro Max',['os']),
 ('Xiaomi','REDMI K90 Pro Max',['os']),
 ('Samsung','三星Galaxy Z Flip3',['os']),
 ('Xiaomi','小米12',['os']),
 ('Xiaomi','小米12 Pro',['os']),
 ('Xiaomi','小米12S Pro',['os']),
 ('Xiaomi','小米MIX FOLD 2',['os']),
 ('Xiaomi','红米Redmi K70至尊版',['os']),
 ('Huawei','华为Mate 70 RS 非凡大师',['os']),
 ('vivo','vivo X80 Pro 天玑9000版',['os']),
 ('OnePlus','一加10T',['os']),
 ('realme','真我GT3',['os']),
 ('Apple','iPhone 16 Plus',['os']),
 ('Maimang','麦芒 30',['os']),
 ('Samsung','Galaxy A55',['os','charging']),
 ('Polestar','Polestar Phone',['os']),
]
cache={}
for brand,name,want in TARGET:
    slug=BRAND_SLUG.get(brand)
    if not slug: print(f'{name:26s} NO SLUG'); continue
    if slug not in cache: cache[slug]=build_pool(slug)
    pool=cache[slug]; tgt=norm(name)
    hits=[(pid,n) for pid,n in pool.items() if norm(n)==tgt]
    if not hits:
        near=[n for n in pool.values() if tgt and (tgt in norm(n) or norm(n) in tgt)]
        print(f'{name:26s} 未命中；相近：{near[:3]}')
        continue
    got=grab(slug,hits[0][0])
    print(f'{name:26s} -> {hits[0][1]} | ' + ' | '.join(f'{k}={got.get(k)}' for k in want))
