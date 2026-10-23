#!/usr/bin/env python3
"""把「待复核/待核验」这类占位写法，换成明确的信息状态说明。

背景：华为官网规格页与中关村在线参数页都不列处理器型号，三星/苹果也不公布充电功率。
这类字段不是"没找到"，而是"厂商未公开"。因此：
- 正文改成「官方未公布…」的陈述句；
- fieldAudit 状态改为 not_published_by_vendor，前端显示「官方未公布」；
- 不再出现「待复核」这种看起来像坏掉的字样。

用法：python scripts/normalize_pending_fields.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_zol_params import patch_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
TODAY = "2026-10-24"

KIRIN = "麒麟平台（官方未公布具体型号）"
EXYNOS = "Exynos 平台（官方未公布具体型号）"
SAM_CHARGE = "支持有线 / 无线充电（官方未标注功率）"

# id -> {字段: (新文案, 依据说明)}
FIX = {
    "hua-pura80": {"chip": (KIRIN, "华为官网 Pura 80 规格页与 ZOL 参数页均无「处理器/CPU 型号」条目")},
    "hua-pura80p": {"chip": (KIRIN, "华为官网与 ZOL 参数页均无「处理器/CPU 型号」条目")},
    "hua-pura80pp": {"chip": (KIRIN, "华为官网与 ZOL 参数页均无「处理器/CPU 型号」条目")},
    "hua-purax": {"chip": (KIRIN, "华为官网与 ZOL 参数页均无「处理器/CPU 型号」条目")},
    "huawei-z21162115265": {"chip": (KIRIN, "华为官网与 ZOL 参数页均无「处理器/CPU 型号」条目")},
    "huawei-z20001999708": {"chip": (KIRIN, "华为官网与 ZOL 参数页均无「处理器/CPU 型号」条目")},
    "huawei-z21292128093": {"chip": (KIRIN, "华为官网与 ZOL 参数页均无「处理器/CPU 型号」条目")},
    "sam-zflip7": {"chip": (EXYNOS, "三星中国官网与 ZOL 参数页均未标注 SoC 具体型号"),
                   "charging": (SAM_CHARGE, "ZOL 参数页无「有线/无线充电」条目")},
    "sam-26": {"charging": (SAM_CHARGE, "ZOL 参数页无「有线/无线充电」条目")},
    "sam-26p": {"charging": (SAM_CHARGE, "ZOL 参数页无「有线/无线充电」条目")},
    "apple-z21052104329": {
        "charging": ("USB-C 快充（官方未标注功率）/ MagSafe 无线充电", "Apple 不公布 iPhone 充电瓦数"),
        "battery": ("官方未按 mAh 公布；视频播放最长 27 小时", "Apple 仅公布续航时长，不公布 mAh"),
    },
}

AUDIT_NAME = {"display": "屏幕", "chip": "处理器", "camera": "影像", "battery": "电池",
              "charging": "充电", "weight": "重量", "storage": "容量组合"}


def main() -> None:
    catalog: list[dict] = json.loads(CATALOG.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in catalog}
    touched = 0
    for pid, fields in FIX.items():
        p = by_id.get(pid)
        if not p:
            print(f"missing record: {pid}")
            continue
        url = p.get("source") if str(p.get("source", "")).startswith("http") else p.get("specSource", "")
        for key, (text, why) in fields.items():
            p[key] = text
            name = AUDIT_NAME[key]
            fa = p.setdefault("fieldAudit", [])
            entry = next((x for x in fa if isinstance(x, dict) and x.get("field") == name), None)
            payload = {"field": name, "value": text, "valueAtAudit": text,
                       "status": "not_published_by_vendor", "sourceUrl": url,
                       "evidenceText": f"{why}（{TODAY} 复核）",
                       "note": "厂商未公开该字段，不用估算值填充。"}
            if entry:
                entry.update(payload)
            else:
                fa.append(payload)
            touched += 1
        p.setdefault("auditNotes", []).append(f"{TODAY} 占位文案改为明确的信息状态：{len(fields)} 项厂商未公开字段。")
    print(f"fields normalized: {touched}")
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    back = json.loads(CATALOG.read_text(encoding="utf-8"))
    for f in [ROOT / "index.html", ROOT / "phone-compare-demo.html"]:
        patch_html(f, back)


if __name__ == "__main__":
    main()
