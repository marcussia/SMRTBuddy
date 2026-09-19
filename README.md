# SMRTBuddy

A smart commuter companion for Singapore — built for NEBULA X 2026, **Problem
Statement 2**. It plans a door-to-door journey for an accessibility-constrained
commuter and, when something goes wrong mid-journey, **decides** what she should
do — one recommended action, one sentence of reason, a deadline on it — and
tells her family when it matters.

- **Live app:** <https://smrtbuddy-1057984221236.asia-southeast1.run.app/ui/>
  (`/ui` is the app, `/app` the fallback dashboard, `/docs` the API). Runs on
  Google Cloud Run in asia-southeast1. The link is in addition to the local
  instructions below, not a replacement.
- **Demo video:** [https://youtu.be/NeR-BKGk7sY](https://youtu.be/NeR-BKGk7sY)
- **Write-up:** [`WRITEUP.md`](WRITEUP.md)
- **API contract:** [`FRONTEND_CONTRACT.md`](FRONTEND_CONTRACT.md)

> **Status:** backend real through PRD Blocks A–F + station resolution;
> `POST /journeys/{id}/precheck` is still a stub (marked `X-Stub: true`).
> The frontend at `/ui` is wired to the live API end to end: profile setup,
> planning, advice with an OSM route map, guidance from real legs, wrong-way,
> SOS, and the three-stage demo (labelled "Simulated disruption for
> demonstration"). The full six-scenario set lives on the fallback dashboard
> at `/app`. Static content (family views, recording upload) says so on
> screen. Build log with every assumption: [`STATUS.md`](STATUS.md).

---

## Run it (clean machine)

### Prerequisites

- **Python 3.11+** (developed and tested on 3.13; 3.10 will not work)
- `pip` (bundled with Python), internet access
- An **LTA DataMall AccountKey** — free, register at
  <https://datamall.lta.gov.sg> (the app starts without one, but every
  DataMall source will honestly report `unavailable`; the six demo scenarios
  work regardless because they run on labelled fixtures)

### Install and run

```bash
git clone https://github.com/marcussia/smrtbuddy.git
cd smrtbuddy
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # then put your DataMall key in .env
.venv/bin/uvicorn app.main:app --port 8000
```

Then open, on a phone browser on the same network or on the machine itself:

- **<http://127.0.0.1:8000/ui/>** — the app (prebuilt frontend, committed in
  `dist/`; no npm needed). Tap through: language → profile → "I am travelling"
  → profile setup → Show my journey. Use the three stage buttons on the
  journey screen to run the demo (one journey, three escalating events); the
  same journey gets a different recommendation each time, live from the
  engine. The six individual scenarios are on the fallback dashboard below.
- <http://127.0.0.1:8000/app> — the plain fallback view (Leaflet map, same API)
- <http://127.0.0.1:8000/docs> — interactive API docs

Health check: `curl http://127.0.0.1:8000/health` → `{"status":"ok"}`.

**Rebuilding the frontend** (only needed if you change `src/`): Node 20+, then
`npm install && npm run build` — the output in `dist/` is what `/ui` serves.
Dependencies are pinned to exact versions.

### Configuration

`.env` at the repo root (never committed; `.env.example` lists the names):

| Variable | Purpose |
|---|---|
| `LTA_DATAMALL_KEY` | LTA DataMall AccountKey (free registration, link above) |

data.gov.sg weather and OSM foot routing need no key.

## What to try first — the demo journey

Mdm Lim (accessibility-constrained persona from the brief): Bedok →
Singapore General Hospital, mid-journey EWL disruption while she is on the
train. Paste these in order:

```bash
BASE=http://127.0.0.1:8000

# 1. Her profile, her daughter's, and the link between them
curl -s -X POST $BASE/profiles -H 'Content-Type: application/json' -d '{
  "user_id": "mdm_lim", "role": "user", "name": "Mdm Lim", "locale": "en",
  "mobility": {"can_use_stairs": false, "wheelchair": false,
               "walking_speed_mps": 0.8, "max_walk_metres": 600}}'
curl -s -X POST $BASE/profiles -H 'Content-Type: application/json' \
  -d '{"user_id": "daughter", "role": "family", "name": "Hui Ling"}'
curl -s -X POST $BASE/profiles/daughter/link \
  -H 'Content-Type: application/json' -d '{"linked_user_id": "mdm_lim"}'

# 2. The journey, on the disruption fixture (labelled test data — see below)
JID=$(curl -s -X POST $BASE/journeys -H 'Content-Type: application/json' -d '{
  "user_id": "mdm_lim", "origin": "Home (Bedok)",
  "destination": "Singapore General Hospital",
  "arrive_by": "2026-09-19T10:00:00+08:00",
  "scenario": "disruption_on_train"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["journey_id"])')

# 3. She is on the train, just past Paya Lebar
curl -s -X POST $BASE/journeys/$JID/location -H 'Content-Type: application/json' -d '{
  "lat": 1.3178, "lon": 103.8927, "accuracy_m": 25,
  "recorded_at": "2026-09-19T08:40:00+08:00",
  "location_state": "on_train", "set_state": true}'

# 4. THE CORE CALL — what should she do, right now?
curl -s $BASE/journeys/$JID/advice | python3 -m json.tool
```

