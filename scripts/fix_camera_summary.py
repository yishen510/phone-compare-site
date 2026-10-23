#!/usr/bin/env python3
"""修复上一轮自动回填产生的相机摘要（形如「后置 后置摄像头1：…」和截断结尾）。

只处理带该缺陷的记录，用参数表重新拼一句人话，并同步 fieldAudit 里的影像条目。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backfill_summary_from_specs import AUDIT_NAME, camera_text  # noqa: E402
from import_zol_params import patch_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"


def broken(value: str) -> bool:
    v = value or ""
    return "后置 后置" in v or "前置 前置" in v or v.endswith("后置") or v.endswith("：") or "：后置" in v


def main() -> None:
    catalog: list[dict] = json.loads(CATALOG.read_text(encoding="utf-8"))
    fixed = 0
    for p in catalog:
        if not broken(p.get("camera") or ""):
            continue
        new = camera_text(p.get("specs") or [])
        if not new or new == p.get("camera"):
            continue
        p["camera"] = new
        for entry in p.get("fieldAudit") or []:
            if isinstance(entry, dict) and entry.get("field") == AUDIT_NAME["camera"]:
                entry["value"] = new
                entry["valueAtAudit"] = new
                entry["evidenceText"] = f"中关村在线参数页：摄像头名称/像素 → {new}"
                entry["note"] = "2026-10-24 由完整参数表重新生成摘要（修正上一版重复前缀与截断）。"
        fixed += 1
    # 统一像素排版：「5000万像素」→「5000 万像素」
    for p in catalog:
        v = p.get("camera") or ""
        nv = re.sub(r"(\d)(万|亿)像素", r"\1 \2像素", v)
        nv = re.sub(r"像素(?=[0-9A-Za-z])", "像素 ", nv)
        if nv != v:
            p["camera"] = nv
            for entry in p.get("fieldAudit") or []:
                if isinstance(entry, dict) and entry.get("field") == AUDIT_NAME["camera"]:
                    entry["value"] = nv
                    entry["valueAtAudit"] = nv
    print(f"camera summaries repaired: {fixed}")
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    back = json.loads(CATALOG.read_text(encoding="utf-8"))
    for f in [ROOT / "index.html", ROOT / "phone-compare-demo.html"]:
        patch_html(f, back)


if __name__ == "__main__":
    main()
