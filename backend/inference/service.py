from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from xgboost import XGBClassifier

from inference.contracts import FEATURE_ORDER


@dataclass
class InferenceResult:
    prediction: str
    confidence: float
    probability_ready: float
    top_drivers: List[Dict[str, float]]
    model_version: str
    model_evidence: Dict[str, str]


def _resolve_model_dir() -> Path:
    env = os.getenv("RYW_INFERENCE_MODEL_DIR")
    if env:
        return Path(env)
    # Repo layout: code/backend/inference/service.py -> parents[2] == code/
    code_dir = Path(__file__).resolve().parents[2]
    return code_dir / "inference_engine" / "results" / "models"


class ExplainableInferenceEngine:
    """
    Loads XGBoost classifier + metadata produced by inference_engine training/export.
    """

    def __init__(self) -> None:
        self.model = XGBClassifier()
        self.classification_threshold = 0.5
        self.model_version = "unknown"
        self.label_source = "unknown"
        self.validation_status = "unknown"
        self.baseline_thresholds: Dict[str, float] = {
            "vehicle_utilization": 0.95,
            "billed_utilization": 1.05,
            "total_volume_pool": 1.2,
            "revenue_per_kent_leg": 70.0,
            "high_acuity_share": 0.05,
            "non_billable_noshow": 0.10,
            "road_hours_per_vehicle": 9.0,
            "contract_concentration": 0.20,
            "cost_per_road_hour": 50.0,
        }
        self.model_loaded = False
        self.load_error: str | None = None
        self._model_dir = _resolve_model_dir()
        self._load_model_artifacts()

    def _load_model_artifacts(self) -> None:
        model_path = self._model_dir / "xgboost_readiness.json"
        metadata_path = self._model_dir / "xgboost_readiness_metadata.json"

        if not model_path.exists():
            self.load_error = f"Missing model: {model_path}"
            return
        if not metadata_path.exists():
            self.load_error = f"Missing metadata: {metadata_path}"
            return

        try:
            with metadata_path.open("r", encoding="utf-8") as fh:
                metadata: Dict[str, Any] = json.load(fh)

            fo = metadata.get("feature_order")
            if isinstance(fo, list) and [str(x) for x in fo] != list(FEATURE_ORDER):
                raise ValueError("feature_order in metadata must match API FEATURE_ORDER")

            self.classification_threshold = float(metadata.get("best_classification_threshold", 0.5))
            self.model_version = str(metadata.get("model_version", "unknown"))
            self.label_source = str(metadata.get("label_source", "unknown"))
            self.validation_status = str(metadata.get("validation_status", "unknown"))

            thresholds = metadata.get("thresholds", {})
            if isinstance(thresholds, dict):
                for k, v in thresholds.items():
                    if k in self.baseline_thresholds:
                        self.baseline_thresholds[k] = float(v)

            self.model.load_model(model_path)
            self.model_loaded = True
            self.load_error = None
        except Exception as exc:
            self.model_loaded = False
            self.load_error = str(exc)

    def health_snapshot(self) -> Dict[str, Any]:
        return {
            "model_loaded": self.model_loaded,
            "model_dir": str(self._model_dir),
            "model_version": self.model_version,
            "label_source": self.label_source,
            "validation_status": self.validation_status,
            "classification_threshold": self.classification_threshold,
            "load_error": self.load_error,
        }

    def predict(self, features: Dict[str, float]) -> InferenceResult:
        if not self.model_loaded:
            raise RuntimeError(self.load_error or "Model not loaded")

        row = np.array([[float(features.get(name, 0.0)) for name in FEATURE_ORDER]])
        proba_ready = float(self.model.predict_proba(row)[0][1])
        prediction = "Ready" if proba_ready >= self.classification_threshold else "Not Ready"
        confidence = max(proba_ready, 1 - proba_ready)

        importances = self.model.feature_importances_.tolist()
        signed_driver = []
        for i, name in enumerate(FEATURE_ORDER):
            delta = float(features.get(name, 0.0) - self.baseline_thresholds[name])
            direction = (
                -1.0
                if name in {"non_billable_noshow", "contract_concentration", "cost_per_road_hour"}
                else 1.0
            )
            signed_driver.append(
                {
                    "feature": name,
                    "weight": float(importances[i]),
                    "impact": float(delta * direction * importances[i]),
                }
            )
        top_drivers = sorted(signed_driver, key=lambda x: abs(x["impact"]), reverse=True)[:5]

        return InferenceResult(
            prediction=prediction,
            confidence=confidence,
            probability_ready=proba_ready,
            top_drivers=top_drivers,
            model_version=self.model_version,
            model_evidence={
                "label_source": self.label_source,
                "validation_status": self.validation_status,
            },
        )


engine = ExplainableInferenceEngine()
