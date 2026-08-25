"""Bronze layer — near-verbatim raw-to-Parquet ingestion, one module per source.

See lakehouse/README.md for the Medallion architecture and the Bronze
"never destroys information" rule.
"""
from __future__ import annotations

import pandas as pd

from lakehouse.bronze import crm, finance, marketing, olist, support, web
from lakehouse.bronze.common import logger


def run_all() -> dict[str, pd.DataFrame]:
    """Run every available Bronze ingestion module. Returns {table_name: df}.

    Olist is skipped gracefully (with a warning) when data/raw/olist is absent.
    """
    tables: dict[str, pd.DataFrame] = {}

    tables["crm_customers"] = crm.ingest()
    tables.update(marketing.ingest())
    tables["support_tickets"] = support.ingest()
    tables["web_events"] = web.ingest()
    tables["customer_payments"] = finance.ingest()

    olist_tables = olist.ingest()
    if olist_tables:
        tables.update(olist_tables)
    else:
        logger.warning("Bronze: Olist source unavailable — Olist-derived Bronze/Silver/Gold tables skipped.")

    logger.info("Bronze: ingested %d tables: %s", len(tables), sorted(tables.keys()))
    return tables


if __name__ == "__main__":
    run_all()
