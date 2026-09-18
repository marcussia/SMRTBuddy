"""Data models.

SourceResult (PRD.md §4) and the four §6 models are transcribed from PRD.md.

Everything under "API request/response models" is PROVISIONAL: PRD.md §8 names
the endpoints but does not define their bodies. Those shapes are the minimum
needed to stub the endpoints, and are open for review before Block B.
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, model_validator


# --- PRD.md §4 ---------------------------------------------------------------

class SourceResult(BaseModel):
    name: str
    status: Literal["live", "cached", "fixture", "unavailable"]
    fetched_at: datetime
    data: Any


# --- PRD.md §6 ---------------------------------------------------------------

class MobilityProfile(BaseModel):
    can_use_stairs: bool
    wheelchair: bool
    walking_speed_mps: float = 0.8      # Q2: configurable, default 0.8
    max_walk_metres: int = 400          # Q2: wheelchair default is 200

    @model_validator(mode="after")
    def _wheelchair_walk_default(self) -> "MobilityProfile":
        # Q2: wheelchair defaults to 200 m unless explicitly set.
        if self.wheelchair and "max_walk_metres" not in self.model_fields_set:
            self.max_walk_metres = 200
        return self


class UserProfile(BaseModel):
    user_id: str
    role: Literal["user", "family"]
    name: str
    mobility: MobilityProfile | None = None   # REQUIRED when role == "user"
    linked_user_ids: list[str] = []
    locale: Literal["en", "zh", "ms", "ta"] = "en"

    @model_validator(mode="after")
    def _mobility_required_for_users(self) -> "UserProfile":
        if self.role == "user" and self.mobility is None:
            raise ValueError("mobility is required when role == 'user'")
        return self


class Leg(BaseModel):
    mode: Literal["walk", "bus", "mrt", "taxi"]
    from_name: str
    to_name: str
    service: str | None = None
    depart: datetime
    arrive: datetime
    instruction: str          # landmark-based
    speech_text: str          # short sentences for TTS
    i18n_key: str
    shelter: Literal["covered", "partial", "exposed"]
    step_free: bool
    geometry: list[tuple[float, float]] = []   # WGS84 (lat, lon) polyline
    crowding: Literal["low", "medium", "high"] | None = None


class Advice(BaseModel):
    action: Literal["proceed", "wait", "reroute", "leave_earlier",
                    "take_taxi", "cancel_trip"]
    headline: str             # ONE short sentence
    speech_text: str
    reason: str               # plain English, ALWAYS populated
    triggered_by: list[str]   # source names — auditable
    decide_by: datetime | None = None
    eta_range: tuple[datetime, datetime]
    confidence: Literal["high", "medium", "low"]
    notify_family: bool
    data_status: dict[str, str]
    legs: list[Leg] = []
    # The part of the ORIGINAL route the disruption hits, for map highlight.
    affected_segment: list[tuple[float, float]] | None = None
    # Other viable routes — transparency, secondary to the recommendation.
    alternatives: list[list[Leg]] = []
    # PRD §3/§7.6: returned with take_taxi. Optional model addition recorded
    # in STATUS.md (PRD names driver_card but defines no model for it).
    driver_card: "DriverCard | None" = None


class DriverCard(BaseModel):
    """Shown to a taxi driver: destination in English + Chinese, arrive-by."""
    destination_en: str
    destination_zh: str
    arrive_by: datetime


# --- API request/response models (PROVISIONAL — not defined in PRD.md) -------

# The five states listed in PRD.md §7.5.
LocationState = Literal["at_home", "walking", "on_bus", "on_train", "on_platform"]


class JourneyCreate(BaseModel):
    user_id: str
    origin: str               # station/place name within the demo corridor
    destination: str
    arrive_by: datetime
    # Selects a labelled fixture set from data/fixtures/ (PRD §9). None = live
    # feeds. Fixture-driven responses carry data_status = "fixture" — never
    # presented as live.
    scenario: str | None = None
    # Optional mode preference for the initial plan (e.g. scenario 2 starts on
    # the bus she prefers; the rain rule then swaps it). Provisional field.
    prefer_mode: Literal["rail", "bus"] | None = None


class Journey(BaseModel):
    journey_id: str
    user_id: str
    origin: str
    destination: str
    arrive_by: datetime
    scenario: str | None = None
    location_state: LocationState = "at_home"
    legs: list[Leg] = []


class LinkRequest(BaseModel):
    linked_user_id: str


class LocationPing(BaseModel):
    lat: float
    lon: float
    accuracy_m: float | None = None     # §7.4: suppress when accuracy is poor
    recorded_at: datetime
    location_state: LocationState | None = None


class LocationAck(BaseModel):
    journey_id: str
    received_at: datetime
    wrong_direction: bool               # §7.4
    notify_family: bool


class SOSRequest(BaseModel):
    """Two-step confirmation: call once without `confirm`, then again with
    `confirm: true` and the returned `sos_id`."""
    user_id: str
    sos_id: str | None = None
    confirm: bool = False


class SOSResponse(BaseModel):
    sos_id: str
    status: Literal["awaiting_confirmation", "confirmed"]
    notified_user_ids: list[str] = []


class AudioAck(BaseModel):
    sos_id: str
    received_bytes: int
    stored: bool


class StationCandidate(BaseModel):
    name: str
    score: float


class StationResolveResponse(BaseModel):
    query: str
    candidates: list[StationCandidate]  # top 3; never auto-selected (§8 G)


class ConditionsResponse(BaseModel):
    sources: list[SourceResult]


class Health(BaseModel):
    status: Literal["ok"]
