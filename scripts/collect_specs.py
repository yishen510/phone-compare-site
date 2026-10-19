#!/usr/bin/env python3
"""批量抓取官方规格页并抽取关键字段，输出紧凑表格供人工复核。

只输出解析到的候选值；解析不到就留空，不做任何推断。
原始页面文本缓存在 .workbuddy/tmp/specs/ 下，便于复核对证。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".workbuddy" / "tmp" / "specs"
CACHE.mkdir(parents=True, exist_ok=True)

LABELS = {
    "weight": [r"重量[^0-9]{0,14}(\d{2,3}(?:\.\d+)?)\s*(?:g|克)", r"(\d{2,3}(?:\.\d+)?)\s*(?:g|克)[^0-9]{0,8}重量"],
    "battery": [r"电池容量[^0-9]{0,18}(\d{3,5})\s*mAh", r"(\d{3,5})\s*mAh"],
    "screen": [r"(\d+\.\d+)\s*英寸", r"(\d+(?:\.\d+)?)\s*英寸"],
    "refresh": [r"(\d{2,3})\s*Hz"],
    "storage": [r"(\d{1,2})\s*GB\s*[+＋]\s*(\d{2,4})\s*GB"],
    "charge": [r"(\d{2,3})\s*W"],
    "chip": [r"(骁龙[®\s]*[0-9A-Za-z\s]{0,18})", r"(天玑\s*[0-9A-Za-z+\s]{0,12})", r"(麒麟\s*[0-9A-Za-z\s]{0,10})",
             r"(Exynos\s*[0-9A-Za-z\s]{0,10})", r"(A1[5-9](?:\s*Pro)?)", r"(A2\d(?:\s*Pro)?)"],
}


def extract(text: str) -> dict:
    out: dict[str, str] = {}
    for key, pats in LABELS.items():
        for pat in pats:
            m = re.search(pat, text)
            if m:
                out[key] = m.group(0).strip()[:60]
                break
    return out


def main() -> None:
    targets = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1200}, locale="zh-CN")
        for item in targets:
            pid, url = item["id"], item["url"]
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=40000)
                page.wait_for_timeout(2500)
                title = page.title()
                text = page.inner_text("body")
            except Exception as exc:  # noqa: BLE001
                rows.append({"id": pid, "url": url, "status": "FAIL", "note": str(exc)[:60]})
                continue
            clean = re.sub(r"[ \t]+", " ", text)
            (CACHE / f"{pid}.txt").write_text(clean, encoding="utf-8")
            data = extract(clean)
            rows.append({"id": pid, "url": url, "status": "OK", "title": title[:40], **data})
        browser.close()

    for r in rows:
        if r["status"] != "OK":
            print(f"{r['id']}\tFAIL\t{r['note']}")
            continue
        print("\t".join([
            r["id"], r.get("screen", "-"), r.get("refresh", "-"), r.get("chip", "-"),
            r.get("battery", "-"), r.get("weight", "-"), r.get("storage", "-"), r.get("charge", "-"),
        ]))


if __name__ == "__main__":
    main()
