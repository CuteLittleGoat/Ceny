#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PRODUCTS = ROOT / "config/products.json"
CONFIG_STORES = ROOT / "config/stores.json"
DATA_PRICES = ROOT / "data/prices.csv"
DATA_PRICES_JSON = ROOT / "data/prices.json"
DATA_LATEST = ROOT / "data/latest.json"
DATA_ERRORS = ROOT / "data/errors.json"

FIELDS = [
    "timestamp", "date", "display_order", "model_id", "model_name", "store_id", "store_name",
    "price_current", "price_regular", "price_lowest_30_days", "currency", "availability", "color",
    "source_url", "seller", "is_marketplace", "status", "notes",
]

USER_AGENT = "Mozilla/5.0 (compatible; CenyBot/2.0; +https://github.com/cutelittlegoat/Ceny)"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_csv_header() -> None:
    if not DATA_PRICES.exists() or DATA_PRICES.stat().st_size == 0:
        DATA_PRICES.parent.mkdir(parents=True, exist_ok=True)
        with DATA_PRICES.open("w", encoding="utf-8", newline="") as handle:
            csv.DictWriter(handle, fieldnames=FIELDS).writeheader()


def append_rows(rows: list[dict]) -> None:
    if not rows:
        return
    ensure_csv_header()
    with DATA_PRICES.open("a", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=FIELDS).writerows(rows)


def parse_price(raw) -> float | None:
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if not text:
        return None
    text = text.replace("zł", "").replace("pln", "")
    text = re.sub(r"\s+", "", text)
    if "," in text and "." in text:
        text = text.replace(" ", "")
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", ".")
    text = re.sub(r"[^0-9.]", "", text)
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value if value > 0 else None


def is_plausible_phone_price(value: float | None) -> bool:
    return value is not None and 300 <= value <= 20000


def normalize_availability(raw: str | None) -> str:
    if not raw:
        return "unknown"
    value = str(raw).lower()
    if any(k in value for k in ["instock", "in_stock", "dostępny", "dostepny", "available"]):
        return "in_stock"
    if any(k in value for k in ["outofstock", "out_of_stock", "niedost", "brak w magazynie"]):
        return "out_of_stock"
    if any(k in value for k in ["preorder", "przedsprzeda"]):
        return "preorder"
    if any(k in value for k in ["withdrawn", "wycof", "discontinued"]):
        return "withdrawn"
    return "unknown"


def fetch_html(url: str) -> tuple[str | None, str, str | None]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8"})
    try:
        with urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8", "ignore"), "ok", None
    except HTTPError as exc:
        if exc.code == 403:
            return None, "http_403_blocked", f"HTTP 403: {exc.reason}"
        if exc.code == 404:
            return None, "http_404_not_found", f"HTTP 404: {exc.reason}"
        return None, "network_error", f"HTTP {exc.code}: {exc.reason}"
    except URLError as exc:
        return None, "network_error", f"URLError: {exc.reason}"
    except TimeoutError as exc:
        return None, "network_error", f"Timeout: {exc}"


def extract_product_jsonld(html: str) -> dict | None:
    blobs = re.findall(r"<script[^>]*type=\"application/ld\\+json\"[^>]*>(.*?)</script>", html, re.S | re.I)
    for blob in blobs:
        try:
            parsed = json.loads(blob.strip())
        except Exception:
            continue
        queue = parsed if isinstance(parsed, list) else [parsed]
        while queue:
            item = queue.pop(0)
            if isinstance(item, dict) and item.get("@type") == "Product":
                return item
            if isinstance(item, dict):
                queue.extend(v for v in item.values() if isinstance(v, (dict, list)))
            if isinstance(item, list):
                queue.extend(item)
    return None


def parse_from_jsonld(html: str) -> dict | None:
    product = extract_product_jsonld(html)
    if not product:
        return None
    offers = product.get("offers", {})
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = parse_price(offers.get("price"))
    availability = normalize_availability(offers.get("availability"))
    return {
        "price_current": price,
        "currency": offers.get("priceCurrency") or "PLN",
        "availability": availability,
        "seller": ((offers.get("seller") or {}).get("name") if isinstance(offers.get("seller"), dict) else None) or "",
    }


