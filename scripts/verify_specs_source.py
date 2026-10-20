#!/usr/bin/env python3
"""回扫所有已入库的 specSource，剔除"非手机页"或型号对不上的记录。

自动抓取难免误命中（例如 P60 Pro 耳机、10Pro 移动电源），本脚本按
「必须是手机页 + 型号词/qualifier 严格一致」重新校验，不合格的直接清空 specs。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_import_zol_specs import brand_ok, in_base, is_phone_page, key_of, title_of  # noqa: E402
from import_zol_params import fetch, patch_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"


def main() -> None:
    catalog: list[dict] = json.loads(CATALOG.read_text(encoding="utf-8"))
    targets = [p for p in catalog if p.get("specSource")]
    print(f"checking {len(targets)} records with specSource")
    dropped = []
    for idx, p in enumerate(targets, 1):
        url = p["specSource"]
        try:
            t = title_of(fetch(url))
        except Exception as exc:  # noqa: BLE001
            print(f"[{idx}] KEEP? fetch fail {p['id']}: {str(exc)[:50]}")
            continue
        base, quals = key_of(p["name"], p["brand"])
        cbase, cquals = key_of(t, p["brand"])
        ok = is_phone_page(t) and brand_ok(t, p["brand"]) and in_base(base, cbase) and cquals == quals
        if not ok:
            dropped.append({"id": p["id"], "name": p["name"], "url": url, "title": t})
            print(f"[{idx}] DROP {p['name']} <- {t[:44]}")
            for k in ["specs", "specSource", "specSourceName", "specFieldCount", "specCollectedAt"]:
                p.pop(k, None)
            p.setdefault("auditNotes", []).append(
                f"2026-10-21 回扫剔除误匹配参数（来源页非手机或型号不符）：{t[:60]}")
        time.sleep(0.4)

    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    back = json.loads(CATALOG.read_text(encoding="utf-8"))
    print(f"dropped={len(dropped)}; remain with specs={sum(1 for x in back if x.get('specs'))}")
    for f in [ROOT / "index.html", ROOT / "phone-compare-demo.html"]:
        patch_html(f, back)
    out = ROOT / "reports" / "specs_source_verify_2026-10-21.json"
    out.write_text(json.dumps(dropped, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
