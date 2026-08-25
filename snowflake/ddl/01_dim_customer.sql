-- snowflake/ddl/01_dim_customer.sql
-- dim_customer — one row per resolved master customer (post-MDM golden record).
-- Portable ANSI SQL: runs unmodified on Snowflake and on DuckDB (see snowflake/local_runner.py).
--
-- Source: data/mdm/golden_record.parquet (identity) joined to
--         data/ml/features/customer_features.parquet (RFM + behavioral features) and
--         data/ml/segmentation/customer_segments.parquet (cluster/segment label).
--
-- churn_score and lifetime_value are PROXIES, not the real ml/churn/ model output —
-- this repo snapshot has no ml/churn/ artifact on disk (only ml/features/ and
-- ml/segmentation/ exist). See snowflake/README.md "Known limitations" for the exact
-- formula and why it stands in for the real model. Semantic-dictionary CLV formula
-- (docs/semantic-dictionary.md) is preserved structurally: lifetime_value =
-- f(AOV, purchase frequency, 1 - churn_score) — only the churn_score input is a proxy.

CREATE TABLE IF NOT EXISTS dim_customer (
    master_customer_id         VARCHAR(20)     NOT NULL,
    canonical_name              VARCHAR(200),
    canonical_email             VARCHAR(200),
    canonical_phone             VARCHAR(30),
    city                        VARCHAR(100),
    state                       VARCHAR(10),
    source_record_count         INTEGER,
    golden_record_created_at    TIMESTAMP,
    golden_record_updated_at    TIMESTAMP,

    -- RFM / behavioral features (data/ml/features/customer_features.parquet)
    recency_days                INTEGER,
    frequency                   INTEGER,        -- proxy for historical completed-order count
    monetary                    DECIMAL(18,2),
    event_count                 INTEGER,
    distinct_event_types        INTEGER,
    days_since_last_activity    INTEGER,
    ticket_count                INTEGER,
    avg_sentiment_score         DECIMAL(6,3),
    unresolved_count            INTEGER,

    -- Segmentation (data/ml/segmentation/customer_segments.parquet)
    cluster                     INTEGER,
    segment                     VARCHAR(30),

    -- Derived / proxy fields (computed in snowflake/local_runner.py, documented above)
    is_repeat_customer          BOOLEAN,        -- frequency >= 2 (Repeat Rate metric numerator)
    churn_score                 DECIMAL(6,4),   -- proxy: LEAST(1.0, recency_days / 365.0)
    lifetime_value               DECIMAL(18,2),  -- proxy CLV, see header note

    PRIMARY KEY (master_customer_id)
);
