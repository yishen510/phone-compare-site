"""把详情才用的字段从内联数据里拆出去，首屏只留列表字段。

为什么要拆：4.19MB 内联数据里 specs 占 56%、fieldAudit 占 25%，而列表卡片只用 4.8%。
4G 下 609KB 的下载里九成是这些"点开某一台才需要"的东西。

关键约束：**推荐打分依赖 specs**（recScreen / recMp / AI功能 都读它）。
所以拆之前要把派生值算好写回记录：
  rs = 屏幕尺寸（英寸）   rm = 最大像素（万）   ra = AI 相关条目数
否则拆完打分结果会悄悄变样。

另外两件事（2026-11-21 补）：
1) 内联只保留页面真正会读的字段（INLINE_DROP 里的审计台账字段一律剔除，
   它们留在 data/phones.json）。实测能减掉整页 34% 的体积。
2) 从 specs 里提炼**特征位** ft（IP68 / 潜望 / 无线充 …）。规格全文索引实测
   gzip 134–181KB，比整页还大，不可行；特征位只要 ~8KB 就能让
   「搜索框承诺的参数关键词」真正可搜。

用法：python scripts/split_detail_data.py [--dry]
幂等：
  - 已拆过的记录（没有 specs/fieldAudit）会跳过，但仍会做字段裁剪
  - 详情文件只在内容真的变了才写盘，避免每次重跑都产生几百个文件的 diff
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

# 这些字段只有审计脚本和人会读，页面 JS 一次都不读（逐字段在 index.html 里 count 过）。
# 剔除后整页 1.42MB → 932KB、gzip 164KB → 131KB。真值仍在 data/phones.json。
INLINE_DROP = {
    "auditNotes",
    "quoteTargetStorage",
    "quoteTargetStorageReason",
    "announcementSource",
    "storageOptions",
    "priceAuditStatus",
    "parameterAuditStatus",
    "scoreMethod",
    "sourceName",
    "priceSourceName",
    "sourceAudit",
    "officialSpecSource",
    "livePriceUrl",
    # 报价层已关闭：这条提示在 493 条记录里逐字重复，页面不再渲染占位卡片，留着纯属体积
    "livePriceNote",
    "launchPromoPrice",
    "launchPromoPriceText",
    "launchPromoPriceSource",
}

# 特征位：id → (中文名, 命中别名)。别名全部小写，按子串匹配规格全文。
# 只收"用户真的会拿去搜"的特征；收之前都用 data/detail 实算过覆盖数，
# 覆盖为 0 的（USB 3 / 毫米波 / 手写笔）已经去掉，不留空钩子。
FEATURE_TERMS = [
    ("ip68", "IP68 防尘防水", ("ip68",)),
    ("ip69", "IP69 高温高压防水", ("ip69",)),
    ("ip66", "IP66 防尘防水", ("ip66",)),
    ("ltpo", "LTPO 自适应刷新", ("ltpo", "promotion")),
    ("ltpo8t", "8T LTPO", ("8t ltpo", "8tltpo")),
    ("periscope", "潜望长焦", ("潜望",)),
    ("ultrasonic", "超声波指纹", ("超声波",)),
    ("wireless", "无线充电", ("无线充", "无线超级快充")),
    ("reverse", "无线反向充电", ("反向充",)),
    ("satellite", "卫星通信", ("卫星",)),
    ("ir", "红外遥控", ("红外",)),
    ("nfc", "NFC", ("nfc",)),
    ("uwb", "UWB 超宽带", ("uwb", "超宽频")),
    ("ufs4", "UFS 4.0", ("ufs 4", "ufs4")),
    ("lpddr5x", "LPDDR5X", ("lpddr5x",)),
    ("dolby", "杜比视界", ("杜比",)),
    ("vc", "VC 液冷散热", ("vc ", "vc液冷", "vc 液冷")),
    ("wifi7", "Wi-Fi 7", ("wi-fi 7", "wifi7", "wifi 7")),
    ("ois", "光学防抖", ("光学防抖", "ois")),
    ("pwm", "高频 PWM 调光", ("pwm",)),
    ("curved", "曲面屏", ("曲面",)),
    ("fold", "折叠屏", ("折叠",)),
    ("esim", "eSIM", ("esim",)),
    ("tof", "ToF 镜头", ("tof",)),
    ("dual", "双卡双待", ("双卡",)),
]


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


def spec_text(p: dict) -> str:
    """规格全文小写串，只用来算特征位。"""
    buf = []
    for g in p.get("specs") or []:
        buf.append(str(g.get("group") or ""))
        for it in g.get("items") or []:
            if isinstance(it, list):
                buf.extend(str(x) for x in it)
            else:
                buf.append(str(it))
    return " ".join(buf).lower()


def feature_flags(p: dict):
    text = spec_text(p)
    if not text:
        return None
    hits = [fid for fid, _label, aliases in FEATURE_TERMS if any(a in text for a in aliases)]
    return hits or None


slim = []
moved = 0
detail_files = {}
with_specs = 0
total_items = 0

for p in arr:
    rec = dict(p)
    has_specs = "specs" in rec
    has_audit = "fieldAudit" in rec
    if not has_specs and not has_audit:
        # 已拆过的记录：只补特征位（老数据没有 ft 时用现有字段兜底，通常为空）
        if rec.get("ft") is None:
            ft = feature_flags(rec)
            if ft:
                rec["ft"] = ft
        for k in INLINE_DROP:
            rec.pop(k, None)
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
    if rec.get("ft") is None:
        ft = feature_flags(rec)
        if ft:
            rec["ft"] = ft

    if has_specs:
        with_specs += 1
        for g in rec["specs"]:
            total_items += len(g.get("items") or [])

    detail = {}
    if has_specs:
        detail["specs"] = rec.pop("specs")
        moved += 1
    if has_audit:
        detail["fieldAudit"] = rec.pop("fieldAudit")
    detail_files[str(rec.get("id"))] = detail
    for k in INLINE_DROP:
        rec.pop(k, None)
    slim.append(rec)

payload = json.dumps(slim, ensure_ascii=False, separators=(",", ":"))
before = len(json.dumps(arr, ensure_ascii=False, separators=(",", ":")).encode())
after = len(payload.encode())
print(f"记录 {len(arr)} 条，其中 {moved} 条带规格，特征位覆盖 {sum(1 for r in slim if r.get('ft'))} 条")
print(f"内联数组 {before/1048576:.2f}MB → {after/1048576:.2f}MB（-{(1-after/before)*100:.0f}%）")

if DRY:
    raise SystemExit(0)

DETAIL_DIR.mkdir(parents=True, exist_ok=True)
written = 0
for pid, d in detail_files.items():
    target = DETAIL_DIR / f"{pid}.json"
    text = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    if target.exists() and target.read_text(encoding="utf-8") == text:
        continue                      # 内容没变就别碰，避免几百个文件的无意义 diff
    target.write_text(text, encoding="utf-8")
    written += 1
print(f"详情文件 {len(detail_files)} 个，实际写盘 {written} 个")

out = SRC[:arr_start] + payload + SRC[arr_end:]

# 「数据说明」面板要的统计值：specs 拆走之后首屏算不出来，由构建期写死。
if with_specs:
    stats = json.dumps(
        {"models": with_specs, "items": total_items,
         "avg": round(total_items / with_specs, 1) if with_specs else 0},
        ensure_ascii=False, separators=(",", ":"),
    )
    new_out, n = re.subn(r"const SPEC_STATS=\{[^}]*\};", f"const SPEC_STATS={stats};", out)
    if not n:
        raise SystemExit("未找到 const SPEC_STATS={...} 占位，无法写入统计值")
    out = new_out
    print(f"SPEC_STATS = {stats}")

out = out.replace("\r\n", "\n").replace("\n", "\r\n")
HTML.write_bytes(out.encode("utf-8"))
print("index.html 已更新")
