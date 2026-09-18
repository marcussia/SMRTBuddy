# VERIFICATION — NEBULA X Problem Statement 2

**Status:** Q1–Q3 and Q5–Q7 answered. **Q4 and the "contradicts PRD.md" section are BLOCKED because `PRD.md` is empty.** See the blocker below.
**Date:** 2026-09-19
**Scope:** verification only. No code was written or changed. Nothing was deleted.

---

## Sources read

- **Our repo:** `~/Projects/nebulax/smrtbuddy` (repo root). Remote is `github.com/marcussia/smrtbuddy`, `main` is level with `origin/main`, and the only untracked file is `PRD.md`.
- **Organisers' repo:** `~/Projects/nebulax/NebulaX-Hackathon-ProblemStatement`. Remote is `github.com/aochinwen/NebulaX-Hackathon-ProblemStatement`, local HEAD is `16526c0`.
  - A fetch tonight found `origin/main` one commit ahead (`966c976 Document predecessor precedence rule in PS1_README.md`). That commit is PS1 only, and upstream's `PS2/` file list is identical to the local one.

The organisers' `PS2/` folder contains exactly these files (local and upstream):

```
PS2/PS2_README.md
PS2/data/AmendmenttoMP2014RailStation.geojson   (500K)
PS2/data/UsefulWebsites.txt                     (8K)
PS2/references/24hourWeatherForecast.json
PS2/references/4dayWeatherForecast.json
PS2/references/LTA_DataMall_API_User_Guide.pdf  (v6.8, 80 pages; byte-identical to the copy at repo root)
PS2/references/Problem_Statement_2_Specification.docx
PS2/references/Problem_Statement_2_Specification.pdf   (5 pages; text matches the .docx)
PS2/submission/README.md
```

Also read: the organisers' top-level `README.md`.

---

## ⛔ BLOCKER 1: `PRD.md` is empty

- `smrtbuddy/PRD.md` is **0 bytes**. It is untracked (never committed; `git log --all -- PRD.md` is empty) and was last modified 2026-09-19 00:20.
- It is not on `origin/main` either.
- No other `PRD*` file exists under `~/Projects/nebulax`, `~/Desktop`, `~/Downloads` or `~/Documents`.
- The lost session's transcript shows it was **already 0 bytes then**, at 00:23 SGT the same night (`PRD.md: empty`). Nothing was lost from the file; it never had content on disk. Most likely it was created but never saved from the editor.

**Consequences:** Q4 and the "contradicts PRD.md" section cannot be answered. I have not guessed at PRD content.

**ACTION NEEDED (you):** put the PRD text into `PRD.md`, or tell me where it is.

## ⛔ BLOCKER 2: `PS2_scoring_rubric.md` does not exist

- You asked me to read `PS2_scoring_rubric.md`. It is not in the organisers' repo, locally or on upstream.
- I searched the working tree and all git history for `*rubric*`, `*scor*`, `*judg*` and `*criteria*`. There were no matches.
- The organisers' top-level `README.md` says it should exist:

  > **`PS2/references/PS2_scoring_rubric.md`** — the full rubric: every dimension broken into sub-axes with a description at each of the five levels, plus caps and judging protocol

- The same README's structure diagram also lists `PS2/generate_ps2_docx.py` and `PS2/generate_ps2_pdf.py`. Neither exists.
- **What is known:** the three-criterion rubric in `PS2_README.md` §3.2.4 (quoted under Q2), which is identical in the .docx and .pdf.
- **What is unknown:** the sub-axes and the descriptions for each of the five levels. That is a question for the organisers (see Open questions).

---

## Q1. Exactly what must be submitted?

**`PS2/PS2_README.md` §4 Deliverables (verbatim):**

> 1. **The app** — runnable, with clear setup instructions, covering all three required capabilities in **3.2**. Judges will follow your README on a clean machine; what does not run does not score.
> 2. **A short write-up** — which persona you built for, your architecture, your assumptions, and the limitations you know about. If you claim a number anywhere — an accuracy figure, a speed-up, a comparison against an alternative — say how you arrived at it. A claim a judge cannot check does not score.
> 3. **A demo** — walk one real commuter journey, end to end, through one real disruption.

