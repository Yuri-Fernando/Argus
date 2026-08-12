# mlflow/

Local MLflow tracking store (backed by the `postgres` + `mlflow` services in `docker-compose.yml`). No source code lives here — this directory holds the **tracking configuration** and is where `mlruns/`/`mlartifacts/` land locally (gitignored).

```
mlflow/
├── mlruns/          # gitignored — local experiment tracking data
├── mlartifacts/     # gitignored — model artifacts, SHAP plots, etc.
└── registry.md       # human-readable log of what's currently in Staging/Production and why (updated per promotion)
```

## Access

```bash
make mlflow-ui   # http://localhost:5000
```

In the cloud profile, this points at the Databricks-hosted MLflow tracking server instead (`DATABRICKS_HOST` in `.env`) — same experiment/run API, no code change needed.
