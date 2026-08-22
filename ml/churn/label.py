"""Proxy churn label definition.

No table in this platform's synthetic sources records a real "customer churned" event — there is
no subscription-cancellation timestamp, no account-closure flag, nothing to supervise against
directly. Every churn model in this package is therefore trained against a PROXY label defined
here, not ground truth. That is disclosed explicitly rather than presented as if a real label
existed, per this project's "No Invention" discipline (ARCHITECTURE.md / AIOX Constitution
Article IV) — a model is only as honest as the label it was trained on.

Label construction
-------------------
1. **Risk score** — a weighted combination of four churn-relevant signals, each drawn from
   `ml/features/build_features.py`'s output:
     - `disengagement_z` (weight 0.45): z-scored `days_since_last_activity` — how unusually long
       this customer has gone without visiting the site, relative to the customer base. Weighted
       highest because sustained inactivity is the single strongest behavioral churn indicator.
     - `unresolved_flag` (weight 0.25): 1.0 if the customer has an open/escalated support ticket.
     - `negative_sentiment_flag` (weight 0.15): 1.0 if net support sentiment is negative.
     - `no_purchase_flag` (weight 0.15): 1.0 if zero settled payments (never converted).
2. **Injected noise** — real churn is never a deterministic function of the handful of signals
   any single feature store can capture (macroeconomic conditions, competitor offers, life
   events — all unobserved here). A Gaussian noise term (`NOISE_STD`) is added to `risk_score`
   before thresholding, so the resulting label is correlated with — but not perfectly
   reconstructible from — the engineered features. This is a deliberate, disclosed modeling
   choice: without it, a label built as an exact deterministic function of the very features a
   tree ensemble would train on trivially reaches ROC-AUC ~1.0, which would look like — and
   effectively be — leakage baked into the label itself, not a meaningful demonstration of churn
   prediction. `NOISE_STD = 0.5` was chosen empirically as the point where all three candidate
   models (`ml/churn/train.py`) land in a realistic, differentiated 0.80-0.90 ROC-AUC band
   instead of a suspiciously perfect one.
3. **Thresholding** — the noisy risk score is cut at its `1 - TARGET_POSITIVE_RATE` quantile, so
   the label's positive rate is pinned to `TARGET_POSITIVE_RATE` (15%) by construction — the
   ~10-20% range typical of real subscription/e-commerce churn problems, tight enough to be a
   meaningfully imbalanced classification problem worth comparing calibration on.

This is a documented modeling choice, not a discovered ground truth, and should be revisited the
moment a real churn/cancellation event becomes available in the source data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RANDOM_STATE = 42
NOISE_STD = 0.5
TARGET_POSITIVE_RATE = 0.15
LABEL_COLUMN = "churned"

# Risk-score component weights — see module docstring point 1.
WEIGHT_DISENGAGEMENT = 0.45
WEIGHT_UNRESOLVED = 0.25
WEIGHT_NEGATIVE_SENTIMENT = 0.15
WEIGHT_NO_PURCHASE = 0.15


def _zscore(series: pd.Series) -> pd.Series:
    return (series - series.mean()) / (series.std() + 1e-9)


def add_churn_label(
    features: pd.DataFrame,
    target_positive_rate: float = TARGET_POSITIVE_RATE,
    noise_std: float = NOISE_STD,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Attach the proxy `churned` label (see module docstring) to a customer feature table.

    Args:
        features: output of `ml.features.build_features.build_customer_features`, must contain
            `days_since_last_activity`, `unresolved_count`, `avg_sentiment_score`, `frequency`.
        target_positive_rate: fraction of customers labeled churned, by construction (0.15 = 15%).
        noise_std: standard deviation of the Gaussian noise added to the risk score before
            thresholding — see module docstring point 2 for why this exists.
        random_state: seed for the noise draw, fixed by default for reproducibility (matching
            this project's `--seed 42` convention, ADR-009).

    Returns:
        `features` with an added binary `churned` column (int 0/1) and the intermediate
        `churn_risk_score` column (kept for inspection/debugging, not intended as a model
        feature — see `ml/churn/train.py` FEATURE_COLUMNS, which excludes it).
    """
    disengagement_z = _zscore(features["days_since_last_activity"])
    unresolved_flag = (features["unresolved_count"] > 0).astype(float)
    negative_sentiment_flag = (features["avg_sentiment_score"] < 0).astype(float)
    no_purchase_flag = (features["frequency"] == 0).astype(float)

    risk_score = (
        WEIGHT_DISENGAGEMENT * disengagement_z
        + WEIGHT_UNRESOLVED * unresolved_flag
        + WEIGHT_NEGATIVE_SENTIMENT * negative_sentiment_flag
        + WEIGHT_NO_PURCHASE * no_purchase_flag
    )

    rng = np.random.default_rng(random_state)
    noisy_score = risk_score + rng.normal(0, noise_std, size=len(risk_score))
    threshold = np.quantile(noisy_score, 1 - target_positive_rate)

    labeled = features.copy()
    labeled["churn_risk_score"] = noisy_score
    labeled[LABEL_COLUMN] = (noisy_score > threshold).astype(int)
    return labeled
