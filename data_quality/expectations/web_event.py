"""DQ rule catalog for Silver `web_event`."""
from __future__ import annotations

from data_quality.validators.engine import Rule


def get_rules(crm_customer_ids: set) -> list[Rule]:
    return [
        Rule("schema_check", severity="hard", description="Expected Silver web_event columns present",
             params={"expected_columns": [
                 "session_id", "customer_id", "event_type", "product_id", "timestamp",
                 "device", "browser", "source", "campaign",
             ]}),
        Rule("not_null", column="session_id", severity="hard", description="Every event must have a session"),
        Rule("not_null", column="customer_id", severity="hard", description="Every event must reference a customer"),
        Rule("referential_integrity", column="customer_id", severity="hard",
             description="customer_id must exist in crm_customer",
             params={"ref_values": crm_customer_ids, "ref_table": "crm_customer"}),
        Rule("range_check", column="device", severity="soft", description="Device must be a known category",
             params={"allowed_values": ["desktop", "mobile", "tablet"]}),
        Rule("range_check", column="event_type", severity="soft", description="Event type must be a known category",
             params={"allowed_values": ["page_view", "product_view", "add_to_cart", "checkout_start", "purchase", "search"]}),
        Rule("valid_date", column="timestamp", severity="hard", description="timestamp must be parseable"),
        Rule("duplicate_rate", severity="soft", description="Structural exact-duplicate rate across all columns",
             params={"subset": None, "threshold": 0.001}),
        Rule("freshness", column="timestamp", severity="soft", description="Most recent event should be reasonably recent",
             params={"max_age_days": 400}),
    ]
