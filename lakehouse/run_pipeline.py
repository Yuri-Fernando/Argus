"""Single entrypoint: Bronze -> Silver -> Data Quality (validate + quarantine).

Usage:
    /c/Users/Yuri_/AppData/Local/Programs/Python/Python310/python.exe lakehouse/run_pipeline.py

Steps:
  1. Bronze: read every available raw/synthetic source, cast dtypes, stamp
     `_ingested_at`, write Parquet (lakehouse/bronze/*). Olist is skipped
     with a warning if data/raw/olist is absent.
  2. Silver: dedup/cast/standardize each Bronze table into a *candidate*
     Silver DataFrame (lakehouse/silver/*) — not yet written to disk.
  3. Data Quality: data_quality/validators/engine.DQEngine runs the rule
     catalog (data_quality/expectations/*) against each candidate table.
     Rows failing a HARD rule are written to data/lakehouse/quarantine/;
     everything else is written to data/lakehouse/silver/. crm_customer is
     processed first so its passing IDs become the referential-integrity
     reference set for the other tables.
  4. Reports: data_quality/reports/dq_report.json + dq_report.md, and a
     per-table + overall DQ score table printed to stdout.
"""
from __future__ import annotations

import logging

from lakehouse import bronze, silver
from lakehouse.bronze.olist import is_available as olist_available
from lakehouse.silver.common import write_silver_parquet
from data_quality.expectations import get_rules_for_table
from data_quality.validators.engine import DQEngine, TableReport, quarantine_reasons
from data_quality.validators.quarantine import write_quarantine
from data_quality.validators.report import write_reports

logger = logging.getLogger("lakehouse.run_pipeline")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# crm_customer MUST run first — its passing IDs feed referential_integrity
# checks on every other table.
TABLE_ORDER = ["crm_customer", "support_ticket", "web_event", "campaign_interaction", "payment_finance"]


def run() -> list[TableReport]:
    logger.info("=== STEP 1/3: Bronze ===")
    bronze_tables = bronze.run_all()

    logger.info("=== STEP 2/3: Silver (candidate build) ===")
    candidates = silver.build_all(bronze_tables)

    logger.info("=== STEP 3/3: Data Quality (validate, quarantine, write final Silver) ===")
    engine = DQEngine()
    reports: list[TableReport] = []
    validated_silver: dict[str, "pd.DataFrame"] = {}  # noqa: F821 - only used for typing hint clarity

    for table_name in TABLE_ORDER:
        if table_name not in candidates:
            logger.warning("Skipping DQ for %s — no candidate Silver table built", table_name)
            continue
        df = candidates[table_name]
        rules = get_rules_for_table(table_name, validated_silver)
        report = engine.validate(table_name, df, rules)
        reports.append(report)

        quarantined_df = df[report.quarantine_mask]
        passing_df = df[~report.quarantine_mask]

        if not quarantined_df.empty:
            reasons = quarantine_reasons(report)
            write_quarantine(quarantined_df, table_name, reasons=reasons)

        write_silver_parquet(passing_df, table_name)
        validated_silver[table_name] = passing_df

        logger.info(
            "DQ[%s]: score=%.2f%% rows=%d quarantined=%d",
            table_name, report.score * 100, report.total_rows, report.quarantined_count,
        )

    json_path, md_path = write_reports(reports, olist_skipped=not olist_available())
    logger.info("DQ reports written: %s | %s", json_path, md_path)

    _print_score_table(reports)
    return reports


def _print_score_table(reports: list[TableReport]) -> None:
    overall = sum(r.score for r in reports) / len(reports) if reports else 0.0
    print("\n" + "=" * 72)
    print("DATA QUALITY SCORE SUMMARY")
    print("=" * 72)
    print(f"{'Table':<22}{'Rows':>10}{'Score':>10}{'Quarantined':>14}{'Q-Rate':>10}")
    print("-" * 72)
    for r in reports:
        q_rate = (r.quarantined_count / r.total_rows * 100) if r.total_rows else 0.0
        print(f"{r.table_name:<22}{r.total_rows:>10}{r.score*100:>9.2f}%{r.quarantined_count:>14}{q_rate:>9.2f}%")
    print("-" * 72)
    print(f"{'OVERALL PLATFORM':<22}{'':>10}{overall*100:>9.2f}%")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    run()
