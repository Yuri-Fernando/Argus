-- Staging: 1:1 light pass-through over Silver campaign_interaction
-- (lakehouse/silver/campaign_interaction.py SCHEMA).

with source as (

    select * from {{ source('silver', 'campaign_interaction') }}

),

renamed as (

    select
        interaction_id,
        customer_id       as crm_customer_id,
        campaign_id,
        channel,
        impressions,
        clicks,
        conversion,              -- 0/1 flag
        cost,
        timestamp         as event_timestamp

    from source

)

select * from renamed
