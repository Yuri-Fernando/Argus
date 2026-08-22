-- snowflake/ddl/07_fact_campaign_interactions.sql
-- fact_campaign_interactions — one row per campaign touch
-- (data/lakehouse/silver/campaign_interaction.parquet), resolved to master_customer_id.

CREATE TABLE IF NOT EXISTS fact_campaign_interactions (
    interaction_id        VARCHAR(50)     NOT NULL,
    master_customer_id       VARCHAR(20),
    campaign_id                  VARCHAR(50),   -- FK to dim_campaign
    date_key                        INTEGER,     -- FK to dim_date, derived from timestamp
    channel                            VARCHAR(50),
    impressions                           INTEGER,
    clicks                                   INTEGER,
    conversion                                  INTEGER,   -- 0/1 flag
    cost                                           DECIMAL(18,2),
    event_timestamp                                   TIMESTAMP,

    PRIMARY KEY (interaction_id)
);
