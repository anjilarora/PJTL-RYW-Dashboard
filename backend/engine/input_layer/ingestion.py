"""
Data ingestion layer for the Q1 Daily Metrics Excel workbook.

Reads each sheet into structured dicts that downstream normalization
and variable mapping can consume. This isolates Excel-specific parsing
from the rest of the engine.

Sheets in Q1 Daily Metrics workbook (canonical copy: code/inputs/Q1 Daily Metrics 2026.xlsx at repo root):
  1. Total Performance    - Daily KPIs by week (utilization, rides, KL, volume pool)
  2. Regional Performance - Same metrics broken out by GR / Lansing / Battle Creek
  3. Mode Breakdown       - Kent-Leg and revenue breakdown by Ambulatory / WC / Stretcher
  4. OTP                  - On-Time Performance (A-leg, B-leg)
  5. Contract Volume      - Ride volume by payer/facility
  6. Heat Map             - Geographic pickup/dropoff zone heatmap
  7. Revenue by Payer     - Revenue breakdown per contract
  8. Weekly Margin        - Revenue, cost, profit margin, cost decomposition by week
  9. Corewell Metrics     - (hidden) Corewell Health pilot metrics
 10. Vehicle Breakdown    - Per-vehicle road time, active time, mileage, revenue, KL
 11. SecureCare Profit    - SecureCare-specific cost/revenue analysis
 12. Sheet2               - (hidden) scratch
"""

from __future__ import annotations

import logging
import csv
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class Q1MetricsIngestor:
    """
    Reads the Q1 Daily Metrics workbook and returns structured data
    per sheet, ready for normalization.
    """

    EXPECTED_SHEETS = [
        "Total Performance",
        "Regional Performance",
        "Mode Breakdown",
        "OTP",
        "Contract Volume",
        "Heat Map",
        "Revenue by Payer",
        "Weekly Margin",
        "Vehicle Breakdown",
        "SecureCare Profit",
    ]

    def __init__(self, filepath: str | Path) -> None:
        self.filepath = Path(filepath)
        self._raw_data: Dict[str, Any] = {}

    def ingest(self) -> Dict[str, Any]:
        """
        Parse all sheets and return a dict keyed by sheet name.

        Returns:
            {
                "total_performance": [...rows...],
                "regional_performance": [...rows...],
                "mode_breakdown": [...rows...],
                ...
            }
        """
        logger.info("Ingesting metrics from %s", self.filepath)

        # CSV fallback ingestion for MVP: if directory is passed, each expected
        # sheet can be provided as a "<sheet_name>.csv" file.
        # If the exact workbook path is passed and Excel parsing is unavailable,
        # this returns empty structures but keeps API contracts stable.

        self._raw_data = {
            "total_performance": self._parse_total_performance(),
            "regional_performance": self._parse_regional_performance(),
            "mode_breakdown": self._parse_mode_breakdown(),
            "otp": self._parse_otp(),
            "contract_volume": self._parse_contract_volume(),
            "revenue_by_payer": self._parse_revenue_by_payer(),
            "weekly_margin": self._parse_weekly_margin(),
            "vehicle_breakdown": self._parse_vehicle_breakdown(),
            "securecare_profit": self._parse_securecare_profit(),
        }

        return self._raw_data

    def _parse_total_performance(self) -> List[Dict[str, Any]]:
        """
        Parse Total Performance sheet.

        Expected columns per week-block:
          Day, Billable NS, Billed Usage, Non-Billable NS, On-Time Performance,
          Vehicle Usage, Scheduled Usage, Total Rides, Kent Legs,
          Target Capacity, SL, SKL, KL Multiple, Volume Pool,
          Total Volume, Quality Pool, Total Pool, Schedule Efficiency
        """
        return self._read_csv_sheet("total_performance")

    def _parse_regional_performance(self) -> List[Dict[str, Any]]:
        """
        Parse Regional Performance sheet.
        Regions: Grand Rapids Fleet, Lansing Fleet, Battle Creek Fleet.
        """
        return self._read_csv_sheet("regional_performance")

    def _parse_mode_breakdown(self) -> List[Dict[str, Any]]:
        """
        Parse Mode Breakdown sheet.
        - Percentage Mode Breakdown (by Ambulatory, Wheelchair, Stretcher)
        - Total Kent Leg Mode Breakdown
        - Revenue By Mode
        - Kent Leg Multiplier by Mode
        """
        return self._read_csv_sheet("mode_breakdown")

    def _parse_otp(self) -> List[Dict[str, Any]]:
        """
        Parse On-Time Performance sheet.
        A-Leg OTP, B-Leg OTP, by region and overall.
        """
        return self._read_csv_sheet("otp")

    def _parse_contract_volume(self) -> List[Dict[str, Any]]:
        """
        Parse Contract Volume sheet.
        Volume by payer/facility (Payer ID, Order Status, Kent Legs, Trip Count).
        """
        return self._read_csv_sheet("contract_volume")

    def _parse_revenue_by_payer(self) -> List[Dict[str, Any]]:
        """
        Parse Revenue by Payer sheet.
        Revenue, Kent Legs, Avg Revenue per Leg, by payer.
        """
        return self._read_csv_sheet("revenue_by_payer")

    def _parse_weekly_margin(self) -> List[Dict[str, Any]]:
        """
        Parse Weekly Margin sheet.

        Per week, per day:
          Revenue side: Total Revenue
          Cost side: Fixed Overhead Cost, Fixed Operating Cost, Gas, Driver Wage
          Derived: Total Cost, Profit Margin, $ Profit, CapX, Post-CapX Margin

        Also contains Revenue-to-Overhead Balance analysis.
        """
        return self._read_csv_sheet("weekly_margin")

    def _parse_vehicle_breakdown(self) -> List[Dict[str, Any]]:
        """
        Parse Vehicle Breakdown sheet.

        Per vehicle per day:
          Date, Name (driver), Road Time, Active Time, Vehicle #,
          Mileage, Mode, Revenue, Kent Legs, AMPL (avg miles per leg),
          Kent Legs/hour
        """
        return self._read_csv_sheet("vehicle_breakdown")

    def _parse_securecare_profit(self) -> List[Dict[str, Any]]:
        """
        Parse SecureCare Profit sheet.

        Monthly/daily fixed overhead: salary (Aaron), dedicated night dispatch
        Monthly/daily operating: vehicle payments, insurance, upfitting,
                                 Samsara, preventative maintenance, repairs
        """
        return self._read_csv_sheet("securecare_profit")

    def _read_csv_sheet(self, sheet_key: str) -> List[Dict[str, Any]]:
        if self.filepath.is_file() and self.filepath.suffix.lower() == ".csv":
            candidate = self.filepath
        else:
            candidate = self.filepath / f"{sheet_key}.csv"

        if not candidate.exists():
            return []

        with candidate.open("r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            return [dict(row) for row in reader]
