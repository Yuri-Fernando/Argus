# versioning/

This platform versions more than just code. This folder documents **how every layer is versioned** and, in [`backup/`](backup/), **how it's backed up and recovered** — a gap the original design conversations (`rascunho.md`) never addressed (see [IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md) §2 item 9).

## What's versioned, and how

| Layer | Mechanism | Where |
|---|---|---|
| **Specification / this repo** | [Semantic Versioning](https://semver.org/) + [Keep a Changelog](https://keepachangelog.com/) | [`../CHANGELOG.md`](../CHANGELOG.md) — the canonical, root-level changelog (GitHub renders it automatically; kept at root by convention) |
| **Data schemas** (Bronze/Silver/Gold, Golden Record) | Additive-by-default evolution policy, breaking changes require a migration script | [`schema_versioning.md`](schema_versioning.md) |
| **ML models** | MLflow Model Registry stages (`None → Staging → Production → Archived`) | [`model_versioning.md`](model_versioning.md), mirrored in [`../mlflow/registry.md`](../mlflow/registry.md) |
| **Synthetic datasets** | Deterministic seed (`data/synthetic/config.yaml`) + git tag on the generator code | [`data_versioning.md`](data_versioning.md) |
| **Infrastructure** | Terraform state (remote backend, versioned) + `terraform.lock.hcl` | [`../terraform/README.md`](../terraform/README.md) |
| **dbt models / metrics** | Git history + dbt's own model versioning (`version:` config in `.yml` files) | [`../dbt/README.md`](../dbt/README.md) |
| **Backups & Disaster Recovery** | Per-component RPO/RTO targets and recovery procedure | [`backup/`](backup/) |

## Why a dedicated folder instead of scattering this across each component's README

Versioning and backup/DR are cross-cutting concerns that get skipped when left implicit inside each component's docs — that omission is exactly what happened in the original design. Centralizing the *policy* here (each component's README still owns its own day-to-day mechanics) makes it a single, auditable place to check "is this platform actually recoverable?" — the kind of question a production-mindset interview will ask.
