"""Step-free classification of walk legs from captured OSM data (Part B).

Source: data/replay/osm_accessibility_corridor.json — one Overpass query over
the demo corridor (steps, elevators, wheelchair=* tags), captured with
provenance. © OpenStreetMap contributors (ODbL).

Rules, conservative by design:
- A leg is "not_step_free" when its polyline actually RUNS ALONG a
  highway=steps way (or a wheelchair=no way) — within STEPS_TRAVERSE_M, i.e.
  on the way itself — and no highway=elevator lies within ELEVATOR_NEAR_M of
  that point. Measured on the demo corridor: routes that traverse steps come
  within 0–1.2 m of the steps way; routes that merely pass stair entrances
  stay 4 m+ away. 3 m separates the two cleanly (STATUS.md).
- Steps traversed but with a lift close by: stays "unverified" — we cannot
  tell which one the route takes.
- A leg is "verified" only when at least VERIFIED_COVERAGE of its points run
  within WHEELCHAIR_NEAR_M of wheelchair=yes ways and no steps hit it.
- Everything else stays "unverified" — the honest default.

All thresholds are geometric-matching assumptions (OSRM gives us geometry,
not OSM way ids), recorded in STATUS.md.
"""
import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Literal

STEPS_TRAVERSE_M = 3.0
ELEVATOR_NEAR_M = 60.0
WHEELCHAIR_NEAR_M = 12.0
VERIFIED_COVERAGE = 0.6

_REPLAY = Path(__file__).resolve().parent.parent.parent / "data" / "replay" \
    / "osm_accessibility_corridor.json"

Point = tuple[float, float]           # (lat, lon)
Line = list[Point]

# local metres per degree at ~1.3° N
_MLAT = 111_320.0
_MLON = 111_320.0 * math.cos(math.radians(1.3))


def _xy(p: Point) -> tuple[float, float]:
    return p[1] * _MLON, p[0] * _MLAT


def _pt_seg_m(p: Point, a: Point, b: Point) -> float:
    px, py = _xy(p)
    ax, ay = _xy(a)
    bx, by = _xy(b)
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _pt_line_m(p: Point, line: Line) -> float:
    if len(line) == 1:
        return _pt_seg_m(p, line[0], line[0])
    return min(_pt_seg_m(p, a, b) for a, b in zip(line, line[1:]))


def _geom(el: dict) -> Line:
    if el["type"] == "node":
        return [(el["lat"], el["lon"])]
    return [(g["lat"], g["lon"]) for g in el.get("geometry", [])]


@lru_cache(maxsize=1)
def _load() -> dict[str, list[Line]]:
    if not _REPLAY.exists():
        return {"steps": [], "elevators": [], "wc_yes": [], "wc_no": []}
    data = json.loads(_REPLAY.read_text())
    out: dict[str, list[Line]] = {"steps": [], "elevators": [], "wc_yes": [], "wc_no": []}
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        line = _geom(el)
        if not line:
            continue
        if tags.get("highway") == "elevator":
            out["elevators"].append(line)
        elif tags.get("highway") == "steps":
            out["steps"].append(line)
        elif tags.get("wheelchair") == "yes":
            out["wc_yes"].append(line)
        elif tags.get("wheelchair") == "no":
            out["wc_no"].append(line)
    return out


def classify_walk(geometry: Line) -> Literal["verified", "unverified", "not_step_free"]:
    if len(geometry) < 2:
        return "unverified"
    osm = _load()
    if not any(osm.values()):
        return "unverified"        # no capture on disk -> Part A behaviour

    barriers = osm["steps"] + osm["wc_no"]
    blocked_pts = [p for p in geometry
                   if any(_pt_line_m(p, b) <= STEPS_TRAVERSE_M for b in barriers)]
    if blocked_pts:
        for p in blocked_pts:
            if not any(_pt_line_m(p, e) <= ELEVATOR_NEAR_M for e in osm["elevators"]):
                return "not_step_free"
        return "unverified"        # steps nearby but a lift alternative exists

    if osm["wc_yes"]:
        covered = sum(1 for p in geometry
                      if any(_pt_line_m(p, w) <= WHEELCHAIR_NEAR_M
                             for w in osm["wc_yes"]))
        if covered / len(geometry) >= VERIFIED_COVERAGE:
            return "verified"
    return "unverified"
