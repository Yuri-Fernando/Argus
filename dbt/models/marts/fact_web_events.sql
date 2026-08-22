-- fact_web_events — mirrors snowflake/ddl/08_fact_web_events.sql.

select
    session_id,
    event_id,
    master_customer_id,
    date_key,
    event_type,
    product_id,
    device,
    browser,
    source,
    campaign,
    event_timestamp
from {{ ref('int_web_events_resolved') }}
