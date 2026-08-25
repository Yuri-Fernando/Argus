"""KMeans customer segmentation over RFM + engagement features.

Run directly:

    python -m ml.segmentation.kmeans_segments

Writes `data/ml/segmentation/customer_segments.parquet` (one row per `master_customer_id` with
its assigned segment) and prints the segment distribution + per-segment feature profile.

Clustering features and preprocessing
--------------------------------------
`recency_days`, `frequency`, `monetary` (from `ml/features/rfm.py`) plus `event_count`,
`distinct_event_types`, `days_since_last_activity` (from `ml/features/engagement.py`) — support
features are deliberately excluded, since this segmentation is about purchasing/engagement
*behavior*, not support experience (a VIP customer who happens to have filed one ticket should
still cluster as a VIP).

`frequency`, `monetary`, and `event_count` are right-skewed (a small share of customers make many
more purchases/visits than the median) — this dataset is no exception (`frequency` ranges 0-8 with
a median of 1; `monetary` ranges $0-$13,136). Log1p-transforming these three before scaling is the
standard RFM-clustering fix: without it, KMeans (which minimizes Euclidean distance) lets the
handful of high-spend outliers dominate cluster assignment and the bulk of ordinary customers
collapse into one or two undifferentiated clusters. `StandardScaler` on top puts every one of the
six features on a comparable scale so no single feature (e.g. `monetary`'s raw dollar range vs.
`distinct_event_types`'s 0-6 range) dominates the distance metric by unit choice alone.

Segment naming rule
--------------------
KMeans produces 5 unlabeled clusters (`k=5`, chosen to match the 5 target business segments);
mapping cluster index -> {VIP, Loyal, Potential, At Risk, Inactive} needs a rule, since cluster
labels are arbitrary and their order is not guaranteed stable. `_assign_segment_names` ranks
each cluster on two independent axes computed from cluster-level (not per-customer) means:

  - `value_rank` (1=best): combined rank of monetary + frequency — how much this cluster has
    historically purchased.
  - `freshness_rank` (1=best): rank of `days_since_last_activity`, ascending — how recently this
    cluster has engaged with the site.

A single combined score (e.g. `value_rank + freshness_rank`) is enough to find the two extremes
unambiguously (the cluster that's best on both axes is the VIP tier; worst on both is Inactive),
but collapsing all five clusters onto one 1-D score for the middle three would misclassify a
zero-value-but-highly-engaged cluster as merely "less bad" rather than recognizing it as a
distinct opportunity segment. So after the two extremes are pulled out:

  - VIP = the cluster with the best (lowest) `value_rank + freshness_rank` — good on both axes.
  - Inactive = the cluster with the worst (highest) `value_rank + freshness_rank` — bad on both.
  - Among the remaining three: **Potential** = freshest (`freshness_rank` best) — customers
    engaging right now but without a purchase history yet, i.e. conversion opportunities, not
    people the business is at risk of losing. **At Risk** = stalest (`freshness_rank` worst) —
    customers who *did* build purchase history but have gone quiet, the opposite failure mode
    from Potential. **Loyal** = whichever cluster remains — solid value and reasonable recency,
    just short of the VIP tier.

This two-axis rule was validated against this dataset's actual cluster centroids (see
`ml/README.md` Results for the real numbers) — a purely 1-D "sort by composite score, slice into
5 bands" rule was tried first and produced a nonsensical mapping (a cluster with ~$0 lifetime
spend but 22-day-fresh engagement was ranked as one of the two worst clusters purely because its
zero purchase history dragged its composite score down, when the correct read of that cluster is
"Potential", not "second-worst").
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from ml.features.build_features import OUTPUT_PATH as FEATURES_PATH

logger = logging.getLogger("ml.segmentation.kmeans_segments")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

OUTPUT_PATH = Path("data/ml/segmentation/customer_segments.parquet")
RANDOM_STATE = 42
N_CLUSTERS = 5

CLUSTER_FEATURES: list[str] = [
    "recency_days",
    "frequency",
    "monetary",
    "event_count",
    "distinct_event_types",
    "days_since_last_activity",
]
LOG_TRANSFORM_FEATURES = ["frequency", "monetary", "event_count"]

SEGMENT_VIP = "VIP"
SEGMENT_LOYAL = "Loyal"
SEGMENT_POTENTIAL = "Potential"
SEGMENT_AT_RISK = "At Risk"
SEGMENT_INACTIVE = "Inactive"


def _prepare_cluster_matrix(features: pd.DataFrame) -> np.ndarray:
    """Log1p-transform skewed features, then standard-scale all clustering features."""
    matrix = features[CLUSTER_FEATURES].copy()
    for col in LOG_TRANSFORM_FEATURES:
        matrix[col] = np.log1p(matrix[col])
    return StandardScaler().fit_transform(matrix)


def _assign_segment_names(cluster_means: pd.DataFrame) -> dict[int, str]:
    """Map cluster index -> business segment name using the two-axis rule in the module
    docstring. `cluster_means` must be indexed by cluster id with raw (untransformed)
    `CLUSTER_FEATURES` columns.
    """
    value_rank = (
        (-cluster_means["monetary"]).rank() + (-cluster_means["frequency"]).rank()
    ).rank(method="first")
    freshness_rank = cluster_means["days_since_last_activity"].rank(method="first")
    combined = value_rank + freshness_rank

    remaining = set(cluster_means.index)
    vip_cluster = combined.idxmin()
    remaining.discard(vip_cluster)
    inactive_cluster = combined.loc[list(remaining)].idxmax()
    remaining.discard(inactive_cluster)

    remaining_freshness = freshness_rank.loc[list(remaining)]
    potential_cluster = remaining_freshness.idxmin()
    remaining.discard(potential_cluster)
    at_risk_cluster = remaining_freshness.loc[list(remaining)].idxmax()
    remaining.discard(at_risk_cluster)
    loyal_cluster = next(iter(remaining))

    return {
        vip_cluster: SEGMENT_VIP,
        loyal_cluster: SEGMENT_LOYAL,
        potential_cluster: SEGMENT_POTENTIAL,
        at_risk_cluster: SEGMENT_AT_RISK,
        inactive_cluster: SEGMENT_INACTIVE,
    }


def build_segments(
    features_path: Path = FEATURES_PATH, output_path: Path = OUTPUT_PATH
) -> pd.DataFrame:
    """Cluster customers and assign business segment names.

    Args:
        features_path: path to the Feature Store output.
        output_path: where to write the resulting segment assignments.

    Returns:
        DataFrame with `["master_customer_id", "cluster", "segment"]` plus the raw
        `CLUSTER_FEATURES`, also written to `output_path`.
    """
    features = pd.read_parquet(features_path)
    X = _prepare_cluster_matrix(features)

    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10)
    clusters = kmeans.fit_predict(X)

    result = features[["master_customer_id"] + CLUSTER_FEATURES].copy()
    result["cluster"] = clusters

    cluster_means = result.groupby("cluster")[CLUSTER_FEATURES].mean()
    segment_map = _assign_segment_names(cluster_means)
    result["segment"] = result["cluster"].map(segment_map)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output_path, index=False)
    logger.info("Wrote %d segmented customer rows to %s", len(result), output_path)
    return result


def print_segment_report(segments: pd.DataFrame) -> None:
    """Print the segment distribution table and per-segment feature profile."""
    distribution = segments["segment"].value_counts()
    distribution_pct = (distribution / len(segments) * 100).round(1)

    print("\nSegment distribution:")
    print(f"{'Segment':<12}{'Count':>8}{'Pct':>8}")
    for segment in [SEGMENT_VIP, SEGMENT_LOYAL, SEGMENT_POTENTIAL, SEGMENT_AT_RISK, SEGMENT_INACTIVE]:
        count = int(distribution.get(segment, 0))
        pct = distribution_pct.get(segment, 0.0)
        print(f"{segment:<12}{count:>8}{pct:>7.1f}%")

    print("\nPer-segment feature profile (mean values):")
    profile = segments.groupby("segment")[CLUSTER_FEATURES].mean().round(1)
    profile = profile.reindex([SEGMENT_VIP, SEGMENT_LOYAL, SEGMENT_POTENTIAL, SEGMENT_AT_RISK, SEGMENT_INACTIVE])
    print(profile.to_string())


if __name__ == "__main__":
    segment_result = build_segments()
    print_segment_report(segment_result)
