-- Staging: 1:1 light pass-through over Silver payment_finance
-- (lakehouse/silver/payment_finance.py SCHEMA). `status` and `method` are already
-- lower-cased in Silver. This is the local stand-in for order-level revenue facts
-- (no data/raw/olist fact_orders exists) — see docs/semantic-dictionary.md Revenue/AOV
-- and snowflake/local_runner.py run_metric() for the documented deviation.

with source as (

    select * from {{ source('silver', 'payment_finance') }}

),

renamed as (

    select
        payment_id,
        customer_id       as crm_customer_id,
        gross_amount,
        fee_amount,
        net_amount,
        method            as payment_method,
        status            as payment_status,   -- settled | pending | chargeback
        settled_at

    from source

)

select * from renamed
