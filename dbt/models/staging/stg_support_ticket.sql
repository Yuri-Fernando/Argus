-- Staging: 1:1 light pass-through over Silver support_ticket
-- (lakehouse/silver/support_ticket.py SCHEMA).

with source as (

    select * from {{ source('silver', 'support_ticket') }}

),

renamed as (

    select
        ticket_id,
        customer_id       as crm_customer_id,
        category,
        priority,
        sentiment,
        created_at,
        resolved_at,
        resolution_status,
        datediff('day', created_at, resolved_at) as resolution_days

    from source

)

select * from renamed
