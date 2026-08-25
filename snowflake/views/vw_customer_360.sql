-- snowflake/views/vw_customer_360.sql
-- Customer 360: golden-record identity + RFM/behavioral features + segmentation +
-- proxy CLV/churn, joined with lifetime settled-payment totals. Portable ANSI SQL,
-- runs on both Snowflake and DuckDB (snowflake/local_runner.py).

CREATE OR REPLACE VIEW vw_customer_360 AS
SELECT
    c.master_customer_id,
    c.canonical_name,
    c.canonical_email,
    c.city,
    c.state,
    c.segment,
    c.recency_days,
    c.frequency,
    c.monetary,
    c.ticket_count,
    c.unresolved_count,
    c.avg_sentiment_score,
    c.churn_score,
    c.lifetime_value,
    c.is_repeat_customer,
    COALESCE(p.settled_payment_count, 0) AS settled_payment_count,
    COALESCE(p.settled_net_revenue, 0)   AS settled_net_revenue
FROM dim_customer c
LEFT JOIN (
    SELECT
        master_customer_id,
        COUNT(*)          AS settled_payment_count,
        SUM(net_amount)    AS settled_net_revenue
    FROM fact_payments
    WHERE status = 'settled'
    GROUP BY master_customer_id
) p ON p.master_customer_id = c.master_customer_id;
