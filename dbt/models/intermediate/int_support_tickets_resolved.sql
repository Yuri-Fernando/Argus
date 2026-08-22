-- int_support_tickets_resolved — stg_support_ticket resolved to master_customer_id,
-- with date_key_created / date_key_resolved derived for the dim_date FKs.
-- Mirrors snowflake/local_runner.py fact_support_interactions build block.

with tickets as (

    select * from {{ ref('stg_support_ticket') }}

),

bridge as (

    select * from {{ ref('int_customer_bridge') }}

)

select
    t.ticket_id,
    b.master_customer_id,
    cast(to_char(t.created_at, 'YYYYMMDD') as integer) as date_key_created,
    cast(to_char(t.resolved_at, 'YYYYMMDD') as integer) as date_key_resolved,
    t.category,
    t.priority,
    t.sentiment,
    t.resolution_status,
    t.resolution_days,
    t.created_at,
    t.resolved_at
from tickets t
left join bridge b on b.crm_customer_id = t.crm_customer_id