**`PS2/submission/README.md` §1 What to hand in (verbatim):**

> | # | Deliverable | Form |
> |---|---|---|
> | 1 | **The app** | Source repository, runnable from a README |
> | 2 | **A short write-up** | `WRITEUP.md` at the repository root |
> | 3 | **A demo** | A recording, linked from your README |
>
> Everything lives in one repository. Do not send a zip of a built artefact with
> no source — judges read the code.

**`PS2/submission/README.md` §3, what the README must contain (verbatim):**

> Your README must state:
>
> - **Prerequisites** — language runtime and version, package manager, anything
>   that must already be installed.
> - **Install and run** — the exact commands, in order. A judge should be able to
>   copy-paste them.
> - **Configuration** — which environment variables or API keys are needed and
>   where to obtain them. Ship a `.env.example` listing the variable *names*.
> - **What to click** — where the app opens, and the one journey to try first.

**`PS2/submission/README.md` §4 Credentials (verbatim, excerpt):**

> **Never commit an API key, an `AccountKey`, a password or a `.env` file.** Use
> environment variables and ship `.env.example` with the names only.
>
> A judge who cannot obtain a key cannot run your app, so if your submission
> depends on a key they must register for, say so plainly in the README and link
> the registration page.

**`PS2/submission/README.md` §5 Claims (verbatim, excerpt):**

> - **If something depends on a live feed that may be quiet on judging day** — a
>   disruption that is not happening — say so, and ship the captured data that
>   reproduces it. Replay and injected test data are fine **provided they are
>   labelled as such**.

**`PS2/submission/README.md` §6 The demo (verbatim):**

> One real commuter journey, end to end, through one real disruption — for the
> persona you chose. Five minutes is plenty.
>
> Record the screen of an actual phone, or a phone-sized browser window, because
> that is where Ease of Use is scored. Link the recording from your README; do not commit a
> large video file to the repository.

**`PS2/submission/README.md` §7 checklist (verbatim):**

> - [ ] Cloned into a fresh directory and followed my own README; it runs
> - [ ] No credentials in the repository or its history
> - [ ] `.env.example` lists every variable the app needs
> - [ ] `WRITEUP.md` names the persona I built for
> - [ ] Any number in `WRITEUP.md` says how I arrived at it
> - [ ] The demo recording is linked and plays
> - [ ] The app has been opened on a real phone browser, not just devtools emulation

**Not yet known:** where to submit, the deadline, and whether private repos are allowed. `submission/README.md` "Logistics" says all three are "**To be confirmed by the organisers before the brief is issued**".

**Current state of our deliverables: none are done.**

| Deliverable | State |
|---|---|
| App | Not started |
| `WRITEUP.md` | Does not exist (`README.md` links to it) |
| Demo recording | Does not exist |
| `.env.example` | Does not exist |
| `README.md` | Run instructions are all `<TBD>` |

---

## Q2. Judging criteria and weights

**`PS2/PS2_README.md` §3.2.4 Judging Rubric (verbatim).** The .docx and .pdf have the same wording, with `--` in place of em dashes.

> Submissions are graded against three criteria, weighted to **100%**:
>
> | Criterion | Weight | What Judges Look For |
> |---|---|---|
> | **Problem Fit** | **40%** | Would a real commuter be better off with this app than without it? Persona fit, proactivity and the quality of the decision it offers — plus whether the submission does anything beyond what this brief asked for. |
> | **Technical Execution** | **35%** | Routing that reflects live conditions on an OpenStreetMap base, the breadth and judgement of the data brought in, and whether the thing is actually built — runs from a clean README, performance is sane. |
> | **Ease of Use** | **25%** | A commuter could pick it up on a phone, one-handed, and get an answer. Interaction design, information hierarchy and accessibility. Scored on a real phone browser, not desktop emulation. |
>
> Each criterion is scored on a 0–5 scale and weighted. **Commuter value and design together carry more than half the total** — a technically impressive app that a commuter would not open twice cannot score well here, and that is deliberate.
>
> **Mandatory-capability cap.** A submission missing one of the three required capabilities in 3.2.1–3.2.3 cannot exceed level 3 on the part of the score that covers it.
>
> **Caps apply regardless of other merit.** A feature shown in the pitch but absent from the running system, mocked data presented as live, a claim a judge cannot verify, a credential committed to the repository, or OpenStreetMap used without attribution — each caps the part of the score it touches, and the attribution one is a licence breach rather than a style point.
>
> **How judging runs.** Judges follow your README on a clean machine; the app is opened in a browser on a real phone; you walk one real journey for your chosen persona end to end; and you are asked to defend one claim per criterion. Saying it is in the slides is not evidence.

