"""Support-signal features from `support_ticket.parquet`."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ml.features.entity_map import map_to_master_id

SUPPORT_TICKET_PATH = Path("data/lakehouse/silver/support_ticket.parquet")

# `sentiment` is a categorical label in the Silver table, not a numeric score. Mapped to a
# signed scale so it can be averaged into a single `avg_sentiment_score` feature: negative
# experiences pull the average down, positive ones pull it up, neutral tickets are inert.
SENTIMENT_SCORE_MAP = {"negative": -1.0, "neutral": 0.0, "positive": 1.0}

# A ticket still `open` or `escalated` is an active, unresolved support signal; `resolved`
# tickets are closed and no longer indicate friction.
UNRESOLVED_STATUSES = {"open", "escalated"}


def build_support_features(
    id_map: pd.DataFrame,
    support_ticket_path: Path = SUPPORT_TICKET_PATH,
) -> pd.DataFrame:
    """Compute ticket volume, sentiment, and unresolved-ticket count per `master_customer_id`.

    Args:
        id_map: `crm_customer_id -> master_customer_id` lookup.
        support_ticket_path: path to the Silver support ticket table.

    Returns:
        DataFrame with columns `["ticket_count", "avg_sentiment_score", "unresolved_count"]`.
        Customers with no support tickets on record get `ticket_count=0`,
        `avg_sentiment_score=0.0` (neutral — no signal either way, not assumed negative), and
        `unresolved_count=0`.
    """
    tickets = pd.read_parquet(support_ticket_path)
    tickets = map_to_master_id(tickets, "customer_id", id_map)
    tickets["sentiment_score"] = tickets["sentiment"].map(SENTIMENT_SCORE_MAP)
    tickets["is_unresolved"] = tickets["resolution_status"].isin(UNRESOLVED_STATUSES)

    grouped = tickets.groupby("master_customer_id").agg(
        ticket_count=("ticket_id", "count"),
        avg_sentiment_score=("sentiment_score", "mean"),
        unresolved_count=("is_unresolved", "sum"),
    )

    all_customers = id_map["master_customer_id"].drop_duplicates()
    result = grouped.reindex(all_customers).fillna(
        {"ticket_count": 0, "avg_sentiment_score": 0.0, "unresolved_count": 0}
    )
    result["ticket_count"] = result["ticket_count"].astype(int)
    result["unresolved_count"] = result["unresolved_count"].astype(int)
    result.index.name = "master_customer_id"
    return result.reset_index()
