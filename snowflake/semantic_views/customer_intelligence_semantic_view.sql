-- snowflake/semantic_views/customer_intelligence_semantic_view.sql
--
-- NOT EXECUTED HERE — no live Snowflake account in this environment. This is real
-- Snowflake Semantic View DDL (GA Mar/2026, per snowflake/README.md and
-- docs/decisions/ADR-005-semantic-layer.md), written against the snowflake/ddl/
-- dim_*/fact_* tables. It implements the SAME metric definitions as
-- snowflake/local_runner.py::run_metric() and docs/semantic-dictionary.md — this file
-- is the "Snowflake Semantic Views" column of the semantic-dictionary parity matrix.
--
-- Would be validated by tests/data/test_metric_parity.py (ADR-005) against a live
-- account; that test cannot run without Snowflake credentials, which this task's
-- environment does not have.
--
-- Reference: https://docs.snowflake.com/en/user-guide/views-semantic/overview

CREATE OR REPLACE SEMANTIC VIEW customer_intelligence_semantic_view
    TABLES (
        customer AS dim_customer
            PRIMARY KEY (master_customer_id)
            WITH SYNONYMS ('customers', 'golden customers')
            COMMENT = 'One row per resolved master customer (post-MDM golden record).',
        payments AS fact_payments
            PRIMARY KEY (payment_id)
            WITH SYNONYMS ('transactions', 'orders')
            COMMENT = 'One row per payment; status = settled/pending/chargeback.',
        support AS fact_support_interactions
            PRIMARY KEY (ticket_id)
            COMMENT = 'One row per support ticket.',
        campaign_touches AS fact_campaign_interactions
            PRIMARY KEY (interaction_id)
            COMMENT = 'One row per campaign touch (impression/click/conversion).',
        web_events AS fact_web_events
            PRIMARY KEY (event_id)
            COMMENT = 'One row per clickstream event.'
    )

    RELATIONSHIPS (
        payments_to_customer AS
            payments (master_customer_id) REFERENCES customer (master_customer_id),
        support_to_customer AS
            support (master_customer_id) REFERENCES customer (master_customer_id),
        campaign_to_customer AS
            campaign_touches (master_customer_id) REFERENCES customer (master_customer_id),
        events_to_customer AS
            web_events (master_customer_id) REFERENCES customer (master_customer_id)
    )

    FACTS (
        payments.is_settled AS IFF(payments.status = 'settled', 1, 0)
    )

    DIMENSIONS (
        customer.master_customer_id AS customer.master_customer_id
            WITH SYNONYMS ('customer id') COMMENT = 'Golden-record customer key.',
        customer.segment AS customer.segment
            WITH SYNONYMS ('customer segment', 'RFM segment'),
        customer.state AS customer.state,
        payments.status AS payments.status
            WITH SYNONYMS ('payment status')
    )

    METRICS (
        -- Revenue — docs/semantic-dictionary.md "Revenue" section.
        -- Local-runner deviation note applies here too: no fact_orders in this
        -- platform snapshot, so Revenue is defined over settled payments net_amount
        -- rather than order_value. See snowflake/README.md "Known limitations".
        payments.revenue AS SUM(payments.net_amount)
            WHERE payments.status = 'settled'
            WITH SYNONYMS ('total revenue', 'settled revenue')
            COMMENT = 'SUM(net_amount) over settled payments — see semantic-dictionary.md Revenue (order-based definition; payments used here as the available proxy for completed-order revenue).',

        -- AOV — semantic-dictionary.md "AOV" section (freight_value not present here,
        -- so gross_amount is used as the end-to-end customer cost proxy).
        payments.aov AS SUM(payments.gross_amount) / COUNT(DISTINCT payments.payment_id)
            WHERE payments.status = 'settled'
            WITH SYNONYMS ('average order value')
            COMMENT = 'SUM(gross_amount) / COUNT(DISTINCT payment_id) over settled payments.',

        -- Churn Rate — semantic-dictionary.md "Churn Rate" section, proxy definition
        -- (recency_days > 90) documented in snowflake/README.md "Known limitations"
        -- since no ml/churn/ time-series label exists in this platform snapshot.
        customer.churn_rate AS
            SUM(IFF(customer.recency_days > 90, 1, 0)) / COUNT(customer.master_customer_id)
            WHERE customer.frequency >= 2
            WITH SYNONYMS ('churn')
            COMMENT = 'Proxy: recency_days > 90, denominator restricted to frequency >= 2 per semantic-dictionary.md exclusion rule.',

        -- Repeat Rate — semantic-dictionary.md "Repeat Rate" section.
        customer.repeat_rate AS
            SUM(IFF(customer.frequency >= 2, 1, 0)) / SUM(IFF(customer.frequency >= 1, 1, 0))
            WITH SYNONYMS ('retention rate', 'repeat purchase rate'),

        -- CLV — semantic-dictionary.md "CLV" section: surfaces dim_customer.lifetime_value,
        -- the pre-computed model output; the semantic layer does not re-derive it.
        customer.clv AS AVG(customer.lifetime_value)
            WITH SYNONYMS ('customer lifetime value', 'lifetime value')
            COMMENT = 'AVG(dim_customer.lifetime_value) — pre-computed by ml/, surfaced not recomputed. Proxy churn_score input documented in snowflake/README.md.'

        -- NPS, Delivery SLA, Orders, Data Quality Score are intentionally NOT defined
        -- here: NPS is "not yet implemented in any of the three layers" per
        -- semantic-dictionary.md; Delivery SLA and Orders require fact_orders
        -- (data/raw/olist), CONFIRMED ABSENT from this build; Data Quality Score is
        -- owned by the data_quality/ module, not this warehouse.
    )

    COMMENT = 'Enterprise Customer Intelligence semantic view — Snowflake GA (Mar/2026) implementation of docs/semantic-dictionary.md, mirroring snowflake/local_runner.py::run_metric(). Not executed in this environment: no live Snowflake account.';
