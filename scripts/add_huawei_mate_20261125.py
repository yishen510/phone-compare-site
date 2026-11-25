"""把华为 Mate X8 / Mate 90 Air 按九字段取证结果加入待审核目录。

来源（2026-11-25 实际打开）：
  规格页  https://consumer.huawei.com/cn/phones/mate-x8/specs/
          https://consumer.huawei.com/cn/phones/mate90-air/specs/
  产品页  https://consumer.huawei.com/cn/phones/mate-x8/        （¥12999 起）
          https://consumer.huawei.com/cn/phones/mate90-air/     （¥4999 起）
  发布日期/开售：新华网、深圳新闻网、环球网（厂商未在官网页面写日期，只能归到
                cross_checked_secondary_source，不能写成官网已核）

口径要点：
  - Mate X8 的逐档价格（12+256=12999 … 16+2TB=20999）出自上证报/南方+，
    与官方产品页「¥12999 起」一致 → priceType=official_launch_msrp，
    但字段状态只能记 cross_checked_secondary_source。
  - Mate 90 Air 官方只给「¥4999 起」，权威媒体未逐个映射容量
    → priceType=official_starting_price，状态 starting_price_only_sku_mapping_unverified。
  - 两款官网规格页都没有「刷新率」（X8 的 1–120Hz 写在屏幕类型里，已采信；
    90 Air 全文无刷新率字样，不填）。
  - X8 官方原文是 IP58、IP59，不是媒体常写的 IP68，按原文录入。

用法：python scripts/add_huawei_mate_20261125.py
幂等：重复执行先移除同 id 再写入。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
REPORT = ROOT / "reports" / "new_models_field_audit_2026-11-25.json"

TODAY = "2026-11-25"
V = "verified_official_page_reviewed"
MEDIA = "cross_checked_secondary_source"
STARTING = "starting_price_only_sku_mapping_unverified"
NEWS_X8 = "https://www.xinhuanet.com/tech/20261125/183b44374e6c40c6844c9bcaa8877f66/c.html"
NEWS_SZ = "https://www.sznews.com/news/content/mb/2026-11/24/content_32222152.htm"


def audit(field, value, status, url, evidence, note=""):
    return {"field": field, "value": value, "valueAtAudit": value,
            "status": status, "sourceUrl": url, "evidenceText": evidence, "note": note}


X8_SPEC = "https://consumer.huawei.com/cn/phones/mate-x8/specs/"
X8_PAGE = "https://consumer.huawei.com/cn/phones/mate-x8/"
AIR_SPEC = "https://consumer.huawei.com/cn/phones/mate90-air/specs/"
AIR_PAGE = "https://consumer.huawei.com/cn/phones/mate90-air/"

X8_DISPLAY = "内屏 8.2 英寸 2424×2340 / 外屏 6.54 英寸 2444×1132 · 双 1–120Hz LTPO · 1440Hz PWM"
X8_CAMERA = ("后置 5000 万超动态范围(F1.4–F4.0 可变光圈,OIS,1/1.56\")+4000 万超广角(F2.2)"
             "+5000 万潜望长焦(F2.2,OIS)+第三代红枫原色；前置 800 万×2（内外屏，F2.4）；3.5x 光学 / 100x 数字")
X8_WEIGHT = "约 237g（标准版）/ 约 239g（典藏版）"
X8_STORAGE = "12GB+256GB / 12GB+512GB / 16GB+512GB / 16GB+1TB / 16GB+2TB（后三档为典藏版）"
X8_CHARGE = "66W 有线超级快充 / 50W 无线超级快充 / 支持无线反向充电"

AIR_DISPLAY = "7 英寸 OLED · FHD+ 2760×1320 · 2160Hz PWM 调光"
AIR_CAMERA = ("后置 5000 万 1/1.3\"(F1.8,OIS)+1200 万 RYYB 长焦(F2.4,OIS,3x)"
              "+800 万超广角微距(F2.2)+150 万多光谱红枫原色；前置 1070 万超广角(F2.2)")
AIR_STORAGE = "12GB+256GB / 12GB+512GB"
AIR_CHARGE = "66W 有线超级快充（仅有线充电）"


def build(pid, name, mtype, spec_url, page_url, display, chip, camera, charging,
          weight, storage, selling, best_for, extra, price, price_type, price_text,
          price_status, price_evidence, date_note, data_note):
    fields = [
        audit("屏幕", display, V, spec_url,
              "官方规格页「屏幕」分组逐项抄录（尺寸/分辨率/类型/刷新率与调光）"),
        audit("处理器", chip, V, spec_url, "官方规格页「处理器」原文：%s" % chip),
        audit("影像", camera, V, spec_url,
              "官方规格页「后置摄像头 / 前置摄像头」原文；变焦倍数见「后置摄像头变焦模式」"),
        audit("电池", "6200mAh（典型）/ 6025mAh（额定）" if "X8" in name else "6500mAh（典型）/ 6380mAh（额定）",
              V, spec_url, "官方规格页电池容量与额定容量备注原文"),
        audit("充电", charging, V, spec_url, "官方规格页「充电」分组原文", "无线快充需另购对应充电器"),
        audit("重量", weight, V, spec_url, "官方规格页「尺寸与重量-重量」原文"),
        audit("容量组合", storage, V, spec_url, "官方规格页「存储」分组原文"),
        audit("正式发布/开售日期", date_note, MEDIA, NEWS_X8,
              "新华网《多款新品发布，HUAWEI Mate X8 及全场景新品发布会召开》写明 11月24日发布、"
              "Mate X8 于 12月4日10:08 开售；深圳新闻网同日报道一致。厂商官网页面未标注日期，故不记官网已核",
              "厂商未在官网页面公布日期，只能按权威媒体记账"),
        audit("官方首发起售价", price, price_status, page_url,
              price_evidence, "见 priceType 说明"),
    ]
    return {
        "id": pid, "brand": "Huawei", "name": name, "year": 2026, "type": mtype,
        "market": "中国大陆正式销售",
        "display": display, "chip": chip, "camera": camera,
        "battery": "6200mAh（典型）/ 6025mAh（额定）" if "X8" in name else "6500mAh（典型）/ 6380mAh（额定）",
        "charging": charging, "weight": weight, "storage": storage,
        "os": "HarmonyOS 7.0",
        "priceCN": price, "priceText": price_text, "selling": selling, "bestFor": best_for,
        "source": spec_url, "sourceName": "华为官方产品规格页",
        "verified": False, "launchMonth": "2026-11",
        "launchDateDisplay": "2026年11月24日发布，12月4日10:08开售",
        "priceType": price_type, "livePrice": None, "livePriceStatus": "not_connected",
        "livePriceCheckedAt": None,
        "storageOptions": [s.strip() for s in storage.split("/")],
        "chinaOfficial": True, "dataNote": data_note,
        "announcementSource": NEWS_X8, "priceSource": page_url,
        "priceSourceName": "华为官方产品页（起售价）",
        "livePriceNote": "尚未接入获授权的实时渠道报价 API；请通过渠道入口核价",
        "scoreMethod": "heuristic_preliminary", "quoteTargetStorage": None,
        "quoteTargetStorageReason": "需官方公布容量档位与价格对应关系后再触发报价检索。",
        "auditStatus": "pending_review",
        "auditNotes": [
            "2026-11-25 新增待审核记录；九字段按华为官方规格页/产品页与权威媒体逐项核对",
            "发布日期与开售时间厂商官网未标注，按新华网/深圳新闻网记为 cross_checked_secondary_source",
            "X8 官方原文防尘抗水为 IP58、IP59（不是媒体常写的 IP68），按原文录入",
            "90 Air 官方规格页全文无刷新率字样，不填；媒体口径未采信",
            "两款官网商城为预售页，逐档价格需以发布稿/权威媒体口径为准",
        ],
        "priceAuditStatus": "cross_checked_sku_mapping" if price_status == MEDIA else "starting_price_only",
        "parameterAuditStatus": "partial",
        "eligibleForRanking": False, "eligibleForRecommendation": False,
        "fieldAudit": fields,
        "specs": [{"group": "官方规格（已核验字段）", "items": [
            ["上市时间", "2026年11月24日发布，12月4日10:08开售（厂商官网未标注，据新华网/深圳新闻网）"],
            ["屏幕", display],
            ["处理器", chip],
            ["后置摄像头", camera],
            ["充电", charging],
            ["电池", "6200mAh（典型）/ 6025mAh（额定）" if "X8" in name else "6500mAh（典型）/ 6380mAh（额定）"],
            ["尺寸与重量", weight],
            ["存储组合", storage],
            ["操作系统", "HarmonyOS 7.0"],
        ] + extra}],
        "specSource": spec_url, "specSourceName": "华为官方产品规格页",
        "specFieldCount": 9, "specCollectedAt": TODAY,
    }


MODELS = [
    build(
        "hua-matex8", "HUAWEI Mate X8", "折叠屏旗舰", X8_SPEC, X8_PAGE,
        X8_DISPLAY, "麒麟 9050 Pro", X8_CAMERA, X8_CHARGE, X8_WEIGHT, X8_STORAGE,
        "8.2 英寸内屏 + 4.2mm 展开厚度 + 麒麟 9050 Pro + 双 5000 万潜望影像",
        ["大屏办公", "拍照视频", "日常全能"],
        [["防尘抗水", "IP58、IP59（官方规格页原文）"],
         ["厚度", "折叠态 8.95mm / 展开态 4.2mm"],
         ["SIM", "支持 eSIM（最多存 2 个号码）；四卡三待需按运营商业务开通"],
         ["卫星通信", "双向北斗卫星消息"],
         ["其他", "星闪 E2.0 · USB 3.1 Gen 1 · 支持睿影 Z10 模块相机"]],
        12999, "official_launch_msrp",
        "官方首发起售价（12GB+256GB，非当前售价）",
        MEDIA,
        "官方产品页原文「¥12999 * 起」；上证报/南方+逐档报道 12GB+256GB=12999、12+512=13999、"
        "典藏 16+512=15999、16+1TB=16999、16+2TB=20999，与起售价一致",
        "2026年11月24日发布，12月4日10:08开售",
        "2026-11-25 新增待审核目录记录。硬件按华为官方规格页录入；日期与逐档价格厂商官网未完整公开，"
        "按权威媒体口径记账并标注。整机待审核，不进入正式排名或推荐。",
    ),
    build(
        "hua-mate90air", "HUAWEI Mate 90 Air", "全能旗舰", AIR_SPEC, AIR_PAGE,
        AIR_DISPLAY, "麒麟 9020", AIR_CAMERA, AIR_CHARGE, "208g", AIR_STORAGE,
        "6.58mm 机身 + 7 英寸大屏 + 6500mAh 电池，华为最薄 Mate 直板机",
        ["大屏办公", "续航", "拍照视频"],
        [["厚度", "6.58mm（华为最薄 Mate 直板机）"],
         ["防尘抗水", "IP68、IP69（官方规格页原文）"],
         ["卫星通信", "北斗卫星消息（仅限中国大陆）"],
         ["其他", "星闪 E2.0 · USB 2.0（不支持有线投屏）· 官方规格页未列刷新率"]],
        4999, "official_starting_price",
        "官方起售价（对应容量组合未公布，非当前售价）",
        STARTING,
        "官方产品页原文「¥4999 * 起」；新华网/环球网报道「4999 元起、国补后 4499 元起」，"
        "但未把 4999 明确对应到 12GB+256GB，故按起售价记账、不写官方首发价",
        "2026年11月24日发布并开启预售，12月4日10:08开售",
        "2026-11-25 新增待审核目录记录。硬件按华为官方规格页录入；官方仅公布起售价，"
        "容量档位与价格对应关系未公开。整机待审核，不进入正式排名或推荐。",
    ),
]

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
before = len(catalog)
ids = {m["id"] for m in MODELS}
catalog = [r for r in catalog if r.get("id") not in ids]
catalog.extend(MODELS)
CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=1).replace("\n", "\r\n"),
                   encoding="utf-8", newline="")

report = {
    "generatedAt": TODAY,
    "scope": "华为 Mate X8 / Mate 90 Air 九字段取证（官方规格页 + 产品页 + 权威媒体）",
    "policy": "AUDIT_POLICY.md：九字段全 verified_official_page_reviewed 才允许 verified/排名/推荐",
    "conclusion": "两款均 7/9：屏幕/处理器/影像/电池/充电/重量/容量组合已官网核验；"
                  "发布日期与价格只有权威媒体口径，按 cross_checked_secondary_source 记账，"
                  "故一律 pending_review、双重资格 false",
    "models": {m["id"]: {"name": m["name"], "market": m["market"],
                         "source": m["source"], "fieldAudit": m["fieldAudit"]} for m in MODELS},
    "updatedAt": "2026-11-25 首轮：华为官网规格页与发布会报道",
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"目录 {before} → {len(catalog)} 条（新增 {len(MODELS)} 条）")
for m in MODELS:
    ok = sum(1 for f in m["fieldAudit"] if f["status"] == V)
    print(f"  {m['id']:<16} {ok}/9 verified  priceType={m['priceType']}  priceCN={m['priceCN']}")
print(f"审计底稿 → {REPORT.relative_to(ROOT)}")
