"""Generates data/synthetic/support/support_tickets.csv.

Sentiment + resolution_status + created_at/resolved_at give the Data
Quality Agent and the churn feature-engineering step (ml/features/) real
signal to work with — e.g. `days_since_last_negative_ticket` as a churn
feature.
"""
from __future__ import annotations

import random

import pandas as pd
from faker import Faker


def generate(
    customer_ids: list[str],
    n: int,
    seed: int,
    categories: list[str],
    priorities: list[str],
    sentiments: list[str],
) -> pd.DataFrame:
    fake = Faker("pt_BR")
    Faker.seed(seed)
    rng = random.Random(seed)

    rows = []
    for i in range(n):
        created = fake.date_time_between(start_date="-1y", end_date="now")
        resolved = None
        status = "open"
        if rng.random() < 0.85:
            resolved = created + pd.Timedelta(hours=rng.randint(1, 240))
            status = rng.choice(["resolved", "resolved", "resolved", "escalated"])
        rows.append(
            {
                "ticket_id": f"TKT{i:08d}",
                "customer_id": rng.choice(customer_ids),
                "category": rng.choice(categories),
                "priority": rng.choice(priorities),
                "sentiment": rng.choices(sentiments, weights=[0.3, 0.4, 0.3])[0],
                "created_at": created.isoformat(),
                "resolved_at": resolved.isoformat() if resolved is not None else None,
                "resolution_status": status,
            }
        )
    return pd.DataFrame(rows)
