# SMRTBuddy — Write-up

**Team SMRTBuddy** · NEBULA X Problem Statement 2
Repo: `github.com/marcussia/SMRTBuddy` · Demo: `[FILL: video link]`

---

## 1. The persona we built for

We built for Mdm Lim, the accessibility-constrained commuter in the brief.

The question we kept coming back to: when something goes wrong mid-journey, what does she actually need? A decision. Not more information.

In the chaos of a service disruption it is too much to ask her to take everything in and work out a new route. Our app does that work for her. It reads her profile and mobility constraints, then tells her what to do next.

What follows from that:

- The app decides, she confirms. One recommended action, one sentence of reason, a deadline on it. Alternatives are in the response for transparency, but the recommendation stays primary.
- Rerouting costs her more than it costs a fast commuter: unfamiliar stations, more walking, more chances to get lost. So when her route still works but is delayed, we recommend switching only if it saves more than 10 minutes at her walking speed. When a route is physically broken (closure, flood, dead lift) we reroute regardless; the threshold governs the judgement call, not the emergency.
- Some disruptions mean don't travel today. We say so. A flood at her destination returns `cancel_trip`, not a longer route.
- Her family hears from us when the plan really changes: a reroute, a switch to taxi, a cancellation, an SOS, a wrong turn. Not for minor delays or crowding advice. Notification fatigue would make the real alerts worthless.

---

## 2. Architecture

```
Frontend  ──►  FastAPI  ──►  Decision engine (9 ordered rules)
                              │
                 ┌────────────┼────────────┐
              Routing     Conditions    Profiles
                              │
                    Adapters, one per source
              live │ fixture │ unavailable
```

The decision engine is the product. Nine rules run in order, first match wins:

| | Rule | Action |
|---|---|---|
| 1 | Flood at origin, destination, or widespread | `cancel_trip` |
| 2 | Lift outage + wheelchair or no stairs | reroute, or `take_taxi` |
| 3 | Route broken by service alert or closure | reroute, or `take_taxi` |
| 4 | Disruption but route usable | wait vs reroute |
| 5 | Platform crowding above threshold | `leave_earlier` or alternative line |
| 6 | Bus crowded, not departed, slack allows | `wait` |
| 7 | Rain forecast | prefer MRT; an exposed walk becomes `leave_earlier` for a shelter-preferring profile |
| 8 | Road incident on a bus leg | `leave_earlier` or rail |
| 9 | Default | `proceed` |

Every response is auditable. `reason` is plain English, `triggered_by` names the data sources that fired, and `data_status` says per source whether the data was live, a labelled fixture, or unavailable. An unreachable source is reported as unavailable, never papered over. If the engine cannot name the source behind a recommendation, that is a bug.

The frontend is a React app served as static files by the same FastAPI
process, so a judge runs one command. Profile setup posts real mobility fields
and the chosen language to the API, and journey planning, advice, location
pings and SOS all run through it. Route legs, instructions, times, crowding
and step-free status come from the advice response, localised in English,
Chinese, Malay and Tamil, with separate spoken phrasing for the voice button.
An OSM map draws the
route, the alternatives and the disrupted segment. The three-stage demo runs
from inside the app under a "Simulated disruption for demonstration" label;
each stage re-plans and shows whatever the engine returns. Any advice built on
fixture data carries a visible REPLAY tag. The full six-scenario set, plus the
three stages, is on the fallback dashboard at `/app` for a judge who wants
every case.

A plainer fallback view also ships at `/app` (plain HTML/JS, no build step). It puts Leaflet on OSM tiles with ODbL attribution, draws the recommended route solid, the disrupted section dashed red and alternatives dotted, and shows crowding as three-level text badges, per-leg step-free status, a live decide-by countdown, and the per-source provenance chips. Fixtures are labelled on screen.

Stack: Python 3.11+, FastAPI, Pydantic; Leaflet and OpenStreetMap tiles for the map layer.

---

## 3. Data, and how we verified it

| Source | Use | Status |
|---|---|---|
| DataMall `TrainServiceAlerts` | disruptions + LTA's own mitigation (free bus/shuttle) | Live |
| DataMall `PCDRealTime` / `PCDForecast` | crowding now / forecast (the proactive half) | Live |
| DataMall `v2/FacilitiesMaintenance` | lift outages per station (load-bearing for this persona) | Live |
| DataMall `PubFloodAlerts`, `TrafficIncidents` | safety stop, road conditions | Live |
| DataMall `v3/BusArrival` | bus load at the boarding stop, when the plan has a bus leg | Live |
| DataMall `BusRoutes` + `BusStops` | one-time verified capture of the bus 2 corridor → `data/replay/` | Captured |
| data.gov.sg two-hour forecast | rain → prefer MRT, shelter, road buffers | Live |
| OpenStreetMap (FOSSGIS foot-profile OSRM; Nominatim, one geocode) | walking legs, geocoding | Live |
| OSM Overpass (steps, elevators, wheelchair tags) | step-free classification of walk legs, capture in `data/replay/` | Captured |
| Station footprint GeoJSON | station positions | Repo file |
| Scenario fixtures | the six demo scenarios | Labelled fixtures |

