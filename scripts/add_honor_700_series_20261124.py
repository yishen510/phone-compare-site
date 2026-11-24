"""把荣耀 700 系列三款机型按九字段取证结果加入待审核目录。

来源（均为厂商域名，2026-11-24 实际打开并逐项核对）：
  规格页  https://www.honor.com/cn/phones/<slug>/spec/
  发布稿  https://www.honor.com/cn/news/honor-700-launch/   （2026-11-23）

口径要点（按 AUDIT_POLICY.md）：
  - 官方只公布「国补后到手价」，未公布建议零售价 → priceType=price_pending，
    priceCN 留空；国补价/促销价不得写作官方首发价。
  - 规格页没有「屏幕刷新率」，也没有背屏尺寸；媒体口径的 120Hz / 1.72 英寸不采信，
    只在 specs 里显式标注「官方未列出」。
  - 九字段中 8 项 verified，首发价 1 项缺失 → auditStatus=pending_review，
    双重资格 false，不进排名/推荐。

用法：python scripts/add_honor_700_series_20261124.py
幂等：重复运行会先移除同 id 记录再写入。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
REPORT = ROOT / "reports" / "new_models_field_audit_2026-11-24.json"

TODAY = "2026-11-24"
NEWS = "https://www.honor.com/cn/news/honor-700-launch/"
SPEC = "https://www.honor.com/cn/phones/{}/spec/"
V = "verified_official_page_reviewed"
MISSING = "unverified_missing_or_insufficient_official_evidence"

COMMON_NOTE = (
    "2026-11-24 新增待审核目录记录。硬件字段按荣耀官网规格页逐项录入；"
    "价格仅有官方国补后到手价，建议零售价未公布，首发价不得视为已核验。"
    "整机待审核，不进入正式排名或推荐。"
)


def audit(field, value, status, url, evidence, note=""):
    return {
        "field": field,
        "value": value,
        "valueAtAudit": value,
        "status": status,
        "sourceUrl": url,
        "evidenceText": evidence,
        "note": note,
    }


def build(slug: str, name: str, mtype: str, chip: str, camera: str, charging: str,
          weight: str, storage: str, selling: str, best_for: list[str],
          screen_note: str, extra_specs: list[list[str]]) -> dict:
    spec_url = SPEC.format(slug)
    pid = slug
    spec_items = [
        ["上市时间", "2026年11月23日发布，11月27日开售（荣耀官网发布稿）"],
        ["屏幕", "6.57 英寸 AMOLED · FHD+ 2728×1264 · 峰值 8000nits · 3840Hz PWM 调光"],
        ["屏幕刷新率", "官方规格页未列出；官网对比页该字段 showInSpec=false 且值为空，故不填（媒体口径 120Hz 未采信）"],
        ["处理器", chip],
        ["后置摄像头", camera],
        ["前置摄像头", "5000 万像素广角摄像头（f/2.0 光圈）"],
        ["电池", "9000mAh（典型）/ 8760mAh（额定）"],
        ["充电", charging],
        ["尺寸与重量", "156.0 × 74.7 × 7.96mm · %s" % weight],
        ["存储组合", storage],
        ["防尘抗水", "IP68 / IP69 / IP69K（官方规格页标注 GB/T 4208-2017 与 ISO 20653:2023）"],
        ["操作系统", "MagicOS 11（基于 Android 17）"],
        ["AI 灵动背屏", "官方规格页未单独列出背屏尺寸与参数"],
    ] + extra_specs

    fields = [
        audit("屏幕", "6.57 英寸 AMOLED，FHD+ 2728×1264，峰值 8000nits", V, spec_url,
              "官方规格页「屏幕」分组：屏幕尺寸 6.57英寸、分辨率 FHD+ 2728x1264、类型 AMOLED、峰值亮度 8000nits",
              screen_note),
        audit("处理器", chip, V, spec_url,
              "官方规格页「处理器-CPU型号」原文：%s" % chip),
        audit("影像", camera, V, spec_url,
              "官方规格页「后置摄像头/前置摄像头」原文逐项抄录；3.5 倍光学变焦见官方发布稿"),
        audit("电池", "9000mAh（典型）/ 8760mAh（额定）", V, spec_url,
              "官方规格页电池容量 9000mAh（典型值），备注原文「电池额定容量为 8760mAh」"),
        audit("充电", charging, V, spec_url,
              "官方规格页「有线快充」原文 80W 荣耀超级快充；Pro 另有「无线充电」项备注最大 50W"),
        audit("重量", weight, V, spec_url,
              "官方规格页「尺寸与重量-重量」原文：%s" % weight),
        audit("容量组合", storage, V, spec_url,
              "官方规格页「存储」分组原文：%s" % storage),
        audit("正式发布/开售日期", "2026-11-23 发布 / 2026-11-27 首销", V, NEWS,
              "荣耀官网发布稿标注「2026年11月23日，荣耀在武汉举办新品发布会」，"
              "并写明首销期为 11月27日至12月31日"),
        audit("官方首发起售价", None, MISSING, NEWS,
              "官方发布稿只给「首销国补到手价」：700 Pro 4099 元起、700 3199 元起、700S 2899 元起；"
              "未公布建议零售价。按 AUDIT_POLICY 国补/促销价不得写作官方首发价，故首发价留空待核",
              "官网商城当前为订金预售，价格显示「暂无报价」"),
    ]

    return {
        "id": pid,
        "brand": "Honor",
        "name": name,
        "year": 2026,
        "type": mtype,
        "market": "中国大陆正式销售",
        "display": "6.57 英寸 AMOLED · FHD+ 2728×1264 · 峰值 8000nits",
        "chip": chip,
        "camera": camera,
        "battery": "9000mAh（典型）/ 8760mAh（额定）",
        "charging": charging,
        "weight": weight,
        "storage": storage,
        "os": "MagicOS 11（基于 Android 17）",
        "priceCN": None,
        "priceText": "官方仅公布国补后到手价，未公布建议零售价（首销期 2026-11-27 至 12-31）",
        "selling": selling,
        "bestFor": best_for,
        "source": spec_url,
        "sourceName": "荣耀官方网站规格页",
        "verified": False,
        "launchMonth": "2026-11",
        "launchDateDisplay": "2026年11月23日发布，11月27日首销",
        "priceType": "price_pending",
        "livePrice": None,
        "livePriceStatus": "not_connected",
        "livePriceCheckedAt": None,
        "storageOptions": [s.strip() for s in storage.split("/")],
        "chinaOfficial": True,
        "dataNote": COMMON_NOTE,
        "announcementSource": NEWS,
        "priceSource": NEWS,
        "priceSourceName": "荣耀官网发布稿（仅国补后到手价）",
        "livePriceNote": "尚未接入获授权的实时渠道报价 API；请通过渠道入口核价",
        "scoreMethod": "heuristic_preliminary",
        "quoteTargetStorage": None,
        "quoteTargetStorageReason": "官方未公布建议零售价与容量档位的对应价格，报价检索暂不触发。",
        "auditStatus": "pending_review",
        "auditNotes": [
            "2026-11-24 新增待审核记录；九字段按荣耀官网规格页与发布稿逐项核对，8/9 官方核验",
            "官方规格页没有「屏幕刷新率」字段，媒体口径 120Hz 未采信，specs 中已标注缺口",
            "官方规格页与概述页均未给出背屏尺寸，媒体口径 1.72 英寸未采信",
            "官方只公布国补后到手价，未公布建议零售价；按政策国补价不写作首发价，priceCN 留空",
            "首销期 2026-11-27 至 12-31；官网商城当前为订金预售，价格显示「暂无报价」",
            "官方未公布刷新率，卡片 display 不含 Hz，硬件筛选的刷新率条件不会命中这三款",
        ],
        "priceAuditStatus": "official_msrp_not_published",
        "parameterAuditStatus": "partial",
        "eligibleForRanking": False,
        "eligibleForRecommendation": False,
        "fieldAudit": fields,
        "specs": [{"group": "官方规格（已核验字段）", "items": spec_items}],
        "specSource": spec_url,
        "specSourceName": "荣耀官方产品规格页（仅含已核验字段）",
        "specFieldCount": 9,
        "specCollectedAt": TODAY,
    }


MODELS = [
    build(
        "honor-700", "荣耀700", "中端影像",
        "第四代骁龙 8s 移动平台（八核，最高 3.2GHz，Adreno 825）",
        "后置 2 亿像素广角(f/1.9,OIS)+5000 万潜望长焦(f/2.85,OIS,3.5x)+1200 万超广角微距(f/2.2)；前置 5000 万(f/2.0)",
        "80W 有线超级快充",
        "约 211g",
        "12GB+256GB / 12GB+512GB / 16GB+256GB / 16GB+512GB",
        "9000mAh 大电池 + AI 灵动背屏 + 2 亿主摄与 3.5 倍潜望长焦",
        ["拍照视频", "续航", "日常全能"],
        "官方规格页未列出刷新率，故只写分辨率与亮度",
        [["官方定位", "潮趣影像轻旗舰（荣耀发布稿原文）"]],
    ),
    build(
        "honor-700-pro", "荣耀700 Pro", "中端影像",
        "第五代骁龙 8 移动平台（八核，最高 3.8GHz，Adreno 829）",
        "后置 2 亿像素广角(f/1.9,OIS)+5000 万潜望长焦(f/2.85,OIS,3.5x)+1200 万超广角微距(f/2.2)；前置 5000 万(f/2.0)",
        "80W 有线超级快充 / 50W 无线超级快充",
        "约 213g",
        "12GB+256GB / 12GB+512GB / 16GB+512GB",
        "第五代骁龙 8 + 9000mAh + 50W 无线充 + 潜望长焦",
        ["拍照视频", "续航", "日常全能"],
        "官方规格页未列出刷新率，故只写分辨率与亮度",
        [["无线充电", "最大 50W 无线超级快充（需另购不小于 50W 的荣耀无线充电器）"],
         ["官方定位", "潮趣影像轻旗舰（荣耀发布稿原文）"]],
    ),
    build(
        "honor-700s", "荣耀700S", "中端全能",
        "第四代骁龙 7 移动平台（八核，最高 2.8GHz，Adreno 722）",
        "后置 2 亿像素广角(f/1.9,OIS)+1200 万超广角微距(f/2.2)；前置 5000 万(f/2.0)；后置双摄，无独立远摄模组",
        "80W 有线超级快充",
        "约 208g",
        "12GB+256GB / 12GB+512GB",
        "9000mAh 大电池 + AI 灵动背屏 + 2 亿主摄（双摄，无独立远摄）",
        ["拍照视频", "续航", "日常全能"],
        "官方规格页未列出刷新率，故只写分辨率与亮度",
        [["官方定位", "潮趣影像轻旗舰（荣耀发布稿原文）"],
         ["镜头说明", "官方规格页仅列广角主摄与超广角微距两枚后置镜头"]],
    ),
]

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
before = len(catalog)
ids = {m["id"] for m in MODELS}
catalog = [r for r in catalog if r.get("id") not in ids]
catalog.extend(MODELS)

CATALOG.write_text(
    json.dumps(catalog, ensure_ascii=False, indent=1).replace("\n", "\r\n"),
    encoding="utf-8", newline="",
)

report = {
    "generatedAt": TODAY,
    "scope": "荣耀700 / 700 Pro / 700S 九字段取证（官方规格页 + 官方发布稿）",
    "policy": "AUDIT_POLICY.md：九字段全 verified_official_page_reviewed 才允许 verified/排名/推荐",
    "conclusion": "三款均为 8/9 官方核验：屏幕/处理器/影像/电池/充电/重量/容量组合/发布日期已核，"
                  "官方首发价未公布（只有国补后到手价），故一律 pending_review、双重资格 false",
    "models": {
        m["id"]: {"name": m["name"], "market": m["market"], "source": m["source"],
                  "fieldAudit": m["fieldAudit"]}
        for m in MODELS
    },
    "updatedAt": "2026-11-24 首轮：荣耀官网规格页与发布稿",
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"目录 {before} → {len(catalog)} 条（新增 {len(MODELS)} 条）")
for m in MODELS:
    ok = sum(1 for f in m["fieldAudit"] if f["status"] == V)
    print(f"  {m['id']:<16} {ok}/9 verified  priceType={m['priceType']}  auditStatus={m['auditStatus']}")
print(f"审计底稿 → {REPORT.relative_to(ROOT)}")
