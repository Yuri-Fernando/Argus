"""Bronze ingestion for the Olist e-commerce source — CONDITIONAL.

`data/raw/olist/*.csv` requires an interactive Kaggle login to download (see
DATA_MODEL.md §1.1) and is confirmed absent in this environment. This module
degrades gracefully: if the raw files are not present, it logs a clear
warning and returns an empty result instead of raising, so
`lakehouse/run_pipeline.py` never crashes because of a missing optional
source.
"""
from __future__ import annotations

import pandas as pd

from lakehouse.bronze.common import RAW_OLIST, add_ingestion_columns, logger, source_missing_warning, write_parquet

# Olist ships 9 relational CSVs — see DATA_MODEL.md §1.1 for the full list.
OLIST_FILES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}


def is_available() -> bool:
    return RAW_OLIST.exists() and any(RAW_OLIST.glob("*.csv"))


def ingest() -> dict[str, pd.DataFrame]:
    if not is_available():
        source_missing_warning("olist", RAW_OLIST)
        return {}

    results: dict[str, pd.DataFrame] = {}
    for table_name, filename in OLIST_FILES.items():
        path = RAW_OLIST / filename
        if not path.exists():
            logger.warning("Bronze[olist]: %s missing, skipping table %s", path, table_name)
            continue
        df = pd.read_csv(path)
        df = add_ingestion_columns(df, source_name="olist")
        write_parquet(df, table_name=table_name, source_dir="olist")
        results[table_name] = df
    return results


if __name__ == "__main__":
    ingest()
