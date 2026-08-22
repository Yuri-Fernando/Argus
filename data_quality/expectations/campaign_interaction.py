"""DQ rule catalog for Silver `campaign_interaction`."""
from __future__ import annotations

from data_quality.validators.engine import Rule


def get_rules(crm_customer_ids: set) -> list[Rule]:
    return [
        Rule("schema_check", severity="hard", description="Expected Silver campaign_interaction columns present",
             params={"expected_columns": [
                 "interaction_id", "customer_id", "campaign_id", "channel",
                 "impressions", "clicks", "conversion", "cost", "timestamp",
             ]}),
        Rule("not_null", column="interaction_id", severity="hard", description="Primary key must be present"),
        Rule("unique", column="interaction_id", severity="hard", description="Primary key must be unique"),
        Rule("referential_integrity", column="customer_id", severity="hard",
             description="customer_id must exist in crm_customer",
             params={"ref_values": crm_customer_ids, "ref_table": "crm_customer"}),
        Rule("range_check", column="cost", severity="hard", description="cost must be non-negative", params={"min": 0}),
        Rule("range_check", column="impressions", severity="soft", description="impressions must be non-negative", params={"min": 0}),
        Rule("valid_date", column="timestamp", severity="hard", description="timestamp must be parseable"),
        Rule("duplicate_rate", severity="soft", description="Structural exact-duplicate rate on interaction_id",
             params={"subset": ["interaction_id"], "threshold": 0.0}),
        Rule("freshness", column="timestamp", severity="soft", description="Most recent interaction should be reasonably recent",
             params={"max_age_days": 400}),
    ]
