-- dim_geography — mirrors snowflake/ddl/03_dim_geography.sql. Distinct city/state
-- combinations observed across the Golden Record.

with distinct_geo as (

    select distinct
        city,
        state
    from {{ source('mdm', 'golden_record') }}
    where city is not null or state is not null

)

select
    {{ dbt_utils.generate_surrogate_key(['city', 'state']) }} as geography_id,
    city,
    state,
    'Brazil' as country
from distinct_geo
