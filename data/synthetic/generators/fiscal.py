"""
Generates data/synthetic/fiscal/fiscal_documents.csv — synthetic Brazilian tax-reform-era invoice
line items (IBS/CBS/Imposto Seletivo), one per sampled crm_customer.

Built per docs/decisions/ADR-015-fiscal-tax-reform-extension.md, closing two gaps
IMPROVEMENTS_AND_RESEARCH.md §5.1/§5.3 documented and deliberately left open: (1) no
fiscal/tributário domain data despite `tributario.txt` asking for exactly that, and (2) no real
VLM use case in the platform, since a *scanned* fiscal document (`render_scanned_documents()`
below) is exactly the input `rag/local_stack/document_parser.py::DoclingVlmDocumentParser` needs
— one dataset closes both gaps instead of two unrelated ones.

HONEST SCOPE NOTE: the NCM/CFOP/CST codes and IBS/CBS/Imposto Seletivo rates below are
illustrative approximations of the Reforma Tributária (EC 132/2023, regulamentação em curso em
2026) — this module is not a certified tax-calculation engine, and `correct_tax_total` in the
ground truth file is this module's own reference formula (`_correct_tax()`), not an authoritative
government figure. The point of this dataset is to give the DQ/RAG/VLM/agent layers something
real and internally-consistent to validate against — same spirit as `crm.py`'s synthetic CPF
hashes never being asked to pass a real Receita Federal check.

Deliberately injects three fiscal data problems, same discipline as
`data/synthetic/generators/crm.py`'s `DirtyRates` — each row gets AT MOST one injected flaw, so
the root-cause label is always unambiguous for `agents/fiscal/tax_discrepancy_classifier.py`:

- `invalid_ncm`: the NCM code is replaced by one outside the (synthetic) product catalog —
  correct per `data_quality/expectations/fiscal_document.py`'s `range_check(allowed_values=...)`
  rule, not a tax-calculation error by itself.
- `cst_cfop_mismatch`: an exempt/immune CST (see `EXEMPT_CST_CODES`) is paired with a
  normal-taxed-sale CFOP, AND the document is (incorrectly) taxed as if it weren't exempt — a
  realistic "system charged tax despite the exemption" error. Caught by the `cst_cfop_valid`
  derived column (see `_cst_cfop_valid()`), not a new cross-column rule type — the DQ engine's 10
  rule types are all single-column, so the compatibility check is materialized as its own boolean
  column and validated with the existing `range_check(allowed_values=[True])`, exactly the same
  trick used for structural checks elsewhere in this codebase.
- `rate_out_of_range`: one of the three tax rates is set outside `[0, 1]` (e.g. a sign-flip
  data-entry bug), and the document's `calculated_tax_total` reflects that bad rate while the
  ground truth `correct_tax_total` uses the category's canonical rate instead.

Every row's true tax figure and (if dirty) the reason it diverges from the printed
`calculated_tax_total` is recorded in a companion `fiscal_documents_ground_truth.csv`
(`fiscal_document_id, correct_tax_total, discrepancy_amount, discrepancy_reason`) — same
"ground truth so precision/recall is measured, not eyeballed" discipline as `crm.py`'s MDM
duplicate labels. This is what `agents/fiscal/root_cause_agent.py` diagnoses against.
"""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from faker import Faker

# (category, ncm_code, is_selective_tax_eligible) — a small, clearly-synthetic product catalog.
# "Imposto Seletivo" (the reform's "sin tax") only applies to a subset of categories, per its
# stated purpose (goods harmful to health/environment) — modeled here as a boolean flag, not a
# claim about the real, still-being-regulated IS incidence list.
PRODUCT_CATALOG: list[tuple[str, str, bool]] = [
    ("Eletrônicos", "85171231", False),
    ("Vestuário", "61091000", False),
    ("Alimentos in natura", "07019000", False),
    ("Bebida alcoólica", "22030000", True),
    ("Cigarros", "24022000", True),
    ("Refrigerante açucarado", "22021000", True),
    ("Móveis", "94036000", False),
    ("Cosméticos", "33049900", False),
]
VALID_NCM_CODES = [ncm for _, ncm, _ in PRODUCT_CATALOG]

# Simplified, illustrative CFOP set for outbound sales operations (5xxx = same state,
# 6xxx = other state) — real CFOP tables have hundreds of codes; this is a representative subset.
CFOP_CATALOG = ["5102", "5405", "6102", "6108", "5949"]
# CFOPs that represent a normal (non-exempt) taxed sale — used by `_cst_cfop_valid()`.
TAXED_SALE_CFOPS = {"5102", "6102", "6108"}

# (cst_code, label) — illustrative CST set under the reform's IBS/CBS regime, not the complete
# official table (still being finalized in regulamentação as of this dataset's fictional present).
CST_CATALOG = [
    ("000", "Tributação integral"),
    ("200", "Imunidade"),
    ("400", "Isenção"),
    ("810", "Diferimento"),
    ("900", "Outros"),
]
VALID_CST_CODES = [c for c, _ in CST_CATALOG]
EXEMPT_CST_CODES = {"200", "400"}  # imunidade / isenção — correct tax is always 0 for these.

