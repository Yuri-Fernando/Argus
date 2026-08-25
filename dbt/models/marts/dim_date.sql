-- dim_date — mirrors snowflake/ddl/02_dim_date.sql. Standard calendar date spine,
-- spanning the min/max event_timestamp/settled_at/created_at across every fact
-- source, matching snowflake/local_runner.py::_load_dim_date() bounds.
--
-- Requires the dbt_utils package (packages.yml, not present in this repo snapshot —
-- structural reference only per this task's "do not run dbt" constraint). On a real
-- run: add `dbt-labs/dbt_utils` to packages.yml and `dbt deps`.

with bounds as (

    select
        least(
            min(settled_at),
            (select min(created_at) from {{ ref('int_support_tickets_resolved') }}),
            (select min(event_timestamp) from {{ ref('int_campaign_interactions_resolved') }}),
            (select min(event_timestamp) from {{ ref('int_web_events_resolved') }})
        ) as min_date,
        greatest(
            max(settled_at),
            (select max(created_at) from {{ ref('int_support_tickets_resolved') }}),
            (select max(event_timestamp) from {{ ref('int_campaign_interactions_resolved') }}),
            (select max(event_timestamp) from {{ ref('int_web_events_resolved') }})
        ) as max_date
    from {{ ref('int_payments_resolved') }}

),

spine as (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="(select cast(date_trunc('day', min_date) as date) from bounds)",
        end_date="(select dateadd('day', 1, cast(date_trunc('day', max_date) as date)) from bounds)"
    ) }}

)

select
    cast(to_char(date_day, 'YYYYMMDD') as integer) as date_key,
    date_day                                       as full_date,
    extract(year from date_day)                    as year,
    extract(quarter from date_day)                 as quarter,
    extract(month from date_day)                   as month,
    to_char(date_day, 'MMMM')                       as month_name,
    extract(day from date_day)                      as day,
    dayofweek(date_day)                              as day_of_week,
    to_char(date_day, 'DY')                           as day_name,
    dayofweek(date_day) in (0, 6)                       as is_weekend
from spine