The three mandatory capabilities are §3.2.1 Route planning, §3.2.2 GIS on OpenStreetMap and §3.2.3 Visualisation.

**Extra cap, only in the .docx/.pdf §2.5 (verbatim):**

> Do not scrape in breach of terms. A site's terms of service govern. Data obtained in breach of them caps the data dimension at 1 and is referred to the organisers before scoring continues.

It refers to a "data dimension", which is not one of the three criteria above. Presumably it is a sub-axis from the missing rubric file (Blocker 2), but that is **unconfirmed**.

**Where beyond-the-brief work counts:** it scores under Problem Fit (§3.3). §3.3.1 on AI:

> An AI feature you can show works — with a measurement, however simple — is worth far more than one you can only describe.

---

## Q3. Static files vs live LTA DataMall key

### Static files in `PS2/data/`: only two

| File | What it actually is |
|---|---|
| `AmendmenttoMP2014RailStation.geojson` | Rail station footprints; details below |
| `UsefulWebsites.txt` | A plain-text list of external sources and URLs. **Not a dataset.** |

Details of `AmendmenttoMP2014RailStation.geojson`, from inspecting the file tonight:

- 208 features, all of type `Polygon`.
- **`crs` is null**, as the brief warns.
- Properties: `OBJECTID`, `GRND_LEVEL`, `TYPE`, `NAME`, `INC_CRC`, `FMEL_UPD_D`, `SHAPE_1.AREA`, `SHAPE_1.LEN`.
- Value counts:
  - `GRND_LEVEL`: `UNDERGROUND` 120, `ABOVEGROUND` 88.
  - `TYPE`: `MRT` 149, `LRT` 46, `CCL` 13.
  - `NAME`: 175 distinct values. **13 are null**, and 5 are the generic `THOMSON LINE` rather than a station name.
  - `FMEL_UPD_D` is `20170509160126` on every feature, so the data was last updated **2017-05-09**.
- **Stations opened after May 2017 may be missing.** I have not checked which ones.
- Coordinates fall within x 103.636–103.989 and y 1.251–1.450. That range fits WGS84 longitude/latitude for Singapore, but **no metadata confirms it**.
- `SHAPE_1.AREA` values (e.g. `8935.27`) are clearly not in degrees². So the area attributes were computed in some other projected system, and the geometry and area fields do not share units.

### Static files in `PS2/references/`: documentation, not data

| File | What it actually is |
|---|---|
| `24hourWeatherForecast.json` | OpenAPI 3.0.3 spec for `/twenty-four-hr-forecast`. **No weather data.** |
| `4dayWeatherForecast.json` | OpenAPI 3.0.3 spec for `/four-day-outlook`. **No weather data.** |
| `LTA_DataMall_API_User_Guide.pdf` | DataMall API docs, v6.8 |
| `Problem_Statement_2_Specification.docx` / `.pdf` | The brief |

**There is no DataMall data anywhere in the organisers' repo:** no captured responses, no bus stops, no station exits, no crowd data.

### Needs a live LTA DataMall `AccountKey` (every DataMall endpoint)

These are all the endpoints `PS2_README.md` §2.4 lists. None is available as a static file.

- **Rail:** `TrainServiceAlerts`, `PCDRealTime`, `PCDForecast`
- **Bus:** `v3/BusArrival`, `BusServices`, `BusRoutes`, `BusStops`, `PlannedBusRoutes`
- **Road:** `EstTravelTimes`, `v4/TrafficSpeedBands`, `TrafficIncidents`, `RoadWorks`, `RoadOpenings`, `VMS`, `PubFloodAlerts`
- **Facilities:** `v2/FacilitiesMaintenance`, `Taxi-Availability`, `TaxiStands`, `CarParkAvailabilityv2`, `BicycleParkingv2`
- **Historical volumes:** `PV/Train`, `PV/Bus`, `PV/ODTrain`, `PV/ODBus`
- **Geospatial layers via `GeospatialWholeIsland`:** `CoveredLinkWay`, `CyclingPath`, `Footpath`, `PedestrainOverheadbridge_UnderPass`, `TrainStation`, `TrainStationExit`, `BusStopLocation`, `TaxiStand`

