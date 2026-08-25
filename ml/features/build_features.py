"""Feature Store build entrypoint — joins RFM, engagement, and support features into one table.

Run directly to (re)build the feature store:

    python -m ml.features.build_features

Writes `data/ml/features/customer_features.parquet`, one row per `master_customer_id`, consumed
by `ml/churn/train.py` and `ml/segmentation/kmeans_segments.py`.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from ml.features.engagement import WEB_EVENT_PATH, build_engagement_features
from ml.features.entity_map import GOLDEN_RECORD_PATH, load_customer_id_map
from ml.features.rfm import PAYMENT_FINANCE_PATH, build_rfm_features
from ml.features.support import SUPPORT_TICKET_PATH, build_support_features

logger = logging.getLogger("ml.features.build_features")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

OUTPUT_PATH = Path("data/ml/features/customer_features.parquet")


def _resolve_reference_date() -> pd.Timestamp:
    """The "as of" timestamp every recency feature is measured against.

    Derived as one day past the latest activity timestamp observed across payments, web events,
    and support tickets — not `pd.Timestamp.now()` — so that RFM/engagement outputs (and every
    downstream churn label built from them) stay reproducible regardless of which real-world day
    this pipeline is executed on.
    """
    max_payment = pd.read_parquet(PAYMENT_FINANCE_PATH, columns=["settled_at"])["settled_at"].max()
    max_event = pd.read_parquet(WEB_EVENT_PATH, columns=["timestamp"])["timestamp"].max()
    max_ticket = pd.read_parquet(SUPPORT_TICKET_PATH, columns=["created_at"])["created_at"].max()
    return max(max_payment, max_event, max_ticket) + pd.Timedelta(days=1)


def build_customer_features(
    golden_record_path: Path = GOLDEN_RECORD_PATH,
    output_path: Path = OUTPUT_PATH,
) -> pd.DataFrame:
    """Build and persist the full customer feature table.

    Args:
        golden_record_path: MDM golden record, source of the `master_customer_id` grain.
        output_path: where to write the resulting Parquet feature store.

    Returns:
        The assembled feature DataFrame (also written to `output_path`).
    """
    id_map = load_customer_id_map(golden_record_path)
    reference_date = _resolve_reference_date()
    logger.info("Reference date for recency features: %s", reference_date.date())

    rfm = build_rfm_features(id_map, reference_date)
    engagement = build_engagement_features(id_map, reference_date)
    support = build_support_features(id_map)

    features = rfm.merge(engagement, on="master_customer_id", how="inner").merge(
        support, on="master_customer_id", how="inner"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(output_path, index=False)
    logger.info("Wrote %d customer feature rows to %s", len(features), output_path)
    return features


if __name__ == "__main__":
    result = build_customer_features()
    print(result.describe(include="all").transpose())
