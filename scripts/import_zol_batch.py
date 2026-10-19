#!/usr/bin/env python3
"""批量导入中关村在线参数页为新机型记录（第三方核验）。

输入：URL 列表文件（每行一个），输出：新增记录 + 目录。
自动从页面标题取机型名、从「上市日期」取年月，按品牌关键词归类；
目录中已有的同名机型会跳过，不覆盖原有数据。
"""
from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126",
      "Accept-Language": "zh-CN"}
NOTE = "第三方参数站（中关村在线）核对，非厂商官方页面；仅供交叉参考，不构成整机准入依据。"
BRANDS = [("HUAWEI", "Huawei"), ("华为", "Huawei"), ("Redmi", "Xiaomi"), ("红米", "Xiaomi"),
          ("小米", "Xiaomi"), ("Samsung", "Samsung"), ("三星", "Samsung"), ("OPPO", "OPPO"),
          ("vivo", "vivo"), ("荣耀", "Honor"), ("一加", "OnePlus"), ("iQOO", "iQOO"),
          ("realme", "realme"), ("真我", "realme"), ("努比亚", "nubia"), ("红魔", "nubia")]


def text_of(url: str) -> tuple[str, str]:
    raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
    h = raw.decode("gbk", "ignore")
    title = re.search(r"<title>(.*?)</title>", h, re.S)
    body = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    body = html.unescape(body)
    return (title.group(1) if title else ""), re.sub(r"\s+", " ", body)


def parse(title: str, t: str) -> dict:
    name = re.split(r"参数】", title.replace("【", ""))[0].strip()
    name = re.sub(r"\s*\d+\s*GB\s*/\s*\d+\s*(?:GB|TB).*$", "", name).strip()
    name = re.sub(r"\s*\d+\s*GB\s*[+/]\s*\d+\s*G.*$", "", name).strip()
    name = re.sub(r"\s*(?:全网通|5G版|全网通/5G版).*$", "", name).strip()
    brand = next((b for k, b in BRANDS if k.lower() in name.lower()), "Other")
    date = re.search(r"上市日期\s*(\d{4})年(\d{1,2})月", t)
    screen = re.search(r"屏幕尺寸.{0,40}?([5-9]\.\d+)英寸", t) or re.search(r"([5-9]\.\d+)英寸", t)
    hz = re.search(r"屏幕刷新率\s*(\d{2,3})Hz", t)
    chip = re.search(r"CPU型号\s*(.+?)\s*(?:更多|纠错|，)", t)
    bat = re.search(r"电池容量\s*(\d{3,5})mAh", t)
    chg = re.search(r"有线充电\s*([0-9.]+)\s*[wW]", t)
    wl = re.search(r"无线充电\s*([0-9.]+)\s*[wW]", t)
    wt = re.findall(r"([0-9]{2,3}(?:\.[0-9])?g)", t[t.find("重量"):t.find("重量") + 120]) if "重量" in t else []
    ram = re.search(r"RAM容量\s*([0-9]+GB)", t)
    rom = re.findall(r"ROM容量\s*([^ ]{2,60})", t)
    return {
        "name": name, "brand": brand,
        "year": int(date.group(1)) if date else None,
        "month": f"{date.group(1)}-{int(date.group(2)):02d}" if date else None,
        "screen": f"{screen.group(1)} 英寸" if screen else None,
        "hz": f"{hz.group(1)}Hz" if hz else None,
        "chip": chip.group(1).strip() if chip else None,
        "battery": f"{bat.group(1)} mAh" if bat else None,
        "charging": (f"{chg.group(1)}W 有线" + (f" / {wl.group(1)}W 无线" if wl else "")) if chg else None,
        "weight": " / ".join(dict.fromkeys(wt[:2])) if wt else None,
        "ram": ram.group(1) if ram else None,
        "rom": rom[0][:40] if rom else None,
    }


