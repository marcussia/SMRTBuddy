# SMRTBuddy

A smart commuter companion for Singapore — a mobile-first web app that tells a commuter
*before they leave* that today is not an ordinary day, and what to do about it. Built for
NEBULA X 2026, **Problem Statement 2**.

- **Live app:** `<TBD>`
- **Demo video:** `<TBD>`
- **Write-up:** [`WRITEUP.md`](WRITEUP.md) — `<TBD>`

> **Status: not built.** This README describes the project we are building and records
> the decisions still open. Nothing below is a claim about working software. Sections
> marked `<TBD>` are unwritten, not undocumented.

## The problem

Singapore's network works well on an ordinary day. The commuter's problem is the day that
is not — a signalling fault at 08:15, an exit closed for works, a line at reduced
frequency, a downpour that turns a 6-minute walk into a decision. Today the burden of
reacting falls on the commuter: notice something is wrong, work out whether it affects
them, decide what to do instead, and do it while standing on a platform.

Most apps are reactive and generic. They tell everyone the same thing, after the fact.
SMRTBuddy is meant to do the opposite: know enough about *this* commuter's routine to
reach them before the problem does, and recommend an action rather than report a status.

## Who it's for

`<TBD — persona not yet chosen>`

One persona, named and built for end to end. Candidates from the brief:

| Persona | Journey | What they need |
|---|---|---|
| **Rachel** — fixed schedule | Tampines → Raffles Place, EWL, leaves 07:40 | Interrupted *only* when it matters, answered in one line. 5 min is noise; 15 min costs a meeting |
| **Arjun** — multi-modal, flexible start | Punggol → one-north, cycles to LRT, sometimes buses | Crowding, sheltered routes, whether he can bring the bike. Will leave 20 min later to avoid a crush |
| **Mdm Lim** — accessibility-constrained | Bedok → SGH, fortnightly | Lifts and sheltered walkways, no stairs, large text, whole trip planned in advance, day-before warning if a lift is out |

## What it must do

Three capabilities are mandatory; missing any one caps that part of the score.

**1. Route planning.** Door to door including both walking legs — a route that starts and
ends at a station is not a commuter's journey. Multi-modal where the persona needs it.
Responsive to live conditions, and it must say **why** a recommendation changed. Timing
with the uncertainty visible rather than hidden behind one confident number.

**2. GIS on OpenStreetMap.** OSM is the required geospatial base — it carries the
footways, crossings, stairs, lifts, covered walkways and cycle paths a road map does not.

**3. Visualisation.** The route on a map with the affected portion distinguished from the
unaffected. The alternative shown against the original so the commuter can judge the
trade-off. Crowding readable in one second. Delay cost obvious. Legible on a phone, in
one hand, in sunlight.

## Architecture

`<TBD>`

Decisions not yet made: framework and hosting, routing engine (OSRM · GraphHopper ·
Valhalla · OneMap), tile source, and how live feeds are cached.

## Data sources

| Source | Used for | Key needed |
|---|---|---|
| **LTA DataMall** `TrainServiceAlerts` | Official structured disruption feed. Carries the *mitigation* too — `FreePublicBus` and `FreeMRTShuttle` name where free boarding and shuttles are active | Free `AccountKey` |
| **DataMall** `PCDForecast` / `PCDRealTime` | Station crowding — forecast at 30-min intervals is what makes *proactive* advice possible; real-time refreshes every 10 min | Same key |
| **DataMall** `v3/BusArrival` | Bus ETA plus `Load` (`SEA`/`SDA`/`LSD`), `Feature=WAB` for wheelchair-accessible, deck type | Same key |
| **DataMall** `v2/FacilitiesMaintenance` | Lift outages per lift and the exit it serves | Same key |
| **DataMall** `RoadWorks`, `PlannedBusRoutes` | The *planned* half of the brief — known in advance | Same key |
| **DataMall** geospatial layers | `CoveredLinkWay`, `TrainStationExit`, `CyclingPath`, `Footpath` — authoritative where OSM is crowd-sourced | Same key |
| **OpenStreetMap** | Required geospatial base; pedestrian and cycling detail | No |
| **data.gov.sg** weather | 2-hour nowcast, 24-hour forecast, rainfall — the walking and cycling legs | No |
| **OneMap** | Geocoding and its routing API | Free, registration |

