-- int_payments_resolved — stg_payment_finance resolved to master_customer_id via
-- int_customer_bridge, plus a date_key derived from settled_at for the dim_date FK.
-- Mirrors snowflake/local_runner.py fact_payments build block.

with payments as (

    select * from {{ ref('stg_payment_finance') }}

),

bridge as (

    select * from {{ ref('int_customer_bridge') }}

)

select
    p.payment_id,
    b.master_customer_id,
    cast(to_char(p.settled_at, 'YYYYMMDD') as integer) as date_key,
    p.gross_amount,
    p.fee_amount,
    p.net_amount,
    p.payment_method as method,
    p.payment_status as status,
    p.settled_at
from payments p
left join bridge b on b.crm_customer_id = p.crm_customer_id
