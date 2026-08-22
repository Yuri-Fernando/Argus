"""DQ rule catalog for Silver `support_ticket`."""
from __future__ import annotations

from data_quality.validators.engine import Rule


def get_rules(crm_customer_ids: set) -> list[Rule]:
    return [
        Rule("schema_check", severity="hard", description="Expected Silver support_ticket columns present",
             params={"expected_columns": [
                 "ticket_id", "customer_id", "category", "priority", "sentiment",
                 "created_at", "resolved_at", "resolution_status",
             ]}),
        Rule("not_null", column="ticket_id", severity="hard", description="Primary key must be present"),
        Rule("unique", column="ticket_id", severity="hard", description="Primary key must be unique"),
        Rule("not_null", column="customer_id", severity="hard", description="Ticket must reference a customer"),
        Rule("referential_integrity", column="customer_id", severity="hard",
             description="customer_id must exist in crm_customer",
             params={"ref_values": crm_customer_ids, "ref_table": "crm_customer"}),
        Rule("range_check", column="priority", severity="soft", description="Priority must be a known value",
             params={"allowed_values": ["low", "medium", "high", "urgent"]}),
        Rule("range_check", column="resolution_status", severity="soft", description="Resolution status must be known",
             params={"allowed_values": ["open", "in_progress", "resolved", "closed", "escalated"]}),
        Rule("valid_date", column="created_at", severity="hard", description="created_at must be parseable"),
        Rule("duplicate_rate", severity="soft", description="Structural exact-duplicate rate on ticket_id",
             params={"subset": ["ticket_id"], "threshold": 0.0}),
        Rule("freshness", column="created_at", severity="soft", description="Most recent ticket should be reasonably recent",
             params={"max_age_days": 400}),
    ]
