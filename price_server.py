#!/usr/bin/env python3
"""Local web server + server-side Hainan discount-search Pro v2 adapter.

Only set HAINAN_API_KEY on the server. Never send it to the browser.
The provider returns search offers, not a guaranteed checkout price; all matched offers include
an exact model/storage check, direct offer URL and query timestamp.
"""
from __future__ import annotations

import json
import os
import re
import time
import unicodedata
import uuid
from threading import Lock
from datetime import datetime, timezone, timedelta
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
PHONES_FILE = ROOT / "data" / "phones.json"
CONFIG_FILE = ROOT / "data" / "price-config.json"


def load_env_file() -> None:
    """Load simple KEY=value lines from a project-local .env without overriding real env vars.

    An explicitly empty env var (``HAINAN_API_KEY=""``) is treated as "not set" so that a
    host or launcher that predefines blank variables cannot silently shadow the .env file.
    """
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("\"'")
        if key and value and not os.environ.get(key, "").strip():
            os.environ[key] = value


# Load .env before reading any tunable below, so server-side settings actually apply.
load_env_file()

API_URL = os.getenv("HAINAN_API_URL", "https://gw-openapi.zhidemai.com/hj-search/discount/v2").strip() or "https://gw-openapi.zhidemai.com/hj-search/discount/v2"
TZ_CN = timezone(timedelta(hours=8))
CACHE_TTL_SECONDS = int(os.getenv("PHONE_QUOTE_CACHE_TTL_SECONDS", "1800"))
EMPTY_CACHE_TTL_SECONDS = int(os.getenv("PHONE_EMPTY_QUOTE_CACHE_TTL_SECONDS", "600"))
MAX_QUERIES_PER_RESPONSE = max(1, min(5, int(os.getenv("HAINAN_MAX_QUERIES_PER_RESPONSE", "5"))))
MIN_REQUEST_INTERVAL_SECONDS = max(0.0, float(os.getenv("HAINAN_MIN_REQUEST_INTERVAL_SECONDS", "0.6")))
REQUEST_FROM = os.getenv("HAINAN_REQUEST_FROM", "phone_compare_site")
QUERY_PROCESS = int(os.getenv("HAINAN_QUERY_PROCESS", "1"))
RESULT_SIZE = max(1, min(20, int(os.getenv("HAINAN_RESULT_SIZE", "20"))))
FIELDS = os.getenv("HAINAN_FIELDS", "")
HTTP_TIMEOUT_SECONDS = max(3.0, min(60.0, float(os.getenv("HAINAN_HTTP_TIMEOUT_SECONDS", "15"))))
CLIENT_RATE_LIMIT_PER_MINUTE = max(1, int(os.getenv("PHONE_API_RATE_LIMIT_PER_MINUTE", "40")))
PHONE_CORS_ORIGIN = os.getenv("PHONE_CORS_ORIGIN", "").strip()
PHONE_SERVE_STATIC = os.getenv("PHONE_SERVE_STATIC", "true").strip().lower() in {"1", "true", "yes", "on"}
_LAST_PROVIDER_REQUEST_AT = 0.0
_PROVIDER_REQUEST_LOCK = Lock()
_CLIENT_HITS: dict[str, list[float]] = {}
_CLIENT_HITS_LOCK = Lock()
_LAST_UPSTREAM: dict[str, Any] = {"at": None, "status": "not_called", "message": ""}

# phoneId -> (cache_epoch, result_or_none); None entries avoid repeated unproductive searches.
QUOTE_CACHE: dict[str, tuple[float, dict[str, Any] | None]] = {}

BRAND_PREFIX = {
    "Apple": "Apple",
    "Samsung": "三星",
    "Xiaomi": "小米",
    "Huawei": "华为",
    "Honor": "荣耀",
    "OnePlus": "一加",
    "OPPO": "OPPO",
    "vivo": "vivo",
    "realme": "真我",
}
EXCLUDE_TERMS_DEFAULT = [
    "二手", "翻新", "官翻", "官换", "展示机", "拆封", "资源机", "仅主机", "保护壳", "手机壳",
    "贴膜", "模型", "美版", "港版", "海外版", "日版", "韩版", "以旧换新价", "换新价", "补贴价", "回收价", "回收", "维修",
    "配件", "碎屏", "屏幕总成", "拆机", "空盒", "模型机", "后封", "无锁版", "卡贴机", "激活机",
]


