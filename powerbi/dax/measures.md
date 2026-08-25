# DAX Measures

Every measure below is layered on top of the semantic model (`powerbi/semantic_model/`),
which connects to Snowflake Semantic Views / dbt marts — **never** DAX re-deriving a
metric from a raw table (`powerbi/README.md` "Hard rule"). Each formula is cross-checked
line-by-line against `snowflake/local_runner.py::run_metric()`, the reference
implementation for this repo snapshot, and traces to the canonical definition in
`docs/semantic-dictionary.md`. Where the local snapshot's data forces a documented
deviation from the canonical formula (no `data/raw/olist` order data), that deviation is
called out explicitly — never silently.

Values quoted next to each measure are this repo snapshot's actual computed values, from
`snowflake/local_runner.py` — used here as an expected-value contract, not an example.

---

## Revenue

```dax
Revenue =
SUMX (
    FILTER ( fact_payments, fact_payments[status] = "settled" ),
    fact_payments[net_amount]
)
```

- **Canonical definition** (`docs/semantic-dictionary.md`): `SUM(order_value)` over
  `status = 'completed'` orders, freight excluded.
- **Local deviation**: no `fact_orders` exists in this snapshot, so Revenue sums
  `fact_payments.net_amount` filtered to `status = "settled"` — the settled-payment
  proxy for "completed and recognized". This mirrors `local_runner.py` exactly:
  ```python
  SELECT SUM(net_amount) FROM fact_payments WHERE status = 'settled'
  ```
- **Expected value** (this snapshot): **R$ 15,515,805.42**

---

## AOV (Average Order Value)

```dax
AOV =
DIVIDE (
    SUMX ( FILTER ( fact_payments, fact_payments[status] = "settled" ), fact_payments[gross_amount] ),
    CALCULATE (
        DISTINCTCOUNT ( fact_payments[payment_id] ),
        fact_payments[status] = "settled"
    )
)
```

- **Canonical definition**: `SUM(order_value + freight_value) / COUNT(DISTINCT order_id)`
  over completed orders — freight **is** included (unlike Revenue).
- **Local deviation**: `payment_finance` has no `freight_value` column, so AOV uses
  `gross_amount` (which already nets in fees the customer effectively pays) as the
  closest "end to end cost to customer" figure, divided by distinct settled
  `payment_id` count. Mirrors `local_runner.py` exactly:
  ```python
  SELECT SUM(gross_amount), COUNT(DISTINCT payment_id)
  FROM fact_payments WHERE status = 'settled'
  ```
- **Expected value** (this snapshot): **R$ 1,751.79**

---

## Churn Rate

```dax
Churn Rate =
DIVIDE (
    CALCULATE (
        DISTINCTCOUNT ( dim_customer[master_customer_id] ),
        dim_customer[recency_days] > 90,
        dim_customer[frequency] >= 2
    ),
    CALCULATE (
        DISTINCTCOUNT ( dim_customer[master_customer_id] ),
        dim_customer[frequency] >= 2
    )
)
```

- **Canonical definition**: `COUNT(churned=TRUE in period) / COUNT(active at period start)`,
  excluding customers with fewer than 2 historical orders from the denominator.
- **Local deviation**: no `ml/churn/` time-series churn label exists on disk, so `churned`
  is a snapshot proxy: `recency_days > 90` (matches the semantic dictionary's own
  "no purchase in trailing 90 days" label definition). Denominator filters
  `frequency >= 2`, exactly as specified. Mirrors `local_runner.py` exactly:
  ```sql
  SELECT
    SUM(CASE WHEN recency_days > 90 THEN 1 ELSE 0 END) AS churned,
    COUNT(*) AS eligible
  FROM dim_customer WHERE frequency >= 2
  ```
- **Expected value** (this snapshot): **0.5308** (53.08%)

---

## Repeat Rate

```dax
Repeat Rate =
DIVIDE (
    CALCULATE (
        DISTINCTCOUNT ( dim_customer[master_customer_id] ),
        dim_customer[frequency] >= 2
    ),
    CALCULATE (
        DISTINCTCOUNT ( dim_customer[master_customer_id] ),
        dim_customer[frequency] >= 1
    )
)
```

- **Canonical definition**: `COUNT(order_count >= 2) / COUNT(order_count >= 1)`,
  cancelled/returned orders excluded from `order_count`.
