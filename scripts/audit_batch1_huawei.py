#!/usr/bin/env python3
"""按官方规格页回填 fieldAudit（第一批：HUAWEI Mate 70 / Mate 70 Pro+ / Mate X6）。

只写官方规格页直接列出的字段：屏幕、影像、电池、充电、重量、容量组合。
处理器、上市日期、官方首发价不在规格页内，保持未核验，整机准入继续关闭。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKED_AT = "2026-10-19"
NOTE = "已逐项对照中国大陆官方规格页；字段核实不等于整机准入通过。"


def item(field: str, value: str, url: str, evidence: str) -> dict:
    return {
        "field": field,
        "value": value,
        "status": "verified_official_page_reviewed",
        "sourceUrl": url,
        "evidenceText": evidence,
        "valueAtAudit": value,
        "note": NOTE,
    }


BATCH: dict[str, dict] = {
    "hua-mate70": {
        "url": "https://consumer.huawei.com/cn/phones/mate70/specs/",
        "patch": {
            "display": "6.7 英寸 OLED · 1–120Hz LTPO 自适应刷新率",
            "camera": "5000 万超光变主摄 + 4000 万超广角 + 1200 万潜望长焦 + 150 万多光谱红枫原色摄像头；5.5× 光学变焦",
            "weight": "约 203 g（含电池）",
        },
        "fields": [
            ("屏幕", "6.7 英寸 OLED，1–120Hz LTPO 自适应刷新率，FHD+ 2688×1216", "规格页「屏幕」列出尺寸 6.7 英寸、OLED 类型与 1-120 Hz LTPO 自适应刷新率及分辨率。"),
            ("影像", "5000 万超光变主摄 + 4000 万超广角 + 1200 万潜望长焦 + 150 万多光谱红枫原色摄像头；5.5× 光学变焦", "规格页「后置摄像头」逐项列出三颗镜头像素与 150 万多光谱通道红枫原色摄像头，并注明 5.5 倍光学变焦。"),
            ("电池", "5300 mAh（典型值），额定 5200 mAh", "规格页「电池」写明 5300 mAh 典型值、额定容量 5200 mAh。"),
            ("充电", "最大 66W 有线超级快充；50W 无线超级快充", "规格页「充电」写明最大 66W 有线、50W 无线，并支持无线反向充电。"),
            ("重量", "约 203 g（含电池）", "规格页「尺寸与重量」列出重量约 203 g（含电池）。"),
            ("容量组合", "12GB+256GB / 12GB+512GB / 12GB+1TB", "规格页「存储」列出 12GB RAM 与 256GB/512GB/1TB ROM 组合。"),
        ],
    },
    "hua-mate70pp": {
        "url": "https://consumer.huawei.com/cn/phones/mate70-pro-plus/specs/",
        "patch": {
            "display": "6.9 英寸 OLED · 1–120Hz LTPO 自适应刷新率",
            "camera": "5000 万超聚光主摄 + 4000 万超广角 + 4800 万超聚光微距长焦 + 150 万多光谱红枫原色摄像头；4× 光学变焦",
            "weight": "约 226 g（含电池）",
        },
        "fields": [
            ("屏幕", "6.9 英寸 OLED，1–120Hz LTPO 自适应刷新率，FHD+ 2832×1316", "规格页「屏幕」列出 6.9 英寸、OLED 类型、1-120 Hz LTPO 与分辨率 2832×1316。"),
            ("影像", "5000 万超聚光主摄 + 4000 万超广角 + 4800 万超聚光微距长焦 + 150 万多光谱红枫原色摄像头；4× 光学变焦", "规格页「后置摄像头」逐项列出三颗镜头像素、RYYB 传感器与 150 万多光谱通道红枫原色摄像头，注明 4 倍光学变焦。"),
            ("电池", "5700 mAh（典型值），额定 5600 mAh", "规格页「电池」写明 5700 mAh 典型值、额定容量 5600 mAh。"),
            ("充电", "最大 100W 有线超级快充；80W 无线超级快充", "规格页「充电」写明最大 100W 有线、80W 无线与 20W 无线反向充电。"),
            ("重量", "约 226 g（含电池）", "规格页「尺寸与重量」列出重量约 226 g（含电池）。"),
            ("容量组合", "16GB+512GB / 16GB+1TB", "规格页「存储」列出 16GB RAM 与 512GB/1TB ROM。"),
        ],
    },
    "hua-matex6": {
        "url": "https://consumer.huawei.com/cn/phones/mate-x6/specs/",
        "patch": {
            "display": "7.93 英寸内屏 + 6.45 英寸外屏 · 1–120Hz LTPO",
            "camera": "5000 万超光变主摄 + 4000 万超广角 + 4800 万长焦微距 + 150 万多光谱红枫原色摄像头；4× 光学变焦",
            "weight": "约 239 g",
        },
        "fields": [
            ("屏幕", "内屏 7.93 英寸可折叠柔性 OLED，外屏 6.45 英寸 3D 四曲 OLED，均支持 1–120Hz LTPO", "规格页「屏幕」分别列出内屏 7.93 英寸、外屏 6.45 英寸及两者的 1-120 Hz LTPO 自适应刷新率。"),
            ("影像", "5000 万超光变主摄 + 4000 万超广角 + 4800 万长焦微距 + 150 万多光谱红枫原色摄像头；4× 光学变焦", "规格页「后置摄像头配置」列出三颗镜头像素与 150 万多光谱通道红枫原色摄像头，注明 4 倍光学变焦。"),
            ("电池", "5110 mAh（典型值，标准版）；典藏版 5200 mAh", "规格页「电池」按标准版与典藏版分别列出 5110 mAh / 5200 mAh 典型容量。"),
            ("充电", "最大 66W 有线超级快充；50W 无线超级快充", "规格页「充电」写明最大 66W 有线、50W 无线。"),
            ("重量", "约 239 g", "规格页「尺寸与重量」列出重量约 239 克。"),
            ("容量组合", "标准版 12GB+256GB / 12GB+512GB；典藏版 16GB+512GB / 16GB+1TB", "规格页「存储」按标准版与典藏版分别列出 RAM/ROM 组合。"),
        ],
    },
}


def build_fields(entry: dict) -> list[dict]:
    return [item(f, v, entry["url"], ev) for f, v, ev in entry["fields"]]


def apply(record: dict, entry: dict) -> None:
    record.update(entry["patch"])
    record["fieldAudit"] = build_fields(entry)
    record["parameterAuditStatus"] = "partial"
    record["auditNotes"] = [
        "机型身份与发布月份按厂商公开信息录入",
        "屏幕、影像、电池、充电、重量、容量组合已按官方规格页逐项核对（2026-10-19）",
        "处理器、上市日期与官方首发价不在规格页内，仍未核验，整机准入保持关闭",
    ]
    record["dataNote"] = (
        "屏幕/影像/电池/充电/重量/容量组合已按厂商中国大陆官方规格页逐项核对；"
        "处理器、上市日期与首发价尚未取得官方直接证据。字段核实不等于整机通过，排名与推荐保持关闭。"
    )


def patch_html(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    m = re.search(r"window\.PHONE_DATA=(\[.*?\]);window\.MANUAL_QUOTES=", html, re.S)
    if not m:
        raise SystemExit(f"FAIL: {path.name} 未找到 PHONE_DATA")
    arr = json.loads(m.group(1))
    touched = 0
    for rec in arr:
        if rec["id"] in BATCH:
            apply(rec, BATCH[rec["id"]])
            touched += 1
    block = json.dumps(arr, ensure_ascii=False, separators=(",", ":"))
    json.loads(block)
    html = html[: m.start(1)] + block + html[m.end(1):]
    path.write_text(html, encoding="utf-8")
    print(f"  {path.name}: {touched}/{len(BATCH)} 条已回填")


def main() -> None:
    catalog_path = ROOT / "data" / "phones.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    seen = set()
    for rec in catalog:
        if rec["id"] in BATCH:
            apply(rec, BATCH[rec["id"]])
            seen.add(rec["id"])
    missing = set(BATCH) - seen
    if missing:
        raise SystemExit(f"FAIL: 目录缺少 {sorted(missing)}")
    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"PASS: 目录回填 {len(seen)} 条")
    for name in ("index.html", "phone-compare-demo.html"):
        patch_html(ROOT / name)

    report = {
        "batchedAt": CHECKED_AT,
        "batch": "huawei-mate70-x6",
        "policy": "仅记录官方规格页直接列出的字段；处理器/上市日期/首发价不在规格页内，保持未核验。",
        "models": [
            {
                "id": pid,
                "name": next(r["name"] for r in catalog if r["id"] == pid),
                "sourceUrl": entry["url"],
                "verifiedFields": [f for f, _, _ in entry["fields"]],
                "unverifiedFields": ["处理器", "正式发布/开售日期", "官方首发起售价"],
                "parameterAuditStatus": "partial",
                "eligibleForRanking": False,
            }
            for pid, entry in BATCH.items()
        ],
        "notes": [
            "HUAWEI Pura 70 / Pura 70 Pro 官方规格页已下线（跳转产品总览），本轮无法完成官方页核验。",
            "HUAWEI Mate X5 页面本轮未取得可用规格内容，保持未核验。",
        ],
    }
    out = ROOT / "reports" / "field_audit_batch1_huawei_2026-10-19.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: 报告 {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
