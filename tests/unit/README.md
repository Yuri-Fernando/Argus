# tests/unit/

This directory intentionally stays near-empty. Real unit tests land **alongside the code they test** — e.g. `mdm/matching/test_fuzzy.py` next to `mdm/matching/fuzzy.py`, `ml/churn/test_features.py` next to `ml/churn/features.py` — following `pytest`'s standard test-discovery behavior (`pyproject.toml`'s `testpaths = ["tests"]` is extended per-module by each workstream's own `pytest.ini`-equivalent path, or simply relies on pytest's rootdir-relative discovery picking up `test_*.py` files wherever they live once those modules exist).

This is an explicit convention, not an oversight: co-locating unit tests keeps a module's logic and its correctness proof in the same diff, the same PR, and the same mental unit — consistent with how `data/synthetic/generators/crm.py` and its eventual `data/synthetic/generators/test_crm.py` are meant to travel together.

`tests/data/`, `tests/ml/`, and `tests/ai/` are the exception to this rule — see [tests/README.md](../README.md) for why those stay centralized instead.
