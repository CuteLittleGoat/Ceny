#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PRODUCTS = ROOT / "config" / "products.json"
CONFIG_STORES = ROOT / "config" / "stores.json"
DATA_PRICES = ROOT / "data" / "prices.csv"
DATA_LATEST = ROOT / "data" / "latest.json"
DATA_ERRORS = ROOT / "data" / "errors.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def append_price_rows(rows: list[dict]) -> None:
    if not rows:
        return
    with DATA_PRICES.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp","date","display_order","model_id","model_name","store_id","store_name",
                "price_current","price_regular","price_lowest_30_days","currency","availability",
                "color","source_url","seller","is_marketplace","status","notes",
            ],
        )
        writer.writerows(rows)


def main() -> None:
    products = load_json(CONFIG_PRODUCTS)
    stores = {s["store_id"]: s for s in load_json(CONFIG_STORES)}
    now = datetime.now(timezone.utc)

    rows = []
    errors = []
    latest_items = []

    for product in products:
        for source in product.get("sources", []):
            store = stores.get(source.get("store_id"))
            if not store:
                errors.append({
                    "timestamp": now.isoformat(),
                    "model_id": product["model_id"],
                    "store_id": source.get("store_id"),
                    "url": source.get("url"),
                    "error_type": "unknown_store",
                    "error_message": "Store not found in stores.json",
                })
                continue
            # MVP: parsery sklepów do zaimplementowania w kolejnych etapach
            # Tu zapisujemy tylko błąd informacyjny, że scraping nie został jeszcze wdrożony.
            errors.append({
                "timestamp": now.isoformat(),
                "model_id": product["model_id"],
                "store_id": store["store_id"],
                "url": source.get("url"),
                "error_type": "not_implemented",
                "error_message": "Scraper sklepu niezaimplementowany w MVP",
            })

        latest_items.append({
            "display_order": product["display_order"],
            "model_id": product["model_id"],
            "model_name": product["model_name"],
            "best_price": None,
            "best_store": None,
            "last_success_at": None,
        })

    append_price_rows(rows)

    DATA_LATEST.write_text(
        json.dumps({"generated_at": now.isoformat(), "items": latest_items}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    DATA_ERRORS.write_text(
        json.dumps({"generated_at": now.isoformat(), "errors": errors}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
