-- fact_payments — mirrors snowflake/ddl/05_fact_payments.sql. Local stand-in for
-- Revenue/AOV facts (no data/raw/olist fact_orders in this snapshot) — Revenue/AOV
-- are computed against SETTLED payments (net_amount / gross_amount), see
-- docs/semantic-dictionary.md and marts/_metrics.yml below.

select
    payment_id,
    master_customer_id,
    date_key,
    gross_amount,
    fee_amount,
    net_amount,
    method,
    status,
    settled_at
from {{ ref('int_payments_resolved') }}
