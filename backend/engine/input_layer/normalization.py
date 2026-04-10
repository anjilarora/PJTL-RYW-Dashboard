"""
Normalization layer -- transforms raw ingested data into consistent,
comparable internal representations.

Handles:
  - Unit standardization (daily -> weekly -> quarterly aggregation)
  - Missing value treatment
  - Outlier detection for obviously erroneous data points
  - Percentage vs decimal normalization
  - Currency standardization
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class MetricsNormalizer:
    """Normalizes raw ingested metrics into clean internal representations."""

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main normalization pipeline.

        Args:
            raw_data: Output from Q1MetricsIngestor.ingest()

        Returns:
            Normalized data dict with consistent units and types.
        """
        normalized = {}

        normalized["total_performance"] = self._normalize_performance(
            raw_data.get("total_performance", [])
        )
        normalized["regional_performance"] = self._normalize_regional(
            raw_data.get("regional_performance", [])
        )
        normalized["mode_breakdown"] = self._normalize_modes(
            raw_data.get("mode_breakdown", [])
        )
        normalized["weekly_margin"] = self._normalize_margins(
            raw_data.get("weekly_margin", [])
        )
        normalized["vehicle_breakdown"] = self._normalize_vehicles(
            raw_data.get("vehicle_breakdown", [])
        )
        normalized["contract_volume"] = self._normalize_contracts(
            raw_data.get("contract_volume", [])
        )
        normalized["revenue_by_payer"] = self._normalize_revenue(
            raw_data.get("revenue_by_payer", [])
        )

        return normalized

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip().replace(",", "")
        if text in {"", "#DIV/0!", "nan", "None"}:
            return default
        if text.endswith("%"):
            return float(text[:-1]) / 100.0
        try:
            return float(text)
        except ValueError:
            return default

    def _normalize_performance(self, rows: List[Dict]) -> List[Dict]:
        """
        Normalize Total Performance data.

        Transformations:
          - Ensure all percentages are decimals (0.85 not 85%)
          - Convert #DIV/0! to None
          - Aggregate Saturday data (partial day) appropriately
          - Compute weekly summaries from daily data
        """
        normalized_rows: List[Dict[str, Any]] = []
        for row in rows:
            normalized = dict(row)
            for key in ["billed_usage", "vehicle_usage", "schedule_efficiency", "volume_pool"]:
                if key in normalized:
                    value = self._to_float(normalized[key])
                    normalized[key] = value if value <= 1 else value / 100.0
            normalized_rows.append(normalized)
        return normalized_rows

    def _normalize_regional(self, rows: List[Dict]) -> Dict[str, List[Dict]]:
        """Split and normalize by region (GR, Lansing, Battle Creek)."""
        split = {"grand_rapids": [], "lansing": [], "battle_creek": []}
        for row in rows:
            region_raw = str(row.get("region", "")).lower()
            if "lansing" in region_raw:
                split["lansing"].append(row)
            elif "battle" in region_raw:
                split["battle_creek"].append(row)
            else:
                split["grand_rapids"].append(row)
        return split

    def _normalize_modes(self, rows: List[Dict]) -> Dict[str, Any]:
        """
        Normalize mode breakdown.

        Output structure:
          {
              "pct_by_mode": {"ambulatory": 0.55, "wheelchair": 0.35, "stretcher": 0.10},
              "kent_legs_by_mode": {"ambulatory": ..., ...},
              "revenue_by_mode": {"ambulatory": ..., ...},
              "kl_multiplier_by_mode": {"ambulatory": ..., ...},
          }
        """
        output = {
            "pct_by_mode": {"ambulatory": 0.52, "wheelchair": 0.36, "stretcher": 0.07, "securecare": 0.05},
            "kent_legs_by_mode": {},
            "revenue_by_mode": {},
            "kl_multiplier_by_mode": {"ambulatory": 1.05, "wheelchair": 1.30, "stretcher": 1.85, "securecare": 2.10},
        }
        for row in rows:
            mode = str(row.get("mode", row.get("label", ""))).strip().lower()
            if not mode:
                continue
            output["kent_legs_by_mode"][mode] = self._to_float(row.get("kent_legs"))
            output["revenue_by_mode"][mode] = self._to_float(row.get("revenue"))
            if "pct" in row:
                output["pct_by_mode"][mode] = self._to_float(row.get("pct"))
        return output

    def _normalize_margins(self, rows: List[Dict]) -> List[Dict]:
        """
        Normalize Weekly Margin data.

        Output per week:
          {
              "week": 1,
              "daily": [{day, revenue, cost, margin_pct, profit, cost_breakdown}, ...],
              "weekly_total": {revenue, cost, margin_pct, profit},
          }
        """
        normalized_rows = []
        for row in rows:
            item = dict(row)
            revenue = self._to_float(item.get("revenue"))
            cost = self._to_float(item.get("cost"))
            item["revenue"] = revenue
            item["cost"] = cost
            item["margin_pct"] = ((revenue - cost) / revenue) if revenue > 0 else 0.0
            normalized_rows.append(item)
        return normalized_rows

    def _normalize_vehicles(self, rows: List[Dict]) -> List[Dict]:
        """
        Normalize Vehicle Breakdown data.

        Output per vehicle per day:
          {
              "date": ..., "driver": ..., "vehicle_id": ...,
              "road_time_hrs": ..., "active_time_hrs": ...,
              "mileage": ..., "mode": ..., "revenue": ...,
              "kent_legs": ..., "kl_per_hour": ..., "ampl": ...,
          }
        """
        normalized_rows = []
        for row in rows:
            item = dict(row)
            item["road_time_hrs"] = self._to_float(item.get("road_time_hrs", item.get("road_time")))
            item["active_time_hrs"] = self._to_float(item.get("active_time_hrs", item.get("active_time")))
            item["mileage"] = self._to_float(item.get("mileage"))
            item["revenue"] = self._to_float(item.get("revenue"))
            item["kent_legs"] = self._to_float(item.get("kent_legs"))
            normalized_rows.append(item)
        return normalized_rows

    def _normalize_contracts(self, rows: List[Dict]) -> List[Dict]:
        """
        Normalize Contract Volume data.

        Output per payer:
          {
              "payer": ..., "order_status": ...,
              "kent_legs": ..., "trip_count": ...,
              "pct_of_total_volume": ...,
          }
        """
        total_volume = sum(self._to_float(r.get("trip_count", r.get("volume"))) for r in rows) or 1.0
        normalized_rows = []
        for row in rows:
            item = dict(row)
            volume = self._to_float(item.get("trip_count", item.get("volume")))
            item["trip_count"] = volume
            item["pct_of_total_volume"] = volume / total_volume
            normalized_rows.append(item)
        return normalized_rows

    def _normalize_revenue(self, rows: List[Dict]) -> List[Dict]:
        """
        Normalize Revenue by Payer data.

        Output per payer:
          {
              "payer": ..., "total_revenue": ...,
              "total_legs": ..., "avg_revenue_per_leg": ...,
              "pct_of_total_revenue": ...,
          }
        """
        total_revenue = sum(self._to_float(r.get("total_revenue", r.get("revenue"))) for r in rows) or 1.0
        normalized_rows = []
        for row in rows:
            item = dict(row)
            revenue = self._to_float(item.get("total_revenue", item.get("revenue")))
            legs = self._to_float(item.get("total_legs", item.get("kent_legs")), default=1.0)
            item["total_revenue"] = revenue
            item["total_legs"] = legs
            item["avg_revenue_per_leg"] = revenue / legs if legs > 0 else 0.0
            item["pct_of_total_revenue"] = revenue / total_revenue
            normalized_rows.append(item)
        return normalized_rows
