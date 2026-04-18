"""
Variable Mapping -- translates normalized metrics into the granular
internal variables that each module expects as input.

This is the bridge between "what the spreadsheet says" and "what
the engine modules need." Each module's input contract is defined
in engine/models/metrics.py.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class VariableMapper:
    """
    Maps normalized Q1 data into the historical_data dict consumed
    by Pipeline.run().
    """

    def map(self, normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produce the full historical_data payload for the pipeline.

        Returns:
            {
                "baselines": { ... },           # for Module 1
                "contracts": { ... },           # for Module 2
                "cost_assumptions": { ... },    # for Module 4
                "revenue_by_mode": { ... },     # for Module 5
            }
        """
        return {
            "baselines": self._build_baselines(normalized_data),
            "contracts": self._build_contract_data(normalized_data),
            "cost_assumptions": self._build_cost_assumptions(normalized_data),
            "revenue_by_mode": self._build_revenue_by_mode(normalized_data),
        }

    def _build_baselines(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build Module 1 baselines from historical performance.

        Maps:
          Total Performance -> per-region daily averages
            - avg_daily_rides_by_region
            - avg_daily_kent_legs_by_region
            - completion_rate_by_region
            - cancellation_rate_by_region
            - noshow_rate_by_region
            - day_of_week_distribution

          Mode Breakdown -> mode proportions
            - mode_pct (ambulatory, wheelchair, stretcher)
            - kl_multiplier_by_mode

          Regional Performance -> per-region fleet/capacity baselines
            - vehicles_by_region
            - vehicle_utilization_by_region
        """
        mode_breakdown = data.get("mode_breakdown", {})
        total_performance = data.get("total_performance", [])
        avg_daily_rides = sum(float(r.get("total_rides", 0) or 0) for r in total_performance) / max(1, len(total_performance))
        avg_daily_kl = sum(float(r.get("kent_legs", 0) or 0) for r in total_performance) / max(1, len(total_performance))
        completion_rate = sum(float(r.get("completion_rate", 0.87) or 0.87) for r in total_performance) / max(1, len(total_performance))
        noshow_rate = sum(float(r.get("noshow_rate", 0.06) or 0.06) for r in total_performance) / max(1, len(total_performance))
        cancellation_rate = sum(float(r.get("cancellation_rate", 0.08) or 0.08) for r in total_performance) / max(1, len(total_performance))

        vehicle_rows = data.get("vehicle_breakdown", [])
        road_hours_values: list[float] = []
        for row in vehicle_rows:
            hrs = row.get("road_time_hrs", row.get("road_time"))
            try:
                hrs_f = float(hrs) if hrs not in (None, "") else 0.0
            except (TypeError, ValueError):
                hrs_f = 0.0
            if hrs_f > 0:
                road_hours_values.append(hrs_f)
        avg_road_hours = (
            sum(road_hours_values) / len(road_hours_values)
            if road_hours_values
            else 0.0
        )

        return {
            "daily_rides": avg_daily_rides or 40.0,
            "daily_kent_legs": avg_daily_kl or 56.0,
            "completion_rate": completion_rate or 0.87,
            "noshow_rate": noshow_rate or 0.06,
            "cancellation_rate": cancellation_rate or 0.08,
            "mode_pct": mode_breakdown.get("pct_by_mode", {}),
            "kl_multiplier_by_mode": mode_breakdown.get("kl_multiplier_by_mode", {}),
            "day_of_week_distribution": {
                "monday": 0.17,
                "tuesday": 0.18,
                "wednesday": 0.18,
                "thursday": 0.17,
                "friday": 0.16,
                "saturday": 0.14,
            },
            "avg_facilities": 12.0,
            # Observed mean of vehicle-day road hours from the Vehicle Breakdown
            # sheet. Used by M3 as the empirical road-hours baseline rather than
            # the previous ad-hoc formula (scheduled_volume / vehicles).
            "road_hours_per_vehicle_per_day": avg_road_hours,
        }

    def _build_contract_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build Module 2 contract data from historical contracts.

        Maps:
          Contract Volume -> per-payer volumes and concentrations
          Revenue by Payer -> per-payer revenue and billability

        Output:
          {
              "contracts": [
                  {"payer": ..., "volume": ..., "revenue": ..., "type": ...},
              ],
              "total_volume": ...,
              "total_revenue": ...,
              "quality_volume_pct": ...,
              "filler_volume_pct": ...,
              "billable_noshow_rate": ...,
              "non_billable_noshow_rate": ...,
          }
        """
        contracts = data.get("contract_volume", [])
        rev_rows = data.get("revenue_by_payer", [])
        total_volume = sum(float(c.get("trip_count", 0) or 0) for c in contracts)
        total_revenue = sum(float(r.get("total_revenue", 0) or 0) for r in rev_rows)
        return {
            "contracts": contracts,
            "total_volume": total_volume,
            "total_revenue": total_revenue,
            "quality_volume_pct": 0.70,
            "filler_volume_pct": 0.30,
            "billable_noshow_rate": 0.03,
            "non_billable_noshow_rate": 0.05,
        }

    def _build_cost_assumptions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build Module 4 cost inputs from Weekly Margin data.

        Maps:
          Weekly Margin -> average daily costs by category
            - daily_overhead (Fixed Overhead Cost)
            - daily_fixed_operating (Fixed Operating Cost)
            - daily_gas (Gas)
            - daily_driver_wage (Driver Wage)
            - daily_capx (CapX)

          SecureCare Profit -> SC-specific cost structure
        """
        rows = data.get("weekly_margin", [])
        avg = lambda key, fallback: (
            sum(float(r.get(key, fallback) or fallback) for r in rows) / max(1, len(rows))
        )
        return {
            "daily_overhead": avg("fixed_overhead_cost", 1200.0),
            "daily_fixed_operating": avg("fixed_operating_cost", 900.0),
            "daily_gas": avg("gas", 250.0),
            "daily_driver_wage": avg("driver_wage", 2400.0),
            "daily_capx": avg("capx", 100.0),
            "fuel_cost_per_mile": 0.48,
            "avg_hourly_rate": 47.5,
        }

    def _build_revenue_by_mode(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Build Module 5 revenue-per-KL by mode.

        Maps:
          Mode Breakdown -> Revenue By Mode / Kent Legs by Mode
            = avg revenue per Kent Leg per mode
        """
        mode = data.get("mode_breakdown", {})
        revenue = mode.get("revenue_by_mode", {})
        kent_legs = mode.get("kent_legs_by_mode", {})
        return {
            "ambulatory": float(revenue.get("ambulatory", 4200)) / max(1.0, float(kent_legs.get("ambulatory", 100))),
            "wheelchair": float(revenue.get("wheelchair", 6200)) / max(1.0, float(kent_legs.get("wheelchair", 100))),
            "stretcher": float(revenue.get("stretcher", 2400)) / max(1.0, float(kent_legs.get("stretcher", 20))),
            "securecare": float(revenue.get("securecare", 2600)) / max(1.0, float(kent_legs.get("securecare", 20))),
        }