Checks against the guide:

- A text search of guide v6.8 finds `TrainServiceAlerts`, `PCDRealTime`, `PCDForecast`, `v3/BusArrival`, `RoadWorks`, `PlannedBusRoutes`, `CoveredLinkWay`, `TrainStationExit` and `PV/Train`.
- Facilities Maintenance "(version 2)" and Geospatial Whole Island are documented under those spaced names.
- The guide says authentication is "now requiring only AccountKey".

**Key status in this environment tonight:**

- No DataMall key was found: no environment variable matching `lta|datamall|account|onemap`, and no `.env` file in `smrtbuddy/`.
- `GET …/ltaodataservice/TrainServiceAlerts` with no key returned **HTTP 404**.
- I don't know whether you hold a key elsewhere. **Please confirm.**

### Needs no DataMall key

| Source | Key? | Checked tonight? |
|---|---|---|
| data.gov.sg real-time weather (`two-hr-forecast`, `twenty-four-hr-forecast`, `four-day-outlook`, `rainfall`) | None, per brief | Yes: `two-hr-forecast` and `twenty-four-hr-forecast` both returned **HTTP 200** |
| OpenStreetMap: Geofabrik extract, Overpass | None | Not tested |
| OneMap (geocoding, routing) | Free registration, per brief | Not tested; no OneMap credential found here |
| SG MRT Updates Telegram, `t.me/s/sgmrt` | None | Not tested. The brief says to read it "as reference material, not as a feed", and that "Scraping is generally not acceptable" (§2.5) |

---

## Q4. Which PRD.md §5 data sources are usable tonight?

**BLOCKED:** `PRD.md` is empty, so there is no §5 to check.

For when it arrives, these are the verified facts about each source tonight. They are not yet mapped to the PRD.

| Source | Usable tonight? |
|---|---|
| Rail station geojson (static) | Yes, it's on disk. Caveats: crs is null (the coordinates look like WGS84 but that's unconfirmed), the data dates from 2017, and 13 names are null |
| data.gov.sg weather | Yes: HTTP 200, no key |
| Any LTA DataMall endpoint | **Not from this environment.** No key found. Usable only if you have or register an AccountKey |
| OneMap | Unknown. Needs registration, not tested |
| OSM (Geofabrik / Overpass) | Unknown. Not tested tonight |
| Real disruption examples (`AffectedSegments`) | Normally empty, per brief §2.6. The disruption path must be a **labelled** replay or injected data. I have **not** created or sourced any such data |

---

## Q5. Prescribed folder structure or naming convention?

**The layout is suggested, not enforced.** `PS2/submission/README.md` §2 (verbatim):

> Nothing here is enforced, but a judge working through a stack of submissions
> will find their way around yours faster if it looks like this:
>
> ```
> your-submission/
> ├── README.md          # Setup + run instructions. The first thing a judge opens.
> ├── WRITEUP.md         # Persona, architecture, assumptions, known limitations
> ├── .env.example       # Names of the environment variables you need — no values
> └── src/ (or app/, apps/, …)
> ```

**Stated as the required form in §1's table** (see Q1):

- The write-up is "`WRITEUP.md` at the repository root".
- The app is a "Source repository, runnable from a README".
- The demo is "A recording, linked from your README".
- "Everything lives in one repository."

There is a tension: §2 says "Nothing here is enforced", while §1 names `WRITEUP.md` at the root as the form. **Safest reading:** treat `README.md`, `WRITEUP.md` and `.env.example` at the repo root as required. That is my reading, not a quote.

The "Standard Template for PS folders" in the organisers' top-level README (`PSX_README.md`, data folder, reference folder, submission folder) describes **the organisers' own** folders, not submissions.

---

## Q6. Does the rubric mention accessibility, elderly users, or specific personas?

**Accessibility: yes.**

