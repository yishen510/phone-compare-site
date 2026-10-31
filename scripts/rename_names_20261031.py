#!/usr/bin/env python3
"""统一机型命名:品牌前缀 + 空格规范化。

仅改动 name 展示字段,不动参数/价格/审计/规格表。
规则(已与用户确认):
  - 华为: 统一 HUAWEI 前缀(去掉「华为」重复词)
  - 三星: 含 Galaxy 的写「三星 Galaxy …」;W 系列(心系天下)写「三星 W…」不加 Galaxy
  - 小米英系: Xiaomi 数字旗舰 / MIX 折叠 改为「小米 …」;红米英文系保持 REDMI
  - 华硕 ROG: 加「华硕 」前缀
  - 魅族 / 努比亚: 品牌词后补空格(如 魅族Lucky → 魅族 Lucky)
  - 通用兜底: 所有已知品牌词后紧接字母/数字时补一个空格
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--dry" in sys.argv

ALL = ["华为", "HUAWEI", "荣耀", "小米", "Xiaomi", "红米", "Redmi", "REDMI", "vivo", "OPPO",
       "真我", "realme", "iQOO", "三星", "Galaxy", "Samsung", "努比亚", "nubia", "红魔", "一加",
       "OnePlus", "Moto", "Motorola", "苹果", "Apple", "iPhone", "中兴", "ZTE", "魅族", "华硕",
       "ASUS", "麦芒", "酷派", "WIKO", "蔚来", "NIO", "Polestar"]


def norm(brand: str, name: str) -> str:
    s = name.strip()
    if brand == "Huawei":
        m = re.match(r"^(?:华为|HUAWEI)+", s)
        if m:
            rest = s[m.end():].lstrip()
            return ("HUAWEI " + rest) if rest else s
        return s
    if brand == "Samsung":
        has_galaxy = bool(re.search(r"Galaxy", s, re.I))
        m = re.match(r"^(?:三星|Galaxy|Samsung)+", s, re.I)
        rest = s[m.end():].lstrip() if m else s
        return ("三星 Galaxy " if has_galaxy else "三星 ") + rest
    if brand == "Xiaomi":
        if s.startswith("Xiaomi"):
            return "小米 " + s[len("Xiaomi"):].lstrip()
        if s.startswith("MIX"):
            return "小米 " + s
        if s.startswith("红米Redmi"):
            return "REDMI " + s[len("红米Redmi"):].lstrip()
        return s
    if brand == "ASUS":
        if s.startswith("ROG"):
            return "华硕 " + s
        return s
    if brand == "MEIZU":
        return re.sub(r"^(魅族)(?=[A-Za-z0-9])", r"\1 ", s)
    if brand == "nubia":
        return re.sub(r"^(努比亚)(?=[A-Za-z0-9])", r"\1 ", s)
    return s


def space_fix(s: str) -> str:
    for w in ALL:
        s = re.sub(r"(" + re.escape(w) + r")(?=[A-Za-z0-9])", r"\1 ", s)
    return s


def main() -> None:
    data = json.loads((ROOT / "data" / "phones.json").read_text(encoding="utf-8"))
    changes = []
    for p in data:
        nw = space_fix(norm(p["brand"], p["name"]))
        if nw != p["name"]:
            changes.append((p["id"], p["name"], nw))
            p["name"] = nw
    names = [p["name"] for p in data]
    dup = {n for n in names if names.count(n) > 1}
    if dup:
        print("ABORT: 改名后出现重复 name ->", dup)
        sys.exit(1)
    print(f"将变更 {len(changes)} 条" + (" [DRY RUN]" if DRY else ""))
    for i, o, n in changes:
        print(f"  {i:28s} | {o}  ->  {n}")
    if DRY:
        return
    # 保留源文件换行符(CRLF/LF)与缩进(indent=1),避免整文件 diff 爆炸
    raw_b = (ROOT / "data" / "phones.json").read_bytes()
    src_nl = "\r\n" if b"\r\n" in raw_b else "\n"
    text = json.dumps(data, ensure_ascii=False, indent=1).replace("\n", src_nl)
    (ROOT / "data" / "phones.json").write_text(text, encoding="utf-8", newline="")
    sys.path.insert(0, str(ROOT / "scripts"))
    from import_zol_params import patch_html
    # patch_html 会保留 index.html 原始换行符(body 段原样拼接)
    for f in ("index.html", "phone-compare-demo.html"):
        patch_html(ROOT / f, data, strict=False)
    print("已写回 data/phones.json 与 index.html / phone-compare-demo.html")


if __name__ == "__main__":
    main()
