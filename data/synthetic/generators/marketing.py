"""Generates data/synthetic/marketing/campaigns.csv and campaign_interactions.csv."""
from __future__ import annotations

import random

import pandas as pd
from faker import Faker


def generate(
    customer_ids: list[str],
    n_interactions: int,
    seed: int,
    n_campaigns: int,
    channels: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fake = Faker("pt_BR")
    Faker.seed(seed)
    rng = random.Random(seed)

    campaigns = []
    for i in range(n_campaigns):
        start = fake.date_between(start_date="-2y", end_date="-1M")
        campaigns.append(
            {
                "campaign_id": f"CMP{i:04d}",
                "name": f"{rng.choice(['Summer', 'Winter', 'Black Friday', 'Loyalty', 'Reactivation', 'Welcome'])} {start.year}",
                "channel": rng.choice(channels),
                "start_date": start.isoformat(),
                "end_date": (start + pd.Timedelta(days=rng.randint(7, 45))).isoformat(),
                "budget": round(rng.uniform(2000, 80000), 2),
            }
        )
    campaigns_df = pd.DataFrame(campaigns)

    interactions = []
    for i in range(n_interactions):
        campaign = campaigns[rng.randrange(n_campaigns)]
        clicked = rng.random() < 0.35
        converted = clicked and rng.random() < 0.12
        interactions.append(
            {
                "interaction_id": f"INT{i:09d}",
                "customer_id": rng.choice(customer_ids),
                "campaign_id": campaign["campaign_id"],
                "channel": campaign["channel"],
                "impressions": rng.randint(1, 10),
                "clicks": 1 if clicked else 0,
                "conversion": 1 if converted else 0,
                "cost": round(rng.uniform(0.05, 3.5), 2),
                "timestamp": fake.date_time_between(start_date="-1y", end_date="now").isoformat(),
            }
        )
    interactions_df = pd.DataFrame(interactions)
    return campaigns_df, interactions_df