- It is in the rubric row for Ease of Use (25%): "Interaction design, information hierarchy and accessibility."
- §3.2.3 (verbatim): "Accessibility is part of this, not separate from it: legible type sizes, sufficient contrast, and not relying on colour alone to convey a state."

**Personas: yes.** Problem Fit (40%) scores "Persona fit". "How judging runs" says "you walk one real journey for your chosen persona end to end". §2.2 (verbatim):

> You do not need to serve all three well — but say which one you are building for, and show a real journey working end to end for that person.

The three personas (§2.2, verbatim):

> **1. Rachel — the fixed-schedule commuter.**
> Tampines to Raffles Place, EWL, leaves 07:40, must be at her desk by 08:45. Has done the same trip for four years and does not check any app on a normal day. A five-minute delay is noise; a fifteen-minute delay costs her a meeting. She needs to be interrupted *only* when it matters, and told what to do in one line.
>
> **2. Arjun — the multi-modal, flexible-start worker.**
> Punggol to one-north. Cycles to the LRT, sometimes takes a bus the whole way if the weather is good, start time flexible within about an hour. Optimises for comfort and predictability over pure speed, and will happily leave twenty minutes later to avoid a crush. Cares about crowding, sheltered routes and whether he can bring his bike.
>
> **3. Mdm Lim — the accessibility-constrained occasional traveller.**
> Bedok to Singapore General Hospital for a fortnightly appointment. Walks slowly, avoids stairs, needs lifts and sheltered walkways, and will not improvise a reroute on the platform. For her the app must be usable in large text, must plan the whole trip in advance including the walk at each end, and must warn her the day before if a lift or exit is out of service.
>
> You may propose your own persona if you can justify it, but do not silently build for "a generic commuter" — that is how apps end up serving nobody.

**Elderly users: no.**

- The words "elderly", "senior", "older", "age" and "ageing" appear **nowhere** in the PS2 docs. I searched `PS2_README.md`, `submission/README.md`, the .docx, the .pdf and the top-level README.
- Mdm Lim is described as "accessibility-constrained", not by age. Calling her elderly would be our inference, not the brief's.

---

## Q7. Hosted/deployed app required, or only "runnable from the README"?

**Only "runnable from the README". No PS2 document requires a hosted deployment.**

- `submission/README.md` §1: the app's form is "Source repository, runnable from a README".
- §3: "**Judges follow your README on a clean machine. What does not run does not score.**"
- §2 header: "You are submitting a **running application**, so what matters is that a judge can get it running on a machine that is not yours".
- `PS2_README.md` §3.2.4: "Judges follow your README on a clean machine; the app is opened in a browser on a real phone".
- A search of the PS2 docs for host/deploy/URL finds no hosting requirement. "Self-host" appears only for OSM tiles and routing engines, and "URL" only for the submission logistics and API paths.

**Gap the docs leave open:** judges run the app from the README on a clean machine *and* open it on a real phone. The docs don't say how the phone reaches an app running on that machine (same network, a tunnel, or a hosted URL we provide), or whether a hosted URL is expected or merely allowed. **This is a question for the organisers.** I have not assumed an answer.

Our `README.md` has "**Live app:** `<TBD>`", which assumes a hosted deployment. The brief does not require one.

---

## Contradictions with PRD.md

**BLOCKED:** `PRD.md` is empty, so nothing in the repo can contradict it yet.

The conflicts below turned up while reading. **They are against the PS2 brief or internal to the repos, not against the PRD.** They are listed so they are not lost. None has been acted on or "fixed".

### A. Our repo (`smrtbuddy/`)

1. **PS3 scaffolding is still present.** You said it's dead; I'm ignoring it and have **not** deleted or moved anything. Inventory:
   - `src/acv.py`, `src/base.py`, `src/door.py`, `src/rail.py`, `src/shm.py`: all **0 bytes**.
   - `scoring/metrics.py`, `scoring/severity.py`: both **0 bytes**.
   - `scripts/extract_rail_features.py`, `scripts/package_submission.py`: both **0 bytes**.
   - `models/rail/` is a real PS3 rail-corrugation pipeline: `feature_extraction.py` (1429 lines), `train.py`, `predict.py`, `verify_pipeline.py`, `README.md`, and `artifacts/` (a 1.4 MB `rail_model.joblib`, `metadata.json` and `selected_features.json`).
   - `models/door/README.md`: documentation only, no code.
   - `predictions/rail_predictions.csv`: 68 PS3 rows.
   - `data/.gitkeep`, `features/.gitkeep`, `predictions/.gitkeep`.
   - Empty, untracked directories: `dashboard/`, `writeup/`, `notebooks/`.
