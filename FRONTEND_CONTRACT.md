# SMRTBuddy backend — frontend contract

**Written for the UI builder, who has not seen the backend code.**
Backend base URL: `http://127.0.0.1:8000` (or whatever port uvicorn was given).
Interactive schema for everything below: `GET /docs` (Swagger UI).

> **Schema change (19 Sep, later):** `LocationPing` gained optional `set_state`
> (default false). Pings are transient unless it is true: the on-train scenario
> ping must send it; the wrong-way check must not.
>
> **Schema change (19 Sep):** `Leg.step_free` is now the string enum above,
> not a boolean. The captured examples below have been updated to match;
> walk legs come back `"unverified"` until checked against real data.

## Conventions

- All bodies are JSON. All datetimes are ISO 8601 **with timezone**
  (`2026-09-19T10:00:00+08:00`). Send them with `+08:00`.
- Errors are `{"detail": "human-readable message"}` with status 404 / 422 / 403.
- **`X-Stub: true` response header** = that endpoint is not implemented yet and
  returns placeholder shapes. Today that is ONLY `POST /journeys/{id}/precheck`.
  Everything else is real. CORS is open (`*`) and `X-Stub` is exposed.
- **Coordinates are `[lat, lon]` pairs** (Leaflet order) in every `geometry`
  and `affected_segment` array.
- **Provenance is part of the product.** Every advice carries `data_status`
  per source: `live` | `fixture` | `unavailable` (+ `walk_routing`). SHOW IT —
  fixture data must be visibly labelled in the UI, never presented as live.
  A judge asking "is this live?" must be able to see the answer on screen.
- Map tiles are the frontend's job (OSM — attribution
  "© OpenStreetMap contributors" is a licence requirement); the backend
  supplies all geometry.
- No push channel: poll `GET /journeys/{id}/advice` (e.g. every 30–60 s) and
  `GET /notifications?user_id=` for family alerts.

## Endpoints

| Method & path | Purpose |
|---|---|
| `POST /profiles` | create commuter (`role:"user"`, mobility REQUIRED) or family (`role:"family"`) profile |
| `GET /profiles/{user_id}` | fetch a profile |
| `POST /profiles/{user_id}/link` | link accounts (family ↔ user); both must exist |
| `GET /profiles/{user_id}/location?viewer_id=` | latest position, family/self only (403 otherwise) |
| `POST /journeys` | plan + store a journey (legs scheduled to arrive_by) |
| `GET /journeys/{journey_id}` | fetch the stored journey |
| `GET /journeys/{journey_id}/advice` | **THE CORE CALL** — what she should do right now |
| `POST /journeys/{journey_id}/location` | GPS ping; updates location_state; wrong-direction check |
| `POST /journeys/{journey_id}/precheck` | STUB (`X-Stub: true`) — ignore for now |
| `POST /sos` | two-step SOS (see below) |
| `POST /sos/{sos_id}/audio` | multipart upload, field name `audio`; stored, not transcribed |
| `GET /stations/resolve?q=` | fuzzy station/place lookup, top 3 with scores |
| `GET /notifications?user_id=` | notification log for a recipient (family view) |
| `GET /conditions[?scenario=]` | raw source data + statuses (debug/edge panel) |
| `GET /health` | `{"status":"ok"}` |

---

## POST /profiles

Request (commuter — `mobility` is REQUIRED when `role` is `"user"`,
must be omitted or null for `"family"`):

```json
{
  "user_id": "mdm_lim",            // required, your chosen id
  "role": "user",                  // "user" | "family"
  "name": "Mdm Lim",               // required
  "locale": "en",                  // optional: "en" (default) | "zh" | "ms" | "ta"
  "mobility": {                    // required for role "user"
    "can_use_stairs": false,       // required
    "wheelchair": false,           // required
    "walking_speed_mps": 0.8,      // optional, default 0.8
    "max_walk_metres": 600,        // optional, default 400 (200 if wheelchair)
    "prefers_shelter": false       // optional, default false — in rain, an
                                   // exposed walk becomes leave_earlier advice
  },
  "linked_user_ids": []            // optional
}
```

Real response (201):

```json
{
  "user_id": "mdm_lim",
  "role": "user",
  "name": "Mdm Lim",
  "mobility": {
    "can_use_stairs": false,
    "wheelchair": false,
    "walking_speed_mps": 0.8,
    "max_walk_metres": 600
  },
  "linked_user_ids": [],
  "locale": "en"
}
```

