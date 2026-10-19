#!/usr/bin/env python3
"""批量：必应定位中关村在线参数页 → GBK 解码 → 提取关键字段。

用法：python zol_batch.py targets.json
targets: [{"id": "...", "kw": "红魔9 Pro"}]
输出：紧凑行 + .workbuddy/tmp/zol_batch.json
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
KEYS = ["屏幕尺寸", "屏幕刷新率", "CPU型号", "电池容量", "有线充电", "重量", "ROM容量"]


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def find_param_url(kw: str) -> str | None:
    q = urllib.parse.quote(f"{kw} 参数 site:detail.zol.com.cn")
    raw = get(f"https://cn.bing.com/search?q={q}").decode("utf-8", "ignore")
    urls = re.findall(r'https://detail\.zol\.com\.cn/\d+/\d+/param\.shtml', raw)
    seen = []
    for u in urls:
        if u not in seen:
            seen.append(u)
    return seen[0] if seen else None


def text_of(raw: bytes) -> tuple[str, str]:
    for enc in ("gbk", "gb18030"):
        try:
            h = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        h = raw.decode("utf-8", "ignore")
    title = re.search(r"<title>(.*?)</title>", h, re.S)
    body = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    body = html.unescape(body)
    return (title.group(1).strip() if title else ""), re.sub(r"\s+", " ", body)


def fields(body: str) -> dict:
    out = {}
    for k in KEYS:
        m = re.search(k + r"\s*([^ ]{1,28})", body)
        if m:
            v = m.group(1).strip()
            if v and not v.startswith("行业最高"):
                out[k] = v
    return out


def main() -> None:
    targets = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    delay = float(sys.argv[2]) if len(sys.argv) > 2 else 12.0
    result = {}
    for t in targets:
        pid, kw = t["id"], t["kw"]
        try:
            url = None
            for attempt in range(3):
                try:
                    url = find_param_url(kw)
                except Exception:
                    url = None
                if url:
                    break
                time.sleep(delay)
            if not url:
                print(f"{pid}\tNO_URL")
                continue
            title, body = text_of(get(url))
            f = fields(body)
            result[pid] = {"url": url, "title": title[:40], **f}
            time.sleep(delay)
            print("\t".join([pid, url.split("zol.com.cn")[1]] + [f.get(k, "-") for k in KEYS]))
        except Exception as exc:  # noqa: BLE001
            print(f"{pid}\tFAIL\t{str(exc)[:40]}")
    (ROOT / ".workbuddy" / "tmp" / "zol_batch.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
