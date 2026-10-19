#!/usr/bin/env python3
"""通过 Bing 定位中关村在线机型页，并抓取参数页关键字段。

输出：.workbuddy/tmp/secondary.json（id -> {url,title,fields}）
stdout 只打印紧凑结果，便于人工复核。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".workbuddy" / "tmp" / "secondary.json"


def pick_link(page, keyword: str) -> str | None:
    page.goto("https://cn.bing.com/search?q=" + keyword.replace(" ", "+") + "+site%3Awap.zol.com.cn",
              wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(1500)
    links = page.eval_on_selector_all("a", "els=>els.map(e=>e.href)")
    for href in links:
        if "wap.zol.com.cn" in href and re.search(r"/\d{4}/\d+", href):
            return href.split("?")[0]
    return None


def extract(page) -> dict:
    text = page.inner_text("body")
    text = re.sub(r"[ \t]+", " ", text)
    patterns = {
        "screen": r"屏幕尺寸\s*\|?\s*(\d+(?:\.\d+)?)\s*英寸",
        "refresh": r"屏幕刷新率\s*\|?\s*(\d{2,3}Hz(?:[^|\n]{0,10})?)",
        "chip": r"CPU型号\s*\|?\s*([A-Za-z0-9\u4e00-\u9fa5+®\s]{2,24})",
        "battery": r"电池容量\s*\|?\s*(\d{3,5}mAh)",
        "charge": r"有线充电\s*\|?\s*(\d{2,3}w)",
        "weight": r"重量\s*\|?\s*(\d{2,3}g)",
        "storage": r"ROM容量\s*\|?\s*([0-9A-Za-z+；;、\s]{3,40})",
        "camera": r"像素\s*\|?\s*([^|\n]{0,90})",
    }
    out = {}
    for k, pat in patterns.items():
        m = re.search(pat, text, re.I)
        if m:
            out[k] = re.sub(r"\s+", " ", m.group(1)).strip()[:80]
    return out


def main() -> None:
    targets = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    result = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1200}, locale="zh-CN")
        for item in targets:
            pid, kw = item["id"], item["keyword"]
            try:
                url = pick_link(page, kw)
                if not url:
                    print(f"{pid}\tNO_LINK")
                    continue
                page.goto(url, wait_until="domcontentloaded", timeout=40000)
                page.wait_for_timeout(1500)
                title = page.title()
                fields = extract(page)
                result[pid] = {"url": url, "title": title[:50], "fields": fields}
                vals = [fields.get(k, "-") for k in ("screen", "refresh", "chip", "battery", "weight", "storage", "charge")]
                print(pid + "\t" + "\t".join(vals))
            except Exception as exc:  # noqa: BLE001
                print(f"{pid}\tFAIL\t{str(exc)[:50]}")
        browser.close()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