`GET /profiles/{user_id}` returns the same shape (404 if unknown).

## POST /profiles/{user_id}/link

Request: `{"linked_user_id": "mdm_lim"}`. Real response (200) — the daughter
after linking:

```json
{
  "user_id": "daughter",
  "role": "family",
  "name": "Hui Ling",
  "mobility": null,
  "linked_user_ids": [
    "mdm_lim"
  ],
  "locale": "en"
}
```

## POST /journeys

Request:

```json
{
  "user_id": "mdm_lim",                          // must have a commuter profile
  "origin": "Home (Bedok)",                      // see resolve endpoint + note below
  "destination": "Singapore General Hospital",
  "arrive_by": "2026-09-19T10:00:00+08:00",
  "scenario": "disruption_on_train",             // optional; omit = live feeds
  "prefer_mode": "bus"                           // optional: "rail" | "bus"
}
```

Origins/destinations accepted tonight (demo corridor): the corridor station
names (Bedok, Bugis, Outram Park, …) and the places `"Home (Bedok)"` and
`"Singapore General Hospital"`. Anything else → 422 listing what is valid.
An implausible pair is rejected, never auto-corrected — real example (422):

```json
{
  "detail": "origin and destination both resolve to 'Bedok' — check the journey"
}
```

Real response (201) — note `legs[*].geometry` (`[lat, lon]`, truncated here
for readability; the API returns every point):

```json
{
  "journey_id": "1e25b5ea-e27a-4def-ac14-d75a1ea3859f",
  "user_id": "mdm_lim",
  "origin": "Home (Bedok)",
  "destination": "Singapore General Hospital",
  "arrive_by": "2026-09-19T10:00:00+08:00",
  "scenario": "disruption_on_train",
  "location_state": "at_home",
  "legs": [
    {
      "mode": "mrt",
      "from_name": "Bedok",
      "to_name": "Outram Park",
      "service": "EWL",
      "depart": "2026-09-19T09:13:19.750000+08:00",
      "arrive": "2026-09-19T09:39:19.750000+08:00",
      "instruction": "Take the East–West line from Bedok towards Tuas Link. Get off at Outram Park (11 stops).",
      "speech_text": "Take the East–West line from Bedok towards Tuas Link. Get off at Outram Park (11 stops).",
      "i18n_key": "leg.mrt.instruction",
      "shelter": "covered",
      "step_free": "verified",
      "geometry": [
        [
          1.323999,
          103.930214
        ],
        [
          1.321103,
          103.912907
        ],
        [
          1.31985,
          103.903488
        ],
        "... 9 more [lat, lon] points"
      ],
      "crowding": null
    },
    {
      "mode": "walk",
      "from_name": "Outram Park",
      "to_name": "Singapore General Hospital",
      "service": null,
      "depart": "2026-09-19T09:39:19.750000+08:00",
      "arrive": "2026-09-19T09:50:00+08:00",
      "instruction": "Walk to Singapore General Hospital. ",
      "speech_text": "Walk to Singapore General Hospital. ",
      "i18n_key": "leg.walk.instruction",
      "shelter": "exposed",
      "step_free": "unverified",
      "geometry": [
        [
          1.280047,
          103.839439
        ],
        [
          1.279872,
          103.839504
        ],
        [
          1.279797,
          103.839442
        ],
        "... 25 more [lat, lon] points"
      ],
      "crowding": null
    }
  ]
}
```

`Leg` fields: `mode` (`walk|bus|mrt|taxi`), `from_name`, `to_name`,
`service` (line code or bus number, null for walks), `depart`, `arrive`,
`instruction` (localised, landmark-based), `speech_text` (for TTS),
`i18n_key`, `shelter` (`covered|partial|exposed`),
`step_free` (`"verified" | "unverified" | "not_step_free"` — a claim with
provenance, not a boolean; SHOW `unverified` as a caveat and `not_step_free`
as a warning — never render an unverified walk as step-free),
`geometry` (`[lat, lon][]`), `crowding` (`low|medium|high` or null —
populated on advice legs, null on journey creation), and `exit_hint` (null, or
`{station, ref, wheelchair: "yes"|"no"|"untagged", text, source}` on walk legs
leaving a station — the nearest exit from captured OSM entrances, with the
localised `text` ready to render; a step-free-needing profile is steered to a
wheelchair=yes exit and the text says so).

