#!/usr/bin/env python3
"""字段核验第三批：Xiaomi 4 款（小米 14 / 14 Pro / 13 / 13 Pro）。

来源：mi.com 中国大陆官方规格页。只写入页面原文明确给出的值；
容量组合、上市日期、首发价未在已读页面段内确认，保持未核验。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTE = "已逐项对照小米中国大陆官方规格页；字段核实不等于整机准入通过。"

BATCH: dict[str, dict] = {
    "xia-14": {
        "url": "https://www.mi.com/xiaomi-14/specs",
        "patch": {
            "display": "6.36 英寸 1.5K 超视感屏 · 120Hz",
            "chip": "第三代骁龙 8",
            "camera": "徕卡超动态主摄（光影猎人 900）+ 徕卡 75mm 浮动长焦 + 115° 徕卡超广角",
            "battery": "4610 mAh",
            "charging": "90W 有线秒充 / 50W 无线秒充",
            "weight": "193 g（玻璃版）/ 188 g（科技纳米皮版）",
        },
        "fields": {
            "屏幕": ("6.36 英寸 1.5K 超视感屏，120Hz", "规格页「屏幕」列出 6.36 英寸 1.5K 超视感屏，显示帧率最高 120Hz。"),
            "处理器": ("第三代骁龙 8", "规格页列出「第三代骁龙 8 移动平台」。"),
            "影像": ("徕卡超动态主摄 + 徕卡 75mm 浮动长焦 + 115° 徕卡超广角", "规格页列出徕卡光学 Summilux 镜头、光影猎人 900 传感器与三颗镜头组合。"),
            "电池": ("4610 mAh", "规格页列出「4610mAh 超大电量」。"),
            "充电": ("90W 有线 / 50W 无线", "规格页列出 90W 小米澎湃有线秒充、50W 无线秒充。"),
            "重量": ("193 g（玻璃版）/ 188 g（科技纳米皮版）", "规格页分别列出玻璃版 193g、科技纳米皮版 188g。"),
        },
    },
    "xia-14p": {
        "url": "https://www.mi.com/xiaomi-14-pro/specs",
        "patch": {
            "display": "6.73 英寸 2K AMOLED 全等深微曲屏 · 120Hz",
            "chip": "第三代骁龙 8",
            "camera": "徕卡超动态主摄 + 徕卡 75mm 浮动长焦 + 115° 徕卡超广角",
            "battery": "4880 mAh",
            "charging": "120W 有线秒充 / 50W 无线秒充",
            "weight": "223 g（玻璃版）/ 230 g（钛金属特别版）",
        },
        "fields": {
            "屏幕": ("6.73 英寸 2K AMOLED 全等深微曲屏，120Hz", "规格页列出 6.73 英寸 2K AMOLED、3200×1440、最高 120Hz。"),
            "处理器": ("第三代骁龙 8", "规格页列出「第三代骁龙 8 移动平台」。"),
            "影像": ("徕卡超动态主摄 + 徕卡 75mm 浮动长焦 + 115° 徕卡超广角", "规格页列出徕卡三摄组合与 75mm 浮动长焦。"),
            "电池": ("4880 mAh", "规格页列出「4880mAh 超大电量」。"),
            "充电": ("120W 有线 / 50W 无线", "规格页列出 120W 有线秒充、50W 无线秒充。"),
            "重量": ("223 g（玻璃版）/ 230 g（钛金属特别版）", "规格页分别列出玻璃版 223g、钛金属特别版 230g。"),
        },
    },
    "xia-13": {
        "url": "https://www.mi.com/xiaomi-13/specs",
        "patch": {
            "display": "6.36 英寸 OLED",
            "chip": "第二代骁龙 8",
            "battery": "4500 mAh",
            "charging": "67W 有线秒充 / 50W 无线秒充",
            "weight": "189 g（玻璃版）/ 185 g（科技纳米皮版）",
        },
        "fields": {
            "屏幕": ("6.36 英寸", "规格页列出屏幕尺寸 6.36 英寸。"),
            "处理器": ("第二代骁龙 8", "规格页列出「第二代骁龙 8 移动平台」。"),
            "电池": ("4500 mAh", "规格页列出 4500mAh 电池容量。"),
            "充电": ("67W 有线 / 50W 无线", "规格页列出 67W 有线秒充与 50W 无线秒充。"),
            "重量": ("189 g（玻璃版）/ 185 g（科技纳米皮版）", "规格页分别列出玻璃版 189g、科技纳米皮版 185g。"),
        },
    },
    "xia-13p": {
        "url": "https://www.mi.com/xiaomi-13-pro/specs",
        "patch": {
            "display": "6.73 英寸 2K OLED",
            "chip": "第二代骁龙 8",
            "battery": "4820 mAh",
            "charging": "120W 有线秒充 / 50W 无线秒充",
            "weight": "229 g（陶瓷版）",
        },
        "fields": {
            "屏幕": ("6.73 英寸 2K", "规格页列出 6.73 英寸 2K 屏幕。"),
            "处理器": ("第二代骁龙 8", "规格页列出「第二代骁龙 8 移动平台」。"),
            "电池": ("4820 mAh", "规格页列出 4820mAh 电池容量。"),
            "充电": ("120W 有线 / 50W 无线", "规格页列出 120W 有线秒充与 50W 无线秒充。"),
            "重量": ("229 g（陶瓷版）", "规格页列出陶瓷版重量 229g。"),
        },
    },
}


def build_fields(entry: dict) -> list[dict]:
    return [
        {"field": k, "value": v, "status": "verified_official_page_reviewed",
         "sourceUrl": entry["url"], "evidenceText": ev, "valueAtAudit": v, "note": NOTE}
        for k, (v, ev) in entry["fields"].items()
    ]


def apply(record: dict, entry: dict) -> None:
    record.update(entry["patch"])
    record["fieldAudit"] = build_fields(entry)
    record["parameterAuditStatus"] = "partial"
    record["auditNotes"] = [
        "机型身份与发布月份按厂商公开信息录入",
        f"屏幕/处理器/影像/电池/充电/重量中可确认部分已按小米官方规格页核对（2026-10-19）",
        "容量组合、上市日期与官方首发价未完成核验，整机准入保持关闭",
    ]
    record["dataNote"] = (
        "部分参数已按小米中国大陆官方规格页逐项核对；未列出字段仍待核验。"
        "字段核实不等于整机通过，排名与推荐保持关闭。"
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
    path.write_text(html[: m.start(1)] + block + html[m.end(1):], encoding="utf-8")
    print(f"  {path.name}: {touched}/{len(BATCH)}")


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
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: 目录回填 {len(seen)} 条")
    for name in ("index.html", "phone-compare-demo.html"):
        patch_html(ROOT / name)

    report = {
        "batchedAt": "2026-10-19",
        "batch": "xiaomi-4",
        "policy": "只写入官方规格页原文明确列出的字段；未确认的容量组合/日期/价格保持未核验。",
        "models": [
            {"id": pid, "name": next(r["name"] for r in catalog if r["id"] == pid),
             "sourceUrl": e["url"], "verifiedFields": list(e["fields"]),
             "unverifiedFields": ["容量组合", "正式发布/开售日期", "官方首发起售价"],
             "parameterAuditStatus": "partial", "eligibleForRanking": False}
            for pid, e in BATCH.items()
        ],
        "notes": [
            "MIX Fold 4 / MIX Fold 3 / MIX Flip / REDMI K80 Pro / K80 的 mi.com 规格页路径本轮未取到内容，未纳入。",
        ],
    }
    out = ROOT / "reports" / "field_audit_batch3_xiaomi_2026-10-19.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: 报告已写入")


if __name__ == "__main__":
    main()
