-- Staging: 1:1 light pass-through over Silver crm_customer
-- (lakehouse/silver/crm_customer.py SCHEMA). No business logic here — identity
-- resolution to master_customer_id happens downstream in intermediate/int_customer_bridge.sql.

with source as (

    select * from {{ source('silver', 'crm_customer') }}

),

renamed as (

    select
        crm_customer_id,
        name              as customer_name,
        email             as customer_email,
        phone             as customer_phone,
        document_hash,
        birth_date,
        address,
        city,
        state,
        created_at        as crm_created_at,
        updated_at        as crm_updated_at

    from source

)

select * from renamed
