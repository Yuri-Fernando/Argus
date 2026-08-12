# data/

Local landing zone for everything before it reaches ADLS/Databricks — this is the local-dev stand-in described in [ADR-010](../docs/decisions/ADR-010-local-first-development.md).

```
data/
├── raw/
│   └── olist/          # populated by `make download-olist` — see DATA_MODEL.md §1.1
├── synthetic/           # populated by `make generate-synthetic` — see DATA_MODEL.md §1.2
│   ├── crm/
│   ├── marketing/
│   ├── support/
│   ├── web/
│   └── finance/
└── documents/            # RAG source policy documents — see DATA_MODEL.md §1.2, ARCHITECTURE.md §14
```

**Nothing under `raw/` or the generated files under `synthetic/`/`documents/` is committed to git** (see [`.gitignore`](../.gitignore)) — they're regenerated deterministically by `make seed`. Only the *generator code* (`synthetic/generators/`, `synthetic/config.yaml`, `synthetic/generate_all.py`) is version-controlled.

Get everything in one command: `make seed` — see [README.md §9](../README.md#9-getting-started-local-dev) and [DATA_MODEL.md](../DATA_MODEL.md) for full detail.
