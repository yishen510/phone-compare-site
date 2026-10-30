"""2026-10-30 第 10 轮补参：厂商官方站（无头浏览器渲染后取的值）。

只填「当前为占位」的字段；华为那批运存改为「厂商未公布运存」——已确认华为官网
规格页本身就不列运行内存，不该把锅甩给参数站。
用法：python scripts/apply_params_20261030b.py [--apply]
"""
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from import_zol_params import patch_html  # noqa: E402

CAT = ROOT / "data" / "phones.json"
LABEL = {'chip': '处理器', 'display': '屏幕', 'battery': '电池', 'storage': '存储组合',
         'charging': '充电', 'weight': '重量', 'os': '操作系统'}
PLACE = ('以官方规格页为准', '以在售版本为准', '待核验', '待录入', '需进一步录入', '暂缺',
         '待复核', '运存未收录', '厂商未公布运存')
DATE = '2026-10-30'

# 新填值：官方来源
CHANGES = [
    ('OPPO A3', 'os', 'ColorOS 14.0',
     'https://www.oppo.com/cn/smartphones/series-a/a3/specs/',
     'OPPO 官网产品参数页：操作系统 ColorOS 14.0'),
    ('WIKO Hi畅享 70m', 'os', '鸿蒙生态（HarmonyOS Connect 认证）',
     'https://www.wiko.com/phones/hi_changxiang_70m',
     'WIKO 官网 Hi畅享 70m 页：获得 HarmonyOS Connect 认证，共享鸿蒙分布式能力'),
    ('HUAWEI nova 14 活力版', 'storage', '256GB / 512GB（厂商未公布运存）',
     'https://consumer.huawei.com/cn/phones/nova14-huoliban/specs/',
     '华为官网规格页：机身内存 256 GB / 512 GB ROM；页面未列运行内存'),
]

# 已核实华为官网规格页不公布运存 → 改写后缀（不再甩锅参数站）
SUFFIX = [
    ('HUAWEI 畅享 100 Pro Max',
     'https://consumer.huawei.com/cn/phones/changxiang-100-pro-max/specs/'),
    ('HUAWEI 畅享 90', 'https://consumer.huawei.com/cn/phones/changxiang-90/specs/'),
    ('HUAWEI 畅享 90 Plus', 'https://consumer.huawei.com/cn/phones/changxiang-90-plus/specs/'),
    ('HUAWEI 畅享 90 Pro Max', 'https://consumer.huawei.com/cn/phones/changxiang-90-pro-max/specs/'),
    ('HUAWEI nova 15', 'https://consumer.huawei.com/cn/phones/nova15/specs/'),
]

# 官方页复核结论：与已录入一致，只记审计，不改值
CONFIRM = [
    ('HUAWEI 畅享 100 Pro Max',
     '华为官网规格页复核：处理器 麒麟8020A（128/256GB 版）/ 麒麟8020（512GB 版）；'
     '机身内存 128/256/512GB；重量约 228g',
     'https://consumer.huawei.com/cn/phones/changxiang-100-pro-max/specs/'),
    ('HUAWEI 畅享 90', '华为官网规格页复核：处理器 麒麟8000A；机身内存 128/256GB',
     'https://consumer.huawei.com/cn/phones/changxiang-90/specs/'),
    ('HUAWEI 畅享 90 Plus', '华为官网规格页复核：处理器 麒麟8000；机身内存 128/256GB',
     'https://consumer.huawei.com/cn/phones/changxiang-90-plus/specs/'),
    ('HUAWEI 畅享 90 Pro Max', '华为官网规格页复核：机身内存 128/256/512GB',
     'https://consumer.huawei.com/cn/phones/changxiang-90-pro-max/specs/'),
    ('HUAWEI nova 15', '华为官网规格页复核：处理器 麒麟8020；机身内存 256/512GB',
     'https://consumer.huawei.com/cn/phones/nova15/specs/'),
]


def missing(v):
    s = str(v or '').strip()
    return (not s) or any(p in s for p in PLACE)


def note(p, text):
    an = p.setdefault('auditNotes', [])
    if text not in an:
        an.insert(0, text)


def main(apply: bool):
    cat = json.loads(CAT.read_text(encoding='utf-8'))
    by = {p['name']: p for p in cat}
    plan = []

    for name, field, val, url, ev in CHANGES:
        p = by.get(name)
        if not p:
            print(f'  !! 目录无此机型 {name}')
            continue
        if not missing(p.get(field)):
            print(f'  -- 跳过 {name} {field}：已有值 {p.get(field)!r}')
            continue
        plan.append(('fill', name, field, p.get(field), val, url, ev))

    for name, url in SUFFIX:
        p = by.get(name)
        cur = str(p.get('storage') or '')
        if '运存未收录' in cur:
            plan.append(('fill', name, 'storage', cur, cur.replace('运存未收录', '厂商未公布运存'),
                         url, '华为官网规格页未列运行内存，措辞由「参数站未收录」改为「厂商未公布」'))

    for name, text, url in CONFIRM:
        if name in by:
            plan.append(('note', name, '', '', text + f'；来源 {url}', url, ''))

    print(f'计划 {len(plan)} 项：')
    for kind, name, field, old, new, url, ev in plan:
        tag = '备注' if kind == 'note' else field
        print(f"  {name:<22} {tag:<8} {str(old)[:30]!r:<36} -> {str(new)[:60]!r}")
    if not apply:
        print('\n（干跑，未写盘）')
        return

    shutil.copy2(CAT, CAT.with_suffix('.json.before-round10'))
    for kind, name, field, old, new, url, ev in plan:
        p = by[name]
        if kind == 'note':
            note(p, f'{DATE} {new}')
            continue
        p[field] = new
        fa = [x for x in p.get('fieldAudit', []) if not (isinstance(x, dict) and x.get('field') == LABEL[field])]
        fa.append({'field': LABEL[field], 'value': new, 'valueAtAudit': new,
                   'status': 'official_source', 'sourceUrl': url, 'evidenceText': ev,
                   'note': f'{DATE} 由厂商官方规格页补录/改写。'})
        p['fieldAudit'] = fa
        note(p, f'{DATE} 补参数（{LABEL[field]}）：{new}；来源 {url}')

    CAT.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n已写 data/phones.json（{len(cat)} 条）')
    patch_html(ROOT / 'index.html', cat)
    print('已同步 index.html')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    main(ap.parse_args().apply)
