-- snowflake/ddl/06_fact_support_interactions.sql
-- fact_support_interactions — one row per support ticket
-- (data/lakehouse/silver/support_ticket.parquet), resolved to master_customer_id.

CREATE TABLE IF NOT EXISTS fact_support_interactions (
    ticket_id             VARCHAR(50)     NOT NULL,
    master_customer_id      VARCHAR(20),
    date_key_created           INTEGER,   -- FK to dim_date, derived from created_at
    date_key_resolved             INTEGER,-- FK to dim_date, derived from resolved_at (nullable)
    category                          VARCHAR(50),
    priority                             VARCHAR(20),
    sentiment                               VARCHAR(20),
    resolution_status                          VARCHAR(30),
    resolution_days                               INTEGER,  -- DATEDIFF(day, created_at, resolved_at)
    created_at                                        TIMESTAMP,
    resolved_at                                          TIMESTAMP,

    PRIMARY KEY (ticket_id)
);
