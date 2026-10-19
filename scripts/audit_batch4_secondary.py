#!/usr/bin/env python3
"""字段核验第四批：第三方来源（中关村在线）。

官方规格页已下架的机型，改用中关村在线产品页交叉核对，
状态记为 cross_checked_secondary_source，界面显示「第三方核验」，
不计入官方核验，也不改变整机准入结论。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTE = "第三方参数站（中关村在线）核对，非厂商官方页面；仅供交叉参考，不构成整机准入依据。"

BATCH: dict[str, dict] = {
    "hua-pura70": {
        "url": "https://wap.zol.com.cn/1987/1986304/index.html",
        "patch": {
            "display": "6.6 英寸 OLED · 1–120Hz",
            "chip": "麒麟 9010",
            "camera": "5000 万超聚光主摄（F1.4–F4.0，OIS）+ 1300 万超广角 + 1200 万潜望长焦（5× 光学）",
            "battery": "4900 mAh（典型值）",
            "charging": "66W 有线 / 50W 无线",
            "weight": "207 g",
        },
        "fields": {
            "屏幕": ("6.6 英寸 OLED，2760×1256，120Hz（1–120）", "中关村在线参数页列出 6.6 英寸 OLED、2760×1256、120Hz（1-120）。"),
            "处理器": ("麒麟 9010", "中关村在线参数页「CPU 型号」为麒麟 9010。"),
            "影像": ("5000 万超聚光主摄 + 1300 万超广角 + 1200 万潜望长焦，5× 光学", "中关村在线参数页列出后置三摄像素与 5 倍光学变焦。"),
            "电池": ("4900 mAh（典型值）", "中关村在线参数页「电池容量」为 4900mAh。"),
            "充电": ("66W 有线 / 50W 无线", "中关村在线参数页列出有线 66W、无线 50W。"),
            "重量": ("207 g", "中关村在线参数页「重量」为 207g。"),
            "容量组合": ("12GB+256GB / 12GB+512GB / 12GB+1TB", "中关村在线参数页 ROM 容量列出 256GB/512GB/1TB，RAM 为 12GB。"),
        },
    },
}


def build(entry: dict) -> list[dict]:
    return [
        {"field": k, "value": v, "status": "cross_checked_secondary_source",
         "sourceUrl": entry["url"], "evidenceText": ev, "valueAtAudit": v, "note": NOTE}
        for k, (v, ev) in entry["fields"].items()
    ]


def apply(rec: dict, entry: dict) -> None:
    rec.update(entry["patch"])
    rec["fieldAudit"] = build(entry)
    rec["parameterAuditStatus"] = "partial_secondary_source"
    rec["auditNotes"] = [
        "厂商官方规格页已下架，改用中关村在线产品页交叉核对（2026-10-19）",
        "第三方来源仅作参考，与官方核验分开记录",
        "整机准入保持关闭",
    ]
    rec["dataNote"] = (
        "厂商官方规格页已下架，参数改由中关村在线产品页交叉核对，界面标注为「第三方核验」；"
        "该等级不等同于官方核验，排名与推荐保持关闭。"
    )


def patch_html(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    m = re.search(r"window\.PHONE_DATA=(\[.*?\]);window\.MANUAL_QUOTES=", html, re.S)
    arr = json.loads(m.group(1))
    for rec in arr:
        if rec["id"] in BATCH:
            apply(rec, BATCH[rec["id"]])
    block = json.dumps(arr, ensure_ascii=False, separators=(",", ":"))
    json.loads(block)
    path.write_text(html[: m.start(1)] + block + html[m.end(1):], encoding="utf-8")
    print("  patched", path.name)


def main() -> None:
    p = ROOT / "data" / "phones.json"
    catalog = json.loads(p.read_text(encoding="utf-8"))
    for rec in catalog:
        if rec["id"] in BATCH:
            apply(rec, BATCH[rec["id"]])
    p.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name in ("index.html", "phone-compare-demo.html"):
        patch_html(ROOT / name)
    print("PASS: 第三方核验回填", len(BATCH), "条")


if __name__ == "__main__":
    main()
