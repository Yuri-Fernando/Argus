"""DQ rule catalog for the synthetic `fiscal_document` dataset (ADR-015).

Not part of `lakehouse/run_pipeline.py::TABLE_ORDER` — the fiscal domain is a self-contained
bolt-on extension (`data/synthetic/generators/fiscal.py`), not another e-commerce Bronze/Silver
table, so it gets its own small runner (`data_quality/validators/fiscal_report.py`) instead of
being wired into the CRM/support/web/campaign/finance pipeline family. It still reuses the exact
same `DQEngine` and the same 10 closed `RuleType`s — see `data_quality/validators/engine.py`,
never a new rule type.

Every rule below traces to one of the three deliberately-injected flaws in
`data/synthetic/generators/fiscal.py::FiscalDirtyRates`:

- `invalid_ncm` -> `range_check(allowed_values=...)` on `ncm_code`.
- `cst_cfop_mismatch` -> `range_check(allowed_values=[True])` on the derived `cst_cfop_valid`
  column (see `fiscal.py::_cst_cfop_valid()`'s docstring for why this is a `range_check`, not a
  new cross-column rule type).
- `rate_out_of_range` -> `range_check(min=0, max=1)` on each of the three rate columns.
"""
from __future__ import annotations

from data_quality.validators.engine import Rule

# Mirrors data/synthetic/generators/fiscal.py::VALID_NCM_CODES. Inlined rather than imported —
# `data/` has no `__init__.py` (it's a script directory, not an importable package; see
# data/synthetic/generate_all.py's sys.path.insert trick), and this matches the existing pattern
# in this same directory: payment_finance.py's schema_check `expected_columns` are inline
# literals mirroring finance.py's output, never imported from the generator either.
VALID_NCM_CODES = [
    "85171231",  # Eletrônicos
    "61091000",  # Vestuário
    "07019000",  # Alimentos in natura
    "22030000",  # Bebida alcoólica
    "24022000",  # Cigarros
    "22021000",  # Refrigerante açucarado
    "94036000",  # Móveis
    "33049900",  # Cosméticos
]


def get_rules(crm_customer_ids: set | None = None) -> list[Rule]:
    rules = [
        Rule(
            "schema_check", severity="hard", description="Expected fiscal_document columns present",
            params={"expected_columns": [
                "fiscal_document_id", "crm_customer_id", "issue_date", "product_category",
                "ncm_code", "cfop_code", "cst_code", "cst_cfop_valid", "item_value",
                "ibs_rate", "cbs_rate", "imposto_seletivo_rate", "calculated_tax_total",
            ]},
        ),
        Rule("not_null", column="fiscal_document_id", severity="hard", description="Primary key must be present"),
        Rule("unique", column="fiscal_document_id", severity="hard", description="Primary key must be unique"),
        Rule("not_null", column="ncm_code", severity="hard", description="NCM code must be present"),
        Rule("not_null", column="cfop_code", severity="hard", description="CFOP code must be present"),
        Rule("not_null", column="cst_code", severity="hard", description="CST code must be present"),
        Rule(
            "range_check", column="ncm_code", severity="hard",
            description="NCM code must be in the platform's (synthetic) product catalog — an out-of-catalog "
                         "code means the item was misclassified upstream (fiscal.py's invalid_ncm injection)",
            params={"allowed_values": VALID_NCM_CODES},
        ),
        Rule(
            "range_check", column="cst_cfop_valid", severity="hard",
            description="cst_cfop_valid must be True — an exempt/immune CST paired with a normal taxed-sale "
                         "CFOP is a logically inconsistent combination (fiscal.py's cst_cfop_mismatch injection); "
                         "materialized as its own boolean column since DQEngine's 10 rule types are single-column",
            params={"allowed_values": [True]},
        ),
        Rule(
            "range_check", column="ibs_rate", severity="hard",
            description="IBS rate must be within [0, 1] — a negative/>100% rate is a data-entry sign-flip bug "
                         "(fiscal.py's rate_out_of_range injection)",
            params={"min": 0, "max": 1},
        ),
        Rule(
            "range_check", column="cbs_rate", severity="hard",
            description="CBS rate must be within [0, 1] — same rationale as ibs_rate above",
            params={"min": 0, "max": 1},
        ),
        Rule(
            "range_check", column="imposto_seletivo_rate", severity="hard",
            description="Imposto Seletivo rate must be within [0, 1] — same rationale as ibs_rate above",
            params={"min": 0, "max": 1},
        ),
        Rule(
            "range_check", column="item_value", severity="hard",
            description="item_value must be non-negative", params={"min": 0},
        ),
        Rule(
            "duplicate_rate", severity="soft",
            description="Structural exact-duplicate rate on fiscal_document_id",
            params={"subset": ["fiscal_document_id"], "threshold": 0.0},
        ),
    ]
    if crm_customer_ids:
        rules.append(
            Rule(
                "referential_integrity", column="crm_customer_id", severity="hard",
                description="crm_customer_id must exist in crm_customer",
                params={"ref_values": crm_customer_ids, "ref_table": "crm_customer"},
            )
        )
    return rules
