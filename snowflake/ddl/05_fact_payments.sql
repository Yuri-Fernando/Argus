-- snowflake/ddl/05_fact_payments.sql
-- fact_payments — one row per payment (data/lakehouse/silver/payment_finance.parquet),
-- resolved to master_customer_id via the golden-record identity bridge.
--
-- This is the local stand-in for Revenue/AOV: this platform snapshot has no
-- data/raw/olist fact_orders, so Revenue and AOV are computed against SETTLED
-- payments (net_amount / gross_amount) rather than order_value. See
-- snowflake/README.md "Known limitations" and snowflake/local_runner.py run_metric().

CREATE TABLE IF NOT EXISTS fact_payments (
    payment_id          VARCHAR(50)     NOT NULL,
    master_customer_id    VARCHAR(20),
    date_key                INTEGER,      -- FK to dim_date, derived from settled_at
    gross_amount               DECIMAL(18,2),
    fee_amount                    DECIMAL(18,2),
    net_amount                       DECIMAL(18,2),
    method                              VARCHAR(30),
    status                                VARCHAR(20),   -- settled | pending | chargeback
    settled_at                              TIMESTAMP,

    PRIMARY KEY (payment_id)
);
