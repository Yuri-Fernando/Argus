"""
Generates every synthetic dataset the platform needs: CRM, Marketing,
Support, Web Events, Finance, and the RAG policy documents. Deterministic
given the same --seed (see DATA_MODEL.md §5).

Usage:
    python data/synthetic/generate_all.py
    python data/synthetic/generate_all.py --profile cloud --seed 7
    python data/synthetic/generate_all.py --only crm,web

Output layout:
    data/synthetic/crm/crm_customers.csv
    data/synthetic/crm/crm_customers_ground_truth.csv   # MDM benchmark labels
    data/synthetic/marketing/campaigns.csv
    data/synthetic/marketing/campaign_interactions.csv
    data/synthetic/support/support_tickets.csv
    data/synthetic/web/web_events.csv
    data/synthetic/finance/customer_payments.csv
    data/synthetic/fiscal/fiscal_documents.csv
    data/synthetic/fiscal/fiscal_documents_ground_truth.csv
    data/documents/*.md  (+ *.pdf if reportlab is installed, see render.py)
    data/documents/fiscal/*.png  (scanned fiscal docs for the VLM demo, if Pillow is installed)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from generators import crm, documents, finance, fiscal, marketing, support, web  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).parent / "config.yaml"

ALL_SOURCES = ["crm", "marketing", "support", "web", "finance", "fiscal", "documents"]


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=None, help="Override config.yaml seed")
    parser.add_argument("--profile", choices=["local", "cloud"], default="local")
    parser.add_argument(
        "--only",
        default=",".join(ALL_SOURCES),
        help=f"Comma-separated subset of sources to generate. Choices: {ALL_SOURCES}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()
    seed = args.seed if args.seed is not None else config["seed"]
    volumes = config["profiles"][args.profile]
    sources = set(s.strip() for s in args.only.split(","))
    out_dir = REPO_ROOT / config["output_dir"]

    print(f"Generating synthetic data | profile={args.profile} seed={seed} sources={sorted(sources)}")
    t0 = time.time()

    customer_ids: list[str] = []

    if "crm" in sources:
        print("-> crm ...")
        dirty = crm.DirtyRates(**config["dirty_rates"])
        crm_df, ground_truth_df = crm.generate(volumes["customers"], seed, dirty)
        crm_dir = out_dir / "crm"
        crm_dir.mkdir(parents=True, exist_ok=True)
        crm_df.to_csv(crm_dir / "crm_customers.csv", index=False)
        ground_truth_df.to_csv(crm_dir / "crm_customers_ground_truth.csv", index=False)
        customer_ids = crm_df["crm_customer_id"].tolist()
        print(f"   {len(crm_df)} customers ({len(ground_truth_df)} deliberate duplicates)")

    if not customer_ids:
        # allow running e.g. --only web without having generated crm this run,
        # by reusing a previously generated file if present.
        existing = out_dir / "crm" / "crm_customers.csv"
        if existing.exists():
            import pandas as pd

            customer_ids = pd.read_csv(existing)["crm_customer_id"].tolist()
        else:
            customer_ids = [f"CRM{i:08d}" for i in range(1000)]

    if "marketing" in sources:
        print("-> marketing ...")
        mkt_cfg = config["campaigns"]
        campaigns_df, interactions_df = marketing.generate(
            customer_ids, volumes["marketing_interactions"], seed, mkt_cfg["count"], mkt_cfg["channels"]
        )
        mkt_dir = out_dir / "marketing"
        mkt_dir.mkdir(parents=True, exist_ok=True)
        campaigns_df.to_csv(mkt_dir / "campaigns.csv", index=False)
        interactions_df.to_csv(mkt_dir / "campaign_interactions.csv", index=False)
        print(f"   {len(campaigns_df)} campaigns, {len(interactions_df)} interactions")

    if "support" in sources:
        print("-> support ...")
        sup_cfg = config["support"]
        support_df = support.generate(
            customer_ids, volumes["support_tickets"], seed,
            sup_cfg["categories"], sup_cfg["priorities"], sup_cfg["sentiments"],
        )
        sup_dir = out_dir / "support"
        sup_dir.mkdir(parents=True, exist_ok=True)
        support_df.to_csv(sup_dir / "support_tickets.csv", index=False)
        print(f"   {len(support_df)} tickets")

    if "web" in sources:
        print("-> web (streamed to disk in chunks) ...")
        web_cfg = config["web"]
        web_dir = out_dir / "web"
        web.generate_to_csv(
            web_dir / "web_events.csv", customer_ids, volumes["web_events"], seed,
            web_cfg["event_types"], web_cfg["devices"], web_cfg["sources"],
        )
        print(f"   {volumes['web_events']} events")

    if "finance" in sources:
        print("-> finance ...")
        finance_df = finance.generate(customer_ids, volumes["customers"], seed)
        fin_dir = out_dir / "finance"
        fin_dir.mkdir(parents=True, exist_ok=True)
        finance_df.to_csv(fin_dir / "customer_payments.csv", index=False)
        print(f"   {len(finance_df)} payment records")

    if "fiscal" in sources:
        print("-> fiscal ...")
        fiscal_cfg = config["fiscal"]
        dirty = fiscal.FiscalDirtyRates(**config["dirty_rates_fiscal"])
        fiscal_df, fiscal_ground_truth_df = fiscal.generate(customer_ids, fiscal_cfg["count"], seed, dirty)
        fiscal_dir = out_dir / "fiscal"
        fiscal_dir.mkdir(parents=True, exist_ok=True)
        fiscal_df.to_csv(fiscal_dir / "fiscal_documents.csv", index=False)
        fiscal_ground_truth_df.to_csv(fiscal_dir / "fiscal_documents_ground_truth.csv", index=False)
        n_dirty = (fiscal_ground_truth_df["discrepancy_reason"] != "none").sum()
        print(f"   {len(fiscal_df)} fiscal documents ({n_dirty} with an injected discrepancy)")

        scanned = fiscal.render_scanned_documents(
            fiscal_df, REPO_ROOT / "data" / "documents" / "fiscal", fiscal_cfg["scanned_sample"], seed
        )
        if scanned:
            print(f"   {len(scanned)} scanned PNGs rendered to data/documents/fiscal/ (VLM demo input)")

    if "documents" in sources:
        print("-> documents ...")
        written = documents.generate(REPO_ROOT / "data" / "documents")
        print(f"   {len(written)} policy documents (.md; run data/documents/render.py for PDF)")

    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s. Output under {out_dir}")


if __name__ == "__main__":
    main()
