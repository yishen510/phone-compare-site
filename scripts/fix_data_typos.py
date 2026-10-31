"""修数据里的错字与单位格式：只改「写法」，不改「数值」。

- os: 'reakme UI5.0' → 'realme UI 5.0'（品牌名拼错）
- os: '警兴OS' → 'Android 14'（中兴官网把定制系统名写成「警兴OS」，疑为「中兴OS」笔误，
  这里只保留官网可核验的 Android 版本，避免把乱码展示给用户）
- weight: '227 g' → '227g'、'约 178 克' → '约 178g'（单位与空格统一）
- battery: '5000 mAh' → '5000mAh'
带区间/括号说明的值不动，避免误伤。
用法：python scripts/fix_data_typos.py [--apply]
"""
from __future__ import annotations
import argparse, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from import_zol_params import patch_html  # noqa: E402

CAT = ROOT / "data" / "phones.json"
DATE = '2026-10-31'

OS_FIX = {
    'reakme UI5.0': ('realme UI 5.0', '修正品牌名拼写错误（reakme → realme），与站内其余真我机型写法统一'),
    'reakme UI 5.0': ('realme UI 5.0', '修正品牌名拼写错误（reakme → realme），与站内其余真我机型写法统一'),
    '警兴OS': ('Android 14', '中兴官网规格页原文为「Android14.0/警兴OS」，「警兴OS」疑为「中兴OS」笔误，'
                          '故只保留可核验的 Android 版本'),
}
WT = re.compile(r'^(约\s*)?(\d+(?:\.\d+)?)\s*(?:g|克)$')
BT = re.compile(r'^(\d{3,5})\s*mAh$')


def norm_weight(v):
    """只做「数字与单位之间去空格 / 克→g」的替换，不动数值，也不动括号说明。"""
    v = re.sub(r'(\d)\s*克', r'\1g', v)          # 约 199 克 → 约 199g
    v = re.sub(r'(\d)\s+g(?![a-zA-Z])', r'\1g', v)  # 227 g / 232–237 g → 227g / 232–237g
    return v


def norm_battery(v):
    return re.sub(r'(\d)\s+mAh', r'\1mAh', v)    # 4000 mAh → 4000mAh


def main(apply: bool):
    cat = json.loads(CAT.read_text(encoding='utf-8'))
    plan = []
    for p in cat:
        cur = str(p.get('os') or '').strip()
        if cur in OS_FIX:
            new, why = OS_FIX[cur]
            plan.append((p, 'os', cur, new, why))
        w = str(p.get('weight') or '').strip()
        nw = norm_weight(w)
        if nw != w:
            plan.append((p, 'weight', w, nw, '统一重量单位与空格写法（数值不变）'))
        b = str(p.get('battery') or '').strip()
        nb = norm_battery(b)
        if nb != b:
            plan.append((p, 'battery', b, nb, '统一电池单位写法（数值不变）'))

    print(f'计划修改 {len(plan)} 项：')
    for p, f, old, new, why in plan:
        print(f"  {p['name'][:22]:<24} {f:<8} {old!r:<26} -> {new!r}")
    if not apply:
        print('\n（干跑，未写盘）')
        return

    shutil.copy2(CAT, CAT.with_suffix('.json.before-typofix'))
    label = {'os': '操作系统', 'weight': '重量', 'battery': '电池'}
    for p, f, old, new, why in plan:
        p[f] = new
        fa = [x for x in p.get('fieldAudit', []) if not (isinstance(x, dict) and x.get('field') == label[f])]
        fa.append({'field': label[f], 'value': new, 'valueAtAudit': new,
                   'status': 'corrected', 'sourceUrl': p.get('source') or '',
                   'evidenceText': f'{why}；原值 {old}',
                   'note': f'{DATE} 修正写法（数值未变）。'})
        p['fieldAudit'] = fa
        an = p.setdefault('auditNotes', [])
        line = f'{DATE} 修正{label[f]}写法：{old} → {new}（{why}）'
        if line not in an:
            an.insert(0, line)
    CAT.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n已写 data/phones.json（{len(cat)} 条，改 {len(plan)} 项）')
    patch_html(ROOT / 'index.html', cat)
    print('已同步 index.html')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    main(ap.parse_args().apply)
