# SMRTBuddy — PS2 Backend PRD (v2)

**Scope: backend only.** UI/UX is owned separately and will connect to these APIs.
Where this document and the organisers' brief disagree, THE BRIEF WINS — flag it,
don't guess.

## 1. Verified requirements

### Deliverables — all in one repository
| # | Deliverable | Form |
|---|---|---|
| 1 | The app | Source repo, runnable from the README |
| 2 | Write-up | WRITEUP.md at repo root |
| 3 | Demo | A recording, linked from the README |

Plus .env.example listing variable NAMES only.

No machine-scored output files. This is judged as a product.
Hosting is NOT required — only "runnable from the README on a clean machine".
Demo: one real journey, end to end, one persona. Five minutes is plenty.

### Judging — weights disclosed
| Criterion | Weight | Rewards |
|---|---|---|
| Problem Fit | 40% | Would a real commuter be better off? Persona fit, proactivity, quality of what it offers |
| Technical Execution | 35% | The build itself |
| Ease of Use | 25% | Usability, clarity |

Problem Fit is the largest criterion and it is not about code. A working narrow
app that visibly helps Mdm Lim beats a broad one that doesn't.

### Persona — use the brief's language
The brief describes Mdm Lim as ACCESSIBILITY-CONSTRAINED. The word "elderly"
appears nowhere in the PS2 documents. Write all code comments, WRITEUP.md and
the demo script in terms of accessibility needs, not age.

## 2. What we are building

A journey companion that gets an accessibility-constrained commuter door to door,
and when a disruption happens, DECIDES what she should do and tells her in terms
she can act on.

Core question the backend answers:
> Given where she is, where she's going, when she must arrive, her mobility
> profile, and everything known about the network and weather — what should she
> do in the next few minutes, and who needs to be told?

She does not make the decision. The app does. One recommended action, one
sentence of reason, a deadline on it. Alternatives exist in the response but are
secondary.

The objective is NOT "fastest route". Rerouting costs an accessibility-constrained
commuter more than a fast one. A marginal time saving does not justify a reroute.
Some disruptions mean "don't travel today".

## 3. Backend vs frontend

NOT backend, do not build: font size, brightness, contrast, disabling zoom,
text-to-speech playback, image-over-text layout.

Backend provides instead:
- Every user-facing string carries i18n_key + resolved text in profile locale
- Separate speech_text field — short sentences, no abbreviations or symbols
- instruction strings referencing landmarks ("turn left after the lift")
- SOS endpoint with two-step confirmation; accept audio blob, store it, NO transcription
- Location pings; latest position exposed to linked family accounts
- Taxi driver_card: destination in English + Chinese, arrive-by time
- All walk legs computed at profile.walking_speed_mps

## 4. Data reality

PS2/data/ is nearly empty: a station-footprint GeoJSON (2017, coordinate system
unstated — VERIFY BEFORE TRUSTING COORDINATES) and a links text file. The weather
JSONs in PS2/references/ are API specs, not data.

- data.gov.sg weather: works, no key needed. Use live.
- LTA DataMall: key now in .env. Use live.

Every adapter declares provenance:

class SourceResult(BaseModel):
    name: str
    status: Literal["live", "cached", "fixture", "unavailable"]
    fetched_at: datetime
    data: Any

status must be truthful and surface in every API response. If we demo on
fixtures, the response says fixture.

## 5. Data sources by priority

TIER 1: train service alerts (load-bearing) · weather/rain · platform crowd
density real-time + forecast · bus arrival + crowding · taxi availability + stands

TIER 2: lift maintenance (HARD CONSTRAINT if wheelchair or no stairs) · flood
alerts (localised → reroute; widespread or at origin/destination → cancel trip) ·
road speed bands · live accidents · roadworks · traffic advisories · new/changed
bus routes

TIER 3 (only if 1 and 2 done): geospatial layers (covered linkways, footpaths,
station exits, stop locations) · historical passenger volume by OD pair · network
reference data

IGNORE: expressway travel times.

## 6. Data models

class MobilityProfile(BaseModel):
    can_use_stairs: bool
    wheelchair: bool
    walking_speed_mps: float = 0.8
    max_walk_metres: int = 400

class UserProfile(BaseModel):
    user_id: str
    role: Literal["user", "family"]
    name: str
    mobility: MobilityProfile | None = None   # REQUIRED when role == "user"
    linked_user_ids: list[str] = []
    locale: Literal["en", "zh", "ms", "ta"] = "en"

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

reason and triggered_by are MANDATORY on every Advice. If the engine cannot name
the source that triggered a recommendation, that is a bug.

## 7. Decision logic

Explicit ordered rules engine in app/engine/rules.py. Not scattered conditionals.
Each rule is a named function whose docstring states its trigger and rationale.
First match wins for action.

1. SAFETY STOP — widespread flood, or flood at origin/destination
   → cancel_trip, notify_family
2. HARD MOBILITY BLOCK — lift out of service on route AND (wheelchair OR cannot
   use stairs) → reroute avoiding it; if no step-free alternative → take_taxi
3. ROUTE BROKEN — service alert or closure makes a leg impossible → reroute;
   if no viable public transport → take_taxi