def now_iso() -> str:
    return datetime.now(TZ_CN).isoformat(timespec="seconds")


def read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def phones_by_id() -> dict[str, dict[str, Any]]:
    records = read_json(PHONES_FILE, [])
    return {str(p.get("id")): p for p in records if isinstance(p, dict) and p.get("id")}


def provider_config() -> dict[str, Any]:
    config = read_json(CONFIG_FILE, {})
    return config if isinstance(config, dict) else {}


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKC", str(text or "")).lower()
    # Preserve the semantic meaning of '+' in names such as vivo X90 Pro+ and in RAM/ROM pairs.
    value = value.replace("+", "plus")
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value)


def first_storage_target(phone: dict[str, Any]) -> str | None:
    """Only quote the SKU the catalogue explicitly designates as quotable.

    An explicit ``quoteTargetStorage: null`` means the SKU mapping is still under review;
    falling back to storageOptions[0] would present an unverified capacity as exact.
    """
    if "quoteTargetStorage" in phone:
        target = phone.get("quoteTargetStorage")
        return target.strip() if isinstance(target, str) and target.strip() else None
    options = phone.get("storageOptions") or []
    if options and isinstance(options[0], str) and options[0].strip():
        return options[0].strip()
    return None


def storage_parts(target: str) -> tuple[int | None, int | None]:
    # RAM + ROM, e.g. 12GB+256GB. For iPhone-like models only ROM is present.
    m = re.search(r"(?i)(\d+)\s*gb\s*\+\s*(\d+)\s*gb", target)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(?i)(\d+)\s*gb", target)
    return None, int(m.group(1)) if m else None


def create_query(phone: dict[str, Any]) -> str | None:
    target = first_storage_target(phone)
    if not target:
        return None
    brand = str(phone.get("brand") or "")
    name = str(phone.get("name") or "").strip()
    prefix = BRAND_PREFIX.get(brand, brand)
    prefixes = {
        "Xiaomi": ["小米", "Xiaomi"],
        "Huawei": ["HUAWEI", "Huawei", "华为"],
        "Honor": ["荣耀", "HONOR", "Honor"],
        "OnePlus": ["一加", "OnePlus"],
        "OPPO": ["OPPO", "欧珀"],
        "vivo": ["vivo"],
        "realme": ["realme", "真我"],
        "Samsung": ["三星", "Samsung"],
    }.get(brand, [])
    clean_name = name
    for token in prefixes:
        if clean_name.casefold().startswith(token.casefold()):
            clean_name = clean_name[len(token):].strip()
            break
    # Keep the query short, but include the exact RAM/ROM chosen as quoteTargetStorage.
    # Prefixing with the mainland brand name helps find Chinese listings while the model stays distinct.
    return f"{prefix} {clean_name} {target}".strip()


def model_aliases(phone: dict[str, Any]) -> list[str]:
    name = str(phone.get("name") or "")
    brand = str(phone.get("brand") or "")
    aliases: list[str] = [name]
    if brand == "Apple":
        aliases += [name.replace("iPhone", "Apple iPhone"), "苹果" + name.replace("iPhone", "iPhone")]
    elif brand == "Samsung":
        aliases += ["三星" + name, "Samsung" + name.replace("Galaxy", "Galaxy")]
        aliases.append(name.replace("Galaxy", ""))
    elif brand == "Xiaomi":
        aliases += ["小米" + name.replace("小米", ""), name.replace("小米", "Xiaomi")]
    elif brand == "Huawei":
        aliases += [name.replace("HUAWEI", "华为"), name.replace("HUAWEI", "")]
    elif brand == "Honor":
        aliases += ["荣耀" + name.replace("荣耀", ""), name.replace("荣耀", "HONOR")]
    elif brand == "OnePlus":
        aliases += ["一加" + name.replace("一加", ""), name.replace("一加", "OnePlus")]
    elif brand == "OPPO":
        aliases += [name.replace("OPPO", "欧珀"), name.replace("OPPO", "")]
    elif brand == "vivo":
        aliases += ["vivo" + name.replace("vivo", ""), name.replace("vivo", "")]
    elif brand == "realme":
        aliases += ["真我" + name.replace("真我", ""), name.replace("真我", "")]
    normalized = []
    for alias in aliases:
        v = normalize(alias)
        if len(v) >= 4 and v not in normalized:
            normalized.append(v)
    # If name includes Chinese brand prefixes the normalized full-name matches may be too long;
    # add a model-name-only alias after known brand tokens are removed.
    for prefix in ["HUAWEI", "小米", "华为", "荣耀", "三星", "Samsung", "OPPO", "vivo", "realme", "真我", "一加", "Apple"]:
        short = normalize(name.replace(prefix, ""))
        if len(short) >= 4 and short not in normalized:
            normalized.append(short)
    return normalized