2. **Two READMEs disagree on where the PS2 work lives.**
   - `ps2/README.md`: "Work folder for NEBULA X **Problem Statement 2**. The PS3 train-condition-monitoring work is unaffected and stays where it is, at the repository root."
   - Root `README.md` is written entirely as the PS2 project and says: "Earlier PS3 train-condition-monitoring work is retained under `models/` and `predictions/` but is **not part of this submission**."
   - `submission/README.md` expects `README.md` and `WRITEUP.md` at the repo root.
   - **Decision needed from you:** does the PS2 app live in `ps2/` or at the root?
3. **`.gitignore` would block the replay data the brief tells us to ship.**
   - It ignores `data/` and `*.csv`, excepting only `!predictions/*.csv`.
   - `submission/README.md` §5 says to "ship the captured data that reproduces it".
   - Any captured or replay data saved under `data/`, or as a `.csv` outside `predictions/`, would be silently left out of the repo.
4. **Root `README.md` "Live app: `<TBD>`"** assumes a hosted deployment the brief does not require (see Q7). It is an unstated assumption rather than a hard contradiction.
5. **Root `README.md` "How this is judged"** omits the scraping cap ("caps the data dimension at 1") that appears in the .docx/.pdf. `ps2/README.md` includes it. Minor.

### B. The organisers' own documents disagree with each other

These are not ours to fix. They are listed so we don't silently follow one version.

1. **The rubric file and generator scripts are referenced but missing** (Blocker 2).
2. **"four deliverables" vs three.** `submission/README.md` says "That section says *what* the four deliverables are", but `PS2_README.md` §4 and `submission/README.md` §1 both list **three**.
3. **Weather JSONs.**
   - The top-level README lists them under "Available Datasets → **Weather Data**", described as "Short-term weather predictions" and "Medium-term weather forecast".
   - `PS2_README.md` §2.4 says they are "**interface documents, not weather data**".
   - **Verified:** both are OpenAPI 3.0.3 specs with no data. `PS2_README.md` is correct.
4. **Telegram channel.**
   - The top-level README files it under "**Live Data Sources**" as "Real-time updates".
   - `UsefulWebsites.txt` says "This is an archive, not a live source."
   - `PS2_README.md` says "Read it as reference material, not as a feed."
5. **Scraping rule.**
   - `PS2_README.md` §2.5: "Scraping is generally not acceptable… raise it with us before you build on it".
   - .docx/.pdf §2.5: scraping in breach of terms "caps the data dimension at 1".
   - The two differ in wording and penalty, and "data dimension" is not in the three-criterion rubric.
6. **Crowding endpoint names.**
   - The .docx/.pdf say `PlatformCrowdDensityRealTime` / `PlatformCrowdDensityForecast`.
   - `PS2_README.md` uses `PCDRealTime` / `PCDForecast` and explains that the APIs were renamed while the URL paths stayed the same.
   - Guide v6.8 contains `PCDRealTime` / `PCDForecast`.
   - The .docx/.pdf themselves defer to `PS2_README.md` for the data architecture: "The participant brief (PS2_README.md, Section 2.4) carries the full data architecture".
7. **Event name and year are inconsistent (cosmetic).** The top-level README says "NebulaX 2026", the spec header says "LTA SMART MOBILITY HACKATHON", and the PDF page footer says "LTA HACKATHON 2027".
8. **The organisers' contact address is a placeholder.** The top-level README says "Email LTA_XX_ title your queries with [PS#] Your Question". No real address is given.

---

## Open questions

**For you:**

1. Where is the PRD content? `PRD.md` is 0 bytes. (Blocks Q4 and the contradictions section.)
2. Do you have an LTA DataMall `AccountKey`? None was found in this environment.
3. Do you have a OneMap account?
4. Should the PS2 app live in `ps2/` or at the repo root? (Contradiction A2.)
5. Do you have a real contact address for the organisers? The README gives only a placeholder.

