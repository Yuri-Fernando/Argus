"""DQ rule catalog for Silver `crm_customer`.

Note on severities: `email` missing (~2%) and `phone` invalid format (~1%)
are *deliberately* injected by the synthetic generator (see
data/synthetic/config.yaml `dirty_rates`) specifically so this pipeline has
something real to catch. `valid_phone` is a HARD rule (quarantines the
offending rows, proving the DQ->quarantine wiring works end to end);
`not_null(email)` is a SOFT rule (scored, not quarantined) since a missing
email is a legitimate, recoverable data gap rather than a corrupt record.
"""
from __future__ import annotations

from data_quality.validators.engine import Rule


def get_rules() -> list[Rule]:
    return [
        Rule("schema_check", severity="hard", description="Expected Silver crm_customer columns present",
             params={"expected_columns": [
                 "crm_customer_id", "name", "email", "phone", "document_hash",
                 "birth_date", "address", "city", "state", "created_at", "updated_at",
             ]}),
        Rule("not_null", column="crm_customer_id", severity="hard", description="Primary key must be present"),
        Rule("unique", column="crm_customer_id", severity="hard", description="Primary key must be unique"),
        Rule("not_null", column="email", severity="soft", description="Email should be present (2% deliberately missing)"),
        Rule("valid_email", column="email", severity="hard", description="Non-null emails must be well-formed"),
        Rule("valid_phone", column="phone", severity="hard", description="Non-null phones must have 10-13 digits (1% deliberately invalid)"),
        Rule("valid_date", column="birth_date", severity="soft", description="Birth date must be parseable",
             params={"max_date": "2026-08-13"}),
        Rule("range_check", column="state", severity="soft", description="State must be a valid Brazilian UF",
             params={"allowed_values": sorted([
                 "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
                 "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
                 "SP", "SE", "TO",
             ])}),
        Rule("duplicate_rate", severity="soft", description="Structural exact-duplicate rate on the natural key",
             params={"subset": ["crm_customer_id"], "threshold": 0.0}),
        Rule("freshness", column="updated_at", severity="soft", description="Most recent update should be reasonably recent",
             params={"max_age_days": 400}),
    ]
