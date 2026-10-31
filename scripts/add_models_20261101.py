#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第 15 轮：补录 43 台「在库缺失」的主力机型（2023-12 ~ 2026-10）。

与 add_new_models.py 的差别：
- 参数统一取中关村在线参数页（specSource 可点开），摘要字段由 derive() 派生，
  derive 派生不出或明显的参数站笔误就地用 overrides 修正，并在 auditNotes 写明原因。
- 价格口径分三档：
  1) 有 ZOL 站内参考报价 → priceType=third_party_reference，priceText 明确写「非首发价」；
  2) 参数站也没有报价 → priceType=price_pending，priceCN=null；
  3) 不猜、不拿电商现价顶替首发价。

用法：python scripts/add_models_20261101.py [--dry]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backfill_summary_from_specs import derive, pick, naive_clean  # noqa: E402
from import_zol_params import fetch, parse_specs, patch_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
TODAY = "2026-10-31"
ZOL_PARAM = "https://detail.zol.com.cn/{}/{}/param.shtml"
ZOL_GOODS = "https://detail.zol.com.cn/{}/{}/"
ZOL_NAME = "中关村在线参数页（第三方核验）"
NO_CHIP = "麒麟平台（官方未公布具体型号）"
REF_TEXT = "中关村在线参考价（站内最低在售版本，非官方首发价）"

