# Data Dictionary

Column-by-column dictionary for every table introduced in [DATA_MODEL.md §6](../DATA_MODEL.md#6-data-dictionary): Olist-derived Bronze/Silver tables, synthetic CRM/Marketing/Support/Web/Finance sources, and the Gold dimensional model ([DATA_MODEL.md §3](../DATA_MODEL.md#3-gold-layer--dimensional-model)). This is the **human-readable companion** to the machine-enforced Unity Catalog / Snowflake registries — see [`governance/data_catalog.md`](../governance/data_catalog.md) for how the two relate.

PII classification values below (`Direct identifier`, `Quasi-identifier`, `Sensitive`, `Non-PII`) are defined and cross-referenced in [`governance/pii.md`](../governance/pii.md) — this document does not redefine them, only tags each column.

---

## Olist-derived tables (Silver layer)

### `silver.customer` (from `olist_customers_dataset.csv`)

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `customer_id` | string | Olist | Quasi-identifier | Per-order customer key (Olist issues a new one per order) |
| `customer_unique_id` | string | Olist | Quasi-identifier | Stable customer key across orders — the join key MDM resolves into `master_customer_id` |
| `customer_zip_code_prefix` | string | Olist | Quasi-identifier | First 5 digits of the Brazilian postal code |
| `customer_city` | string | Olist | Quasi-identifier | |
| `customer_state` | string | Olist | Quasi-identifier | 2-letter Brazilian state code |

### `silver.order`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `order_id` | string | Olist | Non-PII | Primary key |
| `customer_id` | string | Olist | Quasi-identifier | FK to `silver.customer` |
| `order_status` | string | Olist | Non-PII | e.g. `delivered`, `shipped`, `canceled` |
| `order_purchase_timestamp` | timestamp | Olist | Non-PII | |
| `order_delivered_customer_date` | timestamp, nullable | Olist | Non-PII | Null if not yet delivered |
| `order_estimated_delivery_date` | timestamp | Olist | Non-PII | Feeds the Delivery SLA metric ([`semantic-dictionary.md`](semantic-dictionary.md)) |

### `silver.order_item`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `order_id` | string | Olist | Non-PII | FK to `silver.order` |
| `product_id` | string | Olist | Non-PII | FK to `silver.product` |
| `seller_id` | string | Olist | Non-PII | FK to `silver.product`'s seller |
| `price` | float | Olist | Non-PII | |
| `freight_value` | float | Olist | Non-PII | |

### `silver.product`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `product_id` | string | Olist | Non-PII | Primary key |
| `product_category_name` | string | Olist | Non-PII | Joined against `product_category_name_translation.csv` for English labels |

### `silver.payment`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `order_id` | string | Olist | Non-PII | FK to `silver.order` |
| `payment_type` | string | Olist | Non-PII | e.g. `credit_card`, `boleto` |
| `payment_installments` | int | Olist | Non-PII | |

### `silver.review`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `order_id` | string | Olist | Non-PII | FK to `silver.order` |
| `review_score` | int (1–5) | Olist | Non-PII | Feeds the NPS metric via `review_score_10 = review_score * 2` mapping |

---

## Synthetic sources (Bronze/Silver layer)

### `crm_customers`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `crm_customer_id` | string | Synthetic CRM (`Faker`, seed `42`) | Quasi-identifier | Source-system key, resolved into `master_customer_id` by MDM |
| `name` | string | Synthetic CRM | Direct identifier | |
| `email` | string, nullable | Synthetic CRM | Direct identifier | 2% deliberately missing ([DATA_MODEL.md §5](../DATA_MODEL.md#5-synthetic-data-generation-strategy)) |
| `phone` | string | Synthetic CRM | Direct identifier | 1% deliberately invalid format |
| `document_hash` | string | Synthetic CRM | Direct identifier | SHA-256 of a fake CPF — never the raw value, even synthetically |
| `birth_date` | date | Synthetic CRM | Quasi-identifier | |
| `address` | string | Synthetic CRM | Quasi-identifier | 1% deliberately inconsistent city/state pairing |
| `city`, `state` | string | Synthetic CRM | Quasi-identifier | |
| `created_at`, `updated_at` | timestamp | Synthetic CRM | Non-PII | `updated_at` decides `city`/`state` survivorship ([DATA_MODEL.md §4](../DATA_MODEL.md#4-golden-record--survivorship-rules)) |

5% of rows are near-duplicates of another row by design — the MDM ground truth ([`mdm/README.md`](../mdm/README.md)).

### `campaigns`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `campaign_id` | string | Synthetic Marketing | Non-PII | Primary key |
| `name` | string | Synthetic Marketing | Non-PII | |
| `channel` | string | Synthetic Marketing | Non-PII | e.g. `email`, `sms`, `push` |
| `start_date`, `end_date` | date | Synthetic Marketing | Non-PII | |
| `budget` | float | Synthetic Marketing | Non-PII | |

### `campaign_interactions`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `customer_id` | string | Synthetic Marketing | Quasi-identifier | FK, joins to `crm_customer_id` via MDM |
| `campaign_id` | string | Synthetic Marketing | Non-PII | FK to `campaigns` |
| `channel` | string | Synthetic Marketing | Non-PII | |
| `impressions`, `clicks` | int | Synthetic Marketing | Non-PII | |
| `conversion` | boolean | Synthetic Marketing | Non-PII | |
| `cost` | float | Synthetic Marketing | Non-PII | |
| `timestamp` | timestamp | Synthetic Marketing | Non-PII | |

Consent-gated per [`governance/lgpd.md`](../governance/lgpd.md) — legal basis is consent, not contract execution.

### `support_tickets`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `ticket_id` | string | Synthetic Support | Non-PII | Primary key |
| `customer_id` | string | Synthetic Support | Quasi-identifier | FK, resolved via MDM |
| `category` | string | Synthetic Support | Non-PII | |
| `priority` | string | Synthetic Support | Non-PII | |
| `sentiment` | string | Synthetic Support | Sensitive | Derived by `AI_SENTIMENT`; treated as sensitive per [`governance/pii.md`](../governance/pii.md) |
| `created_at`, `resolved_at` | timestamp | Synthetic Support | Non-PII | |
| `resolution_status` | string | Synthetic Support | Non-PII | |

### `web_events`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `session_id` | string | Synthetic Web | Quasi-identifier | Device/session fingerprint proxy |
| `customer_id` | string, nullable | Synthetic Web | Quasi-identifier | Null for anonymous/pre-login sessions |
| `event_type` | string | Synthetic Web | Non-PII | e.g. `page_view`, `add_to_cart` |
| `product_id` | string | Synthetic Web | Non-PII | FK to `silver.product` |
| `timestamp` | timestamp | Synthetic Web | Non-PII | |
| `device`, `browser` | string | Synthetic Web | Quasi-identifier | |
| `source`, `campaign` | string | Synthetic Web | Non-PII | |

~1M rows, sized to exercise distributed PySpark processing ([DATA_MODEL.md §2](../DATA_MODEL.md#2-bronze--silver-schemas-per-source)).

---

## Gold layer — dimensional model

Full ER diagram: [DATA_MODEL.md §3](../DATA_MODEL.md#3-gold-layer--dimensional-model). Snowflake DDL mirror: [`snowflake/tables/`](../snowflake/README.md).

### `dim_customer` — the Golden Record

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `master_customer_id` | string | MDM (`mdm/golden_record/`) | Quasi-identifier | Primary key — the resolved Single Customer View identity |
| `canonical_name` | string | MDM survivorship | Direct identifier | Longest non-truncated value, title-cased ([DATA_MODEL.md §4](../DATA_MODEL.md#4-golden-record--survivorship-rules)) |
| `canonical_email` | string | MDM survivorship | Direct identifier | CRM > Olist > Marketing priority |
| `canonical_phone` | string | MDM survivorship | Direct identifier | CRM > Support > Olist priority |
| `city`, `state` | string | MDM survivorship | Quasi-identifier | Most recent `updated_at` wins |
| `customer_segment` | string | `ml/segmentation/` | Sensitive (derived) | `VIP / Loyal / Potential / At Risk / Inactive` |
| `customer_quality_score` | float | Data Quality layer | Non-PII | Per-customer rollup of the Data Quality Score metric ([`semantic-dictionary.md`](semantic-dictionary.md)) |
| `churn_score` | float | `ml/churn/` | Sensitive (derived) | SHAP-explained, tracked in MLflow |
| `lifetime_value` | float | `ml/churn/` + `ml/segmentation/` | Sensitive (derived) | The CLV metric ([`semantic-dictionary.md`](semantic-dictionary.md)) |
| `created_at`, `updated_at` | timestamp | MDM pipeline | Non-PII | |

### `fact_orders`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `order_id` | string | Olist | Non-PII | Primary key |
| `customer_key` | string | MDM (FK to `dim_customer.master_customer_id`) | Quasi-identifier | |
| `date_key` | string | FK to `dim_date` | Non-PII | |
| `order_value` | float | Olist | Non-PII | Feeds Revenue, AOV ([`semantic-dictionary.md`](semantic-dictionary.md)) |
| `freight_value` | float | Olist | Non-PII | Excluded from Revenue, included in AOV |
| `delivery_days` | int | Derived (Silver transform) | Non-PII | `order_delivered_customer_date − order_purchase_timestamp` |
| `review_score` | int | Olist | Non-PII | |
| `status` | string | Olist | Non-PII | |

### `fact_order_items`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `order_id` | string | Olist | Non-PII | FK to `fact_orders` |
| `product_key` | string | FK to `dim_product` | Non-PII | |
| `seller_key` | string | FK to `dim_seller` | Non-PII | |
| `quantity` | int | Olist | Non-PII | |
| `price` | float | Olist | Non-PII | |

### `fact_payments`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `order_id` | string | Olist | Non-PII | FK to `fact_orders` |
| `payment_type` | string | Olist | Non-PII | |
| `installments` | int | Olist | Non-PII | |
| `amount` | float | Olist | Non-PII | |

### `fact_customer_interactions`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `customer_key` | string | MDM (FK to `dim_customer`) | Quasi-identifier | |
| `channel` | string | Synthetic Marketing / Web | Non-PII | |
| `event_type` | string | Synthetic Marketing / Web | Non-PII | |
| `occurred_at` | timestamp | Synthetic Marketing / Web | Non-PII | |

### `fact_support`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `ticket_id` | string | Synthetic Support | Non-PII | Primary key |
| `customer_key` | string | MDM (FK to `dim_customer`) | Quasi-identifier | |
| `category` | string | Synthetic Support | Non-PII | |
| `sentiment` | string | Synthetic Support | Sensitive | |
| `resolution_status` | string | Synthetic Support | Non-PII | |

### `dim_product`, `dim_seller`, `dim_date`

| Column | Type | Source system | PII classification | Description |
|---|---|---|---|---|
| `product_key` / `product_id` | string | Olist | Non-PII | `dim_product` primary key |
| `product_category_name` | string | Olist | Non-PII | |
| `seller_key` / `seller_id` | string | Olist | Non-PII | `dim_seller` primary key |
| `date_key` | string | Generated calendar table | Non-PII | `dim_date` primary key, standard calendar attributes (year/quarter/month/day/is_weekend) |

---

## Related

- [`governance/pii.md`](../governance/pii.md) — full classification scheme and masking policy per role.
- [`governance/data_catalog.md`](../governance/data_catalog.md) — where these tables live in Unity Catalog / Snowflake.
- [DATA_MODEL.md](../DATA_MODEL.md) — dataset generation strategy and full ER diagram.
- [`docs/semantic-dictionary.md`](semantic-dictionary.md) — metric-level (not column-level) definitions built on top of these tables.
