-- dim_campaign — mirrors snowflake/ddl/04_dim_campaign.sql. One row per distinct
-- campaign_id, aggregated from stg_campaign_interaction.

with interactions as (

    select * from {{ ref('stg_campaign_interaction') }}

),

channel_mode as (

    -- most frequent channel value per campaign_id, mirrors local_runner.py's
    -- `s.mode().iat[0]` via a row-count-ranked window function.
    select
        campaign_id,
        channel,
        row_number() over (
            partition by campaign_id
            order by count(*) desc, channel asc
        ) as rn
    from interactions
    group by campaign_id, channel

),

primary_channel as (

    select campaign_id, channel as primary_channel
    from channel_mode
    where rn = 1

),

agg as (

    select
        campaign_id,
        min(event_timestamp)      as first_seen_at,
        max(event_timestamp)      as last_seen_at,
        sum(impressions)          as total_impressions,
        sum(clicks)               as total_clicks,
        sum(conversion)           as total_conversions,
        sum(cost)                 as total_cost
    from interactions
    group by campaign_id

)

select
    a.campaign_id,
    p.primary_channel,
    a.first_seen_at,
    a.last_seen_at,
    a.total_impressions,
    a.total_clicks,
    a.total_conversions,
    a.total_cost
from agg a
left join primary_channel p on p.campaign_id = a.campaign_id
