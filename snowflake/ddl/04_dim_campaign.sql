-- snowflake/ddl/04_dim_campaign.sql
-- dim_campaign — one row per distinct campaign_id observed in campaign_interaction.
-- Populated from data/lakehouse/silver/campaign_interaction.parquet.

CREATE TABLE IF NOT EXISTS dim_campaign (
    campaign_id        VARCHAR(50)     NOT NULL,
    primary_channel      VARCHAR(50),   -- most frequent channel value for this campaign_id
    first_seen_at          TIMESTAMP,
    last_seen_at             TIMESTAMP,
    total_impressions          BIGINT,
    total_clicks                 BIGINT,
    total_conversions              BIGINT,
    total_cost                       DECIMAL(18,2),

    PRIMARY KEY (campaign_id)
);