**A trap to handle early:** line codes differ between endpoints — Sengkang LRT is `STL`
in `TrainServiceAlerts` but `SLRT` in crowd density; Punggol is `PTL` vs `PLRT`; Circle
Line Extension folds into `CCL` in one and is `CEL` in the other; Changi folds into `EWL`
vs `CGL`. One canonical line table, everything mapped through it.

## Running it

`<TBD — nothing to run yet>`

When there is, this section must carry, per the submission rules: **prerequisites**
(runtime and version, package manager), **exact copy-pasteable install and run commands
in order**, **configuration** (which variables, where to get the keys), and **what to
click** — where the app opens and the one journey to try first. It will be tested by
cloning into a fresh directory and following it literally, because judges run it on a
clean machine and what does not run does not score.

## Configuration

An LTA DataMall `AccountKey` is required — free, from <https://datamall.lta.gov.sg>.
OneMap needs free registration. The data.gov.sg weather endpoints need no key.

**No credential is ever committed.** Keys go in an ignored `.env`; `.env.example` lists
variable names only. `.env` is gitignored; `.env.example` lists `LTA_DATAMALL_KEY`.

## Offline behaviour

Underground there is no signal — a commuter between stations cannot fetch anything. The
brief requires a stated choice here: cache the current journey, degrade gracefully, or
say plainly that the data is stale. **Our choice: `<TBD>`**, to be recorded in
`WRITEUP.md`.

## Attribution

Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors,
licensed under the [ODbL](https://opendatacommons.org/licenses/odbl/). This attribution
must appear wherever the app shows a map or anything derived from it — it is a licence
condition, not a style preference.

Public transport data from [LTA DataMall](https://datamall.lta.gov.sg), weather from
[data.gov.sg](https://data.gov.sg).

## How this is judged

| Criterion | Weight | What it covers |
|---|---|---|
| Problem Fit | 40% | Would a real commuter be better off with this? Persona fit, proactivity, quality of the decision offered — plus anything beyond the brief |
| Technical Execution | 35% | Routing reflecting live conditions on an OSM base, breadth and judgement of data, and whether it actually runs |
| Ease of Use | 25% | Usable on a phone, one-handed. Interaction design, information hierarchy, accessibility |

Scored 0–5 per criterion. Judges follow this README on a clean machine, open the app in a
browser **on a real phone**, watch one real journey walked end to end, and ask us to
defend one claim per criterion.

Capped regardless of other merit: a feature shown but absent from the running system,
mocked data presented as live, a claim a judge cannot verify, a committed credential, or
OSM without attribution. Disruption replay and injected test data are fine **provided
they are labelled as such** — the feeds are quiet most days, so the major-disruption path
will need a labelled replay.

## Deliverables

- [ ] The app — runnable from this README on a clean machine, all three capabilities
- [ ] `WRITEUP.md` at repository root — persona, architecture, assumptions, known limits;
      any number says how we arrived at it
- [ ] Demo recording — one real journey through one real disruption, phone screen, linked
      here not committed
- [ ] `.env.example` — variable names only
- [ ] Tested by cloning fresh and following this README literally
- [ ] Opened on a real phone browser, not devtools emulation

## Open decisions

1. **Persona** — the choice that drives everything else
2. **Framework, hosting, routing engine, tile source**
3. **Offline behaviour underground**
4. **Which disruption the demo walks through**, and how the replay is labelled

## Reference

The brief lives in `NebulaX-Hackathon-ProblemStatement/PS2/` — `PS2_README.md` is
authoritative (the `.docx` is a summary with outdated endpoint names), and
`PS2/submission/README.md` has the packaging rules.

Earlier PS3 train-condition-monitoring work is retained under `archive/ps3/` but is
**not part of this submission**.
