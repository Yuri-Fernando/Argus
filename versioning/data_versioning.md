# Data Versioning Policy

Applies to the synthetic datasets and to the Olist snapshot used across the project.

## Synthetic data — deterministic, not stored

Synthetic CSVs are **never committed to git** (see [`.gitignore`](../.gitignore)) — they're regenerated on demand by `make seed`. What *is* versioned is the thing that determines their content:

- `data/synthetic/config.yaml` (the `seed`, volume profiles, and dirty rates) — a git-tracked file, so `git blame`/`git log` shows exactly when and why the generated data's shape changed.
- The generator code itself (`data/synthetic/generators/`).

Given the same git commit, `python data/synthetic/generate_all.py --seed 42` always produces byte-identical output — see [DATA_MODEL.md §5](../DATA_MODEL.md#5-synthetic-data-generation-strategy). This means **the git commit hash *is* the dataset version**; there is no separate dataset registry needed for the synthetic sources.

## Olist snapshot

The Olist dataset itself is versioned upstream by its publisher on Kaggle (not by this repo). `ingestion/olist/download.py` records the download timestamp and row counts to `data/raw/olist/_manifest.json` (gitignored, regenerated per download) so a run can be traced back to "which Kaggle snapshot did this pipeline run against."

## Delta Lake native versioning

Once data lands in Bronze/Silver/Gold, Delta Lake's own transaction log gives every table point-in-time query capability (`VERSION AS OF` / `TIMESTAMP AS OF`) for free — this is the mechanism [`backup/disaster_recovery.md`](backup/disaster_recovery.md) relies on for accidental-write recovery, not a custom versioning layer.
