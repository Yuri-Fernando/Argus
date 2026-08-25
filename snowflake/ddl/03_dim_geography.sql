-- snowflake/ddl/03_dim_geography.sql
-- dim_geography — distinct city/state combinations observed across golden_record.
-- Populated from data/mdm/golden_record.parquet (city, state columns).

CREATE TABLE IF NOT EXISTS dim_geography (
    geography_id    INTEGER     NOT NULL,
    city             VARCHAR(100),
    state             VARCHAR(10),
    country            VARCHAR(50) DEFAULT 'Brazil',

    PRIMARY KEY (geography_id)
);
