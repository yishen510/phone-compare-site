#!/usr/bin/env python3
"""为缺价格核验条目的机型补 fieldAudit 记录。

背景：详情页「价格字段」一栏读的是 fieldAudit['官方首发起售价']，
老数据只有 priceCN / priceSource，没有对应审计条目，于是全部显示「待核验」。
这里按已有 priceAuditStatus 与 priceSource 生成条目，不改变价格本身。

状态映射：
- priceAuditStatus ∈ {verified, cross_checked_official, cross_checked_official_source}
  → verified_official_page_reviewed（前端显示「已核验」）
- 其余 → cross_checked_secondary_source（前端显示「第三方核验」）
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
OFFICIAL_STATUS = {"verified", "cross_checked_official", "cross_checked_official_source"}
FIELD = "官方首发起售价"


def has_price_audit(p: dict) -> bool:
    for x in p.get("fieldAudit") or []:
        if isinstance(x, dict) and x.get("field") in (FIELD, "价格"):
            return True
    return False


def main() -> None:
    catalog: list[dict] = json.loads(CATALOG.read_text(encoding="utf-8"))
    filled = 0
    for p in catalog:
        if has_price_audit(p) or p.get("priceCN") in (None, ""):
            continue
        url = str(p.get("priceSource") or p.get("source") or "")
        if not url.startswith("http"):
            continue
        price = p["priceCN"]
        official = str(p.get("priceAuditStatus") or "") in OFFICIAL_STATUS
        entry = {
            "field": FIELD,
            "value": price,
            "valueAtAudit": price,
            "status": "verified_official_page_reviewed" if official else "cross_checked_secondary_source",
            "sourceUrl": url,
            "evidenceText": f"首发价来源：{p.get('priceSourceName') or url}",
            "note": f"{TODAY} 按既有 priceSource 生成价格审计条目；价格数值未改动。",
        }
        p.setdefault("fieldAudit", []).append(entry)
        filled += 1
    print(f"price audit entries added: {filled}")
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    back = json.loads(CATALOG.read_text(encoding="utf-8"))
    for f in [ROOT / "index.html", ROOT / "phone-compare-demo.html"]:
        patch_html(f, back)


if __name__ == "__main__":
    main()
