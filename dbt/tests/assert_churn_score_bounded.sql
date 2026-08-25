-- Singular test: churn_score must always be in [0, 1] — a value outside that range
-- means the recency-based proxy formula (int_customer_golden_record.sql /
-- snowflake/local_runner.py) broke, since churn_score directly weights lifetime_value.
-- dbt convention: a test FAILS if this query returns any rows.

select
    master_customer_id,
    churn_score
from {{ ref('dim_customer') }}
where churn_score is not null
  and (churn_score < 0 or churn_score > 1)
