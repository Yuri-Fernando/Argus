# LGPD Compliance Policy

**LGPD** (Lei Geral de Proteção de Dados, Federal Law 13,709/2018) is Brazil's general data protection law — the closest local equivalent to GDPR, and the applicable framework for any platform holding Brazilian customer data. This document states how the platform's design honors LGPD principles.

> **This is a demonstration of LGPD-aware design, not a real Data Protection Officer (DPO) document.** No formal Relatório de Impacto à Proteção de Dados (RIPD), no registered ANPD filing, no real legal review exists behind it. Its purpose is to show that the architecture was built *as if* it held real personal data, because that is the discipline the target roles (Itaú, Nubank, Mercado Livre, and similar regulated-adjacent employers) expect from a data platform engineer.

## No real PII exists in this repository

Per [ADR-009](../docs/decisions/ADR-009-dataset-strategy.md):

- The Olist Brazilian E-Commerce dataset is **already anonymized** by its publisher (CC BY-NC-SA 4.0, Kaggle) — it contains no recoverable individual identity.
- Every CRM/Marketing/Support/Web/Finance record is **synthetically generated** (`Faker`, `pt_BR` locale, fixed seed — [DATA_MODEL.md §5](../DATA_MODEL.md#5-synthetic-data-generation-strategy)). No real name, email, phone, or address is ever written to disk.
- Every document-style identifier (the CRM analogue of a CPF) is stored **only as a SHA-256 hash of a fake value** — `document_hash`, never a raw document number, real or synthetic.
- `tests/data/test_no_real_pii.py` scans every generated fixture against a denylist of real-looking patterns before it is allowed to be committed — this is enforced in CI, not a one-time manual check.

Everything below therefore describes the **policy the platform would enforce if the data were real** — the classification, masking, and rights-handling machinery is real and testable; the underlying data is not.

## Legal basis per data category

LGPD Art. 7 requires an explicit legal basis (*base legal*) for processing each category of personal data. If this were a real deployment, the bases below are the ones each category would be processed under:

| Data category | Example fields | Legal basis (LGPD Art. 7) | Rationale |
|---|---|---|---|
| Account / contact data | `canonical_email`, `canonical_phone`, `canonical_name` | VII — execução de contrato (contract execution) | Needed to fulfill an order, ship a product, or respond to a support ticket |
| Order / transaction data | `fact_orders`, `fact_payments` | VII — execução de contrato | Direct record of a purchase the customer initiated |
| Marketing interaction data | `campaign_interactions` | I — consentimento (consent) | Opt-in campaigns; a customer can be present in `crm_customers` without ever appearing in `campaign_interactions` |
| Support ticket content | `support_tickets`, sentiment field | VII — execução de contrato / IX — legítimo interesse (legitimate interest, for aggregate sentiment analysis only) | Ticket handling is contractual; sentiment aggregation for product improvement is legitimate interest, scoped to non-identifying rollups |
| Derived scores (churn, CLV, segment) | `churn_score`, `lifetime_value`, `customer_segment` | IX — legítimo interesse | Internal business analytics; never used for automated decisions without human review (see Art. 20 below) |
| Web behavioral data | `web_events` | I — consentimento (cookie/tracking consent) | Clickstream is the most sensitive-by-inference category; treated as consent-gated even though it is synthetic here |

## Data subject rights (LGPD Art. 18)

Art. 18 grants the *titular* (data subject) a specific set of rights. The platform's design supports each one structurally, even though there is no real subject to exercise them against today:

| Right (Art. 18) | How the platform would support it |
|---|---|
| **Confirmation & access** (I, II) | `get_customer(master_customer_id)` MCP tool returns every field the Golden Record holds for that customer, subject to the requester's own role-based masking (`pii.md`) |
| **Correction** (III) | Corrections flow through the same survivorship mechanism as any other update — logged to `mdm/golden_record/survivorship_log/` with `{field, winning_source, rule_applied, timestamp}` ([DATA_MODEL.md §4](../DATA_MODEL.md#4-golden-record--survivorship-rules)), so a correction is auditable, not a silent overwrite |
| **Anonymization, blocking, or deletion** (IV) | A `master_customer_id` can be marked for erasure; downstream Gold/Snowflake/Power BI/ML feature tables are re-materialized without that key on the next scheduled run — deletion is a pipeline re-run, not a manual multi-system hunt, because the Golden Record is the single point of truth |
| **Portability** (V) | `get_customer` + `get_customer_orders` + `get_customer_quality` together produce a complete, structured export of one customer's data — the same MCP tools used for support already return a portable JSON shape |
| **Information about sharing** (VI) | Data does not leave the platform's own Databricks/Snowflake boundary; there are no third-party data sales or transfers to disclose |
| **Information about the option to deny consent, and consequences** (VII) | Applies to the consent-gated categories above (marketing, web tracking) — a customer can exist in the platform (contractual data) without being present in consent-gated tables |
| **Revocation of consent** (VIII) | Revoking marketing/web-tracking consent removes future rows from `campaign_interactions`/`web_events` ingestion for that `master_customer_id`; historical rows already aggregated into a metric are handled per the retention policy below |
| **Review of automated decisions** (Art. 20, related) | No agent auto-executes a merge, refund, or retention offer from a churn/CLV score — every consequential recommendation is gated by human approval ([ADR-006](../docs/decisions/ADR-006-human-in-the-loop.md)), which is itself how Art. 20's right to review of automated decisions is satisfied structurally |

## `AI_REDACT` on export

Snowflake's `AI_REDACT` AI Function ([ARCHITECTURE.md §12](../ARCHITECTURE.md#12-layer-9--snowflake-enterprise-dwh--cortex)) is applied on **every export path** out of the governed warehouse — Power BI extracts, ad-hoc CSV pulls, and any Cortex Agents response that would otherwise surface a raw PII-classified column value to a role not authorized to see it unmasked (see [`pii.md`](pii.md) for the classification and role matrix). `AI_REDACT` is a defense-in-depth layer on top of, not instead of, Snowflake masking policies and row-access policies applied directly on the PII columns (`email`, `phone`, `document_hash` — [ARCHITECTURE.md §16](../ARCHITECTURE.md#16-layer-13--governance--security)).

## Retention policy

| Data category | Retention | Rationale |
|---|---|---|
| Bronze (raw ingested) | 90 days rolling, then archived to `adls/archive/` | Replay/audit window without indefinite raw retention |
| Silver / Gold (Golden Record) | Retained for the life of the customer relationship + 5 years after last activity | Aligns with typical Brazilian consumer/fiscal retention expectations (Código de Defesa do Consumidor references); a real deployment would confirm this against actual legal counsel, not this document |
| Survivorship log (`mdm/golden_record/survivorship_log/`) | Retained indefinitely, append-only | Required for LGPD accountability (*prestação de contas*) — you must be able to explain why the platform believes a given field is correct, even long after the merge happened |
| Web events (`web_events`) | 13 months rolling | Matches common cookie-consent retention windows |
| Human-in-the-loop approval log (`agents/recommendation/approval_queue.py`) | Retained indefinitely, append-only | Same accountability rationale as the survivorship log — see [`security.md`](security.md) Repudiation row |
| Deleted/anonymized customer (Art. 18 IV request) | Removed from all Gold/Snowflake/Power BI/ML tables on next scheduled re-materialization; survivorship and approval logs retain the `master_customer_id` reference (not the PII itself) as the accountability trail requires | Deletion of personal data does not delete the record that a deletion happened |

## Related

- [ADR-009 — Dataset strategy](../docs/decisions/ADR-009-dataset-strategy.md) — why no real PII exists anywhere in this repo.
- [ADR-006 — Human-in-the-loop](../docs/decisions/ADR-006-human-in-the-loop.md) — how Art. 20 is honored structurally.
- [`pii.md`](pii.md) — field-level classification and masking policy.
- [`security.md`](security.md) — the AI-specific threat model that protects this same data from a different angle.
- [DATA_MODEL.md §4](../DATA_MODEL.md#4-golden-record--survivorship-rules) — survivorship log structure.
