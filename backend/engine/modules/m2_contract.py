"""
Module 2: Contract Business Model

Encodes RYW's internal billing rules, no-show policies, and contract
quality/filler classification. Determines what fraction of completed
trips actually generate revenue.

Key rules:
  - SNF contracts: 100% billable no-show if cancelled within 12hr of pickup
  - Broker/insurance (SafeRide, MTM, etc.): no-shows are never billable
  - SecureCare: no-shows never billable, demand is spontaneous (ED-driven)
  - VA: flat rate per trip
  - No single contract > 20% of volume or revenue
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from engine.modules.base import BaseModule
from engine.models.market import MarketProfile, ProspectiveContract
from engine.models.metrics import DemandForecast, ContractProfile
from engine.config import NOSHOW_TIERS, VIABILITY


class ContractModule(BaseModule):
    name = "M2_Contract"

    def validate(self, inputs: Dict[str, Any]) -> bool:
        required = ["market_profile", "demand_forecast"]
        return all(k in inputs for k in required)

    def run(
        self,
        market_profile: MarketProfile,
        demand_forecast: DemandForecast,
        historical_contract_data: Optional[Dict[str, Any]] = None,
    ) -> ContractProfile:
        """
        Contract business model pipeline:

        1. Classify each prospective contract as quality or filler
        2. Apply no-show billing rules per contract tier
        3. Calculate expected billable vs non-billable no-show rates
        4. Compute blended revenue per Kent-Leg across all contracts
        5. Check contract concentration (no single contract > 20%)
        6. Flag bad-revenue contracts (below $67.50/KL for wheelchair)
        """

        contracts = market_profile.prospective_contracts
        if not contracts:
            contracts = [
                ProspectiveContract(
                    name="Default Market Contract",
                    contract_type="hospital",
                    estimated_daily_rides=max(8.0, demand_forecast.expected_daily_ride_requests * 0.7),
                    estimated_revenue_per_trip=72.0,
                    order_modes=["ambulatory", "wheelchair"],
                    noshow_billing_tier="snf",
                ),
                ProspectiveContract(
                    name="Default Filler Contract",
                    contract_type="broker",
                    estimated_daily_rides=max(2.0, demand_forecast.expected_daily_ride_requests * 0.3),
                    estimated_revenue_per_trip=45.0,
                    order_modes=["ambulatory"],
                    noshow_billing_tier="broker",
                ),
            ]

        # ── Step 1: Quality vs Filler classification ─────────────────
        # Quality: SNF, hospital, VA, recurring medical
        # Filler: broker-based (SafeRide, MTM, ModivCare, Feonix)
        # TODO: implement classify_contracts()
        quality_types = {"snf", "hospital", "va", "securecare"}
        quality_contracts = [c for c in contracts if c.contract_type.lower() in quality_types]
        filler_contracts = [c for c in contracts if c not in quality_contracts]
        total_volume = sum(c.estimated_daily_rides for c in contracts) or 1.0
        quality_volume_pct = sum(c.estimated_daily_rides for c in quality_contracts) / total_volume
        filler_volume_pct = sum(c.estimated_daily_rides for c in filler_contracts) / total_volume

        # ── Step 2: No-show billing rules ────────────────────────────
        # For each contract, look up its NOSHOW_TIER and compute:
        #   - billable_noshow_rate
        #   - non_billable_noshow_rate
        # TODO: implement apply_noshow_rules()
        tier_weighted_billable = 0.0
        for contract in contracts:
            tier_name = contract.noshow_billing_tier.lower()
            tier = NOSHOW_TIERS.get(tier_name, NOSHOW_TIERS["broker"])
            tier_weighted_billable += (
                contract.estimated_daily_rides / total_volume
            ) * (1.0 if tier.billable_after_12hr else tier.billable_before_12hr_pct)
        assumed_noshow_rate = max(demand_forecast.expected_noshow_rate, 0.03)
        billable_noshow_rate = assumed_noshow_rate * tier_weighted_billable
        non_billable_noshow_rate = max(0.0, assumed_noshow_rate - billable_noshow_rate)

        # ── Step 3: Billed utilization forecast ──────────────────────
        # billed_util = completed_util + billable_noshow_contribution
        # TODO: implement billed_utilization_calc()
        billed_utilization = 1.0 + billable_noshow_rate - non_billable_noshow_rate

        # ── Step 4: Blended revenue per Kent-Leg ─────────────────────
        # weighted avg across all contracts by expected volume
        # TODO: implement blended_revenue_calc()
        blended_revenue = sum(
            c.estimated_daily_rides * c.estimated_revenue_per_trip for c in contracts
        ) / total_volume

        # ── Step 5: Concentration check ──────────────────────────────
        # No single contract > 20% of total volume or revenue
        # TODO: implement concentration_check()
        volume_shares = [c.estimated_daily_rides / total_volume for c in contracts]
        total_revenue = sum(c.estimated_daily_rides * c.estimated_revenue_per_trip for c in contracts) or 1.0
        revenue_shares = [
            (c.estimated_daily_rides * c.estimated_revenue_per_trip) / total_revenue
            for c in contracts
        ]
        top_volume_pct = max(volume_shares)
        top_revenue_pct = max(revenue_shares)
        concentration_flag = (
            top_volume_pct > VIABILITY.contract_concentration_max
            or top_revenue_pct > VIABILITY.contract_concentration_max
        )

        # ── Step 6: Bad-revenue flagging ─────────────────────────────
        # TODO: implement per-contract revenue check
        bad_revenue_flag = any(
            c.contract_type.lower() == "wheelchair" and c.estimated_revenue_per_trip < 67.5
            for c in contracts
        )

        return ContractProfile(
            quality_volume_pct=quality_volume_pct,
            filler_volume_pct=filler_volume_pct,
            billed_utilization_forecast=billed_utilization,
            blended_revenue_per_kent_leg=blended_revenue,
            expected_billable_noshow_rate=billable_noshow_rate,
            expected_non_billable_noshow_rate=non_billable_noshow_rate,
            top_contract_volume_pct=top_volume_pct,
            top_contract_revenue_pct=top_revenue_pct,
            concentration_flag=concentration_flag,
            bad_revenue_flag=bad_revenue_flag,
        )

    def summarize(self, output: ContractProfile) -> Dict[str, Any]:
        return {
            "quality_volume_pct": output.quality_volume_pct,
            "filler_volume_pct": output.filler_volume_pct,
            "billed_utilization": output.billed_utilization_forecast,
            "blended_rev_per_kl": output.blended_revenue_per_kent_leg,
            "non_billable_noshow_rate": output.expected_non_billable_noshow_rate,
            "concentration_flag": output.concentration_flag,
            "bad_revenue_flag": output.bad_revenue_flag,
        }
