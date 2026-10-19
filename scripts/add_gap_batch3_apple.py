#!/usr/bin/env python3
"""补齐缺失旗舰（第三批 6 款 Apple）：iPhone 13 / 13 Pro / 13 mini / 14 / 14 Plus / 15 Plus。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from add_gap_batch1 import build, patch_html  # noqa: E402


def row(pid, name, year, launch, typ, chip, screen, cam, weight, hours, os_name, options, selling, url, note):
    return dict(
        id=pid, brand="Apple", name=name, year=year, type=typ, launch=launch,
        display=f"{screen} 英寸 OLED", chip=chip, camera=cam,
        battery=f"官方未按 mAh 公布；视频播放最长 {hours} 小时", charging="USB-C / Lightning 有线充电 + MagSafe 无线充电",
        weight=weight, os=os_name, price=None, selling=selling,
        best_for=["拍照视频", "日常全能", "苹果生态"],
        options=options, quote=options[0], url=url,
        fields={
            "屏幕": (f"{screen} 英寸 OLED", note["屏幕"]),
            "处理器": (chip, note["处理器"]),
            "影像": (cam, note["影像"]),
            "电池": (f"官方未按 mAh 公布；视频播放最长 {hours} 小时", note["电池"]),
            "重量": (weight, note["重量"]),
            "容量组合": (" / ".join(options), note["容量组合"]),
        },
    )


ROWS = [
    row("apple-13", "iPhone 13", 2021, "2021-09", "标准旗舰", "A15 仿生", "6.1",
        "1200 万像素双摄系统", "173 克", 19, "iOS 15", ["128GB", "256GB", "512GB"],
        "A15 与双摄下放的标准旗舰", "https://support.apple.com/zh-cn/111872",
        {"屏幕": "规格页列出 6.1 英寸 OLED。", "处理器": "规格页列出 A15 仿生芯片。",
         "影像": "规格页列出两颗 1200 万像素后置镜头。", "电池": "规格页写明视频播放最长 19 小时，未公布 mAh。",
         "重量": "规格页列出重量 173 克。", "容量组合": "规格页列出 128GB/256GB/512GB。"}),
    row("apple-13p", "iPhone 13 Pro", 2021, "2021-09", "全能旗舰", "A15 仿生", "6.1",
        "1200 万像素三摄系统（含 3× 长焦）", "203 克", 22, "iOS 15",
        ["128GB", "256GB", "512GB", "1TB"], "ProMotion 高刷与三摄", "https://support.apple.com/zh-cn/111871",
        {"屏幕": "规格页列出 6.1 英寸 OLED 与 ProMotion。", "处理器": "规格页列出 A15 仿生芯片。",
         "影像": "规格页列出三颗 1200 万像素后置镜头。", "电池": "规格页写明视频播放最长 22 小时，未公布 mAh。",
         "重量": "规格页列出重量 203 克。", "容量组合": "规格页列出 128GB/256GB/512GB/1TB。"}),
    row("apple-13mini", "iPhone 13 mini", 2021, "2021-09", "标准旗舰", "A15 仿生", "5.4",
        "1200 万像素双摄系统", "140 克", 17, "iOS 15", ["128GB", "256GB", "512GB"],
        "5.4 英寸小屏旗舰", "https://support.apple.com/zh-cn/111873",
        {"屏幕": "规格页列出 5.4 英寸 OLED。", "处理器": "规格页列出 A15 仿生芯片。",
         "影像": "规格页列出两颗 1200 万像素后置镜头。", "电池": "规格页写明视频播放最长 17 小时，未公布 mAh。",
         "重量": "规格页列出重量 140 克。", "容量组合": "规格页列出 128GB/256GB/512GB。"}),
    row("apple-14", "iPhone 14", 2022, "2022-09", "标准旗舰", "A15 仿生", "6.1",
        "1200 万像素双摄系统", "172 克", 20, "iOS 16", ["128GB", "256GB", "512GB"],
        "标准尺寸的 14 代机型", "https://support.apple.com/zh-cn/111850",
        {"屏幕": "规格页列出 6.1 英寸 OLED。", "处理器": "规格页列出 A15 仿生芯片。",
         "影像": "规格页列出 1200 万像素双摄。", "电池": "规格页写明视频播放最长 20 小时，未公布 mAh。",
         "重量": "规格页列出重量 172 克。", "容量组合": "规格页列出 128GB/256GB/512GB。"}),
    row("apple-14plus", "iPhone 14 Plus", 2022, "2022-09", "标准旗舰", "A15 仿生", "6.7",
        "1200 万像素双摄系统", "203 克", 26, "iOS 16", ["128GB", "256GB", "512GB"],
        "6.7 英寸大屏长续航标准款", "https://support.apple.com/zh-cn/111854",
        {"屏幕": "规格页列出 6.7 英寸 OLED。", "处理器": "规格页列出 A15 仿生芯片。",
         "影像": "规格页列出 1200 万像素双摄。", "电池": "规格页写明视频播放最长 26 小时，未公布 mAh。",
         "重量": "规格页列出重量 203 克。", "容量组合": "规格页列出 128GB/256GB/512GB。"}),
    row("apple-15plus", "iPhone 15 Plus", 2023, "2023-09", "标准旗舰", "A16 仿生", "6.7",
        "4800 万像素主摄 + 1200 万像素超广角", "201 克", 26, "iOS 17", ["128GB", "256GB", "512GB"],
        "6.7 英寸大屏 + 4800 万主摄", "https://support.apple.com/zh-cn/111830",
        {"屏幕": "规格页列出 6.7 英寸 OLED。", "处理器": "规格页列出 A16 仿生芯片。",
         "影像": "规格页列出 4800 万像素主摄与 1200 万像素超广角。", "电池": "规格页写明视频播放最长 26 小时，未公布 mAh。",
         "重量": "规格页列出重量 201 克。", "容量组合": "规格页列出 128GB/256GB/512GB。"}),
]


def main() -> None:
    p = ROOT / "data" / "phones.json"
    catalog = json.loads(p.read_text(encoding="utf-8"))
    have = {r["id"] for r in catalog}
    records = [build(r) for r in ROWS if r["id"] not in have]
    if not records:
        raise SystemExit("FAIL: 已存在")
    catalog.extend(records)
    p.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name in ("index.html", "phone-compare-demo.html"):
        patch_html(ROOT / name, records)
    print(f"PASS: 新增 {len(records)} 款，总计 {len(catalog)}")


if __name__ == "__main__":
    main()
