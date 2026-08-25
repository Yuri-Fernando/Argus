-- int_customer_bridge — crm_customer_id -> master_customer_id, exploded from
-- golden_record.source_customer_ids (semicolon-delimited list of every source
-- CRM record survivorship-merged into this golden record).
--
-- Mirrors snowflake/local_runner.py::_build_bridge() exactly, but in SQL instead
-- of pandas. That function's docstring explains why the explode is *not* done in
-- the portable ANSI DDL in snowflake/ddl/ (SPLIT/FLATTEN syntax differs between
-- warehouses) — here in dbt we accept that divergence and use the Snowflake-native
-- LATERAL FLATTEN(SPLIT(...)) pattern, since dbt/README.md names dbt-snowflake as
-- a primary target adapter. On dbt-databricks, swap the LATERAL FLATTEN block for
-- `LATERAL VIEW explode(split(source_customer_ids, ';'))` — same fan-out, different
-- Databricks-native syntax; not written twice here to avoid drift between two
-- copies of the same logic.

with golden_record as (

    select
        master_customer_id,
        source_customer_ids
    from {{ source('mdm', 'golden_record') }}

),

exploded as (

    select
        gr.master_customer_id,
        trim(f.value::varchar) as crm_customer_id
    from golden_record gr,
    lateral flatten(input => split(gr.source_customer_ids, ';')) f

)

select
    crm_customer_id,
    master_customer_id
from exploded
where crm_customer_id is not null
  and crm_customer_id != ''