def make(pid: str, url: str, d: dict) -> dict:
    typ = "折叠屏旗舰" if re.search(r"Fold|Flip|折叠", d["name"], re.I) else (
        "影像旗舰" if re.search(r"Ultra", d["name"], re.I) else "全能旗舰")
    disp = d["screen"] or "官方规格页待补"
    if d["screen"] and d["hz"]:
        disp = f"{d['screen']} · {d['hz']}"
    fields = {}
    if d["screen"]:
        fields["屏幕"] = disp
    if d["chip"]:
        fields["处理器"] = d["chip"]
    if d["battery"]:
        fields["电池"] = d["battery"]
    if d["charging"]:
        fields["充电"] = d["charging"]
    if d["weight"]:
        fields["重量"] = d["weight"]
    audit = [{"field": k, "value": v, "status": "cross_checked_secondary_source",
              "sourceUrl": url, "evidenceText": f"第三方参数页列出：{v}。",
              "valueAtAudit": v, "note": NOTE} for k, v in fields.items()]
    return {
        "id": pid, "brand": d["brand"], "name": d["name"], "year": d["year"] or 0, "type": typ,
        "market": "中国大陆正式销售", "display": disp, "chip": d["chip"] or "待核验",
        "camera": "第三方参数页未逐项整理镜头组合，待核验",
        "battery": d["battery"] or "待核验", "charging": d["charging"] or "待核验",
        "weight": d["weight"] or "待核验", "storage": d["rom"] or "待核验", "os": "以官方页面为准",
        "priceCN": None, "priceText": "官方首发起售价待核验；不以当前渠道价代替",
        "selling": "第三方参数页补录", "bestFor": ["日常全能"],
        "source": url, "sourceName": "中关村在线参数页（第三方）", "verified": False,
        "launchMonth": d["month"] or "待核验",
        "launchDateDisplay": (f"{d['year']}年{int(d['month'][5:7])}月" if d["month"] else "待核验"),
        "priceType": "unknown", "livePrice": None, "livePriceStatus": "not_connected",
        "livePriceCheckedAt": None, "storageOptions": [], "chinaOfficial": True,
        "dataNote": "机型由中关村在线参数页补录，字段为第三方来源，未经厂商官方页核对。",
        "announcementSource": None, "priceSource": None, "priceSourceName": "暂无可靠的首发价来源",
        "livePriceNote": "尚未接入获授权的实时渠道报价 API；请通过渠道入口核价",
        "scoreMethod": "heuristic_preliminary", "quoteTargetStorage": None,
        "quoteTargetStorageReason": "未确认官方容量组合与型号写法，不触发报价检索。",
        "auditStatus": "needs_parameter_price_audit",
        "auditNotes": ["由中关村在线参数页补录，第三方来源", "参数与首发价未经厂商官方页核对", "整机准入保持关闭"],
        "priceAuditStatus": "missing", "parameterAuditStatus": "partial_secondary_source",
        "fieldAudit": audit,
    }


def norm(s: str) -> str:
    return re.sub(r"[\s\-（）()]+", "", s).lower()


def main() -> None:
    urls = [u.strip() for u in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if "zol.com.cn" in u]
    p = ROOT / "data" / "phones.json"
    catalog = json.loads(p.read_text(encoding="utf-8"))
    have = {norm(r["name"]) for r in catalog}
    ids = {r["id"] for r in catalog}
    added = []
    for url in urls:
        seg = re.search(r"/(\d+)/(\d+)/param", url)
        try:
            title, body = text_of(url)
            d = parse(title, body)
        except Exception as exc:  # noqa: BLE001
            print("FAIL", url[-30:], str(exc)[:30])
            continue
        key = norm(d["name"])
        if not d["name"] or key in have:
            print("SKIP", d["name"] or url[-20:])
            continue
        pid = f"{d['brand'].lower()}-z{seg.group(1)}{seg.group(2)}" if seg else f"zol-{len(added)}"
        if pid in ids:
            continue
        added.append(make(pid, url, d))
        have.add(key)
        print(f"ADD {d['brand']:<8} {d['name'][:26]:<28} {d['month'] or '-':<8} {d['battery'] or '-':<12} {d['weight'] or '-'}")
    if not added:
        print("NO NEW")
        return
    catalog.extend(added)
    p.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name in ("index.html", "phone-compare-demo.html"):
        html_s = (ROOT / name).read_text(encoding="utf-8")
        m = re.search(r"window\.PHONE_DATA=(\[.*?\]);window\.MANUAL_QUOTES=", html_s, re.S)
        base = m.group(1).rstrip()
        body = json.dumps(added, ensure_ascii=False, separators=(",", ":"))[1:-1]
        block = base[:-1] + "," + body + "]"
        json.loads(block)
        (ROOT / name).write_text(html_s[: m.start(1)] + block + html_s[m.end(1):], encoding="utf-8")
    print(f"PASS: 新增 {len(added)} 款，总计 {len(catalog)}")


if __name__ == "__main__":
    main()
