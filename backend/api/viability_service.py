from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from engine.evaluation.dashboard import DashboardFormatter
from engine.evaluation.confidence import derive_confidence_tier
from engine.evaluation.readiness_classifier import classify_readiness
from engine.evaluation.reconstruction import evaluate_reconstruction_drift
from engine.models.market import FleetDeployment, MarketProfile, ProspectiveContract, RegionGeography
from engine.pipeline import Pipeline

from api.ml_features import report_dict_to_inference_features
from inference.service import engine


def evaluate_market(
    market_profile_input: Dict[str, Any],
    historical_data: Dict[str, Any],
    external_data: Dict[str, Any] | None,
    scenario_overrides: Dict[str, Any] | None,
) -> Dict[str, Any]:
    region = RegionGeography(**market_profile_input["region"])
    fleet = FleetDeployment(**market_profile_input["fleet"])
    contracts = [ProspectiveContract(**c) for c in market_profile_input.get("prospective_contracts", [])]
    profile = MarketProfile(
        region=region,
        fleet=fleet,
        overbooking_limit=market_profile_input.get("overbooking_limit", 1.2),
        projection_horizon=market_profile_input.get("projection_horizon", "quarter"),
        broker_volume_pct=market_profile_input.get("broker_volume_pct", 0.30),
        prospective_contracts=contracts,
    )

    report = Pipeline().run(
        market_profile=profile,
        historical_data=historical_data,
        external_data=external_data,
        scenario_overrides=scenario_overrides,
    )
    formatter = DashboardFormatter()
    unresolved_gate_count = sum(
        1 for c in report.conditions if c.metric_number in {2, 3, 6} and not c.passed
    )
    readiness = classify_readiness(
        passing_count=report.passing_count,
        failing_count=report.failing_count,
        unresolved_gate_count=unresolved_gate_count,
    )
    base_payload = {
        "report": formatter.to_dict(report),
        "raw": asdict(report),
        "readiness_state": readiness.state,
        "readiness_reason": readiness.reason,
        "confidence_tier": derive_confidence_tier(report.conditions),
        "governance": {
            "authority_precedence": ["Priority 1 Charter", "Priority 2 Workbook", "Priority 3 PJTL Assumptions"],
            "confidence_framework": ["Tier 1 Audited", "Tier 2 Assumption-Backed", "Tier 3 Manual Override"],
            "phase_artifacts": [
                "knowledge-base/phase-0-freeze-package.md",
                "knowledge-base/phase-1-canonical-analytical-base.md",
            ],
        },
        "lineage_refs": {
            "field_dictionary": "code/intermediates/phase1/field_dictionary.csv",
            "join_key_inventory": "code/intermediates/phase1/join_key_inventory.csv",
            "missingness_audit": "code/intermediates/phase1/missingness_audit.csv",
        },
        "gate_details": [
            _gate_detail(condition.metric_number, condition.name, condition.passed)
            for condition in report.conditions
        ],
    }
    drift = evaluate_reconstruction_drift(
        historical_data=historical_data,
        report_payload=base_payload,
    )

    # tighten insufficient-data path using drift and unresolved gate proxy
    if drift["drift_status"] == "out_of_tolerance" and drift["unresolved_gate_proxy"] >= 1:
        base_payload["readiness_state"] = "Insufficient Data"
        base_payload["readiness_reason"] = (
            "Reconstruction drift exceeded tolerance while unresolved gate coverage remains."
        )
        base_payload["confidence_tier"] = "Tier 3 Manual Override"

    base_payload["reconstruction_drift"] = drift

    # ML-assisted decision (XGBoost trained only on real RYW inputs via inference_engine export)
    base_payload["ml_readiness"] = {}
    if engine.model_loaded:
        try:
            feats = report_dict_to_inference_features(base_payload["report"])
            ml = engine.predict(feats)
            base_payload["ml_readiness"] = {
                "prediction": ml.prediction,
                "probability_ready": ml.probability_ready,
                "confidence": ml.confidence,
                "top_drivers": ml.top_drivers,
                "model_version": ml.model_version,
                "model_evidence": ml.model_evidence,
            }
            gates_state = base_payload["readiness_state"]
            gates_reason = base_payload["readiness_reason"]
            ml_ready = ml.prediction == "Ready"
            if gates_state == "Insufficient Data":
                pass
            elif gates_state != "Ready" or not ml_ready:
                base_payload["readiness_state"] = "Not Ready"
                base_payload["readiness_reason"] = (
                    f"{gates_reason} | ML: {ml.prediction} "
                    f"(p_ready={ml.probability_ready:.3f}, model={ml.model_version})"
                )
            else:
                base_payload["readiness_state"] = "Ready"
                base_payload["readiness_reason"] = (
                    f"{gates_reason} | ML concurs Ready "
                    f"(p_ready={ml.probability_ready:.3f}, model={ml.model_version})"
                )
        except Exception as exc:
            base_payload["ml_readiness"] = {"error": str(exc)}
    else:
        base_payload["ml_readiness"] = {"error": engine.load_error or "Model not loaded"}

    return base_payload


def _gate_detail(metric_number: int, name: str, passed: bool) -> Dict[str, Any]:
    formula_versions = {
        1: "utilization_v1",
        2: "billed_utilization_v2_branch",
        3: "volume_pool_v2_proxy",
        4: "revenue_per_kent_leg_v1",
        5: "high_acuity_share_v1_proxy",
        6: "noshow_denominator_v2_branch",
        7: "road_hours_v1",
        8: "contract_concentration_v1",
        9: "cost_per_road_hour_v1",
    }
    confidence_by_gate = {
        2: "Tier 2 Assumption-Backed",
        3: "Tier 2 Assumption-Backed",
        5: "Tier 2 Assumption-Backed",
        6: "Tier 2 Assumption-Backed",
    }
    return {
        "metric": metric_number,
        "name": name,
        "passed": passed,
        "formula_version": formula_versions.get(metric_number, "v1"),
        "confidence_tier": confidence_by_gate.get(metric_number, "Tier 1 Audited"),
        "fallback": "provisional" if not passed and metric_number in {2, 3, 6} else "deterministic",
    }
