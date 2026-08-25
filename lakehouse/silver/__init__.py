"""Silver layer — dedup, casting, standardization, schema enforcement.

`build_all(bronze_tables)` returns *candidate* Silver DataFrames keyed by
final table name. Final Parquet writing happens in
`lakehouse/run_pipeline.py` only after the Data Quality engine has split
each candidate table into passing rows (-> `data/lakehouse/silver/`) and
hard-rule failures (-> `data/lakehouse/quarantine/`).

Olist-derived Silver tables (`silver.customer`, `silver.order`, etc. per
DATA_MODEL.md §2) are intentionally NOT built here since `data/raw/olist` is
absent in this environment — see `lakehouse/bronze/olist.py`.
"""
from __future__ import annotations

import pandas as pd

from lakehouse.silver import campaign_interaction, crm_customer, payment_finance, support_ticket, web_event
from lakehouse.silver.common import logger

# Maps final Silver table name -> (bronze table name, build function)
TABLE_BUILDERS = {
    "crm_customer": ("crm_customers", crm_customer.build),
    "support_ticket": ("support_tickets", support_ticket.build),
    "web_event": ("web_events", web_event.build),
    "campaign_interaction": ("campaign_interactions", campaign_interaction.build),
    "payment_finance": ("customer_payments", payment_finance.build),
}


def build_all(bronze_tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    candidates: dict[str, pd.DataFrame] = {}
    for silver_name, (bronze_name, builder) in TABLE_BUILDERS.items():
        if bronze_name not in bronze_tables:
            logger.warning("Silver: bronze table %s missing — skipping Silver table %s", bronze_name, silver_name)
            continue
        candidates[silver_name] = builder(bronze_tables[bronze_name])
        logger.info("Silver: built candidate %s (%d rows)", silver_name, len(candidates[silver_name]))
    return candidates
