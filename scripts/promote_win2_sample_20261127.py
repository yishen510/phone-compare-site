"""把荣耀 WIN2 升级为第 4 个「九字段官方核验」准入样本。

为什么是它：换厂商的路都堵死了（华为发布会新闻稿不含价格、三星新闻稿无价格、
vivo/OPPO 前端渲染、苹果不公布 mAh），而荣耀官网有发布稿的机型只有 700/Magic9/WIN2。
700 系列官方至今「暂无报价」，Magic9 已入库，剩下能做的就是 WIN2。

首发价的取证口径（本脚本的判定条件，写进 evidenceText 供复核）
  来源：荣耀商城商品页内嵌 SKU 价目表（官方购买指引）—— 12GB+256GB = ¥5499
  条件一：price == originPrice（未打折，说明不是促销价）
  条件二：与发布稿「首销国补到手价 4999 元起」的差额 = 500 元 = 国补封顶额（旁证）
  两条都满足才认定；WIN RT2 差 1350 元、对不上，因此不纳入。
  **注意：这只是旁证，不是用国补价反推标价**，标价本身是商城自己写的。

日期：发布稿原文「荣耀WIN2、荣耀WIN RT2 发布即首销」「首销期间（10月21日到11月22日）」
      → 2026-10-21 发布并首销。

用法：python scripts/promote_win2_sample_20261127.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
REPORT = ROOT / "reports" / "eligibility_samples_2026-11-27.json"

TODAY = "2026-11-27"
V = "verified_official_page_reviewed"
NEWS = "https://www.honor.com/cn/news/honor-win2-series/"
SPEC = "https://www.honor.com/cn/phones/honor-win2/spec/"
PAGE = "https://www.honor.com/cn/phones/honor-win2/"
MALL = "https://www.honor.com/cn/shop/product/10086249682976.html"

DISPLAY = "6.89 英寸 OLED · 2K 3104×1440 · 185Hz"
CHIP = "第六代骁龙 8 超级至尊版移动平台"
CAMERA = "后置 2 亿主摄(1/1.4,F1.9,OIS)+1200 万超广角(F2.2)；前置 5000 万(F2.0,90°)"
BATTERY = "10100mAh（典型）/ 9850mAh（额定）"
CHARGING = "100W 有线超级快充 / 80W 无线超级快充 / 支持无线反向充电"
WEIGHT = "约 237g"
STORAGE = "12GB+256GB / 12GB+512GB / 16GB+256GB / 16GB+512GB / 16GB+1TB"
PRICE = 5499


def audit(field, value, url, evidence, note=""):
    return {"field": field, "value": value, "valueAtAudit": value,
            "status": V, "sourceUrl": url, "evidenceText": evidence, "note": note}


fields = [
    audit("屏幕", DISPLAY, SPEC,
          "官方规格页「屏幕」分组：6.89 英寸 / QHD+ 3104×1440 / OLED；"
          "185Hz 见官网概述页原文「2K+185Hz」"),
    audit("处理器", CHIP, SPEC, "官方规格页「处理器-CPU型号」原文"),
    audit("影像", CAMERA, SPEC, "官方规格页「后置摄像头/前置摄像头」分组原文"),
    audit("电池", BATTERY, SPEC, "官方规格页电池容量 10100mAh（典型值），备注「额定值为 9850mAh」"),
    audit("充电", CHARGING, SPEC, "官方规格页「有线快充/无线充电」原文：100W 有线、80W 无线、支持无线反向"),
    audit("重量", WEIGHT, SPEC, "官方规格页「尺寸与重量-重量」原文：约 237g（含电池）"),
    audit("容量组合", STORAGE, SPEC, "官方规格页「存储」分组原文，五档"),
    audit("正式发布/开售日期", "2026-10-21 发布并首销", NEWS,
          "荣耀官网发布稿原文「荣耀WIN2、荣耀WIN RT2 发布即首销」及「首销期间（10月21日到11月22日）」"),
    audit("官方首发起售价", PRICE, MALL,
          "荣耀商城商品页内嵌 SKU 价目表：12GB+256GB = ¥5499，且 originPrice 同为 5499（未打折）；"
          "官网发布稿只公布「首销国补到手价 4999 元起」，差额 500 元等于国补封顶额，可互为旁证。"
          "首发价以官方购买指引的 SKU 标价认定，未用国补价反推",
          "判定条件：price==originPrice 且与发布稿国补价差额=500"),
]

patch = {
    "display": DISPLAY, "chip": CHIP, "camera": CAMERA, "battery": BATTERY,
    "charging": CHARGING, "weight": WEIGHT, "storage": STORAGE,
    "selling": "10100mAh + 185Hz 2K 直屏 + 第六代骁龙 8 超级至尊版",
    "bestFor": ["游戏性能", "续航", "日常全能"],
    "priceCN": PRICE, "priceType": "official_launch_msrp",
    "priceText": "官方起售价（12GB+256GB），非当前售价",
    "priceSource": MALL, "priceSourceName": "荣耀商城商品页（SKU 价目表）",
    "announcementSource": NEWS, "source": SPEC, "sourceName": "荣耀官方网站规格页",
    "verified": True, "auditStatus": "verified",
    "eligibleForRanking": True, "eligibleForRecommendation": True,
    "launchMonth": "2026-10", "launchDateDisplay": "2026年10月21日发布并首销",
    "storageOptions": [s.strip() for s in STORAGE.split("/")],
    "dataNote": "2026-11-27 完成九字段官方核验并开启排名/推荐资格。首发价取自荣耀商城 12GB+256GB 的 SKU 标价"
                "（未打折），与发布稿国补价差额等于国补封顶额。",
    "auditNotes": [
        "2026-11-27 九字段全部 verified_official_page_reviewed，auditStatus=verified，双资格开启",
        "首发价来源是荣耀商城 SKU 标价，不是发布稿明示（发布稿只给国补到手价）；判定条件写进 evidenceText",
        "WIN RT2 未纳入：其发布稿国补价 3149 与商城标价 4499 差 1350，不符合「差额=国补封顶 500」的旁证条件",
        "185Hz 不在规格页，来自官网概述页，已在屏幕字段注明",
    ],
    "priceAuditStatus": "official_store_sku_verified",
    "parameterAuditStatus": "complete",
    "fieldAudit": fields,
    "specFieldCount": 9, "specCollectedAt": TODAY,
}

items = [
    ["上市时间", "2026年10月21日发布并首销（荣耀官网发布稿）"],
    ["屏幕", DISPLAY],
    ["处理器", CHIP],
    ["后置摄像头", CAMERA],
    ["电池", BATTERY],
    ["充电", CHARGING],
    ["尺寸与重量", "8.5mm · " + WEIGHT],
    ["存储组合", STORAGE],
    ["防尘抗水", "IP68 / IP69 / IP69K（官方规格页）"],
    ["操作系统", "MagicOS 11（基于 Android 17）"],
]

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
rec = next((r for r in catalog if r["id"] == "honor-win2"), None)
if rec is None:
    raise SystemExit("目录里没有 honor-win2")
keep = [g for g in (rec.get("specs") or []) if g.get("group") != "官方规格（九字段已核验）"]
rec.update(patch)
rec["specs"] = [{"group": "官方规格（九字段已核验）", "items": items}] + keep

CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=1).replace("\n", "\r\n"),
                   encoding="utf-8", newline="")

REQUIRED = ["屏幕", "处理器", "影像", "电池", "充电", "重量", "容量组合", "正式发布/开售日期", "官方首发起售价"]


def gate(r):
    names = {f["field"]: f for f in (r.get("fieldAudit") or [])}
    return (r.get("auditStatus") == "verified" and r.get("eligibleForRanking") is True
            and r.get("eligibleForRecommendation") is True
            and all(names.get(k, {}).get("status") == V for k in REQUIRED))


passed = [r for r in catalog if gate(r)]
report = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {}
report.update({
    "generatedAt": TODAY,
    "conclusion": "全库准入样本 4 台：荣耀 Magic9 / Magic9 Pro Max / Magic9 超能版 / WIN2",
    "win2": {"name": rec["name"], "priceCN": PRICE, "priceSource": MALL, "fieldAudit": fields},
    "gateResult": {"passedIds": [r["id"] for r in passed], "count": len(passed)},
})
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

print("全库 %d 条，通过整机准入 %d 条：" % (len(catalog), len(passed)))
for r in passed:
    print("  ✓ %-22s %-22s ¥%s" % (r["id"], r["name"], r.get("priceCN")))