What we checked:

**The bus option is real.** We searched all 26,823 rows of the live BusRoutes dataset to establish that bus 2 boards at Bedok Stn Exit A and alights at New Bridge Ctr. Captured with provenance.

**Our walking routes are actually walking routes.** `router.project-osrm.org` returned car routing for a test pair (2,255 m at 9.8 m/s where the straight line is about 530 m), so we rejected it. Walk legs use the FOSSGIS foot-profile OSRM, the same service osm.org uses, with cached responses.

**The station GeoJSON is WGS84, not SVY21.** We checked it against known station positions instead of trusting the file, which is dated 2017 and states no coordinate system.

**The README works on a machine that isn't ours.** Fresh `git clone`, new venv on Python 3.14, install, `.env` with no key. The server came up and scenario 3 returned full advice, with keyless sources marked `unavailable` and `confidence: low`. A judge without a DataMall key still sees the whole demo.

**We drove the fallback view in scripted Chrome.** Tiles loaded, attribution visible, scenario 3 clicked, reroute advice rendered, red disrupted segment drawn, fixture chips visible, no horizontal scroll at 390 px.

Our own verification caught two bugs. Interchange closures were applied too broadly: closing Outram Park killed its NEL side too, which pushed the demo scenario to `take_taxi`. Line closures now avoid literal line codes while lift outages stay physical. And an origin and destination resolving to the same station crashed the planner; both same-station and under-500 m pairs now return a clear 422 instead.

---

## 4. Assumptions

Our routing decisions are computed from live data. Our timing is not. Every transit duration is a flat constant rather than a timetable, because we had no timetable data and chose not to fake one.

| Assumption | Value | Basis |
|---|---|---|
| MRT hop between adjacent stations | 2.0 min | Chosen as plausible, no timetable consulted |
| Bus stop-to-stop, incl. dwell | 1.8 min | Chosen as plausible, not measured |
| Interchange transfer | 6.0 min | Fixed allowance, not modelled per station or walking speed |
| Wait for next train | 4.0 min | Chosen as plausible, no headway data consulted |
| Delay when a line reports Status 2 | 20 min | The feed reports status, not duration. A placeholder; see Section 7 |
| Walking speed | 0.8 m/s, configurable | Common figure for reduced-mobility adults; we cite no study and did not measure it |
| Walking pace choices | slowly = 0.8 m/s, average = 1.4 m/s | The profile screen's plain choice maps to these values. Parameters, not measurements |
| prefers_shelter | off by default | A real profile field. In rain, an exposed walk on the plan becomes leave-earlier advice for a shelter-preferring profile; the same inputs without the preference proceed |
| Max walk distance | 400 m, or 200 m for wheelchair | Chosen as plausible |
| Reroute benefit threshold | 10 min | Product judgement, not derived |
| Wrong-direction trigger | 3 divergent pings over ≥90 s, good GPS only | Product judgement: false alarms to family are costly |
| Crowd cutoff | DataMall's own `h` band | The `l`/`m`/`h` scale is the API's, verified live; picking `h` is our judgement |
| Station → weather-area mapping | hand-made table | Our reading of a map, unverified |
| Steps-proximity threshold | 3 m | Measured on this corridor. A 15 m radius produced false positives near the SGH campus, where routes pass stair entrances constantly without climbing them. Routes that actually traverse a steps way touch it at 0–1.2 m; routes that merely pass stay 4 m or more |
| Verified-coverage bar | 60% of route length | Chosen as plausible, not derived |
| Exit-hint ambiguity threshold | 15 m | Chosen as plausible: two entrances closer than this are too close to call, so no hint is shown |
| Exit-hint search | entrances within 300 m of the walk's first geometry points | Chosen as plausible, not derived |

Walk legs are the only durations that come from real geometry. They are routed over OSM footways, so the distance is measured even though the speed is assumed. Nearly every other threshold in the system (flood radii, matching distances, fuzzy floors, notification throttles) was chosen as a plausible value and is listed in `STATUS.md`. The steps threshold above is the exception: that one we measured.

---

## 5. What we store

Required by Section 2.5.

| Data | Where | Retention |
|---|---|---|
| Location pings | Process memory | Lost on restart |
| Journeys and profiles | Process memory | Lost on restart |
| SOS audio | `data/sos_audio/` on disk, gitignored | **No deletion policy — known limitation** |

We do not transcribe SOS audio. GPS pings never leave the machine except as positions shown to explicitly linked family accounts. Journey endpoints (station and place coordinates, not pings) are sent to the FOSSGIS OSRM server to route walking legs. No credentials are committed: `.env` is gitignored and the key appears nowhere in git history (checked).

