from __future__ import annotations

import csv
from pathlib import Path

import pytest

from engine.input_layer.phase1_bridge import phase1_csv_dir_to_historical_data


def test_phase1_bridge_builds_historical(tmp_path: Path) -> None:
    d = tmp_path / "phase1"
    d.mkdir()
    with (d / "contract_volume_base.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["payer_id", "order_mode", "order_status", "kent_legs", "order_price"],
        )
        w.writeheader()
        w.writerow(
            {
                "payer_id": "A",
                "order_mode": "Ambulatory",
                "order_status": "Completed",
                "kent_legs": "10",
                "order_price": "100",
            }
        )
        w.writerow(
            {
                "payer_id": "B",
                "order_mode": "Wheelchair",
                "order_status": "No show",
                "kent_legs": "2",
                "order_price": "0",
            }
        )
    with (d / "vehicle_day_base.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["date_iso", "road_time", "kent_legs", "revenue", "mode"],
        )
        w.writeheader()
        w.writerow(
            {
                "date_iso": "2025-01-01",
                "road_time": "8",
                "kent_legs": "5",
                "revenue": "300",
                "mode": "Wheelchair",
            }
        )
    with (d / "mode_breakdown_base.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["order_mode", "kent_legs", "order_price", "trip_count"],
        )
        w.writeheader()
        w.writerow({"order_mode": "Ambulatory", "kent_legs": "8", "order_price": "400", "trip_count": "1"})

    historical = phase1_csv_dir_to_historical_data(d)
    assert "baselines" in historical
    assert "contracts" in historical
    assert "cost_assumptions" in historical
    assert "revenue_by_mode" in historical
    assert historical["baselines"].get("daily_kent_legs", 0) > 0


def test_phase1_bridge_requires_core_csvs(tmp_path: Path) -> None:
    d = tmp_path / "empty"
    d.mkdir()
    with pytest.raises(FileNotFoundError):
        phase1_csv_dir_to_historical_data(d)
