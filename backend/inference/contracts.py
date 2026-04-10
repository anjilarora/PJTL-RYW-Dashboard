"""Shared inference feature contract (must match training export metadata)."""

from __future__ import annotations

FEATURE_ORDER: tuple[str, ...] = (
    "vehicle_utilization",
    "billed_utilization",
    "total_volume_pool",
    "revenue_per_kent_leg",
    "high_acuity_share",
    "non_billable_noshow",
    "road_hours_per_vehicle",
    "contract_concentration",
    "cost_per_road_hour",
)
