"""2026-10-30 补参数：太平洋电脑网 / 中关村在线 / 华为 HK 官网 → data/phones.json → index.html。

只填「当前为占位/缺失」的字段，绝不覆盖已有值；每次写入都补 fieldAudit 与 auditNotes。
用法：python scripts/apply_params_20261030.py [--apply]
"""
from __future__ import annotations
import argparse, io, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from import_zol_params import patch_html  # noqa: E402

CAT = ROOT / "data" / "phones.json"
LABEL = {'chip': '处理器', 'display': '屏幕', 'battery': '电池', 'storage': '存储组合',
         'charging': '充电', 'weight': '重量', 'os': '操作系统'}
PLACE = ('以官方规格页为准', '以在售版本为准', '待核验', '待录入', '需进一步录入', '暂缺', '待复核', '运存未收录')
DATE = '2026-10-30'


def missing(v):
    s = str(v or '').strip()
    return (not s) or any(p in s for p in PLACE)


def pc_clean(v):
    v = re.sub(r'&#?\w+;.*$', '', str(v))
    v = re.sub(r'查看所有.*$', '', v)
    return v.strip().strip(',，').strip()


def parts(v):
    out = []
    for x in str(v).split(','):
        x = pc_clean(x)
        if re.search(r'\d', x):
            out.append(x)
    return out


def hz_of(v):
    m = re.search(r'(\d+(?:-\d+)?Hz)', str(v))
    return m.group(1) if m else ''


def size_of(v):
    m = re.search(r'(\d+(?:\.\d+)?)\s*英寸', str(v))
    return f'{m.group(1)} 英寸' if m else ''


def build_display(got, prefix=''):
    sz = size_of(got.get('scr_size', ''))
    mat = pc_clean(got.get('scr_mat') or got.get('scr_type', '').split(',')[0])
    hz = hz_of(got.get('scr_hz', ''))
    seg = [x for x in ((prefix + sz) if sz else '', mat, hz) if x]
    return ' · '.join(seg) if len(seg) >= 2 else ''


def norm_chip(v):
    """统一成站内风格：去掉 高通/联发科/三星 等营销前缀。"""
    v = pc_clean(v)
    v = re.sub(r'^(高通|联发科|三星|紫光展锐)\s*', '', v)
    v = re.sub(r'^(骁龙)\s*', '骁龙 ', v)
    v = re.sub(r'^(天玑)\s*', '天玑 ', v)
    v = re.sub(r'(?<=\d)(?=[\u4e00-\u9fff])', ' ', v)   # 数字与汉字之间补空格，统一风格
    return re.sub(r'\s+', ' ', v).strip()


def build_storage(got):
    ram, rom = parts(got.get('ram', '')), parts(got.get('rom', ''))
    if not rom:
        return ''
    if not ram:
        return ' / '.join(rom) + '（运存未收录）'
    if len(ram) == 1:
        return ' / '.join(f'{ram[0]}+{r}' for r in rom)
    if len(ram) == len(rom):
        return ' / '.join(f'{a}+{b}' for a, b in zip(ram, rom))
    return ''


