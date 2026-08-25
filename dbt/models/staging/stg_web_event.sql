-- Staging: 1:1 light pass-through over Silver web_event
-- (lakehouse/silver/web_event.py SCHEMA). No natural primary key in the source
-- (matches snowflake/local_runner.py, which generates a surrogate `event_id` at
-- fact-load time) — a surrogate key is generated here instead so staging output
-- is unique per row.

with source as (

    select * from {{ source('silver', 'web_event') }}

),

renamed as (

    select
        {{ dbt_utils.generate_surrogate_key(['session_id', 'customer_id', 'event_type', 'timestamp']) }} as event_id,
        session_id,
        customer_id       as crm_customer_id,
        event_type,
        product_id,
        timestamp         as event_timestamp,
        device,
        browser,
        source            as traffic_source,
        campaign

    from source

)

select * from renamed
