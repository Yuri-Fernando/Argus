"""Field-level survivorship rules, as code (DATA_MODEL.md §4).

DATA_MODEL.md §4 defines survivorship as a *cross-source* priority table
(e.g. `canonical_email`: CRM > Olist > Marketing). This portfolio's data
sources are CRM-only (see mdm/README.md -- Olist is confirmed absent), so
every merged cluster's members all come from the same source ("CRM") and
the documented priority table never has more than one candidate source to
choose from. DATA_MODEL.md does not specify a tie-break for that case, so
each rule below falls back to **most-recently-updated record wins**
(`updated_at` descending) -- consistent with the `city`/`state` rule
DATA_MODEL.md *does* fully specify, and with this file's role as the single
place that fallback is documented, per mdm/README.md's `mdm/survivorship/`
description ("field-level survivorship rule definitions ... as code").

Every rule function takes the list of member rows (`pd.Series`) for one
`master_customer_id` cluster and returns
`(winning_value, winning_record_id, rule_applied, rationale)` so
`mdm/golden_record/build.py` can both assemble the golden row and write an
auditable `mdm/golden_record/survivorship_log/` entry per field.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd


@dataclass
class SurvivorshipDecision:
    field: str
    winning_value: object
    winning_record_id: str
    losing_record_ids: list[str]
    rule_applied: str
    rationale: str


def _updated_at_sort_key(record: pd.Series) -> pd.Timestamp:
    """`record.get("updated_at") or pd.Timestamp.min` looks right but is a real bug: `bool(pd.NaT)`
    is `True` in pandas, so `NaT or pd.Timestamp.min` evaluates to `NaT` itself (the `or` never
    falls through), not the intended fallback. A code-review pass caught this: `NaT` compares
    `False` to everything, so sorting a list containing one silently produces an order that
    depends on the record's original position rather than a correct chronological ranking — a
    NaT-dated duplicate could beat a genuinely more-recent record for survivorship. Using
    `pd.notna()` explicitly (never relying on Python truthiness for a pandas null) fixes it."""
    val = record.get("updated_at")
    return val if pd.notna(val) else pd.Timestamp.min


def _most_recently_updated(records: list[pd.Series], value_field: str) -> tuple[object, str, list[str]]:
    """Pick the non-null `value_field` from the record with the latest
    `updated_at`; falls back to the next-most-recent if the latest record's
    value is null."""
    ordered = sorted(records, key=_updated_at_sort_key, reverse=True)
    for rec in ordered:
        val = rec.get(value_field)
        if pd.notna(val) and str(val).strip():
            others = [r["crm_customer_id"] for r in records if r["crm_customer_id"] != rec["crm_customer_id"]]
            return val, rec["crm_customer_id"], others
    # every record null on this field
    rec = ordered[0]
    others = [r["crm_customer_id"] for r in records if r["crm_customer_id"] != rec["crm_customer_id"]]
    return rec.get(value_field), rec["crm_customer_id"], others


def survive_canonical_email(records: list[pd.Series]) -> SurvivorshipDecision:
    """DATA_MODEL.md §4: CRM > Olist > Marketing priority (single-source
    fallback: most-recently-updated non-null value wins)."""
    value, winner_id, losers = _most_recently_updated(records, "email")
    return SurvivorshipDecision(
        field="canonical_email",
        winning_value=value,
        winning_record_id=winner_id,
        losing_record_ids=losers,
        rule_applied="single_source_most_recently_updated",
        rationale=(
            "DATA_MODEL.md priority CRM>Olist>Marketing collapses to a single source "
            "(CRM-only dataset); tie-broken by most recent updated_at, preferring a non-null value."
        ),
    )


def survive_canonical_phone(records: list[pd.Series]) -> SurvivorshipDecision:
    """DATA_MODEL.md §4: CRM > Support > Olist priority (single-source
    fallback: most-recently-updated non-null value wins)."""
    value, winner_id, losers = _most_recently_updated(records, "phone")
    return SurvivorshipDecision(
        field="canonical_phone",
        winning_value=value,
        winning_record_id=winner_id,
        losing_record_ids=losers,
        rule_applied="single_source_most_recently_updated",
        rationale=(
            "DATA_MODEL.md priority CRM>Support>Olist collapses to a single source "
            "(CRM-only dataset); tie-broken by most recent updated_at, preferring a non-null value."
        ),
    )


def _is_abbreviated(name: str) -> bool:
    """Heuristic for 'truncated/abbreviated variant', e.g. 'Caleb J. Silva' (the "J." token).

    `len(tok) <= 3` was a real false-positive bug (code-review pass): it also matches legitimate
    3-character name suffixes like "Jr." / "Sr." — so a complete name such as "Carlos Silva Jr."
    got excluded from the survivorship candidate pool in favor of a genuinely truncated variant
    like "Carlos S", the exact opposite of this rule's intent. A single-letter initial + period
    ("J.", "A.") is 2 characters; tightening the threshold to `<= 2` catches real abbreviations
    without matching common suffixes.
    """
    return any(tok.endswith(".") and len(tok) <= 2 for tok in str(name).split())


def survive_canonical_name(records: list[pd.Series]) -> SurvivorshipDecision:
    """DATA_MODEL.md §4: longest non-truncated value, title-cased."""
    candidates = [(r["crm_customer_id"], str(r.get("name") or "")) for r in records]
    candidates = [c for c in candidates if c[1].strip()]
    if not candidates:
        winner_id = records[0]["crm_customer_id"]
        losers = [r["crm_customer_id"] for r in records[1:]]
        return SurvivorshipDecision("canonical_name", None, winner_id, losers, "no_non_null_value", "All member records had a null/empty name.")

    non_abbreviated = [c for c in candidates if not _is_abbreviated(c[1])]
    pool = non_abbreviated or candidates
    winner_id, winner_name = max(pool, key=lambda c: len(c[1]))
    losers = [r["crm_customer_id"] for r in records if r["crm_customer_id"] != winner_id]
    return SurvivorshipDecision(
        field="canonical_name",
        winning_value=winner_name.title(),
        winning_record_id=winner_id,
        losing_record_ids=losers,
        rule_applied="longest_non_truncated_title_cased",
        rationale="DATA_MODEL.md §4: longest non-abbreviated value avoids picking an abbreviated variant.",
    )


def _survive_location_field(records: list[pd.Series], field: str) -> SurvivorshipDecision:
    """DATA_MODEL.md §4: city/state -- most recent updated_at (address changes over time)."""
    value, winner_id, losers = _most_recently_updated(records, field)
    return SurvivorshipDecision(
        field=field,
        winning_value=value,
        winning_record_id=winner_id,
        losing_record_ids=losers,
        rule_applied="most_recently_updated",
        rationale="DATA_MODEL.md §4: address changes over time, so the most recently updated record wins.",
    )


def survive_city(records: list[pd.Series]) -> SurvivorshipDecision:
    return _survive_location_field(records, "city")


def survive_state(records: list[pd.Series]) -> SurvivorshipDecision:
    return _survive_location_field(records, "state")


# Field -> rule function, in the order the golden record is assembled.
SURVIVORSHIP_RULES: dict[str, Callable[[list[pd.Series]], SurvivorshipDecision]] = {
    "canonical_name": survive_canonical_name,
    "canonical_email": survive_canonical_email,
    "canonical_phone": survive_canonical_phone,
    "city": survive_city,
    "state": survive_state,
}