CN_VARIANT_MARKERS = ("至尊版", "至臻版", "非凡大师", "典藏版", "卫星通信版", "创作者套装", "折叠版")


def alias_matches_title(alias: str, norm_title: str, model_key: str) -> bool:
    """Match an alias without letting a base model absorb a longer variant.

    A plain substring test makes "Galaxy S25" match "Galaxy S25 Ultra" (or "一加 13"
    match "一加 13T"), which would attach another model's price to this phoneId.
    Any ASCII variant suffix immediately after the alias must also belong to this model.
    """
    start = 0
    while True:
        idx = norm_title.find(alias, start)
        if idx < 0:
            return False
        end = idx + len(alias)
        tail_end = end
        while tail_end < len(norm_title) and norm_title[tail_end].isascii() and norm_title[tail_end].isalpha():
            tail_end += 1
        tail = norm_title[end:tail_end]
        if not tail or tail in model_key:
            cn_tail = norm_title[end:end + 6]
            if not any(marker in cn_tail and marker not in model_key for marker in CN_VARIANT_MARKERS):
                return True
        start = idx + 1


def _sku_tokens(text: str) -> list[str]:
    value = unicodedata.normalize("NFKC", str(text or "")).lower().replace("+", " plus ")
    value = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", value)
    return [token for token in value.split() if token]


def offer_matches_sku(title: str, target: str) -> bool:
    """Require the exact RAM/ROM pair as standalone tokens.

    Token matching avoids two classic false results: model digits glued to storage
    ("一加 13" + "12GB" -> "1312gb") and bare concatenations such as "12256".
    """
    ram, rom = storage_parts(target)
    if rom is None:
        return False
    tokens = _sku_tokens(title)
    rom_tokens = {f"{rom}gb", f"{rom}g", str(rom)}
    has_rom = any(token in rom_tokens for token in tokens)
    if ram is None:
        return has_rom
    ram_tokens = {f"{ram}gb", f"{ram}g", str(ram)}
    if has_rom and any(token in ram_tokens for token in tokens):
        return True
    # Fallback for titles where the pair is written as one token, e.g. 12GB+256GB.
    joined = "".join(tokens)
    patterns = (
        rf"(?<!\d){ram}gb(?:plus|/|x){rom}(?:gb|g)?(?!\d)",
        rf"(?<!\d){ram}g(?:plus|/|x){rom}(?:gb|g)?(?!\d)",
        rf"(?<!\d){ram}(?:plus|/|x){rom}(?:gb|g)?(?!\d)",
        rf"(?<!\d){ram}gb{rom}(?:gb|g)(?!\d)",
    )
    return any(re.search(pattern, joined) for pattern in patterns)


def parse_price(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"\d[\d,]*(?:\.\d+)?", str(value).replace("，", ","))
    if not match:
        return None
    try:
        price = float(match.group(0).replace(",", ""))
    except ValueError:
        return None
    return price if 100 <= price <= 100000 else None


def safe_offer_url(url: Any) -> bool:
    if not isinstance(url, str):
        return False
    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.netloc)


def reject_offer(title: str, exclude_terms: list[str]) -> bool:
    t = normalize(title)
    return any(normalize(term) in t for term in exclude_terms if term)


class ProviderError(RuntimeError):
    """Upstream failure with a machine-readable kind for per-model status reporting."""

    def __init__(self, message: str, kind: str = "upstream", status: int | None = None) -> None:
        super().__init__(message)
        self.kind = kind
        self.status = status


def _record_upstream(status: str, message: str) -> None:
    global _LAST_UPSTREAM
    _LAST_UPSTREAM = {"at": now_iso(), "status": status, "message": str(message)[:160]}