4. WAIT vs REROUTE — see 7.2
5. PLATFORM CROWDING — above threshold → not departed: leave_earlier or
   alternative line; in transit: alternative line if one exists
6. BUS CROWDING — crowded + not departed + slack allows → wait for next bus
7. WEATHER — rain → prefer MRT over bus; shelter becomes required; buffer road legs
8. ROAD CONDITIONS — slow bands / accident / roadworks on a bus leg →
   leave_earlier or rail
9. DEFAULT → proceed

### 7.2 Wait vs reroute

T_wait   = arrival if she stays on the current plan
T_switch = arrival if she switches now (INCLUDES walking at HER speed + transfer)

WAIT if T_wait <= T_switch OR (T_wait - T_switch) < REROUTE_BENEFIT_THRESHOLD_MIN
REROUTE only if meaningfully faster AND walk within max_walk_metres AND step-free
if mobility requires it.

State the rationale in reason. REROUTE_BENEFIT_THRESHOLD_MIN is one named constant.

### 7.3 Family notification
Notify: cancel_trip, take_taxi, reroute, SOS, wrong-direction, route changed at
pre-check. Do NOT notify: minor delays, crowding advice, proceed, leave_earlier.
Notification fatigue makes real alerts worthless.

### 7.4 Wrong-direction detection
Sustained divergence from the next expected waypoint across N consecutive pings
→ alert + notify family. Do not over-trigger. GPS is noisy underground. Suppress
when accuracy is poor or she is stationary.

### 7.5 Location context changes the instruction
at_home → change the plan, leave earlier or later
walking → redirect to a different stop
on_bus → which stop to alight at
on_train → which station to alight at, and what to do there
on_platform → stay put, or move
Same disruption, different instruction in each state. Hard requirement.

### 7.6 Taxi is last resort
Only when no public transport option exists or mobility blocks all of them.
Nearest stand, prefer higher supply, return driver_card, notify family.

## 8. Build order

A (1.5h) FastAPI skeleton, all §6 models, all endpoints returning correctly-shaped
        stubs, CORS on. FRONTEND UNBLOCKS HERE — this is the gate.
B (2.0h) Adapters + fixtures for Tier 1. Weather and DataMall live.
C (3.0h) Routing: journey → legs at profile walking speed. SEE OPEN Q1 — ASK FIRST.
D (3.0h) Engine §7.1–7.2. Rules 1, 3, 4, 9 first.
E (1.5h) Remaining rules 2, 5, 6, 7, 8.
F (1.0h) Profiles, SOS, location ping, notification log.
G (1.0h) Station resolution (fuzzy, top-3 candidates, NEVER silent auto-correct),
        pre-check endpoint.
H (1.0h) Six demo scenarios end to end through the real engine.
I (1.0h) Buffer, README run instructions, .env.example.

API surface:
POST /profiles · GET /profiles/{id} · POST /profiles/{id}/link
POST /journeys · GET /journeys/{id}
GET  /journeys/{id}/advice          ← THE CORE ENDPOINT
POST /journeys/{id}/location
POST /journeys/{id}/precheck
POST /sos · POST /sos/{id}/audio
GET  /stations/resolve?q=...
GET  /conditions · GET /health

## 9. Demo scenarios — fixtures required

Each must run END TO END THROUGH THE REAL ENGINE on fixture data. No hardcoded
demo responses — change an input, the output must change.

1. Clear day → proceed, no family notification
2. Rain → bus leg swapped for MRT, shelter required, buffer added
3. Disruption mid-journey, location_state = on_train → which station to alight
   at, alternative given, family notified
4. Lift out of service, wheelchair profile → different exit, or taxi if none
5. Flood at destination → cancel_trip, family notified
6. Crowding forecast, not departed → leave_earlier

Scenario 3 is the demo. Build it first and make it good.

## 10. Not building

Frontend or styling · real SMS/push (log to a table, expose via API) · speech
synthesis or recognition · transcription · auth beyond a user_id · fares or
ticketing · streaming (polling is fine) · ML models · deployment infrastructure.

## 11. OPEN QUESTIONS — ask before implementing

Q1. ROUTING APPROACH. A multimodal router from scratch is not feasible tonight.
    Options: (a) hand-built graph covering only the demo corridor, (b) static
    timetable data if any exists, (c) an external routing API if permitted.
    BLOCKING FOR BLOCK C — ASK, DO NOT GUESS.
Q2. Walking speed default — 0.8 m/s. Configurable at signup or fixed?
Q3. REROUTE_BENEFIT_THRESHOLD_MIN — suggest 10 minutes; confirm.
Q4. Wrong-direction sensitivity — suggest 3 consecutive divergent pings over 90s
    with good accuracy; confirm.
Q5. Crowd density threshold — which band is the cutoff?
Q6. Languages — all four for the demo, or English plus one?
Q7. Station GeoJSON coordinate system — unstated, dated 2017. Verify before
    trusting any coordinate.

## 12. Success at 14:00

- GET /journeys/{id}/advice returns a complete, explained Advice for all six
  scenarios
- Every response carries reason, triggered_by, and honest data_status
- The frontend can call every endpoint and get valid shapes
- README lets a judge run it on a clean machine
- Nothing in the codebase fabricates transport data

If Tier 2 and 3 are unfinished, fine. If the advice endpoint doesn't work,
nothing else matters.