## GET /journeys/{journey_id}/advice — THE CORE CALL

No request body. Recompute on demand; poll it. Real response (200), captured
after the location ping below (this is the demo moment — she is on the train
and the EWL city stretch just closed):

```json
{
  "action": "reroute",
  "headline": "Get off at Bugis, then take the Downtown line from Bugis towards Expo. Get off at Chinatown (5 stops).",
  "speech_text": "Get off at Bugis, then take the Downtown line from Bugis towards Expo. Get off at Chinatown (5 stops).",
  "reason": "Train service is suspended at City Hall, Outram Park, Raffles Place, Tanjong Pagar on your usual route. Operator notice: [FIXTURE] EWL: No train service between City Hall and Outram Park due to a signalling fault. Free bus rides and shuttle services are available at designated stops. LTA is running free MRT shuttles at the affected stations (in the alert feed), but the sheltered rail route below avoids the closure entirely.",
  "triggered_by": [
    "train_service_alerts"
  ],
  "decide_by": "2026-09-19T01:53:15.318861+08:00",
  "eta_range": [
    "2026-09-19T02:35:55.568861+08:00",
    "2026-09-19T02:50:55.568861+08:00"
  ],
  "confidence": "medium",
  "notify_family": true,
  "data_status": {
    "train_service_alerts": "fixture",
    "weather": "fixture",
    "crowd_density_realtime": "fixture",
    "crowd_density_forecast": "live",
    "lift_maintenance": "fixture",
    "flood_alerts": "fixture",
    "traffic_incidents": "live",
    "taxi_availability": "live",
    "taxi_stands": "live",
    "walk_routing": "live"
  },
  "legs": [
    {
      "mode": "mrt",
      "from_name": "Paya Lebar",
      "to_name": "Bugis",
      "service": "EWL",
      "depart": "2026-09-19T01:41:15.318861+08:00",
      "arrive": "2026-09-19T01:53:15.318861+08:00",
      "instruction": "Take the East–West line from Paya Lebar towards Tuas Link. Get off at Bugis (4 stops).",
      "speech_text": "Take the East–West line from Paya Lebar towards Tuas Link. Get off at Bugis (4 stops).",
      "i18n_key": "leg.mrt.instruction",
      "shelter": "covered",
      "step_free": "verified",
      "geometry": [
        [
          1.317585,
          103.892281
        ],
        [
          1.316405,
          103.882998
        ],
        [
          1.311421,
          103.871426
        ],
        "... 2 more [lat, lon] points"
      ],
      "crowding": "high"
    },
    {
      "mode": "mrt",
      "from_name": "Bugis",
      "to_name": "Chinatown",
      "service": "DTL",
      "depart": "2026-09-19T01:53:15.318861+08:00",
      "arrive": "2026-09-19T02:13:15.318861+08:00",
      "instruction": "Take the Downtown line from Bugis towards Expo. Get off at Chinatown (5 stops).",
      "speech_text": "Take the Downtown line from Bugis towards Expo. Get off at Chinatown (5 stops).",
      "i18n_key": "leg.mrt.instruction",
      "shelter": "covered",
      "step_free": "verified",
      "geometry": [
        [
          1.300433,
          103.855685
        ],
        [
          1.293224,
          103.860733
        ],
        [
          1.281812,
          103.859152
        ],
        "... 2 more [lat, lon] points"
      ],
      "crowding": "high"
    },
    {
      "mode": "mrt",
      "from_name": "Chinatown",
      "to_name": "Outram Park",
      "service": "NEL",
      "depart": "2026-09-19T02:13:15.318861+08:00",
      "arrive": "2026-09-19T02:25:15.318861+08:00",
      "instruction": "Take the North East line from Chinatown towards HarbourFront. Get off at Outram Park (1 stops).",
      "speech_text": "Take the North East line from Chinatown towards HarbourFront. Get off at Outram Park (1 stops).",
      "i18n_key": "leg.mrt.instruction",
      "shelter": "covered",
      "step_free": "verified",
      "geometry": [
        [
          1.284491,
          103.843457
        ],
        [
          1.280066,
          103.83949
        ]
      ],
      "crowding": "low"
    },
    {
      "mode": "walk",
      "from_name": "Outram Park",
      "to_name": "Singapore General Hospital",
      "service": null,
      "depart": "2026-09-19T02:25:15.318861+08:00",
      "arrive": "2026-09-19T02:35:55.568861+08:00",
      "instruction": "Walk to Singapore General Hospital. ",
      "speech_text": "Walk to Singapore General Hospital. ",
      "i18n_key": "leg.walk.instruction",
      "shelter": "exposed",
      "step_free": "unverified",
      "geometry": [
        [
          1.280047,
          103.839439
        ],
        [
          1.279872,
          103.839504
        ],
        [
          1.279797,
          103.839442
        ],
        "... 25 more [lat, lon] points"
      ],
      "crowding": null
    }
  ],
  "affected_segment": [
    [
      1.292985,
      103.852666
    ],
    [
      1.283455,
      103.851393
    ],
    [
      1.276832,
      103.846613
    ],
    "... 1 more [lat, lon] points"
  ],
  "alternatives": [
    [
      {
        "mode": "taxi",
        "from_name": "Paya Lebar",
        "to_name": "Singapore General Hospital",
        "service": null,
        "depart": "2026-09-19T01:41:15.318861+08:00",
        "arrive": "2026-09-19T02:07:20.868359+08:00",
        "instruction": "Taxi from Paya Lebar to Singapore General Hospital. Show the driver the card on screen.",
        "speech_text": "Taxi from Paya Lebar to Singapore General Hospital. Show the driver the card on screen.",
        "i18n_key": "leg.taxi.instruction",
        "shelter": "covered",
        "step_free": "verified",
        "geometry": [
          [
            1.317585,
            103.892281
          ],
          [
            1.2794489,
            103.8362739
          ]
        ],
        "crowding": null
      }
    ]
  ],
  "driver_card": null
}
```

