-- snowflake/ddl/08_fact_web_events.sql
-- fact_web_events — one row per web/clickstream event
-- (data/lakehouse/silver/web_event.parquet), resolved to master_customer_id.

CREATE TABLE IF NOT EXISTS fact_web_events (
    session_id           VARCHAR(50),
    event_id                VARCHAR(64)     NOT NULL,   -- surrogate: row_number() over source
    master_customer_id          VARCHAR(20),
    date_key                       INTEGER,   -- FK to dim_date, derived from timestamp
    event_type                        VARCHAR(30),
    product_id                           VARCHAR(50),
    device                                   VARCHAR(30),
    browser                                    VARCHAR(30),
    source                                        VARCHAR(30),
    campaign                                         VARCHAR(50),
    event_timestamp                                     TIMESTAMP,

    PRIMARY KEY (event_id)
);