# Canonical (illustrative) rates by category — reused both to generate a clean row and, for a
# `rate_out_of_range` dirty row, as the "correct" rate the ground truth formula falls back to.
IBS_RATE = 0.177   # combined state+municipal reference rate (illustrative)
CBS_RATE = 0.088   # federal reference rate (illustrative)
IS_RATE_SELECTIVE = 0.20  # imposto seletivo, selective-tax-eligible categories only (illustrative)
IS_RATE_NONE = 0.0


@dataclass
class FiscalDirtyRates:
    invalid_ncm: float = 0.03
    cst_cfop_mismatch: float = 0.02
    rate_out_of_range: float = 0.01


def _cst_cfop_valid(cst_code: str, cfop_code: str) -> bool:
    """An exempt/immune CST paired with a normal taxed-sale CFOP is logically inconsistent — the
    CFOP says "this is a regular taxed sale" while the CST says "no tax is due on this operation".
    Materialized as its own column (see module docstring) so the DQ engine's existing
    `range_check(allowed_values=[True])` rule type can validate it without a new rule type."""
    if cst_code in EXEMPT_CST_CODES and cfop_code in TAXED_SALE_CFOPS:
        return False
    return True


def _correct_tax(item_value: float, ibs_rate: float, cbs_rate: float, is_rate: float, cst_code: str) -> float:
    """The reference tax figure a clean document should show — 0 for an exempt/immune CST
    regardless of the rate fields, otherwise the sum of the three reform taxes on `item_value`."""
    if cst_code in EXEMPT_CST_CODES:
        return 0.0
    return round(item_value * (ibs_rate + cbs_rate + is_rate), 2)


