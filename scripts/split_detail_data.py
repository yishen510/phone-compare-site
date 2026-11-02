"""把详情才用的字段从内联数据里拆出去，首屏只留列表字段。

为什么要拆：4.19MB 内联数据里 specs 占 56%、fieldAudit 占 25%，而列表卡片只用 4.8%。
4G 下 609KB 的下载里九成是这些"点开某一台才需要"的东西。

关键约束：**推荐打分依赖 specs**（recScreen / recMp / AI功能 都读它）。
所以拆之前要把派生值算好写回记录：
  rs = 屏幕尺寸（英寸）   rm = 最大像素（万）   ra = AI 相关条目数
否则拆完打分结果会悄悄变样。

用法：python scripts/split_detail_data.py [--dry]
幂等：已拆过的记录（没有 specs/fieldAudit）会跳过。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"
DETAIL_DIR = ROOT / "data" / "detail"
DRY = "--dry" in sys.argv

SRC = HTML.read_text(encoding="utf-8")
MARK = "window.PHONE_DATA="
i = SRC.find(MARK)
if i < 0:
    raise SystemExit("未找到 window.PHONE_DATA")
arr_start = SRC.find("[", i)
arr, arr_end = json.JSONDecoder().raw_decode(SRC, arr_start)

INCH = re.compile(r"(\d+(?:\.\d+)?)\s*英寸")


def screen_inch(p: dict):
    for g in p.get("specs") or []:
        for it in g.get("items") or []:
            if isinstance(it, list) and len(it) > 1 and "屏幕尺寸" in str(it[0]):
                m = INCH.search(str(it[1]))
                if m:
                    return float(m.group(1))
    m = INCH.search(str(p.get("display") or ""))
    return float(m.group(1)) if m else None


def max_mp(p: dict):
    texts = [str(p.get("camera") or "")]
    for g in p.get("specs") or []:
        for it in g.get("items") or []:
            if not (isinstance(it, list) and len(it) > 1):
                continue
            if re.search(r"摄像头|像素|后置", str(it[0])):
                texts.append(str(it[1]))
    best = 0
    for t in texts:
        for x in re.findall(r"(\d{3,4})\s*万像素", t):
            best = max(best, int(x))
        for x in re.findall(r"(\d+(?:\.\d+)?)\s*亿像素", t):
            best = max(best, int(float(x) * 10000))
        for x in re.findall(r"(\d{1,2})\s*MP", t, re.I):
            n = int(x)
            best = max(best, n * 100 if n < 200 else n)
    return best or None


def ai_hits(p: dict):
    n = 0
    for g in p.get("specs") or []:
        for it in g.get("items") or []:
            if isinstance(it, list) and re.search(r"AI|智能", str(it[0]) + str(it[1] if len(it) > 1 else ""), re.I):
                n += 1
    return n


slim = []
moved = 0
detail_files = {}

for p in arr:
    rec = dict(p)
    has_specs = "specs" in rec
    has_audit = "fieldAudit" in rec
    if not has_specs and not has_audit:
        slim.append(rec)
        continue
    # 先算派生值，再抽走原始数据
    if rec.get("rs") is None:
        v = screen_inch(rec)
        if v is not None:
            rec["rs"] = v
    if rec.get("rm") is None:
        v = max_mp(rec)
        if v is not None:
            rec["rm"] = v
    if rec.get("ra") is None:
        rec["ra"] = ai_hits(rec)

    detail = {}
    if has_specs:
        detail["specs"] = rec.pop("specs")
        moved += 1
    if has_audit:
        detail["fieldAudit"] = rec.pop("fieldAudit")
    detail_files[str(rec.get("id"))] = detail
    slim.append(rec)

payload = json.dumps(slim, ensure_ascii=False, separators=(",", ":"))
before = len(json.dumps(arr, ensure_ascii=False, separators=(",", ":")).encode())
after = len(payload.encode())
print(f"记录 {len(arr)} 条，其中 {moved} 条带规格")
print(f"内联数组 {before/1048576:.2f}MB → {after/1048576:.2f}MB（-{(1-after/before)*100:.0f}%）")
print(f"拆出 {len(detail_files)} 个详情文件")

if DRY:
    raise SystemExit(0)

DETAIL_DIR.mkdir(parents=True, exist_ok=True)
for pid, d in detail_files.items():
    (DETAIL_DIR / f"{pid}.json").write_text(
        json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

out = SRC[:arr_start] + payload + SRC[arr_end:]
out = out.replace("\r\n", "\n").replace("\n", "\r\n")
HTML.write_bytes(out.encode("utf-8"))
print("index.html 已更新")
