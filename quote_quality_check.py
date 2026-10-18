#!/usr/bin/env python3
"""Live quote smoke-test and four-metric quality audit.

An authorized API response is required to compute API quote coverage and automatic
rule pass rate. Human page-audit fields in reports/quote_quality_manual_review.csv
are intentionally separate and never inferred from API/search snippets.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import socket
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import price_server as ps

ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT / "reports"
CN_TZ = timezone(timedelta(hours=8))
PAGE_PRICE_TOLERANCE_RMB = 1.00
MANUAL_AUDIT_MAX_AGE_HOURS = 24

DEFAULT_SAMPLE_IDS = [
    "apple-17pm", "sam-25u", "xia-15u", "hua-mate70p", "honor-magic7-pro",
    "oppo-x8u", "op-13", "vivo-x200u", "realme-gt7-pro",
]
MANUAL_FIELDS = [
    "productPageOpened", "pageDisplayedPrice", "pagePriceCheckTime",
    "productPagePriceMatches", "mainlandNewUnitConfirmed",
    "exactStorageConfirmedOnPage", "stockConfirmed", "promotionConditionsClear",
    "reviewerVerdict", "reviewerNotes",
]
CSV_FIELDS = [
    "phoneId", "model", "targetStorage", "offerTitle", "apiPrice", "channel",
    "checkedAt", "url", "autoQualityPass", "autoFailures", *MANUAL_FIELDS,
]


def is_placeholder(value: str) -> bool:
    value = (value or "").strip().casefold()
    return not value or value.startswith(("replace_", "your_", "填入"))


def parse_yes_no(value: Any) -> bool | None:
    if value is None:
        return None
    text = str(value).strip().casefold()
    if text in {"1", "true", "yes", "y", "是", "通过", "有效", "可购买", "正常", "已确认"}:
        return True
    if text in {"0", "false", "no", "n", "否", "未通过", "无效", "不可购买", "售罄", "无货", "未确认"}:
        return False
    return None


def as_float(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    return ps.parse_price(value)


def parse_time(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=CN_TZ)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def check_url(url: str, timeout: float = 8.0) -> dict[str, Any]:
    """Best-effort HTTPS reachability check; retailer anti-bot blocks are inconclusive."""
    from urllib.parse import urlparse

    parsed = urlparse(url or "")
    if parsed.scheme != "https" or not parsed.hostname:
        return {"status": "invalid_url", "finalUrl": None}
    request = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; PhoneCompareQuoteAudit/1.1)",
        "Range": "bytes=0-512",
    }, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            final_url = response.geturl()
            final = urlparse(final_url)
            return {
                "status": "reachable" if response.status < 400 else "http_error",
                "httpStatus": response.status,
                "finalUrl": final_url,
                "sameHttpsHostFamily": final.scheme == "https" and bool(final.hostname),
            }
    except HTTPError as exc:
        status = "blocked_or_restricted" if exc.code in (401, 403, 405, 429) else "http_error"
        return {"status": status, "httpStatus": exc.code, "finalUrl": exc.geturl()}
    except (URLError, TimeoutError, socket.timeout) as exc:
        return {"status": "network_inconclusive", "detail": str(exc)[:160], "finalUrl": None}


def audit_item(item: dict[str, Any], phone: dict[str, Any], check_links: bool) -> dict[str, Any]:
    title = str(item.get("offerTitle") or "")
    target = ps.first_storage_target(phone) or ""
    aliases = ps.model_aliases(phone)
    normalized_title = ps.normalize(title)
    model_match = any(alias and alias in normalized_title for alias in aliases)
    sku_match = ps.offer_matches_sku(title, target)
    price = ps.parse_price(item.get("price"))
    url = str(item.get("url") or "")
    valid_url = ps.safe_offer_url(url)
    channel = str(item.get("channel") or "").strip()
    checked_at = str(item.get("checkedAt") or "")
    timestamp_ok = False
    age_seconds = None
    try:
        stamp = datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        age_seconds = max(0, (datetime.now(timezone.utc) - stamp.astimezone(timezone.utc)).total_seconds())
        timestamp_ok = age_seconds <= 3600
    except ValueError:
        pass

    checks = {
        "model_match": model_match,
        "storage_match": sku_match,
        "price_numeric_and_sane": price is not None,
        "https_product_url": valid_url,
        "channel_present": bool(channel),
        "timestamp_within_1h": timestamp_ok,
        "not_rejected_by_filter": not ps.reject_offer(title, ps.EXCLUDE_TERMS_DEFAULT),
    }
    failures = [key for key, passed in checks.items() if not passed]
    result: dict[str, Any] = {
        "phoneId": phone.get("id"), "model": phone.get("name"),
        "targetStorage": target, "offerTitle": title, "price": price,
        "channel": channel, "checkedAt": checked_at,
        "ageSeconds": round(age_seconds) if age_seconds is not None else None,
        "url": url, "checks": checks, "failures": failures,
        "qualityPass": not failures,
    }
    if check_links and valid_url:
        result["urlCheck"] = check_url(url)
    return result


def load_review_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", newline="", encoding="utf-8-sig") as fh:
            return list(csv.DictReader(fh))
    except (OSError, csv.Error):
        return []


def review_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("phoneId") or ""), str(row.get("url") or "")


def metric_manual_review(rows: list[dict[str, Any]], requested_ids: set[str]) -> dict[str, Any]:
    """Compute manual metrics only for current quote URLs reviewed within 24 hours."""
    now = datetime.now(timezone.utc)
    page_price_rows = []
    link_review_rows = []
    stale_or_incomplete = 0
    for row in rows:
        if str(row.get("phoneId") or "") not in requested_ids or not str(row.get("url") or "").strip():
            continue
        opened = parse_yes_no(row.get("productPageOpened"))
        api_price = as_float(row.get("apiPrice"))
        page_price = as_float(row.get("pageDisplayedPrice"))
        checked = parse_time(row.get("pagePriceCheckTime"))
        fresh = checked is not None and (now - checked).total_seconds() <= MANUAL_AUDIT_MAX_AGE_HOURS * 3600
        if opened is True and api_price is not None and page_price is not None and fresh:
            match = abs(api_price - page_price) <= PAGE_PRICE_TOLERANCE_RMB
            row["productPagePriceMatches"] = "Yes" if match else "No"
            page_price_rows.append({"match": match, "phoneId": row.get("phoneId"), "deltaRmb": round(page_price - api_price, 2)})
        elif opened is True and (row.get("productPagePriceMatches") or "").strip() and fresh:
            # Allow explicit human override when price cannot be parsed (e.g. price hidden behind login),
            # but only include affirmative/negative values with a documented recent page check.
            explicit = parse_yes_no(row.get("productPagePriceMatches"))
            if explicit is not None:
                page_price_rows.append({"match": explicit, "phoneId": row.get("phoneId"), "deltaRmb": None})

        main_new = parse_yes_no(row.get("mainlandNewUnitConfirmed"))
        exact_sku = parse_yes_no(row.get("exactStorageConfirmedOnPage"))
        in_stock = parse_yes_no(row.get("stockConfirmed"))
        if opened is False:
            # A recent, explicit failed page-open is a reviewed invalid link.
            link_review_rows.append({"valid": False, "phoneId": row.get("phoneId")})
        elif opened is True and all(v is not None for v in (main_new, exact_sku, in_stock)) and fresh:
            link_review_rows.append({
                "valid": bool(main_new and exact_sku and in_stock),
                "phoneId": row.get("phoneId"),
            })
        else:
            stale_or_incomplete += 1

    page_price_passes = sum(1 for x in page_price_rows if x["match"])
    link_passes = sum(1 for x in link_review_rows if x["valid"])
    return {
        "pagePriceConsistencyRate": round(page_price_passes / len(page_price_rows), 4) if page_price_rows else None,
        "pagePriceConsistencyNumerator": page_price_passes,
        "pagePriceConsistencyDenominator": len(page_price_rows),
        "pagePriceToleranceRmb": PAGE_PRICE_TOLERANCE_RMB,
        "pagePriceFreshnessHours": MANUAL_AUDIT_MAX_AGE_HOURS,
        "validPurchasableLinkRate": round(link_passes / len(link_review_rows), 4) if link_review_rows else None,
        "validPurchasableLinkNumerator": link_passes,
        "validPurchasableLinkDenominator": len(link_review_rows),
        "manualReviewRowsStaleOrIncomplete": stale_or_incomplete,
        "manualReviewPolicy": "页面价格一致率需有 24 小时内的页面实价与 API 价格，差值≤¥1；有效可购买链接率需近期确认商品页已打开、国行新机、精确存储版本、存在库存/购买路径。未审核或过期记录不计入分母。",
    }


def write_manual_csv(path: Path, results: list[dict[str, Any]], existing_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    existing_by_key = {review_key(row): row for row in existing_rows if row.get("url")}
    current_rows: list[dict[str, str]] = []
    current_keys: set[tuple[str, str]] = set()
    for result in results:
        row = {
            "phoneId": result.get("phoneId", ""), "model": result.get("model", ""),
            "targetStorage": result.get("targetStorage", ""), "offerTitle": result.get("offerTitle", ""),
            "apiPrice": result.get("price", ""), "channel": result.get("channel", ""),
            "checkedAt": result.get("checkedAt", ""), "url": result.get("url", ""),
            "autoQualityPass": result.get("qualityPass", False),
            "autoFailures": ";".join(result.get("failures", [])),
        }
        key = review_key(row)
        current_keys.add(key)
        old = existing_by_key.get(key, {})
        for field in MANUAL_FIELDS:
            row[field] = old.get(field, "")
        page_price = as_float(row.get("pageDisplayedPrice"))
        api_price = as_float(row.get("apiPrice"))
        page_opened = parse_yes_no(row.get("productPageOpened"))
        checked = parse_time(row.get("pagePriceCheckTime"))
        fresh = checked is not None and (datetime.now(timezone.utc) - checked).total_seconds() <= MANUAL_AUDIT_MAX_AGE_HOURS * 3600
        if page_opened is True and page_price is not None and api_price is not None and fresh:
            row["productPagePriceMatches"] = "Yes" if abs(page_price - api_price) <= PAGE_PRICE_TOLERANCE_RMB else "No"
        current_rows.append({field: str(row.get(field, "")) for field in CSV_FIELDS})

    # Retain older manual audits when today's API did not return that URL; do not destroy user-entered review data.
    for old in existing_rows:
        key = review_key(old)
        if key in current_keys or not old.get("url"):
            continue
        keep = {field: str(old.get(field, "")) for field in CSV_FIELDS}
        if not keep.get("model"):
            keep["model"] = keep.get("offerTitle", "")
        current_rows.append(keep)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(current_rows)
    return current_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="真实报价 API 联调与四项质量指标验收")
    parser.add_argument("--ids", help="逗号分隔的 phones.json 机型 ID")
    parser.add_argument("--all", action="store_true", help="查询数据库全部机型；可能消耗更多 API 配额")
    parser.add_argument("--check-links", action="store_true", help="逐一访问 API 返回的直达商品链接")
    parser.add_argument("--no-report", action="store_true", help="只打印摘要，不写 JSON/CSV 报告")
    args = parser.parse_args()

    ps.load_env_file()
    api_key = os.getenv("HAINAN_API_KEY", "")
    phone_map = ps.phones_by_id()
    if args.all:
        ids = list(phone_map.keys())
    elif args.ids:
        ids = list(dict.fromkeys(x.strip() for x in args.ids.split(",") if x.strip()))
    else:
        ids = DEFAULT_SAMPLE_IDS
    unknown = [x for x in ids if x not in phone_map]
    if unknown:
        print("未知机型 ID: " + ", ".join(unknown), file=sys.stderr)
        return 2

    credentials_present = not is_placeholder(api_key)
    if credentials_present:
        combined_items: list[dict[str, Any]] = []
        batch_messages: list[str] = []
        api_status = "no_exact_offers"
        for start in range(0, len(ids), 5):
            batch_payload = ps.query_prices(ids[start:start + 5])
            combined_items.extend(x for x in batch_payload.get("items", []) if isinstance(x, dict))
            batch_messages.append(str(batch_payload.get("message") or ""))
            if batch_payload.get("status") == "upstream_error":
                api_status = "upstream_error"
                break
            if batch_payload.get("status") == "ok":
                api_status = "ok"
        payload = {
            "asOf": ps.now_iso(),
            "provider": "hainan_discount_v2",
            "status": api_status,
            "message": "；".join(x for x in batch_messages if x),
            "items": combined_items,
        }
    else:
        payload = {
            "asOf": ps.now_iso(), "provider": "hainan_discount_v2",
            "status": "needs_credentials",
            "message": "未检测到有效的 HAINAN_API_KEY。未发起请求；四项 API 报价指标不能计算。请项目所有者在本地 .env 中配置轮换后的海纳 API Key。",
            "items": [],
        }

    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    by_id = {str(x.get("phoneId")): x for x in items if isinstance(x, dict)}
    results: list[dict[str, Any]] = []
    for phone_id in ids:
        phone = phone_map[phone_id]
        quote = by_id.get(phone_id)
        if quote:
            results.append(audit_item(quote, phone, args.check_links))
        else:
            results.append({
                "phoneId": phone_id, "model": phone.get("name"),
                "targetStorage": ps.first_storage_target(phone),
                "qualityPass": False, "failures": ["no_quote_returned"],
                "reason": payload.get("message", "API 未返回该型号精确容量报价"),
            })

    passing = sum(1 for r in results if r.get("qualityPass") and "price" in r)
    quoted = sum(1 for r in results if "price" in r)
    api_was_tested = credentials_present and payload.get("status") in {"ok", "no_exact_offers"}
    old_review_rows = load_review_csv(REPORT_DIR / "quote_quality_manual_review.csv")
    # If API was not queried, leave any prior manually annotated CSV intact; create a template only if absent.
    if not args.no_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        review_path = REPORT_DIR / "quote_quality_manual_review.csv"
        if api_was_tested or not review_path.exists():
            csv_rows = write_manual_csv(review_path, results, old_review_rows)
        else:
            csv_rows = old_review_rows
            if not csv_rows:
                csv_rows = write_manual_csv(review_path, results, old_review_rows)
        manual_metrics = metric_manual_review(csv_rows, set(ids))
    else:
        csv_rows = old_review_rows
        manual_metrics = metric_manual_review(csv_rows, set(ids))

    quote_coverage = round(quoted / len(ids), 4) if ids and api_was_tested else None
    auto_pass_rate = round(passing / quoted, 4) if quoted else None
    report = {
        "createdAt": ps.now_iso(), "provider": payload.get("provider"),
        "apiStatus": payload.get("status"), "apiMessage": payload.get("message"),
        "credentialsPresent": credentials_present, "apiWasActuallyTested": api_was_tested,
        "requestedModels": len(ids), "returnedQuotes": quoted,
        "qualityPassingQuotes": passing,
        "metrics": {
            "quoteCoverageRate": quote_coverage,
            "quoteCoverageNumerator": quoted if api_was_tested else None,
            "quoteCoverageDenominator": len(ids) if api_was_tested else None,
            "automaticRulePassRate": auto_pass_rate,
            "automaticRulePassNumerator": passing if quoted else None,
            "automaticRulePassDenominator": quoted if quoted else None,
            **manual_metrics,
        },
        "metricDefinitions": {
            "quoteCoverageRate": "精确型号+容量的 API 报价机型数 / 本轮请求机型数；没有真实 API 调用时为 null，不将未授权算作 0%。",
            "automaticRulePassRate": "通过型号、存储、数值价格、HTTPS、商城、时间与排除规则的报价数 / API 返回报价数。",
            "pagePriceConsistencyRate": "24小时内人工录入商品页实价且与 API 报价差值≤¥1 的条数 / 有可比较实价的条数。",
            "validPurchasableLinkRate": "24小时内确认页面打开、国行新机、容量准确且有库存/购买路径的链接数 / 已完成页面审核的 API 商品链接数。",
        },
        "items": results,
    }
    summary = {
        "status": report["apiStatus"], "credentialsPresent": credentials_present,
        "apiWasActuallyTested": api_was_tested, "requestedModels": len(ids),
        "returnedQuotes": quoted, "qualityPassingQuotes": passing,
        "metrics": report["metrics"], "message": report["apiMessage"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if not args.no_report:
        out = REPORT_DIR / "quote_quality_latest.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"详细报告已写入: {out}")
        print(f"人工抽检表已写入/保留: {REPORT_DIR / 'quote_quality_manual_review.csv'}")
        if not credentials_present:
            print("提示：无授权时本次 API 指标留空，不会把未执行的测试报告为 0% 或通过。")
    return 0 if api_was_tested and payload.get("status") == "ok" and quoted > 0 and passing == quoted else (2 if not credentials_present else 1)


if __name__ == "__main__":
    raise SystemExit(main())