def generate(
    customer_ids: list[str], n: int, seed: int, dirty_rates: FiscalDirtyRates
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fake = Faker("pt_BR")
    Faker.seed(seed)
    rng = random.Random(seed)

    rows: list[dict] = []
    ground_truth: list[dict] = []

    for i in range(n):
        category, ncm_code, is_selective = rng.choice(PRODUCT_CATALOG)
        cst_code, _ = rng.choice(CST_CATALOG)
        # A clean (non-injected) row must always be a logically valid CST/CFOP combination — pick
        # the CFOP conditioned on the CST so `_cst_cfop_valid()` is true by construction here; the
        # `cst_cfop_mismatch` branch below is the only place that deliberately breaks it.
        if cst_code in EXEMPT_CST_CODES:
            cfop_code = rng.choice([c for c in CFOP_CATALOG if c not in TAXED_SALE_CFOPS])
        else:
            cfop_code = rng.choice(CFOP_CATALOG)
        item_value = round(rng.uniform(15, 4000), 2)
        ibs_rate, cbs_rate = IBS_RATE, CBS_RATE
        is_rate = IS_RATE_SELECTIVE if is_selective else IS_RATE_NONE

        # At most one injected flaw per row, so the root-cause label is always unambiguous.
        roll = rng.random()
        reason = "none"
        if roll < dirty_rates.invalid_ncm:
            reason = "invalid_ncm"
        elif roll < dirty_rates.invalid_ncm + dirty_rates.cst_cfop_mismatch:
            reason = "cst_cfop_mismatch"
        elif roll < dirty_rates.invalid_ncm + dirty_rates.cst_cfop_mismatch + dirty_rates.rate_out_of_range:
            reason = "rate_out_of_range"

        discrepancy_amount = 0.0

        if reason == "invalid_ncm":
            # Metadata-only flaw: the code is nonsense, the tax math itself stays consistent.
            ncm_code = "99999999"
            calculated_tax_total = _correct_tax(item_value, ibs_rate, cbs_rate, is_rate, cst_code)
            correct_tax_total = calculated_tax_total
        elif reason == "cst_cfop_mismatch":
            # Force an exempt CST onto a normal taxed-sale CFOP, and (the realistic error) charge
            # tax anyway — the document says "taxed", the CST says "exempt".
            cst_code = rng.choice(list(EXEMPT_CST_CODES))
            cfop_code = rng.choice(list(TAXED_SALE_CFOPS))
            calculated_tax_total = round(item_value * (ibs_rate + cbs_rate + is_rate), 2)
            correct_tax_total = _correct_tax(item_value, ibs_rate, cbs_rate, is_rate, cst_code)  # 0.0, exempt
            discrepancy_amount = round(calculated_tax_total - correct_tax_total, 2)
        elif reason == "rate_out_of_range":
            # A sign-flip-style data-entry bug on one of the three rates.
            bad_rate = round(-rng.uniform(0.01, 0.10), 4)
            which = rng.choice(["ibs_rate", "cbs_rate", "imposto_seletivo_rate"])
            correct_tax_total = _correct_tax(item_value, ibs_rate, cbs_rate, is_rate, cst_code)
            bad_ibs, bad_cbs, bad_is = ibs_rate, cbs_rate, is_rate
            if which == "ibs_rate":
                bad_ibs = bad_rate
            elif which == "cbs_rate":
                bad_cbs = bad_rate
            else:
                bad_is = bad_rate
            calculated_tax_total = round(item_value * (bad_ibs + bad_cbs + bad_is), 2)
            ibs_rate, cbs_rate, is_rate = bad_ibs, bad_cbs, bad_is
            discrepancy_amount = round(calculated_tax_total - correct_tax_total, 2)
        else:
            calculated_tax_total = _correct_tax(item_value, ibs_rate, cbs_rate, is_rate, cst_code)
            correct_tax_total = calculated_tax_total

        fiscal_document_id = f"NFE{i:08d}"
        rows.append(
            {
                "fiscal_document_id": fiscal_document_id,
                "crm_customer_id": rng.choice(customer_ids),
                "issue_date": fake.date_time_between(start_date="-1y", end_date="now").isoformat(),
                "product_category": category,
                "ncm_code": ncm_code,
                "cfop_code": cfop_code,
                "cst_code": cst_code,
                "cst_cfop_valid": _cst_cfop_valid(cst_code, cfop_code),
                "item_value": item_value,
                "ibs_rate": ibs_rate,
                "cbs_rate": cbs_rate,
                "imposto_seletivo_rate": is_rate,
                "calculated_tax_total": calculated_tax_total,
            }
        )
        ground_truth.append(
            {
                "fiscal_document_id": fiscal_document_id,
                "correct_tax_total": correct_tax_total,
                "discrepancy_amount": discrepancy_amount,
                "discrepancy_reason": reason,
            }
        )

    return pd.DataFrame(rows), pd.DataFrame(ground_truth)


def render_scanned_documents(df: pd.DataFrame, out_dir: Path, sample_n: int, seed: int) -> list[Path]:
    """Render `sample_n` rows of `df` as a "scanned" invoice-style PNG each — the real input
    `DoclingVlmDocumentParser` (rag/local_stack/document_parser.py) parses, giving the VLM path an
    actual image to process instead of a hypothetical one.

    Optional and gracefully degrading, same pattern as `data/documents/render.py`'s `reportlab`
    fallback: if Pillow isn't installed, this prints a warning and returns an empty list rather
    than failing the whole synthetic-data generation run.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print(
            "Pillow is not installed — skipping scanned fiscal document rendering. The fiscal "
            "CSV/ground-truth files are already usable by data_quality/ and agents/fiscal/. Run "
            "`pip install -e .[genai-extra]` to also get the scanned PNGs for the VLM demo.",
            file=sys.stderr,
        )
        return []

    rng = random.Random(seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    sample = df.sample(n=min(sample_n, len(df)), random_state=seed)

    try:
        font_title = ImageFont.truetype("arial.ttf", 22)
        font_body = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    written: list[Path] = []
    for _, row in sample.iterrows():
        img = Image.new("RGB", (900, 500), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((30, 20), "NOTA FISCAL ELETRÔNICA (Reforma Tributária) — DOCUMENTO SINTÉTICO", fill="black", font=font_title)
        lines = [
            f"Documento: {row['fiscal_document_id']}",
            f"Cliente: {row['crm_customer_id']}",
            f"Data de emissão: {row['issue_date']}",
            f"Categoria do produto: {row['product_category']}",
            f"NCM: {row['ncm_code']}    CFOP: {row['cfop_code']}    CST: {row['cst_code']}",
            f"Valor do item: R$ {row['item_value']:.2f}",
            f"Alíquota IBS: {row['ibs_rate']:.2%}   Alíquota CBS: {row['cbs_rate']:.2%}   "
            f"Imposto Seletivo: {row['imposto_seletivo_rate']:.2%}",
            f"Total de tributos: R$ {row['calculated_tax_total']:.2f}",
        ]
        y = 90
        for line in lines:
            draw.text((30, y), line, fill="black", font=font_body)
            y += 40
        draw.text(
            (30, 460),
            "Documento sintético gerado para fins de portfólio — não representa uma NF-e real.",
            fill="gray",
            font=font_body,
        )

        # Light "scan" degradation: small rotation + per-pixel jitter, so the VLM path is
        # exercising something closer to a real scanned document than a pristine screenshot.
        angle = rng.uniform(-1.5, 1.5)
        img = img.rotate(angle, expand=True, fillcolor="white")
        pixels = img.load()
        w, h = img.size
        for _ in range(int(w * h * 0.01)):
            x, y = rng.randrange(w), rng.randrange(h)
            grey = rng.randint(150, 220)
            pixels[x, y] = (grey, grey, grey)

        path = out_dir / f"{row['fiscal_document_id']}_scan.png"
        img.save(path)
        written.append(path)

    return written
