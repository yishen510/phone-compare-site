# -*- coding: utf-8 -*-
"""2026-10-20：为 2024—2026 年机型回填官方首发价（含容量 SKU 映射与来源）。

规则（见 AUDIT_POLICY.md「首发价规则」）：
- 有「中国大陆版 + 具体容量组合 + 可追溯发布稿/官方 MSRP 页」，写 priceCN，
  priceType=official_launch_msrp。
- 只有「XX 元起」而没有容量映射，仍写 priceCN 以便前端展示，但
  priceType=official_starting_price（卡片标签显示「官方起售价（容量待核）」），
  fieldAudit 状态为 starting_price_only_sku_mapping_unverified。
- 权威媒体对发布会现场公布价格的报道，按 cross_checked_secondary_source 记账，
  不冒充官方页核验。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "phones.json"
HTMLS = [ROOT / "index.html", ROOT / "phone-compare-demo.html"]

V_OFFICIAL = "verified_official_page_reviewed"
V_SECONDARY = "cross_checked_secondary_source"
V_START_ONLY = "starting_price_only_sku_mapping_unverified"

FIELD = "官方首发起售价"
TAG = "2026-10-20 回填官方首发价"

MEDIA_XIAOMI = "央广网、证券时报、中国日报网对 2024-10-29 小米发布会的报道（三家价格一致）"

P = {
    # ---------- 小米 ----------
    "xia-15": dict(
        price=4499, sku="12GB+256GB", status=V_SECONDARY,
        url="https://www.cnr.cn/tech/techph/20241030/t20241030_526958166.shtml",
        name=MEDIA_XIAOMI,
        ev="发布会现场公布小米 15 12GB+256GB 售价 4499 元起；亮银版同容量 4699 元；定制版 16GB+512GB 4999 元；钻石限定版 16GB+1TB 5999 元。",
    ),
    "xia-15p": dict(
        price=5299, sku="12GB+256GB", status=V_SECONDARY,
        url="https://www.cnr.cn/tech/techph/20241030/t20241030_526958166.shtml",
        name=MEDIA_XIAOMI,
        ev="发布会现场公布小米 15 Pro 12GB+256GB 售价 5299 元起；16GB+512GB 5799 元；16GB+1TB 6499 元；亮银版同容量 5499 元。",
    ),
    "xia-15sp": dict(
        price=5499, sku="16GB+512GB", status=V_SECONDARY,
        url="https://baike.baidu.com/starmap/view?lemmaId=64636516",
        name="小米 15 周年发布会售价（百度百科条目转述，另经太平洋科技、中关村在线同价印证）",
        ev="2025-05-22 小米 15 周年战略新品发布会公布：16GB+512GB 售价 5499 元，16GB+1TB 售价 5999 元；该机不提供 256GB 版本。",
    ),
    "xia-mixflip2": dict(
        price=5999, sku=None, status=V_START_ONLY,
        url="https://g.pconline.com.cn/product/note/57022.html",
        name="太平洋科技产品对比（标注官方价 5999 元）",
        ev="太平洋科技注明 Xiaomi MIX Flip 2 官方价 5999 元，为全系最低价；官方未在发布稿中逐字给出 5999 元对应的容量组合。另有 2025-08-22 钻石限定版 12GB+512GB 6999 元的独立 SKU。",
    ),
    # ---------- 华为 ----------
    "hua-pura80": dict(
        price=4699, sku="12GB+256GB", status=V_OFFICIAL,
        url="https://consumer.huawei.com/cn/press/events/2025/huawei-pura-80-series-and-new-product-launch-event/",
        name="华为官网 Pura 80 系列及全场景新品发布会页面",
        ev="华为官网发布会页把 Pura 80 标注为「￥4699 起」；官方同时公布 12GB+256GB 4699 元、12GB+512GB 5199 元、12GB+1TB 6199 元，2025-07-30 开售。",
    ),
    "hua-pura80pp": dict(
        price=7999, sku=None, status=V_START_ONLY,
        url="https://www.cnstock.com/commonDetail/452687",
        name="上海证券报·中国证券网对 2025-06-11 华为发布会的报道",
        ev="发布会公布 HUAWEI Pura 80 Pro+ 建议零售价 7999 元起，2025-06-14 开售；官方稿未给出 7999 元对应的容量组合。注：2025-07 中旬该机曾限时降价至 7199 元起，属促销价，不计入首发价。",
    ),
    "hua-mate80p": dict(
        price=5999, sku="12GB+256GB", status=V_SECONDARY,
        url="https://www.cnstock.com/commonDetail/593079",
        name="中国证券网、上海市黄浦区政府新闻、无锡市科技局简报对 2025-11-25 华为发布会的报道（三家一致）",
        ev="发布会公布 HUAWEI Mate 80 Pro 售价 5999 元起，11 月 28 日开售；中关村在线参数页 12GB+256GB 亦标 5999 元。⚠ 华为官网发布会页当前标注「￥6999 起」，与发布当时媒体报道相差 1000 元，疑为 2026 年存储涨价后的调价或高配版本起售，SKU 归属待复核。",
    ),
    # ---------- 荣耀 ----------
    "honor-magic9pm": dict(
        price=6499, sku=None, status=V_START_ONLY,
        url="https://www.honor.com/cn/news/honor-magic9-launch/",
        name="荣耀官网 Magic9 系列发布稿",
        ev="官方发布稿写明荣耀 Magic9 Pro Max 售价 6499 元起，2026-09-28 开售；未逐档列出容量与价格对应关系。",
    ),
    "honor-magic9-ultra": dict(
        price=4499, sku=None, status=V_START_ONLY,
        url="https://www.honor.com/cn/news/honor-magic9-launch/",
        name="荣耀官网 Magic9 系列发布稿",
        ev="官方发布稿写明荣耀 Magic9 超能版售价 4499 元起，2026-09-28 开售；未逐档列出容量与价格对应关系。",
    ),
    # ---------- OPPO ----------
    "oppo-x8s": dict(
        price=4199, sku="12GB+256GB", status=V_SECONDARY,
        url="https://www.ce.cn/cysc/tech/gd2012/202504/11/t20250411_39342322.shtml",
        name="中国经济网、深圳新闻网对 2025-04-10 OPPO Find X8 系列发布会的报道（价格一致）",
        ev="官方公布 Find X8s 12GB+256GB 零售价 4199 元（国补后 3699 元），2025-04-16 开售。",
    ),
    "oppo-x8sp": dict(
        price=4199, sku="12GB+256GB", status=V_SECONDARY,
        url="https://www.ce.cn/cysc/tech/gd2012/202504/11/t20250411_39342322.shtml",
        name="中国经济网、深圳新闻网对 2025-04-10 OPPO Find X8 系列发布会的报道（价格一致）",
        ev="官方公布 Find X8s+ 12GB+256GB 零售价 4199 元（国补后 3699 元），2025-04-16 开售。",
    ),
    "oppo-n5": dict(
        price=8999, sku="12GB+256GB", status=V_SECONDARY,
        url="https://www.news.cn/tech/20250221/69257f8169f74d2f8c0a23acc3d2b1ab/c.html",
        name="新华网、央广网、中国青年网、海外网对 2025-02-20 OPPO 发布会的报道（价格一致）",
        ev="官方公布 Find N5 12GB+256GB 8999 元、16GB+512GB 9999 元、16GB+1TB 卫星通信版 10999 元，2025-02-26 开售。",
    ),
    "oppo-x10": dict(
        price=5499, sku="12GB+256GB", status=V_SECONDARY,
        url="https://www.ce.cn/cysc/tech/gd2012/202609/t20260924_3234942.shtml",
        name="中国经济网、人民政协网、河北青年报对 2026-09-22 OPPO Find X10 发布会的报道（价格一致）",
        ev="官方公布 Find X10 四档售价：12GB+256GB 5499 元、12GB+512GB 5999 元、16GB+512GB 6499 元、16GB+1TB 7499 元，2026-09-24 开售。",
    ),
    "oppo-x9u": dict(
        price=7499, sku="12GB+256GB", status=V_SECONDARY,
        url="https://www.sina.cn/gc/article/niuwqpv5509071.html",
        name="新浪网多篇价格梳理（列出发布会公布的五档官方价）",
        ev="2026-04-21 发布会公布 Find X9 Ultra 12GB+256GB 7499 元、12GB+512GB 7999 元、16GB+512GB 8499 元、16GB+1TB 9299 元、16GB+1TB 卫星通信版 9499 元；OPPO 商城 16GB+512GB 当前标价 8499 元与该表一致。",
    ),
    # ---------- 一加 / iQOO / vivo ----------
    "op-13t": dict(
        price=3399, sku=None, status=V_START_ONLY,
        url="https://www3.xinhuanet.com/tech/20250427/651ea66255d74c1b8b2a8ee12fa781c4/c.html",
        name="新华网、中国新闻网上海对 2025-04-24 一加 13T 发布会的报道",
        ev="官方公布一加 13T 起售价 3399 元（国补到手 2899 元起），2025-04-30 开售；稿件未逐字说明 3399 元对应的容量组合，官方规格序列为 12GB+256GB 起。",
    ),
    "iqoo-15": dict(
        price=4199, sku="12GB+256GB", status=V_SECONDARY,
        url="https://www.news.cn/tech/20251021/b6092f5573bf404fb0efdc73acb708d9/c.html",
        name="新华网等对 iQOO 15 发布会的报道（五档价格一致）",
        ev="官方公布 iQOO 15 五档售价：12GB+256GB 4199 元、16GB+256GB 4499 元、12GB+512GB 4699 元、16GB+512GB 4999 元、16GB+1TB 5499 元。",
    ),
    "iqoo-13": dict(
        price=3999, sku="12GB+256GB", status=V_OFFICIAL,
        url="https://www.vivo.com.cn/vivo/param/iqoo13",
        name="vivo 官网 iQOO 13 规格参数页（建议零售价）",
        ev="vivo 官网参数页给出建议零售价：12GB+256GB 3999 元、12GB+512GB 4499 元、16GB+256GB 4299 元、16GB+512GB 4699 元、16GB+1TB 5199 元，与中国新闻网对 2024-10-30 发布会的报道完全一致。",
    ),
    "vivo-x500": dict(
        price=5499, sku="12GB+256GB", status=V_OFFICIAL,
        url="https://www.vivo.com.cn/vivo/param/x500",
        name="vivo 官网 X500 规格参数页（建议零售价）",
        ev="vivo 官网参数页给出建议零售价：12GB+256GB 5499 元、12GB+512GB 5999 元、12GB+1TB 6999 元；发布会公布 X500 5499 元起、2026-09-24 开售，与之吻合。",
    ),
    # ---------- 三星 ----------
    "sam-26p": dict(
        price=7999, sku="12GB+256GB", status=V_SECONDARY,
        url="https://t.cj.sina.com.cn/articles/view/7879777290/1d5abdc0a06802kfs6",
        name="新浪财经头条（列出 S26 系列首发价与 2026-10 调价后对比）",
        ev="Galaxy S26 系列 2026-02-26 发布，首发价 S26 6999 元、S26+ 7999 元（12GB+256GB）、S26 Ultra 9999 元；2026-10 起官方调价后 S26+ 为 8999 元，三星商城当前标价与调价后一致。",
    ),
    "sam-26u": dict(
        price=9999, sku="12GB+256GB", status=V_SECONDARY,
        url="https://t.cj.sina.com.cn/articles/view/7879777290/1d5abdc0a06802kfs6",
        name="新浪财经头条（列出 S26 系列首发价与 2026-10 调价后对比）",
        ev="Galaxy S26 Ultra 2026-02-26 发布，12GB+256GB 首发价 9999 元；2026-10 官方调价后为 10999 元，三星商城当前标价与调价后一致。",
    ),
    "sam-zflip7": dict(
        price=7999, sku="12GB+256GB", status=V_OFFICIAL,
        url="https://www.samsung.com.cn/news/product/z-flip7/",
        name="三星电子中国官网 Galaxy Z Flip7 发布稿 + 官方促销页价目",
        ev="三星中国官网发布稿写明厂商建议零售价 7999 元起；官方促销页列出 12GB+256GB ￥7,999、12GB+512GB ￥8,999，2025-07-25 开售。",
    ),
    "sam-25e": dict(
        price=7999, sku="12GB+256GB", status=V_OFFICIAL,
        url="https://support-cn.samsung.com.cn/campaign/event/psg/2025/promotion/july/index.html",
        name="三星电子中国官方活动页（厂商建议零售价价目）",
        ev="三星中国官方活动页列出 Galaxy S25 Edge 12GB+256GB 厂商建议零售价 ￥7,999、12GB+512GB ￥8,999。",
    ),
    # ---------- 真我 / 努比亚 ----------
    "realme-gt8-pro": dict(
        price=3999, sku="12GB+256GB", status=V_SECONDARY,
        url="http://m.mnw.cn/news/digi/3051167.html",
        name="闽南网、中国网科技、南方+对 2025-10-21 真我 GT8 系列发布会的报道（五档价格一致）",
        ev="官方公布真我 GT8 Pro 五档售价：12GB+256GB 3999 元、16GB+256GB 4299 元、12GB+512GB 4499 元、16GB+512GB 4699 元、16GB+1TB 5199 元，2025-10-21 现货开售。",
    ),
    "realme-gt7": dict(
        price=2599, sku="12GB+256GB", status=V_SECONDARY,
        url="https://www.news.cn/tech/20250424/542d609da75d4e7bb8c44e791b6a4df5/c.html",
        name="新华网、中国日报网、中国经济网对 2025-04-23 真我 GT7 发布会的报道（价格一致）",
        ev="官方公布真我 GT7 售价 2599 元起（国补到手 2210 元起），共 5 个版本；中关村在线参数页 12GB+256GB 标价 2599 元，与之一致。",
    ),
    "nubia-z70u": dict(
        price=4599, sku="12GB+256GB", status=V_OFFICIAL,
        url="https://www.ztedevices.com/cn/news/nubia-z70-ultra-launch",
        name="中兴（努比亚）官网 Z70 Ultra 发布稿",
        ev="官网发布稿写明 12GB+256GB 4599 元、16GB+512GB 4999 元、16GB+1TB 5599 元、24GB+1TB 6299 元，星空典藏版 16GB+512GB 5499 元 / 16GB+1TB 5999 元，11-25 开售。",
    ),
    "redmagic-10p": dict(
        price=4999, sku="12GB+256GB", status=V_SECONDARY,
        url="http://i1.ce.cn/ce/cysc/tech/gd2012/202411/14/t20241114_39203011.shtml",
        name="中国经济网、中国青年网对 2024-11-13 红魔 10 Pro 系列发布会的报道 + 红魔官方微博价目",
        ev="红魔官方微博与媒体一致：红魔 10 Pro 12GB+256GB 4999 元、12GB+512GB 5499 元；氘锋透明版同容量 5299 / 5799 元；Pro+ 16GB+512GB 5999 元起。11-18 开售。",
    ),
}

PRICE_TEXT_OK = "官方首发起售价（非当前售价）"


def main():
    records = json.loads(DATA.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in records}
    missing = [k for k in P if k not in by_id]
    if missing:
        sys.exit("未找到记录: %s" % missing)

    n_real = n_start = 0
    for rid, cfg in P.items():
        r = by_id[rid]
        fa = r.get("fieldAudit")
        if not isinstance(fa, list):
            fa = []
        entry = None
        for e in fa:
            if isinstance(e, dict) and e.get("field") == FIELD:
                entry = e
                break
        if entry is None:
            entry = {"field": FIELD}
            fa.append(entry)

        r["priceCN"] = cfg["price"]
        if cfg["sku"]:
            entry.update({
                "value": "%d元（%s）" % (cfg["price"], cfg["sku"]),
                "status": cfg["status"],
                "sourceUrl": cfg["url"],
                "evidenceText": cfg["ev"],
                "note": "已核对中国大陆版与具体容量组合；首发价不等于当前售价。",
            })
            r["priceType"] = "official_launch_msrp"
            r["priceText"] = PRICE_TEXT_OK
            r["priceAuditStatus"] = ("verified" if cfg["status"] == V_OFFICIAL
                                     else "cross_checked_secondary")
            n_real += 1
        else:
            entry.update({
                "value": "%d元起；对应容量组合未公布" % cfg["price"],
                "status": V_START_ONLY,
                "sourceUrl": cfg["url"],
                "evidenceText": cfg["ev"],
                "note": "官方只给出起售价，未逐字公布该价位对应的容量 SKU；前端按「官方起售价（容量待核）」展示，不得当作已核验首发价。",
            })
            r["priceType"] = "official_starting_price"
            r["priceText"] = "官方起售价（对应容量组合未公布，非当前售价）"
            r["priceAuditStatus"] = "starting_price_only"
            n_start += 1

        r["fieldAudit"] = fa
        r["priceSource"] = cfg["url"]
        r["priceSourceName"] = cfg["name"]
        if not r.get("source"):
            r["source"] = cfg["url"]
        notes = r.get("auditNotes")
        if not isinstance(notes, list):
            notes = []
        if not any(TAG in x for x in notes):
            notes.append("%s：%s（%s）" % (
                TAG, entry["value"],
                "官网核验" if cfg["status"] == V_OFFICIAL else ("交叉核对" if cfg["sku"] else "仅起售价")))
        r["auditNotes"] = notes

    DATA.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("已写入 %d 条（含 SKU %d 条 / 仅起售价 %d 条）" % (len(P), n_real, n_start))
    print("目录：有价 %d / 共 %d" % (sum(1 for r in records if r.get("priceCN")), len(records)))

    # 注意：必须整体替换 `[...]` 块。早前版本用 `base[:-1] + "," + body + "]"` 拼接，
    # 会把旧数组一起保留，导致内嵌数据成倍重复，切勿再用。
    block = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
    for hp in HTMLS:
        html = hp.read_text(encoding="utf-8")
        m = re.search(r"window\.PHONE_DATA=(\[.*?\]);window\.MANUAL_QUOTES=", html, re.S)
        if not m:
            sys.exit("未在 %s 找到 PHONE_DATA 块" % hp.name)
        html2 = html[:m.start(1)] + block + html[m.end(1):]
        m2 = re.search(r"window\.PHONE_DATA=(\[.*?\]);window\.MANUAL_QUOTES=", html2, re.S)
        if json.loads(m2.group(1)) != records:
            sys.exit("%s 内嵌数据自检失败" % hp.name)
        hp.write_text(html2, encoding="utf-8")
        print("已同步", hp.name)


if __name__ == "__main__":
    main()
