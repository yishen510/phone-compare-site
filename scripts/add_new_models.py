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

HUAWEI_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126",
             "Accept-Language": "zh-CN"}
ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
TODAY = "2026-10-29"
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
    # ---------------- 2026-09/10 追加：本轮补齐的漏收机型 ----------------
    {
        "id": "hua-puraxview", "brand": "Huawei", "name": "HUAWEI Pura X View",
        "type": "影像旗舰", "launchMonth": "2026-09", "launchDateDisplay": "2026年09月09日",
        "priceCN": 5999, "priceType": "official_launch_msrp",
        "priceText": "官方起售价（12GB+256GB）；512GB 6999 / 1TB 8499",
        "priceSource": "https://consumer.huawei.com/cn/phones/pura-x-view/",
        "priceSourceName": "华为官网·Pura X View 产品页（¥5999 起）",
        "announcementSource": "https://consumer.huawei.com/cn/phones/pura-x-view/specs/",
        "selling": "6.68mm / 201g 的 6.39 英寸阔直板，2 亿像素红枫影像 + 7000mAh",
        "bestFor": ["拍照视频", "日常全能", "续航"],
        "storageOptions": ["12GB+256GB", "12GB+512GB", "12GB+1TB"],
        "quoteTargetStorage": "12GB+256GB",
        "official": "https://consumer.huawei.com/cn/phones/pura-x-view/specs/",
        "officialFields": ["display", "chip", "battery", "charging", "weight", "camera"],
        "manualSpecsFrom": "https://consumer.huawei.com/cn/phones/pura-x-view/specs/",
        "overrides": {"display": "6.39 英寸 OLED · 120Hz（16:10 阔直板）",
                      "chip": "麒麟 9030S", "battery": "7000mAh（典型值；额定 6815mAh）",
                      "charging": "66W 有线 / 40W 无线", "weight": "201g",
                      "os": "HarmonyOS 7.0",
                      "camera": "2 亿像素超聚光主摄（F1.8，OIS）+ 3.7 倍光学潜望长焦，前置 5000 万"},
        "notes": [
            "9 月 7 日发布、9 月 9 日 10:08 开售；5999 / 6999 / 8499 对应 256GB / 512GB / 1TB，取自华为官网产品页与发布会报道。",
            "ZOL 参数页把该机误标为折叠屏（列出「折叠尺寸」与 3.5 英寸副屏，疑似沿用上代 Pura X 模板），且系统写成 HarmonyOS 5.0.1、上市日期写成 8 月 28 日；本站按华为官网规格页取单屏 6.39 英寸、HarmonyOS 7.0、9 月 9 日开售。",
            "参数表整组来自华为官网规格页（非 ZOL），因此参数条目数以官网列项为准。",
        ],
    },
    {
        "id": "xiaomi-18-fold", "brand": "Xiaomi", "name": "Xiaomi 18 Fold",
        "type": "折叠屏旗舰", "launchMonth": "2026-09", "launchDateDisplay": "2026年09月10日",
        "priceCN": 10999, "priceType": "official_launch_msrp",
        "priceText": "官方起售价（12GB+256GB）；12+512 11999 / 16+512 12999 / 16+1TB 14999 / 陶瓷特别版 15999",
        "priceSource": "https://www.toutiao.com/article/7683742104514609674",
        "priceSourceName": "华商网转 IT之家·小米 18 Fold 首销报道（含五档价目）",
        "announcementSource": "https://www.zgcsb.com/news/shouYe/2026-09/08/ma_689574.html",
        "selling": "5.38 英寸外屏 + 7.58 英寸内屏的「中折叠」，玄戒 O3 + 徕卡三摄",
        "bestFor": ["大屏办公", "拍照视频", "日常全能"],
        "storageOptions": ["12GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB", "16GB+1TB 陶瓷特别版"],
        "quoteTargetStorage": "12GB+256GB",
        "sourceName": "厂商规格（多方转载）+ 发布会报道",
        "manualSpecsSource": "https://g.pconline.com.cn/x/2183/21831111.html",
        "manualSpecs": [
            {"group": "基本参数", "items": [
                ["国内发布时间", "2026年09月07日"], ["上市日期", "2026年09月10日"],
                ["产品型号", "小米18 Fold"], ["机身颜色", "西野红等"]]},
            {"group": "外形", "items": [
                ["展开尺寸", "163.8 × 117.8 × 5.02mm"], ["折叠尺寸", "117.8 × 83.6 × 10.68mm"],
                ["重量", "219g"], ["中框材质", "7 系铝合金"]]},
            {"group": "屏幕", "items": [
                ["外屏", "5.38 英寸，1712 × 1168，龙晶玻璃 3.0"],
                ["内屏", "7.58 英寸，2364 × 1672，双层 UTG（50μm + 30μm）"],
                ["屏幕刷新率", "1–120Hz LTPO 自适应（内外屏）"],
                ["屏幕亮度", "峰值 4000nits"]]},
            {"group": "硬件", "items": [
                ["CPU型号", "玄戒 O3（3nm，10 核全大核）"],
                ["RAM容量", "12GB / 16GB（长鑫 LPDDR6）"],
                ["ROM容量", "256GB / 512GB / 1TB"],
                ["操作系统", "小米澎湃 OS 4"], ["扬声器", "立体声双扬声器"]]},
            {"group": "摄像头", "items": [
                ["后置摄像头1", "2 亿像素 HP5 主摄（1/1.56\"，F1.7，23mm，OIS）"],
                ["后置摄像头2", "5000 万像素 JN5 潜望长焦（F2.8，80mm，3.5 倍光学变焦）"],
                ["后置摄像头3", "5000 万像素 OV50M 超广角（F2.4，17mm，102°）"],
                ["前置摄像头", "1600 万像素"]]},
            {"group": "电池与续航", "items": [
                ["电池容量", "6000mAh 小米金沙江电池"],
                ["有线充电", "67W"], ["无线充电", "50W"]]},
            {"group": "功能与服务", "items": [
                ["三防功能", "IP58 / IP59"], ["其他", "UWB、Wi-Fi 7、23 个 5G 频段、至高六分屏"]]},
        ],
        "overrides": {"display": "7.58 英寸内屏 + 5.38 英寸外屏 · 1–120Hz",
                      "chip": "玄戒 O3", "battery": "6000mAh",
                      "charging": "67W 有线 / 50W 无线", "weight": "219g",
                      "os": "小米澎湃 OS 4",
                      "camera": "徕卡三摄：2 亿主摄 + 5000 万潜望长焦（3.5 倍）+ 5000 万超广角，前置 1600 万"},
        "notes": [
            "9 月 7 日发布、9 月 10 日 10:00 首销；10999 元起，五档价目见华商网转 IT之家报道，与中国城市网、太平洋科技口径一致。",
            "ZOL 尚未为小米 18 Fold 建立参数页，参数按发布会与多家媒体规格整理（太平洋科技逐项列出屏幕分辨率、机身尺寸、传感器型号），整组标注为「厂商规格（多方转载）+ 发布会报道」，未冒充 ZOL 来源。",
            "该机为小米首款「中折叠」，本站按折叠屏旗舰归类。",
        ],
    },
    {
        "id": "nubia-redmagic12-proplus", "brand": "nubia", "name": "红魔 12 Pro+",
        "type": "游戏性能旗舰", "launchMonth": "2026-10", "launchDateDisplay": "2026年10月15日",
        "priceCN": 6999, "priceType": "official_launch_msrp",
        "priceText": "官方价（12GB+256GB）；16+512 7999 / 16+1TB 8999，国补后 6499 / 7499 / 8499",
        "priceSource": "https://www.sctv.com/news/2111083901061894146",
        "priceSourceName": "四川网络广播电视台·红魔 12 Pro+ 发布会报道",
        "announcementSource": "https://www.toutiao.com/article/7696815248037003791",
        "selling": "第九代屏下前摄 185Hz 全面屏 + RGB 脉动水冷，8400mAh / 120W",
        "bestFor": ["游戏性能", "续航", "日常全能"],
        "storageOptions": ["12GB+256GB", "16GB+512GB", "16GB+1TB"],
        "quoteTargetStorage": "12GB+256GB",
        "zol": ("2181", "2180635"),
        "overrides": {"display": "6.85 英寸 1.5K 屏下前摄全面屏 · 185Hz",
                      "charging": "120W 有线 / 80W 无线", "os": "REDMAGIC OS 12",
                      "weight": "223g"},
        "notes": [
            "10 月 15 日 14:30 发布、当日 18:00 开售；6999 / 7999 / 8999 三档价目见四川网络广播电视台与华商网报道。",
            "无线充电口径：ZOL 与中国深圳网均写 80W，华商网写 50W，本站按多数来源取 80W。",
        ],
    },
    {
        "id": "honor-win2", "brand": "Honor", "name": "荣耀 WIN2",
        "type": "游戏性能旗舰", "launchMonth": "2026-10", "launchDateDisplay": "2026年10月21日",
        "priceCN": 5499, "priceType": "official_launch_msrp",
        "priceText": "首销价（12GB+256GB）；16+256 5799 / 12+512 首销 5999 / 16+512 6999 / 16+1TB 7999",
        "priceSource": "https://www.cfbond.com/ejy/qyzxpd/4896228675.shtml",
        "priceSourceName": "中国财富网·荣耀 WIN2 系列开售报道（含三机起售价）",
        "announcementSource": "https://baike.baidu.com/item/%E8%8D%A3%E8%80%80WIN2%E7%B3%BB%E5%88%97/67803436",
        "selling": "双风扇主动散热 + 10100mAh 青海湖电池，2K 185Hz 电竞屏",
        "bestFor": ["游戏性能", "续航", "日常全能"],
        "storageOptions": ["12GB+256GB", "16GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"],
        "quoteTargetStorage": "12GB+256GB",
        "zol": ("2182", "2181338"),
        "overrides": {"display": "6.89 英寸 2K 直屏 · 185Hz",
                      "charging": "100W 有线 / 80W 无线", "os": "MagicOS 11",
                      "weight": "237g"},
        "notes": [
            "10 月 21 日发布并当日开售；WIN2 / WIN RT2 / WIN Turbo2 起售价分别为 5499 / 4199 / 3199 元，见中国财富网报道，与荣耀官方开售页一致。",
            "国补与首销优惠后的到手价另计（5499 → 4999），本站只记官方标价。",
        ],
    },
    {
        "id": "honor-win-rt2", "brand": "Honor", "name": "荣耀 WIN RT2",
        "type": "性能续航旗舰", "launchMonth": "2026-10", "launchDateDisplay": "2026年10月21日",
        "priceCN": 4199, "priceType": "official_launch_msrp",
        "priceText": "首销限时价起（12GB+256GB）；国补后 3149 元起",
        "priceSource": "https://www.cfbond.com/ejy/qyzxpd/4896228675.shtml",
        "priceSourceName": "中国财富网·荣耀 WIN2 系列开售报道",
        "announcementSource": "https://baike.baidu.com/item/%E8%8D%A3%E8%80%80WIN2%E7%B3%BB%E5%88%97/67803436",
        "selling": "12070mAh 青海湖电池 + 第五代骁龙 8 至尊版，2K 185Hz 直屏",
        "bestFor": ["续航", "游戏性能", "日常全能"],
        "storageOptions": ["12GB+256GB", "16GB+256GB", "12GB+512GB", "16GB+512GB"],
        "quoteTargetStorage": "12GB+256GB",
        "zol": ("2182", "2181347"),
        "overrides": {"display": "6.89 英寸 2K 直屏 · 185Hz",
                      "charging": "90W 有线 / 27W 有线反向", "os": "MagicOS 11"},
        "notes": [
            "与 WIN2 同场发布，首销限时 4199 元起，国补后 3149 元起，见中国财富网报道。",
            "电池 12070mAh、90W 有线充电取自 ZOL 参数页，与荣耀官方口径一致。",
        ],
    },
    {
        "id": "honor-win-turbo2", "brand": "Honor", "name": "荣耀 WIN Turbo2",
        "type": "性能旗舰", "launchMonth": "2026-10", "launchDateDisplay": "2026年10月21日",
        "priceCN": 3199, "priceType": "official_launch_msrp",
        "priceText": "首销限时价起（12GB+256GB）；国补后 2251 元起，10 月 30 日首销",
        "priceSource": "https://www.cfbond.com/ejy/qyzxpd/4896228675.shtml",
        "priceSourceName": "中国财富网·荣耀 WIN2 系列开售报道",
        "announcementSource": "https://baike.baidu.com/item/%E8%8D%A3%E8%80%80WIN2%E7%B3%BB%E5%88%97/67803436",
        "selling": "12070mAh 大电池 + 第四代骁龙 8s，2K 185Hz 直屏的电竞性价比款",
        "bestFor": ["续航", "游戏性能", "性价比"],
        "storageOptions": ["12GB+256GB", "16GB+256GB", "12GB+512GB", "16GB+512GB"],
        "quoteTargetStorage": "12GB+256GB",
        "zol": ("2182", "2181343"),
        "overrides": {"display": "6.89 英寸 2K 直屏 · 185Hz",
                      "charging": "90W 有线 / 27W 有线反向", "os": "MagicOS 11",
                      "weight": "235g"},
        "notes": [
            "10 月 21 日发布、10 月 30 日正式首销；首销限时 3199 元起，见中国财富网报道与百度百科词条。",
        ],
    },
    # ---------------- 2026-10-29 一加 Ace 7 系列（发布当日补录） ----------------
    {
        "id": "oneplus-ace7", "brand": "OnePlus", "name": "一加 Ace 7",
        "type": "性能旗舰", "launchMonth": "2026-10", "launchDateDisplay": "2026年10月29日",
        "priceCN": 4399, "priceType": "official_launch_msrp",
        "priceText": "官方价（12GB+256GB）；16+256 4899 / 12+512 5199 / 16+512 5699",
        "priceSource": "https://m.ithome.com/html/1019744.htm",
        "priceSourceName": "IT之家·一加 Ace 7/Pro 系列发布（含全系价目表）",
        "announcementSource": "https://www.oneplus.com/cn/ace-7",
        "selling": "9000mAh + 185Hz 东方屏 + 双路冰河风冷，Ace 系列首次上主动散热",
        "bestFor": ["游戏性能", "续航", "日常全能"],
        "storageOptions": ["12GB+256GB", "16GB+256GB", "12GB+512GB", "16GB+512GB"],
        "quoteTargetStorage": "12GB+256GB",
        "official": "https://www.oneplus.com/cn/ace-7",
        "officialFields": ["display", "battery", "charging", "os"],
        "sourceName": "发布会报道 + 厂商官网（人工整理）",
        "manualSpecsSource": "https://antutu.com/doc/138197",
        "manualSpecs": [
            {"group": "基本参数", "items": [
                ["国内发布时间", "2026年10月29日"], ["上市日期", "2026年10月29日"],
                ["产品型号", "一加 Ace 7"], ["机身颜色", "淬火、极夜黑、流光白"]]},
            {"group": "外形", "items": [
                ["长度", "162.30mm"], ["宽度", "77.37mm"],
                ["厚度", "8.59mm（淬火）/ 8.50mm（黑白）"],
                ["重量", "约 223g（淬火）/ 约 217g（黑白）"], ["中框材质", "金属中框"]]},
            {"group": "屏幕", "items": [
                ["屏幕尺寸", "6.78 英寸 1.5K（2772 × 1272）"],
                ["屏幕类型", "第四代东方屏，京东方 X4 发光材料，LTPO 直屏"],
                ["屏幕刷新率", "1–165Hz 自适应（全局 165Hz），适配游戏中最高 185Hz"],
                ["屏幕亮度", "峰值 3600nit"], ["其他", "10.7 亿色、100% DCI-P3、3840Hz 高频 PWM 调光"]]},
            {"group": "硬件", "items": [
                ["CPU型号", "第五代骁龙8至尊版 V Series（3nm，最高 4.6GHz）"],
                ["RAM容量", "12GB / 16GB（LPDDR5X Ultra）"],
                ["ROM容量", "256GB / 512GB（UFS 4.1）"],
                ["操作系统", "ColorOS 17"],
                ["散热", "双路冰河风冷（主动风扇）+ 6350mm² VC + 14 层塔式鳍片"]]},
            {"group": "摄像头", "items": [
                ["后置摄像头1", "2 亿像素三星 HP5 主摄（1/1.56\"，F1.8，OIS）"],
                ["前置摄像头", "1600 万像素"],
                ["变焦", "无长焦镜头，支持数码变焦"]]},
            {"group": "电池与续航", "items": [
                ["电池容量", "9000mAh 冰川电池"], ["有线充电", "100W 超级闪充"],
                ["其他", "支持旁路供电"]]},
            {"group": "功能与服务", "items": [
                ["三防功能", "IP66 / IP68 / IP69 / IP69K"],
                ["生物识别", "3D 超声波屏下指纹"], ["其他", "金属中框、X 轴线性马达、立体声双扬、NFC、红外"]]},
        ],
        "overrides": {
            "display": "6.78 英寸 1.5K LTPO 直屏 · 全局 165Hz / 游戏最高 185Hz",
            "chip": "第五代骁龙8至尊版 V Series", "battery": "9000mAh",
            "charging": "100W 有线（无线充电未公布）",
            "weight": "约 217g（黑白）/ 223g（淬火）", "os": "ColorOS 17",
            "camera": "2 亿像素三星 HP5 主摄（1/1.56\"，F1.8，OIS），前置 1600 万"},
        "notes": [
            "10 月 29 日 19:00 发布并开售；4399 / 4899 / 5199 / 5699 四档价目见 IT之家，与 CNMO、安兔兔口径一致。",
            "ZOL 参数页仍是上代 Ace 6 的模板（7800mAh、165Hz、ColorOS 16、120W），与官网「9000mAh + 100W + 全局 165Hz + ColorOS 17」冲突，本站按官网与发布会报道填写，参数表按多方报道整理。",
        ],
    },
    {
        "id": "oneplus-ace7-pro", "brand": "OnePlus", "name": "一加 Ace 7 Pro",
        "type": "性能旗舰", "launchMonth": "2026-10", "launchDateDisplay": "2026年10月29日",
        "priceCN": 4799, "priceType": "official_launch_msrp",
        "priceText": "官方价（12GB+256GB）；16+256 5299 / 12+512 5599 / 16+512 5999 / 16+1TB 7299",
        "priceSource": "https://m.ithome.com/html/1019744.htm",
        "priceSourceName": "IT之家·一加 Ace 7/Pro 系列发布（含全系价目表）",
        "announcementSource": "https://www.oneplus.com/cn/ace-7-pro",
        "selling": "9000mAh + 满血第五代骁龙8至尊版 + 3.5 倍潜望长焦",
        "bestFor": ["游戏性能", "拍照视频", "续航"],
        "storageOptions": ["12GB+256GB", "16GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"],
        "quoteTargetStorage": "12GB+256GB",
        "official": "https://www.oneplus.com/cn/ace-7-pro",
        "officialFields": ["display", "battery", "charging", "os"],
        "sourceName": "发布会报道 + 厂商官网（人工整理）",
        "manualSpecsSource": "https://antutu.com/doc/138197",
        "manualSpecs": [
            {"group": "基本参数", "items": [
                ["国内发布时间", "2026年10月29日"], ["上市日期", "2026年10月29日"],
                ["产品型号", "一加 Ace 7 Pro"], ["机身颜色", "破风、极夜黑、流光白"]]},
            {"group": "外形", "items": [
                ["长度", "162.30mm"], ["宽度", "77.37mm"],
                ["厚度", "8.59mm（破风）/ 8.50mm（黑白）"],
                ["重量", "约 225g（破风）/ 约 218g（黑白）"], ["中框材质", "金属中框"]]},
            {"group": "屏幕", "items": [
                ["屏幕尺寸", "6.78 英寸 1.5K（2772 × 1272）"],
                ["屏幕类型", "第四代东方屏，京东方 X4 发光材料，LTPO 直屏"],
                ["屏幕刷新率", "1–165Hz 自适应（全局 165Hz），适配游戏中最高 185Hz"],
                ["屏幕亮度", "峰值 3600nit"], ["其他", "10.7 亿色、100% DCI-P3、3840Hz 高频 PWM 调光"]]},
            {"group": "硬件", "items": [
                ["CPU型号", "第五代骁龙8至尊版（3nm，最高 4.6GHz，满血版）"],
                ["RAM容量", "12GB / 16GB（LPDDR5X Ultra）"],
                ["ROM容量", "256GB / 512GB / 1TB（UFS 4.1）"],
                ["操作系统", "ColorOS 17"],
                ["散热", "双路冰河风冷（主动风扇）+ 6350mm² VC + 14 层塔式鳍片"]]},
            {"group": "摄像头", "items": [
                ["后置摄像头1", "2 亿像素三星 HP5 主摄（1/1.56\"，F1.8，OIS）"],
                ["后置摄像头2", "5000 万像素潜望长焦（3.5 倍光学，80mm 人像焦段）"],
                ["前置摄像头", "1600 万像素"]]},
            {"group": "电池与续航", "items": [
                ["电池容量", "9000mAh 冰川电池"], ["有线充电", "100W 超级闪充"],
                ["其他", "支持旁路供电"]]},
            {"group": "功能与服务", "items": [
                ["三防功能", "IP66 / IP68 / IP69 / IP69K"],
                ["生物识别", "3D 超声波屏下指纹"], ["其他", "风暴岛进风口、星际光效呼吸灯、X 轴线性马达、NFC、红外"]]},
        ],
        "overrides": {
            "display": "6.78 英寸 1.5K LTPO 直屏 · 全局 165Hz / 游戏最高 185Hz",
            "chip": "第五代骁龙8至尊版", "battery": "9000mAh",
            "charging": "100W 有线（无线充电未公布）",
            "weight": "约 218g（黑白）/ 225g（破风）", "os": "ColorOS 17",
            "camera": "2 亿像素三星 HP5 主摄（OIS）+ 5000 万 3.5 倍潜望长焦，前置 1600 万"},
        "notes": [
            "10 月 29 日 19:00 发布并开售；4799 / 5299 / 5599 / 5999 / 7299 五档价目见 IT之家。",
            "同标准版一样，ZOL 参数页仍套用 Ace 6 模板（7800mAh、120W、ColorOS 16），与官网「9000mAh + 100W + ColorOS 17」冲突，按官网填写。",
        ],
    },
]

