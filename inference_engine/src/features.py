"""
KPI and feature engineering aligned to `knowledge-base/phase-2-formula-cards.md`.

Tier notes:
- Tier 1: canonical formula when inputs exist.
- Tier 2: explicit alternate branch (e.g. Kent divisor, non-billable denominator).
- Tier 3 / insufficient: NaN with reason column (caller imputes or drops).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def kent_legs_from_miles_canonical(trip_miles: pd.Series | float) -> pd.Series:
    """((trip_miles - 8) / 23) + 1, floored at 1 (integer Kent legs)."""
    m = pd.to_numeric(pd.Series(trip_miles), errors="coerce")
    raw = (m - 8.0) / 23.0 + 1.0
    legs = np.floor(raw)
    return pd.Series(np.maximum(1, legs), index=m.index, dtype="float64")


def kent_legs_from_miles_alternate(trip_miles: pd.Series | float, divisor: float = 8.5) -> pd.Series:
    """Alternate branch: miles / divisor (Tier 2 proxy)."""
    m = pd.to_numeric(pd.Series(trip_miles), errors="coerce")
    return np.maximum(1.0, m / divisor)


def non_billable_rate_denominator_completed(
    completed: pd.Series, billed_ns: pd.Series, non_bill_ns: pd.Series
) -> pd.Series:
    """non_billable / (completed + billable + non_billable) — Tier 2 branch when counts exist."""
    c = pd.to_numeric(completed, errors="coerce").fillna(0)
    b = pd.to_numeric(billed_ns, errors="coerce").fillna(0)
    n = pd.to_numeric(non_bill_ns, errors="coerce").fillna(0)
    den = c + b + n
    return np.where(den > 0, n / den, np.nan)


def operating_margin(revenue: pd.Series, cost: pd.Series) -> pd.Series:
    """(revenue - cost) / revenue with guard."""
    rev = pd.to_numeric(revenue, errors="coerce")
    cst = pd.to_numeric(cost, errors="coerce")
    return np.where(rev > 0, (rev - cst) / rev, np.nan)


def revenue_per_kent_leg(total_revenue: pd.Series, completed_kent_legs: pd.Series) -> pd.Series:
    legs = pd.to_numeric(completed_kent_legs, errors="coerce")
    rev = pd.to_numeric(total_revenue, errors="coerce")
    return np.where(legs > 0, rev / legs, np.nan)


def build_mode_summary_week_features(mode_summary: pd.DataFrame) -> pd.DataFrame:
    """Aggregate mode_summary_base to week × order_mode for Completed trips."""
    ms = mode_summary.copy()
    ms = ms[ms["order_status"].astype(str) == "Completed"]
    if ms.empty:
        return pd.DataFrame()

    g = ms.groupby(["week_normalized", "order_mode"], as_index=False).agg(
        sum_order_price=("sum_order_price", "sum"),
        sum_kent_legs=("sum_kent_legs", "sum"),
        sum_order_mileage=("sum_order_mileage", "sum"),
        completed_count=("completed_count", "sum"),
        billed_no_show_count=("billed_no_show_count", "sum"),
        non_billable_no_show_count=("non_billable_no_show_count", "sum"),
    )
    g["revenue_per_kent_leg"] = revenue_per_kent_leg(g["sum_order_price"], g["sum_kent_legs"])
    g["non_billable_rate_completed_branch"] = non_billable_rate_denominator_completed(
        g["completed_count"], g["billed_no_show_count"], g["non_billable_no_show_count"]
    )
    # Aggregate-mile diagnostic: compare summed reported legs vs canonical reconstruction from summed miles
    g["kent_leg_recon_delta"] = g["sum_kent_legs"] - kent_legs_from_miles_canonical(g["sum_order_mileage"])
    return g


def build_vehicle_week_features(vehicle_day: pd.DataFrame) -> pd.DataFrame:
    vd = vehicle_day.copy()
    g = vd.groupby("week_normalized", as_index=False).agg(
        vehicle_rows=("vehicle", "count"),
        total_road_hours=("road_time", "sum"),
        total_kent_legs=("kent_legs", "sum"),
        total_revenue=("revenue", "sum"),
        total_mileage=("mileage", "sum"),
    )
    g["road_hours_per_vehicle_row"] = np.where(
        g["vehicle_rows"] > 0, g["total_road_hours"] / g["vehicle_rows"], np.nan
    )
    g["revenue_per_kent_leg_vehicle_grain"] = revenue_per_kent_leg(
        g["total_revenue"], g["total_kent_legs"]
    )
    g["kent_legs_per_road_hour"] = np.where(
        g["total_road_hours"] > 0, g["total_kent_legs"] / g["total_road_hours"], np.nan
    )
    return g


def build_weekly_margin_quarter_slice(weekly_margin: pd.DataFrame) -> pd.DataFrame:
    wm = weekly_margin.copy()
    if "scope_level" in wm.columns:
        # Prefer week-level rows (quarter_total often lacks week_normalized in this extract)
        week_rows = wm[wm["scope_level"].astype(str) == "week"]
        if not week_rows.empty and week_rows["week_normalized"].notna().any():
            wm = week_rows
        else:
            wm = wm[wm["scope_level"].astype(str) == "quarter_total"]
    if wm.empty:
        return pd.DataFrame(columns=["week_normalized", "total_revenue", "total_cost", "profit_margin"])
    agg_map: dict[str, str] = {}
    if "total_revenue" in wm.columns:
        agg_map["total_revenue"] = "sum"
    if "total_cost" in wm.columns:
        agg_map["total_cost"] = "sum"
    if "profit_margin" in wm.columns:
        agg_map["profit_margin"] = "mean"
    if not agg_map:
        return pd.DataFrame(columns=["week_normalized"])
    return wm.groupby("week_normalized", as_index=False).agg(agg_map)


def payer_concentration_by_week(payer_summary: pd.DataFrame) -> pd.DataFrame:
    """max payer share of completed revenue by week (Tier 2 contract concentration proxy)."""
    ps = payer_summary.copy()
    ps = ps[ps["order_status"].astype(str) == "Completed"]
    if ps.empty:
        return pd.DataFrame(columns=["week_normalized", "contract_concentration_revenue"])

    rev_by = ps.groupby(["week_normalized", "payer_id"], as_index=False)["sum_order_price"].sum()
    week_tot = rev_by.groupby("week_normalized", as_index=False)["sum_order_price"].transform("sum")
    rev_by["share"] = np.where(week_tot > 0, rev_by["sum_order_price"] / week_tot, np.nan)
    out = rev_by.groupby("week_normalized", as_index=False)["share"].max()
    out = out.rename(columns={"share": "contract_concentration_revenue"})
    return out


def merge_weekly_analytic_frame(
    mode_week: pd.DataFrame,
    vehicle_week: pd.DataFrame,
    margin_slice: pd.DataFrame,
    concentration: pd.DataFrame,
) -> pd.DataFrame:
    """Merge on week_normalized; mode_week may be long (week × mode)."""
    base = mode_week.merge(vehicle_week, on="week_normalized", how="outer", suffixes=("", "_veh"))
    base = base.merge(
        margin_slice.drop_duplicates(subset=["week_normalized"], keep="first"),
        on="week_normalized",
        how="left",
    )
    base = base.merge(concentration, on="week_normalized", how="left")
    return base


def derive_supervised_proxy_label(df: pd.DataFrame, margin_col: str = "profit_margin") -> pd.Series:
    """
    Binary proxy for modeling: 1 if margin at or above median (within notebook slice).
    Documented as **analysis-only** — not a business readiness gate.
    """
    m = pd.to_numeric(df[margin_col], errors="coerce")
    med = m.median(skipna=True)
    if np.isnan(med):
        return pd.Series(np.nan, index=df.index)
    return (m >= med).astype(int)


def build_ml_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Numeric columns for sklearn; drops identifiers."""
    id_cols = {"week_normalized", "order_mode", "day"}
    feature_cols = [
        c
        for c in df.columns
        if c not in id_cols
        and pd.api.types.is_numeric_dtype(df[c])
        and df[c].notna().sum() > 0
    ]
    # Prefer stable subset if present
    preferred = [
        "revenue_per_kent_leg",
        "non_billable_rate_completed_branch",
        "road_hours_per_vehicle_row",
        "kent_legs_per_road_hour",
        "contract_concentration_revenue",
        "profit_margin",
        "sum_kent_legs",
        "sum_order_price",
    ]
    ordered = [c for c in preferred if c in feature_cols]
    rest = [c for c in feature_cols if c not in ordered]
    use_cols = ordered + rest
    X = df[use_cols].copy()
    return X, use_cols
