-- dim_customer — mirrors snowflake/ddl/01_dim_customer.sql column-for-column.
-- One row per resolved master customer (post-MDM golden record).

select
    master_customer_id,
    canonical_name,
    canonical_email,
    canonical_phone,
    city,
    state,
    source_record_count,
    golden_record_created_at,
    golden_record_updated_at,
    recency_days,
    frequency,
    monetary,
    event_count,
    distinct_event_types,
    days_since_last_activity,
    ticket_count,
    avg_sentiment_score,
    unresolved_count,
    cluster,
    segment,
    is_repeat_customer,
    churn_score,
    lifetime_value
from {{ ref('int_customer_golden_record') }}