Expected: `action: "reroute"`, headline **"Get off at Bugis, then take the
Downtown line…"**, a `decide_by` deadline (her arrival at Bugis), the closed
stations in `affected_segment` for the map, `notify_family: true` (check
`curl "$BASE/notifications?user_id=daughter"`), and a `data_status` block that
says exactly which sources were fixture vs live.

## The six demo scenarios

Every scenario runs through the real rules engine on a **labelled fixture**
(`data/fixtures/<name>.json`, each bannered `_fixture: true`; the API reports
those sources as `"fixture"`, never as live — the feeds are quiet most days, so
the brief explicitly allows labelled replay). Create the journey with the
`scenario` field; omit it for live feeds. Ready-to-paste commands for all six
are in [`FRONTEND_CONTRACT.md`](FRONTEND_CONTRACT.md). In the browser, the
fallback dashboard at `/app` has buttons for all six plus the three demo
stages; the React app at `/ui` drives the three stages.

| `scenario` | Expected advice |
|---|---|
| `clear_day` | `proceed` — no interruption, no family notification |
| `rain` (create with `"prefer_mode": "bus"`) | `reroute` — bus swapped for MRT, shelter reasoning, road buffer |
| `disruption_on_train` | `reroute` — alight guidance, deadline, family notified |
| `lift_outage` (use a wheelchair profile) | `take_taxi` — with EN/中文 driver card |
| `flood_destination` | `cancel_trip` — family notified |
| `crowding_forecast` | `leave_earlier` — 20 min, deliberately no notification |

## How it decides

`GET /journeys/{id}/advice` runs: gather sources (truthful `live` /
`fixture` / `unavailable` per source) → typed facts → **nine ordered rules**
(`app/engine/rules.py`, first match wins: safety stop, mobility block, broken
route, wait-vs-reroute, platform crowding, bus crowding, weather, road
conditions, default) → localised advice. Every response carries `reason` (plain
English) and `triggered_by` (the exact sources) — a recommendation that cannot
name its source is treated as a bug.

## Data sources

| Source | Used for | Key |
|---|---|---|
| LTA DataMall `TrainServiceAlerts` | disruptions + LTA's own mitigation (free bus/shuttle) | AccountKey |
| DataMall `PCDRealTime` / `PCDForecast` | station crowding, now and forecast | AccountKey |
| DataMall `v2/FacilitiesMaintenance` | lift outages per station | AccountKey |
| DataMall `PubFloodAlerts`, `TrafficIncidents`, `v3/BusArrival`, `Taxi-Availability`, `TaxiStands` | floods, road incidents, bus loads, taxi supply | AccountKey |
| data.gov.sg two-hour forecast | rain on the route | none |
| **OpenStreetMap** (FOSSGIS foot-profile OSRM) | real pedestrian routing for every walk leg | none |
| **OSM Overpass** (captured) | steps, lifts and wheelchair tags for step-free status: `data/replay/` | none |
| Organisers' station GeoJSON (this repo) | station geometry (WGS84, verified) | — |
| DataMall BusRoutes/BusStops (captured) | the verified bus 2 alternative — `data/replay/` | — |

Line codes are canonicalised through one table (`app/engine/facts.py`) because
the same line is coded differently across DataMall endpoints.

## Attribution

Map and routing data © [OpenStreetMap](https://www.openstreetmap.org/copyright)
contributors, licensed under the [ODbL](https://opendatacommons.org/licenses/odbl/).
This attribution must also appear wherever the frontend shows the map or
anything derived from it — a licence condition, not a style point.
Public transport data from [LTA DataMall](https://datamall.lta.gov.sg); weather
from [data.gov.sg](https://data.gov.sg); geocoding by OSM Nominatim.

## Honesty guarantees

- **No fabricated transport data.** An unreachable API reports
  `unavailable` with the error; fixtures are labelled `fixture` end to end.
- **No silent auto-correction.** `GET /stations/resolve?q=` returns top-3
  candidates with scores; implausible origin/destination pairs are rejected
  with a clear 422, never "fixed".
- Assumptions (timing constants, area mappings, the assumed delay when a line
  reports Status 2) are named constants in `app/config.py` and listed in
  [`STATUS.md`](STATUS.md).

## Submission checklist (from PS2/submission/README.md §7)

- [x] Cloned into a fresh directory and followed this README; it runs (done twice, including keyless)
- [x] No credentials in the repository or its history (checked against git history)
- [x] `.env.example` lists every variable the app needs
- [x] `WRITEUP.md` names the persona we built for
- [x] Any number in `WRITEUP.md` says how we arrived at it
- [ ] The demo recording is linked and plays
- [x] The app has been opened on a real phone browser, not just devtools emulation
      (tested `/ui` on an iPhone over a hotspot: fast first load, demo path works —
      the judge setup is the same shape, server on their machine and phone on the
      same network, so first-load size is not a concern for judging)

## Repo layout

```
app/            backend (FastAPI): adapters, routing, engine, service, store
data/fixtures/  labelled per-scenario test data (committed)
data/replay/    captured real API data with provenance (committed)
tools/          fixture generator
archive/        earlier PS3 work — not part of this submission
```