def parse_morele(html: str) -> dict:
    data = parse_from_jsonld(html) or {}
    if not data.get("price_current"):
        m = re.search(r'"price"\s*:\s*"?([0-9\s,.]+)"?', html)
        data["price_current"] = parse_price(m.group(1)) if m else None
    if not data.get("availability") or data["availability"] == "unknown":
        data["availability"] = "out_of_stock" if re.search(r"niedostępny|chwilowo niedost", html, re.I) else "in_stock"
    data["currency"] = data.get("currency") or "PLN"
    data["seller"] = data.get("seller") or "Morele"
    return data


def parse_rtv_euro_agd(html: str) -> dict:
    data = parse_from_jsonld(html) or {}
    if not data.get("price_current"):
        m = re.search(r'"price"\s*:\s*"?([0-9\s,.]+)"?', html)
        data["price_current"] = parse_price(m.group(1)) if m else None
    if not data.get("availability") or data["availability"] == "unknown":
        if re.search(r"niedostępny|brak\s+w\s+sklepie", html, re.I):
            data["availability"] = "out_of_stock"
        else:
            data["availability"] = "in_stock" if re.search(r"Dostępny|Kup teraz", html, re.I) else "unknown"
    data["currency"] = data.get("currency") or "PLN"
    data["seller"] = data.get("seller") or "RTV Euro AGD"
    return data


def parse_xkom(html: str) -> dict:
    data = parse_from_jsonld(html) or {}
    data["seller"] = data.get("seller") or "x-kom"
    data["currency"] = data.get("currency") or "PLN"
    return data


PARSERS = {
    "morele": parse_morele,
    "rtv-euro-agd": parse_rtv_euro_agd,
    "x-kom": parse_xkom,
}


def read_historical_rows() -> list[dict]:
    if not DATA_PRICES.exists():
        return []
    with DATA_PRICES.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def select_best(offers: list[dict]) -> dict | None:
    in_stock = [o for o in offers if o.get("availability") == "in_stock" and o.get("price_current") is not None]
    candidates = in_stock or [o for o in offers if o.get("price_current") is not None]
    return min(candidates, key=lambda o: o["price_current"]) if candidates else None


