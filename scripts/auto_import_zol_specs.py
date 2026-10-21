#!/usr/bin/env python3
"""自动解析中关村在线参数页并批量补录完整参数（无链接机型）。

流程：机型名 → ZOL 搜索 → 候选 param 链接 → 抓参数页标题严格比对 → 解析分组参数 → 写库。

匹配规则（宁可漏，不可错）：
- 归一化：小写、去空格/括号容量、`+`→`plus`、去品牌别名与 5G/全网通 等噪声；
- 把 Ultra/Pro/ProMax/Max/Plus/Mini/FE/SE/Lite/Air/Edge/Turbo 等qualifier 从名字里剥离，
  目标与候选的 qualifier 集合必须完全一致（防止 S24 命中 S24+、K80 命中 K80 Pro）；
- 品牌归一为中文别名后同样剥离，避免 HUAWEI/华为 写法差异；
- 基名要求互相包含且长度 ≥3。

用法：
  python scripts/auto_import_zol_specs.py --dry --limit 10   # 只报告，不写库
  python scripts/auto_import_zol_specs.py                    # 全量写入
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_zol_params import clean, fetch, parse_specs, patch_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
REPORT = ROOT / "reports" / "zol_auto_import_2026-10-21.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126",
      "Accept-Language": "zh-CN"}

BRAND_ALIAS = {
    "huawei": ["huawei", "华为"], "samsung": ["samsung", "三星"],
    "xiaomi": ["xiaomi", "小米", "redmi", "红米"], "redmi": ["redmi", "红米", "xiaomi", "小米"],
    "honor": ["honor", "荣耀"], "oneplus": ["oneplus", "一加"],
    "iqoo": ["iqoo"], "realme": ["realme", "真我"], "nubia": ["nubia", "努比亚"],
    "oppo": ["oppo"], "vivo": ["vivo"], "apple": ["apple", "苹果"],
}
BRAND_CN = {"huawei": "华为", "samsung": "三星", "xiaomi": "小米", "redmi": "红米",
            "honor": "荣耀", "oneplus": "一加", "iqoo": "iQOO", "realme": "真我",
            "nubia": "努比亚", "oppo": "OPPO", "vivo": "vivo", "apple": "苹果"}
QUALIFIERS = ["promax", "proplus", "pro", "ultra", "plus", "max", "mini", "fe", "se",
              "lite", "air", "edge", "turbo", "rs"]
NOISE = ["5g版", "4g版", "全网通", "5g", "4g", "双卡", "国行"]


def norm(s: str) -> str:
    s = str(s or "").lower().replace("＋", "+")
    s = re.sub(r"\(.*?\)|（.*?）", " ", s)
    # 容量必须先于 "+"→"plus" 处理，否则 12GB+512GB 会被误判成 Plus 后缀
    s = re.sub(r"\d+\s*(?:gb|tb)\s*[/+]\s*\d+\s*(?:gb|tb)", " ", s)
    s = re.sub(r"\d+\s*(?:gb|tb)", " ", s)
    s = s.replace("+", "plus")
    s = re.sub(r"[^0-9a-z\u4e00-\u9fa5]", "", s)
    return s


def strip_brand(s: str, brand: str) -> str:
    for alias in BRAND_ALIAS.get(str(brand).lower(), [str(brand).lower()]):
        s = s.replace(alias, "")
    return s


def split_qual(s: str) -> tuple[str, set[str]]:
    found: set[str] = set()
    for q in QUALIFIERS:
        if q in s:
            found.add(q)
            s = s.replace(q, "")
    return s, found


def key_of(name: str, brand: str) -> tuple[str, set[str]]:
    s = norm(name)
    for n in NOISE:
        s = s.replace(n, "")
    s = strip_brand(s, brand)
    return split_qual(s)


def title_of(h: str) -> str:
    m = re.search(r"<title>(.*?)</title>", h, re.S)
    return clean(m.group(1)) if m else ""


NON_PHONE = ["耳机", "移动电源", "充电宝", "笔记本", "平板", "手表", "手环", "路由", "音箱",
             "相机", "键盘", "鼠标", "显示器", "电视", "投影", "吸尘器", "超极本"]


def is_phone_page(title: str) -> bool:
    if "手机" not in title:
        return False
    return not any(w in title for w in NON_PHONE)


def in_base(base: str, cbase: str) -> bool:
    """短型号（如 15、13、70）用数字边界判定，长型号直接包含。"""
    if not base or not cbase:
        return False
    if len(base) >= 3:
        return base in cbase or cbase in base
    left = r"(?<!\d)" if base[0].isdigit() else ""
    right = r"(?!\d)" if base[-1].isdigit() else ""
    return re.search(left + re.escape(base) + right, cbase) is not None


def queries(p: dict) -> list[str]:
    name = p["name"]
    cn = BRAND_CN.get(str(p["brand"]).lower(), "")
    bare = name
    for alias in BRAND_ALIAS.get(str(p["brand"]).lower(), []):
        bare = re.sub(re.escape(alias), "", bare, flags=re.I)
    bare = bare.strip()
    bare_ns = re.sub(r"\s+", "", bare)
    nospace = re.sub(r"\s+", "", name)
    out = [f"{name} 参数"]
    if nospace != name:
        out.append(f"{nospace} 参数")
    if cn and bare_ns:
        out.append(f"{cn}{bare_ns} 参数")
    # 带容量能区分 Pro / Pro+ / Max 等同系列变体
    storage = re.sub(r"\s+", " ", str(p.get("quoteTargetStorage") or "").replace("+", " ")).strip()
    if storage:
        out.append(f"{name} {storage} 参数")
        out.append(f"{name} {storage}")
    out += [name, nospace]
    return list(dict.fromkeys(out))


def brand_ok(title: str, brand: str) -> bool:
    """候选页标题必须出现目标品牌的任一别名，防止「小米14 Pro」命中「iPhone 14 Pro」。"""
    t = norm(title)
    aliases = BRAND_ALIAS.get(str(brand).lower(), [str(brand).lower()])
    return any(norm(a) and norm(a) in t for a in aliases)


def bing_links(name: str) -> list[str]:
    """站内搜索缺失时，用 Bing 找 wap.zol.com.cn 页面，再映射成 detail 参数页。"""
    url = "https://cn.bing.com/search?q=" + urllib.parse.quote(f"{name} 参数 site:wap.zol.com.cn")
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read()
    except Exception:  # noqa: BLE001
        return []
    h = raw.decode("utf-8", "ignore")
    pairs = re.findall(r"(?:detail|wap)\.zol\.com\.cn[/\\\"]*(\d+)/(\d+)", h)
    out = [f"https://detail.zol.com.cn/{a}/{b}/param.shtml" for a, b in dict.fromkeys(pairs)]
    return out[:4]


def so360_links(name: str, storage: str = "") -> list[str]:
    """360 搜索兜底：中文机型命中率高于 Bing；带容量可区分同系列变体。"""
    qs = []
    if storage:
        qs.append(f"{name} {storage} 参数 中关村在线")
    qs.append(f"{name} 参数 中关村在线")
    pairs: list[tuple[str, str]] = []
    for q in qs:
        url = "https://www.so.com/s?q=" + urllib.parse.quote(q)
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read()
        except Exception:  # noqa: BLE001
            continue
        h = raw.decode("utf-8", "ignore")
        pairs += re.findall(r"detail\.zol\.com\.cn[/\\\"]*(\d+)/(\d+)", h)
        pairs += re.findall(r"wap\.zol\.com\.cn[/\\\"]*(\d+)/(\d+)", h)
        if len(dict.fromkeys(pairs)) >= 4:
            break
    return [f"https://detail.zol.com.cn/{a}/{b}/param.shtml" for a, b in dict.fromkeys(pairs)][:6]


def search_links(kw: str) -> list[str]:
    url = "https://search.zol.com.cn/s/all.php?kword=" + urllib.parse.quote(kw)
    try:
        h = fetch(url)
    except Exception:  # noqa: BLE001
        return []
    links = re.findall(r'href="(//detail\.zol\.com\.cn/\d+/\d+/param\.shtml)"', h)
    if not links:  # 搜索结果可能只给商品页，转成参数页
        pairs = re.findall(r'detail\.zol\.com\.cn/(\d+)/(\d+)/', h)
        links = [f"//detail.zol.com.cn/{a}/{b}/param.shtml" for a, b in dict.fromkeys(pairs)]
    return list(dict.fromkeys("https:" + x for x in links))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="逗号分隔的机型 id，仅重抓这些")
    args = ap.parse_args()

    catalog: list[dict] = json.loads(CATALOG.read_text(encoding="utf-8"))
    only = [x.strip() for x in args.only.split(",") if x.strip()]
    targets = [p for p in catalog if not p.get("specs") and (not only or p["id"] in only)]
    if args.limit:
        targets = targets[: args.limit]
    print(f"targets without specs: {len(targets)}")

    report = {"matched": [], "rejected": [], "not_found": [], "failed": []}
    ok = 0
    used_urls: set[str] = set()
    for idx, p in enumerate(targets, 1):
        base, quals = key_of(p["name"], p["brand"])
        links: list[str] = []
        try:
            for q in queries(p):
                try:
                    got = search_links(q)
                except Exception:  # noqa: BLE001
                    got = []
                for u in got:
                    if u not in links:
                        links.append(u)
                if len(links) >= 6:
                    break
                time.sleep(0.2)
            for u in bing_links(p["name"]):
                if u not in links:
                    links.append(u)
            for u in so360_links(p["name"], str(p.get("quoteTargetStorage") or "")):
                if u not in links:
                    links.append(u)
        except Exception as exc:  # noqa: BLE001
            report["failed"].append({"id": p["id"], "name": p["name"], "err": str(exc)[:80]})
            print(f"[{idx}/{len(targets)}] FAIL {p['id']}")
            continue
        hit = None
        for link in links[:20]:
            try:
                h = fetch(link)
            except Exception:  # noqa: BLE001
                continue
            t = title_of(h)
            cbase, cquals = key_of(t, p["brand"])
            if not is_phone_page(t):
                report["rejected"].append({"id": p["id"], "name": p["name"], "title": t,
                                           "url": link, "reason": "non_phone"})
                continue
            if in_base(base, cbase) and cquals == quals and link not in used_urls and brand_ok(t, p["brand"]):
                hit = (link, t, h)
                break
            report["rejected"].append({"id": p["id"], "name": p["name"], "title": t, "url": link})
        if not hit:
            report["not_found"].append({"id": p["id"], "name": p["name"], "links": links[:3]})
            print(f"[{idx}/{len(targets)}] NONE {p['name']}")
            continue
        link, t, h = hit
        used_urls.add(link)
        specs = parse_specs(h)
        if not specs:
            report["failed"].append({"id": p["id"], "name": p["name"], "err": "empty specs", "url": link})
            print(f"[{idx}/{len(targets)}] EMPTY {p['name']}")
            continue
        n = sum(len(g["items"]) for g in specs)
        print(f"[{idx}/{len(targets)}] MATCH {p['name']} -> {t[:44]} | {len(specs)}组/{n}项")
        report["matched"].append({"id": p["id"], "name": p["name"], "title": t, "url": link,
                                  "groups": len(specs), "items": n})
        if not args.dry:
            p["specs"] = specs
            p["specSource"] = link
            p["specSourceName"] = "中关村在线参数页（第三方核验）"
            p["specFieldCount"] = n
            p["specCollectedAt"] = "2026-10-21"
            p.setdefault("auditNotes", []).append(
                f"2026-10-21 自动补录完整参数：{len(specs)} 组 / {n} 项（中关村在线，标题比对通过）")
            ok += 1
        time.sleep(0.6)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: matched={len(report['matched'])} rejected={len(report['rejected'])} "
          f"not_found={len(report['not_found'])} failed={len(report['failed'])}")

    if not args.dry:
        CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
        back = json.loads(CATALOG.read_text(encoding="utf-8"))
        print(f"saved: {len(back)} records, {sum(1 for x in back if x.get('specs'))} with specs")
        for f in [ROOT / "index.html", ROOT / "phone-compare-demo.html"]:
            patch_html(f, back)
        print(f"imported ok={ok}")


if __name__ == "__main__":
    main()
