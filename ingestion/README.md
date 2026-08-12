# ingestion/

Everything responsible for getting data from a source system into `adls/landing/` (or its local MinIO equivalent). Built in **Sprint 1** — see [ROADMAP.md](../ROADMAP.md).

```
ingestion/
├── olist/          # download.py (implemented — see DATA_MODEL.md §1.1) + landing loader
├── api/             # thin clients for CRM/Marketing/Support synthetic "APIs" (simulated REST endpoints
│                     # over the generated CSVs, so the ingestion code path is realistic even though the
│                     # underlying data is a local file — see Sprint 1 acceptance criteria)
├── files/           # generic CSV/JSON/Parquet landing loader shared by all batch sources
└── streaming/        # Event Hubs producer/consumer stand-in for web_events (local: a simple Kafka-
                       # compatible consumer against a file-tailing producer, since standing up a full
                       # Event Hubs emulator is out of scope for the local profile)
```

## Design rule

Every loader here is **idempotent** and **storage-agnostic**: it writes through a thin `Storage` interface (`abfss://` in the cloud profile, the MinIO S3-compatible endpoint locally) so the same code path is exercised in both environments — no `if cloud: ... else: ...` branching inside business logic. See [ADR-010](../docs/decisions/ADR-010-local-first-development.md).

## Cloud provisioning

`terraform/modules/azure/{adls,data_factory,event_hubs}` provisions the real Azure Data Factory pipelines and Event Hubs namespace for the `dev` environment — optional until Sprint 1 needs to demo against real Azure.
