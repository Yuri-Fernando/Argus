"""Central registry of per-table DQ rule catalogs (`get_rules(...)` functions).

Human-readable rule catalog per Silver table — one module per table, mirroring
data_quality/README.md's `rules/` folder concept. `get_rules_for_table` wires
these to `lakehouse/run_pipeline.py`/`data_quality/validators/engine.py`.
"""
from __future__ import annotations

import pandas as pd

from data_quality.expectations import campaign_interaction, crm_customer, payment_finance, support_ticket, web_event
from data_quality.validators.engine import Rule

# Tables that need crm_customer_id as a referential-integrity reference set.
_NEEDS_CRM_IDS = {
    "support_ticket": support_ticket.get_rules,
    "web_event": web_event.get_rules,
    "campaign_interaction": campaign_interaction.get_rules,
    "payment_finance": payment_finance.get_rules,
}


def get_rules_for_table(table_name: str, silver_tables: dict[str, pd.DataFrame]) -> list[Rule]:
    if table_name == "crm_customer":
        return crm_customer.get_rules()
    if table_name in _NEEDS_CRM_IDS:
        crm_df = silver_tables.get("crm_customer")
        crm_ids: set = set(crm_df["crm_customer_id"].dropna()) if crm_df is not None else set()
        return _NEEDS_CRM_IDS[table_name](crm_ids)
    raise KeyError(f"No DQ rule catalog registered for table '{table_name}'")
