"""DQ rule catalog for Silver `payment_finance`."""
from __future__ import annotations

from data_quality.validators.engine import Rule


def get_rules(crm_customer_ids: set) -> list[Rule]:
    return [
        Rule("schema_check", severity="hard", description="Expected Silver payment_finance columns present",
             params={"expected_columns": [
                 "payment_id", "customer_id", "gross_amount", "fee_amount", "net_amount",
                 "method", "settled_at", "status",
             ]}),
        Rule("not_null", column="payment_id", severity="hard", description="Primary key must be present"),
        Rule("unique", column="payment_id", severity="hard", description="Primary key must be unique"),
        Rule("referential_integrity", column="customer_id", severity="hard",
             description="customer_id must exist in crm_customer",
             params={"ref_values": crm_customer_ids, "ref_table": "crm_customer"}),
        Rule("range_check", column="gross_amount", severity="hard", description="gross_amount must be non-negative", params={"min": 0}),
        Rule("range_check", column="net_amount", severity="hard", description="net_amount must be non-negative", params={"min": 0}),
        Rule("range_check", column="status", severity="soft", description="status must be a known category",
             params={"allowed_values": ["settled", "pending", "failed", "refunded", "chargeback"]}),
        Rule("valid_date", column="settled_at", severity="hard", description="settled_at must be parseable"),
        Rule("duplicate_rate", severity="soft", description="Structural exact-duplicate rate on payment_id",
             params={"subset": ["payment_id"], "threshold": 0.0}),
        Rule("freshness", column="settled_at", severity="soft", description="Most recent payment should be reasonably recent",
             params={"max_age_days": 400}),
    ]
