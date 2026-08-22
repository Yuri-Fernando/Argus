-- fact_campaign_interactions — mirrors snowflake/ddl/07_fact_campaign_interactions.sql.

select
    interaction_id,
    master_customer_id,
    campaign_id,
    date_key,
    channel,
    impressions,
    clicks,
    conversion,
    cost,
    event_timestamp
from {{ ref('int_campaign_interactions_resolved') }}
