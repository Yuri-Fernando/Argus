# modules/azure/adls

Provisions the ADLS Gen2 storage account (`is_hns_enabled = true`) and the eight containers that make up the data lake's lifecycle structure — `landing/ raw/ bronze/ silver/ gold/ quarantine/ checkpoints/ archive/` — matching [ARCHITECTURE.md §5](../../../../ARCHITECTURE.md#5-layer-2--data-lake-adls-gen2) exactly, so the same prefixes used by `ingestion/`, `lakehouse/`, and the local MinIO dev stack map 1:1 onto real cloud storage.

Built in **Sprint 1** ([ROADMAP.md](../../../../ROADMAP.md)) — this is the first cloud module the roadmap calls for, optional at that stage since local dev runs entirely against MinIO until a real ADLS container is needed.
