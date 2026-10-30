"""为剩余 18 台补「操作系统」：ZOL 参数页（出厂系统内核/操作系统）。

注意：小米/苹果机型名是英文，ZOL 标题是中文，检索词与校验 token 都要换算。
用法：python _jst/zol_os.py
"""
import io, json, re, sys, time
sys.path.insert(0, '_jst')
from zol_fill import search, parse

# (目录机型名, ZOL 检索词, 标题必须包含, 标题不能包含)
JOBS = [
    ('Xiaomi 18 Pro', '小米18 Pro', ['18 Pro'], []),
    ('Xiaomi 17 Pro', '小米17 Pro', ['17 Pro'], ['Max']),
    ('Xiaomi 17 Pro Max', '小米17 Pro Max', ['17 Pro Max'], []),
    ('REDMI K90 Pro Max', 'Redmi K90 Pro Max', ['K90 Pro Max'], []),
    ('三星Galaxy Z Flip3', '三星Galaxy Z Flip3', ['Flip3'], []),
    ('小米12', '小米12', ['小米12'], ['Pro', 'X', 'S']),
    ('小米12 Pro', '小米12 Pro', ['小米12 Pro'], ['S']),
    ('小米12S Pro', '小米12S Pro', ['12S Pro'], []),
    ('小米MIX FOLD 2', '小米MIX Fold 2', ['MIX Fold 2'], []),
    ('红米Redmi K70至尊版', 'Redmi K70至尊版', ['K70至尊版'], []),
    ('华为Mate 70 RS 非凡大师', '华为Mate 70 RS 非凡大师', ['Mate 70 RS'], []),
    ('vivo X80 Pro 天玑9000版', 'vivo X80 Pro 天玑9000版', ['X80 Pro', '天玑9000'], []),
    ('一加10T', '一加10T', ['10T'], []),
    ('真我GT3', '真我GT3', ['GT3'], []),
    ('iPhone 16 Plus', '苹果iPhone 16 Plus', ['16 Plus'], []),
    ('麦芒 30', '华为麦芒30', ['麦芒30', '麦芒 30'], []),
    ('Galaxy A55', '三星Galaxy A55', ['A55'], []),
    ('Polestar Phone', 'Polestar Phone', ['Polestar'], []),
]


def clean_title(t):
    return re.sub(r'\s+', '', t or '')


def main():
    out, fail = [], []
    for name, q, must, forbid in JOBS:
        links = []
        for attempt in range(4):          # ZOL 搜索会间歇 503/504，重试即可
            try:
                links, _ = search(q)
                break
            except Exception:
                time.sleep(2 + attempt * 2)
        time.sleep(0.3)
        got = None
        for u in links:
            try:
                g = parse(u)
            except Exception:
                continue
            t = clean_title(g.get('_title', ''))
            mt = [clean_title(x) for x in must]
            if not all(any(m in t for m in mt) for m in mt):
                continue
            if any(clean_title(f) in t for f in forbid):
                continue
            g['_url'] = u
            got = g
            break
        if not got:
            fail.append(name)
            print(f'  x {name:<24} 未取到（links={len(links)}）')
            continue
        os_v = got.get('os') or ''
        kernel = got.get('os_kernel') or ''
        out.append({'name': name, 'os': os_v, 'kernel': kernel, 'url': got['_url'], 'title': got.get('_title', '')})
        print(f"  {name:<24} 操作系统={os_v!r} 内核={kernel!r}")
    io.open('_jst/zol_os.json', 'w', encoding='utf-8').write(
        json.dumps({'res': out, 'fail': fail}, ensure_ascii=False, indent=1))
    print(f'\n命中 {len(out)} / 未取到 {len(fail)}')


if __name__ == '__main__':
    main()
