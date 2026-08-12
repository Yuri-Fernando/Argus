# tests/

The test pyramid for the platform — `pyproject.toml` points `pytest` at this directory (`testpaths = ["tests"]`). Five categories, each becoming non-trivial at a different point in [ROADMAP.md](../ROADMAP.md), by design: there is no value in writing a churn-model regression test before there is a churn model.

```
tests/
├── unit/          # fast, no I/O — see tests/unit/README.md
├── integration/   # multi-component, local stack (MinIO/Postgres/MLflow) — see tests/integration/README.md
├── data/          # data quality / MDM / semantic-layer correctness — this directory, non-trivial from Sprint 0
├── ml/            # model metric regression — see tests/ml/README.md
└── ai/            # agent evaluation harnesses — see tests/ai/README.md
```

## Unit

Fast, isolated, no network/filesystem I/O beyond tmp fixtures — pure function correctness (a survivorship rule, a similarity score, a DAX-equivalent aggregation). These land **alongside the code they test**, not centrally in `tests/unit/` — see [tests/unit/README.md](unit/README.md) for the convention. Trivial through Sprint 3, grows meaningfully from **Sprint 4** (MDM matching functions) onward, since that's the first layer with enough pure logic to be worth unit-testing in isolation from data.

## Integration

Exercises real component boundaries against the local Docker stack (`docker-compose.yml`): a pipeline job actually writing to MinIO, an MDM run actually reading from Postgres, an MCP tool actually returning data end-to-end. Like unit tests, these land next to the code they cover — see [tests/integration/README.md](integration/README.md). Meaningful from **Sprint 2** (Bronze/Silver landing in the local lake) and critical by **Sprint 13** (MCP server tool calls, which are integration tests almost by definition).

## Data

Lives in `tests/data/` (this repo's scope, kept centralized rather than co-located, since these tests validate cross-cutting platform guarantees — "no real PII anywhere," "one metric one definition," "quarantine actually quarantines" — not any single module). Non-trivial starting **Sprint 0**: `test_no_real_pii.py` is a real, running gate from day one, because the LGPD promise in ARCHITECTURE.md §16 has to hold from the very first synthetic row generated, not retrofitted later. `test_dq_quarantine.py` activates at **Sprint 3**, `test_gold_snowflake_parity.py` at **Sprint 7**, `test_metric_parity.py` at **Sprint 8** — each currently a documented `pytest.skip` stub until its sprint lands (see each file's docstring for the exact assertion it will make).

## ML

Model metric regression tests — asserts a retrained/refactored model doesn't quietly get worse (ROC-AUC, F1, PR-AUC floors; segment-distribution sanity checks). Non-trivial from **Sprint 10** (churn model) and **Sprint 11** (segmentation) — see [tests/ml/README.md](ml/README.md). `.github/workflows/ml.yml` runs a smoke-test version of this on every PR touching `ml/`.

## AI

Agent evaluation harnesses — golden question sets, LLM-as-judge scoring, prompt-injection defense verification, human-in-the-loop gate enforcement. Non-trivial from **Sprint 14** (`agents/*/evaluation/`, owned by the agentic-AI workstream) — see [tests/ai/README.md](ai/README.md). This is the category most tightly coupled to ARCHITECTURE.md §15's "no agent auto-executes unsupervised" guarantee, so its tests double as evidence for that design principle, not just quality gates.
