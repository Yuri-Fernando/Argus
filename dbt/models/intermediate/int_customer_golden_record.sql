-- int_customer_golden_record — one row per master_customer_id, joining the MDM
-- Golden Record identity to ML RFM/behavioral features and the segmentation
-- cluster/segment label, plus three derived columns computed HERE (not re-derived
-- downstream) so dim_customer is a pure select from this model.
--
-- This is the dbt mirror of snowflake/local_runner.py::build_warehouse()'s
-- dim_customer construction block — every derived-column formula below is copied
-- from there verbatim so the two implementations can never silently diverge
-- (see ADR-005 / tests/data/test_metric_parity.py).

with golden_record as (

    select * from {{ source('mdm', 'golden_record') }}

),

features as (

    select * from {{ source('ml', 'customer_features') }}

),

segments as (

    select
        master_customer_id,
        cluster,
        segment
    from {{ source('ml', 'customer_segments') }}

),

joined as (

    select
        gr.master_customer_id,
        gr.canonical_name,
        gr.canonical_email,
        gr.canonical_phone,
        gr.city,
        gr.state,
        gr.source_record_count,
        gr.created_at   as golden_record_created_at,
        gr.updated_at   as golden_record_updated_at,

        f.recency_days,
        f.frequency,
        f.monetary,
        f.event_count,
        f.distinct_event_types,
        f.days_since_last_activity,
        f.ticket_count,
        f.avg_sentiment_score,
        f.unresolved_count,

        s.cluster,
        s.segment

    from golden_record gr
    left join features f on f.master_customer_id = gr.master_customer_id
    left join segments s on s.master_customer_id = gr.master_customer_id

),

derived as (

    select
        *,

        -- is_repeat_customer: frequency >= 2, treating missing frequency as 0.
        -- Mirrors local_runner.py: dim_customer["frequency"].fillna(0) >= 2
        coalesce(frequency, 0) >= 2 as is_repeat_customer,

        -- churn_score: recency-based proxy standing in for the missing ml/churn/
        -- model output (no ml/churn/ parquet exists in this snapshot). Matches
        -- the semantic dictionary's "no purchase in trailing 90+ days" churn
        -- intuition, scaled to [0,1]. Mirrors local_runner.py:
        --   (recency_days.fillna(365) / 365.0).clip(upper=1.0)
        least(1.0, coalesce(recency_days, 365) / 365.0) as churn_score

    from joined

),

final as (

    select
        *,

        -- lifetime_value: structurally per docs/semantic-dictionary.md CLV formula
        -- (expected future Revenue, weighted by 1 - churn_score, using historical
        -- AOV proxy and frequency as purchase rate). Mirrors local_runner.py:
        --   avg_order_value = (monetary / frequency.replace(0, NA)).fillna(0.0)
        --   lifetime_value = avg_order_value * frequency.fillna(0) * (1 - churn_score)
        round(
            coalesce(monetary / nullif(frequency, 0), 0.0)
            * coalesce(frequency, 0)
            * (1 - churn_score),
            2
        ) as lifetime_value

    from derived

)

select
    master_customer_id,
    canonical_name,
    canonical_email,
    canonical_phone,
    city,
    state,
    source_record_count,
    golden_record_created_at,
    golden_record_updated_at,
    recency_days,
    frequency,
    monetary,
    event_count,
    distinct_event_types,
    days_since_last_activity,
    ticket_count,
    avg_sentiment_score,
    unresolved_count,
    cluster,
    segment,
    is_repeat_customer,
    churn_score,
    lifetime_value
from final