---

## 6. Underground behaviour

Required by Section 2.6, which asks us to state our choice. It is this: when connectivity drops, the cached route and the next instruction stay visible; live conditions freeze with a visible "last updated" timestamp; stale data is never presented as current. The backend already timestamps every source (`fetched_at`) to support this. The offline view itself is not yet implemented. It belongs to the real frontend, and the fallback dashboard does not handle it.

---

## 7. Known limitations

We would rather name these than have a judge find them.

**One corridor only.** Bedok to Outram Park, plus two named places: "Home (Bedok)" and "Singapore General Hospital", the two ends of Mdm Lim's journey in the brief. SGH was geocoded once via OSM Nominatim and saved to `data/replay/`; "Home (Bedok)" is a placeholder pinned to the Bedok station centroid. Adding a place is one geocode in a data file, so the small corridor is a time limit, not a design limit. Any other origin gets a clear message naming what is supported. We scoped deliberately rather than claim coverage we could not verify with real data.

**OpenStreetMap: we read the tags, and OSM mostly does not know.** Walk legs
are routed over OSM footways, the map renders OSM tiles with ODbL attribution,
and we query OSM's pedestrian tags directly. One cached Overpass query returned
284 elements within 600 m of Bedok station, Outram Park station and Singapore
General Hospital: 164 steps ways, 11 elevators, 87 `wheelchair=yes`, 9
`wheelchair=no`, 5 `wheelchair=limited`, and 16 subway entrances. The capture
is in `data/replay/osm_accessibility_corridor.json` with its provenance and the
query text.

Applied to our four demo walk routes, that gives 0 verified, 1 not step-free,
3 unverified. Zero verified is the honest result: OSM's `wheelchair=yes`
coverage around SGH never reached our 60% threshold for any route. The one
positive finding is real — the Chinatown to SGH walk runs along a steps way,
with the nearest lift 480 m away.

The named entrances in the same capture drive an exit hint on walk legs that
leave a station: the exit nearest to the actual route, with its OSM wheelchair
tag stated as yes, no, or not tagged. A profile that needs step-free access is
steered to a wheelchair=yes exit over a nearer unconfirmed one, and the hint
says which nearer exit was passed over and why. The hint is skipped when two
entrances are within 15 m of each other. We never imply step-free where OSM does not
say so.

**Step-free status is declared, not asserted.** Walk legs are unverified
unless OSM says otherwise. Known lift outages downgrade affected legs to
not step-free. We block routing on not step-free but allow unverified,
because rejecting everything unverified would rule out all walking.

**Timing is assumed, not measured** (Section 4), and `eta_range` is a fixed-width band, not historical variance.

**Wait-vs-reroute runs on a placeholder.** The comparison logic is real; the 20-minute delay estimate feeding it is not.

**Fixtures for the demo.** The network ran normally all build night, so the six scenarios use labelled fixtures. Every response says which sources were fixtures, so the labelling is enforced in the API. One consequence: flood handling has never seen a real alert. Live parsing follows the official guide's schema and is fixture-tested only.

**Everything is in memory.** A backend restart loses profiles, journeys and pings. Acceptable for a prototype; stated so nobody discovers it.

**Still stubbed:** `POST /journeys/{id}/precheck` (marked `X-Stub: true`). The fallback view has not been opened on a real phone browser, only 390 px emulation, and the brief scores on a real phone. It also does not render the taxi driver card.

**Some screens are still static.** The family views and the recording
screen's upload step are design previews and say so on screen; the family
contact name is fixed copy. Voice input uses the browser's speech API, not our
backend. Everything on the route itself now comes from the engine: legs,
instructions, times, crowding and step-free status. The only illustrative
content left is the landmark photos, which appear only on legs they match and
carry an "illustrative" caption.

---

## 8. What we would do next

1. Extend the OSM accessibility capture beyond the demo corridor, add covered-walkway tags for sheltered routing, and contribute the missing `wheelchair` tags around SGH back to OSM. The gap we found is fixable at the source.
2. Learn disruption duration from historical incidents (the SG MRT archive the brief points at) instead of the 20-minute placeholder (the brief's own suggested AI direction).
3. Expand beyond the demo corridor, verifying each route against real data the way bus 2 was verified.
4. Retention policy and encryption for SOS audio; TTL on location pings.

---

## 9. Sources and licences

- LTA DataMall — accessed under its published API terms (guide v6.8 in the organisers' repo)
- data.gov.sg — Singapore Open Data Licence
- OpenStreetMap — © OpenStreetMap contributors, ODbL; rendered with attribution. Routing via FOSSGIS OSRM, one Nominatim geocode and one Overpass query for pedestrian tags, all under their usage policies, with an identifying User-Agent and cached responses
- Station footprint GeoJSON — provided in the problem statement repository
- Libraries: FastAPI, Pydantic, uvicorn, rapidfuzz (MIT/BSD); Leaflet (BSD-2)
