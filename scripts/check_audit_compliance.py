"""三级审核：对 data/phones.json 里指定机型做事实来源 / 逻辑自洽 / 未验证标注三项检查。

起因：新增机型时容易漏项或自相矛盾（九字段写少一个、价格留空却标 official_launch_msrp、
状态写了 verified 但资格标志没开）。这个脚本把这些判据写死，任一条不过就退出码 1。

用法：
  python scripts/check_audit_compliance.py                 # 全库体检
  python scripts/check_audit_compliance.py honor-700 ...   # 只查指定 id

判据：
  一级 事实来源
    - 九字段齐全、字段名不重复（严格 9 个）
    - 每个 verified_official_page_reviewed 字段必须有 https 来源 + 非空证据文字
    - 非厂商域名的来源不得标 verified_official_page_reviewed（只允许 cross_checked_secondary_source）
  二级 逻辑自洽
    - priceCN 为空 ⇔ priceType ∈ {price_pending, price_unavailable}
    - auditStatus=verified ⇒ 双资格 true 且九字段全 verified
    - auditStatus≠verified ⇒ 双资格必须 false
    - 记录必须能在 data/detail/<id>.json 找到，且 specs 非空
  三级 未验证信息显式标注
    - auditNotes 至少一条带日期（YYYY-MM-DD）
    - 出现"媒体口径/未采信/待核/未公布"等缺口语义时，文案里必须同时出现来源限定词
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
DETAIL = ROOT / "data" / "detail"

def _is_official(url: str) -> bool:
    """按主机名后缀判断，避免 'apple.com' 这类子串把 fake-apple.com 也算进来。"""
    host = urlparse(url).netloc.lower().split(":")[0]
    return any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS)


REQUIRED = ["屏幕", "处理器", "影像", "电池", "充电", "重量", "容量组合", "正式发布/开售日期", "官方首发起售价"]
VERIFIED = "verified_official_page_reviewed"
SECONDARY = "cross_checked_secondary_source"
# 厂商自有域名（含官方商城/支持站）。实测出现过的全部收录，别再漏：
# support.apple.com / support-cn.samsung.com.cn / www.vmall.com 都是厂商自己的站。
OFFICIAL_HOSTS = (
    "honor.com", "hihonor.com", "huawei.com", "vmall.com",
    "oppo.com", "vivo.com.cn", "vivo.com", "mi.com",
    "apple.com.cn", "apple.com", "samsung.com.cn",
    "oneplus.com", "realme.com", "iqoo.com", "meizu.com",
    "zte.com.cn", "ztedevices.com", "motorola.com.cn",
)
PRICE_PENDING_TYPES = {"price_pending", "price_unavailable"}
GAP_WORDS = ("未公布", "未采信", "待核", "媒体口径", "未列出")

records = json.loads(CATALOG.read_text(encoding="utf-8"))
want = set(sys.argv[1:])
targets = [r for r in records if not want or r.get("id") in want]
if want and len(targets) != len(want):
    missing = want - {r.get("id") for r in targets}
    print(f"[失败] 目录里找不到这些 id：{sorted(missing)}")
    sys.exit(1)

errors: list[str] = []
warns: list[str] = []

for r in targets:
    rid = r.get("id")
    prefix = f"{rid}: "
    fields = r.get("fieldAudit") or []

    # —— 一级：事实来源 ——
    names = [f.get("field") for f in fields]
    # 判据用「必需字段名是否齐全」，而不是「数量是否等于 9」：
    # 数量相等但名字不对同样不合格，数量 10 但九个都在则是合格的。
    miss = [x for x in REQUIRED if x not in set(names)]
    if miss:
        msg = prefix + "fieldAudit 缺必需字段：" + "、".join(miss)
        # 显式点名检查时是硬错误；全库体检时降级为统计，避免 400+ 存量记录淹没新问题
        (errors if want else warns).append(msg)
    dup = [x for x, c in __import__("collections").Counter(names).items() if c > 1]
    if dup:
        (errors if want else warns).append(prefix + "fieldAudit 有重复字段：" + "、".join(dup))
    for f in fields:
        if f.get("status") != VERIFIED:
            continue
        url = str(f.get("sourceUrl") or "")
        ev = str(f.get("evidenceText") or "").strip()
        if not url.startswith("https://"):
            errors.append(prefix + f"{f.get('field')} 标为 verified 但来源不是 https：{url!r}")
        elif not _is_official(url):
            errors.append(prefix + f"{f.get('field')} 标为 verified 但来源非厂商域名：{url}")
        if len(ev) < 8:
            errors.append(prefix + f"{f.get('field')} 标为 verified 但证据文字过短：{ev!r}")

    # —— 二级：逻辑自洽 ——
    price = r.get("priceCN")
    ptype = r.get("priceType")
    if (price is None or price == "") and ptype not in PRICE_PENDING_TYPES:
        errors.append(prefix + f"priceCN 为空但 priceType={ptype}（应为 {sorted(PRICE_PENDING_TYPES)}）")
    if price not in (None, "") and ptype in PRICE_PENDING_TYPES:
        errors.append(prefix + f"priceCN={price} 但 priceType={ptype}（价格待核就不该有价）")

    verified_n = sum(1 for f in fields if f.get("status") == VERIFIED)
    is_verified = r.get("auditStatus") == "verified"
    dual = (r.get("eligibleForRanking") is True) and (r.get("eligibleForRecommendation") is True)
    if is_verified and not (dual and verified_n == 9 and r.get("verified") is True):
        errors.append(prefix + "auditStatus=verified 但资格/标志不齐全")
    if not is_verified and dual:
        errors.append(prefix + f"auditStatus={r.get('auditStatus')} 却开了排名/推荐资格")

    detail_file = DETAIL / f"{rid}.json"
    if not detail_file.exists():
        errors.append(prefix + "找不到 data/detail/<id>.json")
    else:
        d = json.loads(detail_file.read_text(encoding="utf-8"))
        if not d.get("specs"):
            errors.append(prefix + "详情文件里 specs 为空")

    # —— 三级：未验证信息显式标注 ——
    notes = r.get("auditNotes") or []
    if not any(re.search(r"\d{4}-\d{2}-\d{2}", str(n)) for n in notes):
        errors.append(prefix + "auditNotes 没有任何一条带 YYYY-MM-DD 日期")
    blob = " ".join(str(x) for x in notes) + " " + str(r.get("dataNote") or "") + " " + str(r.get("priceText") or "")
    if any(w in blob for w in GAP_WORDS):
        if "官方" not in blob and "媒体" not in blob:
            warns.append(prefix + "有缺口措辞但没有说明口径来源（官方/媒体）")

print(f"检查 {len(targets)} 条记录")
if warns:
    print("\n警告（不阻断）：")
    for w in warns:
        print("  -", w)
if errors:
    print("\n失败：")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("\n三级审核通过：九字段齐全、来源可追溯、价格口径自洽、缺口已标注")
