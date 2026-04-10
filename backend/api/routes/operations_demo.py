from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_role, require_role
from api.schemas import (
    AdminSettingsUpdateRequest,
    ApiResponse,
    Booking,
    CreateBookingRequest,
    CreateDispatchRequest,
    CreatePaymentRequest,
    CreateProfileRequest,
    DispatchAssignment,
    NotificationEvent,
    Payment,
    Profile,
    Role,
    SendNotificationRequest,
)
from api.store import store

logger = logging.getLogger("ryw.ops")

router = APIRouter(prefix="/api/v1", tags=["operations-demo"])


def _ops_audit(action: str, entity: str, entity_id: str, **extra: object) -> None:
    logger.info(json.dumps({"event": "ops_mutation", "action": action, "entity": entity, "entity_id": entity_id, **extra}))


def _push_in_app(message: str, recipient: str = "ops_console") -> None:
    event = NotificationEvent(
        id=store.next_id("notification"),
        channel="in_app",
        recipient=recipient,
        message=message,
        status="sent",
        created_at=store.now(),
    )
    store.notifications[event.id] = event


@router.get("/bookings", response_model=ApiResponse)
def list_bookings(role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data={"items": [b.model_dump() for b in store.bookings.values()]})


@router.post("/bookings", response_model=ApiResponse)
def create_booking(payload: CreateBookingRequest, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("ops", role)
    booking = Booking(
        id=store.next_id("booking"),
        rider_name=payload.rider_name,
        pickup=payload.pickup,
        dropoff=payload.dropoff,
        mode=payload.mode,
        created_at=store.now(),
    )
    store.bookings[booking.id] = booking
    _ops_audit("create", "booking", booking.id, rider_name=booking.rider_name, mode=booking.mode)
    _push_in_app(f"Booking {booking.id} created for {booking.rider_name} ({booking.pickup} → {booking.dropoff})")
    return ApiResponse(data={"item": booking.model_dump()})


@router.get("/dispatches", response_model=ApiResponse)
def list_dispatches(role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data={"items": [d.model_dump() for d in store.dispatches.values()]})


@router.get("/payments", response_model=ApiResponse)
def list_payments(role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data={"items": [p.model_dump() for p in store.payments.values()]})


@router.post("/dispatch", response_model=ApiResponse)
def create_dispatch(payload: CreateDispatchRequest, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("ops", role)
    booking_id = payload.booking_id
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    assignment = DispatchAssignment(
        id=store.next_id("dispatch"),
        booking_id=booking_id,
        driver_id=payload.driver_id,
        vehicle_id=payload.vehicle_id,
        created_at=store.now(),
    )
    store.dispatches[assignment.id] = assignment
    store.bookings[booking_id] = store.bookings[booking_id].model_copy(update={"status": "assigned"})
    _ops_audit(
        "create",
        "dispatch",
        assignment.id,
        booking_id=booking_id,
        driver_id=payload.driver_id,
        vehicle_id=payload.vehicle_id,
    )
    _push_in_app(
        f"Dispatch {assignment.id}: booking {booking_id} assigned to driver {payload.driver_id} / vehicle {payload.vehicle_id}"
    )
    return ApiResponse(data={"item": assignment.model_dump()})


@router.post("/payments", response_model=ApiResponse)
def create_payment(payload: CreatePaymentRequest, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("ops", role)
    booking_id = payload.booking_id
    if booking_id not in store.bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    payment = Payment(
        id=store.next_id("payment"),
        booking_id=booking_id,
        amount=payload.amount,
        currency=payload.currency,
        created_at=store.now(),
    )
    store.payments[payment.id] = payment
    _ops_audit(
        "create",
        "payment",
        payment.id,
        booking_id=booking_id,
        amount=str(payment.amount),
        currency=payment.currency,
    )
    _push_in_app(f"Payment {payment.id}: {payment.currency} {payment.amount} for booking {booking_id}")
    return ApiResponse(data={"item": payment.model_dump()})


@router.get("/profiles", response_model=ApiResponse)
def list_profiles(role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data={"items": [p.model_dump() for p in store.profiles.values()]})


@router.post("/profiles", response_model=ApiResponse)
def create_profile(payload: CreateProfileRequest, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("admin", role)
    profile = Profile(
        id=store.next_id("profile"),
        name=payload.name,
        email=payload.email,
        organization=payload.organization,
        role=payload.role,
        notification_opt_in=payload.notification_opt_in,
    )
    store.profiles[profile.id] = profile
    _ops_audit("create", "profile", profile.id, email=profile.email, role=profile.role)
    _push_in_app(f"Profile {profile.id} created: {profile.name} ({profile.email})", recipient="admin_console")
    return ApiResponse(data={"item": profile.model_dump()})


@router.get("/admin/settings", response_model=ApiResponse)
def get_settings_route(role: Role = Depends(get_role)) -> ApiResponse:
    require_role("admin", role)
    return ApiResponse(data={"settings": store.settings})


@router.put("/admin/settings", response_model=ApiResponse)
def update_settings(payload: AdminSettingsUpdateRequest, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("admin", role)
    store.settings.update(payload.root)
    _ops_audit("update", "admin_settings", "store", keys=list(payload.root.keys()))
    return ApiResponse(data={"settings": store.settings})


@router.get("/notifications", response_model=ApiResponse)
def list_notifications(role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data={"items": [n.model_dump() for n in store.notifications.values()]})


@router.post("/notifications", response_model=ApiResponse)
def send_notification(payload: SendNotificationRequest, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("ops", role)
    event = NotificationEvent(
        id=store.next_id("notification"),
        channel=payload.channel,
        recipient=payload.recipient,
        message=payload.message,
        status="sent",
        created_at=store.now(),
    )
    store.notifications[event.id] = event
    _ops_audit("send", "notification", event.id, channel=event.channel, recipient=event.recipient)
    return ApiResponse(data={"item": event.model_dump()})
