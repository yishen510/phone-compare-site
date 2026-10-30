#!/usr/bin/env python3
"""批量补录「参数站无参考价」的机型（_jst/pending_models.json 驱动）。

价格口径分两种，按上市时间区分，避免把停产老机说成「厂商未公布」：
- 上市 ≤ 12 个月：priceType=price_pending，文案「厂商与参数站均未公布参考价」；
- 上市 > 12 个月：priceType=price_unavailable，文案「参数站已无参考价（该机已下架）」。

用法：python scripts/add_pending_batch.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from add_new_models import build  # noqa: E402
from import_zol_params import patch_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
ROWS = ROOT / "_jst" / "pending_models.json"
TODAY = date(2026, 10, 29)

BRAND_EN = {
    "小米": "Xiaomi", "红米": "Xiaomi", "华为": "Huawei", "荣耀": "Honor",
    "OPPO": "OPPO", "vivo": "vivo", "iQOO": "iQOO", "真我": "realme",
    "一加": "OnePlus", "三星": "Samsung", "努比亚": "nubia", "魅族": "MEIZU",
    "苹果": "Apple", "Moto": "Motorola", "WIKO": "WIKO", "金立": "Gionee",
    "中兴": "ZTE", "华硕": "ASUS", "酷派": "Coolpad", "蔚来": "NIO",
    "麦芒": "Maimang", "Polestar": "Polestar", "亮见": "亮见",
}
# 名称前缀：跟站内各品牌既有写法对齐
BRAND_PREFIX = {
    "小米": "小米 ", "红米": "REDMI ", "华为": "HUAWEI ", "荣耀": "荣耀 ",
    "OPPO": "OPPO ", "vivo": "vivo ", "iQOO": "iQOO ", "真我": "真我 ",
    "一加": "一加 ", "三星": "", "努比亚": "", "魅族": "魅族 ",
    "苹果": "", "Moto": "Moto ", "WIKO": "WIKO ", "金立": "金立 ",
    "中兴": "中兴 ", "华硕": "", "酷派": "酷派 ", "蔚来": "蔚来 ",
    "麦芒": "麦芒 ", "Polestar": "Polestar ",
}
SLUG_BRAND = {
    "Xiaomi": "xiaomi", "Huawei": "huawei", "Honor": "honor", "OPPO": "oppo",
    "vivo": "vivo", "iQOO": "iqoo", "realme": "realme", "OnePlus": "oneplus",
    "Samsung": "samsung", "nubia": "nubia", "MEIZU": "meizu", "Apple": "apple",
    "Motorola": "moto", "WIKO": "wiko", "Gionee": "gionee", "ZTE": "zte",
    "ASUS": "asus", "Coolpad": "coolpad", "NIO": "nio", "Maimang": "maimang",
    "Polestar": "polestar",
}

CN_NUM = {"畅享": "changxiang", "畅玩": "changwan", "超级版": "super", "至尊版": "ultra",
          "元气版": "yuanqi", "活力版": "huoli", "定制版": "custom", "天通版": "tiantong",
          "哈利·波特版": "harrypotter", "至臻版": "ultimate", "典藏版": "collector",
          "保时捷设计": "porsche", "摄影师版": "photographer", "竞速版": "racing",
          "限定版": "limited", "远航": "yuanhang", "小牛": "xiaoniu"}


def norm_name(brand_cn: str, model: str) -> str:
    """按站内风格拼出完整机型名：补数字前空格、修正大小写、加品牌前缀。"""
    m = model.strip()
    m = re.sub(r"([\u4e00-\u9fa5])(?=\d)", r"\1 ", m)      # 远航41S -> 远航 41S
    m = re.sub(r"(?<=\d)([\u4e00-\u9fa5])", r" \1", m)      # 15定制版 -> 15 定制版
    m = re.sub(r"\s+", " ", m).strip()
    # 常见大小写修正
    m = re.sub(r"\brazr\b", "razr", m, flags=re.I)
    m = re.sub(r"\brzar\b", "razr", m, flags=re.I)
    if brand_cn == "华硕" and not m.upper().startswith("ROG"):
        m = re.sub(r"^游戏手机", "ROG 游戏手机", m)
    if brand_cn == "Moto":
        m = re.sub(r"\bpro\b", "Pro", m, flags=re.I)
        m = re.sub(r"\brazr\b", "razr", m, flags=re.I)
        m = re.sub(r"\bRazr\b", "razr", m)
    pre = BRAND_PREFIX.get(brand_cn, "")
    if brand_cn == "华硕" and not m.upper().startswith("ROG"):
        pre = "华硕 "          # Zenfone 要带品牌，ROG 本身已是产品线名
    return (pre + m).strip()


def classify(brand_cn: str, model: str) -> str:
    m = model
    if re.search(r"(Fold|Flip|razr|Razr|Magic ?V\d|Magic ?Vs|Mate ?X|Pocket)", m, re.I):
        return "折叠屏旗舰"
    if re.search(r"(ROG|游戏手机|红魔)", m):
        return "游戏性能旗舰"
    if re.search(r"(RSR|至臻|保时捷|非凡大师|典藏)", m):
        return "影像旗舰"
    # 明确的高端线
    if re.search(r"(Mate ?\d|Magic\d|Pura|Find X|Axon 60 Ultra|X50 Ultra|Zenfone 11 Ultra|iPhone)", m):
        return "全能旗舰"
    if brand_cn == "小米" and re.match(r"^1\d\b", m):
        return "全能旗舰"
    if re.search(r"(GT\d|Ace ?\d)", m):
        return "中端全能"
    if re.search(r"(S\d{2}\b|Reno|Civi|nova|S\d{2}[a-z]|Ultra|Pro\+)", m, re.I):
        return "中端影像"
    if brand_cn == "真我" and re.match(r"^1\d\b", m):
        return "中端影像"
    if re.search(r"(Y\d|A\d|Z\d|X\d{2}|\d{2}C\b|Note|畅享|畅玩|Play|Power|远航|V\d{2}|M\d{2,})", m):
        return "中端续航"
    return "中端全能"


BEST_FOR = {
    "折叠屏旗舰": ["大屏办公", "拍照视频", "日常全能"],
    "游戏性能旗舰": ["游戏性能", "续航"],
    "影像旗舰": ["拍照视频", "日常全能"],
    "全能旗舰": ["日常全能", "拍照视频", "续航"],
    "中端影像": ["拍照视频", "日常全能"],
    "中端续航": ["续航", "日常全能"],
    "中端全能": ["游戏性能", "日常全能", "续航"],
}


PREFIX_STRIP = re.compile(
    r"^(HUAWEI|小米|REDMI|OPPO|vivo|iQOO|真我|一加|荣耀|魅族|Moto|WIKO|金立|中兴|酷派|蔚来|麦芒|Polestar)\s*",
    re.I)


def make_slug(brand_en: str, name: str, pid: str) -> str:
    body = PREFIX_STRIP.sub("", name)
    for cn, en in CN_NUM.items():
        body = body.replace(cn, en)
    body = re.sub(r"[^a-zA-Z0-9]+", "-", body).strip("-").lower()
    if not body:
        body = f"m{pid}"
    return f"{SLUG_BRAND.get(brand_en, brand_en.lower())}-{body}"


def month_of(d: str):
    m = re.search(r"(20\d{2})(?:\D{0,2}(\d{1,2}))?", d or "")
    if not m:
        return 2026, 1
    return int(m.group(1)), int(m.group(2) or 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = json.loads(ROWS.read_text(encoding="utf-8"))
    catalog: list[dict] = json.loads(CATALOG.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in catalog}
    by_name = {re.sub(r"\s+", "", p["name"]).lower() for p in catalog}

    added = 0
    skipped = []
    for r in rows:
        brand_cn = r["brand"]
        if brand_cn not in BRAND_EN:
            skipped.append((r["model"], f"未登记品牌 {brand_cn}"))
            continue
        brand_en = BRAND_EN[brand_cn]
        name = norm_name(brand_cn, r["model"])
        if re.sub(r"\s+", "", name).lower() in by_name:
            skipped.append((name, "站内已有同名"))
            continue
        pid = r["pids"][0]
        series = r["series"] or "0"
        year, month = month_of(r["date"])
        if r["year"]:
            year = int(r["year"])
        slug = make_slug(brand_en, name, pid)
        if slug in by_id:
            slug = f"{slug}-std"
        if slug in by_id:
            slug = f"{slug}-{pid[-4:]}"
        t = classify(brand_cn, r["model"])
        skus = [s for s in r["skus"] if re.match(r"^\d+(GB|TB)(\+\d+(GB|TB))?$", s)]
        skus.sort(key=lambda s: (int(re.search(r"^(\d+)", s).group(1)),
                                 int((re.search(r"\+(\d+)", s) or re.match(r"$", "")).group(1))
                                 if re.search(r"\+(\d+)", s) else 0))
        recent = (TODAY.year - year) * 12 + (TODAY.month - month) <= 12
        price_type = "price_pending" if recent else "price_unavailable"
        if recent:
            price_text = "厂商与参数站均未公布参考价，价格待核（该机上市不足一年，可能尚未开售）"
            price_src_name = "中关村在线参数页（未列出电商报价）"
        else:
            price_text = "中关村在线未提供该机参考价，本站不臆造价格，标注为参考价缺失"
            price_src_name = "中关村在线参数页（未提供参考价）"
        base = skus[0] if skus else "以在售版本为准"
        # 参数站有的只给年份（如「2025年>」），这种不要编造月份
        raw_date = r["date"] or ""
        dm = re.search(r"(20\d{2})\D{0,3}(\d{1,2})\D{0,3}(\d{1,2})?", raw_date)
        has_month = "月" in raw_date or bool(re.search(r"20\d{2}-\d{1,2}", raw_date))
        if has_month and dm:
            disp = f"{year}年{int(dm.group(2) or 1):02d}月" + (f"{int(dm.group(3)):02d}日" if dm.group(3) else "")
        else:
            disp = f"{year}年"
        meta = {
            "id": slug, "brand": brand_en, "name": name, "type": t,
            "launchMonth": f"{year}-{month:02d}",
            "launchDateDisplay": disp,
            "priceCN": None, "priceType": price_type, "priceText": price_text,
            "priceSource": f"https://detail.zol.com.cn/{series}/{pid}/param.shtml",
            "priceSourceName": price_src_name,
            "announcementSource": f"https://detail.zol.com.cn/{series}/{pid}/param.shtml",
            "selling": f"{t}，{year} 年 {month} 月上市；参数见详情，价格待补",
            "bestFor": BEST_FOR[t],
            "storageOptions": skus or ["以在售版本为准"],
            "quoteTargetStorage": base,
            "zol": (series, pid),
            "year": year,
            "notes": [
                f"该机上市于 {year} 年 {month} 月，参数取自中关村在线参数页；"
                f"参数站未提供电商报价，本站不臆造价格，价格列为「待补」。",
                "价格口径说明：" + price_text,
            ],
        }
        if args.dry_run:
            print(f"[dry] {name:<28} {t:<8} {price_type:<17} {year}-{month:02d} {len(skus)}款 → {slug}")
            continue
        rec = build(meta)
        catalog.append(rec)
        by_id[slug] = rec
        by_name.add(re.sub(r"\s+", "", name).lower())
        added += 1
        print(f"added {slug}: {name} | {t} | {price_type} | {year}-{month:02d} | {rec['specFieldCount']} specs")

    for n, why in skipped:
        print(f"skip  {n}: {why}")
    if args.dry_run:
        print(f"\n[dry] 将新增 {len(rows) - len(skipped)} 台，跳过 {len(skipped)} 台")
        return
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    back = json.loads(CATALOG.read_text(encoding="utf-8"))
    print(f"added {added}, catalog now {len(back)} records")
    for f in (ROOT / "index.html", ROOT / "phone-compare-demo.html"):
        patch_html(f, back, strict=False)


if __name__ == "__main__":
    main()
