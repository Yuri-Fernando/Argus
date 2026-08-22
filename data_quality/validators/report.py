"""Generates data_quality/reports/dq_report.json and dq_report.md from TableReports."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from data_quality.validators.engine import TableReport

ROOT = Path(__file__).resolve().parents[2]
REPORTS_ROOT = ROOT / "data_quality" / "reports"


def _overall_score(table_reports: list[TableReport]) -> float:
    if not table_reports:
        return 0.0
    return sum(t.score for t in table_reports) / len(table_reports)


def write_reports(table_reports: list[TableReport], olist_skipped: bool = True) -> tuple[Path, Path]:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    overall_score = _overall_score(table_reports)

    payload = {
        "generated_at": generated_at,
        "overall_score": round(overall_score, 4),
        "overall_score_pct": round(overall_score * 100, 2),
        "tables": [t.to_dict() for t in table_reports],
        "notes": {
            "olist_skipped": olist_skipped,
            "reason": "data/raw/olist absent in this environment — Olist-derived tables intentionally excluded",
        },
    }
    json_path = REPORTS_ROOT / "dq_report.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md_lines = [
        "# Data Quality Report",
        "",
        f"Generated: {generated_at}",
        "",
        f"## Overall Platform DQ Score: {overall_score * 100:.2f}%",
        "",
        "| Table | Rows | Score | Quarantined | Quarantine Rate |",
        "|---|---:|---:|---:|---:|",
    ]
    for t in table_reports:
        d = t.to_dict()
        md_lines.append(
            f"| {d['table_name']} | {d['total_rows']} | {d['score']*100:.2f}% | "
            f"{d['quarantined_count']} | {d['quarantine_rate']*100:.2f}% |"
        )

    md_lines.append("")
    if olist_skipped:
        md_lines.append("> Olist-derived tables skipped: `data/raw/olist` is absent in this environment.")
        md_lines.append("")

    for t in table_reports:
        md_lines.append(f"## {t.table_name}")
        md_lines.append("")
        md_lines.append("| Rule | Column | Severity | Score | Failed | Detail |")
        md_lines.append("|---|---|---|---:|---:|---|")
        for r in t.rule_results:
            rd = r.to_dict()
            md_lines.append(
                f"| {rd['type']} | {rd['column'] or '-'} | {rd['severity']} | {rd['score']*100:.2f}% | "
                f"{rd['failed_count']} | {rd['detail']} |"
            )
        md_lines.append("")

    md_path = REPORTS_ROOT / "dq_report.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    return json_path, md_path
