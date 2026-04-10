"""
Module 1: Demand Forecasting

Projects demand in a prospective market based on:
  - Historical ride volume by region / contract / mode / broker %
  - External data: hospital density, population demographics, competitor presence
  - Geographic similarity to existing RYW markets

Outputs: expected contracts, ride requests, completed trips, Kent-Legs, mode mix.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from engine.modules.base import BaseModule
from engine.models.market import MarketProfile, RegionGeography
from engine.models.metrics import DemandForecast
from engine.config import ORDER_MODES, DAYS_OF_WEEK


class DemandModule(BaseModule):
    name = "M1_Demand"

    def validate(self, inputs: Dict[str, Any]) -> bool:
        required = ["market_profile", "historical_baselines"]
        return all(k in inputs for k in required)

    def run(
        self,
        market_profile: MarketProfile,
        historical_baselines: Dict[str, Any],
        external_data: Optional[Dict[str, Any]] = None,
    ) -> DemandForecast:
        """
        Demand forecasting pipeline:

        1. Retrieve historical volume from analogous existing regions
           (Grand Rapids, Lansing, Battle Creek baselines from Q1 data)
        2. Scale by facility density ratio:
           (new_region_facilities / analogous_region_facilities)
        3. Adjust for population demographics (age mix, Medicaid eligibility)
        4. Adjust for competitor density (more competitors -> lower capture rate)
        5. Apply mode mix from historical data
        6. Convert trips -> Kent-Legs using historical KL multipliers by mode
        7. Project daily/daypart demand curves from historical patterns
        """

        region = market_profile.region

        # ── Step 1: Historical baseline lookup ───────────────────────
        # TODO: Pull per-region daily averages from ingested Q1 data
        # Variables needed:
        #   - total_rides_per_day by region
        #   - kent_legs_per_day by region
        #   - mode_breakdown_pct by region
        #   - completion_rate by region
        #   - cancellation_rate by region
        baseline = historical_baselines or {}

        # ── Step 2: Facility density scaling ─────────────────────────
        # ratio = new_region_facilities / comparable_region_facilities
        # TODO: implement facility_density_ratio()
        comparable_facilities = float(baseline.get("avg_facilities", 12.0))
        region_facilities = float(region.hospital_count + region.snf_count + region.clinic_count)
        density_ratio = region_facilities / comparable_facilities if comparable_facilities > 0 else 1.0
        density_ratio = max(0.6, min(1.8, density_ratio))

        # ── Step 3: Population adjustment ────────────────────────────
        # Higher elderly % and Medicaid eligibility -> higher NEMT demand
        # TODO: implement population_adjustment_factor()
        elderly_factor = max(0.0, region.elderly_population_pct) / 100.0
        medicaid_factor = max(0.0, region.medicaid_eligible_pct) / 100.0
        pop_adjustment = 0.85 + (elderly_factor * 0.6) + (medicaid_factor * 0.4)

        # ── Step 4: Competitor adjustment ────────────────────────────
        # More competitors -> lower expected market capture
        # TODO: implement competitor_adjustment_factor()
        competitor_penalty = min(0.35, region.competitor_count * 0.04)
        competitor_adjustment = 1.0 - competitor_penalty

        # ── Step 5: Composite demand estimate ────────────────────────
        # scaled_demand = baseline * density_ratio * pop_adj * competitor_adj
        # TODO: implement composite calculation
        baseline_daily = float(baseline.get("daily_rides", 40.0))
        expected_daily_rides = max(5.0, baseline_daily * density_ratio * pop_adjustment * competitor_adjustment)
        expected_contracts = max(1, int(round(expected_daily_rides / 10)))

        # ── Step 6: Mode mix application ─────────────────────────────
        # Apply historical mode percentages from Q1 data
        # TODO: pull from Mode Breakdown sheet
        provided_mix = baseline.get("mode_pct", {})
        mode_mix = {
            "ambulatory": float(provided_mix.get("ambulatory", 0.52)),
            "wheelchair": float(provided_mix.get("wheelchair", 0.36)),
            "stretcher": float(provided_mix.get("stretcher", 0.07)),
            "securecare": float(provided_mix.get("securecare", 0.05)),
        }
        total_mix = sum(mode_mix.values()) or 1.0
        mode_mix = {k: v / total_mix for k, v in mode_mix.items()}

        # ── Step 7: Kent-Leg conversion ──────────────────────────────
        # Use historical KL multipliers per mode from Q1 data
        # TODO: implement kent_leg_projection()
        multipliers = baseline.get("kl_multiplier_by_mode", {})
        expected_kent_legs = expected_daily_rides * sum(
            mode_mix[mode] * float(multipliers.get(mode, 1.2))
            for mode in ORDER_MODES
        )

        # ── Step 8: Daily / daypart curves ───────────────────────────
        # TODO: pull day-of-week distribution from Total Performance sheet
        day_dist = baseline.get("day_of_week_distribution", {})
        default_day_dist = {day: (1.0 / len(DAYS_OF_WEEK)) for day in DAYS_OF_WEEK}
        distribution = {
            day: float(day_dist.get(day, default_day_dist[day]))
            for day in DAYS_OF_WEEK
        }
        dist_total = sum(distribution.values()) or 1.0
        daily_demand = {
            day: expected_daily_rides * (distribution[day] / dist_total)
            for day in DAYS_OF_WEEK
        }

        return DemandForecast(
            region_name=region.region_name,
            expected_contracts=expected_contracts,
            expected_daily_ride_requests=expected_daily_rides,
            expected_completed_trips=expected_daily_rides * float(baseline.get("completion_rate", 0.87)),
            expected_kent_legs=expected_kent_legs,
            mode_mix=mode_mix,
            daily_demand=daily_demand,
            expected_cancellation_rate=float(baseline.get("cancellation_rate", 0.08)),
            expected_noshow_rate=float(baseline.get("noshow_rate", 0.06)),
        )

    def summarize(self, output: DemandForecast) -> Dict[str, Any]:
        return {
            "region": output.region_name,
            "expected_contracts": output.expected_contracts,
            "daily_ride_requests": output.expected_daily_ride_requests,
            "completed_trips": output.expected_completed_trips,
            "kent_legs": output.expected_kent_legs,
            "mode_mix": output.mode_mix,
            "noshow_rate": output.expected_noshow_rate,
        }