Field notes:

- `action`: `proceed | wait | reroute | leave_earlier | take_taxi | cancel_trip`
- `headline` + `speech_text`: localised, ONE sentence — this is the screen/voice
- `reason`: plain-English explanation. ALWAYS present. Show it.
- `triggered_by`: source names behind the decision — auditable
- `decide_by`: nullable — when the recommendation expires (e.g. her arrival at
  the alight station). Render as a countdown.
- `eta_range`: `[earliest, latest]` — show the range, not one confident number
- `confidence`: `high | medium | low` (`low` when a needed source was
  unavailable or walking fell back to an estimate)
- `notify_family`: whether this advice logged family notifications
- `data_status`: per-source provenance — RENDER THIS (fixture ≠ live)
- `legs`: the RECOMMENDED plan (single-plan actions keep the current legs)
- `affected_segment`: nullable `[lat, lon][]` — the disrupted part of the
  ORIGINAL route; draw it highlighted (e.g. red) against the new route
- `alternatives`: 0–2 extra `Leg[]` lists — secondary options for transparency;
  the recommendation stays primary. **We decide, she confirms.**
- `driver_card`: only with `take_taxi` — `{destination_en, destination_zh,
  arrive_by}`: render full-screen for showing to a taxi driver

## POST /journeys/{journey_id}/location

Request:

```json
{
  "lat": 1.3178, "lon": 103.8927,
  "accuracy_m": 25,                              // optional but needed for wrong-direction
  "recorded_at": "2026-09-19T08:40:00+08:00",
  "location_state": "on_train",                  // optional: at_home | walking | on_bus | on_train | on_platform
  "set_state": true                              // optional, default false: see note below
}
```

A ping is transient by default: it records position and feeds
wrong-direction detection, but does NOT change the journey's location
context. Send `"set_state": true` only for a deliberate state change (she
boarded the train). The wrong-way check must NOT set it, or it erases
"on_train" and later advice loses the alight phrasing.

Send `location_state` whenever the UI knows it — the SAME advice is worded
differently per state (on_train → "get off at …"). Real response (200):

```json
{
  "journey_id": "1e25b5ea-e27a-4def-ac14-d75a1ea3859f",
  "received_at": "2026-09-19T01:41:14.917383+08:00",
  "wrong_direction": false,
  "notify_family": false
}
```

`wrong_direction` goes true after 3 consecutive accurate pings moving away
from the next waypoint over ≥90 s (family notified, throttled to 1/10 min).

## POST /sos — two-step

