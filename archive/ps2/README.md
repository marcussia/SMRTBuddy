# PS2 — Smart Commuter Companion

Work folder for NEBULA X **Problem Statement 2**. The PS3 train-condition-monitoring
work is unaffected and stays where it is, at the repository root.

> **Status: empty scaffold.** Nothing is built yet. No stack chosen, no persona chosen.
> Everything below is quoted requirement from the PS2 brief, not a claim about this folder.

## What PS2 asks for

A **web app, mobile-first** — `PS2_README.md` §3.1: *"No native build, no app store — a
web application a commuter opens in their phone's browser."* Judges open it in a mobile
browser on a real phone. A desktop layout shrunk down does not score.

## Three mandatory capabilities

Missing any one caps that part of the score at level 3 of 5.

1. **Route planning** — door to door including both walking legs, multi-modal where the
   persona needs it, responsive to live conditions, and it must say *why* a
   recommendation changed. Timing with uncertainty visible. Building on an existing
   engine (OSRM / GraphHopper / Valhalla / OneMap) is explicitly allowed.
2. **GIS on OpenStreetMap** — OSM is the required base. Two hard conditions: display
   "© OpenStreetMap contributors" wherever the map or derived data appears, and do not
   bulk-hit `tile.openstreetmap.org`.
3. **Visualisation** — route on a map with affected vs unaffected portions
   distinguished; the alternative shown against the original; crowding readable in one
   second; time and delay cost obvious.

## Rubric

| Criterion | Weight |
|---|---|
| Problem Fit | 40% |
| Technical Execution | 35% |
| Ease of Use | 25% |

Each scored 0–5. Judging: judges follow the README on a clean machine, open the app on a
real phone, one real journey is walked end to end, and one claim per criterion must be
defended.

## Deliverables

- The app, runnable from a README on a clean machine
- `WRITEUP.md` — persona, architecture, assumptions, known limitations
- A demo recording, linked not committed — one real journey through one real disruption
- `.env.example` listing variable *names* only

There is no predictions file for PS2.

## Caps to avoid

A feature in the pitch but absent from the running system · mocked data presented as
live · a claim a judge cannot verify · a credential committed to the repository · OSM
used without attribution (a licence breach, not a style point) · data scraped in breach
of a site's terms (caps the data dimension at 1 and is referred to the organisers).

## Decisions still open

- **Persona** — Rachel (fixed-schedule, EWL) · Arjun (multi-modal, cycles) · Mdm Lim
  (accessibility-constrained). The brief requires naming one and showing their journey
  working end to end.
- **Stack and hosting**
- **Offline behaviour underground** — §2.6 requires a stated choice: cache the journey,
  degrade gracefully, or say plainly that it is stale.

## Source of truth

`NebulaX-Hackathon-ProblemStatement/PS2/` — `PS2_README.md` is the authoritative brief
(the `.docx` is a summary and uses outdated endpoint names; the crowding paths are
`PCDRealTime` / `PCDForecast`). Packaging rules are in `PS2/submission/README.md`.