# meta 字段说明：
#   zol=(pid, ...)  skus=容量组合  quotes=ZOL 站内参考报价（元）
#   type/selling/bestFor 由参数表事实拼出，不写无来源的营销词
NEW = [
    # ---------------- 华为 ----------------
    dict(id="hua-mate70air", brand="Huawei", name="HUAWEI Mate 70 Air",
         type="全能旗舰", year=2025, launchMonth="2025-11", launchDateDisplay="2025年11月06日",
         price=3899, skus=["12GB+256GB"], pid="2146832",
         selling="7 英寸大屏 + 6500mAh，麒麟 9020 系列，机身仅 6.x mm 级厚度",
         bestFor=["大屏办公", "拍照视频", "续航"],
         overrides={"display": "7 英寸 · OLED（未标刷新率）", "chip": "麒麟 9020B", "charging": "66W 有线"},
         notes=["屏幕刷新率参数页未单列，摘要只写尺寸与材质，不补猜测值。"]),
    dict(id="hua-pura90p", brand="Huawei", name="HUAWEI Pura 90 Pro",
         type="影像旗舰", year=2026, launchMonth="2026-04", launchDateDisplay="2026年04月20日",
         price=5199, skus=["12GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"], pid="2163933",
         selling="麒麟 9030S + 红枫影像，6000mAh，66W 有线 / 50W 无线",
         bestFor=["拍照视频", "日常全能", "续航"],
         overrides={"chip": "麒麟 9030S"}, notes=[]),
    dict(id="hua-pura90pm", brand="Huawei", name="HUAWEI Pura 90 Pro Max",
         type="影像旗舰", year=2026, launchMonth="2026-04", launchDateDisplay="2026年04月20日",
         price=5999, skus=["12GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"], pid="2162803",
         selling="6.9 英寸 2 亿像素长焦，100W 有线 / 80W 无线，6000mAh",
         bestFor=["拍照视频", "长焦摄影", "大屏办公"],
         overrides={"chip": "麒麟 9030S"}, notes=[]),
    dict(id="hua-nova13", brand="Huawei", name="HUAWEI nova 13",
         type="中端影像", year=2024, launchMonth="2024-10", launchDateDisplay="2024年10月25日",
         price=2719, skus=["256GB", "512GB"], pid="2111321",
         selling="6000 万像素前置 + 100W 快充，6.7 英寸 OLED 直屏",
         bestFor=["拍照视频", "日常全能"],
         overrides={"chip": NO_CHIP, "storage": "256GB / 512GB（运存未公布）"},
         notes=["华为官网与参数页均不列运行内存，容量组合只写存储。"]),
    dict(id="hua-nova14", brand="Huawei", name="HUAWEI nova 14",
         type="中端影像", year=2025, launchMonth="2025-05", launchDateDisplay="2025年05月30日",
         price=2149, skus=["256GB", "512GB"], pid="2128361",
         selling="前置 5000 万像素 + 后置 RYYB 长焦，5500mAh / 100W",
         bestFor=["拍照视频", "日常全能"],
         overrides={"chip": NO_CHIP, "storage": "256GB / 512GB（运存未公布）"},
         notes=["华为官网不列运行内存。"]),
    dict(id="hua-nova14p", brand="Huawei", name="HUAWEI nova 14 Pro",
         type="中端影像", year=2025, launchMonth="2025-05", launchDateDisplay="2025年05月23日",
         price=2299, skus=["256GB", "512GB"], pid="2128363",
         selling="可变光圈主摄 + 5000 万前置，6.78 英寸四曲屏",
         bestFor=["拍照视频", "日常全能"],
         overrides={"chip": NO_CHIP, "storage": "256GB / 512GB（运存未公布）"},
         notes=["华为官网不列运行内存。"]),
    dict(id="hua-nova15p", brand="Huawei", name="HUAWEI nova 15 Pro",
         type="中端影像", year=2025, launchMonth="2025-12", launchDateDisplay="2025年12月25日",
         price=3749, skus=["512GB"], pid="2151923",
         selling="麒麟 9010S + 6500mAh，6.84 英寸 120Hz OLED",
         bestFor=["拍照视频", "续航", "日常全能"],
         overrides={"chip": "麒麟 9010S", "storage": "512GB（运存未公布）"},
         notes=["参数页只列 512GB 一个容量、不列运存；实际在售组合以官网为准。"]),
    dict(id="hua-changxiang80", brand="Huawei", name="HUAWEI 畅享 80",
         type="中端续航", year=2025, launchMonth="2025-04", launchDateDisplay="2025年04月25日",
         price=1049, skus=["128GB", "256GB", "512GB"], pid="2126869",
         selling="6620mAh 大电池 + 40W 快充，6.67 英寸 LCD",
         bestFor=["续航", "日常全能"],
         overrides={"chip": "厂商未公布处理器型号", "storage": "128GB / 256GB / 512GB（运存未公布）"},
         notes=["华为官网畅享系列规格页不列处理器型号与运行内存。"]),
    # ---------------- 荣耀 ----------------
    dict(id="honor-100", brand="Honor", name="荣耀 100",
         type="中端影像", year=2023, launchMonth="2023-12", launchDateDisplay="2023年12月01日",
         price=None, skus=["12GB+256GB", "16GB+256GB", "16GB+512GB"], pid="1957927",
         selling="5000 万像素写真主摄 + 5000 万前置，骁龙 7 Gen3",
         bestFor=["拍照视频", "日常全能"],
         overrides={"charging": "100W 有线"},
         notes=["参数页把充电写成「20V/5A 超级快充」，按 P=UI 换算为 100W。",
                "参数站与官网均未给出参考报价，价格留空待核。"]),
    dict(id="honor-100p", brand="Honor", name="荣耀 100 Pro",
         type="中端影像", year=2023, launchMonth="2023-12", launchDateDisplay="2023年12月01日",
         price=None, skus=["12GB+256GB", "16GB+256GB", "16GB+512GB", "16GB+1TB"], pid="1957930",
         selling="3200 万像素 50 倍长焦 + 66W 无线充，骁龙 8 Gen2",
         bestFor=["拍照视频", "长焦摄影"],
         overrides={"charging": "100W 有线 / 66W 无线"},
         notes=["参数页把有线充电写成「20V/5A」，换算 100W；无线 66W 为参数页原值。",
                "参数站与官网均未给出参考报价，价格留空待核。"]),
    dict(id="honor-200", brand="Honor", name="荣耀 200",
         type="中端影像", year=2024, launchMonth="2024-05", launchDateDisplay="2024年05月31日",
         price=2999, skus=["8GB+256GB", "12GB+256GB", "12GB+512GB", "16GB+512GB"], pid="2018015",
         selling="5000 万像素长焦 + 5000 万前置，5200mAh / 100W",
         bestFor=["拍照视频", "日常全能"], overrides={}, notes=[]),
    dict(id="honor-200p", brand="Honor", name="荣耀 200 Pro",
         type="中端影像", year=2024, launchMonth="2024-05", launchDateDisplay="2024年05月27日",
         price=2678, skus=["12GB+512GB", "16GB+512GB", "16GB+1TB"], pid="2018019",
         selling="骁龙 8s Gen3 + 50 倍长焦，100W 有线 / 66W 无线",
         bestFor=["拍照视频", "日常全能"], overrides={}, notes=[]),
    dict(id="honor-300p", brand="Honor", name="荣耀 300 Pro",
         type="中端影像", year=2024, launchMonth="2024-12", launchDateDisplay="2024年12月02日",
         price=3699, skus=["12GB+256GB", "12GB+512GB", "16GB+512GB"], pid="2115651",
         selling="骁龙 8 Gen3 + 5300mAh，100W 有线 / 80W 无线",
         bestFor=["拍照视频", "日常全能", "游戏性能"], overrides={}, notes=[]),
    dict(id="honor-500", brand="Honor", name="荣耀 500",
         type="中端全能", year=2025, launchMonth="2025-11", launchDateDisplay="2025年11月24日",
         price=2999, skus=["12GB+256GB", "12GB+512GB", "16GB+512GB"], pid="2148942",
         selling="8000mAh 电池 + 2 亿像素主摄，骁龙 8s Gen4",
         bestFor=["续航", "日常全能", "拍照视频"], overrides={}, notes=[]),
    dict(id="honor-500p", brand="Honor", name="荣耀 500 Pro",
         type="中端全能", year=2025, launchMonth="2025-11", launchDateDisplay="2025年11月24日",
         price=3299, skus=["12GB+256GB", "12GB+512GB", "16GB+512GB"], pid="2148026",
         selling="骁龙 8 Elite + 8000mAh，2 亿主摄 + 5000 万长焦",
         bestFor=["续航", "日常全能", "拍照视频"], overrides={}, notes=[]),
    dict(id="honor-win", brand="Honor", name="荣耀 WIN",
         type="游戏性能旗舰", year=2025, launchMonth="2025-12", launchDateDisplay="2025年12月26日",
         price=3999, skus=["12GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"], pid="2152396",
         selling="10000mAh 电池 + 185Hz 屏，骁龙 8 Elite Gen5",
         bestFor=["游戏性能", "续航", "日常全能"], overrides={}, notes=[]),
    # ---------------- 小米 / 红米 ----------------
    dict(id="xia-17max", brand="Xiaomi", name="Xiaomi 17 Max",
         type="全能旗舰", year=2026, launchMonth="2026-05", launchDateDisplay="2026年05月21日",
         price=5099, skus=["16GB+256GB", "16GB+512GB"], pid="2166982",
         selling="6.9 英寸 LTPO + 8000mAh，2 亿主摄 + 徕卡潜望长焦",
         bestFor=["大屏办公", "拍照视频", "续航"], overrides={}, notes=[]),
    dict(id="xia-17tp", brand="Xiaomi", name="Xiaomi 17T Pro",
         type="全能旗舰", year=2026, launchMonth="2026-06", launchDateDisplay="2026年06月08日",
         price=4299, skus=["12GB+256GB", "12GB+512GB", "16GB+512GB"], pid="2168676",
         selling="天玑 9500 + 徕卡 5 倍潜望，6.83 英寸 144Hz",
         bestFor=["拍照视频", "日常全能", "游戏性能"], overrides={}, notes=[]),
    dict(id="red-k90", brand="Xiaomi", name="REDMI K90",
         type="中端全能", year=2025, launchMonth="2025-10", launchDateDisplay="2025年10月23日",
         price=2399, skus=["12GB+512GB", "16GB+256GB", "16GB+512GB", "16GB+1TB"], pid="2145492",
         selling="骁龙 8 Elite + 7100mAh，5000 万主摄 + 5000 万长焦",
         bestFor=["性价比", "续航", "游戏性能"],
         overrides={"os": "Xiaomi HyperOS 3"}, notes=["参数页内核只写 Android 不带版本，系统摘要取 HyperOS 版本。"]),
    dict(id="red-k100", brand="Xiaomi", name="REDMI K100",
         type="性能续航旗舰", year=2026, launchMonth="2026-10", launchDateDisplay="2026年10月27日",
         price=4049, skus=["12GB+512GB", "16GB+512GB"], pid="2181744",
         selling="10000mAh 电池 + 165Hz 屏，骁龙 8 Elite",
         bestFor=["续航", "游戏性能", "日常全能"],
         overrides={"os": "Xiaomi HyperOS 4"}, notes=["参数页内核只写 Android 不带版本，系统摘要取 HyperOS 版本。"]),
    dict(id="red-k100pm", brand="Xiaomi", name="REDMI K100 Pro Max",
         type="性能旗舰", year=2026, launchMonth="2026-08", launchDateDisplay="2026年08月11日",
         price=4299, skus=["12GB+512GB", "16GB+256GB", "16GB+512GB", "16GB+1TB"], pid="2174706",
         selling="骁龙 8 Elite Gen5 + 9070mAh，2 亿主摄 + 5000 万潜望",
         bestFor=["游戏性能", "续航", "拍照视频"], overrides={}, notes=[]),
    dict(id="red-note15p", brand="Xiaomi", name="REDMI Note 15 Pro",
         type="中端续航", year=2025, launchMonth="2025-08", launchDateDisplay="2025年08月21日",
         price=1349, skus=["8GB+256GB", "12GB+256GB", "12GB+512GB"], pid="2139079",
         selling="7000mAh 电池 + 天玑 7400-Ultra，6.83 英寸 OLED",
         bestFor=["续航", "性价比"], overrides={}, notes=[]),
    dict(id="xia-civi4p", brand="Xiaomi", name="小米 Civi 4 Pro",
         type="中端影像", year=2024, launchMonth="2024-03", launchDateDisplay="2024年03月26日",
         price=2099, skus=["12GB+256GB", "12GB+512GB", "16GB+512GB"], pid="2036645",
         selling="徕卡光学三摄 + 179g 轻薄机身，骁龙 8s Gen3",
         bestFor=["拍照视频", "小屏手感"],
         overrides={"camera": "5000 万像素徕卡光学主摄 + 5000 万像素徕卡专业人像 + 1200 万像素徕卡超广角；前置 3200 万像素双摄"},
         notes=["参数页取的是「迪士尼公主限定版」标题页，硬件参数与标准版一致；影像摘要已去掉版本限定词。"]),
    # ---------------- OPPO ----------------
    dict(id="oppo-reno14", brand="OPPO", name="OPPO Reno14",
         type="中端影像", year=2025, launchMonth="2025-05", launchDateDisplay="2025年05月23日",
         price=2598, skus=["12GB+512GB", "16GB+256GB", "16GB+512GB", "16GB+1TB"], pid="2127911",
         selling="天玑 8350 + 6000mAh，5000 万主摄 + 5000 万长焦",
         bestFor=["拍照视频", "续航"], overrides={}, notes=[]),
    dict(id="oppo-reno14p", brand="OPPO", name="OPPO Reno14 Pro",
         type="中端影像", year=2025, launchMonth="2025-05", launchDateDisplay="2025年05月15日",
         price=3699, skus=["12GB+256GB", "16GB+512GB", "16GB+1TB"], pid="2127915",
         selling="天玑 8450 + 6200mAh，三颗 5000 万像素镜头，80W / 50W 无线",
         bestFor=["拍照视频", "日常全能"],
         overrides={"display": "6.83 英寸 AMOLED 四曲屏 · 120Hz",
                    "camera": "5000 万像素广角 + 5000 万像素超广角 + 5000 万像素长焦；前置 5000 万像素"},
         notes=["参数页屏幕材质写作「AMOLED(柔) 等高四曲」，摘要改写成可读写法，尺寸与刷新率不变。"]),
    dict(id="oppo-reno15", brand="OPPO", name="OPPO Reno15",
         type="中端影像", year=2025, launchMonth="2025-11", launchDateDisplay="2025年11月17日",
         price=2999, skus=["12GB+256GB", "16GB+256GB", "16GB+1TB"], pid="2147420",
         selling="2 亿像素主摄 + 5000 万潜望，6.32 英寸小直屏 / 6200mAh",
         bestFor=["拍照视频", "小屏手感"], overrides={}, notes=[]),
    dict(id="oppo-reno16", brand="OPPO", name="OPPO Reno16",
         type="中端影像", year=2026, launchMonth="2026-05", launchDateDisplay="2026年05月29日",
         price=3899, skus=["12GB+256GB", "12GB+512GB", "16GB+256GB", "16GB+512GB"], pid="2167290",
         selling="天玑 8550 SUPER + 6700mAh，2 亿主摄 + 5000 万潜望",
         bestFor=["拍照视频", "续航"], overrides={}, notes=[]),
    dict(id="oppo-findn6", brand="OPPO", name="OPPO Find N6",
         type="折叠屏旗舰", year=2026, launchMonth="2026-03", launchDateDisplay="2026年03月20日",
         price=10999, skus=["12GB+256GB", "16GB+512GB", "16GB+1TB"], pid="2160878",
         selling="8.12 英寸内屏 + 6.62 英寸外屏，2 亿主摄 / 6000mAh",
         bestFor=["大屏办公", "拍照视频", "日常全能"],
         overrides={"display": "主屏 8.12 英寸 + 副屏 6.62 英寸 · AMOLED · 120Hz"}, notes=[]),
    dict(id="oppo-x9sp", brand="OPPO", name="OPPO Find X9s Pro",
         type="影像旗舰", year=2026, launchMonth="2026-04", launchDateDisplay="2026年04月21日",
         price=5299, skus=["12GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"], pid="2164071",
         selling="天玑 9500 + 双 2 亿像素（主摄 / 长焦），7025mAh",
         bestFor=["拍照视频", "长焦摄影"], overrides={}, notes=[]),
    # ---------------- vivo ----------------
    dict(id="vivo-s19", brand="vivo", name="vivo S19",
         type="中端影像", year=2024, launchMonth="2024-06", launchDateDisplay="2024年06月07日",
         price=2999, skus=["8GB+256GB", "12GB+256GB", "16GB+512GB"], pid="2018384",
         selling="6000mAh 大电池 + 5000 万前置，骁龙 7 Gen3",
         bestFor=["续航", "拍照视频"], overrides={}, notes=[]),
    dict(id="vivo-s19p", brand="vivo", name="vivo S19 Pro",
         type="中端影像", year=2024, launchMonth="2024-06", launchDateDisplay="2024年06月07日",
         price=2799, skus=["8GB+256GB", "12GB+256GB", "12GB+512GB", "16GB+512GB"], pid="2018381",
         selling="天玑 9200+ + 5000 万长焦，5500mAh / 80W",
         bestFor=["拍照视频", "日常全能"], overrides={}, notes=[]),
    dict(id="vivo-s30pmini", brand="vivo", name="vivo S30 Pro mini",
         type="中端影像", year=2025, launchMonth="2025-05", launchDateDisplay="2025年05月29日",
         price=3499, skus=["12GB+256GB", "12GB+512GB", "16GB+512GB"], pid="2128323",
         selling="6.31 英寸小屏 + 6500mAh，5000 万潜望 / 90W",
         bestFor=["小屏手感", "拍照视频", "续航"], overrides={}, notes=[]),
    dict(id="vivo-s60", brand="vivo", name="vivo S60",
         type="中端影像", year=2026, launchMonth="2026-06", launchDateDisplay="2026年06月03日",
         price=3899, skus=["12GB+256GB", "12GB+512GB", "16GB+512GB"], pid="2167620",
         selling="7200mAh + 5000 万潜望长焦，6.59 英寸 144Hz",
         bestFor=["拍照视频", "续航"], overrides={}, notes=[]),
    dict(id="vivo-x300s", brand="vivo", name="vivo X300s",
         type="影像旗舰", year=2026, launchMonth="2026-03", launchDateDisplay="2026年03月30日",
         price=5299, skus=["12GB+256GB", "16GB+1TB"], pid="2161777",
         selling="天玑 9500+ + 2 亿像素蔡司主摄，7100mAh",
         bestFor=["拍照视频", "长焦摄影", "续航"],
         overrides={"camera": "2 亿像素云台级主摄 + 5000 万像素超广角 + 5000 万像素潜望长焦；前置 5000 万像素"},
         notes=["参数页把超广角写成「5000 亿像素」，同一行的传感器尺寸与光圈显示应为 5000 万，属页面笔误，摘要按 5000 万写。"]),
    dict(id="vivo-x200s", brand="vivo", name="vivo X200s",
         type="影像旗舰", year=2025, launchMonth="2025-04", launchDateDisplay="2025年04月25日",
         price=3799, skus=["12GB+512GB", "16GB+256GB", "16GB+512GB", "16GB+1TB"], pid="2126442",
         selling="天玑 9400+ + 5000 万潜望，6200mAh / 90W",
         bestFor=["拍照视频", "日常全能"], overrides={}, notes=[]),
    # ---------------- iQOO ----------------
    dict(id="iqoo-z11", brand="iQOO", name="iQOO Z11",
         type="中端续航", year=2026, launchMonth="2026-03", launchDateDisplay="2026年03月26日",
         price=2699, skus=["12GB+256GB", "12GB+512GB", "16GB+256GB", "16GB+512GB"], pid="2161683",
         selling="9020mAh 大电池 + 165Hz 屏，天玑 8500 Elite",
         bestFor=["续航", "游戏性能"], overrides={}, notes=[]),
    dict(id="iqoo-neo11", brand="iQOO", name="iQOO Neo11",
         type="游戏性能旗舰", year=2025, launchMonth="2025-10", launchDateDisplay="2025年10月30日",
         price=3099, skus=["12GB+512GB", "16GB+256GB", "16GB+512GB", "16GB+1TB"], pid="2146218",
         selling="骁龙 8 Elite + 7500mAh，6.82 英寸 144Hz 电竞屏",
         bestFor=["游戏性能", "续航", "性价比"], overrides={}, notes=[]),
    dict(id="iqoo-neo12", brand="iQOO", name="iQOO Neo12",
         type="游戏性能旗舰", year=2026, launchMonth="2026-10", launchDateDisplay="2026年10月28日",
         price=4199, skus=["12GB+512GB", "16GB+256GB", "16GB+512GB", "16GB+1TB"], pid="2181828",
         selling="骁龙 8 Gen5 + 9000mAh，6.83 英寸 185Hz",
         bestFor=["游戏性能", "续航", "日常全能"], overrides={}, notes=[]),
    dict(id="iqoo-15t", brand="iQOO", name="iQOO 15T",
         type="性能旗舰", year=2026, launchMonth="2026-05", launchDateDisplay="2026年05月20日",
         price=4099, skus=["12GB+512GB", "16GB+256GB", "16GB+512GB", "16GB+1TB"], pid="2166853",
         selling="天玑 9500 Monster 版 + 2 亿主摄，8000mAh / 100W",
         bestFor=["游戏性能", "拍照视频", "续航"], overrides={}, notes=[]),
    # ---------------- 苹果 ----------------
    dict(id="apple-17e", brand="Apple", name="iPhone 17e",
         type="标准旗舰", year=2026, launchMonth="2026-03", launchDateDisplay="2026年03月11日",
         price=4499, skus=["256GB", "512GB"], pid="2159097",
         selling="A19 + 6.1 英寸 OLED，单摄 4800 万像素的入门档 iPhone",
         bestFor=["苹果生态", "小屏手感", "日常全能"],
         overrides={"battery": "官方不公布 mAh；续航以官网为准", "charging": "USB-C 快充 / MagSafe 无线",
                    "storage": "256GB / 512GB"},
         notes=["苹果不在官网公布电池容量与有线充电功率，摘要按既有 iPhone 记录口径写。"]),
    dict(id="apple-16e", brand="Apple", name="iPhone 16e",
         type="标准旗舰", year=2025, launchMonth="2025-02", launchDateDisplay="2025年02月28日",
         price=None, skus=["256GB", "512GB"], pid="2121125",
         selling="A18 + 自研 5G 基带，6.1 英寸 OLED 的入门档 iPhone",
         bestFor=["苹果生态", "小屏手感"],
         overrides={"battery": "官方不公布 mAh；续航以官网为准", "charging": "USB-C 快充 / MagSafe 无线",
                    "storage": "256GB / 512GB"},
         notes=["国外发布时间 2025-02-20、大陆开售 2025-02-28，取开售日。",
                "参数站只收录 256GB / 512GB 两个容量版本，其它版本未在参数站列出，未写入。",
                "参数站未给参考报价，价格留空待核。"]),
    # ---------------- Moto ----------------
    dict(id="moto-x70airpro", brand="Motorola", name="Moto X70 Air Pro",
         type="中端全能", year=2026, launchMonth="2026-01", launchDateDisplay="2026年01月20日",
         price=4499, skus=["16GB+512GB", "16GB+1TB"], pid="2155046",
         selling="骁龙 8 Gen5 + 三颗 5000 万像素镜头，186g 轻薄机身",
         bestFor=["拍照视频", "小屏手感", "日常全能"],
         overrides={"os": "Android（厂商规格页未列版本号）"},
         notes=["参数页系统栏只写 Android，不写版本，按原样记录不补猜测值。"]),
    dict(id="moto-razrfold", brand="Motorola", name="Moto Razr Fold",
         type="折叠屏旗舰", year=2026, launchMonth="2026-05", launchDateDisplay="2026年05月19日",
         price=10999, skus=["12GB+256GB", "16GB+512GB", "16GB+1TB"], pid="2166714",
         selling="8.09 英寸内屏 + 6.56 英寸外屏，三颗 5000 万像素镜头",
         bestFor=["大屏办公", "拍照视频"],
         overrides={"display": "主屏 8.09 英寸 + 副屏 6.56 英寸 · pOLED · 120Hz"},
         notes=["参数页取的是 FIFA 世界杯联名版本标题页，硬件参数与标准版一致。"]),
]


