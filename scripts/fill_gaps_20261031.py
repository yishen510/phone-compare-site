#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补最后几处可见缺口 + 把「查过但厂商不公布」的字段从「待核验」改成明确状态。

两类改动：

A. 补值（1 处）
   HUAWEI Pura 90 Pro 的重量：ZOL 参数页无「重量」条目，
   华为官网 Pura 90 Pro 规格页「尺寸与重量」写的是「约 213.5 g（含电池）」。

B. 改审计状态（9 处，值不动）
   这些字段的取值仍是占位文案，前端会渲染成「缺失说明」；但它们的审计状态一直是
   「待核验」，等于把「已查过、厂商就是不公布」和「还没查」混在一起。
   本次按复核结果写成 not_published_by_vendor（前端徽标显示「官方未公布」），
   evidenceText 写清是哪一次复核、哪两处都没有该条目。

用法：python scripts/fill_gaps_20261031.py [--dry]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_zol_params import patch_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
TODAY = "2026-10-31"
HUAWEI_PURA90P = "https://consumer.huawei.com/cn/phones/pura90-pro/specs/"

FILL = [
    dict(id="hua-pura90p", key="weight", label="重量", value="约 213.5g",
         status="verified_official_page_reviewed", sourceUrl=HUAWEI_PURA90P,
         evidence="华为官网 Pura 90 Pro 规格页「尺寸与重量」：重量 约 213.5 g（含电池）",
         note=f"{TODAY} ZOL 参数页没有「重量」条目，改用厂商官网规格页。"),
]

CHIP_REASON = "厂商未公开处理器型号"
CHIP_EV = ("ZOL 参数页「硬件」分组无 CPU 型号条目，只有 CPU 核心数；"
           "华为官网规格页一贯不列 SoC 型号（2026-10-31 复核）")
CHG_REASON = "厂商规格页未列充电功率"
CHG_EV = "ZOL 参数页无「有线充电 / 无线充电」条目；三星中国官网规格页不列充电功率（2026-10-31 复核）"

STATUS_ONLY = [
    ("huawei-changxiang-70xhuoli", "chip", "处理器", CHIP_REASON, CHIP_EV),
    ("huawei-nova-14-huoli", "chip", "处理器", CHIP_REASON, CHIP_EV),
    ("huawei-nova-flip-s", "chip", "处理器", CHIP_REASON, CHIP_EV),
    ("huawei-nova-flip", "chip", "处理器", CHIP_REASON, CHIP_EV),
    ("huawei-pocket-2", "chip", "处理器", CHIP_REASON, CHIP_EV),
    ("hua-changxiang80", "chip", "处理器", CHIP_REASON, CHIP_EV),
    ("samsung-galaxy-a55", "charging", "充电", CHG_REASON, CHG_EV),
    ("samsung-galaxy-c55", "charging", "充电", CHG_REASON, CHG_EV),
    ("samsung-galaxy-z-flip7-fe", "charging", "充电", CHG_REASON, CHG_EV),
]


def upsert(p: dict, label: str, payload: dict) -> None:
    fa = p.setdefault("fieldAudit", [])
    entry = next((x for x in fa if isinstance(x, dict) and x.get("field") == label), None)
    if entry:
        entry.update(payload)
    else:
        fa.append(payload)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in catalog}
    n = 0

    for f in FILL:
        p = by_id.get(f["id"])
        if not p:
            print(f"!! 找不到 {f['id']}")
            continue
        print(f"FILL {p['name']} {f['label']}: {p.get(f['key'])!r} -> {f['value']!r}")
        if not args.dry:
            p[f["key"]] = f["value"]
            upsert(p, f["label"], {"field": f["label"], "value": f["value"], "valueAtAudit": f["value"],
                                   "status": f["status"], "sourceUrl": f["sourceUrl"],
                                   "evidenceText": f["evidence"], "note": f["note"]})
        n += 1

    for rid, key, label, reason, ev in STATUS_ONLY:
        p = by_id.get(rid)
        if not p:
            print(f"!! 找不到 {rid}")
            continue
        print(f"MARK {p['name']} {label}: 状态 -> 官方未公布（取值仍是占位，页面显示缺失说明）")
        if not args.dry:
            upsert(p, label, {"field": label, "value": reason, "valueAtAudit": reason,
                              "status": "not_published_by_vendor",
                              "sourceUrl": p.get("specSource") or p.get("source") or "",
                              "evidenceText": ev,
                              "note": f"{TODAY} 复核后确认为厂商不公布，不是「还没查」；取值保留占位，页面按缺失说明渲染。"})
        n += 1

    print(f"{'dry-run ' if args.dry else ''}处理 {n} 处")
    if args.dry:
        return
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    back = json.loads(CATALOG.read_text(encoding="utf-8"))
    for f in (ROOT / "index.html", ROOT / "phone-compare-demo.html"):
        if f.is_file():
            patch_html(f, back, strict=False)


if __name__ == "__main__":
    main()
