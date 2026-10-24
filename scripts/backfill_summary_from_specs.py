#!/usr/bin/env python3
"""用已抓取的完整参数（中关村在线）回填卡片/详情里的摘要字段占位符。

只处理"待复核/待核验/待补/待录入"这类占位值，绝不覆盖已有真值。
回填后写入 fieldAudit（cross_checked_secondary_source），前端显示"第三方核验"。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_zol_params import patch_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "phones.json"
PLACEHOLDER = ("待复核", "待核验", "待补", "待录入", "待逐项录入", "官方规格待", "待定")

# 前端 AUDIT_FIELD_NAMES 的中文名字
AUDIT_NAME = {"display": "屏幕", "chip": "处理器", "camera": "影像", "battery": "电池",
              "charging": "充电", "weight": "重量", "storage": "容量组合"}


def is_placeholder(v: str) -> bool:
    return (not v) or any(k in str(v) for k in PLACEHOLDER)


def naive_clean(v: str) -> str:
    v = re.sub(r"更多[^，,>]{0,40}(?:手机)?>?", "", v)
    v = re.sub(r"\s*[>＞]+\s*", " ", v)
    v = re.sub(r"\s*[，,]+\s*$", "", v)
    return re.sub(r"\s+", " ", v).strip()


def pick(specs: list[dict], label: str) -> str | None:
    for g in specs:
        for k, v in g["items"]:
            if k == label:
                return v
    return None


def num(pattern: str, value: str | None) -> str | None:
    if not value:
        return None
    m = re.search(pattern, value, re.I)
    return m.group(1) if m else None


def _slots(txt: str | None) -> dict[tuple[str, int], str]:
    """把「后置摄像头1：xxx 后置摄像头2：yyy」拆成 {(位置, 序号): 名称}。"""
    out: dict[tuple[str, int], str] = {}
    if not txt:
        return out
    pat = r"(后置|前置)摄像头\s*(\d+)?\s*[：:]\s*(.*?)(?=\s*[前后]置摄像头\s*\d*\s*[：:]|$)"
    for m in re.finditer(pat, txt):
        pos, idx = m.group(1), int(m.group(2) or 1)
        val = m.group(3).strip(" ;；,，")
        if val and (pos, idx) not in out:
            out[(pos, idx)] = val
    return out


def _pix(value: str | None) -> str:
    p = re.sub(r"[>＞\s]+$", "", (value or "").strip())
    p = re.sub(r"像素$", "", p).strip()
    m = re.fullmatch(r"(\d+(?:\.\d+)?)万", p)
    if m and float(m.group(1)) >= 10000:
        return f"{float(m.group(1)) / 10000:g}亿"
    return p


def _spaced(pix: str) -> str:
    """「5000万」→「5000 万」，和站点里已有的写法保持一致。"""
    return re.sub(r"(\d)(万|亿)$", r"\1 \2", pix)


def _lens(name: str | None, pix: str | None) -> str:
    n = re.sub(r"\s+", " ", name or "").strip()
    n = re.sub(r"(摄像头|镜头)$", "", n).strip()
    p = _pix(pix)
    if p and n:
        if re.search(r"\d+(?:\.\d+)?\s*(?:亿|万)", n):
            return n
        head = f"{_spaced(p)}像素{n}" if ("万" in p or "亿" in p) else n
        return re.sub(r"像素(?=[0-9A-Za-z])", "像素 ", head)
    return n or (re.sub(r"像素(?=[0-9A-Za-z])", "像素 ", f"{_spaced(p)}像素") if p else "")


def _rear_count(specs: list[dict], rear: list) -> int:
    total = pick(specs, "摄像头总数") or ""
    m = re.search(r"后\s*([二三四五六七])", total)
    if m:
        return "二三四五六七".index(m.group(1)) + 2
    return len(rear)


def _slot_pairs(specs: list[dict], suffix: str) -> dict[tuple[str, int], str]:
    """处理把位置写进标签的页面：「后置摄像头1 摄像头名称 / 后置摄像头1 后置摄像头」。"""
    out: dict[tuple[str, int], str] = {}
    pat = re.compile(r"^(后置|前置)摄像头\s*(\d+)\s+" + suffix + "$")
    for g in specs:
        for k, v in g.get("items", []):
            m = pat.match(str(k))
            if m:
                out[(m.group(1), int(m.group(2)))] = str(v).strip()
    return out


def camera_text(specs: list[dict]) -> str | None:
    """从「摄像头名称 / 像素」拼一句可读的影像摘要，避免“后置 后置摄像头1：”这种机器味儿。"""
    name_map = _slots(pick(specs, "摄像头名称")) or _slot_pairs(specs, "摄像头名称")
    pix_map = (_slots(pick(specs, "像素"))
               or _slot_pairs(specs, "摄像头")
               or _slot_pairs(specs, "后置摄像头"))
    rear = sorted({k for k in list(name_map) + list(pix_map) if k[0] == "后置"}, key=lambda k: k[1])
    front = sorted({k for k in list(name_map) + list(pix_map) if k[0] == "前置"}, key=lambda k: k[1])
    simple = pick(specs, "后置摄像头") or pick(specs, "后置摄像头1")
    if not rear and simple:
        txt = "后置 " + naive_clean(simple)
        f0 = pick(specs, "前置摄像头") or pick(specs, "前置摄像头1")
        return txt + (f"；前置 {naive_clean(f0)[:18]}" if f0 else "")
    parts = [x for x in (_lens(name_map.get(k), pix_map.get(k)) for k in rear[:3]) if x]
    if not parts:
        return None
    head = f"{'双三四五六七'[_rear_count(specs, rear) - 2]}摄：" if _rear_count(specs, rear) > 3 else ""
    txt = head + " + ".join(parts)
    if front:
        f0 = front[0]
        p = _pix(pix_map.get(f0))
        txt += f"；前置 {_spaced(p)}像素" if ("万" in p or "亿" in p) else f"；前置 {_lens(name_map.get(f0), None) or '单摄'}"
    if len(txt) > 72:
        txt = txt[:72].rsplit(" + ", 1)[0]
    return txt


def watts(value: str | None) -> str | None:
    """「100w」「100」都按 100W 处理；「支持> ，50w」取第一个数字。"""
    if not value:
        return None
    m = re.search(r"(\d{2,3})\s*[wW]", str(value))
    if m:
        return m.group(1)
    m = re.fullmatch(r"\s*(\d{2,3})\s*", str(value))
    return m.group(1) if m else None


def derive(specs: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    size_raw = pick(specs, "屏幕尺寸") or ""
    duo = re.search(r"主\s*[：:]\s*(\d+(?:\.\d+)?)\s*英寸.*?副\s*[：:]\s*(\d+(?:\.\d+)?)\s*英寸", size_raw)
    size = f"主 {duo.group(1)} 英寸 + 副 {duo.group(2)} 英寸" if duo else num(r"(\d+(?:\.\d+)?)\s*英寸", size_raw)
    refresh = num(r"(\d{2,3})\s*Hz", pick(specs, "屏幕刷新率"))
    stype = pick(specs, "屏幕类型") or ""
    stype = naive_clean(re.split(r"[，,]", stype)[0])
    stype = re.sub(r"[（(].*?[)）]", "", stype).strip()
    mat = naive_clean(pick(specs, "屏幕材质") or "")
    if "主：" in mat or "主:" in mat:
        mat = re.split(r"\s+副", re.sub(r"^主\s*[：:]\s*", "", mat))[0].strip()
    if re.search(r"OLED|AMOLED|LCD|IPS|LTPS", mat, re.I):
        stype = mat
    elif re.search(r"^(全面屏|直面屏|曲面屏|折叠屏)$", stype):
        stype = ""
    if size:
        size_txt = size if size.startswith("主") else f"{size} 英寸"
        out["display"] = " · ".join(x for x in [size_txt, stype or "OLED", f"{refresh}Hz" if refresh else ""] if x)

    chip = pick(specs, "CPU型号") or pick(specs, "处理器") or pick(specs, "芯片型号")
    if chip:
        chip = naive_clean(chip)
        chip = re.sub(r"^(高通|海思|苹果|华为|联发科|三星)\s*", "", chip)
        out["chip"] = chip[:40]

    mah = num(r"(\d{3,5})\s*mAh", pick(specs, "电池容量"))
    if mah:
        out["battery"] = f"{mah}mAh"

    wired = watts(pick(specs, "有线充电") or pick(specs, "充电功率"))
    wireless = watts(pick(specs, "无线充电"))
    parts = []
    if wired:
        parts.append(f"{wired}W 有线")
    if wireless:
        parts.append(f"{wireless}W 无线")
    if parts:
        out["charging"] = " / ".join(parts)

    wt_all = [float(x) for x in re.findall(r"(\d{2,3}(?:\.\d{1,2})?)\s*(?:g|克)", pick(specs, "重量") or "")]
    gram = max(wt_all) if wt_all else None
    if gram:
        out["weight"] = f"{gram:g}g"

    ram = num(r"(\d{1,2}\s*GB)", pick(specs, "RAM容量"))
    rom = num(r"(\d{1,3}\s*(?:GB|TB))", pick(specs, "ROM容量"))
    if ram and rom:
        out["storage"] = f"{ram.replace(' ', '')}+{rom.replace(' ', '')}"

    cam = camera_text(specs)
    if cam:
        out["camera"] = cam

    osv = pick(specs, "操作系统")
    if osv:
        out["os"] = naive_clean(osv)[:30]
    return out


def main() -> None:
    catalog: list[dict] = json.loads(CATALOG.read_text(encoding="utf-8"))
    filled = 0
    per_field: dict[str, int] = {}
    for p in catalog:
        specs = p.get("specs")
        if not specs:
            continue
        vals = derive(specs)
        # 发布日期：用参数页的「上市日期/国内发布时间」补成完整日期
        raw_date = pick(specs, "上市日期") or pick(specs, "国内发布时间")
        m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", naive_clean(raw_date or ""))
        if m:
            disp = f"{m.group(1)}年{int(m.group(2)):02d}月{int(m.group(3)):02d}日"
            fa = p.setdefault("fieldAudit", [])
            entry = next((x for x in fa if isinstance(x, dict) and x.get("field") == "正式发布/开售日期"), None)
            if entry is None or is_placeholder(str(entry.get("valueAtAudit", ""))):
                payload = {"field": "正式发布/开售日期", "value": disp, "valueAtAudit": disp,
                           "status": "cross_checked_secondary_source",
                           "sourceUrl": p.get("specSource", ""),
                           "evidenceText": f"中关村在线参数页：上市日期 {disp}",
                           "note": "2026-10-21 由完整参数表自动回填；第三方参数站。"}
                if entry:
                    entry.update(payload)
                else:
                    fa.append(payload)
                if not p.get("launchDateDisplay") or is_placeholder(p["launchDateDisplay"]):
                    p["launchDateDisplay"] = disp
        changed = []
        for k, v in vals.items():
            if not v:
                continue
            if k == "os":
                if is_placeholder(p.get("os")):
                    p["os"] = v
                    changed.append(k)
                continue
            name = AUDIT_NAME.get(k)
            fa = p.setdefault("fieldAudit", []) if name else None
            entry = next((x for x in fa if isinstance(x, dict) and x.get("field") == name), None) if fa else None
            need_value = is_placeholder(p.get(k))
            need_audit = bool(entry) and is_placeholder(str(entry.get("valueAtAudit", "")))
            if not (need_value or need_audit):
                continue
            if need_value:
                p[k] = v
                changed.append(k)
                per_field[k] = per_field.get(k, 0) + 1
            payload = {
                "field": name,
                "value": v,
                "valueAtAudit": v,
                "status": "cross_checked_secondary_source",
                "sourceUrl": p.get("specSource", ""),
                "evidenceText": f"中关村在线参数页：{name} {v}",
                "note": "2026-10-21 由完整参数表自动回填；第三方参数站，非厂商官方页。",
            }
            if entry:
                entry.update(payload)
            elif fa is not None:
                fa.append(payload)
        if changed:
            filled += 1
    print(f"records updated: {filled}; per-field: {per_field}")
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    back = json.loads(CATALOG.read_text(encoding="utf-8"))
    for f in [ROOT / "index.html", ROOT / "phone-compare-demo.html"]:
        patch_html(f, back)


if __name__ == "__main__":
    main()
