-- int_campaign_interactions_resolved — stg_campaign_interaction resolved to
-- master_customer_id, with date_key derived for the dim_date FK.
-- Mirrors snowflake/local_runner.py fact_campaign_interactions build block.

with interactions as (

    select * from {{ ref('stg_campaign_interaction') }}

),

bridge as (

    select * from {{ ref('int_customer_bridge') }}

)

select
    i.interaction_id,
    b.master_customer_id,
    i.campaign_id,
    cast(to_char(i.event_timestamp, 'YYYYMMDD') as integer) as date_key,
    i.channel,
    i.impressions,
    i.clicks,
    i.conversion,
    i.cost,
    i.event_timestamp
from interactions i
left join bridge b on b.crm_customer_id = i.crm_customer_id