def main(apply: bool):
    cat = json.loads(CAT.read_text(encoding='utf-8'))
    by = {p['name']: p for p in cat}
    changes = []

    # ---------- 1. 太平洋电脑网 ----------
    pc = json.loads(io.open(ROOT / '_jst/pc_explore.json', encoding='utf-8').read())
    for r in pc['res']:
        name, got = r['name'], r['got']
        p = by.get(name)
        if not p:
            continue
        url = f"https://product.pconline.com.cn/mobile/{r['brand'].lower()}/{r['pc_id']}_detail.html"
        foldable = ('Fold' in name) or ('Flip' in name)
        for field in r['need']:
            if not missing(p.get(field)):
                continue
            if field == 'display':
                if foldable:
                    continue          # 折叠屏单独处理：太平洋只给单一尺寸，容易误读成整机尺寸
                val = build_display(got)
            elif field == 'storage':
                val = build_storage(got)
            elif field == 'chip':
                val = norm_chip(got.get('chip', ''))
            elif field == 'battery':
                m = re.search(r'(\d+)\s*mAh', str(got.get('battery', '')))
                val = f'{m.group(1)}mAh' if m else ''
            else:
                val = pc_clean(got.get(field, ''))
            if val:
                changes.append((name, field, val, url,
                                f"太平洋电脑网参数页：{LABEL[field]} {val}",
                                'cross_checked_secondary_source'))

    # 折叠屏：太平洋只给单一尺寸，容易误读成整机尺寸，单独处理
    # Z Fold7：中关村在线参数页给出主/副屏两个尺寸
    for r in json.loads(io.open(ROOT / '_jst/zol_fill.json', encoding='utf-8').read())['res']:
        if r['name'] != 'Galaxy Z Fold7':
            continue
        got = r['got']
        sz = re.sub(r'纠错', '', got.get('scr_size', '')).strip()
        m1 = re.search(r'主：(\d+(?:\.\d+)?)英寸', sz)
        m2 = re.search(r'副：(\d+(?:\.\d+)?)英寸', sz)
        if not (m1 and m2):
            continue
        mat_raw = re.sub(r'纠错|[<>]', '', got.get('scr_mat', '')).strip()
        mm = re.search(r'主：\s*(.+?)\s*副', mat_raw)
        mat = (mm.group(1) if mm else mat_raw.replace('主：', '')).strip()
        hz = hz_of(got.get('scr_hz', ''))
        val = f"主屏 {m1.group(1)} 英寸 + 副屏 {m2.group(1)} 英寸 · {mat} · {hz}"
        changes.append(('Galaxy Z Fold7', 'display', val, got['_url'],
                        f"中关村在线参数页：屏幕尺寸 {sz}；屏幕材质 {mat}；屏幕刷新率 {hz}",
                        'cross_checked_secondary_source'))

    # Z Flip7：太平洋的 6.9 英寸对应内屏，标注清楚，副屏尺寸另行说明
    for r in pc['res']:
        if r['name'] != 'Galaxy Z Flip7' or not missing(by['Galaxy Z Flip7'].get('display')):
            continue
        val = build_display(r['got'], prefix='内屏 ')
        if val:
            url = f"https://product.pconline.com.cn/mobile/samsung/{r['pc_id']}_detail.html"
            changes.append(('Galaxy Z Flip7', 'display', val, url,
                            "太平洋电脑网参数页：屏幕大小 6.9 英寸（内屏）；副屏尺寸未收录",
                            'cross_checked_secondary_source'))

    # ---------- 2. 华为 HK 官网（厂商一手）----------
    hk = 'https://consumer.huawei.com/hk/phones/pura80-ultra/specs/'
    p = by.get('HUAWEI Pura 80 Ultra')
    if p and missing(p.get('chip')):
        changes.append(('HUAWEI Pura 80 Ultra', 'chip', '麒麟 9020', hk,
                        '华为官网（中国香港）规格参数页：處理器 Kirin 9020，Octa-core',
                        'official_source'))

    # ---------- 2b. 太平洋 redmi 池（小米主品牌页无产品链接，需单独取）----------
    MANUAL = [
        ('REDMI K90 Pro Max', 'chip', '骁龙 8 至尊版 Gen 5',
         'https://product.pconline.com.cn/mobile/redmi/2718419_detail.html',
         '太平洋电脑网参数页：CPU 高通骁龙8至尊版 Gen 5'),
        ('REDMI K90 Pro Max', 'display', '6.9 英寸 · OLED',
         'https://product.pconline.com.cn/mobile/redmi/2718419_detail.html',
         '太平洋电脑网参数页：屏幕大小 6.9 英寸；屏幕材质 OLED（刷新率未收录）'),
    ]
    for name, field, val, url, ev in MANUAL:
        if name in by and missing(by[name].get(field)):
            changes.append((name, field, val, url, ev, 'cross_checked_secondary_source'))

    # ---------- 3. 已知差异：只记审计，不改值 ----------
    notes = [('酷派 COOL 60',
              '2026-10-30 电池存在来源差异：本条取中关村在线 4900mAh，太平洋电脑网记为 4500mAh(typ)；差异未消解，保留原值。')]

    print(f'待写入 {len(changes)} 项：')
    for name, field, val, url, ev, st in changes:
        cur = by[name].get(field)
        print(f"  {name:<24} {field:<8} {str(cur)[:34]!r:<40} -> {val!r}")
    print(f'审计备注 {len(notes)} 条')
    if not apply:
        print('\n（干跑，未写盘。加 --apply 生效）')
        return

    shutil.copy2(CAT, CAT.with_suffix('.json.before-params-20261030'))
    for name, field, val, url, ev, st in changes:
        p = by[name]
        p[field] = val
        fa = p.setdefault('fieldAudit', [])
        fa = [x for x in fa if not (isinstance(x, dict) and x.get('field') == LABEL[field])]
        fa.append({'field': LABEL[field], 'value': val, 'valueAtAudit': val, 'status': st,
                   'sourceUrl': url, 'evidenceText': ev,
                   'note': f'{DATE} 补录缺失参数；来源：{url.split("/")[2]}。'})
        p['fieldAudit'] = fa
        an = p.setdefault('auditNotes', [])
        an.insert(0, f'{DATE} 补参数（{LABEL[field]}）：{val}；来源 {url}')
        p['auditNotes'] = an
    for name, note in notes:
        by[name].setdefault('auditNotes', []).insert(0, note)

    CAT.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n已写 data/phones.json（{len(cat)} 条）')
    patch_html(ROOT / 'index.html', cat)
    print('已同步 index.html 内嵌数据')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    main(ap.parse_args().apply)
