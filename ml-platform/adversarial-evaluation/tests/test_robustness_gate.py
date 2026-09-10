from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from robustness_gate import GateThresholds, evaluate_gate  # noqa: E402


@dataclass
class _Rob:
    clean_accuracy: float
    robust_accuracy: float
    risk_level: str = "low"


@dataclass
class _Report:
    model_name: str
    overall_risk: str
    robustness: _Rob


def test_gate_approves_robust_model():
    r = _Report("churn@4", "low", _Rob(clean_accuracy=0.94, robust_accuracy=0.80))
    d = evaluate_gate(r)
    assert d.approved is True
    assert d.reasons == []


def test_gate_blocks_high_overall_risk():
    r = _Report("churn@5", "high", _Rob(clean_accuracy=0.94, robust_accuracy=0.80))
    d = evaluate_gate(r)
    assert d.approved is False
    assert any("overall_risk" in reason for reason in d.reasons)


def test_gate_blocks_low_robust_accuracy_and_big_drop():
    r = _Report("churn@6", "medium", _Rob(clean_accuracy=0.95, robust_accuracy=0.40))
    d = evaluate_gate(r)
    assert d.approved is False
    assert len(d.reasons) == 2  # robust_accuracy baixa E drop grande


def test_gate_accepts_risklevel_enum_like_value():
    class _Enum:
        value = "medium"

    r = _Report("churn@7", _Enum(), _Rob(clean_accuracy=0.9, robust_accuracy=0.75))
    assert evaluate_gate(r).approved is True


def test_custom_thresholds():
    r = _Report("churn@8", "low", _Rob(clean_accuracy=0.9, robust_accuracy=0.65))
    strict = GateThresholds(min_robust_accuracy=0.7)
    assert evaluate_gate(r, strict).approved is False