def _call_provider(query: str, api_key: str) -> list[dict[str, Any]]:
    """Call Hainan discount-search Pro v2; credentials stay server-side."""
    global _LAST_PROVIDER_REQUEST_AT
    # Reserve request start times under a lock so concurrent web requests cannot
    # accidentally exceed the upstream API's configured minimum interval.
    with _PROVIDER_REQUEST_LOCK:
        wait = MIN_REQUEST_INTERVAL_SECONDS - (time.monotonic() - _LAST_PROVIDER_REQUEST_AT)
        if wait > 0:
            time.sleep(wait)
        _LAST_PROVIDER_REQUEST_AT = time.monotonic()
    body = {"request_from": REQUEST_FROM, "question_id": "phonecompare-" + str(uuid.uuid4()), "product_query": query, "query_process": QUERY_PROCESS, "size": RESULT_SIZE, "fields": FIELDS}
    request = Request(API_URL, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers={"Accept":"application/json","Content-Type":"application/json","x-api-key":api_key,"User-Agent":"PhoneCompareMainland/1.0"}, method="POST")
    try:
        with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            status_code, raw = response.status, response.read(4_000_000)
    except HTTPError as exc:
        hints = {401:"API Key 无效或已轮换",403:"Key 可能没有好价检索 Pro 权限",422:"请求字段不符合上游接口要求",429:"已达到调用频率或配额限制",502:"上游服务暂时不可用",504:"上游处理超时"}
        kind = {401:"auth",403:"auth",422:"bad_request",429:"quota"}.get(exc.code, "upstream")
        message = "海纳 API HTTP " + str(exc.code) + ("：" + hints[exc.code] if exc.code in hints else "")
        _record_upstream("error", message)
        raise ProviderError(message, kind=kind, status=exc.code) from exc
    except URLError as exc:
        if isinstance(getattr(exc, "reason", None), TimeoutError):
            message = f"海纳好价检索 API 请求超时（{HTTP_TIMEOUT_SECONDS:g} 秒）"
            kind = "timeout"
        else:
            message, kind = "无法连接海纳好价检索 API", "network"
        _record_upstream("error", message)
        raise ProviderError(message, kind=kind) from exc
    except TimeoutError as exc:
        message = f"海纳好价检索 API 请求超时（{HTTP_TIMEOUT_SECONDS:g} 秒）"
        _record_upstream("error", message)
        raise ProviderError(message, kind="timeout") from exc
    if status_code < 200 or status_code >= 300:
        message = "海纳 API 返回 HTTP " + str(status_code)
        _record_upstream("error", message)
        raise ProviderError(message, kind="upstream", status=status_code)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        message = "海纳 API 返回的不是有效 JSON"
        _record_upstream("error", message)
        raise ProviderError(message, kind="format") from exc
    if not isinstance(payload, dict):
        _record_upstream("error", "海纳 API 返回格式异常")
        raise ProviderError("海纳 API 返回格式异常", kind="format")
    error_code = payload.get("error_code")
    if error_code not in (None, 0, "0", ""):
        msg = str(payload.get("error_msg") or payload.get("message") or "上游返回错误")[:160]
        message = "海纳 API 错误 " + str(error_code) + ": " + msg
        _record_upstream("error", message)
        raise ProviderError(message, kind="api_error")
    data = payload.get("data") or {}
    rows = data.get("rows", []) if isinstance(data, dict) else data if isinstance(data, list) else []
    if not isinstance(rows, list):
        _record_upstream("error", "海纳 API 的 data.rows 字段格式异常")
        raise ProviderError("海纳 API 的 data.rows 字段格式异常", kind="format")
    mapped = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        price_field = next((key for key in ("digital_price", "price", "page_price") if row.get(key) not in (None, "")), None)
        direct_url = row.get("direct_link") or row.get("haojia_dplink") or row.get("url")
        mapped.append({**row, "title":row.get("title") or row.get("goods_name") or "", "price":row.get(price_field) if price_field else None, "priceFieldUsed":price_field, "url":direct_url, "mall_name":row.get("mall_name") or row.get("mall") or "", "prom_info":[str(x) for x in (row.get("coupon"),row.get("activity")) if x not in (None,"")]})
    _record_upstream("ok", f"HTTP 200，返回 {len(mapped)} 条商品")
    return mapped


