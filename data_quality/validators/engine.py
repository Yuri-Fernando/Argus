"""Self-contained pandas-based Data Quality rule engine.

Primary path: pure pandas, no external dependency required at runtime. This
intentionally does NOT hard-depend on Great Expectations for the core
validation path — GX (or the GX Core suites described in data_quality/README.md)
remains a documented, optional alternative engine that could implement the
same `Rule` contract later without changing `expectations/` or
`lakehouse/run_pipeline.py`.

10 rule types implemented, matching data_quality/README.md's catalog:
    not_null, unique, valid_email, valid_phone, valid_date,
    referential_integrity, range_check, duplicate_rate, schema_check, freshness

Row-level rules (not_null, unique, valid_email, valid_phone, valid_date,
referential_integrity, range_check) produce a per-row pass/fail mask. Rows
failing a rule marked `severity="hard"` are quarantined by the caller
(`lakehouse/run_pipeline.py`) instead of being written to Silver.

Table-level rules (duplicate_rate, schema_check, freshness) evaluate the
whole table and never quarantine individual rows, but still count toward
the table's DQ score.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Literal

import pandas as pd

RuleType = Literal[
    "not_null", "unique", "valid_email", "valid_phone", "valid_date",
    "referential_integrity", "range_check", "duplicate_rate", "schema_check", "freshness",
]
Severity = Literal["hard", "soft"]

ROW_LEVEL_TYPES = {
    "not_null", "unique", "valid_email", "valid_phone", "valid_date",
    "referential_integrity", "range_check",
}
TABLE_LEVEL_TYPES = {"duplicate_rate", "schema_check", "freshness"}

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


@dataclass
class Rule:
    type: RuleType
    column: str | None = None
    severity: Severity = "hard"
    description: str = ""
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleResult:
    rule: Rule
    total_rows: int
    failed_count: int
    pass_rate: float
    score: float
    detail: str
    fail_mask: pd.Series | None = None  # row-level only

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.rule.type,
            "column": self.rule.column,
            "severity": self.rule.severity,
            "description": self.rule.description,
            "total_rows": self.total_rows,
            "failed_count": self.failed_count,
            "pass_rate": round(self.pass_rate, 4),
            "score": round(self.score, 4),
            "detail": self.detail,
        }


@dataclass
class TableReport:
    table_name: str
    total_rows: int
    rule_results: list[RuleResult]
    score: float
    quarantined_count: int
    quarantine_mask: pd.Series

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_name": self.table_name,
            "total_rows": self.total_rows,
            "score": round(self.score, 4),
            "quarantined_count": self.quarantined_count,
            "quarantine_rate": round(self.quarantined_count / self.total_rows, 4) if self.total_rows else 0.0,
            "rules": [r.to_dict() for r in self.rule_results],
        }


def _empty_mask(df: pd.DataFrame) -> pd.Series:
    return pd.Series(False, index=df.index)


def _eval_not_null(df: pd.DataFrame, rule: Rule) -> RuleResult:
    col = df[rule.column]
    fail_mask = col.isna() | (col.astype("string").str.strip() == "")
    return _row_level_result(df, rule, fail_mask, detail=f"{fail_mask.sum()} null/blank values in '{rule.column}'")


def _eval_unique(df: pd.DataFrame, rule: Rule) -> RuleResult:
    col = df[rule.column]
    fail_mask = col.duplicated(keep=False) & col.notna()
    return _row_level_result(df, rule, fail_mask, detail=f"{fail_mask.sum()} rows share a duplicated '{rule.column}'")


def _eval_valid_email(df: pd.DataFrame, rule: Rule) -> RuleResult:
    col = df[rule.column].astype("string")
    non_null = col.notna() & (col.str.strip() != "")
    valid = col.str.match(EMAIL_RE, na=False)
    fail_mask = non_null & ~valid
    return _row_level_result(df, rule, fail_mask, detail=f"{fail_mask.sum()} malformed non-null emails in '{rule.column}'")


def _eval_valid_phone(df: pd.DataFrame, rule: Rule) -> RuleResult:
    min_digits = rule.params.get("min_digits", 10)
    max_digits = rule.params.get("max_digits", 13)
    col = df[rule.column].astype("string")
    non_null = col.notna() & (col.str.strip() != "")
    digits = col.str.replace(r"\D", "", regex=True)
    length_ok = digits.str.len().between(min_digits, max_digits)
    fail_mask = non_null & ~length_ok.fillna(False)
    return _row_level_result(
        df, rule, fail_mask,
        detail=f"{fail_mask.sum()} phones outside {min_digits}-{max_digits} digits in '{rule.column}'",
    )


def _eval_valid_date(df: pd.DataFrame, rule: Rule) -> RuleResult:
    col = df[rule.column]
    parsed = pd.to_datetime(col, errors="coerce")
    non_null_original = col.notna() if not pd.api.types.is_string_dtype(col) else col.astype("string").str.strip().ne("")
    fail_mask = non_null_original & parsed.isna()
    min_date, max_date = rule.params.get("min_date"), rule.params.get("max_date")
    if min_date is not None:
        fail_mask = fail_mask | (parsed.notna() & (parsed < pd.Timestamp(min_date)))
    if max_date is not None:
        fail_mask = fail_mask | (parsed.notna() & (parsed > pd.Timestamp(max_date)))
    return _row_level_result(df, rule, fail_mask.fillna(False), detail=f"{fail_mask.sum()} unparseable/out-of-range dates in '{rule.column}'")


def _eval_referential_integrity(df: pd.DataFrame, rule: Rule) -> RuleResult:
    ref_values: set = rule.params["ref_values"]
    col = df[rule.column].astype("string")
    non_null = col.notna()
    fail_mask = non_null & ~col.isin(ref_values)
    return _row_level_result(
        df, rule, fail_mask,
        detail=f"{fail_mask.sum()} '{rule.column}' values with no match in {rule.params.get('ref_table', 'reference table')}",
    )


def _eval_range_check(df: pd.DataFrame, rule: Rule) -> RuleResult:
    col = df[rule.column]
    fail_mask = _empty_mask(df)
    allowed_values = rule.params.get("allowed_values")
    if allowed_values is not None:
        non_null = col.notna()
        fail_mask = non_null & ~col.astype("string").str.upper().isin({str(v).upper() for v in allowed_values})
    else:
        numeric = pd.to_numeric(col, errors="coerce")
        min_v, max_v = rule.params.get("min"), rule.params.get("max")
        non_null = col.notna()
        if min_v is not None:
            fail_mask = fail_mask | (non_null & (numeric < min_v))
        if max_v is not None:
            fail_mask = fail_mask | (non_null & (numeric > max_v))
    return _row_level_result(df, rule, fail_mask.fillna(False), detail=f"{fail_mask.sum()} rows outside allowed range/set for '{rule.column}'")


def _row_level_result(df: pd.DataFrame, rule: Rule, fail_mask: pd.Series, detail: str) -> RuleResult:
    total = len(df)
    failed = int(fail_mask.sum())
    pass_rate = 1.0 if total == 0 else 1 - failed / total
    return RuleResult(rule=rule, total_rows=total, failed_count=failed, pass_rate=pass_rate, score=pass_rate, detail=detail, fail_mask=fail_mask)


def _eval_duplicate_rate(df: pd.DataFrame, rule: Rule) -> RuleResult:
    subset = rule.params.get("subset")
    threshold = rule.params.get("threshold", 0.0)
    total = len(df)
    dup_count = int(df.duplicated(subset=subset, keep="first").sum())
    rate = 0.0 if total == 0 else dup_count / total
    score = 1.0 if rate <= threshold else max(0.0, 1 - (rate - threshold) / max(threshold, 0.01))
    detail = f"duplicate rate {rate:.4f} (threshold {threshold:.4f}) on subset={subset}"
    return RuleResult(rule=rule, total_rows=total, failed_count=dup_count, pass_rate=1 - rate, score=score, detail=detail, fail_mask=None)


def _eval_schema_check(df: pd.DataFrame, rule: Rule) -> RuleResult:
    expected = rule.params.get("expected_columns", [])
    missing = [c for c in expected if c not in df.columns]
    score = 1.0 if not missing else 0.0
    detail = "schema OK" if not missing else f"missing expected columns: {missing}"
    return RuleResult(rule=rule, total_rows=len(df), failed_count=len(missing), pass_rate=score, score=score, detail=detail, fail_mask=None)


def _eval_freshness(df: pd.DataFrame, rule: Rule) -> RuleResult:
    max_age_days = rule.params.get("max_age_days", 90)
    col = pd.to_datetime(df[rule.column], errors="coerce")
    total = len(df)
    if col.notna().sum() == 0:
        return RuleResult(rule=rule, total_rows=total, failed_count=total, pass_rate=0.0, score=0.0, detail=f"no valid dates in '{rule.column}'", fail_mask=None)
    now = pd.Timestamp(datetime.now(timezone.utc)).tz_localize(None)
    most_recent = col.max()
    age_days = (now - most_recent).days
    passed = age_days <= max_age_days
    score = 1.0 if passed else max(0.0, 1 - (age_days - max_age_days) / max_age_days)
    detail = f"most recent '{rule.column}' is {age_days}d old (threshold {max_age_days}d)"
    return RuleResult(rule=rule, total_rows=total, failed_count=0 if passed else total, pass_rate=score, score=score, detail=detail, fail_mask=None)


_EVALUATORS = {
    "not_null": _eval_not_null,
    "unique": _eval_unique,
    "valid_email": _eval_valid_email,
    "valid_phone": _eval_valid_phone,
    "valid_date": _eval_valid_date,
    "referential_integrity": _eval_referential_integrity,
    "range_check": _eval_range_check,
    "duplicate_rate": _eval_duplicate_rate,
    "schema_check": _eval_schema_check,
    "freshness": _eval_freshness,
}


class DQEngine:
    """Runs a list of `Rule`s against a DataFrame and produces a `TableReport`."""

    def validate(self, table_name: str, df: pd.DataFrame, rules: Iterable[Rule]) -> TableReport:
        results: list[RuleResult] = []
        hard_fail_mask = _empty_mask(df)

        for rule in rules:
            evaluator = _EVALUATORS[rule.type]
            result = evaluator(df, rule)
            results.append(result)
            if rule.type in ROW_LEVEL_TYPES and rule.severity == "hard" and result.fail_mask is not None:
                hard_fail_mask = hard_fail_mask | result.fail_mask

        table_score = sum(r.score for r in results) / len(results) if results else 1.0

        return TableReport(
            table_name=table_name,
            total_rows=len(df),
            rule_results=results,
            score=table_score,
            quarantined_count=int(hard_fail_mask.sum()),
            quarantine_mask=hard_fail_mask,
        )


def quarantine_reasons(report: TableReport) -> pd.Series:
    """Per-row, comma-joined list of hard-rule names that failed (index-aligned to quarantined rows)."""
    reasons = pd.Series([[] for _ in range(report.total_rows)], index=report.quarantine_mask.index, dtype=object)
    for result in report.rule_results:
        if result.rule.type in ROW_LEVEL_TYPES and result.rule.severity == "hard" and result.fail_mask is not None:
            label = f"{result.rule.type}:{result.rule.column}"
            for idx in result.fail_mask[result.fail_mask].index:
                reasons.at[idx].append(label)
    joined = reasons.apply(lambda lst: ", ".join(lst))
    return joined[report.quarantine_mask]
