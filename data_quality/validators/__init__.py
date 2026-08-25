"""Data Quality validation engine — see engine.py for the rule catalog contract.

Optional/alternative path: Great Expectations 1.0+ Checkpoints wired to these
same Silver tables would satisfy the same contract (see data_quality/README.md)
but are NOT the primary/default path implemented here — this package's
`DQEngine` (pure pandas) is what `lakehouse/run_pipeline.py` actually calls.
"""
