from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, RootModel


Role = Literal["admin", "ops", "analyst"]


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ApiResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[ErrorEnvelope] = None


class RegionGeographyIn(BaseModel):
    region_name: str
    state: str
    hospital_count: int = 0
    snf_count: int = 0
    clinic_count: int = 0
    competitor_count: int = 0
    total_population: int = 0
    elderly_population_pct: float = 0.0
    medicaid_eligible_pct: float = 0.0
    urban_rural_mix: str = "urban"
    service_area_sq_miles: float = 0.0
    avg_trip_distance_miles: float = 0.0


class FleetDeploymentIn(BaseModel):
    wheelchair_vehicles: int = 0
    ambulatory_vehicles: int = 0
    stretcher_vehicles: int = 0
    securecare_vehicles: int = 0
    drivers: int = 0


class ProspectiveContractIn(BaseModel):
    name: str
    contract_type: str
    estimated_daily_rides: float = 0.0
    estimated_revenue_per_trip: float = 0.0
    order_modes: List[str] = Field(default_factory=list)
    noshow_billing_tier: str = "snf"
    payer_name: Optional[str] = None


class MarketProfileIn(BaseModel):
    region: RegionGeographyIn
    fleet: FleetDeploymentIn
    overbooking_limit: float = 1.2
    projection_horizon: str = "quarter"
    broker_volume_pct: float = 0.30
    prospective_contracts: List[ProspectiveContractIn] = Field(default_factory=list)


class EvaluateRequest(BaseModel):
    market_profile: MarketProfileIn
    historical_data: Dict[str, Any] = Field(default_factory=dict)
    external_data: Optional[Dict[str, Any]] = None
    scenario_overrides: Optional[Dict[str, Any]] = None


class InferenceRequest(BaseModel):
    vehicle_utilization: float
    billed_utilization: float
    total_volume_pool: float
    revenue_per_kent_leg: float
    high_acuity_share: float
    non_billable_noshow: float
    road_hours_per_vehicle: float
    contract_concentration: float
    cost_per_road_hour: float


class Booking(BaseModel):
    id: str
    rider_name: str
    pickup: str
    dropoff: str
    mode: str
    status: Literal["created", "assigned", "in_progress", "completed", "cancelled"] = "created"
    created_at: datetime


class DispatchAssignment(BaseModel):
    id: str
    booking_id: str
    driver_id: str
    vehicle_id: str
    status: Literal["assigned", "acknowledged", "arrived", "completed"] = "assigned"
    created_at: datetime


class Payment(BaseModel):
    id: str
    booking_id: str
    amount: float
    currency: str = "USD"
    status: Literal["pending", "captured", "failed", "refunded"] = "pending"
    created_at: datetime


class Profile(BaseModel):
    id: str
    name: str
    email: str
    organization: str
    role: Role
    notification_opt_in: bool = True


class NotificationEvent(BaseModel):
    id: str
    channel: Literal["email", "sms", "in_app"]
    recipient: str
    message: str
    status: Literal["queued", "sent", "failed"] = "queued"
    created_at: datetime


# --- Operations demo (in-memory store) request bodies ---


class CreateBookingRequest(BaseModel):
    rider_name: str
    pickup: str
    dropoff: str
    mode: str = "ambulatory"


class CreateDispatchRequest(BaseModel):
    booking_id: str
    driver_id: str
    vehicle_id: str


class CreatePaymentRequest(BaseModel):
    booking_id: str
    amount: float = Field(gt=0)
    currency: str = "USD"


class CreateProfileRequest(BaseModel):
    name: str
    email: str
    organization: str = "Ride YourWay"
    role: Role = "analyst"
    notification_opt_in: bool = True


class SendNotificationRequest(BaseModel):
    recipient: str
    message: str
    channel: Literal["email", "sms", "in_app"] = "in_app"


class AdminSettingsUpdateRequest(RootModel[Dict[str, str]]):
    """JSON object of string settings keys to values (flat map)."""

    pass
