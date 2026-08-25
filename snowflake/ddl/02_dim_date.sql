-- snowflake/ddl/02_dim_date.sql
-- dim_date — standard calendar date dimension. Populated in snowflake/local_runner.py
-- by generating a date spine (no external date source needed). Portable ANSI SQL.

CREATE TABLE IF NOT EXISTS dim_date (
    date_key        INTEGER     NOT NULL,   -- YYYYMMDD, e.g. 20260821
    full_date       DATE        NOT NULL,
    year             INTEGER,
    quarter          INTEGER,
    month             INTEGER,
    month_name        VARCHAR(20),
    day                INTEGER,
    day_of_week         INTEGER,   -- 0=Monday .. 6=Sunday
    day_name             VARCHAR(20),
    is_weekend            BOOLEAN,

    PRIMARY KEY (date_key)
);
