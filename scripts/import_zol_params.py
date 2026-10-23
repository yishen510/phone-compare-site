#!/usr/bin/env python3
"""把中关村在线「参数页」的完整参数表（分组 + 字段）导入目录与 HTML 内嵌数据。

与 import_zol_batch.py 的区别：那个只抽 5-6 个摘要字段；本脚本保留 ZOL 的全部分组，
原样落到每条记录的 `specs` 字段：

    "specs": [{"group": "基本参数", "items": [["上市日期", "2026年08月28日"], ...]}, ...]

目标机型来源（按优先级）：
1) 命令行显式指定：`python scripts/import_zol_params.py hua-purax=https://detail.zol.com.cn/2176/2175582/param.shtml`
2) 目录中已保存的 ZOL param 链接（source / priceSource / fieldAudit[].sourceUrl 等）

写盘前会重新解析 JSON 核对条数与 specs 数量，防止把内嵌数组写坏。
"""
from __future__ import annotations

import html as H
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
HTML_FILES = [ROOT / "index.html", ROOT / "phone-compare-demo.html"]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126",
      "Accept-Language": "zh-CN"}
SOURCE_NAME = "中关村在线参数页（第三方核验）"
GROUP_HINTS = {"基本参数", "外形", "硬件", "屏幕", "摄像头", "网络与连接", "网络",
               "电池与续航", "电池", "功能与服务", "手机附件", "保修信息", "包装清单"}


def clean(x: str) -> str:
    x = H.unescape(re.sub(r"<[^>]+>", " ", x)).replace("\xa0", " ")
    x = re.sub(r"\s*纠错\s*$", "", x)
    x = re.sub(r"\s*(?:查看外观|手机性能排行|游戏运行流畅)\s*>?\s*$", "", x)
    x = re.sub(r"\s*更多[^>]{0,24}>\s*$", "", x)
    x = re.sub(r"\s*\d+(?:\.\d+)?万张照片\s*\d+(?:\.\d+)?万首歌曲\s*$", "", x)
    return re.sub(r"\s+", " ", x).strip()


def fetch(url: str) -> str:
    raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()
    return raw.decode("gbk", "ignore")


def parse_specs(h: str) -> list[dict]:
    groups: list[dict] = []
    cur: dict | None = None
    for _attr, inner in re.findall(r"<tr([^>]*)>(.*?)</tr>", h, re.S):
        if "<th" not in inner:  # 分组标题行：<td colspan=2>基本参数</td>
            g = clean(inner)
            if 2 <= len(g) <= 10 and (g in GROUP_HINTS or not any(ch.isdigit() for ch in g)):
                cur = {"group": g, "items": []}
                groups.append(cur)
            continue
        th = re.search(r"<th[^>]*>(.*?)</th>", inner, re.S)
        td = re.search(r"<td[^>]*>(.*?)</td>", inner, re.S)
        if th and td and cur is not None:
            k, v = clean(th.group(1)), clean(td.group(1))
            if k and v:
                cur["items"].append([k, v])
    return [g for g in groups if g["items"]]


def find_zol_url(p: dict) -> str | None:
    for k, v in p.items():
        if isinstance(v, str) and "zol.com.cn" in v and "param.shtml" in v:
            return v
        if isinstance(v, list):
            for it in v:
                if isinstance(it, dict):
                    for vv in it.values():
                        if isinstance(vv, str) and "zol.com.cn" in vv and "param.shtml" in vv:
                            return vv
    return None


def patch_html(path: Path, catalog: list[dict], strict: bool = True) -> None:
    """用 raw_decode 精确定位内嵌数组边界，整体替换后再回读校验。"""
    if not path.is_file():
        return
    html = path.read_text(encoding="utf-8")
    marker = "window.PHONE_DATA="
    i = html.find(marker)
    if i < 0:
        print(f"SKIP {path.name}: no PHONE_DATA")
        return
    j = i + len(marker)
    old, end = json.JSONDecoder().raw_decode(html[j:])
    if strict and len(old) != len(catalog):
        raise SystemExit(f"FAIL {path.name}: embedded {len(old)} != catalog {len(catalog)}")
    body = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))
    new_html = html[:j] + body + html[j + end:]
    check, _ = json.JSONDecoder().raw_decode(new_html[j:])
    if len(check) != len(catalog):
        raise SystemExit(f"FAIL {path.name}: rewrite count mismatch")
    path.write_text(new_html, encoding="utf-8")
    print(f"PATCH {path.name}: {len(check)} records, {sum(1 for x in check if x.get('specs'))} with specs")


def main() -> None:
    extra: dict[str, str] = {}
    for arg in sys.argv[1:]:
        if "=" in arg and "http" in arg:
            pid, url = arg.split("=", 1)
            extra[pid.strip()] = url.strip()

    catalog: list[dict] = json.loads(CATALOG.read_text(encoding="utf-8"))
    targets: list[tuple[dict, str]] = []
    for p in catalog:
        url = extra.get(p["id"]) or find_zol_url(p)
        if url:
            targets.append((p, url))
    print(f"targets: {len(targets)}")

    ok = fail = 0
    for idx, (p, url) in enumerate(targets, 1):
        try:
            specs = parse_specs(fetch(url))
            if not specs:
                print(f"[{idx}/{len(targets)}] EMPTY {p['id']}")
                fail += 1
                continue
            p["specs"] = specs
            p["specSource"] = url
            p["specSourceName"] = SOURCE_NAME
            p["specFieldCount"] = sum(len(g["items"]) for g in specs)
            p["specCollectedAt"] = "2026-10-20"
            p.setdefault("auditNotes", []).append(
                f"2026-10-20 补录完整参数表：{len(specs)} 组 / {p['specFieldCount']} 项（{SOURCE_NAME}）")
            ok += 1
            print(f"[{idx}/{len(targets)}] OK {p['id']}: {len(specs)} groups / {p['specFieldCount']} items")
        except Exception as exc:  # noqa: BLE001
            fail += 1
            print(f"[{idx}/{len(targets)}] FAIL {p['id']}: {str(exc)[:70]}")
        time.sleep(0.35)

    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    back = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert len(back) == len(catalog), "catalog count changed"
    print(f"SAVED catalog: {len(back)} records, {sum(1 for x in back if x.get('specs'))} with specs")

    for f in HTML_FILES:
        patch_html(f, back)

    print(f"DONE ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
