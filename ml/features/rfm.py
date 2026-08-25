"""RFM (Recency, Frequency, Monetary) features from `payment_finance.parquet`.

Only `status == "settled"` payments count towards Frequency/Monetary — `pending` transactions
have not yet cleared and `chargeback` transactions were reversed, so counting either would
overstate a customer's real purchasing behavior.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ml.features.entity_map import map_to_master_id

PAYMENT_FINANCE_PATH = Path("data/lakehouse/silver/payment_finance.parquet")
SETTLED_STATUS = "settled"


def build_rfm_features(
    id_map: pd.DataFrame,
    reference_date: pd.Timestamp,
    payment_finance_path: Path = PAYMENT_FINANCE_PATH,
) -> pd.DataFrame:
    """Compute Recency/Frequency/Monetary per `master_customer_id`.

    Args:
        id_map: `crm_customer_id -> master_customer_id` lookup, see `ml/features/entity_map.py`.
        reference_date: the "as of" timestamp Recency is measured against — kept as an explicit
            argument (rather than `pd.Timestamp.now()`) so results are reproducible across runs;
            `ml/features/build_features.py` derives it once from the max observed activity
            timestamp across all Silver tables and shares it with every feature builder.
        payment_finance_path: path to the Silver payment table.

    Returns:
        DataFrame indexed by `master_customer_id` with columns
        `["recency_days", "frequency", "monetary"]`. Customers with zero settled payments
        (never purchased, or every payment is pending/chargeback) get `frequency=0`,
        `monetary=0.0`, and `recency_days` equal to the widest observed recency + 1 — the
        conventional RFM convention for "no purchase on record", worse than every customer who
        has purchased at least once.
    """
    payments = pd.read_parquet(payment_finance_path)
    payments = payments[payments["status"] == SETTLED_STATUS]
    payments = map_to_master_id(payments, "customer_id", id_map)

    grouped = payments.groupby("master_customer_id").agg(
        recency_days=("settled_at", lambda s: (reference_date - s.max()).days),
        frequency=("payment_id", "count"),
        monetary=("net_amount", "sum"),
    )

    # Fill customers absent from the settled-payments group (no qualifying purchase history)
    # with the worst-case recency observed among purchasers + 1, and zero frequency/monetary.
    all_customers = id_map["master_customer_id"].drop_duplicates()
    worst_recency = int(grouped["recency_days"].max()) + 1 if not grouped.empty else 1
    result = grouped.reindex(all_customers).fillna(
        {"recency_days": worst_recency, "frequency": 0, "monetary": 0.0}
    )
    result["frequency"] = result["frequency"].astype(int)
    result["recency_days"] = result["recency_days"].astype(int)
    result.index.name = "master_customer_id"
    return result.reset_index()
