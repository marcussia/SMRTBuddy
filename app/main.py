"""SMRTBuddy backend — Block A skeleton (PRD.md §8).

EVERY ENDPOINT EXCEPT /health IS A STUB. Stubs return correctly-shaped
responses so the frontend can build against them. They consult no data source,
persist nothing, and their values are placeholders, not transport data. Every
stub response carries the header `X-Stub: true`.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    Advice,
    AudioAck,
    ConditionsResponse,
    Health,
    Journey,
    JourneyCreate,
    Leg,
    LinkRequest,
    LocationAck,
    LocationPing,
    MobilityProfile,
    SOSRequest,
    SOSResponse,
    SourceResult,
    StationResolveResponse,
    UserProfile,
)

SGT = timezone(timedelta(hours=8), "SGT")

STUB_HEADER = "X-Stub"
STUB_REASON = ("STUB: not implemented yet (see PRD.md §8). "
               "No transport data was consulted.")

# Tier 1 sources from PRD.md §5. Names are placeholders until Block B.
TIER1_SOURCES = [
    "train_service_alerts",
    "weather",
    "crowd_density_realtime",
    "crowd_density_forecast",
    "bus_arrival",
    "taxi_availability",
    "taxi_stands",
]

app = FastAPI(
    title="SMRTBuddy backend",
    version="0.1.0-block-a",
    description="Block A: every endpoint except /health is a stub "
                "(response header `X-Stub: true`).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[STUB_HEADER],
)


def _now() -> datetime:
    return datetime.now(SGT)


def _mark_stub(response: Response) -> None:
    response.headers[STUB_HEADER] = "true"


def _stub_leg() -> Leg:
    now = _now()
    return Leg(
        mode="walk",
        from_name="STUB origin",
        to_name="STUB destination",
        depart=now,
        arrive=now,
        instruction="STUB: routing not built yet (PRD.md §8 Block C).",
        speech_text="Route not available yet.",
        i18n_key="stub.leg",
        shelter="exposed",
        step_free=False,
    )


def _stub_advice() -> Advice:
    now = _now()
    return Advice(
        action="proceed",
        headline="STUB: advice engine not built yet.",
        speech_text="Advice is not available yet.",
        reason=STUB_REASON,
        triggered_by=["stub"],
        eta_range=(now, now),
        confidence="low",
        notify_family=False,
        data_status={"stub": "unavailable"},
        legs=[_stub_leg()],
    )


def _stub_profile(user_id: str) -> UserProfile:
    return UserProfile(
        user_id=user_id,
        role="user",
        name="STUB profile (not persisted)",
        mobility=MobilityProfile(can_use_stairs=False, wheelchair=False),
    )


# --- Profiles ----------------------------------------------------------------

@app.post("/profiles", response_model=UserProfile, status_code=201)
def create_profile(profile: UserProfile, response: Response) -> UserProfile:
    """STUB: validates and echoes the profile back. Not persisted (Block F)."""
    _mark_stub(response)
    return profile


@app.get("/profiles/{user_id}", response_model=UserProfile)
def get_profile(user_id: str, response: Response) -> UserProfile:
    """STUB: returns a placeholder profile for any id (Block F)."""
    _mark_stub(response)
    return _stub_profile(user_id)


@app.post("/profiles/{user_id}/link", response_model=UserProfile)
def link_profile(user_id: str, body: LinkRequest, response: Response) -> UserProfile:
    """STUB: returns a placeholder profile showing the link. Not persisted (Block F)."""
    _mark_stub(response)
    profile = _stub_profile(user_id)
    profile.linked_user_ids = [body.linked_user_id]
    return profile


# --- Journeys ----------------------------------------------------------------

@app.post("/journeys", response_model=Journey, status_code=201)
def create_journey(body: JourneyCreate, response: Response) -> Journey:
    """STUB: echoes the request with a new id and one placeholder leg (Block C)."""
    _mark_stub(response)
    return Journey(
        journey_id=str(uuid.uuid4()),
        user_id=body.user_id,
        origin=body.origin,
        destination=body.destination,
        arrive_by=body.arrive_by,
        legs=[_stub_leg()],
    )


@app.get("/journeys/{journey_id}", response_model=Journey)
def get_journey(journey_id: str, response: Response) -> Journey:
    """STUB: returns a placeholder journey for any id (Block C)."""
    _mark_stub(response)
    return Journey(
        journey_id=journey_id,
        user_id="STUB user",
        origin="STUB origin",
        destination="STUB destination",
        arrive_by=_now(),
        legs=[_stub_leg()],
    )


@app.get("/journeys/{journey_id}/advice", response_model=Advice)
def get_advice(journey_id: str, response: Response) -> Advice:
    """THE CORE ENDPOINT. STUB until the rules engine exists (Blocks D–E)."""
    _mark_stub(response)
    return _stub_advice()


@app.post("/journeys/{journey_id}/location", response_model=LocationAck)
def post_location(journey_id: str, ping: LocationPing, response: Response) -> LocationAck:
    """STUB: accepts a ping; not stored, wrong-direction not evaluated (Block F)."""
    _mark_stub(response)
    return LocationAck(
        journey_id=journey_id,
        received_at=_now(),
        wrong_direction=False,
        notify_family=False,
    )


@app.post("/journeys/{journey_id}/precheck", response_model=Advice)
def precheck(journey_id: str, response: Response) -> Advice:
    """STUB: pre-check returns placeholder advice (Block G)."""
    _mark_stub(response)
    return _stub_advice()


# --- SOS ---------------------------------------------------------------------

@app.post("/sos", response_model=SOSResponse)
def sos(body: SOSRequest, response: Response) -> SOSResponse:
    """STUB: two-step confirmation shape only. Nobody is notified (Block F)."""
    _mark_stub(response)
    if not body.confirm:
        return SOSResponse(sos_id=str(uuid.uuid4()), status="awaiting_confirmation")
    if body.sos_id is None:
        raise HTTPException(status_code=422,
                            detail="confirm=true requires the sos_id from the first call")
    return SOSResponse(sos_id=body.sos_id, status="confirmed")


@app.post("/sos/{sos_id}/audio", response_model=AudioAck)
async def sos_audio(sos_id: str, response: Response,
                    audio: UploadFile = File(...)) -> AudioAck:
    """STUB: reads the upload to report its size; does not store it (Block F)."""
    _mark_stub(response)
    content = await audio.read()
    return AudioAck(sos_id=sos_id, received_bytes=len(content), stored=False)


# --- Stations, conditions, health --------------------------------------------

@app.get("/stations/resolve", response_model=StationResolveResponse)
def resolve_station(response: Response,
                    q: str = Query(..., min_length=1)) -> StationResolveResponse:
    """STUB: no station data is loaded yet, so no candidates (Block G)."""
    _mark_stub(response)
    return StationResolveResponse(query=q, candidates=[])


@app.get("/conditions", response_model=ConditionsResponse)
def conditions(response: Response) -> ConditionsResponse:
    """STUB: every Tier 1 source reports `unavailable` until Block B."""
    _mark_stub(response)
    now = _now()
    return ConditionsResponse(sources=[
        SourceResult(name=name, status="unavailable", fetched_at=now, data=None)
        for name in TIER1_SOURCES
    ])


@app.get("/health", response_model=Health)
def health() -> Health:
    """Real, not a stub: the process is up."""
    return Health(status="ok")
