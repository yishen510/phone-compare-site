#!/usr/bin/env python3
"""补录新发布机型：参数取自中关村在线参数页，价格与开售日取自官方页/权威媒体。

约定：
- 参数（屏幕/芯片/电池/充电/重量/容量/摄像头明细）整组写入 specs；
  display/chip/camera/battery/charging/weight/storage/os 先由参数表派生（derive），
  再用 meta["overrides"] 覆盖参数表写得含糊或缺失的字段。
- 价格必须有可点开的来源（meta["priceSource"]），不拿渠道现价顶替首发价。
- 参数站与官方页冲突时以官方页为准，冲突写进 auditNotes。

用法：
  python scripts/add_new_models.py            # 只补缺的
  python scripts/add_new_models.py --refresh  # 已存在的也按最新来源重建
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backfill_summary_from_specs import derive  # noqa: E402
from import_zol_params import fetch, parse_specs, patch_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
TODAY = "2026-10-24"
ZOL_SRC = "https://detail.zol.com.cn/{}/{}/param.shtml"

NEW = [
    # ---------------- 2026-10 ----------------
    {
        "id": "hua-mate90rs", "brand": "Huawei", "name": "HUAWEI Mate 90 RS 非凡大师",
        "type": "顶级全能旗舰", "launchMonth": "2026-10", "launchDateDisplay": "2026年10月01日",
        "priceCN": 12999, "priceType": "official_launch_msrp",
        "priceText": "官方起售价（16GB+512GB 起，非当前渠道价）",
        "priceSource": "https://www.cnr.cn/tech/techph/20261001/t20261001_527831564.shtml",
        "priceSourceName": "央广网·华为 Mate 90 系列发布会报道",
        "announcementSource": "https://www.cnr.cn/tech/techph/20261001/t20261001_527831564.shtml",
        "selling": "麒麟 9050 Pro + 第三代红枫影像，星钻镜头设计",
        "bestFor": ["拍照视频", "日常全能", "大屏办公"],
        "storageOptions": ["16GB+512GB", "16GB+2TB"],
        "quoteTargetStorage": "16GB+512GB",
        "zol": ("2180", "2179252"),
        "overrides": {"display": "6.9 英寸 OLED · 1–120Hz",
                      "battery": "6800mAh", "charging": "100W 有线 / 50W 无线",
                      "os": "HarmonyOS 7"},
        "notes": [
            "价格 12999 元与 10 月 1 日 12:08 开售来自央广网、湖北日报、经济网三篇发布会报道，口径一致。",
            "ZOL 参数页未列「操作系统」，HarmonyOS 7 取自同场发布会报道，标注为媒体口径。",
        ],
    },
    {
        "id": "oneplus-16", "brand": "OnePlus", "name": "一加 16",
        "type": "性能旗舰", "launchMonth": "2026-10", "launchDateDisplay": "2026年10月12日",
        "priceCN": 5999, "priceType": "official_launch_msrp",
        "priceText": "官方标价（12GB+256GB）；首销 5699 元，国补到手 5199 元起",
        "priceSource": "https://it.sohu.com/a/1091255588_114838",
        "priceSourceName": "搜狐科技·一加 16 发布报道（含四档价格表）",
        "announcementSource": "https://news.qq.com/rain/a/20261023A08TVX00",
        "selling": "185 帧游戏 + 9000mAh 冰川电池，100W 有线 / 50W 无线",
        "bestFor": ["游戏性能", "续航", "日常全能"],
        "storageOptions": ["12GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"],
        "quoteTargetStorage": "12GB+256GB",
        "zol": ("2181", "2180390"),
        "overrides": {"display": "6.78 英寸 OLED · 1–165Hz（游戏场景 185Hz）",
                      "charging": "100W 有线 / 50W 无线", "os": "ColorOS 17"},
        "notes": [
            "价格取自搜狐科技报道的四档价目表（5999/6499/7199/8499 标价），与华商网、腾讯新闻口径一致。",
            "ZOL 参数页屏幕刷新率写 165Hz；官方口径为日常 1-165Hz、游戏最高 185Hz，本站按官方描述填写。",
        ],
    },
    {
        "id": "apple-duo", "brand": "Apple", "name": "iPhone Duo",
        "type": "折叠屏旗舰", "launchMonth": "2026-10", "launchDateDisplay": "2026年10月23日",
        "priceCN": 15999, "priceType": "official_launch_msrp",
        "priceText": "官方起售价（256GB）；512GB 17999 / 1TB 21499 / 2TB 26499",
        "priceSource": "https://www.apple.com.cn/cn_kiosk_800773/shop/buy-iphone/iphone-duo/iphoneduo_gsm",
        "priceSourceName": "Apple 中国大陆官网·iPhone Duo 购买页",
        "announcementSource": "https://www.apple.com.cn/shop/iphone",
        "selling": "苹果首款折叠屏：7.6 英寸内屏 + 5.4 英寸外屏，A20 Pro",
        "bestFor": ["大屏办公", "拍照视频", "苹果生态"],
        "storageOptions": ["256GB", "512GB", "1TB", "2TB"],
        "quoteTargetStorage": "256GB",
        "zol": ("2178", "2177309"),
        "official": "https://www.apple.com.cn/iphone-duo/specs/",
        "officialFields": ["display", "battery", "charging", "camera", "weight"],
        "overrides": {"display": "7.6 英寸内屏 + 5.4 英寸外屏 · 1–120Hz",
                      "battery": "官方未公布 mAh；视频播放内屏 31 小时 / 外屏 44 小时",
                      "charging": "60W 有线（约 20 分钟充至 50%）/ MagSafe 15W",
                      "weight": "254g", "os": "iOS 27",
                      "camera": "4800 万融合式主摄 + 4800 万超广角（无长焦，支持 2 倍光学品质变焦）"},
        "notes": [
            "10 月 16 日晚 8 点预购、10 月 23 日发售；256GB 15999 元起，均来自 Apple 中国大陆官网。",
            "屏幕尺寸、芯片、充电、续航按 Apple 技术规格页填写（官网为准）；ZOL 参数页缺屏幕尺寸与系统两项。",
            "仅支持双 eSIM，不兼容实体 SIM 卡。",
        ],
    },
    # ---------------- 2026-04 ----------------
    {
        "id": "hua-pura90", "brand": "Huawei", "name": "HUAWEI Pura 90",
        "type": "影像旗舰", "launchMonth": "2026-04", "launchDateDisplay": "2026年04月29日",
        "priceCN": 4699, "priceType": "official_launch_msrp",
        "priceText": "官方起售价（12GB+256GB）；16GB+512GB 5699 元",
        "priceSource": "https://consumer.huawei.com/cn/press/events/2026/huawei-pura-90-series-and-new-product-launch-event",
        "priceSourceName": "华为官网·Pura 90 系列发布会页",
        "announcementSource": "https://www.cnii.com.cn/rmydb/202604/t20260420_731175.html",
        "selling": "麒麟 9010S + 红枫影像，6500mAh 大电池",
        "bestFor": ["拍照视频", "日常全能", "续航"],
        "storageOptions": ["12GB+256GB", "12GB+512GB", "16GB+512GB"],
        "quoteTargetStorage": "12GB+256GB",
        "zol": ("2163", "2162693"),
        "overrides": {"display": "6.8 英寸 OLED · 1–120Hz",
                      "charging": "100W 有线 / 50W 无线", "os": "HarmonyOS 6.1"},
        "notes": [
            "4 月 20 日发布、4 月 29 日 10:08 开售；4699 元起，华为官网发布会页与科技日报、中国工信新闻网一致。",
            "ZOL 参数页未列「上市日期」，只有「国内发布时间」，开售日取发布会口径。",
        ],
    },
    # ---------------- 2026-09 ----------------
    {
        "id": "hua-matext2", "brand": "Huawei", "name": "HUAWEI Mate XT 2 非凡大师",
        "type": "折叠屏旗舰", "launchMonth": "2026-09", "launchDateDisplay": "2026年09月07日",
        "priceCN": 19999, "priceType": "official_launch_msrp",
        "priceText": "官方起售价（16GB+256GB）；512GB 21999 / 1TB 23999",
        "priceSource": "https://www.toutiao.com/article/7684546614664413732",
        "priceSourceName": "湖南日报转财联社·Mate XT 2 首销报道（含各版本价目）",
        "announcementSource": "https://www.vmall.com/",
        "selling": "华为第二代三折叠，10.2 英寸内屏 + 麒麟 9050 Pro",
        "bestFor": ["大屏办公", "拍照视频", "日常全能"],
        "storageOptions": ["16GB+256GB", "16GB+512GB", "16GB+1TB"],
        "quoteTargetStorage": "16GB+512GB",
        "zol": ("2177", "2176798"),
        "overrides": {"display": "10.2 英寸三折叠 LTPO · 1–120Hz",
                      "os": "HarmonyOS（版本以官方为准）"},
        "notes": [
            "定价 19999 元起、9 月 12 日 10:08 首销，来自湖南日报转财联社报道；华为商城同期标价与之一致。",
            "ZOL 参数页未列屏幕尺寸与系统版本：屏幕尺寸取华为商城商品页（10.2 英寸），系统版本未标注具体号，按“以官方为准”填写。",
        ],
    },
    {
        "id": "xia-18pm", "brand": "Xiaomi", "name": "Xiaomi 18 Pro Max",
        "type": "影像旗舰", "launchMonth": "2026-09", "launchDateDisplay": "2026年09月23日",
        "priceCN": 6999, "priceType": "official_launch_msrp",
        "priceText": "官方起售价（12GB+256GB）；16GB+1TB 9999 元，透明特别版 10999 元",
        "priceSource": "https://www3.xinhuanet.com/tech/20260924/1dcd469b76984a5b946abcb6f92508bf/c.html",
        "priceSourceName": "新华网·小米 2026 秋季发布会报道",
        "announcementSource": "https://cn.chinadaily.com.cn/a/202609/24/WS6ab4d214e4b09a165c78c885.html",
        "selling": "双 2 亿像素 + 2.9 英寸 AI 背屏，8500mAh",
        "bestFor": ["拍照视频", "大屏办公", "日常全能"],
        "storageOptions": ["12GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"],
        "quoteTargetStorage": "12GB+256GB",
        "zol": ("2179", "2178755"),
        "overrides": {"display": "6.9 英寸 2K 主屏 + 2.9 英寸背屏 · 120Hz",
                      "charging": "100W 有线 / 50W 无线", "os": "Xiaomi HyperOS 4"},
        "notes": [
            "价格 6999 元起，新华网、北京日报、中国日报三处口径一致；四档价目 6999/7999/8999/9999。",
            "ZOL 参数页把背屏算作「副屏」，本站按官方叫法写成「主屏 + 背屏」。",
        ],
    },
    {
        "id": "iqoo-16", "brand": "iQOO", "name": "iQOO 16",
        "type": "游戏性能旗舰", "launchMonth": "2026-09", "launchDateDisplay": "2026年09月29日",
        "priceCN": 5999, "priceType": "official_launch_msrp",
        "priceText": "官方零售价（12GB+256GB）；国补到手 5499 元起",
        "priceSource": "http://scitech.ce.cn/sy/zx/202609/t20260929_3242409.shtml",
        "priceSourceName": "中国经济网·iQOO 16 发布报道（含四档价格）",
        "announcementSource": "https://www.toutiao.com/article/7690936297904538153/",
        "selling": "2K 165Hz 珠峰屏 + 8400mAh，电竞芯片 Q4",
        "bestFor": ["游戏性能", "续航", "日常全能"],
        "storageOptions": ["12GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"],
        "quoteTargetStorage": "12GB+256GB",
        "zol": ("2179", "2178849"),
        "overrides": {"display": "6.85 英寸 2K AMOLED · 165Hz",
                      "charging": "100W 有线 / 40W 无线", "os": "OriginOS 7"},
        "notes": [
            "5999/6799/7499/8499 四档零售价，中国经济网、IT之家、中关村在线报道一致；国补后 5499 元起。",
            "首发第六代骁龙 8 超级至尊版 + 自研 Q4 电竞芯片，定位游戏向旗舰。",
        ],
    },
    # ---------------- 2026-06 ----------------
    {
        "id": "vivo-xfold6", "brand": "vivo", "name": "vivo X Fold6",
        "type": "折叠屏旗舰", "launchMonth": "2026-06", "launchDateDisplay": "2026年06月26日",
        "priceCN": 7999, "priceType": "official_launch_msrp",
        "priceText": "官方建议零售价（12GB+256GB）；16GB+1TB 10999 元",
        "priceSource": "https://www.vivo.com.cn/vivo/param/xfold6",
        "priceSourceName": "vivo 官网·X Fold6 参数与建议零售价",
        "announcementSource": "https://m.vivo.com.cn/brand/news/detail?id=1369",
        "selling": "8.02 英寸内屏 + 天玑 9500 超能版，7000mAh",
        "bestFor": ["大屏办公", "拍照视频", "续航"],
        "storageOptions": ["12GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"],
        "quoteTargetStorage": "12GB+256GB",
        "zol": ("2171", "2170555"),
        "official": "https://www.vivo.com.cn/vivo/param/xfold6",
        "officialFields": ["display", "battery", "charging", "storage"],
        "overrides": {"display": "主 8.02 英寸 + 副 6.51 英寸 · AMOLED · 120Hz",
                      "charging": "80W 有线 / 40W 无线", "os": "OriginOS 6 Fold"},
        "notes": [
            "四档价格 7999/8999/9999/10999 来自 vivo 官网参数页（建议零售价），与发布会报道一致。",
            "6 月 26 日发布、7 月 1 日开售；ZOL 参数页发布时间一致。",
        ],
    },
    {
        "id": "hua-nova16", "brand": "Huawei", "name": "HUAWEI nova 16",
        "type": "标准旗舰", "launchMonth": "2026-06", "launchDateDisplay": "2026年06月05日",
        "priceCN": 2999, "priceType": "official_launch_msrp",
        "priceText": "官方首发起售价（256GB）；512GB 3499 元（2026-10 调价后 3399 元起）",
        "priceSource": "https://consumer.huawei.com/cn/press/events/2026/nova-16-series-and-all-scenario-new-product-launch-event",
        "priceSourceName": "华为官网·nova 16 系列发布会页",
        "announcementSource": "https://dzrb.dzng.com/general/0/NEWS3426420ZQXVSYBBIHKCK",
        "selling": "麒麟 9010S + 7000mAh，同档少见的 5000 万潜望长焦",
        "bestFor": ["拍照视频", "日常全能", "性价比"],
        "storageOptions": ["256GB", "512GB"],
        "quoteTargetStorage": "256GB",
        "zol": ("2168", "2167426"),
        "overrides": {"display": "6.68 英寸 OLED · 120Hz",
                      "charging": "100W 有线", "os": "HarmonyOS 6.1"},
        "notes": [
            "首发 2999/3499 元（256GB/512GB），华为官网发布会页与齐鲁晚报、中国基金报一致。",
            "2026-10-09 华为上调在售机型指导价，nova 16 现为 3399 元起；本站记录的是首发价。",
            "ZOL 参数页未列运行内存，容量组合按 ROM 记录。",
        ],
    },
    # ---------------- 2025-10 ----------------
    {
        "id": "realme-gt8", "brand": "realme", "name": "真我 GT8",
        "type": "性能旗舰", "year": 2025, "launchMonth": "2025-10", "launchDateDisplay": "2025年10月21日",
        "priceCN": 2899, "priceType": "official_launch_msrp",
        "priceText": "官方首发起售价（12GB+256GB）；16GB+1TB 4099 元",
        "priceSource": "https://tech.ifeng.com/c/8ndO0euK7HM",
        "priceSourceName": "凤凰网科技·真我 GT8 系列发布（含五档价目）",
        "announcementSource": "https://www.toutiao.com/article/7563929910687875636",
        "selling": "理光 GR 影像 + 骁龙 8 Elite，7000mAh",
        "bestFor": ["性价比", "游戏性能", "日常全能"],
        "storageOptions": ["12GB+256GB", "16GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"],
        "quoteTargetStorage": "12GB+256GB",
        "zol": ("2146", "2145216"),
        "overrides": {"display": "6.79 英寸 AMOLED · 144Hz",
                      "charging": "100W 有线", "os": "realme UI 6.0"},
        "notes": [
            "2899 元起（12GB+256GB），凤凰网、网易、真我社区三处价目一致。",
            "该机 2025 年 10 月发布，此前库里只有 GT8 Pro，本次补齐标准版。",
        ],
    },
    # ---------------- 2026-08 ----------------
    {
        "id": "redmi-k100-pro", "brand": "Xiaomi", "name": "REDMI K100 Pro",
        "type": "性能旗舰", "launchMonth": "2026-08", "launchDateDisplay": "2026年08月11日",
        "priceCN": 3999, "priceType": "official_launch_msrp",
        "priceText": "官方建议零售价（12GB+256GB）；首销 3699 元，国补 3199 元",
        "priceSource": "https://m.ithome.com/html/988472.htm",
        "priceSourceName": "IT之家·REDMI K100 Pro 系列发布（含全系价目表）",
        "announcementSource": "https://www.antutu.com/doc/137466.htm",
        "selling": "8580mAh + 100W，185Hz 直屏与 2 亿像素主摄",
        "bestFor": ["游戏性能", "性价比", "续航"],
        "storageOptions": ["12GB+256GB", "16GB+256GB", "12GB+512GB", "16GB+512GB"],
        "quoteTargetStorage": "12GB+256GB",
        "zol": ("2174", "2173757"),
        "overrides": {"charging": "100W 有线 / 50W 无线", "os": "Xiaomi HyperOS 3"},
        "notes": [
            "价格为 8 月 11 日发布会建议零售价，IT之家、安兔兔、北京商报三处口径一致。",
            "该机 8 月发布、此前未入库，本次作为补齐机型加入。",
        ],
    },
    # ---------------- 2024 及更早的补齐机型可继续往下列 ----------------
]


def build(meta: dict) -> dict:
    url = ZOL_SRC.format(*meta["zol"])
    specs = parse_specs(fetch(url))
    d = derive(specs)
    field_count = sum(len(g["items"]) for g in specs)
    overrides = meta.get("overrides", {})

    def val(key: str, fallback: str = "") -> str:
        return overrides.get(key) or d.get(key) or fallback

    official_fields = set(meta.get("officialFields", []))
    os_value = overrides.get("os") or d.get("os") or "以官方规格页为准"
    audit = []
    for key, label in (("display", "屏幕"), ("chip", "处理器"), ("camera", "影像"),
                       ("battery", "电池"), ("charging", "充电"), ("weight", "重量"),
                       ("storage", "容量组合")):
        v = val(key)
        if not v:
            continue
        audit.append({
            "field": label, "value": v, "valueAtAudit": v,
            "status": "verified_official_page_reviewed" if key in official_fields
                      else "cross_checked_secondary_source",
            "sourceUrl": (meta.get("official") if key in official_fields else url),
            "evidenceText": f"参数表/官方页：{label} {v}",
            "note": f"{TODAY} 新增机型时按来源填写；参数站与官方页有冲突时以官方页为准。",
        })
    audit.append({
        "field": "正式发布/开售日期", "value": meta["launchDateDisplay"],
        "valueAtAudit": meta["launchDateDisplay"], "status": "cross_checked_secondary_source",
        "sourceUrl": meta["announcementSource"],
        "evidenceText": f"发布会/官网信息：{meta['launchDateDisplay']}",
        "note": f"{TODAY} 新增机型时按发布会报道与官网信息填写。",
    })

    rec = {
        "id": meta["id"], "brand": meta["brand"], "name": meta["name"],
        "year": meta.get("year", 2026),
        "type": meta["type"], "market": "中国大陆正式销售",
        "display": val("display", "以官方规格页为准"),
        "chip": val("chip", "以官方规格页为准"),
        "camera": val("camera", "以官方规格页为准"),
        "battery": val("battery", "以官方规格页为准"),
        "charging": val("charging", "以官方规格页为准"),
        "weight": val("weight", "以官方规格页为准"),
        "storage": " / ".join(meta["storageOptions"]),
        "os": os_value,
        "priceCN": meta["priceCN"], "priceText": meta["priceText"],
        "selling": meta["selling"], "bestFor": meta["bestFor"],
        "source": meta.get("official") or url,
        "sourceName": "厂商官方规格页" if meta.get("official") else "中关村在线参数页（第三方核验）",
        "verified": bool(meta.get("official")),
        "launchMonth": meta["launchMonth"], "launchDateDisplay": meta["launchDateDisplay"],
        "priceType": meta["priceType"],
        "livePrice": None, "livePriceStatus": "not_connected", "livePriceCheckedAt": None,
        "storageOptions": meta["storageOptions"], "chinaOfficial": True,
        "dataNote": "参数来自中关村在线参数页；首发价与开售时间来自官方页/发布会报道，均标注来源",
        "announcementSource": meta["announcementSource"],
        "priceSource": meta["priceSource"], "priceSourceName": meta["priceSourceName"],
        "livePriceNote": "尚未接入获授权的实时渠道报价 API；请通过渠道入口核价",
        "scoreMethod": "heuristic_preliminary",
        "quoteTargetStorage": meta["quoteTargetStorage"],
        "quoteTargetStorageReason": "报价检索只接受商品标题中可核验的型号与这一指定大陆版 RAM/ROM 组合；无法匹配就不显示价格。",
        "auditStatus": "needs_parameter_price_audit",
        "auditNotes": [f"{TODAY} 新增机型：{field_count} 项参数（中关村在线，标题比对通过）"] + meta["notes"],
        "priceAuditStatus": "official_source_present" if meta.get("official") else "source_present_needs_crosscheck",
        "parameterAuditStatus": "partial",
        "specSource": url, "specSourceName": "中关村在线参数页（第三方核验）",
        "specFieldCount": field_count, "specCollectedAt": TODAY,
        "specs": specs, "fieldAudit": audit,
    }
    if meta.get("official"):
        rec["officialSpecSource"] = meta["official"]
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="已存在的机型也按最新来源重建")
    args = ap.parse_args()
    catalog: list[dict] = json.loads(CATALOG.read_text(encoding="utf-8"))
    index = {p["id"]: i for i, p in enumerate(catalog)}
    added = refreshed = 0
    for meta in NEW:
        if meta["id"] in index and not args.refresh:
            print(f"skip existing: {meta['id']}")
            continue
        rec = build(meta)
        if meta["id"] in index:
            catalog[index[meta["id"]]] = rec
            refreshed += 1
            print(f"refresh {rec['id']}: {rec['name']} | {rec['specFieldCount']} specs")
        else:
            catalog.append(rec)
            added += 1
            print(f"added {rec['id']}: {rec['name']} | {rec['specFieldCount']} specs | ¥{rec['priceCN']}")
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    back = json.loads(CATALOG.read_text(encoding="utf-8"))
    print(f"added {added}, refreshed {refreshed}, catalog now {len(back)} records")
    for f in [ROOT / "index.html", ROOT / "phone-compare-demo.html"]:
        patch_html(f, back, strict=False)


if __name__ == "__main__":
    main()
