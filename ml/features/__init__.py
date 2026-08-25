"""Feature engineering — RFM, engagement, and support signals at the golden-record level.

Every feature builder in this package joins Silver-layer tables (`data/lakehouse/silver/`) to
`data/mdm/golden_record.parquet` first, so a customer who exists as two duplicate CRM rows (an
MDM-resolved pair) contributes one feature row, not two — the same customer-identity discipline
the rest of this platform applies (see `mdm/README.md`). Falling back to raw `crm_customer_id`
grain would silently double-count RFM and engagement history for every merged duplicate.
"""