def main() -> None:
    now = datetime.now(timezone.utc)
    stamp = now.isoformat()
    date = now.date().isoformat()

    products = load_json(CONFIG_PRODUCTS)
    stores = {s["store_id"]: s for s in load_json(CONFIG_STORES)}
    old_rows = read_historical_rows()

    errors, rows, latest = [], [], []

    for product in sorted(products, key=lambda x: x["display_order"]):
        ok_offers = []
        checked = failed = 0

        for source in product.get("sources", []):
            checked += 1
            store_id = source.get("store_id")
            store = stores.get(store_id)
            parser = PARSERS.get(store_id)
            url = source.get("url")

            if not source.get("scrape_enabled", False):
                failed += 1
                errors.append({"timestamp": stamp, "model_id": product["model_id"], "model_name": product["model_name"], "store_id": store_id, "store_name": source.get("store_name"), "url": url, "error_type": "source_disabled", "error_message": "Source scrape disabled in products config", "status": "manual_review", "scrape_enabled": False})
                continue
            if not store:
                failed += 1
                errors.append({"timestamp": stamp, "model_id": product["model_id"], "model_name": product["model_name"], "store_id": store_id, "store_name": source.get("store_name"), "url": url, "error_type": "manual_review", "error_message": "Store not found in stores config", "status": "manual_review", "scrape_enabled": True})
                continue
            if not store.get("scrape_enabled", False):
                failed += 1
                errors.append({"timestamp": stamp, "model_id": product["model_id"], "model_name": product["model_name"], "store_id": store_id, "store_name": store.get("store_name"), "url": url, "error_type": "store_disabled", "error_message": "Store scrape disabled in stores config", "status": "store_disabled", "scrape_enabled": False})
                continue
            if not url:
                failed += 1
                errors.append({"timestamp": stamp, "model_id": product["model_id"], "model_name": product["model_name"], "store_id": store_id, "store_name": store.get("store_name"), "url": url, "error_type": "manual_review", "error_message": "Missing source URL", "status": "manual_review", "scrape_enabled": True})
                continue
            if not parser:
                failed += 1
                errors.append({"timestamp": stamp, "model_id": product["model_id"], "model_name": product["model_name"], "store_id": store_id, "store_name": store.get("store_name"), "url": url, "error_type": "parser_not_implemented", "error_message": f"No parser for store {store_id}", "status": "parser_not_implemented", "scrape_enabled": True})
                continue

            html, fetch_status, fetch_error = fetch_html(url)
            if html is None:
                failed += 1
                errors.append({"timestamp": stamp, "model_id": product["model_id"], "model_name": product["model_name"], "store_id": store_id, "store_name": store.get("store_name"), "url": url, "error_type": fetch_status, "error_message": fetch_error, "status": fetch_status, "scrape_enabled": True})
                continue

            try:
                parsed = parser(html)
            except Exception as exc:
                failed += 1
                errors.append({"timestamp": stamp, "model_id": product["model_id"], "model_name": product["model_name"], "store_id": store_id, "store_name": store.get("store_name"), "url": url, "error_type": "parse_error", "error_message": str(exc), "status": "parse_error", "scrape_enabled": True})
                continue

            price_current = parse_price(parsed.get("price_current"))
            availability = normalize_availability(parsed.get("availability"))
            if availability == "withdrawn":
                failed += 1
                errors.append({"timestamp": stamp, "model_id": product["model_id"], "model_name": product["model_name"], "store_id": store_id, "store_name": store.get("store_name"), "url": url, "error_type": "withdrawn", "error_message": "Product withdrawn", "status": "withdrawn", "scrape_enabled": True})
                continue
            if price_current is None or not is_plausible_phone_price(price_current):
                failed += 1
                err_type = "out_of_stock" if availability == "out_of_stock" else "price_missing"
                errors.append({"timestamp": stamp, "model_id": product["model_id"], "model_name": product["model_name"], "store_id": store_id, "store_name": store.get("store_name"), "url": url, "error_type": err_type, "error_message": "Price not found", "status": err_type, "scrape_enabled": True})
                continue

            row = {
                "timestamp": stamp, "date": date, "display_order": product["display_order"], "model_id": product["model_id"], "model_name": product["model_name"],
                "store_id": store_id, "store_name": store.get("store_name", source.get("store_name", store_id)),
                "price_current": price_current, "price_regular": parse_price(parsed.get("price_regular")),
                "price_lowest_30_days": parse_price(parsed.get("price_lowest_30_days")), "currency": parsed.get("currency") or "PLN",
                "availability": availability, "color": source.get("color"), "source_url": url, "seller": parsed.get("seller") or store.get("store_name", store_id),
                "is_marketplace": store.get("source_type") == "marketplace", "status": "ok", "notes": f"Parsed successfully using parser: {store_id}"
            }
            rows.append(row)
            ok_offers.append(row)

        best = select_best(ok_offers)
        history_model = [r for r in old_rows + rows if r.get("model_id") == product["model_id"] and r.get("price_current")]
        prices = [float(r["price_current"]) for r in history_model if parse_price(r["price_current"]) is not None]
        previous = None
        old_model = [r for r in old_rows if r.get("model_id") == product["model_id"] and parse_price(r.get("price_current")) is not None]
        if old_model:
            previous = parse_price(old_model[-1].get("price_current"))

        best_price = best["price_current"] if best else None
        price_change = (best_price - previous) if best_price is not None and previous is not None else None
        price_change_percent = (price_change / previous * 100) if price_change is not None and previous else None

        latest.append({
            "display_order": product["display_order"], "model_id": product["model_id"], "model_name": product["model_name"], "ram_gb": product.get("ram_gb"), "storage_gb": product.get("storage_gb"),
            "best_price": best_price, "best_store": best["store_name"] if best else None, "best_url": best["source_url"] if best else None, "best_color": best["color"] if best else None,
            "currency": best["currency"] if best else "PLN", "availability": best["availability"] if best else None,
            "last_success_at": stamp if best else None, "previous_price": previous, "price_change": price_change, "price_change_percent": price_change_percent,
            "historical_min_price": min(prices) if prices else None, "historical_max_price": max(prices) if prices else None,
            "sources_checked": checked, "sources_ok": len(ok_offers), "sources_failed": failed,
            "status": "ok" if best else "no_data",
        })

    append_rows(rows)
    all_history = old_rows + rows
    DATA_PRICES_JSON.write_text(json.dumps({"generated_at": stamp, "rows": all_history}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    DATA_LATEST.write_text(json.dumps({"generated_at": stamp, "items": latest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    DATA_ERRORS.write_text(json.dumps({"generated_at": stamp, "errors": errors}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
