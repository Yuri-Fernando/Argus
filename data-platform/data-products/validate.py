"""Validador de contratos de Data Product (RFC-001 — Data Mesh).

Roda no CI: garante que todo `data-products/*/contract.yaml` declara os
campos obrigatórios de um contrato (owner, SLA, schema, quality rules,
lineage, política de acesso) e que os tipos/valores são coerentes.

    python data-platform/data-products/validate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

CONTRACTS_DIR = Path(__file__).parent
REQUIRED_TOP = {"name", "domain", "owner", "version", "output_ports", "sla", "schema",
                "quality_rules", "lineage", "access_policy"}
REQUIRED_SLA = {"freshness", "availability"}
ALLOWED_COLUMN_TYPES = {"string", "integer", "double", "boolean", "timestamp", "date"}
ALLOWED_CLASSIFICATION = {"public", "internal", "confidential", "restricted"}


def validate_contract(path: Path) -> list[str]:
    errors: list[str] = []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    missing = REQUIRED_TOP - set(data)
    if missing:
        errors.append(f"campos obrigatórios ausentes: {sorted(missing)}")
        return errors  # sem esses campos não dá pra validar o resto

    if data["name"] != path.parent.name:
        errors.append(f"name '{data['name']}' != nome da pasta '{path.parent.name}'")

    if not REQUIRED_SLA <= set(data["sla"]):
        errors.append(f"sla precisa de {sorted(REQUIRED_SLA)}")

    schema_cols = set()
    for col in data["schema"]:
        if "name" not in col or "type" not in col:
            errors.append(f"coluna sem name/type: {col}")
            continue
        schema_cols.add(col["name"])
        if col["type"] not in ALLOWED_COLUMN_TYPES:
            errors.append(f"tipo inválido em {col['name']}: {col['type']}")

    for rule in data["quality_rules"]:
        for c in rule.get("columns", []):
            if c not in schema_cols:
                errors.append(f"quality rule referencia coluna inexistente: {c}")
        if "column" in rule and rule["column"] not in schema_cols:
            errors.append(f"quality rule referencia coluna inexistente: {rule['column']}")

    cls = data["access_policy"].get("classification")
    if cls not in ALLOWED_CLASSIFICATION:
        errors.append(f"classification inválida: {cls}")
    for masked in data["access_policy"].get("masking", []):
        if masked not in schema_cols:
            errors.append(f"masking referencia coluna inexistente: {masked}")

    if not data["lineage"].get("upstream"):
        errors.append("lineage.upstream vazio")

    return errors


def validate_all() -> dict[str, list[str]]:
    results = {}
    for contract in sorted(CONTRACTS_DIR.glob("*/contract.yaml")):
        results[contract.parent.name] = validate_contract(contract)
    return results


def main() -> int:
    results = validate_all()
    ok = True
    for name, errors in results.items():
        if errors:
            ok = False
            print(f"[FAIL] {name}")
            for e in errors:
                print(f"       - {e}")
        else:
            print(f"[ok]   {name}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
