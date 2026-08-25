"""Churn modeling — label definition, training/comparison, and MLflow-tracked champion selection.

No ground-truth "did this customer churn" label exists anywhere in the synthetic source data (no
subscription-cancellation event, no explicit churn flag) — see `ml/churn/label.py` for the
proxy-label definition and the reasoning behind it.
"""