**For the organisers:**

1. `PS2/references/PS2_scoring_rubric.md` is referenced but missing. Can they publish the sub-axes and level descriptions?
2. Hosting: judges run from the README on a clean machine and open the app on a real phone. How is the phone expected to reach it? Is a hosted URL expected, allowed, or neither?
3. Scraping penalty: which wording governs, `PS2_README.md` or the .docx/.pdf? What is the "data dimension"?
4. Submission logistics: where to submit, the deadline and timezone, and whether private repos are allowed. All are still "To be confirmed".
5. `submission/README.md` says "four deliverables", but only three are listed. Is one missing?

---

*Verification stops here. Waiting for instructions.*

---

## Update: 2026-09-19, after PRD v2

**Blocker 1 is resolved.** `PRD.md` now holds v2. It was written verbatim from the delimited content in your message.

**Decisions recorded:**

- The app lives at the **repo root**. `ps2/README.md` still says otherwise; it has not been touched.
- The DataMall key is in `.env`, which is gitignored (`git check-ignore -v .env` → `.gitignore:2:.env`). The key appears in no other file.
- The key works. `TrainServiceAlerts` returned HTTP 200 with `Status: 1`, 0 `AffectedSegments` and 3 `Message` entries.
- Fixture and replay data go in `data/fixtures/` (injected test data) and `data/replay/` (captured real responses). Both are committed, including CSV. Everything else under `data/` stays ignored.

### The six contradictions in the organisers' documents: which ones matter

| # | Contradiction | Affects our build? |
|---|---|---|
| B2 | "four deliverables" vs three | **Noise.** Every list has the same three, and the PRD matches. |
| B3 | Weather JSONs: "data" vs "spec" | **Affects us.** There is no weather data on disk. Weather is live-only, and the rain scenario needs our own labelled fixture. |
| B4 | Telegram: "live" vs "archive" | **Noise.** The PRD doesn't use Telegram. |
| B5 | Scraping rule and "data dimension" cap | **Noise** while we use only official APIs. It matters only if we ever scrape Telegram. |
| B6 | `PlatformCrowdDensity*` vs `PCD*` names | **Affects Block B.** Call `PCDRealTime` / `PCDForecast` (guide v6.8). |
| B7 | Event name/year | **Noise.** Cosmetic. |

### Where PRD v2 conflicts with the brief (the brief wins)

1. **OpenStreetMap is missing from the PRD.**
   - Brief §3.2.2 makes GIS on OSM mandatory. Missing it caps that part of the score at level 3.
   - Technical Execution is judged on "Routing that reflects live conditions on an OpenStreetMap base".
   - None of the PRD §11 Q1 routing options mentions OSM. This affects Block C.
2. **The §6 models can't carry what the brief's visualisation needs** (§3.2.3, mandatory):
   - `Leg` has no geometry, so a route can't be drawn on a map.
   - There is no flag to mark the affected portion.
   - `Advice` has a single `legs` list, so the alternative can't be shown against the original. PRD §2 itself says "Alternatives exist in the response".
   - There is no field for crowding level.
3. **The PRD's rubric summary drops scored content.**
   - Technical Execution is not "The build itself". It is OSM-based live routing, breadth and judgement of data, a clean-README run, and sane performance.
   - Ease of Use is scored one-handed on a real phone.
   - Problem Fit includes going beyond the brief.
4. **Privacy statement.** Brief §2.5 requires stating what we store, where and for how long. The PRD stores location pings and SOS audio, so `WRITEUP.md` must cover them.

### Internal PRD gaps (not brief conflicts)

- `driver_card` is in §3 and §7.6 but not in any §6 model. There is also no source in the repo for Chinese destination names.
- `Advice` has no `i18n_key`, although §3 says every user-facing string carries one.
- §3 says family accounts can see the latest position, but no endpoint in §8 exposes it.

### Block A status (built 2026-09-19)

- The skeleton, all §6 models and `SourceResult` are real and verified.
- **Every endpoint except `/health` is a STUB.** Stubs return the header `X-Stub: true`, persist nothing and consult no data.
- The request/response shapes that PRD.md does not define are **provisional**. They are marked in `app/models.py`.
