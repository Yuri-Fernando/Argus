"""
Scans every `.csv`/`.md` file under `data/synthetic/` and `data/documents/`
for patterns that resemble real PII: a formatted or raw Brazilian CPF, or an
email address using a domain outside the allowlist of Faker's own "safe"
email domains. This makes the LGPD guarantee in ARCHITECTURE.md §16 — "no
real CPF/email/phone anywhere" — a verifiable gate instead of a claim in a
docstring, and is the first test `pytest` runs per ROADMAP.md Sprint 0's
acceptance criteria.

Skips gracefully (not a failure) when neither directory has any generated
files yet, so a fresh clone that hasn't run `make seed` is never punished
by this gate — see ROADMAP.md Sprint 0: "fresh clone -> `make install &&
make up && make seed && make test` succeeds with zero manual steps."
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = [REPO_ROOT / "data" / "synthetic", REPO_ROOT / "data" / "documents"]

# Formatted Brazilian CPF: 000.000.000-00
CPF_FORMATTED_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")

# Raw 11-digit CPF, checked ONLY inside columns whose header looks
# document/CPF-like — an unqualified 11-digit check would false-positive on
# things like malformed phone numbers or long numeric IDs that have nothing
# to do with a document number (see crm.py's `invalid_phone` dirty-rate,
# which deliberately produces short digit-only strings, not 11-digit ones).
CPF_RAW_RE = re.compile(r"^\d{11}$")
DOCUMENT_COLUMN_HINTS = ("document", "cpf", "cnpj", "tax_id", "ssn")

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@([a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+)")

# data/synthetic/generators/crm.py generates emails via Faker's `email()`,
# which — for the Faker version pinned in pyproject.toml — is safe-by-default
# and only ever emits these RFC 2606 reserved example domains. Any other
# domain showing up in a "synthetic" dataset is suspicious enough to fail
# the build: it could mean a generator regression, a real sample row pasted
# in by mistake, or a Faker upgrade that silently stopped using
# `safe_email()` under the hood.
ALLOWED_EMAIL_DOMAINS = {"example.com", "example.net", "example.org", "test.com", "synthetic.local"}

MAX_REPORTED_VIOLATIONS = 50


def _iter_target_files() -> list[Path]:
    files: list[Path] = []
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        files.extend(base.rglob("*.csv"))
        files.extend(base.rglob("*.md"))
    return files


def _check_email_domain(value: str) -> list[str]:
    problems = []
    for match in EMAIL_RE.finditer(value):
        domain = match.group(1).lower()
        if domain not in ALLOWED_EMAIL_DOMAINS:
            problems.append(f"email domain '{domain}' not in the synthetic-data allowlist {sorted(ALLOWED_EMAIL_DOMAINS)}")
    return problems


def _scan_csv(path: Path) -> list[str]:
    violations: list[str] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return violations
        doc_columns = {c for c in reader.fieldnames if any(hint in c.lower() for hint in DOCUMENT_COLUMN_HINTS)}

        for line_num, row in enumerate(reader, start=2):  # header occupies line 1
            for col, value in row.items():
                if not value:
                    continue
                if CPF_FORMATTED_RE.search(value):
                    violations.append(f"{path}:{line_num} col={col} — formatted CPF-like pattern found")
                if col in doc_columns and CPF_RAW_RE.match(value.strip()):
                    violations.append(f"{path}:{line_num} col={col} — raw 11-digit value in a document-like column")
                for problem in _check_email_domain(value):
                    violations.append(f"{path}:{line_num} col={col} — {problem}")
    return violations


def _scan_markdown(path: Path) -> list[str]:
    violations: list[str] = []
    text = path.read_text(encoding="utf-8")

    for match in CPF_FORMATTED_RE.finditer(text):
        line_num = text.count("\n", 0, match.start()) + 1
        violations.append(f"{path}:{line_num} — formatted CPF-like pattern found")

    for match in EMAIL_RE.finditer(text):
        domain = match.group(1).lower()
        if domain not in ALLOWED_EMAIL_DOMAINS:
            line_num = text.count("\n", 0, match.start()) + 1
            violations.append(
                f"{path}:{line_num} — email domain '{domain}' not in the synthetic-data allowlist {sorted(ALLOWED_EMAIL_DOMAINS)}"
            )
    return violations


def test_no_real_pii_in_generated_data():
    """LGPD gate: no real-looking CPF or non-allowlisted email domain
    anywhere under data/synthetic/ or data/documents/."""
    files = _iter_target_files()
    if not files:
        pytest.skip(
            "No files found under data/synthetic/ or data/documents/ — run "
            "`make seed` to generate synthetic data before this test has "
            "anything to scan. This is a skip, not a failure: a fresh clone "
            "that hasn't seeded data yet should not be punished by this gate."
        )

    all_violations: list[str] = []
    for path in files:
        if path.suffix == ".csv":
            all_violations.extend(_scan_csv(path))
        elif path.suffix == ".md":
            all_violations.extend(_scan_markdown(path))

    assert not all_violations, (
        f"Found {len(all_violations)} possible real-PII pattern(s) in synthetic data "
        f"(showing up to {MAX_REPORTED_VIOLATIONS}):\n"
        + "\n".join(all_violations[:MAX_REPORTED_VIOLATIONS])
        + ("\n... (truncated)" if len(all_violations) > MAX_REPORTED_VIOLATIONS else "")
    )
