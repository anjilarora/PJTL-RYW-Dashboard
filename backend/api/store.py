from __future__ import annotations

from datetime import datetime, timezone
from itertools import count
from typing import Dict

from api.schemas import Booking, DispatchAssignment, NotificationEvent, Payment, Profile


class InMemoryStore:
    def __init__(self) -> None:
        self.bookings: Dict[str, Booking] = {}
        self.dispatches: Dict[str, DispatchAssignment] = {}
        self.payments: Dict[str, Payment] = {}
        self.profiles: Dict[str, Profile] = {}
        self.notifications: Dict[str, NotificationEvent] = {}
        self.settings: Dict[str, str] = {
            "default_timezone": "America/Detroit",
            "booking_auto_assign": "false",
            "payment_capture_mode": "manual",
        }
        self._seq = count(1)

    def next_id(self, prefix: str) -> str:
        return f"{prefix}_{next(self._seq)}"

    @staticmethod
    def now() -> datetime:
        return datetime.now(tz=timezone.utc)


store = InMemoryStore()