def match_offer(phone: dict[str, Any], offers: list[dict[str, Any]], exclude_terms: list[str], checked_at: str) -> dict[str, Any] | None:
    target = first_storage_target(phone)
    if not target:
        return None
    aliases = model_aliases(phone)
    model_key = normalize(phone.get("name") or "")
    matched: list[dict[str, Any]] = []
    for offer in offers:
        title = str(offer.get("title") or "").strip()
        norm_title = normalize(title)
        if not title or reject_offer(title, exclude_terms):
            continue
        if not any(alias and alias_matches_title(alias, norm_title, model_key) for alias in aliases):
            continue
        if not offer_matches_sku(title, target):
            continue
        price = parse_price(offer.get("price") if offer.get("price") is not None else offer.get("price_1"))
        url = offer.get("url")
        mall = str(offer.get("mall_name") or "未知商城").strip()
        if price is None or not safe_offer_url(url):
            continue
        # Gentle preference for official/self-operated mall names, then sort by price.
        mall_norm = normalize(mall)
        preferred = any(term in mall_norm for term in ["官方旗舰店", "自营", "荣耀商城", "小米商城", "华为商城", "三星商城", "oppo商城", "苹果官网"])
        promo = offer.get("prom_info") or []
        if isinstance(promo, str):
            promo_text = promo.strip()
        elif isinstance(promo, list):
            promo_text = "；".join(str(x).strip() for x in promo if str(x).strip())
        else:
            promo_text = ""
        base_note = f"海纳好价检索 Pro 搜索结果；匹配大陆机型与 {target}。此为检索报价，不是订单结算承诺；请点开商品页核对新旧、颜色、库存、地区和优惠资格。"
        if promo_text:
            base_note += f" API 促销提示：{promo_text}。"
        matched.append({
            "phoneId": phone["id"],
            "sku": target,
            "channel": mall,
            "price": price,
            "checkedAt": checked_at,
            "url": url,
            "offerTitle": title,
            "promoInfo": promo_text,
            "note": base_note,
            "_preferred": preferred,
            "_sales": int(offer.get("sales_cnt") or 0) if str(offer.get("sales_cnt") or "0").isdigit() else 0,
        })
    if not matched:
        return None
    # Prefer the official/self-operated listings where possible; otherwise the lowest exact-SKU result.
    if any(x["_preferred"] for x in matched):
        matched = [x for x in matched if x["_preferred"]]
    matched.sort(key=lambda x: (x["price"], -x["_sales"]))
    result = matched[0]
    result.pop("_preferred", None)
    result.pop("_sales", None)
    return result


