"""
Module 4: Cost Modeling

Projects the fully-loaded operating cost for the deployed fleet,
combining fixed costs (overhead, insurance, lease) with variable
costs (driver wages, fuel, maintenance) scaled by Module 3 scheduling.

Key output: Cost per Road Hour (Metric #9, must be <= $50).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from engine.modules.base import BaseModule
from engine.models.market import MarketProfile
from engine.models.metrics import CapacityResult, CostEstimate
from engine.config import COST, VIABILITY


class CostModule(BaseModule):
    name = "M4_Cost"

    def validate(self, inputs: Dict[str, Any]) -> bool:
        required = ["market_profile", "capacity_result"]
        return all(k in inputs for k in required)

    def run(
        self,
        market_profile: MarketProfile,
        capacity_result: CapacityResult,
        cost_assumptions: Optional[Dict[str, float]] = None,
    ) -> CostEstimate:
        """
        Cost modeling pipeline:

        1. Calculate fixed overhead (office wages, admin, allocated corporate)
        2. Calculate fixed operating (insurance, vehicle lease/payments, Samsara)
        3. Calculate variable: driver wages = drivers * hours * wage_rate
        4. Calculate variable: fuel = expected_mileage * cost_per_mile
        5. Calculate variable: maintenance (preventative + reactive)
        6. Add SecureCare-specific costs if SC vehicles deployed
        7. Compute total cost and cost-per-road-hour
        """

        fleet = market_profile.fleet
        defaults = cost_assumptions or {}

        # ── Step 1: Fixed overhead ───────────────────────────────────
        # From Weekly Margin sheet: Fixed Overhead Cost = $4,276/day (current)
        # Scales with region (smaller market = proportionally less overhead)
        # TODO: implement overhead_scaling()
        base_overhead = float(defaults.get("daily_overhead", 1200.0))
        scaling = max(0.5, min(1.8, fleet.total_vehicles / 8 if fleet.total_vehicles else 0.5))
        daily_overhead = base_overhead * scaling

        # ── Step 2: Fixed operating ──────────────────────────────────
        # Insurance, vehicle payments, Samsara GPS, etc.
        # From Weekly Margin sheet: Fixed Operating Cost = $3,690/day (current)
        # Scales linearly with vehicle count
        # TODO: implement per-vehicle fixed operating cost
        per_vehicle_fixed = float(defaults.get("per_vehicle_fixed_operating", 210.0))
        daily_fixed_operating = per_vehicle_fixed * fleet.total_vehicles

        # ── Step 3: Driver wages ─────────────────────────────────────
        # The physically meaningful quantity is "hours a vehicle is rolling ×
        # wage rate" because each on-road hour needs one driver in the seat.
        # The previous formula used ``fleet.drivers`` as the multiplier which
        # double-counted bench/relief drivers (a fleet with drivers > vehicles
        # does not pay every driver a full road-hours shift simultaneously).
        # We clamp active drivers to the number of vehicles actually on the
        # road; remaining driver capacity is absorbed into fixed overhead.
        avg_hourly_rate = float(defaults.get("avg_hourly_rate", 47.5))
        road_hours = max(1.0, capacity_result.road_hours_per_vehicle_per_day)
        active_drivers = max(0, min(fleet.drivers, fleet.total_vehicles))
        if active_drivers == 0:
            active_drivers = fleet.total_vehicles
        daily_driver_wage = active_drivers * road_hours * avg_hourly_rate

        # ── Step 4: Fuel ─────────────────────────────────────────────
        # expected_mileage * fuel_cost_per_mile
        # TODO: pull fuel cost from historical gas data in Weekly Margin sheet
        fuel_cost_per_mile = float(defaults.get("fuel_cost_per_mile", 0.48))
        daily_fuel = capacity_result.expected_mileage * fuel_cost_per_mile

        # ── Step 5: Maintenance ──────────────────────────────────────
        # preventative + reactive, scaled by fleet size and mileage
        # TODO: implement maintenance_cost_model()
        maintenance_per_mile = float(defaults.get("maintenance_per_mile", 0.18))
        daily_maintenance = capacity_result.expected_mileage * maintenance_per_mile

        # ── Step 6: SecureCare-specific ──────────────────────────────
        # Dedicated vehicle, higher driver wage (+$2-3/hr), separate insurance
        # From SecureCare Profit sheet
        # TODO: implement securecare_cost_model()
        securecare_fixed = fleet.securecare_vehicles * float(defaults.get("securecare_fixed_per_vehicle", 95.0))
        securecare_variable = (
            capacity_result.expected_completed_kent_legs
            * float(defaults.get("securecare_variable_per_kl", 0.9))
            * max(0, fleet.securecare_vehicles)
        )

        # ── Step 7: Totals ───────────────────────────────────────────
        total_daily = (
            daily_overhead
            + daily_fixed_operating
            + daily_driver_wage
            + daily_fuel
            + daily_maintenance
            + securecare_fixed
            + securecare_variable
        )

        # Cost per road hour
        total_road_hours = (
            capacity_result.road_hours_per_vehicle_per_day
            * fleet.total_vehicles
        )
        cost_per_road_hour = 0.0
        if total_road_hours > 0:
            cost_per_road_hour = total_daily / total_road_hours

        # Cost per Kent-Leg
        cost_per_kl = 0.0
        if capacity_result.expected_completed_kent_legs > 0:
            cost_per_kl = total_daily / capacity_result.expected_completed_kent_legs

        return CostEstimate(
            total_cost=total_daily,
            total_driver_wage=daily_driver_wage,
            total_gas_cost=daily_fuel,
            total_fixed_cost=daily_fixed_operating + daily_maintenance,
            total_overhead=daily_overhead,
            cost_per_road_hour=cost_per_road_hour,
            cost_per_kent_leg=cost_per_kl,
            securecare_fixed_cost=securecare_fixed,
            securecare_variable_cost=securecare_variable,
            cost_breakdown={
                "overhead": daily_overhead,
                "fixed_operating": daily_fixed_operating,
                "driver_wage": daily_driver_wage,
                "fuel": daily_fuel,
                "maintenance": daily_maintenance,
                "securecare": securecare_fixed + securecare_variable,
            },
        )

    def summarize(self, output: CostEstimate) -> Dict[str, Any]:
        return {
            "total_cost": output.total_cost,
            "cost_per_road_hour": output.cost_per_road_hour,
            "cost_per_kent_leg": output.cost_per_kent_leg,
            "breakdown": output.cost_breakdown,
        }
