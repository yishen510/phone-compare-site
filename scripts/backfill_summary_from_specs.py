#!/usr/bin/env python3
"""用已抓取的完整参数（中关村在线）回填卡片/详情里的摘要字段占位符。

只处理"待复核/待核验/待补/待录入"这类占位值，绝不覆盖已有真值。
回填后写入 fieldAudit（cross_checked_secondary_source），前端显示"第三方核验"。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_zol_params import patch_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
PLACEHOLDER = ("待复核", "待核验", "待补", "待录入", "待逐项录入", "官方规格待", "待定")

# 前端 AUDIT_FIELD_NAMES 的中文名字
AUDIT_NAME = {"display": "屏幕", "chip": "处理器", "camera": "影像", "battery": "电池",
              "charging": "充电", "weight": "重量", "storage": "容量组合"}


def is_placeholder(v: str) -> bool:
    return (not v) or any(k in str(v) for k in PLACEHOLDER)


def naive_clean(v: str) -> str:
    v = re.sub(r"更多[^，,>]{0,40}(?:手机)?>?", "", v)
    v = re.sub(r"\s*[>＞]+\s*", " ", v)
    v = re.sub(r"\s*[，,]+\s*$", "", v)
    return re.sub(r"\s+", " ", v).strip()


def pick(specs: list[dict], label: str) -> str | None:
    for g in specs:
        for k, v in g["items"]:
            if k == label:
                return v
    return None


def num(pattern: str, value: str | None) -> str | None:
    if not value:
        return None
    m = re.search(pattern, value, re.I)
    return m.group(1) if m else None


def derive(specs: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    size = num(r"(\d+(?:\.\d+)?)\s*英寸", pick(specs, "屏幕尺寸"))
    refresh = num(r"(\d{2,3})\s*Hz", pick(specs, "屏幕刷新率"))
    stype = pick(specs, "屏幕类型") or ""
    stype = naive_clean(re.split(r"[，,]", stype)[0])
    stype = re.sub(r"[（(].*?[)）]", "", stype).strip()
    if size:
        out["display"] = " · ".join(x for x in [f"{size} 英寸", stype or "OLED", f"{refresh}Hz" if refresh else ""] if x)

    chip = pick(specs, "CPU型号")
    if chip:
        out["chip"] = naive_clean(chip)[:40]

    mah = num(r"(\d{3,5})\s*mAh", pick(specs, "电池容量"))
    if mah:
        out["battery"] = f"{mah}mAh"

    wired = num(r"(\d{2,3})\s*[wW]", pick(specs, "有线充电") or pick(specs, "充电功率"))
    wl_raw = pick(specs, "无线充电")
    wireless = num(r"(\d{2,3})\s*[wW]", wl_raw)
    parts = []
    if wired:
        parts.append(f"{wired}W 有线")
    if wireless:
        parts.append(f"{wireless}W 无线")
    if parts:
        out["charging"] = " / ".join(parts)

    gram = num(r"(\d{2,3}(?:\.\d)?)\s*g", pick(specs, "重量"))
    if gram:
        out["weight"] = f"{gram}g"

    ram = num(r"(\d{1,2}\s*GB)", pick(specs, "RAM容量"))
    rom = num(r"(\d{1,3}\s*(?:GB|TB))", pick(specs, "ROM容量"))
    if ram and rom:
        out["storage"] = f"{ram.replace(' ', '')}+{rom.replace(' ', '')}"

    rear = pick(specs, "后置摄像头")
    front = pick(specs, "前置摄像头")
    if rear:
        txt = f"后置 {naive_clean(rear)[:46]}"
        if front:
            txt += f"；前置 {naive_clean(front)[:22]}"
        out["camera"] = txt

    osv = pick(specs, "操作系统")
    if osv:
        out["os"] = naive_clean(osv)[:30]
    return out


def main() -> None:
    catalog: list[dict] = json.loads(CATALOG.read_text(encoding="utf-8"))
    filled = 0
    per_field: dict[str, int] = {}
    for p in catalog:
        specs = p.get("specs")
        if not specs:
            continue
        vals = derive(specs)
        # 发布日期：用参数页的「上市日期/国内发布时间」补成完整日期
        raw_date = pick(specs, "上市日期") or pick(specs, "国内发布时间")
        m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", naive_clean(raw_date or ""))
        if m:
            disp = f"{m.group(1)}年{int(m.group(2)):02d}月{int(m.group(3)):02d}日"
            fa = p.setdefault("fieldAudit", [])
            entry = next((x for x in fa if isinstance(x, dict) and x.get("field") == "正式发布/开售日期"), None)
            if entry is None or is_placeholder(str(entry.get("valueAtAudit", ""))):
                payload = {"field": "正式发布/开售日期", "value": disp, "valueAtAudit": disp,
                           "status": "cross_checked_secondary_source",
                           "sourceUrl": p.get("specSource", ""),
                           "evidenceText": f"中关村在线参数页：上市日期 {disp}",
                           "note": "2026-10-21 由完整参数表自动回填；第三方参数站。"}
                if entry:
                    entry.update(payload)
                else:
                    fa.append(payload)
                if not p.get("launchDateDisplay") or is_placeholder(p["launchDateDisplay"]):
                    p["launchDateDisplay"] = disp
        changed = []
        for k, v in vals.items():
            if not v:
                continue
            if k == "os":
                if is_placeholder(p.get("os")):
                    p["os"] = v
                    changed.append(k)
                continue
            name = AUDIT_NAME.get(k)
            fa = p.setdefault("fieldAudit", []) if name else None
            entry = next((x for x in fa if isinstance(x, dict) and x.get("field") == name), None) if fa else None
            need_value = is_placeholder(p.get(k))
            need_audit = bool(entry) and is_placeholder(str(entry.get("valueAtAudit", "")))
            if not (need_value or need_audit):
                continue
            if need_value:
                p[k] = v
                changed.append(k)
                per_field[k] = per_field.get(k, 0) + 1
            payload = {
                "field": name,
                "value": v,
                "valueAtAudit": v,
                "status": "cross_checked_secondary_source",
                "sourceUrl": p.get("specSource", ""),
                "evidenceText": f"中关村在线参数页：{name} {v}",
                "note": "2026-10-21 由完整参数表自动回填；第三方参数站，非厂商官方页。",
            }
            if entry:
                entry.update(payload)
            elif fa is not None:
                fa.append(payload)
        if changed:
            filled += 1
    print(f"records updated: {filled}; per-field: {per_field}")
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    back = json.loads(CATALOG.read_text(encoding="utf-8"))
    for f in [ROOT / "index.html", ROOT / "phone-compare-demo.html"]:
        patch_html(f, back)


if __name__ == "__main__":
    main()
