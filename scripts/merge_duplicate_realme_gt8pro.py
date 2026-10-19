#!/usr/bin/env python3
"""合并重复的真我 GT8 Pro 记录。

保留 realme-gt8-pro（带 realme 中国大陆官方规格页、容量组合与报价目标容量），
删除占位记录 realme-gt8p，并把后者独有的发布来源与审计说明回填到保留记录。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEEP = "realme-gt8-pro"
DROP = "realme-gt8p"
FIELDS_FROM_DROP = ("announcementSource", "auditNotes")


def merge(catalog: list[dict]) -> tuple[list[dict], dict]:
    by_id = {p["id"]: p for p in catalog}
    if KEEP not in by_id or DROP not in by_id:
        raise SystemExit("FAIL: 待合并记录不全，可能已合并过")
    keep, drop = by_id[KEEP], by_id[DROP]
    for field in ("name", "brand", "year"):
        if keep.get(field) != drop.get(field):
            raise SystemExit(f"FAIL: {field} 不一致，拒绝合并")
    for field in FIELDS_FROM_DROP:
        if not keep.get(field) and drop.get(field):
            keep[field] = drop[field]
    merged = [p for p in catalog if p["id"] != DROP]
    return merged, keep


def patch_html(path: Path, keep: dict) -> None:
    html = path.read_text(encoding="utf-8")
    m = re.search(r"window\.PHONE_DATA=(\[.*?\]);window\.MANUAL_QUOTES=", html, re.S)
    if not m:
        raise SystemExit(f"FAIL: {path.name} 未找到 PHONE_DATA")
    arr = json.loads(m.group(1))
    before = len(arr)
    arr = [p for p in arr if p["id"] != DROP]
    idx = next((i for i, p in enumerate(arr) if p["id"] == KEEP), None)
    if idx is None:
        raise SystemExit(f"FAIL: {path.name} 缺少 {KEEP}")
    for field in FIELDS_FROM_DROP:
        if not arr[idx].get(field) and keep.get(field):
            arr[idx][field] = keep[field]
    block = json.dumps(arr, ensure_ascii=False, separators=(",", ":"))
    json.loads(block)
    html = html[: m.start(1)] + block + html[m.end(1):]
    path.write_text(html, encoding="utf-8")
    print(f"  {path.name}: {before} -> {len(arr)}")


def main() -> None:
    catalog_path = ROOT / "data" / "phones.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    merged, keep = merge(catalog)
    catalog_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"PASS: catalog {len(catalog)} -> {len(merged)}; kept {KEEP}")
    for name in ("index.html", "phone-compare-demo.html"):
        patch_html(ROOT / name, keep)


if __name__ == "__main__":
    main()
