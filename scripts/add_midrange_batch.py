#!/usr/bin/env python3
"""批量补录中端机型：数据来自 ZOL 品牌页 + 参数页，价格用 ZOL 参考报价（非首发价）。

与 add_new_models.py 的区别：
- 条目由 _jst/mid_rows.json 批量生成，不逐台手写；
- 价格统一标记为 third_party_reference，文案写明「非官方首发价」，与站内既有 59 台同口径；
- 定位（type）按机型线自动归类到 中端全能 / 中端影像 / 中端续航。

用法：python scripts/add_midrange_batch.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from add_new_models import build  # noqa: E402
from import_zol_params import patch_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
ROWS = ROOT / "_jst" / "mid_rows.json"

BRAND_MAP = {"OPPO": "OPPO", "vivo": "vivo", "华为": "Huawei", "小米": "Xiaomi",
             "红米": "Xiaomi", "荣耀": "Honor", "iQOO": "iQOO", "真我": "realme",
             "三星": "Samsung", "努比亚": "nubia", "魅族": "MEIZU"}
BRAND_PREFIX = {"OPPO": "OPPO ", "vivo": "vivo ", "华为": "HUAWEI ", "小米": "Xiaomi ", "红米": "REDMI ",
                "荣耀": "荣耀", "iQOO": "iQOO ", "真我": "真我 ", "三星": "三星", "努比亚": "努比亚", "魅族": "魅族"}

# 机型线 → 定位
IMAGE_LINES = ("S60", "Civi", "Reno", "nova", "Neo7")
BATTERY_LINES = ("Y600", "Y6", "Y60", "畅享", "Play", "畅玩", "A7", "A6s", "Note", "Z11", "Z10", "Power", "X70")
BEST_FOR = {
    "中端影像": ["拍照视频", "日常全能"],
    "中端续航": ["续航", "日常全能"],
    "中端全能": ["游戏性能", "日常全能", "续航"],
}


def classify(name: str) -> str:
    """按机型线归类：S/Reno/Civi/nova 走影像，Y/A/Z/Note/畅享/畅玩/Play/Power/X 走续航，其余算全能。"""
    n = name
    if re.search(r"(S\d{2}\b|Reno|Civi|nova)", n):
        return "中端影像"
    if re.search(r"(Y\d|A\d|Z\d|X\d{2}|\d{2}C\b|Note|畅享|畅玩|Play|Power)", n):
        return "中端续航"
    return "中端全能"


def clean_name(raw: str, brand_cn: str) -> str:
    n = raw.strip()
    for pref in (brand_cn, brand_cn + " ", "Redmi（红米）", "Redmi ", "iQOO", "真我", "realme"):
        if n.startswith(pref):
            n = n[len(pref):].strip()
    n = re.sub(r"^(OPPO|vivo|HUAWEI|Xiaomi|REDMI|荣耀|华为|小米|红米|iQOO|realme|真我)\s*", "", n)
    n = re.sub(r"\s+", " ", n)
    # 型号里的数字前后补空格：Note17 → Note 17，畅享100 → 畅享 100
    n = re.sub(r"(Note|畅享|Turbo)(\d)", r"\1 \2", n)
    return BRAND_PREFIX[brand_cn] + n


def norm_sku(s: str) -> str:
    return s.replace("/", "+").replace(" ", "")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = json.loads(ROWS.read_text(encoding="utf-8"))
    catalog: list[dict] = json.loads(CATALOG.read_text(encoding="utf-8"))
    index = {p["id"]: i for i, p in enumerate(catalog)}

    added = 0
    seen_names: set[tuple[str, str]] = set()
    rows.sort(key=lambda x: x["min"])
    for r in rows:
        name = clean_name(r["name"], r["brand"])
        name_key = (BRAND_MAP[r["brand"]], name)
        if name_key in seen_names:
            print(f"skip duplicate name: {name}")
            continue
        seen_names.add(name_key)
        t = classify(name)
        skus = [norm_sku(s) for s in r.get("skus") or []]
        skus = [s for s in skus if re.match(r"^\d+GB\+\d+(GB|TB)$", s)]
        skus.sort(key=lambda s: (int(re.search(r"(\d+)GB", s).group(1)),
                                 int(re.search(r"\+(\d+)", s).group(1))))
        base = skus[0] if skus else "以在售版本为准"
        date = r["date"].replace(" 年", "年").replace("年 ", "年")
        m = re.search(r"(20\d{2})\D*(\d{1,2})?\D*(\d{1,2})?", date)
        year = int(m.group(1)) if m else 2026
        month = int(m.group(2) or 1) if m else 1
        day = int(m.group(3) or 1) if m else 1

        # id：品牌前缀 + 去掉品牌名后的型号；中文词做简单转写，避免出现 non-ascii 或空 slug
        base_name = re.sub(r"^(HUAWEI|Xiaomi|REDMI|OPPO|vivo|iQOO|realme|荣耀|华为|小米|红米|真我)\s*", "", name)
        for cn, en in (("畅享", "changxiang"), ("畅玩", "changwan"), ("超级版", "super"),
                       ("至尊版", "ultra"), ("元气版", "yuanqi"), ("活力版", "huoli")):
            base_name = base_name.replace(cn, en)
        slug_body = re.sub(r"[^a-z0-9]+", "-", base_name.lower()).strip("-") or r["pid"]
        slug = f"{BRAND_MAP[r['brand']].lower()}-{slug_body}"
        meta = {
            "id": slug,
            "brand": BRAND_MAP[r["brand"]],
            "name": name,
            "type": t,
            "launchMonth": f"{year}-{month:02d}",
            "launchDateDisplay": f"{year}年{month:02d}月{day:02d}日",
            "priceCN": r["min"],
            "priceType": "third_party_reference",
            "priceText": f"中关村在线参考报价（非官方首发价，仅供比价参考）；{base} 版本 {r['min']} 元起",
            "priceSource": f"https://detail.zol.com.cn/{r['series']}/{r['pid']}/param.shtml",
            "priceSourceName": "中关村在线商品页参考价",
            "announcementSource": f"https://detail.zol.com.cn/{r['series']}/{r['pid']}/param.shtml",
            "selling": "中端价位机型，参数与参考报价见详情",
            "bestFor": BEST_FOR[t],
            "storageOptions": skus or ["以在售版本为准"],
            "quoteTargetStorage": base,
            "zol": (r["series"], r["pid"]),
            "year": year,
            "notes": [
                f"{year} 年 {month} 月上市；参考报价取自 ZOL 商品页（当前渠道价，非首发价），"
                f"价格区间 {r['min']}~{r['max']} 元。",
                "该机为此轮中端补录机型，价格口径为第三方参考价，未做首发价核验。",
            ],
        }
        if meta["id"] in index:
            print(f"skip existing: {meta['id']}")
            continue
        rec = build(meta)
        if args.dry_run:
            print(f"[dry] {rec['name']:<24} {rec['type']} ¥{rec['priceCN']:<5} {rec['launchMonth']} {rec['specFieldCount']}项")
            continue
        catalog.append(rec)
        added += 1
        print(f"added {rec['id']}: {rec['name']} | {rec['type']} | ¥{rec['priceCN']} | {rec['specFieldCount']} specs")

    if args.dry_run:
        return
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    back = json.loads(CATALOG.read_text(encoding="utf-8"))
    print(f"added {added}, catalog now {len(back)} records")
    for f in (ROOT / "index.html", ROOT / "phone-compare-demo.html"):
        patch_html(f, back, strict=False)


if __name__ == "__main__":
    main()
