# -*- coding: utf-8 -*-
"""把用户在「待补价格机型填写表」里填的 15 条价格录入目录。

用户填写路径：只填 G 列参考价 + H 列容量，未填中关村参数页链接。
因此统一按 priceType=third_party_reference 记账，价格来源标注为「用户按中关村在线
参考价填写」，不冒充官方首发价。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "phones.json"
HTMLS = [ROOT / "index.html", ROOT / "phone-compare-demo.html"]

FIELD = "官方首发起售价"
TAG = "2026-10-20 按用户填写表补入参考价"
SRC_NAME = "用户按中关村在线参考价填写（2026-10-20 填写表；未附参数页链接）"
PRICE_TEXT = "中关村在线参考价（非官方首发价，仅供比价参考）"

# id: (价格, 容量)
FILLED = {
    "apple-13":      (5999,  "128GB"),
    "apple-13mini":  (5199,  "128GB"),
    "apple-13-pro":  (7999,  "128GB"),
    "apple-14":      (5999,  "128GB"),
    "apple-14plus":  (6999,  "128GB"),
    "apple-15plus":  (6999,  "128GB"),
    "sam-zf5":       (12999, "512GB"),
    "sam-zflip5":    (8499,  "256GB"),
    "redmi-k70":     (2499,  "256GB"),
    "redmi-k70-pro": (3299,  "256GB"),
    "redmi-k60-pro": (3299,  "128GB"),
    "vivo-x90":      (3699,  "128GB"),
    "vivo-xfold2":   (8999,  "256GB"),
    "hua-matex5":    (12999, "256GB"),
    "oppo-x6":       (4999,  "256GB"),
}

# 与官方首发时的容量-价格搭配存在出入、需向用户回问的两条
CONFLICT_NOTE = {
    "sam-zf5": "用户填写为 512GB/12999 元；官方 2023-07 首发时 12999 元对应 12GB+256GB，"
               "512GB 为 13999 元，容量与价格搭配待与中关村页面核对。",
    "sam-zflip5": "用户填写为 256GB/8499 元；官方 2023-07 首发时 8GB+256GB 为 7499 元、"
                  "8GB+512GB 为 8499 元，容量与价格搭配待与中关村页面核对。",
}


def main():
    records = json.loads(DATA.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in records}
    missing = [k for k in FILLED if k not in by_id]
    if missing:
        sys.exit("未找到记录: %s" % missing)

    for rid, (price, cap) in FILLED.items():
        r = by_id[rid]
        r["priceCN"] = price
        r["priceType"] = "third_party_reference"
        r["priceText"] = PRICE_TEXT
        r["priceAuditStatus"] = "secondary_source_reference"
        r["priceSource"] = ""
        r["priceSourceName"] = SRC_NAME
        # 容量：写成 RAM+ROM 前的单值也保留原样，便于回溯
        if not r.get("storage") or r.get("storage", "").startswith("官方容量组合待复核"):
            r["storage"] = cap

        ev = ("用户在《待补价格机型填写表》中填入参考价 %d 元、容量 %s，来源为中关村在线页面；"
              "未提供参数页链接，故按第三方参考价记录，不作为官方首发价。" % (price, cap))
        if rid in CONFLICT_NOTE:
            ev += "⚠ " + CONFLICT_NOTE[rid]
        note = ("第三方参考价，未经厂商官方页核对；" +
                ("容量与价格搭配存疑，待核。" if rid in CONFLICT_NOTE else "缺参数页链接，待补。"))

        fa = r.get("fieldAudit")
        if not isinstance(fa, list):
            fa = []
        entry = next((e for e in fa if isinstance(e, dict) and e.get("field") == FIELD), None)
        if entry is None:
            entry = {"field": FIELD}
            fa.append(entry)
        entry.update({
            "value": "%d元（%s，第三方参考价）" % (price, cap),
            "status": "unverified_missing_or_insufficient_official_evidence",
            "sourceUrl": "",
            "evidenceText": ev,
            "note": note,
        })
        r["fieldAudit"] = fa

        notes = r.get("auditNotes") if isinstance(r.get("auditNotes"), list) else []
        if not any(TAG in x for x in notes):
            notes.append("%s：%d元 / %s（第三方参考价，缺链接）" % (TAG, price, cap))
        r["auditNotes"] = notes

    DATA.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("已录入 %d 条；有价 %d / %d" % (
        len(FILLED), sum(1 for r in records if r.get("priceCN")), len(records)))

    # 整体替换内嵌数据（切勿沿用旧的拼接写法，会成倍重复）
    block = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
    for hp in HTMLS:
        html = hp.read_text(encoding="utf-8")
        m = re.search(r"window\.PHONE_DATA=(\[.*?\]);window\.MANUAL_QUOTES=", html, re.S)
        if not m:
            sys.exit("未在 %s 找到 PHONE_DATA 块" % hp.name)
        html2 = html[:m.start(1)] + block + html[m.end(1):]
        m2 = re.search(r"window\.PHONE_DATA=(\[.*?\]);window\.MANUAL_QUOTES=", html2, re.S)
        if json.loads(m2.group(1)) != records:
            sys.exit("%s 内嵌数据自检失败" % hp.name)
        hp.write_text(html2, encoding="utf-8")
        print("已同步", hp.name)


if __name__ == "__main__":
    main()
