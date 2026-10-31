#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修「容量组合」字段的两种毛病（46 条）：

1. 值以 `>` 结尾——这是早期从中关村在线表格里原样搬过来的箭头，卡片上会显示成「256GB>」；
2. 只剩一个存储容量、没有运存——参数表里其实有「RAM容量」，只是没被用上。

修法（不猜、不补）：
- 有 ZOL 机型池的 SKU 列表（≥2 个组合）→ 用池里的组合，来源写商品页版本列表；
- 否则用该记录自带参数表的 RAM容量 + ROM容量 拼一个组合，并在审计里写明「参数页只列该版本」。

用法：python scripts/fix_storage_20261031.py [--dry]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_zol_params import patch_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
POOL = ROOT / "_jst" / "all_models_grouped.json"
TODAY = "2026-10-31"

BRAND = {"华为": "Huawei", "荣耀": "Honor", "vivo": "vivo", "OPPO": "OPPO", "红米": "Xiaomi",
         "真我": "realme", "iQOO": "iQOO", "三星": "Samsung", "努比亚": "nubia", "小米": "Xiaomi",
         "一加": "OnePlus", "Moto": "Motorola", "苹果": "Apple", "WIKO": "WIKO", "中兴": "ZTE",
         "魅族": "MEIZU", "华硕": "ASUS", "麦芒": "Maimang", "酷派": "Coolpad"}
PRE = ["huawei", "honor", "xiaomi", "redmi", "oppo", "vivo", "iqoo", "realme", "samsung", "galaxy",
       "oneplus", "nubia", "zte", "meizu", "asus", "apple", "iphone", "motorola", "moto",
       "华为", "三星", "荣耀", "小米", "红米", "中兴", "酷派", "魅族", "努比亚", "真我", "一加"]


def norm(s: str) -> str:
    x = re.sub(r"[\s\u3000·\-_/]+", "", str(s)).lower()
    for w in PRE:
        if x.startswith(w):
            x = x[len(w):]
    return x


def pick(specs, label):
    for g in specs or []:
        for k, v in g.get("items", []):
            if k == label:
                return str(v)
    return ""


def sort_key(combo: str):
    """容量组合按运存、存储升序排，页面上一眼看得出从低到高。"""
    m = re.match(r"(\d+)\s*GB\s*\+\s*(\d+)\s*(GB|TB)", str(combo))
    if m:
        rom = int(m.group(2)) * (1024 if m.group(3) == "TB" else 1)
        return (int(m.group(1)), rom, str(combo))
    m = re.match(r"(\d+)\s*(GB|TB)", str(combo))
    if m:
        return (999, int(m.group(1)) * (1024 if m.group(2) == "TB" else 1), str(combo))
    return (999, 9999, str(combo))


def clean(x: str) -> str:
    return re.sub(r"[>＞\s]+$", "", str(x or "")).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    pool = {}
    if POOL.is_file():
        for x in json.loads(POOL.read_text(encoding="utf-8")):
            b = BRAND.get(x.get("brand"))
            if b and len(x.get("skus") or []) >= 2:
                pool.setdefault((b, norm(x["model"])), x)

    changed = 0
    for p in catalog:
        cur = str(p.get("storage") or "")
        if not re.search(r"[>＞]\s*$", cur):
            continue
        specs = p.get("specs") or []
        ram, rom = clean(pick(specs, "RAM容量")), clean(pick(specs, "ROM容量"))
        pooled = pool.get((p["brand"], norm(p["name"])))
        if pooled:
            new = " / ".join(sorted(pooled["skus"], key=sort_key))
            src, ev = (pooled["pids"] and
                       f"https://detail.zol.com.cn/{pooled['pids'][0][:4]}/{pooled['pids'][0]}/"
                       or p.get("specSource", "")), \
                      "中关村在线机型页在售版本：" + "、".join(pooled["skus"])
            note = f"{TODAY} 用参数站机型页的在售版本列表重建容量组合；原值「{cur}」只有存储、无运存。"
        elif ram and rom:
            orig = clean(cur)
            new = f"{ram}+{rom}" if orig == rom else f"{ram}+{rom} / {orig}（后者运存未收录）"
            src = p.get("specSource") or p.get("source") or ""
            ev = f"中关村在线参数页：RAM容量 {ram}；ROM容量 {rom}"
            note = (f"{TODAY} 按参数页的 RAM/ROM 重建容量组合；参数页只列 {ram}+{rom} 这一版本。原值「{cur}」。"
                    + ("原记录写的存储容量与参数表的不是同一版本，两个都保留。" if clean(cur) != rom else ""))
        elif rom:
            new = f"{rom}（运存未收录）"
            src = p.get("specSource") or p.get("source") or ""
            ev = f"中关村在线参数页：ROM容量 {rom}"
            note = f"{TODAY} 去掉误带进来的「>」；参数页无 RAM 字段，运存仍缺。原值「{cur}」。"
        else:
            new = cur.rstrip(">＞ ")
            src = p.get("specSource") or p.get("source") or ""
            ev = "去掉参数表里原样带入的「>」"
            note = f"{TODAY} 仅去掉「>」，容量组合待补。"
        if args.dry:
            print(f"DRY {p['name']:26s} {cur!r} -> {new}")
        else:
            p["storage"] = new
            if new and not str(new).endswith("待补"):
                p.setdefault("storageOptions", [x.strip() for x in str(new).split("/") if x.strip()])
            fa = p.setdefault("fieldAudit", [])
            entry = next((x for x in fa if isinstance(x, dict) and x.get("field") == "容量组合"), None)
            payload = {"field": "容量组合", "value": new, "valueAtAudit": new,
                       "status": "cross_checked_secondary_source", "sourceUrl": src,
                       "evidenceText": ev, "note": note}
            if entry:
                entry.update(payload)
            else:
                fa.append(payload)
            print(f"{p['name']:26s} {cur!r} -> {new}")
        changed += 1

    print(f"{'dry-run ' if args.dry else ''}修改 {changed} 条")
    if args.dry or not changed:
        return
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    back = json.loads(CATALOG.read_text(encoding="utf-8"))
    for f in (ROOT / "index.html", ROOT / "phone-compare-demo.html"):
        if f.is_file():
            patch_html(f, back, strict=False)


if __name__ == "__main__":
    main()
