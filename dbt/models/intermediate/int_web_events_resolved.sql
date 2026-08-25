-- int_web_events_resolved — stg_web_event resolved to master_customer_id, with
-- date_key derived for the dim_date FK.
-- Mirrors snowflake/local_runner.py fact_web_events build block.

with events as (

    select * from {{ ref('stg_web_event') }}

),

bridge as (

    select * from {{ ref('int_customer_bridge') }}

)

select
    e.session_id,
    e.event_id,
    b.master_customer_id,
    cast(to_char(e.event_timestamp, 'YYYYMMDD') as integer) as date_key,
    e.event_type,
    e.product_id,
    e.device,
    e.browser,
    e.traffic_source as source,
    e.campaign,
    e.event_timestamp
from events e
left join bridge b on b.crm_customer_id = e.crm_customer_id
