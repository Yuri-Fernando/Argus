"""Testes do validador de contratos de Data Product (RFC-001)."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))

from validate import validate_all, validate_contract  # noqa: E402


def test_all_shipped_contracts_are_valid():
    results = validate_all()
    assert results, "nenhum contrato encontrado"
    for name, errors in results.items():
        assert errors == [], f"{name}: {errors}"


def test_every_domain_is_represented():
    domains = set()
    for c in Path(__file__).parent.glob("*/contract.yaml"):
        domains.add(yaml.safe_load(c.read_text(encoding="utf-8"))["domain"])
    assert {"customer", "analytics", "sales", "risk"} <= domains


def test_validator_catches_missing_field(tmp_path):
    bad = tmp_path / "broken"
    bad.mkdir()
    (bad / "contract.yaml").write_text("name: broken\ndomain: x\n", encoding="utf-8")
    errors = validate_contract(bad / "contract.yaml")
    assert any("obrigatórios ausentes" in e for e in errors)


def test_validator_catches_quality_rule_on_unknown_column(tmp_path):
    bad = tmp_path / "risk"  # pasta precisa bater com `name`
    bad.mkdir()
    contract = {
        "name": "risk", "domain": "risk", "owner": "t", "version": "0.1.0",
        "output_ports": [{"type": "delta_table", "location": "x"}],
        "sla": {"freshness": "1h", "availability": "99%"},
        "schema": [{"name": "id", "type": "string", "nullable": False}],
        "quality_rules": [{"rule": "not_null", "columns": ["does_not_exist"]}],
        "lineage": {"upstream": ["bronze.x"]},
        "access_policy": {"classification": "internal", "masking": []},
    }
    (bad / "contract.yaml").write_text(yaml.safe_dump(contract), encoding="utf-8")
    errors = validate_contract(bad / "contract.yaml")
    assert any("coluna inexistente" in e for e in errors)
