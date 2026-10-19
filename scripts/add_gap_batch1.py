#!/usr/bin/env python3
"""补齐缺失旗舰（第一批 4 款）：Redmi K70 Pro、vivo X90、vivo X Fold2、OPPO Find X6。

只写入官方页明确的字段；价格、影像细节未确认则留空或标注待核验。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTE = "已逐项对照厂商中国大陆官方规格页；字段核实不等于整机准入通过。"

ROWS = [
    dict(
        id="redmi-k70-pro", brand="Xiaomi", name="REDMI K70 Pro", year=2023, type="性能旗舰",
        launch="2023-11", display="6.67 英寸 · 120Hz", chip="第三代骁龙 8",
        camera="官方规格页未逐项列出镜头组合，待核验",
        battery="5000 mAh", charging="120W 有线快充",
        weight="209 g / 211 g（版本不同）", os="MIUI 14", price=None,
        selling="2K 直屏 + 第三代骁龙 8 的性能旗舰",
        best_for=["游戏性能", "续航", "性价比"],
        options=["12GB+256GB", "16GB+512GB", "24GB+1TB"], quote="12GB+256GB",
        url="https://www.mi.com/redmi-k70-pro/specs",
        fields={"屏幕": ("6.67 英寸，120Hz", "官方规格页列出 6.67 英寸屏幕与 120Hz。"),
                "处理器": ("第三代骁龙 8", "官方规格页列出第三代骁龙 8 移动平台。"),
                "电池": ("5000 mAh", "官方规格页列出 5000mAh（典型值）。"),
                "充电": ("120W 有线", "官方规格页列出 120W 有线快充。"),
                "重量": ("209 g / 211 g（版本不同）", "官方规格页按版本列出 209g / 211g。")},
    ),
    dict(
        id="vivo-x90", brand="vivo", name="vivo X90", year=2022, type="影像旗舰",
        launch="2022-11", display="6.78 英寸 · 120Hz", chip="天玑 9200",
        camera="官方规格页未逐项列出镜头组合，待核验",
        battery="等效 4810 mAh（典型值，双电芯）/ 等效 4690 mAh（额定）",
        charging="120W 闪充",
        weight="约 200 g（至黑、冰蓝）/ 196 g（华夏红）/ 202 g（告白）",
        os="OriginOS 3", price=None, selling="天玑 9200 与蔡司影像的标准旗舰",
        best_for=["拍照视频", "日常全能"],
        options=["8GB+128GB", "8GB+256GB", "12GB+256GB", "12GB+512GB"], quote="12GB+256GB",
        url="https://www.vivo.com.cn/vivo/param/x90",
        fields={"屏幕": ("6.78 英寸", "官方规格页列出 6.78 英寸屏幕。"),
                "处理器": ("天玑 9200", "官方规格页列出天玑 9200 旗舰 5G 移动平台。"),
                "电池": ("等效 4810 mAh（典型值）/ 4690 mAh（额定）", "官方规格页按双电芯列出典型与额定等效容量。"),
                "充电": ("120W 闪充", "官方规格页列出 120W 闪充。"),
                "重量": ("约 200 g / 196 g / 202 g（配色不同）", "官方规格页按配色列出重量。")},
    ),
    dict(
        id="vivo-xfold2", brand="vivo", name="vivo X Fold2", year=2023, type="折叠屏旗舰",
        launch="2023-04", display="8.03 英寸内屏 + 6.53 英寸外屏 · 120Hz", chip="骁龙 8 Gen 2",
        camera="官方规格页未逐项列出镜头组合，待核验",
        battery="等效 4800 mAh（典型值，双电池）/ 等效 4680 mAh（额定）",
        charging="120W 有线 + 50W 无线",
        weight="278.5 g（华夏红、天青蓝）/ 279.5 g（弦影黑）",
        os="OriginOS 3", price=None, selling="大折叠中的快充与影像堆料款",
        best_for=["大屏办公", "拍照视频", "日常全能"],
        options=["12GB+256GB", "12GB+512GB"], quote="12GB+256GB",
        url="https://www.vivo.com.cn/vivo/param/xfold2",
        fields={"屏幕": ("内屏 8.03 英寸 / 外屏 6.53 英寸", "官方规格页分别列出内屏与外屏尺寸。"),
                "处理器": ("骁龙 8 Gen 2", "官方规格页列出骁龙 8 移动平台。"),
                "电池": ("等效 4800 mAh（典型值）/ 4680 mAh（额定）", "官方规格页按双电池列出等效容量。"),
                "充电": ("120W 有线 / 50W 无线", "官方规格页列出 120W 闪充与 50W 无线充电。"),
                "重量": ("278.5 g / 279.5 g（配色不同）", "官方规格页按配色列出重量。"),
                "容量组合": ("12GB+256GB / 12GB+512GB", "官方规格页列出两种容量组合。")},
    ),
    dict(
        id="oppo-x6", brand="OPPO", name="OPPO Find X6", year=2023, type="影像旗舰",
        launch="2023-03", display="6.74 英寸 · 120Hz", chip="天玑 9200",
        camera="官方规格页未逐项列出镜头组合，待核验",
        battery="等效 4800 mAh（典型值，双电芯）/ 等效 4700 mAh（额定）",
        charging="80W 超级闪充", weight="207 克",
        os="ColorOS 13.1", price=None, selling="哈苏影像的标准旗舰",
        best_for=["拍照视频", "日常全能"],
        options=["12GB+256GB", "16GB+512GB"], quote="12GB+256GB",
        url="https://www.oppo.com/cn/smartphones/series-find-x/find-x6/specs/",
        fields={"屏幕": ("6.74 英寸（对角线）", "官方规格页列出 6.74 英寸屏幕。"),
                "处理器": ("天玑 9200", "官方规格页列出天玑 9200 移动平台。"),
                "电池": ("等效 4800 mAh（典型值）/ 4700 mAh（额定）", "官方规格页按双电芯列出等效容量。"),
                "充电": ("80W 超级闪充", "官方规格页列出 80W 超级闪充。"),
                "重量": ("207 克", "官方规格页列出重量 207 克。"),
                "容量组合": ("12GB+256GB / 16GB+512GB", "官方规格页列出两种容量组合。")},
    ),
]


def build(row: dict) -> dict:
    audit = [
        {"field": k, "value": v, "status": "verified_official_page_reviewed",
         "sourceUrl": row["url"], "evidenceText": ev, "valueAtAudit": v, "note": NOTE}
        for k, (v, ev) in row["fields"].items()
    ]
    return {
        "id": row["id"], "brand": row["brand"], "name": row["name"], "year": row["year"],
        "type": row["type"], "market": "中国大陆正式销售",
        "display": row["display"], "chip": row["chip"], "camera": row["camera"],
        "battery": row["battery"], "charging": row["charging"], "weight": row["weight"],
        "storage": " / ".join(row["options"]), "os": row["os"],
        "priceCN": row["price"],
        "priceText": ("官方首发起售价（非当前售价，待官方发布稿复核）" if row["price"]
                      else "官方首发起售价待核验；不以当前渠道价代替"),
        "selling": row["selling"], "bestFor": row["best_for"],
        "source": row["url"], "sourceName": "厂商官方站点；字段核验状态见 auditStatus",
        "verified": False, "launchMonth": row["launch"],
        "launchDateDisplay": f"{row['launch'][:4]}年{row['launch'][5:7]}月",
        "priceType": "official_launch_msrp" if row["price"] else "unknown",
        "livePrice": None, "livePriceStatus": "not_connected", "livePriceCheckedAt": None,
        "storageOptions": row["options"], "chinaOfficial": True,
        "dataNote": "主要参数已按厂商中国大陆官方规格页核对；未列出的字段仍待核验，整机准入保持关闭。",
        "announcementSource": row["url"],
        "priceSource": row["url"] if row["price"] else None,
        "priceSourceName": ("厂商官方站点；首发价仍需官方发布稿二次核对" if row["price"]
                            else "来源页未直接支持该首发价，需补查官方发布稿"),
        "livePriceNote": "尚未接入获授权的实时渠道报价 API；请通过渠道入口核价",
        "scoreMethod": "heuristic_preliminary",
        "quoteTargetStorage": row["quote"],
        "quoteTargetStorageReason": "报价检索只接受商品标题中可核验的型号与这一指定大陆版 RAM/ROM 组合。",
        "auditStatus": "needs_parameter_price_audit",
        "auditNotes": ["机型身份与发布月份按厂商公开信息录入",
                       "主要参数已按厂商官方规格页核对（2026-10-20）",
                       "影像细节与首发价未核验，整机准入保持关闭"],
        "priceAuditStatus": "source_present_needs_crosscheck" if row["price"] else "missing",
        "parameterAuditStatus": "partial",
        "fieldAudit": audit,
    }


def patch_html(path: Path, records: list[dict]) -> None:
    html = path.read_text(encoding="utf-8")
    m = re.search(r"window\.PHONE_DATA=(\[.*?\]);window\.MANUAL_QUOTES=", html, re.S)
    base = m.group(1).rstrip()
    body = json.dumps(records, ensure_ascii=False, separators=(",", ":"))[1:-1]
    block = base[:-1] + "," + body + "]"
    json.loads(block)
    path.write_text(html[: m.start(1)] + block + html[m.end(1):], encoding="utf-8")


def main() -> None:
    p = ROOT / "data" / "phones.json"
    catalog = json.loads(p.read_text(encoding="utf-8"))
    have = {r["id"] for r in catalog}
    records = [build(r) for r in ROWS if r["id"] not in have]
    if not records:
        raise SystemExit("FAIL: 目标机型已存在")
    catalog.extend(records)
    p.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name in ("index.html", "phone-compare-demo.html"):
        patch_html(ROOT / name, records)
    print(f"PASS: 新增 {len(records)} 款，总计 {len(catalog)}")


if __name__ == "__main__":
    main()
