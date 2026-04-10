from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadinessDecision:
    state: str
    reason: str


def classify_readiness(passing_count: int, failing_count: int, unresolved_gate_count: int) -> ReadinessDecision:
    """
    Confidence-aware tri-state readiness classifier aligned to Phase 0 policy:
    Ready / Not Ready / Insufficient Data.
    """
    if unresolved_gate_count >= 3:
        return ReadinessDecision(
            state="Insufficient Data",
            reason="Three or more gate-critical metrics are unresolved or manually overridden.",
        )
    if failing_count > 0:
        return ReadinessDecision(
            state="Not Ready",
            reason="One or more required gates failed under current assumptions.",
        )
    if passing_count >= 9:
        return ReadinessDecision(
            state="Ready",
            reason="All nine gates pass with available evidence.",
        )
    return ReadinessDecision(
        state="Insufficient Data",
        reason="Gate set incomplete for deterministic decision.",
    )
