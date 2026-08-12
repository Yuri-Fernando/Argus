"""
Generates data/synthetic/crm/crm_customers.csv.

Deliberately injects the data problems the MDM / Entity Resolution pipeline
(see mdm/entity_resolution/) and the Data Quality framework (data_quality/)
are built to detect and fix:

- `duplicate_customers` fraction of rows are near-duplicates of an existing
  customer (name variant, same email/phone) -> ground truth for the
  Entity Resolution benchmark (mdm/entity_resolution/evaluation/).
- `missing_email` fraction have a null email.
- `invalid_phone` fraction have a malformed phone number.
- `inconsistent_address` fraction have a city/state pair that doesn't match
  (e.g. city="São Paulo", state="RJ").

Every injected duplicate is also recorded in a companion
`crm_customers_ground_truth.csv` (`customer_id, duplicate_of_customer_id`),
so the MDM matcher's precision/recall can be measured against a known
answer instead of eyeballed.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

import pandas as pd
from faker import Faker

# A handful of real Brazilian state/city pairs, used both for valid
# generation and to build deliberately inconsistent pairs.
STATE_CITIES = {
    "SP": ["São Paulo", "Campinas", "Santos"],
    "RJ": ["Rio de Janeiro", "Niterói", "Petrópolis"],
    "MG": ["Belo Horizonte", "Uberlândia", "Juiz de Fora"],
    "RS": ["Porto Alegre", "Caxias do Sul", "Pelotas"],
    "BA": ["Salvador", "Feira de Santana", "Ilhéus"],
    "PR": ["Curitiba", "Londrina", "Maringá"],
}


@dataclass
class DirtyRates:
    duplicate_customers: float = 0.05
    missing_email: float = 0.02
    invalid_phone: float = 0.01
    inconsistent_address: float = 0.01


def _fake_document_hash(fake: Faker) -> str:
    """Never store a real-looking CPF — hash a synthetic one immediately."""
    raw = fake.cpf() if hasattr(fake, "cpf") else fake.ssn()
    return hashlib.sha256(raw.encode()).hexdigest()


def _name_variant(name: str, rng: random.Random) -> str:
    """Produces a plausible 'same person, different spelling' variant,
    the exact ambiguity Entity Resolution has to resolve deterministically
    vs. probabilistically vs. via ML (see ARCHITECTURE.md §8)."""
    variant_type = rng.choice(["drop_accent", "abbreviate_middle", "case_swap"])
    parts = name.split()
    if variant_type == "abbreviate_middle" and len(parts) > 2:
        parts = [parts[0]] + [p[0] + "." for p in parts[1:-1]] + [parts[-1]]
        return " ".join(parts)
    if variant_type == "case_swap":
        return name.title() if not name.istitle() else name.upper()
    # drop_accent (cheap approximation, good enough for a fuzzy-match demo)
    table = str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc")
    return name.translate(table)


def generate(n: int, seed: int, dirty_rates: DirtyRates) -> tuple[pd.DataFrame, pd.DataFrame]:
    fake = Faker("pt_BR")
    Faker.seed(seed)
    rng = random.Random(seed)

    rows = []
    for i in range(n):
        state = rng.choice(list(STATE_CITIES.keys()))
        city = rng.choice(STATE_CITIES[state])
        name = fake.name()
        email = fake.email()
        phone = fake.phone_number()

        if rng.random() < dirty_rates.missing_email:
            email = None
        if rng.random() < dirty_rates.invalid_phone:
            phone = "".join(c for c in phone if c.isdigit())[:4]  # truncated/malformed
        if rng.random() < dirty_rates.inconsistent_address:
            # pick a city from a DIFFERENT state on purpose
            other_state = rng.choice([s for s in STATE_CITIES if s != state])
            city = rng.choice(STATE_CITIES[other_state])

        rows.append(
            {
                "crm_customer_id": f"CRM{i:08d}",
                "name": name,
                "email": email,
                "phone": phone,
                "document_hash": _fake_document_hash(fake),
                "birth_date": fake.date_of_birth(minimum_age=18, maximum_age=85).isoformat(),
                "address": fake.street_address(),
                "city": city,
                "state": state,
                "created_at": fake.date_time_between(start_date="-3y", end_date="-1y").isoformat(),
                "updated_at": fake.date_time_between(start_date="-1y", end_date="now").isoformat(),
            }
        )

    df = pd.DataFrame(rows)

    # Inject near-duplicates of a random sample of existing customers.
    n_dupes = int(n * dirty_rates.duplicate_customers)
    dupe_source_idx = rng.sample(range(len(df)), k=min(n_dupes, len(df)))
    ground_truth = []
    dupes = []
    next_id = n
    for src_idx in dupe_source_idx:
        src = df.iloc[src_idx]
        dupe = src.copy()
        dupe["crm_customer_id"] = f"CRM{next_id:08d}"
        dupe["name"] = _name_variant(src["name"], rng)
        dupe["updated_at"] = fake.date_time_between(start_date="-6M", end_date="now").isoformat()
        dupes.append(dupe)
        ground_truth.append(
            {
                "customer_id": dupe["crm_customer_id"],
                "duplicate_of_customer_id": src["crm_customer_id"],
            }
        )
        next_id += 1

    df = pd.concat([df, pd.DataFrame(dupes)], ignore_index=True)
    ground_truth_df = pd.DataFrame(ground_truth)
    return df, ground_truth_df
