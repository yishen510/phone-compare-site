#!/usr/bin/env python3
"""拼音首字母搜索的误召回评估（只读，不改页面）。

用法：python _jst/eval_pinyin.py
结论：startsWith（前缀）在 485 条真实数据上误召回为 0；
      includes 会因 Flip / MIX 等型号里的中间子串而跨品牌。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "index.html").read_text(encoding="utf-8")
start = html.find("window.PHONE_DATA=")
data, _ = json.JSONDecoder().raw_decode(html[start + len("window.PHONE_DATA="):])
print(f"数据条数 {len(data)}")

# 品牌前缀 → 拼音首字母（只覆盖库里实际出现的写法）
RULES = [
    (r"^小米", "xm"), (r"^红米", "hm"), (r"^REDMI", "hm"),
    (r"^三星", "sx"), (r"^华为", "hw"), (r"^HUAWEI", "hw"),
    (r"^荣耀", "ry"), (r"^vivo", "vivo"), (r"^OPPO", "oppo"), (r"^Reno", "oppo"), (r"^Find", "oppo"),
    (r"^真我", "zw"), (r"^realme", "zw"), (r"^iQOO", "iqoo"),
    (r"^努比亚", "nby"), (r"^红魔", "nby"), (r"^一加", "yj"), (r"^魅族", "mz"),
    (r"^中兴", "zx"), (r"^酷派", "kp"), (r"^华硕", "hs"), (r"^ROG", "hs"), (r"^麦芒", "mm"),
    (r"^iPhone", "pg"), (r"^苹果", "pg"), (r"^Moto", "moto"), (r"^WIKO", "wiko"),
    (r"^蔚来", "wl"), (r"^Polestar", "polestar"),
]


def pykey(p):
    n = str(p.get("name") or "")
    brand = ""
    for pat, py in RULES:
        m = re.match(pat, n, re.I)
        if m:
            brand = py
            n = n[m.end():]          # 关键：剥掉品牌前缀，否则 HUAWEI Mate 70 会变成 hwhuaweimate70
            break
    rest = re.sub(r"[^\x00-\x7F]", "", n)          # 去掉中文（中文型号字不转拼音）
    rest = re.sub(r"[^a-z0-9]", "", rest.lower())
    return (brand + rest).lower()


KEYS = [(pykey(p), p) for p in data]


def query(q, mode="prefix"):
    t = q.lower().strip()
    if len(t) < 2:
        return []
    if mode == "prefix":
        return [p for k, p in KEYS if k.startswith(t)]
    return [p for k, p in KEYS if t in k]


def report(q, mode):
    hits = query(q, mode)
    dist = {}
    for p in hits:
        dist[p["brand"]] = dist.get(p["brand"], 0) + 1
    return len(hits), dist


print("\n===== 前缀匹配（上线方案） =====")
for q in ["xm", "hw", "ry", "sx", "pg", "ip", "mi", "xm15", "hwmate", "hwmate70", "nby"]:
    n, dist = report(q, "prefix")
    hits = query(q, "prefix")
    print(f"  {q:10s} {n:3d} 条 / {len(dist)} 品牌 {dist}")
    if hits:
        print("             前3:", " / ".join(p["name"] for p in hits[:3]))

print("\n===== 对比：子串匹配（includes，未采用） =====")
for q in ["ip", "mi"]:
    n, dist = report(q, "substr")
    print(f"  {q:10s} {n:3d} 条 / {len(dist)} 品牌 {dist}  <- 跨品牌误召回")
