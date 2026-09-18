"""In-memory stores (PRD §10: no auth beyond user_id, no real SMS/push —
notifications are logged to a table and exposed via the API). Process-lifetime
persistence is acceptable for the demo; stated in WRITEUP.md limitations."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from app.config import SGT
from app.models import Journey, LocationPing, UserProfile

profiles: dict[str, UserProfile] = {}
journeys: dict[str, Journey] = {}
pings: dict[str, list[LocationPing]] = {}


@dataclass
class Notification:
    notification_id: str
    to_user_id: str
    about_user_id: str
    journey_id: str | None
    event: str            # cancel_trip | take_taxi | reroute | sos | wrong_direction | precheck_change
    message: str
    created_at: datetime


notifications: list[Notification] = []


@dataclass
class SOSRecord:
    sos_id: str
    user_id: str
    status: Literal["awaiting_confirmation", "confirmed"]
    created_at: datetime
    audio_path: str | None = None
    notified: list[str] = field(default_factory=list)


sos_records: dict[str, SOSRecord] = {}


def family_of(user_id: str) -> list[str]:
    """Family accounts linked to this user, in either direction."""
    out = set()
    me = profiles.get(user_id)
    if me:
        for other_id in me.linked_user_ids:
            other = profiles.get(other_id)
            if other and other.role == "family":
                out.add(other_id)
    for other in profiles.values():
        if other.role == "family" and user_id in other.linked_user_ids:
            out.add(other.user_id)
    return sorted(out)


def notify_family(about_user_id: str, event: str, message: str,
                  journey_id: str | None = None) -> list[str]:
    """Log one notification per linked family account (§7.3). Returns the
    recipients — empty when nobody is linked, which is honest, not an error."""
    recipients = family_of(about_user_id)
    now = datetime.now(SGT)
    for to in recipients:
        notifications.append(Notification(
            notification_id=str(uuid.uuid4()), to_user_id=to,
            about_user_id=about_user_id, journey_id=journey_id,
            event=event, message=message, created_at=now))
    return recipients


def latest_ping(journey_id: str) -> LocationPing | None:
    lst = pings.get(journey_id) or []
    return lst[-1] if lst else None