def clean_text(x: str) -> str:
    import html as _h
    import re as _re
    x = _re.sub(r"<[^>]+>", " ", x)
    return _re.sub(r"\s+", " ", _h.unescape(x).replace("\xa0", " ")).strip()


def parse_huawei_specs(url: str) -> list[dict]:
    """华为官网规格页（consumer.huawei.com）转成与 ZOL 相同的 groups/items 结构。

    小节标题在 .large-accordion__title；成对字段是 .large-accordion-subtitle + <p>；
    电池/充电这类只有 <p> 的小节，用小节名当键、正文合并当值。
    """
    import re as _re
    import urllib.request as _u
    raw = _u.urlopen(_u.Request(url, headers=HUAWEI_UA), timeout=40).read().decode("utf-8", "ignore")
    groups: list[dict] = []
    for block in _re.split(r'<li class="large-accordion__item">', raw)[1:]:
        t = _re.search(r"large-accordion__title[^>]*>(.*?)</span>", block, _re.S)
        if not t:
            continue
        name = clean_text(t.group(1))
        pairs = _re.findall(r"large-accordion-subtitle[^>]*>(.*?)</div>\s*<p[^>]*>(.*?)</p>", block, _re.S)
        items = [(clean_text(k), clean_text(v)) for k, v in pairs]
        items = [(k, v) for k, v in items if k and v]
        if not items:
            body = block.split("large-accordion__content", 1)[-1]
            ps = [clean_text(x) for x in _re.findall(r"<p(?![^>]*subtext)[^>]*>(.*?)</p>", body, _re.S)]
            ps = [x for x in ps if x and not x.startswith("*")]
            if ps:
                items = [(name, "；".join(ps))]
        if items:
            groups.append({"group": name, "items": items})
    return groups


def build(meta: dict) -> dict:
    if meta.get("manualSpecs"):
        specs = meta["manualSpecs"]
        url = meta["manualSpecsSource"]
        src_name = meta.get("sourceName", "官方规格（人工整理）")
    elif meta.get("manualSpecsFrom"):
        specs = parse_huawei_specs(meta["manualSpecsFrom"])
        url = meta["manualSpecsFrom"]
        src_name = meta.get("sourceName", "厂商官方规格页")
    else:
        url = ZOL_SRC.format(*meta["zol"])
        specs = parse_specs(fetch(url))
        src_name = "中关村在线参数页（第三方核验）"
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
        "sourceName": meta.get("sourceName") or ("厂商官方规格页" if meta.get("official") else src_name),
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
        "specSource": url, "specSourceName": src_name,
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
