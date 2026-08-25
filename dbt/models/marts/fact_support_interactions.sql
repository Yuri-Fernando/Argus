-- fact_support_interactions — mirrors snowflake/ddl/06_fact_support_interactions.sql.

select
    ticket_id,
    master_customer_id,
    date_key_created,
    date_key_resolved,
    category,
    priority,
    sentiment,
    resolution_status,
    resolution_days,
    created_at,
    resolved_at
from {{ ref('int_support_tickets_resolved') }}
