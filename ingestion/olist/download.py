"""
Downloads the Olist Brazilian E-Commerce Public Dataset from Kaggle into
data/raw/olist/, using kagglehub (no manual API-token file required — it
will prompt for browser-based Kaggle auth on first run).

Dataset: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
License: CC BY-NC-SA 4.0

Usage:
    python ingestion/olist/download.py
    python ingestion/olist/download.py --dest data/raw/olist --force

If you prefer the Kaggle CLI instead, see DATA_MODEL.md §1.1 (Option A).
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

DATASET_SLUG = "olistbr/brazilian-ecommerce"
EXPECTED_FILES = [
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "product_category_name_translation.csv",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest",
        default="data/raw/olist",
        help="Destination directory for the raw CSV files (default: data/raw/olist)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download and overwrite even if files already exist locally",
    )
    return parser.parse_args()


def already_downloaded(dest: Path) -> bool:
    return dest.exists() and all((dest / f).exists() for f in EXPECTED_FILES)


def download(dest: Path) -> None:
    try:
        import kagglehub
    except ImportError:
        print(
            "kagglehub is not installed. Run: pip install kagglehub\n"
            "Alternatively, use the Kaggle CLI or manual download — see "
            "DATA_MODEL.md §1.1 for both options.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    print(f"Downloading '{DATASET_SLUG}' via kagglehub "
          f"(a browser login prompt may appear on first run)...")
    cache_path = Path(kagglehub.dataset_download(DATASET_SLUG))
    print(f"Downloaded to kagglehub cache: {cache_path}")

    dest.mkdir(parents=True, exist_ok=True)
    copied = 0
    for csv_file in cache_path.glob("*.csv"):
        shutil.copy2(csv_file, dest / csv_file.name)
        copied += 1
    print(f"Copied {copied} CSV file(s) to {dest}")


def verify(dest: Path) -> None:
    missing = [f for f in EXPECTED_FILES if not (dest / f).exists()]
    if missing:
        print(
            "WARNING: the following expected Olist files are missing after "
            f"download: {missing}\nThe dataset structure may have changed "
            "upstream — check https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
            file=sys.stderr,
        )
    else:
        print(f"All {len(EXPECTED_FILES)} expected Olist files are present in {dest}.")


def main() -> None:
    args = parse_args()
    dest = Path(args.dest)

    if already_downloaded(dest) and not args.force:
        print(f"Olist dataset already present in {dest} (use --force to re-download).")
        return

    download(dest)
    verify(dest)


if __name__ == "__main__":
    main()
