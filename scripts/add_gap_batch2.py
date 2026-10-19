#!/usr/bin/env python3
"""补齐缺失旗舰（第二批 2 款）：Redmi K70、Redmi K60 Pro。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from add_gap_batch1 import build, patch_html  # noqa: E402

ROWS = [
    dict(
        id="redmi-k70", brand="Xiaomi", name="REDMI K70", year=2023, type="性能旗舰",
        launch="2023-11", display="6.67 英寸 · 120Hz", chip="骁龙 8 移动平台",
        camera="官方规格页未逐项列出镜头组合，待核验",
        battery="5000 mAh", charging="120W 有线快充", weight="209 g",
        os="MIUI 14", price=None, selling="2K 直屏的标准版性能机",
        best_for=["游戏性能", "续航", "性价比"],
        options=["12GB+256GB", "16GB+512GB", "16GB+1TB"], quote="12GB+256GB",
        url="https://www.mi.com/redmi-k70/specs",
        fields={"屏幕": ("6.67 英寸，120Hz", "官方规格页列出 6.67 英寸屏幕与 120Hz。"),
                "处理器": ("骁龙 8 移动平台", "官方规格页列出骁龙 8 移动平台。"),
                "电池": ("5000 mAh", "官方规格页列出 5000mAh（典型值）。"),
                "充电": ("120W 有线", "官方规格页列出 120W 有线快充。"),
                "重量": ("209 g", "官方规格页列出重量 209g。")},
    ),
    dict(
        id="redmi-k60-pro", brand="Xiaomi", name="REDMI K60 Pro", year=2022, type="性能旗舰",
        launch="2022-12", display="6.67 英寸 · 120Hz", chip="骁龙 8 移动平台",
        camera="官方规格页未逐项列出镜头组合，待核验",
        battery="5000 mAh", charging="120W 有线 + 30W 无线", weight="205 g / 201 g（版本不同）",
        os="MIUI 14", price=None, selling="120W + 30W 无线的性能旗舰",
        best_for=["游戏性能", "续航", "性价比"],
        options=["8GB+128GB", "8GB+256GB", "12GB+256GB", "12GB+512GB"], quote="12GB+256GB",
        url="https://www.mi.com/redmi-k60-pro/specs",
        fields={"屏幕": ("6.67 英寸，120Hz", "官方规格页列出 6.67 英寸屏幕与 120Hz。"),
                "处理器": ("骁龙 8 移动平台", "官方规格页列出骁龙 8 移动平台。"),
                "电池": ("5000 mAh", "官方规格页列出 5000mAh（典型值）。"),
                "充电": ("120W 有线 / 30W 无线", "官方规格页列出 120W 秒充与 30W 无线秒充。"),
                "重量": ("205 g / 201 g（版本不同）", "官方规格页按版本列出 205g 与 201g。")},
    ),
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