Step 1 `{"user_id": "mdm_lim"}` → real response:

```json
{
  "sos_id": "9948038c-a38e-4a5b-90d8-8ad690acfec9",
  "status": "awaiting_confirmation",
  "notified_user_ids": []
}
```

Step 2 `{"user_id": "mdm_lim", "sos_id": "<from step 1>", "confirm": true}` →

```json
{
  "sos_id": "9948038c-a38e-4a5b-90d8-8ad690acfec9",
  "status": "confirmed",
  "notified_user_ids": [
    "daughter"
  ]
}
```

UI: big button → confirmation dialog → step 2. Audio (optional, after step 1):
`POST /sos/{sos_id}/audio` as `multipart/form-data`, field **`audio`** →
`{"sos_id": "...", "received_bytes": 14, "stored": true}`.

## GET /stations/resolve?q=

Real response for `q=outrm park` (typo intended):

```json
{
  "query": "outrm park",
  "candidates": [
    {
      "name": "Outram Park",
      "score": 76.2
    }
  ]
}
```

Scores are 0–100. NEVER auto-pick: show candidates and let her choose
(large tap targets). Empty `candidates` = nothing plausible.

## GET /notifications?user_id=

Real response (one entry shown):

```json
[
  {
    "notification_id": "6827f004-469b-40a2-b1a0-cd04c18b396d",
    "to_user_id": "daughter",
    "about_user_id": "mdm_lim",
    "journey_id": "1e25b5ea-e27a-4def-ac14-d75a1ea3859f",
    "event": "reroute",
    "message": "Get off at Bugis, then take the Downtown line from Bugis towards Expo. Get off at Chinatown (5 stops). — Train service is suspended at City Hall, Outram Park, Raffles Place, Tanjong Pagar on your usual route. Operator notice: [FIXTURE] EWL: No train service between City Hall and Outram Park due to a signalling fault. Free bus rides and shuttle services are available at designated stops. LTA is running free MRT shuttles at the affected stations (in the alert feed), but the sheltered rail route below avoids the closure entirely.",
    "created_at": "2026-09-19T01:41:15.323313+08:00"
  }
]
```

`event`: `reroute | take_taxi | cancel_trip | sos | wrong_direction`.
Poll this on the family account's screen.

## GET /profiles/{user_id}/location?viewer_id=

Family view of her latest position (403 unless viewer is linked family/self):

```json
{
  "user_id": "mdm_lim",
  "journey_id": "1e25b5ea-e27a-4def-ac14-d75a1ea3859f",
  "location": {
    "lat": 1.3178,
    "lon": 103.8927,
    "accuracy_m": 25.0,
    "recorded_at": "2026-09-19T08:40:00+08:00",
    "location_state": "on_train"
  }
}
```

## GET /conditions?scenario=

Raw per-source data + statuses, same gathering the engine uses (`data`
payloads elided here — they are the raw upstream shapes):

```json
{
  "sources": [
    {
      "name": "train_service_alerts",
      "status": "fixture",
      "fetched_at": "2026-09-19T01:41:15.353928+08:00",
      "data": "… full raw payload of this source …"
    },
    {
      "name": "weather",
      "status": "fixture",
      "fetched_at": "2026-09-19T01:41:15.353935+08:00",
      "data": "… full raw payload of this source …"
    }
  ]
}
```

---


## The three-stage demo (one journey, escalating events)

One journey, Bedok to Singapore General Hospital, three moments, one morning.
Stage 1 creates the journey; stages 2 and 3 advance the scenario on the SAME
journey with `POST /journeys/{id}/scenario` `{"scenario": "<stage id>"}`, then
ping and re-request advice. Place the stage pings on the journey's own
morning: recorded_at = first leg's depart +20 min (stage 2) and +45 min
(stage 3). For scenario journeys the engine's clock is the latest ping's
recorded_at, so the three advice moments land in order on one morning. All three run through the real engine;
the fixtures are labelled and the REPLAY tag shows.

Journey body for every stage: `user_id: "mdm_lim"`, `origin: "Home (Bedok)"`,
`destination: "Singapore General Hospital"`, `arrive_by` in the future,
`scenario` per stage.

