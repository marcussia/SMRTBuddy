# STATUS — build log

Newest entries at the bottom. Every block appends here: what was built, what
works, what is stubbed, what was assumed.

---

## 2026-09-19 ~01:00 — Pre-build fixes (after Block A commit `3f5ec05`)

**Done:**
- `ps2/README.md` → `archive/ps2/README.md`. One app, repo root.
- **Q7 RESOLVED — station GeoJSON is WGS84, not SVY21.** All coordinates are in
  [103.64, 103.99] × [1.25, 1.45] (degrees; SVY21 would be metres in the
  thousands). Sanity-checked: BEDOK centroid (1.3240, 103.9302) and MARINA BAY
  (1.276, 103.855) match known positions. No conversion needed.
- Extracted demo-corridor station centroids from the provided GeoJSON into
  `app/reference/stations.json` (mean of footprint exterior-ring vertices).
  19/20 matched. **DOWNTOWN (DT17) is not findable in the GeoJSON** (2017 data;
  13 features have null names, 5 are generic "THOMSON LINE"). It stays in the
  transit graph for hop timing with `coordinates: null`; route geometry skips it.

**Decisions applied (from user, resolved-questions list):**
- Q1 routing: OSM walking via OpenRouteService or OSRM public demo (30-min
  budget, else straight-line × 1.3, labelled); hand-built transit graph for the
  demo corridor only; tiles frontend-side.
- Q2: walking_speed default 0.8 m/s; wheelchair max_walk_metres defaults 200.
- Q3: REROUTE_BENEFIT_THRESHOLD_MIN = 10.
- Q4: wrong-direction = 3 consecutive divergent pings over ≥90 s, suppressed if
  accuracy > 50 m or near-stationary.
- Q5: crowd bands = whatever PCDRealTime returns (`l`/`m`/`h`/`NA` per the LTA
  guide; will record actual live values here when first fetched).
- Q6: en + zh for demo; i18n is table-driven so ms/ta are data additions.
- Model additions: Leg.geometry, Leg.crowding, Advice.affected_segment,
  Advice.alternatives.