def query_prices(ids: list[str]) -> dict[str, Any]:
    api_key = os.getenv("HAINAN_API_KEY", "").strip()
    as_of = now_iso()
    if not api_key or api_key.casefold().startswith(("replace_", "your_", "填入")):
        return {"asOf":as_of,"provider":"hainan_discount_v2","status":"needs_credentials","message":"未检测到有效的 HAINAN_API_KEY。请将轮换后的 Key 仅配置在服务端 .env；未授权时不会伪造实时价格。","items":[],"statuses":{},"counts":{"requested":0,"matched":0,"noOffer":0,"failed":0,"skipped":0}}
    phone_map = phones_by_id()
    unique_ids = list(dict.fromkeys(str(i).strip() for i in ids if str(i).strip()))
    valid_ids = [id_ for id_ in unique_ids if id_ in phone_map]
    statuses: dict[str, dict[str, Any]] = {}
    for id_ in unique_ids:
        if id_ not in phone_map:
            statuses[id_] = {"status": "unknown_phone", "message": "后端机型库没有该 ID，未发起查询"}
    if not valid_ids:
        return {"asOf":as_of,"provider":"hainan_discount_v2","status":"no_exact_offers","message":"没有可查询的有效机型 ID。","items":[],"statuses":statuses,"counts":{"requested":0,"matched":0,"noOffer":0,"failed":0,"skipped":len(statuses)}}
    requested_ids = valid_ids[:MAX_QUERIES_PER_RESPONSE]
    omitted_ids = valid_ids[MAX_QUERIES_PER_RESPONSE:]
    for id_ in omitted_ids:
        statuses[id_] = {"status": "not_requested", "message": "超出单次批量上限，请继续下一批请求"}
    output: list[dict[str, Any]] = []
    errors: list[str] = []
    config = provider_config()
    exclude_terms = list(dict.fromkeys((config.get("excludeKeywords") or []) + EXCLUDE_TERMS_DEFAULT))
    consecutive_errors = 0
    for idx, id_ in enumerate(requested_ids):
        phone = phone_map[id_]
        query = create_query(phone)
        target = first_storage_target(phone)
        if not query or not target:
            statuses[id_] = {"status": "skipped", "sku": target, "message": "该机型尚未确定可报价的大陆版容量，未发起查询"}
            continue
        cached = QUOTE_CACHE.get(id_)
        if cached:
            cached_at, cached_item = cached
            ttl = CACHE_TTL_SECONDS if cached_item else EMPTY_CACHE_TTL_SECONDS
            if time.time() - cached_at < ttl:
                if cached_item:
                    item = dict(cached_item)
                    item["cached"] = True
                    output.append(item)
                    statuses[id_] = {"status": "ok", "cached": True, "checkedAt": item.get("checkedAt"), "sku": item.get("sku")}
                else:
                    statuses[id_] = {"status": "no_exact_offers", "cached": True, "sku": target, "message": "缓存结果：未找到同时匹配型号与容量的商品"}
                continue
        try:
            offers = _call_provider(query, api_key)
            item = match_offer(phone, offers, exclude_terms, now_iso())
            if item:
                item["provider"] = "hainan_discount_v2"
                item["priceFieldUsed"] = next((row.get("priceFieldUsed") for row in offers if str(row.get("title") or "") == item.get("offerTitle")), None)
            QUOTE_CACHE[id_] = (time.time(), item)
            if item:
                output.append(item)
                statuses[id_] = {"status": "ok", "cached": False, "checkedAt": item.get("checkedAt"), "sku": item.get("sku")}
            else:
                statuses[id_] = {"status": "no_exact_offers", "cached": False, "sku": target, "message": "已查询，但未找到同时匹配型号与目标容量的商品"}
            consecutive_errors = 0
        except ProviderError as exc:
            QUOTE_CACHE.pop(id_, None)
            errors.append(str(phone.get("name")) + ": " + str(exc))
            statuses[id_] = {"status": "error", "errorKind": exc.kind, "message": str(exc), "sku": target}
            # Auth/quota/parameter errors will repeat for every remaining model: stop burning quota.
            if exc.kind in ("auth", "quota", "bad_request"):
                fatal = True
            else:
                consecutive_errors += 1
                fatal = consecutive_errors >= 3
            if fatal:
                for rest in requested_ids[idx + 1:]:
                    statuses[rest] = {"status": "skipped", "message": "上游错误，本轮已停止查询"}
                break
    def count_status(name: str) -> int:
        return sum(1 for value in statuses.values() if value.get("status") == name)
    counts = {
        "requested": len(requested_ids),
        "matched": len(output),
        "noOffer": count_status("no_exact_offers"),
        "failed": count_status("error"),
        "skipped": count_status("skipped") + count_status("not_requested") + count_status("unknown_phone"),
    }
    if output and (counts["failed"] or counts["noOffer"] or counts["skipped"]):
        status, message = "partial", "已获取 " + str(len(output)) + "/" + str(len(requested_ids)) + " 款机型的精确型号与容量候选报价；其余机型暂无精确匹配、跳过或查询失败。"
    elif output:
        status, message = "ok", "已获得 " + str(len(output)) + "/" + str(len(requested_ids)) + " 款机型的精确型号与容量候选报价。"
    elif errors:
        status, message = "upstream_error", errors[0]
    elif counts["skipped"] and counts["skipped"] >= counts["requested"]:
        status, message = "no_exact_offers", "本轮机型都没有可报价的大陆版容量映射（或 ID 未知），未向上游发起查询。"
    else:
        status, message = "no_exact_offers", "接口已成功查询，但没有返回同时匹配型号、指定容量、合理价格与 HTTPS 链接的商品。"
    if omitted_ids:
        message += " 本次最多处理 " + str(len(requested_ids)) + " 款；另有 " + str(len(omitted_ids)) + " 款需要下一批请求。"
    return {"asOf":now_iso(),"provider":"hainan_discount_v2","status":status,"message":message,"requestedIds":requested_ids,"remainingIds":valid_ids[len(requested_ids):],"items":output,"statuses":statuses,"counts":counts}


def _client_rate_ok(client_ip: str) -> tuple[bool, int]:
    """Light per-IP limiter so the browser cannot flood the paid upstream by accident."""
    now = time.monotonic()
    with _CLIENT_HITS_LOCK:
        hits = [t for t in _CLIENT_HITS.get(client_ip, []) if now - t < 60]
        if len(hits) >= CLIENT_RATE_LIMIT_PER_MINUTE:
            retry_after = max(1, int(60 - (now - hits[0])) + 1)
            _CLIENT_HITS[client_ip] = hits
            return False, retry_after
        hits.append(now)
        _CLIENT_HITS[client_ip] = hits
        if len(_CLIENT_HITS) > 500:
            for key in [k for k, v in _CLIENT_HITS.items() if not v or now - v[-1] > 600]:
                _CLIENT_HITS.pop(key, None)
        return True, 0


class PhoneCompareHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args: Any) -> None:
        # Log paths/status only; never print query signatures or credential-bearing URLs.
        print(f"[{self.log_date_time_string()}] {self.client_address[0]} {fmt % args}")

    def send_json(self, status: int, payload: dict[str, Any], extra_headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        origin = self.headers.get("Origin", "")
        if PHONE_CORS_ORIGIN and origin == PHONE_CORS_ORIGIN:
            self.send_header("Access-Control-Allow-Origin", PHONE_CORS_ORIGIN)
            self.send_header("Vary", "Origin")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        origin = self.headers.get("Origin", "")
        self.send_response(204)
        if PHONE_CORS_ORIGIN and origin == PHONE_CORS_ORIGIN:
            self.send_header("Access-Control-Allow-Origin", PHONE_CORS_ORIGIN)
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Vary", "Origin")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        # Never serve project secrets, dotfiles, or the backend source over the static file handler.
        decoded_path = __import__("urllib.parse", fromlist=["unquote"]).unquote(parsed.path)
        parts = [part for part in Path(decoded_path).parts if part not in ("/", "", ".")]
        if any(part.startswith(".") for part in parts) or decoded_path.rstrip("/").endswith("price_server.py"):
            self.send_json(404, {"status": "not_found", "message": "此资源不通过静态站点公开。"})
            return
        if parsed.path == "/api/health":
            self.send_json(200, {
                "status": "ok",
                "provider": "hainan_discount_v2",
                "credentialsConfigured": bool(os.getenv("HAINAN_API_KEY", "").strip() and not os.getenv("HAINAN_API_KEY", "").strip().casefold().startswith(("replace_", "your_", "填入"))),
                "requestTimeoutSeconds": HTTP_TIMEOUT_SECONDS,
                "maxQueriesPerResponse": MAX_QUERIES_PER_RESPONSE,
                "minRequestIntervalSeconds": MIN_REQUEST_INTERVAL_SECONDS,
                "clientRateLimitPerMinute": CLIENT_RATE_LIMIT_PER_MINUTE,
                "lastUpstream": dict(_LAST_UPSTREAM),
                "message": "服务器已运行；该状态不代表报价 API 授权已通过。"
            })
            return
        if parsed.path == "/api/prices":
            allowed, retry_after = _client_rate_ok(self.client_address[0])
            if not allowed:
                self.send_json(429, {
                    "status": "rate_limited",
                    "provider": "hainan_discount_v2",
                    "message": "请求过于频繁，请 " + str(retry_after) + " 秒后再试。",
                    "retryAfterSeconds": retry_after,
                    "items": [],
                    "statuses": {},
                }, {"Retry-After": str(retry_after)})
                return
            qs = parse_qs(parsed.query)
            requested = qs.get("ids", [""])[0]
            ids = [part.strip() for part in requested.split(",") if part.strip()][:100]
            try:
                result = query_prices(ids)
            except Exception:
                self.send_json(500, {
                    "status": "internal_error",
                    "provider": "hainan_discount_v2",
                    "message": "后端处理报价请求时发生内部错误；未返回任何价格。",
                    "items": [],
                    "statuses": {},
                })
                return
            self.send_json(200, result)
            return
        if parsed.path.startswith("/api/"):
            self.send_json(404, {"status": "not_found", "message": "没有此 API 路由。"})
            return
        # The hosted Render service is API-only; local development can still serve the site.
        if not PHONE_SERVE_STATIC:
            self.send_json(404, {"status": "not_found", "message": "此后端仅提供 API；请访问 GitHub Pages 前端。"})
            return
        super().do_GET()


def main() -> None:
    load_env_file()
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), PhoneCompareHandler)
    print(f"机选网站已启动: http://{host}:{port}")
    if os.getenv("HAINAN_API_KEY", "").strip():
        print("报价源配置：已检测到服务端 HAINAN_API_KEY（仍需真实请求确认授权）。")
    else:
        print("报价源状态：待授权。复制 .env.example 为 .env 并填入轮换后的海纳 API Key。")
    print("按 Ctrl+C 结束服务。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