| Stage | `scenario` | Ping after creating (then GET advice) | Expected |
|---|---|---|---|
| 1 | `demo_stage1_peak_crowding` | none (she is at home) | `leave_earlier`, no family notification |
| 2 | `demo_stage2_planned_closure` | `{"lat": 1.317585, "lon": 103.892281, "accuracy_m": 25, "recorded_at": "<now>", "location_state": "on_train", "set_state": true}` (Paya Lebar) | `reroute`, "Get off at Bugis…", family notified |
| 3 | `demo_stage3_breakdown` | `{"lat": 1.300433, "lon": 103.855685, "accuracy_m": 25, "recorded_at": "<now>", "location_state": "on_train", "set_state": true}` (Bugis) | `take_taxi` with driver_card, family notified; reason names the rejected bus with real distances |

`set_state: true` is required on both pings (she boarded the train — a
deliberate state change). Stage 3's `affected_segment` carries both broken
stretches for the map.

## The six demo scenarios — paste and run

Fixture-driven (labelled!), each through the real engine. Setup once:

```bash
BASE=http://127.0.0.1:8000
curl -s -X POST $BASE/profiles -H 'Content-Type: application/json' -d '{
  "user_id": "mdm_lim", "role": "user", "name": "Mdm Lim", "locale": "en",
  "mobility": {"can_use_stairs": false, "wheelchair": false,
               "walking_speed_mps": 0.8, "max_walk_metres": 600}}'
curl -s -X POST $BASE/profiles -H 'Content-Type: application/json' \
  -d '{"user_id": "daughter", "role": "family", "name": "Hui Ling"}'
curl -s -X POST $BASE/profiles/daughter/link \
  -H 'Content-Type: application/json' -d '{"linked_user_id": "mdm_lim"}'
curl -s -X POST $BASE/profiles -H 'Content-Type: application/json' -d '{
  "user_id": "wc_user", "role": "user", "name": "Mr Tan",
  "mobility": {"can_use_stairs": false, "wheelchair": true}}'
curl -s -X POST $BASE/profiles/daughter/link \
  -H 'Content-Type: application/json' -d '{"linked_user_id": "wc_user"}'

adv() { JID=$(curl -s -X POST $BASE/journeys -H 'Content-Type: application/json' \
  -d "$1" | python3 -c 'import sys,json; print(json.load(sys.stdin)["journey_id"])');
  [ -n "$2" ] && curl -s -X POST $BASE/journeys/$JID/location \
    -H 'Content-Type: application/json' -d "$2" > /dev/null;
  curl -s $BASE/journeys/$JID/advice | python3 -m json.tool; }
```

```bash
# 1. clear_day -> proceed
adv '{"user_id":"mdm_lim","origin":"Home (Bedok)","destination":"Singapore General Hospital","arrive_by":"2026-09-19T10:00:00+08:00","scenario":"clear_day"}'

# 2. rain (plan starts on the bus she prefers) -> reroute to MRT
adv '{"user_id":"mdm_lim","origin":"Home (Bedok)","destination":"Singapore General Hospital","arrive_by":"2026-09-19T10:00:00+08:00","scenario":"rain","prefer_mode":"bus"}'

# 3. THE DEMO: disruption while she is on the train -> "get off at Bugis..."
adv '{"user_id":"mdm_lim","origin":"Home (Bedok)","destination":"Singapore General Hospital","arrive_by":"2026-09-19T10:00:00+08:00","scenario":"disruption_on_train"}' \
    '{"lat":1.3178,"lon":103.8927,"accuracy_m":25,"recorded_at":"2026-09-19T08:40:00+08:00","location_state":"on_train","set_state":true}'

# 4. lift outage + wheelchair profile -> take_taxi with driver card
adv '{"user_id":"wc_user","origin":"Home (Bedok)","destination":"Singapore General Hospital","arrive_by":"2026-09-19T10:00:00+08:00","scenario":"lift_outage"}'

# 5. flood at destination -> cancel_trip
adv '{"user_id":"mdm_lim","origin":"Home (Bedok)","destination":"Singapore General Hospital","arrive_by":"2026-09-19T10:00:00+08:00","scenario":"flood_destination"}'

# 6. crowding forecast -> leave_earlier
adv '{"user_id":"mdm_lim","origin":"Home (Bedok)","destination":"Singapore General Hospital","arrive_by":"2026-09-19T10:00:00+08:00","scenario":"crowding_forecast"}'

# family screen after the above:
curl -s "$BASE/notifications?user_id=daughter" | python3 -m json.tool
```
