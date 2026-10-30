"""2026-10-30 第 12 轮：补 62 条「操作系统」占位 + 其余占位字段。

起因：扫描占位符时只认「以官方规格页为准」，漏掉了「以官方页面为准」（46 条）
和「以官方大陆版页面为准」（13 条）两种变体，导致这些占位值被当成正常值显示。
本轮先用正则识别全部占位变体，再用太平洋电脑网回填，并把占位规则同步进脚本与前端。
用法：python scripts/apply_params_20261030c.py [--apply]
"""
from __future__ import annotations
import argparse, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from import_zol_params import patch_html  # noqa: E402

CAT = ROOT / "data" / "phones.json"
LABEL = {'chip': '处理器', 'display': '屏幕', 'battery': '电池', 'storage': '存储组合',
         'charging': '充电', 'weight': '重量', 'os': '操作系统'}
# 占位变体必须全覆盖：漏一种就会把占位值当成正常值写进页面
PH = re.compile(r'^以.{0,12}为准$|^.{0,6}(待核验|待录入|暂缺|未公布|未收录).{0,8}$|^.{0,4}待复核.{0,6}$')
DATE = '2026-10-30'


def missing(v):
    s = str(v or '').strip()
    return (not s) or bool(PH.match(s))


def pc_clean(v):
    v = re.sub(r'&#?\w+;.*$', '', str(v))
    v = re.sub(r'查看所有.*$', '', v)
    return v.strip().strip(',，').strip()


def build_os(got):
    """太平洋的「操作系统」是一串带解释尾巴的逗号列表，取有效项并去掉被包含的泛化项。"""
    parts = []
    for x in str(got.get('os', '')).split(','):
        x = pc_clean(x)
        if x and len(x) <= 30:
            parts.append(x)
    # 裸版本号（如 HarmonyOS,4.0 里的 4.0）并入前一项，避免出现「HarmonyOS / 4.0」
    merged = []
    for x in parts:
        if re.fullmatch(r'\d+(?:\.\d+)*', x) and merged:
            merged[-1] = f'{merged[-1]} {x}'
        else:
            merged.append(x)
    out = []
    for x in merged:
        if any(x != y and y.startswith(x + ' ') for y in merged):   # Android 被 Android 16 覆盖
            continue
        x = re.sub(r'^(?:三星|荣耀|华为)\s*(?=One UI)', '', x)          # 「三星One UI」统一成「One UI」
        if x not in out:
            out.append(x)
    return ' / '.join(out)


def build_weight(got):
    m = re.search(r'(\d+(?:\.\d+)?)\s*g', str(got.get('weight', '')))
    return f'{m.group(1)}g' if m else ''


def build_charging(got):
    raw = str(got.get('charging', ''))
    seg = re.findall(r'(\d+(?:\.\d+)?)\s*[Ww瓦]\s*(有线|无线)', raw)
    if seg:
        seen, out = set(), []
        for w, k in seg:
            key = f'{w} {k}'
            if key not in seen:
                seen.add(key)
                out.append(key)
        return ' / '.join(out)
    return pc_clean(raw)[:40]


def num(s):
    m = re.search(r'(\d+(?:\.\d+)?)', str(s or ''))
    return float(m.group(1)) if m else None


def conflict(cur, field, val):
    """抓到的值不能与在库已知值明显冲突。"""
    if field == 'battery':
        a, b = num(cur.get('battery')), num(val)
        if a and b and abs(a - b) / a > 0.08:
            return f'电池 在库{a} vs 抓到{b}'
    if field == 'weight':
        a, b = num(cur.get('weight')), num(val)
        if a and b and abs(a - b) / a > 0.12:
            return f'重量 在库{a} vs 抓到{b}'
    return ''


def main(apply: bool):
    cat = json.loads(CAT.read_text(encoding='utf-8'))
    by = {p['name']: p for p in cat}
    pc = json.loads((ROOT / '_jst/pc_explore.json').read_text(encoding='utf-8'))
    plan, skip = [], []
    for r in pc['res']:
        name, got = r['name'], r['got']
        p = by.get(name)
        if not p:
            continue
        url = f"https://product.pconline.com.cn/mobile/{r['brand'].lower()}/{r['pc_id']}_detail.html"
        for field in r['need']:
            if not missing(p.get(field)):
                continue
            if field == 'os':
                val = build_os(got)
            elif field == 'weight':
                val = build_weight(got)
            elif field == 'charging':
                val = build_charging(got)
            elif field == 'chip':
                val = re.sub(r'^(高通|联发科|三星|紫光展锐)\s*', '', pc_clean(got.get('chip', '')))
                val = re.sub(r'(?<=\d)(?=[\u4e00-\u9fff])', ' ', val)
            elif field == 'battery':
                m = re.search(r'(\d+)\s*mAh', str(got.get('battery', '')))
                val = f'{m.group(1)}mAh' if m else ''
            elif field == 'display':
                continue   # 折叠屏单独处理，避免只取到单一尺寸
            else:
                val = ''
            if not val:
                continue
            bad = conflict(p, field, val)
            if bad:
                skip.append((name, field, bad))
                continue
            plan.append((name, field, p.get(field), val, url))

    print(f'可写 {len(plan)} 项；冲突拒绝 {len(skip)} 项')
    for n, f, b, _ in skip:
        print(f'  !! {n} {f}: {b}')
    for name, field, old, val, url in plan:
        print(f"  {name:<24} {field:<8} {str(old)[:22]!r:<26} -> {val!r}")
    if not apply:
        print('\n（干跑，未写盘）')
        return

    shutil.copy2(CAT, CAT.with_suffix('.json.before-round12'))
    for name, field, old, val, url in plan:
        p = by[name]
        p[field] = val
        fa = [x for x in p.get('fieldAudit', []) if not (isinstance(x, dict) and x.get('field') == LABEL[field])]
        fa.append({'field': LABEL[field], 'value': val, 'valueAtAudit': val,
                   'status': 'cross_checked_secondary_source', 'sourceUrl': url,
                   'evidenceText': f'太平洋电脑网参数页：{LABEL[field]} {val}',
                   'note': f'{DATE} 补录占位字段；第三方参数站，非厂商官方页。'})
        p['fieldAudit'] = fa
        an = p.setdefault('auditNotes', [])
        line = f'{DATE} 补参数（{LABEL[field]}）：{val}；来源 {url}'
        if line not in an:
            an.insert(0, line)
    CAT.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n已写 data/phones.json（{len(cat)} 条）')
    patch_html(ROOT / 'index.html', cat)
    print('已同步 index.html')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    main(ap.parse_args().apply)
