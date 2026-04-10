from __future__ import annotations

from typing import Iterable

from engine.models.metrics import ConditionResult


def derive_confidence_tier(conditions: Iterable[ConditionResult]) -> str:
    failing = 0
    provisional = 0
    for condition in conditions:
        if not condition.passed:
            failing += 1
        if condition.metric_number in {2, 3, 6}:
            # Explicitly sensitive/underdefined metrics from execution plan.
            provisional += 1
    if failing == 0 and provisional == 0:
        return "Tier 1 Audited"
    if failing <= 2:
        return "Tier 2 Assumption-Backed"
    return "Tier 3 Manual Override"
