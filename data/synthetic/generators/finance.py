"""Generates data/synthetic/finance/customer_payments.csv — a reconciliation
feed independent of Olist's own payments table, used in ROADMAP Sprint 6
to demonstrate cross-source reconciliation (Olist payment total vs. finance
system settlement total) as an extra Data Quality check."""
from __future__ import annotations

import random

import pandas as pd
from faker import Faker


def generate(customer_ids: list[str], n: int, seed: int) -> pd.DataFrame:
    fake = Faker("pt_BR")
    Faker.seed(seed)
    rng = random.Random(seed)

    rows = []
    for i in range(n):
        gross = round(rng.uniform(30, 3500), 2)
        fee = round(gross * rng.uniform(0.02, 0.06), 2)
        rows.append(
            {
                "payment_id": f"PAY{i:08d}",
                "customer_id": rng.choice(customer_ids),
                "gross_amount": gross,
                "fee_amount": fee,
                "net_amount": round(gross - fee, 2),
                "method": rng.choice(["credit_card", "boleto", "pix", "voucher"]),
                "settled_at": fake.date_time_between(start_date="-1y", end_date="now").isoformat(),
                "status": rng.choices(
                    ["settled", "pending", "chargeback"], weights=[0.93, 0.05, 0.02]
                )[0],
            }
        )
    return pd.DataFrame(rows)
