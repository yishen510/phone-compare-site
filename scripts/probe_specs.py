#!/usr/bin/env python3
"""用本地无头浏览器渲染官方规格页，只打印关键字段命中行。

用法：python probe_specs.py <url>
输出控制在 30 行内，便于人工核对后写入 fieldAudit。
"""
from __future__ import annotations

import re
import sys

from playwright.sync_api import sync_playwright

PATTERNS = [
    ("屏幕", r"\d+(?:\.\d+)?\s*英寸[^。；\n]{0,40}"),
    ("刷新率", r"[^\s]{0,12}\d{2,3}\s*Hz[^。；\n]{0,20}"),
    ("电池", r"[^\s]{0,10}\d{3,5}\s*mAh[^。；\n]{0,20}"),
    ("充电", r"[^\s]{0,10}\d{2,3}\s*W[^。；\n]{0,20}"),
    ("重量", r"[^\s]{0,10}\d{2,3}(?:\.\d+)?\s*(?:g|克)[^。；\n]{0,10}"),
    ("存储", r"\d{1,2}\s*GB\s*[+＋]\s*\d{2,4}\s*GB"),
    ("芯片", r"(骁龙|天玑|麒麟|Exynos|Dimensity|Snapdragon|A1[5-9]|A2\d)[^。；\n]{0,30}"),
]


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: probe_specs.py <url>")
    url = sys.argv[1]
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1200},
                                locale="zh-CN", user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"))
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(3500)
        text = page.inner_text("body")
        title = page.title()
        browser.close()

    text = re.sub(r"[ \t]+", " ", text)
    print("TITLE:", title[:90])
    print("LEN:", len(text))
    # 标签行：规格表常见“重量 199 g / 电池容量 4000 mAh”写法
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines() if ln.strip()]
    # --block KEY N：打印包含 KEY 的行起连续 N 行（用于表格式规格页）
    if "--block" in sys.argv:
        i = sys.argv.index("--block")
        key = sys.argv[i + 1]
        n = int(sys.argv[i + 2]) if len(sys.argv) > i + 2 else 8
        for idx, ln in enumerate(lines):
            if key in ln:
                print("BLOCK:", " | ".join(lines[idx:idx + n]))
                break
    for kw in ("重量", "电池容量", "处理器", "CPU", "充电", "内存", "存储"):
        picked = [ln[:90] for ln in lines if kw in ln][:2]
        if picked:
            print(f"<{kw}>", " || ".join(picked))

    for name, pat in PATTERNS:
        hits, seen = [], set()
        for m in re.finditer(pat, text):
            frag = re.sub(r"\s+", " ", m.group(0)).strip()
            key = frag[:31]
            if key in seen:
                continue
            seen.add(key)
            hits.append(frag)
            if len(hits) >= 4:
                break
        if hits:
            print(f"[{name}]", " || ".join(hits))


if __name__ == "__main__":
    main()
