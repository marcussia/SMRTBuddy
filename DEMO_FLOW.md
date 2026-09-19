# The three-stage demo: one journey, one morning

Findings and fixes from the demo-flow audit, 2026-09-19. The demo is Mdm Lim,
Bedok home to Singapore General Hospital, peak hour, one morning, three
escalating events.

## Findings against the five requirements

1. **Journey identity — WAS WRONG, fixed.** `runStage` (src/api.ts) called
   `createJourney` on every stage, so each stage POSTed /journeys and got a
   new journey_id. There was also no backend way to change an existing
   journey's scenario. Fix: stage 1 creates the journey once; stages 2 and 3
   advance the scenario on the SAME journey via a new
   `POST /journeys/{id}/scenario` (app/main.py), which validates the fixture
   exists and changes nothing else.

2. **The clock — WAS WRONG, fixed.** Two causes. Ping times came from
   `new Date()` in postLocation (src/api.ts), and the engine's clock was
   `datetime.now(SGT)` (app/service.py:109), so a replan run at 15:00 real
   time stamped a morning demo's advice in the afternoon. Fix: stage pings
   are placed on the journey's own morning (departure +20 min at Paya Lebar,
   +45 min at Bayfront), and for scenario journeys the engine's clock is the
   latest ping's recorded_at, else 45 min before departure. Live journeys
   keep the real clock. Departure itself was already anchored: legs are
   scheduled back from arrive_by (app/main.py).

3. **Cumulative conditions — ALREADY CORRECT.** The stage 3 fixture carries
   BOTH segments: the EWL closure (EW13–EW16) from stage 2 and the DTL fault
   (DT17–DT19). See tools/make_fixtures.py: TSA_BREAKDOWN reuses
   TSA_PLANNED_CLOSURE's segment (lines 187–191). With the breakdown alone
   she could route Bugis → EWL → Outram Park; the taxi is earned because
   both are in force. Verified in the run below: stage 3's active conditions
   list shows both lines.

4. **Positions — ALREADY CORRECT.** STAGES (src/api.ts): stage 1 `ping:
   null`, stage 2 (1.317585, 103.892281) Paya Lebar, stage 3
   (1.281812, 103.859152) Bayfront. Unchanged.

5. **notify_family — ALREADY CORRECT.** false / true / true, re-verified in
   the run below.

## The verified sequence (one run, pasted)

```
STAGE 1  journey 196a0cad-…7b7d  depart 09:13  advice at ~08:28 (pre-departure)
         action leave_earlier   notify false
         conditions: TSA normal, Bedok crowd band h
         eta 09:50–09:55

STAGE 2  journey 196a0cad-…7b7d  same departure  advice at 09:33 (Paya Lebar)
         action reroute          notify true    decide_by 09:45 (before Bugis)
         conditions: EWL EW13–EW16 closed (planned works)
         "Get off at Bugis, then take the Downtown line…"  eta 10:28–10:43

STAGE 3  journey 196a0cad-…7b7d  same departure  advice at 09:58 (Bayfront)
         action take_taxi        notify true
         conditions: EWL EW13–EW16 closed AND DTL DT17–DT19 down
         "Take a taxi from Bayfront — show the driver the card."  eta 10:10–10:25
```

One journey_id across all three stages; all timestamps on the same morning;
the advice moments are in order (08:28, 09:33, 09:58). Stage 3's arrival
estimate is earlier than stage 2's because the taxi is faster than the rail
detour it replaces — that is the engine being right, not the clock being
wrong.

Also verified from the browser: pressing the three stage buttons in the UI
produces exactly one `POST /journeys` and two `POST /journeys/{id}/scenario`.

## Diff summary

- `app/main.py`: new `POST /journeys/{journey_id}/scenario` (advance the
  labelled replay scenario on an existing journey; 404 unknown journey, 422
  unknown scenario).
- `app/service.py`: simulated clock for scenario journeys — latest ping's
  recorded_at, else departure minus 45 min; real time for live journeys.
- `src/api.ts`: `runStage` keeps one journey across stages; ping recorded_at
  derived from the journey's departure; `postLocation` gains an optional
  recordedAt; the Journey type now includes legs.
- No visual changes; no new screens or components; fixtures untouched.
- Regressions after: six scenarios 6/6, three stages 3/3.