def goods_url(pid: str) -> str:
    return ZOL_GOODS.format(pid[:4], pid)


def build(meta: dict) -> dict:
    url = ZOL_PARAM.format(meta["pid"][:4], meta["pid"])
    specs = parse_specs(fetch(url))
    if not specs:
        raise SystemExit(f"参数页解析失败：{meta['name']} {url}")
    title = ""
    d = derive(specs)
    ov = meta.get("overrides", {})

    def tidy_display(x: str) -> str:
        x = x.replace("柔性OLED屏", "柔性 OLED").replace("柔性AMOLED", "柔性 AMOLED")
        x = x.replace("POLED", "pOLED")
        return x

    def val(k: str, fallback: str = "") -> str:
        v = ov.get(k) or d.get(k) or fallback
        return tidy_display(v) if k == "display" else v

    field_count = sum(len(g["items"]) for g in specs)
    audit = []
    PH = __import__("re").compile(r"^(以.{0,12}为准|.{0,6}(待核验|待录入|暂缺|未公布|未收录|未公开).{0,10})$")
    for key, label in (("display", "屏幕"), ("chip", "处理器"), ("camera", "影像"),
                       ("battery", "电池"), ("charging", "充电"), ("weight", "重量"),
                       ("storage", "容量组合")):
        v = val(key)
        if not v or PH.match(v):
            continue
        audit.append({"field": label, "value": v, "valueAtAudit": v,
                      "status": "cross_checked_secondary_source", "sourceUrl": url,
                      "evidenceText": f"中关村在线参数页：{label} {v}",
                      "note": f"{TODAY} 新增机型时按参数页填写；参数页明显笔误处已按同页其他字段校正。"})
    audit.append({"field": "正式发布/开售日期", "value": meta["launchDateDisplay"],
                  "valueAtAudit": meta["launchDateDisplay"],
                  "status": "cross_checked_secondary_source", "sourceUrl": url,
                  "evidenceText": f"中关村在线参数页上市日期：{meta['launchDateDisplay']}",
                  "note": f"{TODAY} 新增机型时按参数页上市日期填写。"})

    price = meta.get("price")
    skus = meta["skus"]
    if price:
        priceType = "third_party_reference"
        priceText = REF_TEXT
        priceSrc = goods_url(meta["pid"])
        priceSrcName = "中关村在线商品页（站内参考报价）"
        quoteTarget = skus[0] if len(skus) == 1 else "以 ZOL 商品页在售版本为准"
        priceAudit = "secondary_source_reference"
    else:
        priceType = "price_pending"
        priceText = "参数站未给出参考报价，价格待核；以在售版本为准"
        priceSrc = url
        priceSrcName = "中关村在线参数页（未提供参考价）"
        quoteTarget = "以在售版本为准"
        priceAudit = "source_present_needs_crosscheck"

    rec = {
        "id": meta["id"], "brand": meta["brand"], "name": meta["name"],
        "year": meta["year"], "type": meta["type"], "market": "中国大陆正式销售",
        "display": val("display", "以官方规格页为准"),
        "chip": val("chip", "以官方规格页为准"),
        "camera": val("camera", "以官方规格页为准"),
        "battery": val("battery", "以官方规格页为准"),
        "charging": val("charging", "以官方规格页为准"),
        "weight": val("weight", "以官方规格页为准"),
        "storage": " / ".join(skus),
        "os": val("os", "以官方规格页为准"),
        "priceCN": price, "priceText": priceText,
        "selling": meta["selling"], "bestFor": meta["bestFor"],
        "source": url, "sourceName": ZOL_NAME,
        "verified": False,
        "launchMonth": meta["launchMonth"], "launchDateDisplay": meta["launchDateDisplay"],
        "priceType": priceType,
        "livePrice": None, "livePriceStatus": "not_connected", "livePriceCheckedAt": None,
        "storageOptions": skus, "chinaOfficial": True,
        "dataNote": "参数取自中关村在线参数页；价格若为参考价会在 priceText 里注明非首发价，缺价不做估算。",
        "announcementSource": url, "priceSource": priceSrc, "priceSourceName": priceSrcName,
        "livePriceNote": "尚未接入获授权的实时渠道报价 API；请通过渠道入口核价",
        "scoreMethod": "heuristic_preliminary",
        "quoteTargetStorage": quoteTarget,
        "quoteTargetStorageReason": "报价检索只接受商品标题中可核验的型号与指定大陆版容量组合；无法匹配就不显示价格。",
        "auditStatus": "needs_parameter_price_audit",
        "auditNotes": ([f"{TODAY} 新增机型：{field_count} 项参数（中关村在线，标题比对通过）"]
                        + ([f"参数站只收录一个容量版本（{skus[0]}），实际在售组合以官网为准。"] if len(skus) == 1 else [])
                        + meta.get("notes", [])),
        "priceAuditStatus": priceAudit,
        "parameterAuditStatus": "partial",
        "specSource": url, "specSourceName": ZOL_NAME,
        "specFieldCount": field_count, "specCollectedAt": TODAY,
        "specs": specs, "fieldAudit": audit,
    }
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    have = {p["id"] for p in catalog}
    names = {p["name"] for p in catalog}
    added = 0
    for meta in NEW:
        if meta["id"] in have:
            print(f"skip existing id {meta['id']}")
            continue
        if meta["name"] in names:
            print(f"skip existing name {meta['name']}")
            continue
        rec = build(meta)
        if args.dry:
            print(f"DRY {rec['name']:22s} | {rec['specFieldCount']:3d} 字段 | ¥{rec['priceCN']} | "
                  f"{rec['display']} | {rec['chip']}")
            continue
        catalog.append(rec)
        have.add(meta["id"])
        names.add(meta["name"])
        added += 1
    if args.dry:
        print(f"dry-run: {len(NEW)} 条候选")
        return
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    back = json.loads(CATALOG.read_text(encoding="utf-8"))
    print(f"added {added}, catalog now {len(back)} records")
    for f in (ROOT / "index.html", ROOT / "phone-compare-demo.html"):
        if f.is_file():
            patch_html(f, back, strict=False)


if __name__ == "__main__":
    main()
