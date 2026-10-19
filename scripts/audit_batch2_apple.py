#!/usr/bin/env python3
"""字段核验第二批：Apple 5 款（iPhone 17 Pro / 16 Pro / 16 / 15 Pro / 14 Pro）。

来源全部为 Apple 官方页面（support.apple.com 技术规格页或 apple.com.cn 在售规格页）。
逐项只记录页面直接写明的值；处理器在规格页明确列出，故一并核验。
首发价与上市日期不在规格页内，保持未核验。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTE = "已逐项对照 Apple 中国大陆官方规格页；字段核实不等于整机准入通过。"
BATTERY = "官方未按 mAh 公布；视频播放最长 {h} 小时"

BATCH: dict[str, dict] = {
    "apple-17p": {
        "url": "https://support.apple.com/zh-cn/125090",
        "patch": {
            "display": "6.3 英寸 OLED · ProMotion 1–120Hz",
            "camera": "4800 万融合式主摄 + 4800 万融合式超广角 + 4800 万融合式长焦（4×/8× 光学品质变焦）",
            "battery": BATTERY.format(h=31),
            "charging": "USB-C 快充（40W 及以上适配器 20 分钟充至 50%）；MagSafe 最高 15W",
            "weight": "204 g",
        },
        "fields": {
            "屏幕": ("6.3 英寸 OLED，2622×1206，ProMotion 最高 120Hz", "规格页「显示屏」列出 6.3 英寸 OLED、2622×1206 分辨率与 ProMotion 最高 120Hz。"),
            "处理器": ("A19 Pro", "规格页「芯片」列出 A19 Pro，6 核 CPU / 6 核 GPU / 16 核神经网络引擎。"),
            "影像": ("4800 万融合式主摄 + 4800 万融合式超广角 + 4800 万融合式长焦；4×/8× 光学品质变焦", "规格页「摄像头」列出三颗 4800 万像素融合式镜头，并注明 8 倍光学品质变焦。"),
            "电池": (BATTERY.format(h=31), "规格页「电源和电池」写明视频播放最长可达 31 小时，未公布 mAh。"),
            "充电": ("USB-C 快充（40W 及以上适配器 20 分钟充至 50%）；MagSafe 最高 15W", "规格页写明需 40W 或更大功率适配器、20 分钟充至 50%，MagSafe 最高 15 瓦。"),
            "重量": ("204 g", "规格页「尺寸与重量」列出重量 204 克。"),
            "容量组合": ("256GB / 512GB / 1TB", "规格页「容量」列出 256GB、512GB、1TB。"),
        },
    },
    "apple-16p": {
        "url": "https://support.apple.com/zh-cn/121031",
        "patch": {
            "display": "6.3 英寸 OLED · ProMotion 1–120Hz",
            "camera": "4800 万融合式主摄 + 4800 万超广角 + 1200 万 5× 长焦",
            "battery": BATTERY.format(h=27),
            "charging": "USB-C 快充（20W 及以上适配器 30 分钟充至 50%）；MagSafe 最高 15W",
            "weight": "199 g",
        },
        "fields": {
            "屏幕": ("6.3 英寸 OLED，2622×1206，ProMotion 最高 120Hz", "规格页「显示屏」列出 6.3 英寸 OLED、2622×1206 与 ProMotion 最高 120Hz。"),
            "处理器": ("A18 Pro", "规格页「芯片」列出 A18 Pro。"),
            "影像": ("4800 万融合式主摄 + 4800 万超广角 + 1200 万 5× 长焦", "规格页「摄像头」列出主摄 4800 万、超广角 4800 万、长焦 1200 万，5 倍光学变焦。"),
            "电池": (BATTERY.format(h=27), "规格页「电源和电池」写明视频播放最长可达 27 小时，未公布 mAh。"),
            "充电": ("USB-C 快充（20W 及以上适配器 30 分钟充至 50%）；MagSafe 最高 15W", "规格页写明需 20W 或更大功率适配器、30 分钟充至 50%，MagSafe 最高 15 瓦。"),
            "重量": ("199 g", "规格页「尺寸与重量」列出重量 199 克。"),
            "容量组合": ("128GB / 256GB / 512GB / 1TB", "规格页「容量」列出 128GB、256GB、512GB、1TB。"),
        },
    },
    "apple-16": {
        "url": "https://www.apple.com.cn/iphone-16/specs",
        "patch": {
            "display": "6.1 英寸 OLED · 60Hz",
            "camera": "4800 万融合式主摄 + 1200 万超广角（支持 2× 光学品质变焦）",
            "battery": BATTERY.format(h=22),
            "charging": "USB-C 快充（20W 及以上适配器 30 分钟充至 50%）；MagSafe 最高 15W",
            "weight": "170 g",
        },
        "fields": {
            "屏幕": ("6.1 英寸 OLED，2556×1179，60Hz", "规格页「显示屏」列出 6.1 英寸 OLED、2556×1179 分辨率，未标注高刷新率。"),
            "处理器": ("A18", "规格页「芯片」列出 A18 芯片（6 核 CPU / 5 核 GPU / 16 核神经网络引擎）。"),
            "影像": ("4800 万融合式主摄 + 1200 万超广角；支持 2× 光学品质变焦", "规格页「摄像头」列出 4800 万融合式主摄与 1200 万超广角，注明 2 倍光学品质变焦。"),
            "电池": (BATTERY.format(h=22), "规格页「电源和电池」写明视频播放最长可达 22 小时，未公布 mAh。"),
            "充电": ("USB-C 快充（20W 及以上适配器 30 分钟充至 50%）；MagSafe 最高 15W", "规格页写明需 20 瓦或更大功率适配器、30 分钟充至 50%，MagSafe 最高 15 瓦。"),
            "重量": ("170 g", "规格页「尺寸与重量」列出重量 170 克。"),
            "容量组合": ("128GB / 256GB / 512GB", "规格页「容量」列出 128GB 起，中国大陆在售档位为 128/256/512GB。"),
        },
    },
    "apple-15p": {
        "url": "https://support.apple.com/zh-cn/111829",
        "patch": {
            "display": "6.1 英寸 OLED · ProMotion 1–120Hz",
            "camera": "4800 万主摄 + 1200 万超广角 + 1200 万 3× 长焦",
            "battery": BATTERY.format(h=23),
            "charging": "USB-C 快充（20W 及以上适配器 30 分钟充至 50%）；MagSafe 最高 15W",
            "weight": "187 g",
        },
        "fields": {
            "屏幕": ("6.1 英寸 OLED，2556×1179，ProMotion 最高 120Hz", "规格页「显示屏」列出 6.1 英寸 OLED、2556×1179 与 ProMotion 最高 120Hz。"),
            "处理器": ("A17 Pro", "规格页「芯片」列出 A17 Pro（6 核 CPU / 6 核 GPU / 16 核神经网络引擎）。"),
            "影像": ("4800 万主摄 + 1200 万超广角 + 1200 万 3× 长焦", "规格页「摄像头」列出三颗镜头像素，3 倍光学变焦。"),
            "电池": (BATTERY.format(h=23), "规格页「电源和电池」写明视频播放最长可达 23 小时，未公布 mAh。"),
            "充电": ("USB-C 快充（20W 及以上适配器 30 分钟充至 50%）；MagSafe 最高 15W", "规格页写明需 20 瓦或更大功率适配器、30 分钟充至 50%，MagSafe 最高 15 瓦。"),
            "重量": ("187 g", "规格页「尺寸与重量」列出重量 187 克。"),
            "容量组合": ("128GB / 256GB / 512GB / 1TB", "规格页「容量」列出 128GB、256GB、512GB、1TB。"),
        },
    },
    "apple-14p": {
        "url": "https://support.apple.com/zh-cn/111849",
        "patch": {
            "display": "6.1 英寸 OLED · ProMotion 1–120Hz",
            "camera": "4800 万主摄 + 1200 万超广角 + 1200 万 3× 长焦",
            "battery": BATTERY.format(h=23),
            "charging": "闪电接口有线充电（20W 及以上适配器 30 分钟充至 50%）；MagSafe 最高 15W",
            "weight": "206 g",
        },
        "fields": {
            "屏幕": ("6.1 英寸 OLED，2556×1179，ProMotion 最高 120Hz", "规格页「显示屏」列出 6.1 英寸 OLED、2556×1179 与 ProMotion 最高 120Hz。"),
            "处理器": ("A16 仿生", "规格页「芯片」列出 A16 仿生芯片（6 核 CPU / 5 核 GPU / 16 核神经网络引擎）。"),
            "影像": ("4800 万主摄 + 1200 万超广角 + 1200 万 3× 长焦", "规格页「摄像头」列出三颗镜头像素，3 倍光学变焦。"),
            "电池": (BATTERY.format(h=23), "规格页「电源和电池」写明视频播放最长可达 23 小时，未公布 mAh。"),
            "充电": ("闪电接口有线充电（20W 及以上适配器 30 分钟充至 50%）；MagSafe 最高 15W", "规格页写明通过闪电接口有线充电、20 瓦适配器 30 分钟充至 50%，MagSafe 最高 15 瓦。"),
            "重量": ("206 g", "规格页「尺寸与重量」列出重量 206 克。"),
            "容量组合": ("128GB / 256GB / 512GB / 1TB", "规格页「容量」列出 128GB、256GB、512GB、1TB。"),
        },
    },
}


def build_fields(entry: dict) -> list[dict]:
    out = []
    for name, (value, evidence) in entry["fields"].items():
        out.append({
            "field": name,
            "value": value,
            "status": "verified_official_page_reviewed",
            "sourceUrl": entry["url"],
            "evidenceText": evidence,
            "valueAtAudit": value,
            "note": NOTE,
        })
    return out


def apply(record: dict, entry: dict) -> None:
    record.update(entry["patch"])
    record["fieldAudit"] = build_fields(entry)
    record["parameterAuditStatus"] = "partial"
    record["auditNotes"] = [
        "机型身份与发布月份按厂商公开信息录入",
        "屏幕、处理器、影像、电池、充电、重量、容量组合已按 Apple 官方规格页逐项核对（2026-10-19）",
        "上市日期与官方首发价不在规格页内，仍未核验，整机准入保持关闭",
    ]
    record["dataNote"] = (
        "屏幕/处理器/影像/电池/充电/重量/容量组合已按 Apple 中国大陆官方规格页逐项核对；"
        "上市日期与首发价尚未取得官方直接证据。字段核实不等于整机通过，排名与推荐保持关闭。"
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
        "batchedAt": "2026-10-19",
        "batch": "apple-5",
        "policy": "只记录 Apple 官方规格页直接列出的字段；上市日期与首发价不在规格页内，保持未核验。",
        "models": [
            {
                "id": pid,
                "name": next(r["name"] for r in catalog if r["id"] == pid),
                "sourceUrl": e["url"],
                "verifiedFields": list(e["fields"]),
                "unverifiedFields": ["正式发布/开售日期", "官方首发起售价"],
                "parameterAuditStatus": "partial",
                "eligibleForRanking": False,
            }
            for pid, e in BATCH.items()
        ],
        "notes": [
            "iPhone 15（标准版）支持页编号未确认，本轮未纳入，保持原状。",
            "Apple 中国官网已下架 16 Pro / 15 Pro / 14 Pro 的在售页，改用 support.apple.com 官方技术规格页（长期保留）。",
        ],
    }
    out = ROOT / "reports" / "field_audit_batch2_apple_2026-10-19.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: 报告 {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
