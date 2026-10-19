#!/usr/bin/env python3
"""补录 2022-2025 中高端机型，并同步 data/phones.json、index.html、phone-compare-demo.html。

原则：
- 只录入可确认存在的大陆版机型，宁可 priceCN 留空，也不用渠道现价顶替首发价。
- 字段口径与既有记录完全一致（同一组键、同一套枚举值）。
- storage 字符串由 storageOptions 生成，避免两者不一致。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SRC = {
    "Apple": "https://www.apple.com.cn/",
    "Samsung": "https://www.samsung.com.cn/",
    "Xiaomi": "https://www.mi.com/",
    "Huawei": "https://consumer.huawei.com/cn/",
    "Honor": "https://www.honor.com/cn/",
    "OPPO": "https://www.oppo.com/cn/",
    "vivo": "https://www.vivo.com.cn/",
    "OnePlus": "https://www.oneplus.com/cn",
    "iQOO": "https://www.vivo.com.cn/",
    "realme": "https://www.realme.com/cn/",
    "nubia": "https://www.nubia.com/",
}

# id, brand, name, year, type, launchMonth, display, chip, camera, battery, charging,
# weight, os, priceCN, selling, bestFor, storageOptions, quoteTargetStorage
NEW = [
    # ---------- Apple ----------
    ("apple-17p", "Apple", "iPhone 17 Pro", 2025, "全能旗舰", "2025-09",
     "6.3 英寸 LTPO OLED · 1–120Hz", "A19 Pro",
     "4800 万像素主摄 + 4800 万像素超广角 + 4800 万像素 4× 长焦（以官方规格页为准）",
     "官方未按 mAh 公布", "USB-C 快充 / MagSafe 无线充电", "约 206 g", "iOS 26", 8999,
     "Pro 级三摄与 A19 Pro，钛金属中框", ["拍照视频", "游戏性能", "日常全能"],
     ["256GB", "512GB", "1TB"], "256GB"),
    ("apple-16p", "Apple", "iPhone 16 Pro", 2024, "全能旗舰", "2024-09",
     "6.3 英寸 LTPO OLED · 1–120Hz", "A18 Pro",
     "4800 万像素主摄 + 4800 万像素超广角 + 1200 万像素 5× 长焦",
     "官方未按 mAh 公布", "USB-C 快充 / MagSafe 无线充电", "199 g", "iOS 18", 7999,
     "钛金属中框与 5× 潜望长焦", ["拍照视频", "游戏性能", "日常全能"],
     ["128GB", "256GB", "512GB", "1TB"], "128GB"),
    ("apple-16", "Apple", "iPhone 16", 2024, "标准旗舰", "2024-09",
     "6.1 英寸 OLED · 60Hz", "A18",
     "4800 万像素主摄 + 1200 万像素超广角",
     "官方未按 mAh 公布", "USB-C 快充 / MagSafe 无线充电", "170 g", "iOS 18", 5999,
     "相机控制按键与 A18，标准尺寸直屏", ["拍照视频", "日常全能", "苹果生态"],
     ["128GB", "256GB", "512GB"], "128GB"),
    ("apple-15p", "Apple", "iPhone 15 Pro", 2023, "全能旗舰", "2023-09",
     "6.1 英寸 LTPO OLED · 1–120Hz", "A17 Pro",
     "4800 万像素主摄 + 1200 万像素超广角 + 1200 万像素 3× 长焦",
     "官方未按 mAh 公布", "USB-C 快充 / MagSafe 无线充电", "187 g", "iOS 17", 7999,
     "钛金属机身与 A17 Pro，改用 USB-C", ["拍照视频", "游戏性能", "日常全能"],
     ["128GB", "256GB", "512GB", "1TB"], "128GB"),
    ("apple-15", "Apple", "iPhone 15", 2023, "标准旗舰", "2023-09",
     "6.1 英寸 OLED · 60Hz", "A16",
     "4800 万像素主摄 + 1200 万像素超广角",
     "官方未按 mAh 公布", "USB-C 快充 / MagSafe 无线充电", "171 g", "iOS 17", 5999,
     "灵动岛与 4800 万主摄下放到标准版", ["拍照视频", "日常全能", "苹果生态"],
     ["128GB", "256GB", "512GB"], "128GB"),
    ("apple-14p", "Apple", "iPhone 14 Pro", 2022, "全能旗舰", "2022-09",
     "6.1 英寸 LTPO OLED · 1–120Hz", "A16",
     "4800 万像素主摄 + 1200 万像素超广角 + 1200 万像素 3× 长焦",
     "官方未按 mAh 公布", "USB-C 快充 / MagSafe 无线充电", "206 g", "iOS 16", 7999,
     "灵动岛首发机型，48MP 主摄", ["拍照视频", "游戏性能", "日常全能"],
     ["128GB", "256GB", "512GB", "1TB"], "128GB"),

    # ---------- Samsung ----------
    ("sam-24", "Samsung", "Galaxy S24", 2024, "全能旗舰", "2024-01",
     "6.2 英寸 Dynamic AMOLED 2X · 1–120Hz", "骁龙 8 Gen 3 for Galaxy",
     "5000 万像素主摄 + 1200 万像素超广角 + 1000 万像素 3× 长焦",
     "4000 mAh", "25W 有线 / 15W 无线", "167 g", "Android / One UI 6.1", 5999,
     "小尺寸 Galaxy AI 旗舰", ["拍照视频", "小屏手感", "日常全能"],
     ["8GB+256GB", "12GB+256GB", "8GB+512GB"], "8GB+256GB"),
    ("sam-24p", "Samsung", "Galaxy S24+", 2024, "全能旗舰", "2024-01",
     "6.7 英寸 Dynamic AMOLED 2X · 1–120Hz", "骁龙 8 Gen 3 for Galaxy",
     "5000 万像素主摄 + 1200 万像素超广角 + 1000 万像素 3× 长焦",
     "4900 mAh", "45W 有线 / 15W 无线", "196 g", "Android / One UI 6.1", 6999,
     "大屏 S 系列，2K 屏与更大电池", ["拍照视频", "大屏办公", "日常全能"],
     ["12GB+256GB", "12GB+512GB"], "12GB+256GB"),
    ("sam-zf6", "Samsung", "Galaxy Z Fold6", 2024, "折叠屏旗舰", "2024-07",
     "7.6 英寸内屏 + 6.3 英寸外屏 · 1–120Hz", "骁龙 8 Gen 3 for Galaxy",
     "5000 万像素主摄 + 1200 万像素超广角 + 1000 万像素 3× 长焦",
     "4400 mAh", "25W 有线 / 无线充电", "239 g", "Android / One UI 6.1.1", 13999,
     "横向大折叠，机身进一步减薄", ["大屏办公", "拍照视频", "日常全能"],
     ["12GB+256GB", "12GB+512GB", "12GB+1TB"], "12GB+256GB"),
    ("sam-zflip6", "Samsung", "Galaxy Z Flip6", 2024, "折叠屏旗舰", "2024-07",
     "6.7 英寸内屏 + 3.4 英寸外屏 · 1–120Hz", "骁龙 8 Gen 3 for Galaxy",
     "5000 万像素主摄 + 1200 万像素超广角",
     "4000 mAh", "25W 有线 / 无线充电", "187 g", "Android / One UI 6.1.1", 7999,
     "竖向小折叠，外屏交互与影像升级", ["小屏手感", "拍照视频", "日常全能"],
     ["12GB+256GB", "12GB+512GB"], "12GB+256GB"),
    ("sam-zf5", "Samsung", "Galaxy Z Fold5", 2023, "折叠屏旗舰", "2023-07",
     "7.6 英寸内屏 + 6.2 英寸外屏 · 1–120Hz", "骁龙 8 Gen 2 for Galaxy",
     "5000 万像素主摄 + 1200 万像素超广角 + 1000 万像素 3× 长焦",
     "4400 mAh", "25W 有线 / 无线充电", "253 g", "Android / One UI 5.1", None,
     "水滴铰链闭合无缝的横向大折叠", ["大屏办公", "拍照视频", "日常全能"],
     ["12GB+256GB", "12GB+512GB", "12GB+1TB"], None),
    ("sam-zflip5", "Samsung", "Galaxy Z Flip5", 2023, "折叠屏旗舰", "2023-07",
     "6.7 英寸内屏 + 3.4 英寸外屏 · 1–120Hz", "骁龙 8 Gen 2 for Galaxy",
     "1200 万像素主摄 + 1200 万像素超广角",
     "3700 mAh", "25W 有线 / 无线充电", "187 g", "Android / One UI 5.1", None,
     "外屏扩至 3.4 英寸的竖向小折叠", ["小屏手感", "拍照视频", "日常全能"],
     ["8GB+256GB", "8GB+512GB"], None),
    ("sam-25e", "Samsung", "Galaxy S25 Edge", 2025, "全能旗舰", "2025-05",
     "6.7 英寸 Dynamic AMOLED 2X · 1–120Hz", "骁龙 8 至尊版 for Galaxy",
     "2 亿像素主摄 + 1200 万像素超广角",
     "3900 mAh", "25W 有线 / 无线充电", "163 g", "Android / One UI 7", None,
     "5.8mm 级超薄机身，主打轻薄手感", ["拍照视频", "日常全能", "小屏手感"],
     ["12GB+256GB", "12GB+512GB"], "12GB+256GB"),

    # ---------- Xiaomi ----------
    ("xia-14", "Xiaomi", "小米 14", 2023, "全能旗舰", "2023-10",
     "6.36 英寸 OLED · 1–120Hz", "骁龙 8 Gen 3",
     "徕卡三摄：5000 万主摄 + 5000 万浮动长焦 + 5000 万超广角",
     "4610 mAh", "90W 有线 / 50W 无线", "193 g", "Xiaomi HyperOS", 3999,
     "小尺寸徕卡影像旗舰，首发澎湃 OS", ["拍照视频", "小屏手感", "日常全能"],
     ["8GB+256GB", "12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("xia-14p", "Xiaomi", "小米 14 Pro", 2023, "全能旗舰", "2023-10",
     "6.73 英寸 2K OLED · 1–120Hz", "骁龙 8 Gen 3",
     "徕卡三摄：5000 万可变光圈主摄 + 5000 万浮动长焦 + 5000 万超广角",
     "4880 mAh", "120W 有线 / 50W 无线", "223 g", "Xiaomi HyperOS", 4999,
     "2K 全等深微曲屏与可变光圈主摄", ["拍照视频", "大屏办公", "日常全能"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("xia-13", "Xiaomi", "小米 13", 2022, "全能旗舰", "2022-12",
     "6.36 英寸 OLED · 1–120Hz", "骁龙 8 Gen 2",
     "徕卡三摄：5000 万主摄 + 1000 万长焦 + 1200 万超广角",
     "4500 mAh", "67W 有线 / 50W 无线", "189 g", "MIUI 14", 3999,
     "小尺寸直屏与徕卡影像", ["拍照视频", "小屏手感", "日常全能"],
     ["8GB+128GB", "8GB+256GB", "12GB+256GB", "12GB+512GB"], "8GB+128GB"),
    ("xia-13p", "Xiaomi", "小米 13 Pro", 2022, "全能旗舰", "2022-12",
     "6.73 英寸 2K OLED · 1–120Hz", "骁龙 8 Gen 2",
     "徕卡三摄：1 英寸主摄 + 5000 万长焦 + 5000 万超广角",
     "4820 mAh", "120W 有线 / 50W 无线", "229 g", "MIUI 14", 4999,
     "1 英寸大底主摄下放到 Pro 款", ["拍照视频", "大屏办公", "日常全能"],
     ["8GB+128GB", "8GB+256GB", "12GB+256GB", "12GB+512GB"], "8GB+128GB"),
    ("xia-mixfold4", "Xiaomi", "MIX Fold 4", 2024, "折叠屏旗舰", "2024-07",
     "7.98 英寸内屏 + 6.56 英寸外屏 · 1–120Hz", "骁龙 8 Gen 3",
     "徕卡四摄：5000 万主摄 + 1000 万潜望长焦 + 5000 万浮动长焦 + 1200 万超广角",
     "5100 mAh", "67W 有线 / 50W 无线", "226 g", "Xiaomi HyperOS", 8999,
     "9.2mm 级横向大折叠，四摄五焦段", ["大屏办公", "拍照视频", "日常全能"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("xia-mixfold3", "Xiaomi", "MIX Fold 3", 2023, "折叠屏旗舰", "2023-08",
     "8.03 英寸内屏 + 6.56 英寸外屏 · 1–120Hz", "骁龙 8 Gen 2 领先版",
     "徕卡四摄：5000 万主摄 + 1000 万潜望长焦 + 1000 万浮动长焦 + 1200 万超广角",
     "4800 mAh", "67W 有线 / 50W 无线", "255 g", "MIUI 14", 8999,
     "轻薄大折叠，徕卡全焦段四摄", ["大屏办公", "拍照视频", "日常全能"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("xia-mixflip", "Xiaomi", "MIX Flip", 2024, "折叠屏旗舰", "2024-07",
     "6.86 英寸内屏 + 4.01 英寸外屏 · 1–120Hz", "骁龙 8 Gen 3",
     "5000 万主摄 + 5000 万浮动长焦",
     "4780 mAh", "67W 有线 / 无线充电", "192 g", "Xiaomi HyperOS", 5999,
     "小折叠首作，大外屏可直接用主摄自拍", ["拍照视频", "小屏手感", "日常全能"],
     ["12GB+256GB", "12GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("redmi-k80p", "Xiaomi", "REDMI K80 Pro", 2024, "性能旗舰", "2024-11",
     "6.67 英寸 2K OLED · 120Hz", "骁龙 8 至尊版",
     "5000 万主摄 + 5000 万浮动长焦 + 3200 万超广角",
     "6000 mAh", "120W 有线 / 50W 无线", "212 g", "Xiaomi HyperOS 2", 3699,
     "2K 直屏 + 骁龙 8 至尊版的性能价位段机型", ["游戏性能", "续航", "日常全能"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("redmi-k80", "Xiaomi", "REDMI K80", 2024, "性能续航旗舰", "2024-11",
     "6.67 英寸 2K OLED · 120Hz", "骁龙 8 Gen 3",
     "5000 万主摄 + 800 万超广角",
     "6550 mAh", "90W 有线", "206 g", "Xiaomi HyperOS 2", 2499,
     "6550mAh 大电池的标准版性能机", ["游戏性能", "续航", "性价比"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),

    # ---------- Huawei ----------
    ("hua-mate70", "Huawei", "HUAWEI Mate 70", 2024, "全能旗舰", "2024-11",
     "6.7 英寸 OLED · 1–120Hz", "麒麟 9020",
     "红枫原色影像：5000 万主摄 + 4000 万超广角 + 1200 万潜望长焦",
     "5300 mAh", "66W 有线 / 50W 无线", "203 g", "HarmonyOS 4.3", 5499,
     "Mate 标准旗舰，红枫原色影像", ["拍照视频", "日常全能", "大屏办公"],
     ["12GB+256GB", "12GB+512GB", "12GB+1TB"], "12GB+256GB"),
    ("hua-mate70pp", "Huawei", "HUAWEI Mate 70 Pro+", 2024, "顶级全能旗舰", "2024-11",
     "6.9 英寸 OLED · 1–120Hz", "麒麟 9020",
     "5000 万主摄 + 4000 万超广角 + 4800 万潜望长焦",
     "5700 mAh", "100W 有线 / 80W 无线", "226 g", "HarmonyOS 4.3", 8499,
     "高亮钛玄武架构与 4800 万潜望长焦", ["拍照视频", "大屏办公", "日常全能"],
     ["16GB+512GB", "16GB+1TB"], "16GB+512GB"),
    ("hua-matex6", "Huawei", "HUAWEI Mate X6", 2024, "折叠屏旗舰", "2024-11",
     "7.93 英寸内屏 + 6.45 英寸外屏 · 1–120Hz", "麒麟 9020",
     "5000 万主摄 + 4000 万超广角 + 4800 万潜望长焦",
     "5110 mAh", "66W 有线 / 50W 无线", "239 g", "HarmonyOS 4.3", 12999,
     "横向大折叠，支持卫星通信", ["大屏办公", "拍照视频", "日常全能"],
     ["12GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("hua-matex5", "Huawei", "HUAWEI Mate X5", 2023, "折叠屏旗舰", "2023-09",
     "7.85 英寸内屏 + 6.4 英寸外屏 · 1–120Hz", "麒麟 9000S",
     "5000 万主摄 + 1300 万超广角 + 1200 万潜望长焦",
     "5060 mAh", "66W 有线 / 50W 无线", "243 g", "HarmonyOS 4", None,
     "轻薄横向大折叠，玄武钢化玻璃", ["大屏办公", "拍照视频", "日常全能"],
     ["12GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"], None),
    ("hua-pura70", "Huawei", "HUAWEI Pura 70", 2024, "影像旗舰", "2024-04",
     "6.6 英寸 OLED · 1–120Hz", "麒麟 9010",
     "5000 万主摄 + 1300 万超广角 + 1200 万潜望长焦",
     "4900 mAh", "66W 有线 / 50W 无线", "207 g", "HarmonyOS 4.2", 5499,
     "Pura 系列标准款，三角风向标设计", ["拍照视频", "日常全能"],
     ["12GB+256GB", "12GB+512GB", "12GB+1TB"], "12GB+256GB"),
    ("hua-pura70p", "Huawei", "HUAWEI Pura 70 Pro", 2024, "影像旗舰", "2024-04",
     "6.8 英寸 OLED · 1–120Hz", "麒麟 9010",
     "5000 万主摄 + 1250 万超广角 + 4800 万潜望长焦",
     "5050 mAh", "100W 有线 / 80W 无线", "220 g", "HarmonyOS 4.2", 6499,
     "4800 万潜望长焦，支持长焦微距", ["拍照视频", "长焦摄影", "日常全能"],
     ["12GB+256GB", "12GB+512GB", "12GB+1TB"], "12GB+256GB"),
    ("hua-purax", "Huawei", "HUAWEI Pura X", 2025, "折叠屏旗舰", "2025-03",
     "6.3 英寸 16:10 内屏 + 3.5 英寸外屏 · 1–120Hz", "麒麟 9020",
     "5000 万主摄 + 4000 万超广角 + 800 万长焦",
     "4720 mAh", "66W 有线 / 40W 无线", "195 g", "HarmonyOS 5", 7499,
     "16:10 阔折叠，展开接近小平板", ["大屏办公", "拍照视频", "日常全能"],
     ["12GB+256GB", "12GB+512GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),

    # ---------- Honor ----------
    ("honor-magic7", "Honor", "荣耀 Magic7", 2024, "全能旗舰", "2024-10",
     "6.78 英寸 OLED · 1–120Hz", "骁龙 8 至尊版",
     "5000 万主摄 + 5000 万潜望长焦 + 5000 万超广角",
     "5650 mAh", "100W 有线 / 80W 无线", "199 g", "MagicOS 9.0", 4499,
     "标准版直屏旗舰，AI 与青海湖电池", ["拍照视频", "日常全能", "游戏性能"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("honor-magic6", "Honor", "荣耀 Magic6", 2024, "全能旗舰", "2024-01",
     "6.78 英寸 OLED · 1–120Hz", "骁龙 8 Gen 3",
     "5000 万主摄 + 5000 万潜望长焦 + 5000 万超广角",
     "5450 mAh", "66W 有线 / 50W 无线", "206 g", "MagicOS 8.0", 4399,
     "等深微曲屏与单反级长焦", ["拍照视频", "日常全能"],
     ["12GB+256GB", "16GB+512GB"], "12GB+256GB"),
    ("honor-v3", "Honor", "荣耀 Magic V3", 2024, "折叠屏旗舰", "2024-07",
     "7.92 英寸内屏 + 6.43 英寸外屏 · 1–120Hz", "骁龙 8 Gen 3",
     "5000 万主摄 + 4000 万超广角 + 5000 万潜望长焦",
     "5150 mAh", "66W 有线 / 50W 无线", "226 g", "MagicOS 8.0", 8999,
     "9.2mm 级轻薄大折叠，支持潜望长焦", ["大屏办公", "拍照视频", "日常全能"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("honor-v2", "Honor", "荣耀 Magic V2", 2023, "折叠屏旗舰", "2023-07",
     "7.92 英寸内屏 + 6.43 英寸外屏 · 1–120Hz", "骁龙 8 Gen 2 领先版",
     "5000 万主摄 + 5000 万超广角 + 5000 万长焦",
     "5000 mAh", "66W 有线", "231 g", "MagicOS 7.2", 8999,
     "主打轻薄的横向大折叠", ["大屏办公", "拍照视频", "日常全能"],
     ["12GB+256GB", "16GB+512GB"], "12GB+256GB"),

    # ---------- OPPO ----------
    ("oppo-x8", "OPPO", "OPPO Find X8", 2024, "影像旗舰", "2024-10",
     "6.59 英寸 OLED · 1–120Hz", "天玑 9400",
     "5000 万主摄 + 5000 万潜望长焦 + 5000 万超广角",
     "5630 mAh", "80W 有线 / 50W 无线", "193 g", "ColorOS 15", 4199,
     "小尺寸直屏影像旗舰，哈苏人像", ["拍照视频", "小屏手感", "日常全能"],
     ["12GB+256GB", "16GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("oppo-x8p", "OPPO", "OPPO Find X8 Pro", 2024, "影像旗舰", "2024-10",
     "6.78 英寸 OLED · 1–120Hz", "天玑 9400",
     "5000 万主摄 + 5000 万潜望长焦 ×2 + 5000 万超广角",
     "5910 mAh", "80W 有线 / 50W 无线", "215 g", "ColorOS 15", 5299,
     "双潜望长焦，哈苏全焦段影像", ["拍照视频", "长焦摄影", "日常全能"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("oppo-x7", "OPPO", "OPPO Find X7", 2024, "影像旗舰", "2024-01",
     "6.74 英寸 OLED · 1–120Hz", "天玑 9300",
     "5000 万主摄 + 6400 万潜望长焦 + 5000 万超广角",
     "5000 mAh", "100W 有线", "202 g", "ColorOS 14", 3999,
     "标准版影像旗舰，潜望长焦下放", ["拍照视频", "日常全能"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("oppo-n3", "OPPO", "OPPO Find N3", 2023, "折叠屏旗舰", "2023-10",
     "7.82 英寸内屏 + 6.31 英寸外屏 · 1–120Hz", "骁龙 8 Gen 2",
     "4800 万主摄 + 6400 万潜望长焦 + 4800 万超广角",
     "4805 mAh", "67W 有线", "239 g", "ColorOS 13.2", 9999,
     "大折叠影像旗舰，三摄均为高像素", ["大屏办公", "拍照视频", "日常全能"],
     ["12GB+512GB", "16GB+1TB"], "12GB+512GB"),
    ("oppo-n3flip", "OPPO", "OPPO Find N3 Flip", 2023, "折叠屏旗舰", "2023-08",
     "6.8 英寸内屏 + 3.26 英寸外屏 · 1–120Hz", "天玑 9200",
     "5000 万主摄 + 4800 万超广角 + 3200 万长焦",
     "4300 mAh", "44W 有线", "198 g", "ColorOS 13.2", 6799,
     "小折叠加入独立长焦，哈苏人像", ["拍照视频", "小屏手感", "日常全能"],
     ["12GB+256GB", "12GB+512GB"], "12GB+256GB"),
    ("oppo-n2", "OPPO", "OPPO Find N2", 2022, "折叠屏旗舰", "2022-12",
     "7.1 英寸内屏 + 5.54 英寸外屏 · 1–120Hz", "骁龙 8+ Gen 1",
     "5000 万主摄 + 4800 万超广角 + 3200 万长焦",
     "4520 mAh", "67W 有线", "233 g", "ColorOS 13", 7999,
     "小尺寸横向折叠，主打单手可用", ["大屏办公", "拍照视频", "日常全能"],
     ["12GB+256GB", "16GB+512GB"], "12GB+256GB"),

    # ---------- vivo ----------
    ("vivo-x200", "vivo", "vivo X200", 2024, "影像旗舰", "2024-10",
     "6.67 英寸 AMOLED · 1–120Hz", "天玑 9400",
     "5000 万主摄 + 5000 万潜望长焦 + 5000 万超广角",
     "5800 mAh", "90W 有线", "197 g", "OriginOS 5", 4299,
     "蔡司影像标准旗舰，蓝海电池", ["拍照视频", "日常全能", "续航"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("vivo-x200p", "vivo", "vivo X200 Pro", 2024, "影像旗舰", "2024-10",
     "6.78 英寸 AMOLED · 1–120Hz", "天玑 9400",
     "5000 万主摄 + 2 亿潜望长焦 + 5000 万超广角",
     "6000 mAh", "90W 有线 / 30W 无线", "223 g", "OriginOS 5", 5299,
     "2 亿像素蔡司 APO 长焦", ["拍照视频", "长焦摄影", "续航"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("vivo-x200pm", "vivo", "vivo X200 Pro mini", 2024, "影像旗舰", "2024-10",
     "6.31 英寸 AMOLED · 1–120Hz", "天玑 9400",
     "5000 万主摄 + 5000 万潜望长焦 + 5000 万超广角",
     "5700 mAh", "90W 有线 / 30W 无线", "187 g", "OriginOS 5", 4699,
     "小尺寸影像旗舰，6.31 英寸直屏", ["拍照视频", "小屏手感", "日常全能"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("vivo-x100", "vivo", "vivo X100", 2023, "影像旗舰", "2023-11",
     "6.78 英寸 AMOLED · 1–120Hz", "天玑 9300",
     "5000 万主摄 + 6400 万潜望长焦 + 5000 万超广角",
     "5000 mAh", "100W 有线", "206 g", "OriginOS 4", 3999,
     "蔡司 APO 长焦下放到标准版", ["拍照视频", "日常全能"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("vivo-x100p", "vivo", "vivo X100 Pro", 2023, "影像旗舰", "2023-11",
     "6.78 英寸 AMOLED · 1–120Hz", "天玑 9300",
     "1 英寸 5000 万主摄 + 5000 万潜望长焦 + 5000 万超广角",
     "5400 mAh", "100W 有线 / 50W 无线", "221 g", "OriginOS 4", 4999,
     "1 英寸大底主摄 + 蔡司 APO 长焦", ["拍照视频", "长焦摄影", "日常全能"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("vivo-xfold5", "vivo", "vivo X Fold5", 2025, "折叠屏旗舰", "2025-07",
     "8.03 英寸内屏 + 6.53 英寸外屏 · 1–120Hz", "骁龙 8 Gen 3",
     "5000 万主摄 + 5000 万潜望长焦 + 5000 万超广角",
     "6000 mAh", "80W 有线 / 40W 无线", "217 g", "OriginOS 5", 6999,
     "轻薄大折叠，6000mAh 蓝海电池", ["大屏办公", "拍照视频", "续航"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("vivo-xfold3p", "vivo", "vivo X Fold3 Pro", 2024, "折叠屏旗舰", "2024-03",
     "8.03 英寸内屏 + 6.53 英寸外屏 · 1–120Hz", "骁龙 8 Gen 3",
     "5000 万主摄 + 6400 万潜望长焦 + 5000 万超广角",
     "5700 mAh", "100W 有线 / 50W 无线", "236 g", "OriginOS 4", 9999,
     "大折叠中的影像与快充堆料款", ["大屏办公", "拍照视频", "日常全能"],
     ["16GB+512GB", "16GB+1TB"], "16GB+512GB"),

    # ---------- OnePlus ----------
    ("op-ace5p", "OnePlus", "一加 Ace 5 Pro", 2024, "性能旗舰", "2024-12",
     "6.78 英寸 1.5K OLED · 120Hz", "骁龙 8 至尊版",
     "5000 万主摄 + 800 万超广角 + 200 万微距",
     "6100 mAh", "100W 有线", "217 g", "ColorOS 15", 3399,
     "骁龙 8 至尊版 + 6100mAh 的性能直屏机", ["游戏性能", "续航", "性价比"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("op-ace5", "OnePlus", "一加 Ace 5", 2024, "性能旗舰", "2024-12",
     "6.78 英寸 1.5K OLED · 120Hz", "骁龙 8 Gen 3",
     "5000 万主摄 + 800 万超广角 + 200 万微距",
     "6415 mAh", "80W 有线", "206 g", "ColorOS 15", 2299,
     "6415mAh 大电池的性能价位段机型", ["游戏性能", "续航", "性价比"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),

    # ---------- iQOO ----------
    ("iqoo-12", "iQOO", "iQOO 12", 2023, "游戏性能旗舰", "2023-11",
     "6.78 英寸 1.5K OLED · 144Hz", "骁龙 8 Gen 3",
     "5000 万主摄 + 6400 万潜望长焦 + 5000 万超广角",
     "5000 mAh", "120W 有线", "203 g", "OriginOS 4", 3999,
     "电竞向性能旗舰，加入潜望长焦", ["游戏性能", "拍照视频", "日常全能"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("iqoo-12p", "iQOO", "iQOO 12 Pro", 2023, "游戏性能旗舰", "2023-11",
     "6.78 英寸 2K OLED · 144Hz", "骁龙 8 Gen 3",
     "5000 万主摄 + 6400 万潜望长焦 + 5000 万超广角",
     "5100 mAh", "120W 有线 / 50W 无线", "210 g", "OriginOS 4", 4999,
     "2K 屏 + 无线充电的满配性能旗舰", ["游戏性能", "拍照视频", "日常全能"],
     ["16GB+512GB", "16GB+1TB"], "16GB+512GB"),
    ("iqoo-neo10p", "iQOO", "iQOO Neo10 Pro", 2024, "游戏性能旗舰", "2024-11",
     "6.78 英寸 1.5K OLED · 144Hz", "天玑 9400",
     "5000 万主摄 + 5000 万超广角",
     "6100 mAh", "120W 有线", "206 g", "OriginOS 5", 3199,
     "天玑 9400 + 自研电竞芯片的中端性能机", ["游戏性能", "续航", "性价比"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),

    # ---------- realme ----------
    ("realme-gt6", "realme", "真我 GT6", 2024, "性能旗舰", "2024-07",
     "6.78 英寸 1.5K OLED · 120Hz", "骁龙 8 Gen 3",
     "5000 万主摄 + 800 万超广角",
     "5800 mAh", "120W 有线", "207 g", "realme UI 5.0", 2799,
     "骁龙 8 Gen 3 的性能价位段直屏机", ["游戏性能", "续航", "性价比"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
    ("realme-gt7", "realme", "真我 GT7", 2025, "性能旗舰", "2025-04",
     "6.8 英寸 1.5K OLED · 144Hz", "天玑 9400+",
     "5000 万主摄 + 800 万超广角",
     "7000 mAh", "100W 有线", "203 g", "realme UI 6.0", None,
     "7000mAh 大电池的高刷性能机", ["游戏性能", "续航", "性价比"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),

    # ---------- nubia ----------
    ("redmagic-9p", "nubia", "红魔 9 Pro", 2023, "游戏性能旗舰", "2023-11",
     "6.8 英寸 OLED · 120Hz（屏下前摄）", "骁龙 8 Gen 3",
     "5000 万主摄 + 5000 万超广角 + 200 万微距",
     "6500 mAh", "80W 有线", "229 g", "RedMagic OS 9.0", 4399,
     "屏下前摄 + 主动散热的电竞旗舰", ["游戏性能", "续航", "日常全能"],
     ["12GB+256GB", "16GB+512GB", "16GB+1TB"], "12GB+256GB"),
]


def build_record(row: tuple) -> dict:
    (pid, brand, name, year, typ, launch, display, chip, camera, battery,
     charging, weight, os_name, price, selling, best_for, options, quote) = row
    if quote is not None and quote not in options:
        raise ValueError(f"{pid}: quoteTargetStorage {quote} 不在 storageOptions 内")
    return {
        "id": pid,
        "brand": brand,
        "name": name,
        "year": year,
        "type": typ,
        "market": "中国大陆正式销售",
        "display": display,
        "chip": chip,
        "camera": camera,
        "battery": battery,
        "charging": charging,
        "weight": weight,
        "storage": " / ".join(options),
        "os": os_name,
        "priceCN": price,
        "priceText": ("官方首发起售价（非当前售价，待官方发布稿复核）" if price
                      else "官方首发起售价待核验；不以当前渠道价代替"),
        "selling": selling,
        "bestFor": best_for,
        "source": SRC[brand],
        "sourceName": "厂商官方站点；字段核验状态见 auditStatus",
        "verified": False,
        "launchMonth": launch,
        "launchDateDisplay": f"{launch[:4]}年{launch[5:7]}月",
        "priceType": "official_launch_msrp" if price else "unknown",
        "livePrice": None,
        "livePriceStatus": "not_connected",
        "livePriceCheckedAt": None,
        "storageOptions": options,
        "chinaOfficial": True,
        "dataNote": ("本条机型身份与发布月份按厂商公开信息录入；参数与价格尚未完成官方规格页逐项核验，"
                     "标注“待复核”的字段不得视为已核实。排名与推荐资格保持关闭。"),
        "announcementSource": SRC[brand],
        "priceSource": SRC[brand] if price else None,
        "priceSourceName": ("厂商官方站点；首发价仍需官方发布稿二次核对" if price
                            else "来源页未直接支持该首发价，需补查官方发布稿"),
        "livePriceNote": "尚未接入获授权的实时渠道报价 API；请通过渠道入口核价",
        "scoreMethod": "heuristic_preliminary",
        "quoteTargetStorage": quote,
        "quoteTargetStorageReason": ("报价检索只接受商品标题中可核验的型号与这一指定大陆版 RAM/ROM 组合；"
                                     "未确定容量组合时不应触发报价检索。"),
        "auditStatus": "needs_parameter_price_audit",
        "auditNotes": [
            "机型身份与发布月份按厂商公开信息录入",
            "参数与价格尚未完成官方规格页逐项交叉核验",
            "排名与推荐资格保持关闭",
        ],
        "priceAuditStatus": ("source_present_needs_crosscheck" if price else "missing"),
        "parameterAuditStatus": "needs_source_crosscheck",
    }


def embed_html(path: Path, records: list[dict]) -> None:
    html = path.read_text(encoding="utf-8")
    m = re.search(r"window\.PHONE_DATA=(\[.*?\]);window\.MANUAL_QUOTES=", html, re.S)
    if not m:
        raise SystemExit(f"FAIL: {path.name} 未找到 PHONE_DATA")
    existing = json.loads(m.group(1))
    have = {p["id"] for p in existing}
    dup = have & {r["id"] for r in records}
    if dup:
        raise SystemExit(f"FAIL: {path.name} 已存在 {sorted(dup)}")
    base = m.group(1).rstrip()
    if not base.endswith("]"):
        raise SystemExit(f"FAIL: {path.name} PHONE_DATA 结构异常")
    body = json.dumps(records, ensure_ascii=False, separators=(",", ":"))[1:-1]  # 去掉外层 [ ]
    new_block = base[:-1] + "," + body + "]"
    json.loads(new_block)  # 落盘前先自检
    html = html[: m.start(1)] + new_block + html[m.end(1):]
    path.write_text(html, encoding="utf-8")


def main() -> None:
    catalog_path = ROOT / "data" / "phones.json"
    original = json.loads(catalog_path.read_text(encoding="utf-8"))
    have = {p["id"] for p in original}
    records = [build_record(row) for row in NEW]
    dup = have & {r["id"] for r in records}
    if dup:
        raise SystemExit(f"FAIL: 目录已存在 {sorted(dup)}")

    merged = original + records
    catalog_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for name in ("index.html", "phone-compare-demo.html"):
        embed_html(ROOT / name, records)
    print(f"PASS: {len(original)} -> {len(merged)} records; html embedded {len(records)}")


if __name__ == "__main__":
    main()
