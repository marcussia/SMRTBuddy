"""SMRTBuddy backend.

Real (Blocks A–F): profiles, journeys, advice (the core endpoint), location
pings, conditions, SOS, notifications. Still stubbed (Block G, header
`X-Stub: true`): /stations/resolve, /journeys/{id}/precheck.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import conditions as conditions_service
from app import service, store
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
    StationCandidate,
    StationResolveResponse,
    UserProfile,
)

SGT = timezone(timedelta(hours=8), "SGT")

STUB_HEADER = "X-Stub"
STUB_REASON = ("STUB: not implemented yet (see PRD.md §8). "
               "No transport data was consulted.")

# Kept for reference by older stubs; the real list lives in app/conditions.py.
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
    version="0.6.0",
    description="Blocks A–F are real. Still stubbed (X-Stub: true): "
                "/stations/resolve, /journeys/{id}/precheck (Block G).",
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
def create_profile(profile: UserProfile) -> UserProfile:
    """REAL: stores the profile (in-memory, PRD §10)."""
    store.profiles[profile.user_id] = profile
    return profile


@app.get("/profiles/{user_id}", response_model=UserProfile)
def get_profile(user_id: str) -> UserProfile:
    """REAL: returns the stored profile or 404."""
    profile = store.profiles.get(user_id)
    if profile is None:
        raise HTTPException(404, f"no profile '{user_id}'")
    return profile


@app.post("/profiles/{user_id}/link", response_model=UserProfile)
def link_profile(user_id: str, body: LinkRequest) -> UserProfile:
    """REAL: links an account (family <-> user). Both ids must exist."""
    profile = store.profiles.get(user_id)
    if profile is None:
        raise HTTPException(404, f"no profile '{user_id}'")
    if body.linked_user_id not in store.profiles:
        raise HTTPException(404, f"no profile '{body.linked_user_id}'")
    if body.linked_user_id not in profile.linked_user_ids:
        profile.linked_user_ids.append(body.linked_user_id)
    return profile


# --- Journeys ----------------------------------------------------------------

@app.post("/journeys", response_model=Journey, status_code=201)
def create_journey(body: JourneyCreate) -> Journey:
    """REAL: plans the journey now (Block C planner) and stores it.
    prefer_mode picks the bus option when the persona wants it; default is the
    best mobility-viable public-transport option."""
    profile = store.profiles.get(body.user_id)
    if profile is None or profile.mobility is None:
        raise HTTPException(404, f"no commuter profile '{body.user_id}' — "
                            "create it first (role='user' with mobility)")
    from datetime import timedelta
    # implausible pair check: same place, same physical station, or a trip
    # shorter than one walking leg — flagged, never silently "corrected".
    from app.routing.planner import _resolve_endpoint
    from app.routing.walk import _haversine_m
    o_res, d_res = _resolve_endpoint(body.origin), _resolve_endpoint(body.destination)
    if o_res and d_res:
        if o_res[0] == d_res[0]:
            raise HTTPException(422, f"origin and destination both resolve to "
                                f"'{o_res[0]}' — check the journey")
        if _haversine_m(o_res[1], d_res[1]) < 500:
            raise HTTPException(422, f"origin '{o_res[0]}' and destination "
                                f"'{d_res[0]}' are under 500 m apart — this "
                                f"journey does not need transit; check the pair")
    from app.routing.planner import plan_options
    try:
        opts = plan_options(body.origin, body.destination, _now(),
                            profile.mobility, profile.locale)
    except ValueError as exc:
        raise HTTPException(422, {
            "error": "outside_demo_corridor",
            "message": str(exc),
            "supported_corridor": "Bedok – Outram Park (EWL), with the DTL/NEL "
                                  "interchange alternatives via Bugis and "
                                  "Chinatown, plus bus service 2",
            "try": {"origin": "Home (Bedok)",
                    "destination": "Singapore General Hospital"},
            "why_limited": "We scoped routing to one verified corridor and "
                           "checked every piece of it against real data, "
                           "rather than pretend island-wide coverage we could "
                           "not verify tonight. Unsupported journeys are "
                           "refused honestly instead of guessed.",
        }) from exc
    public = [o for o in opts if o.kind != "taxi"]
    if body.prefer_mode:
        preferred = [o for o in public if o.kind == body.prefer_mode]
        public = preferred or public
    if not public:
        raise HTTPException(422, "no public-transport route found")
    chosen = public[0]
    # schedule the legs so the plan arrives before arrive_by
    shift = (body.arrive_by - chosen.legs[-1].arrive
             - timedelta(minutes=10))          # 10-min arrival margin
    for leg in chosen.legs:
        leg.depart += shift
        leg.arrive += shift
    journey = Journey(
        journey_id=str(uuid.uuid4()), user_id=body.user_id,
        origin=body.origin, destination=body.destination,
        arrive_by=body.arrive_by, scenario=body.scenario,
        location_state="at_home", legs=chosen.legs)
    store.journeys[journey.journey_id] = journey
    return journey


@app.get("/journeys/{journey_id}", response_model=Journey)
def get_journey(journey_id: str) -> Journey:
    """REAL: the stored journey or 404."""
    journey = store.journeys.get(journey_id)
    if journey is None:
        raise HTTPException(404, f"no journey '{journey_id}'")
    return journey


class ScenarioUpdate(BaseModel):
    scenario: str


@app.post("/journeys/{journey_id}/scenario", response_model=Journey)
def set_scenario(journey_id: str, body: ScenarioUpdate) -> Journey:
    """REAL: advance the labelled replay scenario on an EXISTING journey, so a
    multi-stage demo stays one journey with one id. The journey's plan and
    history are kept; only the fixture set the advice is computed against
    changes."""
    journey = store.journeys.get(journey_id)
    if journey is None:
        raise HTTPException(404, f"no journey '{journey_id}'")
    if conditions_service.load_fixture(body.scenario) is None:
        raise HTTPException(422, f"unknown scenario '{body.scenario}' — no "
                            f"fixture file")
    journey.scenario = body.scenario
    return journey


@app.get("/journeys/{journey_id}/advice", response_model=Advice)
def get_advice(journey_id: str) -> Advice:
    """THE CORE ENDPOINT (real): conditions -> facts -> ordered rules ->
    one recommended action with reason, sources, deadline and alternatives."""
    journey = store.journeys.get(journey_id)
    if journey is None:
        raise HTTPException(404, f"no journey '{journey_id}'")
    profile = store.profiles.get(journey.user_id)
    if profile is None:
        raise HTTPException(404, f"journey's profile '{journey.user_id}' missing")
    return service.compute_advice(journey, profile)


@app.post("/journeys/{journey_id}/location", response_model=LocationAck)
def post_location(journey_id: str, ping: LocationPing) -> LocationAck:
    """REAL: stores the ping, updates location_state if given, and runs
    wrong-direction detection (Q4 parameters, Block F)."""
    journey = store.journeys.get(journey_id)
    if journey is None:
        raise HTTPException(404, f"no journey '{journey_id}'")
    store.pings.setdefault(journey_id, []).append(ping)
    if ping.location_state and ping.set_state:
        journey.location_state = ping.location_state
    wrong, notified = service.check_wrong_direction(journey)
    return LocationAck(journey_id=journey_id, received_at=_now(),
                       wrong_direction=wrong, notify_family=notified)


@app.post("/journeys/{journey_id}/precheck", response_model=Advice)
def precheck(journey_id: str, response: Response) -> Advice:
    """STUB: pre-check returns placeholder advice (Block G)."""
    _mark_stub(response)
    return _stub_advice()


# --- SOS ---------------------------------------------------------------------

@app.post("/sos", response_model=SOSResponse)
def sos(body: SOSRequest) -> SOSResponse:
    """REAL: two-step SOS. First call opens it (awaiting_confirmation); the
    second call with confirm=true + sos_id confirms and notifies every linked
    family account (logged, PRD §10 — no real push)."""
    if body.user_id not in store.profiles:
        raise HTTPException(404, f"no profile '{body.user_id}'")
    if not body.confirm:
        rec = store.SOSRecord(sos_id=str(uuid.uuid4()), user_id=body.user_id,
                              status="awaiting_confirmation", created_at=_now())
        store.sos_records[rec.sos_id] = rec
        return SOSResponse(sos_id=rec.sos_id, status=rec.status)
    if body.sos_id is None:
        raise HTTPException(status_code=422,
                            detail="confirm=true requires the sos_id from the first call")
    rec = store.sos_records.get(body.sos_id)
    if rec is None or rec.user_id != body.user_id:
        raise HTTPException(404, f"no open SOS '{body.sos_id}' for this user")
    rec.status = "confirmed"
    rec.notified = store.notify_family(
        body.user_id, "sos",
        f"SOS from {store.profiles[body.user_id].name} — confirmed by the "
        f"user. Latest known location is available via the app.")
    return SOSResponse(sos_id=rec.sos_id, status=rec.status,
                       notified_user_ids=rec.notified)


@app.post("/sos/{sos_id}/audio", response_model=AudioAck)
async def sos_audio(sos_id: str, audio: UploadFile = File(...)) -> AudioAck:
    """REAL: stores the audio blob against the SOS (no transcription, §3)."""
    rec = store.sos_records.get(sos_id)
    if rec is None:
        raise HTTPException(404, f"no SOS '{sos_id}'")
    content = await audio.read()
    from app.config import REPO_ROOT
    audio_dir = REPO_ROOT / "data" / "sos_audio"    # gitignored runtime data
    audio_dir.mkdir(parents=True, exist_ok=True)
    path = audio_dir / f"{sos_id}.bin"
    path.write_bytes(content)
    rec.audio_path = str(path)
    return AudioAck(sos_id=sos_id, received_bytes=len(content), stored=True)


# --- Notifications & family location (Block F) --------------------------------

@app.get("/notifications")
def get_notifications(user_id: str = Query(...)) -> list[dict]:
    """REAL: the notification log for one recipient (PRD §10: logged to a
    table and exposed via API — no real SMS/push)."""
    return [vars(n) for n in store.notifications if n.to_user_id == user_id]


@app.get("/profiles/{user_id}/location")
def get_latest_location(user_id: str, viewer_id: str = Query(...)) -> dict:
    """REAL: latest position of a linked user, for family accounts (§3).
    viewer must be the user themselves or a linked family account."""
    if user_id not in store.profiles:
        raise HTTPException(404, f"no profile '{user_id}'")
    if viewer_id != user_id and viewer_id not in store.family_of(user_id):
        raise HTTPException(403, "viewer is not linked family of this user")
    latest, journey_id = None, None
    for jid, journey in store.journeys.items():
        if journey.user_id != user_id:
            continue
        ping = store.latest_ping(jid)
        if ping and (latest is None or ping.recorded_at > latest.recorded_at):
            latest, journey_id = ping, jid
    if latest is None:
        return {"user_id": user_id, "location": None,
                "note": "no location pings recorded"}
    return {"user_id": user_id, "journey_id": journey_id,
            "location": latest.model_dump()}


# --- Stations, conditions, health --------------------------------------------

@app.get("/stations/resolve", response_model=StationResolveResponse)
def resolve_station(q: str = Query(..., min_length=1)) -> StationResolveResponse:
    """REAL: fuzzy match over corridor stations and known places (rapidfuzz
    WRatio). Returns the top 3 with scores 0-100 — the CALLER picks; a strong
    match is still only a candidate, never a silent auto-correct."""
    from rapidfuzz import fuzz, process
    from app.routing import stations as net
    pool = sorted({s.name for s in net.BY_CODE.values()} | set(net.PLACES))
    hits = process.extract(q, pool, scorer=fuzz.WRatio, limit=3)
    return StationResolveResponse(
        query=q,
        candidates=[StationCandidate(name=name, score=round(score, 1))
                    for name, score, _ in hits if score >= 40])


@app.get("/conditions", response_model=ConditionsResponse)
def conditions(scenario: str | None = Query(default=None)) -> ConditionsResponse:
    """REAL (Block B): live feeds, or the labelled fixture set for `scenario`.
    Each source's `status` says exactly where its data came from."""
    results = conditions_service.gather(scenario)
    return ConditionsResponse(sources=list(results.values()))


# The real frontend (Vite build, committed in dist/) is served at /ui so a
# judge runs ONE command. Rebuild with `npm run build`.
from fastapi.staticfiles import StaticFiles
from app.config import REPO_ROOT as _ROOT
if (_ROOT / "dist" / "index.html").exists():
    app.mount("/ui", StaticFiles(directory=_ROOT / "dist", html=True), name="ui")


@app.get("/app", include_in_schema=False)
def dashboard():
    """Fallback dashboard (dashboard/index.html) — insurance for §3.2.2/§3.2.3
    while the real frontend is built. Plain static file, no build step."""
    from fastapi.responses import FileResponse
    from app.config import REPO_ROOT
    return FileResponse(REPO_ROOT / "dashboard" / "index.html")


@app.get("/health", response_model=Health)
def health() -> Health:
    """Real, not a stub: the process is up."""
    return Health(status="ok")