- **Local deviation**: `dim_customer.frequency` (from `ml/features/`) is used as the
  completed-order-count proxy — `payment_finance` has no cancelled/returned status to
  net out beyond what `frequency` already reflects. Mirrors `local_runner.py` exactly:
  ```sql
  SELECT
    SUM(CASE WHEN frequency >= 2 THEN 1 ELSE 0 END) AS repeat_customers,
    SUM(CASE WHEN frequency >= 1 THEN 1 ELSE 0 END) AS active_customers
  FROM dim_customer
  ```
- **Expected value** (this snapshot): **0.4033** (40.33%)

---

## CLV (Customer Lifetime Value)

```dax
CLV (avg) =
AVERAGEX (
    FILTER ( dim_customer, NOT ISBLANK ( dim_customer[lifetime_value] ) ),
    dim_customer[lifetime_value]
)

CLV (median) =
MEDIANX (
    FILTER ( dim_customer, NOT ISBLANK ( dim_customer[lifetime_value] ) ),
    dim_customer[lifetime_value]
)

CLV (min) = CALCULATE ( MIN ( dim_customer[lifetime_value] ) )
CLV (max) = CALCULATE ( MAX ( dim_customer[lifetime_value] ) )
```

- **Canonical definition**: `dim_customer.lifetime_value` — the ML-modeled projection
  (expected future Revenue over a forward horizon, weighted by `1 - churn_score`,
  using historical AOV/frequency features). Per the semantic dictionary, the semantic
  layer **surfaces**, never re-derives, this value.
- **Local deviation**: `dim_customer.lifetime_value` is itself a proxy in this snapshot
  (no `ml/churn/` model output exists, so `churn_score` is the recency-based proxy
  above) — but the DAX correctly does not re-derive it, exactly as the canonical
  definition requires. Mirrors `local_runner.py` exactly:
  ```sql
  SELECT AVG(lifetime_value), MIN(lifetime_value), MAX(lifetime_value), MEDIAN(lifetime_value)
  FROM dim_customer WHERE lifetime_value IS NOT NULL
  ```
- **Expected value** (this snapshot): **avg R$ 990.26**

---

## Supporting / context measures

These are not in the five headline metrics above but are referenced by the dashboard
pages (`powerbi/dashboard/`) and are computable from the same tables.

```dax
Active Customers =
CALCULATE ( DISTINCTCOUNT ( dim_customer[master_customer_id] ), dim_customer[frequency] >= 1 )

Total Customers = DISTINCTCOUNT ( dim_customer[master_customer_id] )

Settled Payment Count =
CALCULATE ( DISTINCTCOUNT ( fact_payments[payment_id] ), fact_payments[status] = "settled" )

Support Ticket Volume = COUNTROWS ( fact_support_interactions )

Unresolved Ticket Rate =
DIVIDE (
    COUNTROWS ( FILTER ( fact_support_interactions, fact_support_interactions[resolution_status] <> "resolved" ) ),
    COUNTROWS ( fact_support_interactions )
)

Avg Ticket Resolution Days =
AVERAGE ( fact_support_interactions[resolution_days] )

Avg Sentiment Score =
AVERAGE ( dim_customer[avg_sentiment_score] )

Campaign Conversion Rate =
DIVIDE ( SUM ( fact_campaign_interactions[conversion] ), SUM ( fact_campaign_interactions[clicks] ) )

Campaign Click-Through Rate =
DIVIDE ( SUM ( fact_campaign_interactions[clicks] ), SUM ( fact_campaign_interactions[impressions] ) )

Web Event Count = COUNTROWS ( fact_web_events )
```

## Metrics NOT implemented (documented, not invented)

Per `docs/semantic-dictionary.md` and `snowflake/local_runner.py SKIPPED_METRICS`, the
following canonical metrics have **no DAX measure** in this file because the underlying
data does not exist in this repo snapshot — inventing a value for them would violate
the "one metric, one definition, backed by real data" principle this platform is built
around:

| Metric | Why skipped |
|---|---|
| **Orders** | Requires `fact_orders` (`data/raw/olist`), confirmed absent from this build. |
| **Delivery SLA** | Requires `order_delivered_customer_date` / `order_estimated_delivery_date` (`data/raw/olist`), confirmed absent. |
| **NPS** | Not yet implemented in any of the three semantic layers per `docs/semantic-dictionary.md` — canonical definition exists, tracked as Sprint 8+ backlog. |
| **Data Quality Score** | Owned by `data_quality/` module, not a warehouse-native semantic-layer metric. |
