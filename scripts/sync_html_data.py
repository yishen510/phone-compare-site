"""把主库里的新机型同步进 index.html 的内联数据。

流程：
  1) 从 data/phones.json 读完整数据（含 specs/fieldAudit）
  2) 写回 index.html 的 window.PHONE_DATA=[...]（全量形态）
  3) 调用方再跑 scripts/split_detail_data.py 拆成页面版 + 详情文件

为什么不直接把新记录塞进现有的拆分版页面数据：
  页面数据已经去掉了 specs/fieldAudit，拆分脚本对没有这两个字段的记录
  会直接跳过，详情文件永远生成不了。必须从主库重建。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "phones.json"
HTML = ROOT / "index.html"

records = json.loads(DB.read_text(encoding="utf-8"))
raw = HTML.read_text(encoding="utf-8")
m = re.search(r"window\.PHONE_DATA=(\[.*?\]);window\.MANUAL_QUOTES=", raw, re.S)
if not m:
    raise SystemExit("未找到 window.PHONE_DATA 块")

old = json.loads(m.group(1))
payload = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
out = raw[:m.start(1)] + payload + raw[m.end(1):]
out = out.replace("\r\n", "\n").replace("\n", "\r\n")
HTML.write_bytes(out.encode("utf-8"))
print(f"已注入 {len(records)} 条（原页面 {len(old)} 条，新增 {len(records)-len(old)} 条）")
