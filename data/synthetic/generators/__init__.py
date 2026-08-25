"""Synthetic data generators — one module per source system.

Every generator function takes `n`, `seed`, and a `dirty_rates` / domain
config dict and returns a pandas DataFrame. See DATA_MODEL.md §5 for the
rationale (why each source is "dirty" on purpose).
"""
