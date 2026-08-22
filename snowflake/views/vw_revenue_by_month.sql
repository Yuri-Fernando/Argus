-- snowflake/views/vw_revenue_by_month.sql
-- Monthly Revenue (settled payments net_amount) and AOV, per docs/semantic-dictionary.md
-- (local stand-in: payments in place of fact_orders — see snowflake/README.md).
-- Portable ANSI SQL, runs on both Snowflake and DuckDB.

CREATE OR REPLACE VIEW vw_revenue_by_month AS
SELECT
    d.year,
    d.month,
    SUM(f.net_amount)                              AS revenue,
    SUM(f.gross_amount) / COUNT(DISTINCT f.payment_id) AS aov,
    COUNT(DISTINCT f.payment_id)                    AS settled_payment_count
FROM fact_payments f
JOIN dim_date d ON d.date_key = f.date_key
WHERE f.status = 'settled'
GROUP BY d.year, d.month
ORDER BY d.year, d.month;
