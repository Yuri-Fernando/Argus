# Deployment

How local and cloud deployment work in practice, per [ADR-010](decisions/ADR-010-local-first-development.md) (local-first development) and [ARCHITECTURE.md §1](../ARCHITECTURE.md#1-design-principles) design principle 6. Everything below the cloud line can be developed and demoed without a single cloud resource provisioned.

## Local stack (default path)

The root [`docker-compose.yml`](../docker-compose.yml) brings up everything needed to develop and run the pipeline end to end with no cloud credentials:

| Service | Port | Stands in for | Purpose |
|---|---|---|---|
| **MinIO** | `9000` (S3 API), `9001` (console) | Azure Data Lake Storage Gen2 | S3-compatible object storage — `ingestion/` and `lakehouse/` code talks to it through the same `abfss://`-vs-`s3://`-agnostic storage layer used against real ADLS in the cloud, so no code path is local-only |
| **Postgres** | `5432` | — | MLflow's backend store (experiment/run metadata) |
| **MLflow** | `5000` | Azure Databricks-hosted MLflow | Experiment tracking + Model Registry, backed by the Postgres container and a local `mlruns` artifact volume |
| **Prometheus** | `9090` | Azure Monitor | Metrics scraping — `pipeline_duration`, `rows_processed`, `dq_score`, `ml_latency`, `agent_latency`, `mcp_calls`, `llm_tokens` ([ARCHITECTURE.md §17](../ARCHITECTURE.md#17-layer-14--observability--finops)) |
| **Grafana** | `3000` | — | Dashboards over the Prometheus metrics above (default login `admin`/`admin`, see `docker-compose.yml`) |

PySpark, GX Core, MDM entity resolution, dbt models against a local warehouse, and every agent's unit-testable logic all run against this stack — none of it requires Databricks, Snowflake, or Power BI to be live.

### Bringing it up

```bash
git clone <repo-url> && cd argus
cp .env.example .env
make up      # docker compose up -d — starts MinIO, Postgres, MLflow, Prometheus, Grafana
make seed    # downloads Olist + generates all synthetic datasets (DATA_MODEL.md §1)
make test    # unit + data tests
```

`make up` prints the MinIO console (`http://localhost:9001`) and MLflow UI (`http://localhost:5000`) URLs on success. `make seed` is `download-olist` (pulls the real Olist dataset via `ingestion/olist/download.py`) followed by `generate-synthetic` (runs `data/synthetic/generate_all.py --profile local`, which scales volumes down to a laptop-friendly size — 10k customers / 50k web events / 2k support tickets instead of the full 100k/1M/50k — see [DATA_MODEL.md §5](../DATA_MODEL.md#5-synthetic-data-generation-strategy)).

Other useful targets (full list: `make help`):

```bash
make dq          # run the GX Core data quality suite
make mdm         # run entity resolution / Golden Record pipeline
make mlflow-ui   # standalone MLflow UI, if you skip docker-compose's mlflow service
make down        # stop the local stack
make clean       # remove generated data, caches, __pycache__
```

## Cloud deployment (opt-in)

Cloud resources — Azure (ADLS, Data Factory, Event Hubs, Key Vault, Azure OpenAI), Databricks, Snowflake, and Power BI — are **not required** to explore the local pipeline, and are provisioned only when a specific sprint's acceptance criteria actually need the real service (e.g. Sprint 7 needs real Snowflake; Sprint 9 needs real Power BI — see [`terraform/README.md`](../terraform/README.md) and [ROADMAP.md](../ROADMAP.md)).

Provisioning is entirely through Terraform, never ClickOps:

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars   # fill in your own subscription/account values
terraform init
terraform plan
terraform apply
```

This wires up the modules under [`terraform/modules/{azure,databricks,snowflake}/`](../terraform/README.md) — owned by the infrastructure workstream, not this document — against a personal-budget sandbox subscription. Only `environments/dev/` ships full HCL in this repo; `staging/` and `prod/` are documented as the same module graph with progressively stricter approval gates (see [`terraform/README.md`](../terraform/README.md)).

Once cloud resources are up, the same code paths that ran against MinIO/local Postgres/local MLflow point at the real services by changing environment variables only (`.env`, never hard-coded endpoints — [ADR-010](decisions/ADR-010-local-first-development.md) consequences) — `abfss://` instead of the MinIO S3 endpoint, the Databricks workspace's own MLflow tracking URI instead of the local one, and so on.

## Teardown between demo sessions

Cloud components are **provisioned on demand and torn down between demo sessions** to control cost — a personal-budget project has no justification for Azure Databricks, Snowflake, and Power BI Premium capacity running continuously ([ADR-010](decisions/ADR-010-local-first-development.md)):

```bash
cd terraform/environments/dev
terraform destroy
```

This is safe because:

- All cloud state is reproducible: the local `make seed` datasets are deterministic (`--seed 42` — [DATA_MODEL.md §5](../DATA_MODEL.md#5-synthetic-data-generation-strategy)), so a fresh `terraform apply` followed by a pipeline re-run reconstructs the same Gold layer, Golden Record, and DQ scores byte-for-byte.
- MLflow experiment history, Golden Record survivorship logs, and human-in-the-loop approval logs that matter for demo continuity are periodically exported to the local/versioned artifact store, not left as the only copy inside ephemeral cloud infrastructure.
- `terraform apply`/`terraform destroy` is itself part of what this portfolio project demonstrates — Sprint 16's acceptance criteria specifically require an unattended `destroy` → `apply` cycle to succeed end to end (see [`terraform/README.md`](../terraform/README.md)).

## Related

- [ADR-010 — Local-first development](decisions/ADR-010-local-first-development.md) — the decision this document implements.
- [`terraform/README.md`](../terraform/README.md) — full IaC structure, provider rationale, environment layout.
- [DATA_MODEL.md §1](../DATA_MODEL.md#1-datasets--how-to-get-them) — dataset download/generation commands `make seed` wraps.
- [ARCHITECTURE.md §21](../ARCHITECTURE.md#21-production-readiness--honesty-note) — what "production-like" means given this cost-controlled deployment model.
