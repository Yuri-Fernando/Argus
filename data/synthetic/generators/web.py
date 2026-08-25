"""Generates data/synthetic/web/web_events.csv.

Sized in the hundreds-of-thousands to millions of rows on purpose (see
DATA_MODEL.md §5 volume knobs) so lakehouse/silver PySpark code has a
real reason to run distributed instead of trivially fitting in pandas.
Written out in chunks to keep memory bounded regardless of `--profile`.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

from faker import Faker


FIELDS = [
    "session_id",
    "customer_id",
    "event_type",
    "product_id",
    "timestamp",
    "device",
    "browser",
    "source",
    "campaign",
]


def generate_to_csv(
    path: Path,
    customer_ids: list[str],
    n: int,
    seed: int,
    event_types: list[str],
    devices: list[str],
    sources: list[str],
    chunk_size: int = 50_000,
) -> None:
    fake = Faker()
    Faker.seed(seed)
    rng = random.Random(seed)
    browsers = ["Chrome", "Safari", "Firefox", "Edge"]

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()

        written = 0
        while written < n:
            batch = min(chunk_size, n - written)
            rows = []
            for _ in range(batch):
                rows.append(
                    {
                        "session_id": fake.uuid4(),
                        "customer_id": rng.choice(customer_ids),
                        "event_type": rng.choices(
                            event_types, weights=[0.45, 0.25, 0.12, 0.08, 0.05, 0.05]
                        )[0],
                        "product_id": f"PROD{rng.randint(0, 30000):06d}",
                        "timestamp": fake.date_time_between(
                            start_date="-6M", end_date="now"
                        ).isoformat(),
                        "device": rng.choices(devices, weights=[0.4, 0.5, 0.1])[0],
                        "browser": rng.choice(browsers),
                        "source": rng.choice(sources),
                        "campaign": f"CMP{rng.randint(0, 11):04d}" if rng.random() < 0.3 else "",
                    }
                )
            writer.writerows(rows)
            written += batch
