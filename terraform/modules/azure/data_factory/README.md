# modules/azure/data_factory

Provisions the Azure Data Factory instance and its two linked services (ADLS Gen2 via managed identity, Key Vault for source-system credentials) that back the scheduled batch ingestion described in [ARCHITECTURE.md §4](../../../../ARCHITECTURE.md#4-layer-1--sources--ingestion) — CRM/Marketing/Support exports and the Olist CSV drop, all landing untouched in `adls/landing/`. Pipeline/dataset JSON itself is authored in `ingestion/api/` and deployed separately; this module only owns the ADF instance and its trust relationships.

Built in **Sprint 1** ([ROADMAP.md](../../../../ROADMAP.md)), alongside `adls`.
