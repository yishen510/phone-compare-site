#!/usr/bin/env python3
"""通用回填器：把 JSON 里的字段级结果写入 data/phones.json 与两个页面。

JSON 结构：{id: {url, fields: {中文字段名: 值}, status?}}
中文字段名到记录字段的映射固定；容量组合只写入 storageOptions 的一致性校验，不改 storage 字符串。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELD_MAP = {"屏幕": "display", "处理器": "chip", "影像": "camera", "电池": "battery",
             "充电": "charging", "重量": "weight"}


def build(entry: dict) -> list[dict]:
    status = entry.get("status", "verified_official_page_reviewed")
    note = entry.get("note") or (
        "已逐项对照厂商中国大陆官方规格页；字段核实不等于整机准入通过。"
        if status == "verified_official_page_reviewed"
        else "第三方参数站核对，非厂商官方页面；仅供交叉参考，不构成整机准入依据。"
    )
    return [
        {"field": k, "value": v, "status": status, "sourceUrl": entry["url"],
         "evidenceText": f"官方规格页明确列出：{v}。" if status == "verified_official_page_reviewed" else f"第三方参数页列出：{v}。",
         "valueAtAudit": v, "note": note}
        for k, v in entry["fields"].items()
    ]


def apply(rec: dict, entry: dict) -> None:
    for zh, en in FIELD_MAP.items():
        if zh in entry["fields"]:
            rec[en] = entry["fields"][zh]
    rec["fieldAudit"] = build(entry)
    rec["parameterAuditStatus"] = "partial"
    rec["auditNotes"] = [
        "机型身份与发布月份按厂商公开信息录入",
        "屏幕/电池/充电/重量/容量组合等已按厂商官方规格页核对（2026-10-19）",
        "其余字段与整机准入仍未通过，排名与推荐保持关闭",
    ]
    rec["dataNote"] = (
        "部分字段已按厂商中国大陆官方规格页逐项核对；未列出字段仍待核验。"
        "字段核实不等于整机通过，排名与推荐保持关闭。"
    )


def patch_html(path: Path, batch: dict) -> None:
    html = path.read_text(encoding="utf-8")
    m = re.search(r"window\.PHONE_DATA=(\[.*?\]);window\.MANUAL_QUOTES=", html, re.S)
    arr = json.loads(m.group(1))
    n = 0
    for rec in arr:
        if rec["id"] in batch:
            apply(rec, batch[rec["id"]])
            n += 1
    block = json.dumps(arr, ensure_ascii=False, separators=(",", ":"))
    json.loads(block)
    path.write_text(html[: m.start(1)] + block + html[m.end(1):], encoding="utf-8")
    print("  patched", path.name, n)


def main() -> None:
    batch = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    p = ROOT / "data" / "phones.json"
    catalog = json.loads(p.read_text(encoding="utf-8"))
    hit = 0
    for rec in catalog:
        if rec["id"] in batch:
            apply(rec, batch[rec["id"]])
            hit += 1
    missing = set(batch) - {r["id"] for r in catalog}
    if missing:
        raise SystemExit(f"FAIL: 目录缺少 {sorted(missing)}")
    p.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: 回填 {hit} 条")
    for name in ("index.html", "phone-compare-demo.html"):
        patch_html(ROOT / name, batch)


if __name__ == "__main__":
    main()
