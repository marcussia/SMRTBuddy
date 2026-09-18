"""Walking legs on real OSM foot paths (Q1).

Primary: the FOSSGIS OSRM instance (routing.openstreetmap.de/routed-foot) —
the same foot profile openstreetmap.org offers; verified working 2026-09-19
(768 m at walking pace across a Bedok test pair, vs router.project-osrm.org
which returned car routing for the same pair and was rejected).

Responses are cached in-memory per coordinate pair — the brief requires not
hammering public OSM infrastructure. On any failure the fallback is
straight-line distance x WALK_DETOUR_FACTOR, and the result SAYS SO in
`source` (it is also surfaced in STATUS.md); it is an estimate, not OSM data.

Durations are always recomputed at the commuter's own walking speed — the
engine's speed, not the server's default pedestrian."""
import math
from dataclasses import dataclass

from app.adapters.base import AdapterError, fetch_json
from app.config import WALK_DETOUR_FACTOR

FOOT_OSRM = "https://routing.openstreetmap.de/routed-foot"

_cache: dict[tuple, "WalkRoute"] = {}


@dataclass(frozen=True)
class WalkRoute:
    distance_m: float
    geometry: list[tuple[float, float]]   # (lat, lon)
    source: str                           # "osm_foot" | "straightline_estimate"


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def walk_route(frm: tuple[float, float], to: tuple[float, float]) -> WalkRoute:
    key = (round(frm[0], 5), round(frm[1], 5), round(to[0], 5), round(to[1], 5))
    if key in _cache:
        return _cache[key]
    try:
        d = fetch_json(f"{FOOT_OSRM}/route/v1/foot/"
                       f"{frm[1]},{frm[0]};{to[1]},{to[0]}"
                       f"?overview=full&geometries=geojson")
        route = d["routes"][0]
        geom = [(lat, lon) for lon, lat in route["geometry"]["coordinates"]]
        result = WalkRoute(distance_m=float(route["distance"]),
                           geometry=geom, source="osm_foot")
    except (AdapterError, KeyError, IndexError, TypeError):
        # Labelled estimate — never presented as OSM routing.
        result = WalkRoute(distance_m=_haversine_m(frm, to) * WALK_DETOUR_FACTOR,
                           geometry=[frm, to], source="straightline_estimate")
    _cache[key] = result
    return result


def walk_minutes(distance_m: float, speed_mps: float) -> float:
    return distance_m / max(speed_mps, 0.1) / 60.0
