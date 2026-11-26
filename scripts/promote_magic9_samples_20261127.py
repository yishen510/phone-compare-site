"""把荣耀 Magic9 三兄弟升级为「九字段全官方核验」的准入样本。

目的：全库原本 0 台通过整机准入，推荐面板只能跑启发式打分。这里按 AUDIT_POLICY
把 3 台旗舰的九个字段逐项核到 verified_official_page_reviewed，让排名/推荐
第一次有真实候选。

证据链（2026-11-27 全部实际打开）
  规格页   https://www.honor.com/cn/phones/honor-magic9/spec/
           https://www.honor.com/cn/phones/honor-magic9-pro-max/spec/
           https://www.honor.com/cn/phones/honor-magic9-super-power/spec/
  概述页   .../cn/phones/<slug>/            （刷新率写在概述页：120Hz / 1–120Hz 自适应）
  发布稿   https://www.honor.com/cn/news/honor-magic9-launch/
           「荣耀Magic9 系列已于2026年9月28日正式开售」
           起售价：Pro Max 6499 / Magic9 4999 / 超能版 4499
  商城     https://www.honor.com/cn/shop/product/<prdId>.html
           内嵌 SKU 价目表（HTML 转义 JSON，价格字段 price/originPrice）：
             Magic9        12+256 4999 / 12+512 5499 / 16+512 5999 / 16+1TB 6999
             Magic9 ProMax 12+256 6499 / 12+512 6999 / 16+512 7499 / 16+1TB 8499
             超能版         12+256 4499 / 12+512 4999 / 16+512 5499
           三款「最低档价」与发布稿「XX 元起」完全一致 → 可判定为官方首发价，
           不是「只到起的起售价」。商城另有 handPrice（4699/4199）是国补到手价，
           按政策不得写作首发价，此处不用。

顺带修正：honor-magic9 原记录 priceCN=4499 是错的（与超能版串了），应为 4999。

用法：python scripts/promote_magic9_samples_20261127.py
幂等：按 id 覆盖审计相关字段。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
REPORT = ROOT / "reports" / "eligibility_samples_2026-11-27.json"

TODAY = "2026-11-27"
V = "verified_official_page_reviewed"
NEWS = "https://www.honor.com/cn/news/honor-magic9-launch/"
REQUIRED = ["屏幕", "处理器", "影像", "电池", "充电", "重量", "容量组合", "正式发布/开售日期", "官方首发起售价"]


def audit(field, value, url, evidence, note=""):
    return {"field": field, "value": value, "valueAtAudit": value,
            "status": V, "sourceUrl": url, "evidenceText": evidence, "note": note}


def build(pid, name, prd_id, display, chip, camera, battery, charging, weight,
          storage, selling, best_for, spec_extra, price, mtype):
    spec_url = f"https://www.honor.com/cn/phones/{pid}/spec/"
    page_url = f"https://www.honor.com/cn/phones/{pid}/"
    mall_url = f"https://www.honor.com/cn/shop/product/{prd_id}.html"

    fields = [
        audit("屏幕", display, spec_url,
              "官方规格页「屏幕」分组：尺寸/分辨率/类型/亮度/护眼逐项抄录；"
              "刷新率见官网概述页（%s）" % page_url),
        audit("处理器", chip, spec_url, "官方规格页「处理器-CPU型号」原文：%s" % chip),
        audit("影像", camera, spec_url, "官方规格页「后置摄像头 / 前置摄像头」分组原文"),
        audit("电池", battery, spec_url, "官方规格页电池容量（典型值）及其额定容量备注原文"),
        audit("充电", charging, spec_url, "官方规格页「有线快充 / 无线充电」分组原文"),
        audit("重量", weight, spec_url, "官方规格页「尺寸与重量-重量」原文"),
        audit("容量组合", storage, spec_url, "官方规格页「存储」分组原文"),
        audit("正式发布/开售日期", "2026-09-28 发布并开售", NEWS,
              "荣耀官网发布稿原文「荣耀Magic9 系列已于2026年9月28日正式开售」",
              "厂商发布稿，非媒体转述"),
        audit("官方首发起售价", price, mall_url,
              "荣耀商城商品页内嵌 SKU 价目表：12GB+256GB = ¥%d；与官网发布稿「售价 %d 元起」一致，"
              "故判定为官方首发价（对应中国大陆版 12GB+256GB）。商城另列 handPrice 为国补到手价，未采用" % (price, price),
              "首个 9/9 准入样本"),
    ]

    items = [
        ["上市时间", "2026年9月28日发布并开售（荣耀官网发布稿）"],
        ["屏幕", display],
        ["处理器", chip],
        ["后置摄像头", camera],
        ["电池", battery],
        ["充电", charging],
        ["尺寸与重量", weight],
        ["存储组合", storage],
        ["防尘抗水", "IP68 / IP69 / IP69K（官方规格页）"],
        ["操作系统", "MagicOS 11（基于 Android 17）"],
    ] + spec_extra

    return {
        "id": pid,
        "name": name,
        "type": mtype,
        "market": "中国大陆正式销售",
        "display": display,
        "chip": chip,
        "camera": camera,
        "battery": battery,
        "charging": charging,
        "weight": weight,
        "storage": storage,
        "selling": selling,
        "bestFor": best_for,
        "priceCN": price,
        "priceText": "官方首发起售价（12GB+256GB），非当前售价",
        "priceType": "official_launch_msrp",
        "priceSource": mall_url,
        "priceSourceName": "荣耀商城商品页（SKU 价目表）",
        "announcementSource": NEWS,
        "source": spec_url,
        "sourceName": "荣耀官方网站规格页",
        "verified": True,
        "auditStatus": "verified",
        "eligibleForRanking": True,
        "eligibleForRecommendation": True,
        "launchMonth": "2026-09",
        "launchDateDisplay": "2026年9月28日发布并开售",
        "storageOptions": [s.strip() for s in storage.split("/")],
        "chinaOfficial": True,
        "os": "MagicOS 11（基于 Android 17）",
        "dataNote": "2026-11-27 完成九字段官方核验，为全库首批通过整机准入的样本："
                    "屏幕/处理器/影像/电池/充电/重量/容量组合/发布日期/首发价均来自荣耀官网"
                    "（规格页、概述页、发布稿、商城 SKU 价目表）。价格为国补前官方首发价。",
        "auditNotes": [
            "2026-11-27 九字段全部 verified_official_page_reviewed，auditStatus=verified，双资格开启",
            "首发价取荣耀商城 12GB+256GB SKU 官方标价，与发布稿「XX 元起」一致；商城 handPrice 是国补到手价，未采用",
            "刷新率不在规格页，来自官网概述页（120Hz / 1–120Hz 自适应），已在屏幕字段注明",
            "honor-magic9 原记录 priceCN=4499 有误（与超能版串档），本次修正为 4999",
        ],
        "priceAuditStatus": "official_sku_mapping_verified",
        "parameterAuditStatus": "complete",
        "fieldAudit": fields,
        "_official_items": items,
        "specSource": spec_url,
        "specSourceName": "荣耀官方产品规格页 + 概述页 + 发布稿 + 商城价目表",
        "specFieldCount": 9,
        "specCollectedAt": TODAY,
        "scoreMethod": "heuristic_preliminary",
    }


UPDATES = {
    "honor-magic9": build(
        "honor-magic9", "荣耀 Magic9", "10086225001424",
        "6.37 英寸 OLED · FHD+ 1236×2664 · 120Hz · 峰值 10000nits",
        "第五代骁龙 8 至尊版移动平台",
        "后置 2 亿广角(1/1.4,F1.9,OIS)+2 亿长焦(F2.6,OIS,3.5x/120x)+5000 万超广角(F2.0)；前置 5500 万(F2.0,92°)",
        "8000mAh（典型）/ 7820mAh（额定）",
        "80W 有线超级快充 / 50W 无线超级快充 / 支持无线反向充电",
        "约 209g",
        "12GB+256GB / 12GB+512GB / 16GB+512GB / 16GB+1TB",
        "双 2 亿像素 + 8000mAh + 6.37 英寸小直屏",
        ["拍照视频", "日常全能"],
        [["屏幕刷新率", "120Hz（官网概述页）"], ["防尘抗水备注", "IP69K 满足 ISO 20653:2023"]],
        4999, "全能旗舰",
    ),
    "honor-magic9pm": build(
        "honor-magic9pm", "荣耀 Magic9 Pro Max", "10086407229464",
        "6.8 英寸 OLED · FHD+ 1320×2868 · 1–120Hz 自适应 · 峰值 10000nits",
        "第六代骁龙 8 超级至尊版移动平台",
        "后置 2 亿广角(F1.57,OIS)+2 亿潜望长焦(F2.6,OIS,3.5x/200x)+5000 万超广角(F2.0,AF)；前置 5500 万 + 3D 深感",
        "8800mAh（典型）/ 8600mAh（额定）",
        "100W 有线超级快充 / 80W 无线超级快充 / 支持无线反向充电",
        "约 233g",
        "12GB+256GB / 12GB+512GB / 16GB+512GB / 16GB+1TB",
        "第六代骁龙 8 超级至尊版 + 双 2 亿 + 200 倍潜望",
        ["拍照视频", "游戏性能", "日常全能"],
        [["屏幕刷新率", "1–120Hz 自适应（官网概述页）"]],
        6499, "全能旗舰",
    ),
    "honor-magic9-ultra": build(
        "honor-magic9-ultra", "荣耀 Magic9 超能版", "10086019084925",
        "6.81 英寸 OLED · FHD+ 1280×2788 · 120Hz · 峰值 10000nits",
        "第五代骁龙 8 至尊版移动平台",
        "后置 2 亿广角(1/1.55,F1.9,OIS)+5000 万长焦(F2.4,OIS,3x/100x)+1200 万超广角微距(F2.2)；前置 5000 万(F2.0,90°)",
        "11000mAh（典型）/ 10690mAh（额定）",
        "80W 有线超级快充 / 50W 无线超级快充 / 支持无线反向充电",
        "约 227g",
        "12GB+256GB / 12GB+512GB / 16GB+512GB",
        "11000mAh 超大电池 + 第五代骁龙 8 至尊版",
        ["续航", "日常全能"],
        [["屏幕刷新率", "120Hz（官网概述页）"]],
        4499, "性能续航旗舰",
    ),
}

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
by_id = {r["id"]: r for r in catalog}
for pid, patch in UPDATES.items():
    if pid not in by_id:
        raise SystemExit("目录里没有 %s" % pid)
    rec = by_id[pid]
    official = patch.pop("_official_items")
    keep = [g for g in (rec.get("specs") or []) if g.get("group") != "官方规格（九字段已核验）"]
    # 官方核验组置顶，完整参数表保留在下：既不丢细节，也让「已核验」的部分先被看到
    patch["specs"] = [{"group": "官方规格（九字段已核验）", "items": official}] + keep
    rec.update(patch)

CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=1).replace("\n", "\r\n"),
                   encoding="utf-8", newline="")


def gate(rec):
    fields = {f["field"]: f for f in rec.get("fieldAudit") or []}
    return (rec.get("auditStatus") == "verified" and rec.get("eligibleForRanking") is True
            and rec.get("eligibleForRecommendation") is True
            and all(fields.get(k, {}).get("status") == V for k in REQUIRED))


passed = [r for r in catalog if gate(r)]
report = {
    "generatedAt": TODAY,
    "scope": "荣耀 Magic9 / Magic9 Pro Max / Magic9 超能版 九字段官方核验，目标：产出首批准入样本",
    "policy": "AUDIT_POLICY.md 九字段全 verified_official_page_reviewed 才允许 verified/排名/推荐",
    "conclusion": "三款均 9/9 通过；全库准入样本从 0 台变为 3 台",
    "models": {pid: {"name": UPDATES[pid]["name"], "priceCN": UPDATES[pid]["priceCN"],
                     "priceSource": UPDATES[pid]["priceSource"],
                     "fieldAudit": UPDATES[pid]["fieldAudit"]} for pid in UPDATES},
    "gateResult": {"passedIds": [r["id"] for r in passed], "count": len(passed)},
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

print("全库 %d 条，通过整机准入 %d 条：" % (len(catalog), len(passed)))
for r in passed:
    print("  ✓ %-22s %s  ¥%s（12+256）" % (r["id"], r["name"], r.get("priceCN")))
print("报告 →", REPORT.relative_to(ROOT))
