# PII Classification & Masking Policy

Field-level classification for every PII-bearing field introduced across [DATA_MODEL.md](../DATA_MODEL.md) (Bronze/Silver sources §2, Gold dimensional model §3), plus the masking policy applied per Unity Catalog and Snowflake role. Companion to [`lgpd.md`](lgpd.md) (why the policy exists) and [`access_control.md`](access_control.md) (the roles referenced below).

## Classification scheme

| Classification | Definition |
|---|---|
| **Direct identifier** | Uniquely and directly identifies a person on its own |
| **Quasi-identifier** | Does not identify alone, but narrows the population sharply when combined with other quasi-identifiers |
| **Sensitive** | LGPD Art. 5 II "dado pessoal sensível"-adjacent, or business-sensitive derived attribute whose exposure creates risk beyond simple re-identification |
| **Non-PII** | Carries no personal-identification risk on its own |

## Field classification table

| Field | Source table(s) | Classification | Notes |
|---|---|---|---|
| `canonical_email` / `email` | `dim_customer`, `crm_customers` | Direct identifier | CRM is system of record ([DATA_MODEL.md §4](../DATA_MODEL.md#4-golden-record--survivorship-rules)) |
| `canonical_phone` / `phone` | `dim_customer`, `crm_customers` | Direct identifier | 1% deliberately invalid format in synthetic source |
| `document_hash` | `crm_customers` | Direct identifier | SHA-256 of a fake CPF — never the raw value, even synthetically ([DATA_MODEL.md §5](../DATA_MODEL.md#5-synthetic-data-generation-strategy)) |
| `canonical_name` / `name` | `dim_customer`, `crm_customers` | Direct identifier | |
| `birth_date` | `crm_customers` | Quasi-identifier | Combined with `city`/`state` can narrow re-identification sharply |
| `address` | `crm_customers` | Quasi-identifier | 1% deliberately inconsistent city/state pairs in synthetic source |
| `city`, `state` | `dim_customer`, `crm_customers` | Quasi-identifier | Low risk alone; masked jointly with `address`/`birth_date` in restrictive contexts |
| `customer_zip_code_prefix` | Olist `customers` | Quasi-identifier | Geolocation proxy at prefix granularity |
| `customer_unique_id`, `crm_customer_id`, `master_customer_id` | Olist, `crm_customers`, `dim_customer` | Quasi-identifier | Pseudonymous keys — not directly identifying alone, but a stable join key across every table that touches a person, which is exactly what makes it powerful for re-identification if combined with an external source |
| `churn_score`, `lifetime_value`, `customer_segment`, `customer_quality_score` | `dim_customer` | Sensitive (derived) | Not personal-identification risk, but business-sensitive: exposing a customer's churn/CLV score outside authorized roles creates commercial and fairness risk (profiling) |
| `sentiment` | `support_tickets` | Sensitive | Free-text-derived signal about a person's emotional state / satisfaction |
| `review_score`, `resolution_status` | `fact_orders`, `fact_support` | Non-PII | Transaction/ticket-level facts, not personally identifying on their own |
| `order_id`, `order_value`, `freight_value`, `payment_type`, `installments` | `fact_orders`, `fact_payments` | Non-PII | Financial facts about a transaction, not a person — becomes quasi-identifying only if joined back to `master_customer_id`, which is where the join-key row above matters |
| `product_category_name`, `seller_id` | `dim_product`, `dim_seller` | Non-PII | Catalog/seller data |
| `session_id`, `device`, `browser`, `source`, `campaign` | `web_events` | Quasi-identifier | Device/session fingerprints are treated as quasi-identifying per common web-privacy practice |

## Masking policy by role

Masking is enforced with Snowflake **masking policies** on the columns above and mirrored with Unity Catalog **row/column-level security** on the Delta equivalents ([ARCHITECTURE.md §16](../ARCHITECTURE.md#16-layer-13--governance--security)). The reference pattern — mirrored across both platforms:

| Role (Unity Catalog / Snowflake) | Direct identifiers (`email`, `phone`, `document_hash`, `name`) | Quasi-identifiers (`address`, `birth_date`, `zip_prefix`) | Sensitive derived (`churn_score`, `lifetime_value`, `sentiment`) | Justification required? |
|---|---|---|---|---|
| `data_analyst` | **Masked** (`***@***.com`-style / hashed) | **Masked** at coarse granularity (city/state visible, street/zip masked) | Visible, aggregated only (no row-level customer detail) | No — masking is the default, unmasked access is the exception |
| `data_steward` | **Unmasked** | **Unmasked** | Visible, row-level | Yes — access is logged and tied to a data-quality/MDM investigation ticket, per [ADR-006](../docs/decisions/ADR-006-human-in-the-loop.md)'s accountability principle |
| `data_engineer` | **Masked** in query results; unmasked only in pipeline execution context (no interactive SQL access to raw PII) | Masked in query results | Visible, aggregated only | No, but pipeline-context access is logged |
| `ml_engineer` | **Masked**; feature tables consume `master_customer_id` as a pseudonymous key, never raw PII | Masked | Visible, row-level (needed for training/evaluation) | No |
| `agent_service_account` (MCP) | **Masked by default**; unmasked only when the *inheriting* human caller holds `data_steward` — the agent never has a standing elevated grant of its own ([`access_control.md`](access_control.md#mcp-tool-call-inheritance)) | Same inheritance rule | Visible when the inheriting caller's role permits | Inherits the human caller's justification, never bypasses it |

This mirrors the `DATA_ANALYST` (masked) vs. `DATA_STEWARD` (authorized, logged) pattern used throughout the platform's role design: **masking is the default state for every PII-classified field, and unmasking is a deliberate, logged exception — never the other way around.**

## Related

- [`lgpd.md`](lgpd.md) — legal basis and data subject rights this classification supports.
- [`access_control.md`](access_control.md) — full RBAC model, including how MCP tool calls inherit these roles.
- [`security.md`](security.md) — why Cortex AI Guardrails and MCP tool scoping exist as a second layer on top of this masking policy.
- [DATA_MODEL.md §6](../DATA_MODEL.md#6-data-dictionary) → [`docs/data_dictionary.md`](../docs/data_dictionary.md) — the full column dictionary that cross-references this classification per field.
