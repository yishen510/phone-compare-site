#!/usr/bin/env python3
"""ZOL 抓取工具：带反爬 Cookie 的品牌页/参数页抓取，供批量补录用。

要点：
- 品牌页首次会返回 <meta refresh> 跳到 service.zol.com.cn/checking，访问一次即拿到 ip_ck Cookie；
- 翻页规则：subcate57_{brand}_list_1.html → subcate57_{brand}_list_1_0_1_2_0_{page}.html（page≥2）；
- 参数页 /{series}/{pid}/param.shtml 的「电商报价」可能为空，需要另一条兜底取价路径。
"""
from __future__ import annotations

import html as H
import http.cookiejar
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
BASE = "https://detail.zol.com.cn/cell_phone_index/"

_cj = http.cookiejar.CookieJar()
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj))


def get(url: str, enc: str = "gbk", tries: int = 3) -> str:
    """带 Cookie 的 GET；遇到 checking 跳转自动过验证后重试。"""
    for _ in range(tries):
        try:
            raw = _op.open(urllib.request.Request(url, headers=UA), timeout=30).read()
        except Exception:
            time.sleep(1)
            continue
        text = raw.decode(enc, "ignore")
        if "checking" in text and len(text) < 500:
            m = re.search(r"url=([^\"]+)", text)
            if m:
                try:
                    _op.open(urllib.request.Request(m.group(1), headers=UA), timeout=30).read()
                except Exception:
                    pass
            continue
        return text
    return ""


def list_brand(brand_id: str, pages: int = 3) -> list[dict]:
    """抓品牌页前 N 页，返回 [{brand_id,pid,raw}]。"""
    out: list[dict] = []
    for page in range(1, pages + 1):
        pat = (f"subcate57_{brand_id}_list_1.html" if page == 1
               else f"subcate57_{brand_id}_list_1_0_1_2_0_{page}.html")
        h = get(BASE + pat)
        for pid, title in re.findall(r'<h3><a href="/cell_phone/index(\d+)\.shtml" title="([^"]+)"', h):
            out.append({"brand_id": brand_id, "pid": pid, "raw": H.unescape(title)})
        time.sleep(0.2)
    return out


def series_of(pid: str, opener=None) -> str | None:
    h = (opener or get)(f"https://detail.zol.com.cn/cell_phone/index{pid}.shtml")
    m = re.search(r"/(\d+)/" + pid + r"/param\.shtml", h)
    return m.group(1) if m else None


def price_from_product_page(pid: str) -> int | None:
    """兜底取价：商品页里的「参考报价」/「电商报价」。"""
    h = get(f"https://detail.zol.com.cn/cell_phone/index{pid}.shtml")
    for pat in (r"参考报价[^0-9]{0,20}[￥¥]?\s*([\d,]{3,})",
                r"class=\"price[^\"]*\"[^>]*>[^0-9]{0,12}([\d,]{3,})",
                r"电商报价[^0-9]{0,20}[￥¥]?\s*([\d,]{3,})"):
        m = re.search(pat, h)
        if m:
            v = int(m.group(1).replace(",", ""))
            if 400 <= v <= 60000:
                return v
    return None


if __name__ == "__main__":
    brand = sys.argv[1]
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    rows = list_brand(brand, pages)
    print(json.dumps(rows, ensure_ascii=False))
