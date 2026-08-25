-- Singular test: settled payments must never carry a negative net_amount or
-- gross_amount — the Revenue/AOV metrics (marts/_metrics.yml) SUM these directly,
-- and a negative settled amount would either be a data quality bug upstream
-- (data_quality/ module) or an unhandled refund/chargeback that should carry a
-- different status, not 'settled'.
-- dbt convention: a test FAILS if this query returns any rows.

select
    payment_id,
    status,
    gross_amount,
    net_amount
from {{ ref('fact_payments') }}
where status = 'settled'
  and (net_amount < 0 or gross_amount < 0)
