#!/usr/bin/env python3
"""Local web server + server-side Zhidemai/SMZDM offer search adapter.

Only set SMZDM_APP_KEY and SMZDM_APP_SECRET on the server. Never send them to the browser.
The provider returns search offers, not a guaranteed checkout price; all matched offers include
an exact model/storage check, direct offer URL and query timestamp.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import unicodedata
from datetime import datetime, timezone, timedelta
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
PHONES_FILE = ROOT / "data" / "phones.json"
CONFIG_FILE = ROOT / "data" / "price-config.json"
API_URL = "https://openapi.smzdm.com/v1/agent/search/list"
TZ_CN = timezone(timedelta(hours=8))
CACHE_TTL_SECONDS = int(os.getenv("PHONE_QUOTE_CACHE_TTL_SECONDS", "1800"))
EMPTY_CACHE_TTL_SECONDS = int(os.getenv("PHONE_EMPTY_QUOTE_CACHE_TTL_SECONDS", "600"))
BATCH_SIZE = 8
HTTP_TIMEOUT_SECONDS = 12

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


def load_env_file() -> None:
    """Load simple KEY=value lines from a project-local .env without overriding real env vars."""
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("\"'")
        if key and value and key not in os.environ:
            os.environ[key] = value


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


def sign_params(params: dict[str, str], secret: str) -> str:
    """SMZDM Open Platform: UPPER(MD5(secret + sorted key/value concatenation + secret))."""
    parts = []
    for key in sorted(params.keys()):
        if key == "sign":
            continue
        value = params[key]
        if value is None or value == "":
            continue
        parts.append(f"{key}{value}")
    raw = secret + "".join(parts) + secret
    return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKC", str(text or "")).lower()
    # Preserve the semantic meaning of '+' in names such as vivo X90 Pro+ and in RAM/ROM pairs.
    value = value.replace("+", "plus")
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value)


def first_storage_target(phone: dict[str, Any]) -> str | None:
    target = phone.get("quoteTargetStorage")
    if isinstance(target, str) and target.strip():
        return target.strip()
    options = phone.get("storageOptions") or []
    if options and isinstance(options[0], str):
        return options[0]
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


def offer_matches_sku(title: str, target: str) -> bool:
    text = normalize(title)
    ram, rom = storage_parts(target)
    if rom is None:
        return False
    # For iPhone storage strings such as 256GB, accept 256GB/256G but not 1256GB/2560GB.
    if ram is None:
        return bool(re.search(rf"(?<!\d){rom}(?:gb|g)(?!\d)", text))
    # Preferred explicit pairs: 12GB+256GB, 12G+256G, 12+256GB.
    pair_pattern = rf"(?<!\d){ram}(?:gb|g)?(?:\+|plus|/|x|×)?{rom}(?:gb|g)?(?!\d)"
    if re.search(pair_pattern, text):
        return True
    # Some marketplace titles split the two values: e.g. 12GB 内存 256GB 存储.
    ram_found = re.search(rf"(?<!\d){ram}(?:gb|g)(?!\d)", text)
    rom_found = re.search(rf"(?<!\d){rom}(?:gb|g)(?!\d)", text)
    return bool(ram_found and rom_found)


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


def _call_provider(queries: list[str], app_key: str, app_secret: str) -> list[list[dict[str, Any]]]:
    params = {
        "app_key": app_key,
        "timestamp": str(int(time.time())),
        "keyword": ",".join(queries),
    }
    params["sign"] = sign_params(params, app_secret)
    url = API_URL + "?" + urlencode(params)
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "PhoneCompareMainland/1.0"})
    try:
        with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            body = response.read(4_000_000)
    except HTTPError as exc:
        raise RuntimeError(f"报价上游 HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("无法连接报价上游服务") from exc
    except TimeoutError as exc:
        raise RuntimeError("报价上游请求超时") from exc
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("报价上游返回的不是有效 JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("报价上游返回格式异常")
    error_code = payload.get("error_code", 0)
    if error_code not in (0, "0", None, ""):
        msg = str(payload.get("error_msg") or "上游返回错误")[:160]
        raise RuntimeError(f"报价 API 错误 {error_code}: {msg}")
    data = payload.get("data") or []
    # Official docs describe data as Search[] for each input keyword; with multi-keyword search,
    # the response is normally a list of result lists. Accommodate a flat list too.
    if not isinstance(data, list):
        raise RuntimeError("报价上游 data 字段格式异常")
    if not data:
        return [[] for _ in queries]
    if all(isinstance(x, list) for x in data):
        groups = [[y for y in x if isinstance(y, dict)] for x in data]
        if len(groups) < len(queries):
            groups.extend([[] for _ in range(len(queries) - len(groups))])
        return groups[:len(queries)]
    flat = [x for x in data if isinstance(x, dict)]
    if len(queries) == 1:
        return [flat]
    groups: list[list[dict[str, Any]]] = [[] for _ in queries]
    query_to_idx = {q.casefold(): i for i, q in enumerate(queries)}
    for item in flat:
        key = str(item.get("keyword") or "").casefold()
        idx = query_to_idx.get(key)
        if idx is not None:
            groups[idx].append(item)
    return groups


def match_offer(phone: dict[str, Any], offers: list[dict[str, Any]], exclude_terms: list[str], checked_at: str) -> dict[str, Any] | None:
    target = first_storage_target(phone)
    if not target:
        return None
    aliases = model_aliases(phone)
    matched: list[dict[str, Any]] = []
    for offer in offers:
        title = str(offer.get("title") or "").strip()
        norm_title = normalize(title)
        if not title or reject_offer(title, exclude_terms):
            continue
        if not any(alias and alias in norm_title for alias in aliases):
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
        base_note = f"值得买开放平台商品检索结果；匹配大陆机型与 {target}。此为检索报价，不是订单结算承诺；请点开商品页核对新旧、颜色、库存、地区和优惠资格。"
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
    config = provider_config()
    app_key = os.getenv("SMZDM_APP_KEY", "").strip()
    app_secret = os.getenv("SMZDM_APP_SECRET", "").strip()
    as_of = now_iso()
    key_is_placeholder = app_key.casefold().startswith(("replace_", "your_", "填入"))
    secret_is_placeholder = app_secret.casefold().startswith(("replace_", "your_", "填入"))
    if not app_key or not app_secret or key_is_placeholder or secret_is_placeholder:
        return {
            "asOf": as_of,
            "provider": "smzdm_openapi",
            "status": "needs_credentials",
            "message": "报价源已接入，但尚未授权：请从什么值得买开放平台申请 AppKey/AppSecret，并放入服务器 .env。当前不展示伪造实时价。",
            "items": [],
        }
    phone_map = phones_by_id()
    ids = list(dict.fromkeys(id_ for id_ in ids if id_ in phone_map))
    if not ids:
        return {"asOf": as_of, "provider": "smzdm_openapi", "status": "no_exact_offers", "message": "没有可查询的有效机型 ID。", "items": []}
    output: list[dict[str, Any]] = []
    todo: list[str] = []
    now = time.time()
    for id_ in ids:
        cached = QUOTE_CACHE.get(id_)
        if cached:
            cached_at, item = cached
            ttl = CACHE_TTL_SECONDS if item else EMPTY_CACHE_TTL_SECONDS
            if now - cached_at < ttl:
                if item:
                    output.append(item)
                continue
        todo.append(id_)
    for start in range(0, len(todo), BATCH_SIZE):
        batch_ids = todo[start:start + BATCH_SIZE]
        phones = [phone_map[id_] for id_ in batch_ids]
        valid_pairs = [(p, create_query(p)) for p in phones]
        valid_pairs = [(p, q) for p, q in valid_pairs if q]
        if not valid_pairs:
            for p in phones:
                QUOTE_CACHE[p["id"]] = (time.time(), None)
            continue
        queries = [q for _, q in valid_pairs]
        checked_at = now_iso()
        try:
            result_groups = _call_provider(queries, app_key, app_secret)
        except RuntimeError as exc:
            # Do not memoize provider failures as "no exact offer"; a temporary upstream issue
            # should be retried on the next request rather than hidden by the negative cache.
            for phone, _ in valid_pairs:
                QUOTE_CACHE.pop(phone["id"], None)
            return {
                "asOf": now_iso(),
                "provider": "smzdm_openapi",
                "status": "upstream_error",
                "message": f"报价源请求失败：{str(exc)}。请检查授权状态、API 配额和网络后重试。",
                "items": output,
            }
        exclude_terms = list(dict.fromkeys((config.get("excludeKeywords") or []) + EXCLUDE_TERMS_DEFAULT))
        for index, (phone, _query) in enumerate(valid_pairs):
            offers = result_groups[index] if index < len(result_groups) else []
            item = match_offer(phone, offers, exclude_terms, checked_at)
            QUOTE_CACHE[phone["id"]] = (time.time(), item)
            if item:
                output.append(item)
        # Light pacing between multi-batch cold starts to avoid hammering an API.
        if start + BATCH_SIZE < len(todo):
            time.sleep(0.15)
    # Preserve the IDs' order and keep one exact SKU price per model.
    order = {id_: i for i, id_ in enumerate(ids)}
    output.sort(key=lambda x: order.get(x.get("phoneId", ""), 10_000))
    fresh_items = [x for x in output if x.get("phoneId") in ids]
    missing_count = max(0, len(ids) - len(fresh_items))
    status = "ok" if fresh_items else "no_exact_offers"
    if fresh_items and missing_count:
        message = f"已匹配 {len(fresh_items)} 款机型的精确容量报价；{missing_count} 款暂无同时匹配型号与容量的新机商品结果。"
    elif fresh_items:
        message = f"已匹配全部 {len(fresh_items)} 款机型的精确容量报价。"
    else:
        message = "接口已查询，但暂时没有商品标题同时匹配型号与指定存储版本的有效报价；可稍后重试或手动打开电商平台核对。"
    return {"asOf": now_iso(), "provider": "smzdm_openapi", "status": status, "message": message, "items": fresh_items}


class PhoneCompareHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args: Any) -> None:
        # Log paths/status only; never print query signatures or credential-bearing URLs.
        print(f"[{self.log_date_time_string()}] {self.client_address[0]} {fmt % args}")

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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
                "provider": "smzdm_openapi",
                "credentialsConfigured": bool(
                    os.getenv("SMZDM_APP_KEY", "").strip()
                    and os.getenv("SMZDM_APP_SECRET", "").strip()
                    and not os.getenv("SMZDM_APP_KEY", "").strip().casefold().startswith(("replace_", "your_", "填入"))
                    and not os.getenv("SMZDM_APP_SECRET", "").strip().casefold().startswith(("replace_", "your_", "填入"))
                ),
                "message": "服务器已运行；该状态不代表报价 API 授权已通过。"
            })
            return
        if parsed.path == "/api/prices":
            qs = parse_qs(parsed.query)
            requested = qs.get("ids", [""])[0]
            ids = [part.strip() for part in requested.split(",") if part.strip()]
            result = query_prices(ids)
            self.send_json(200, result)
            return
        if parsed.path.startswith("/api/"):
            self.send_json(404, {"status": "not_found", "message": "没有此 API 路由。"})
            return
        # Serve static website assets from the project folder.
        super().do_GET()


def main() -> None:
    load_env_file()
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), PhoneCompareHandler)
    print(f"机选网站已启动: http://{host}:{port}")
    if os.getenv("SMZDM_APP_KEY", "").strip() and os.getenv("SMZDM_APP_SECRET", "").strip():
        print("报价源配置：已检测到服务端凭据（实际 API 授权还需有效且未过期）。")
    else:
        print("报价源状态：待授权。复制 .env.example 为 .env 并填入开放平台提供的凭据。")
    print("按 Ctrl+C 结束服务。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
