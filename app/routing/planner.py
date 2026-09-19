"""Journey planner (Block C). Small explicit graph over the demo corridor.

Produces RouteOptions (rail / rail-with-transfer / verified bus 2 / taxi);
the ENGINE decides which one becomes the recommendation — the planner only
enumerates what is physically viable and prices it in minutes.

Timing constants are assumptions recorded in STATUS.md (no timetable data in
the repo): MRT_HOP_MIN per adjacent station, TRANSFER_MIN per line change,
BOARDING_WAIT_MIN per boarding, BUS_HOP_MIN per bus stop."""
import heapq
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.config import (BOARDING_WAIT_MIN, MRT_HOP_MIN, TAXI_SPEED_KMH,
                        TRANSFER_MIN)
from app.i18n import place_zh, resolve
from app.models import DriverCard, Leg, MobilityProfile
from app.routing import stations as net
from app.routing.walk import _haversine_m, walk_minutes, walk_route

BUS_HOP_MIN = 1.8  # minutes per bus stop incl. dwell (assumption, STATUS.md)

LINE_NAMES = {"EWL": {"en": "East–West", "zh": "东西"},
              "DTL": {"en": "Downtown", "zh": "滨海市区"},
              "NEL": {"en": "North East", "zh": "东北"}}


@dataclass
class RouteOption:
    kind: str                 # "rail" | "bus" | "taxi"
    legs: list[Leg]
    total_min: float
    n_transfers: int
    walk_m: float
    uses_stations: list[str] = field(default_factory=list)
    driver_card: DriverCard | None = None
    walk_sources: set[str] = field(default_factory=set)


# --- rail graph ---------------------------------------------------------------

def _adjacency() -> dict[str, list[tuple[str, float, str]]]:
    """code -> [(neighbour_code, minutes, kind)]"""
    adj: dict[str, list[tuple[str, float, str]]] = {}
    for line in net.LINES.values():
        for a, b in zip(line, line[1:]):
            adj.setdefault(a.code, []).append((b.code, MRT_HOP_MIN, "hop"))
            adj.setdefault(b.code, []).append((a.code, MRT_HOP_MIN, "hop"))
    for a, b in net.INTERCHANGES:
        adj.setdefault(a, []).append((b, TRANSFER_MIN, "transfer"))
        adj.setdefault(b, []).append((a, TRANSFER_MIN, "transfer"))
    return adj


def rail_path(from_code: str, to_code: str,
              avoid: set[str]) -> list[str] | None:
    """Dijkstra over the corridor. `avoid` = station codes that cannot be
    used (disruption, lift outage for this profile). Interchange codes are
    avoided as a physical station: avoiding EW16 also avoids NE3 only if the
    caller says so — the engine decides that."""
    adj = _adjacency()
    if from_code in avoid or to_code in avoid:
        return None
    dist: dict[str, float] = {from_code: 0.0}
    prev: dict[str, str] = {}
    pq: list[tuple[float, str]] = [(0.0, from_code)]
    while pq:
        d, node = heapq.heappop(pq)
        if node == to_code:
            break
        if d > dist.get(node, float("inf")):
            continue
        for nxt, w, _kind in adj.get(node, []):
            if nxt in avoid:
                continue
            nd = d + w
            if nd < dist.get(nxt, float("inf")):
                dist[nxt] = nd
                prev[nxt] = node
                heapq.heappush(pq, (nd, nxt))
    if to_code not in dist:
        return None
    path = [to_code]
    while path[-1] != from_code:
        path.append(prev[path[-1]])
    return list(reversed(path))


def _split_by_line(path: list[str]) -> list[list[str]]:
    """Split a station-code path into same-line runs (each run = one MRT leg)."""
    runs: list[list[str]] = []
    for code in path:
        line = net.BY_CODE[code].line
        if runs and net.BY_CODE[runs[-1][-1]].line == line:
            runs[-1].append(code)
        else:
            runs.append([code])
    # drop 1-station runs that are just the interchange's other-code side
    return [r for r in runs if len(r) > 1]


def _direction(line: str, from_code: str, to_code: str) -> str:
    codes = [s.code for s in net.LINES[line]]
    i, j = codes.index(from_code), codes.index(to_code)
    if line == "EWL":
        return "Tuas Link" if j > i else "Pasir Ris"
    if line == "DTL":
        return "Expo" if j > i else "Bukit Panjang"
    return "Punggol" if j > i else "HarbourFront"


def _geom(codes: list[str]) -> list[tuple[float, float]]:
    return [(net.BY_CODE[c].lat, net.BY_CODE[c].lon)
            for c in codes if net.BY_CODE[c].lat is not None]


# --- leg builders --------------------------------------------------------------

def _mk(mode, from_name, to_name, depart, minutes, key, locale, *, svc=None,
        shelter, step_free, geometry, **params) -> Leg:
    arrive = depart + timedelta(minutes=minutes)
    text = resolve(key, locale, **params)
    return Leg(mode=mode, from_name=from_name, to_name=to_name, service=svc,
               depart=depart, arrive=arrive, instruction=text,
               speech_text=text, i18n_key=key, shelter=shelter,
               step_free=step_free, geometry=geometry)


def _walk_leg(frm_name, frm, to_name, to, depart, profile, locale,
              landmark_key="landmark.none") -> tuple[Leg, str]:
    """Returns (leg, source) — source says osm_foot or straightline_estimate."""
    wr = walk_route(frm, to)
    minutes = walk_minutes(wr.distance_m, profile.walking_speed_mps)
    leg = _mk("walk", frm_name, to_name, depart, minutes,
              "leg.walk.instruction", locale,
              # shelter "exposed" is conservative: no CoveredLinkWay data yet.
              # step_free "unverified": OSM foot routing does not tell us the
              # path avoids steps, and we do not assert what we have not checked.
              shelter="exposed", step_free="unverified", geometry=wr.geometry,
              to=to_name, landmark=resolve(landmark_key, locale))
    return leg, wr.source


def _rail_legs(path: list[str], depart: datetime, locale: str) -> list[Leg]:
    legs = []
    t = depart
    for run in _split_by_line(path):
        line = net.BY_CODE[run[0]].line
        stops = len(run) - 1
        minutes = BOARDING_WAIT_MIN + stops * MRT_HOP_MIN
        if legs:  # a transfer precedes every leg after the first
            minutes += TRANSFER_MIN
        frm, to = net.BY_CODE[run[0]], net.BY_CODE[run[-1]]
        leg = _mk("mrt", frm.name, to.name, t, minutes,
                  "leg.mrt.instruction", locale, svc=line,
                  # "verified" rests on LTA's barrier-free station programme
                  # (every MRT station has lift access); a live lift outage
                  # downgrades the leg to "not_step_free" in the engine.
                  shelter="covered", step_free="verified", geometry=_geom(run),
                  line=LINE_NAMES[line].get(locale, LINE_NAMES[line]["en"]),
                  from_=frm.name, to=to.name, stops=stops,
                  direction=_direction(line, run[0], run[-1]))
        legs.append(leg)
        t = leg.arrive
    return legs


# --- options -------------------------------------------------------------------

def _resolve_endpoint(name: str) -> tuple[str, tuple[float, float]] | None:
    """A journey endpoint is a known place or a corridor station name."""
    coord = net.place_for(name)
    if coord:
        return name, coord
    matches = net.station_for(name)
    for m in matches:
        if m.lat is not None:
            return m.name, (m.lat, m.lon)
    return None


def _nearest_station(coord: tuple[float, float],
                     avoid: set[str]) -> net.Station:
    usable = [s for s in net.BY_CODE.values()
              if s.lat is not None and s.code not in avoid]
    return min(usable, key=lambda s: _haversine_m(coord, (s.lat, s.lon)))


def plan_options(origin: str, destination: str, depart_at: datetime,
                 profile: MobilityProfile, locale: str = "en",
                 avoid: set[str] | None = None,
                 start_station_code: str | None = None) -> list[RouteOption]:
    """All viable options, cheapest first. `start_station_code` plans a
    mid-journey continuation from that station instead of the origin place.
    Raises ValueError for endpoints outside the demo corridor — the caller
    turns that into an honest 'cannot plan' rather than a guess."""
    avoid = avoid or set()
    o = _resolve_endpoint(origin)
    d = _resolve_endpoint(destination)
    if o is None or d is None:
        unknown = origin if o is None else destination
        raise ValueError(f"'{unknown}' is not in the demo corridor "
                         f"(places: {sorted(net.PLACES)}; "
                         f"stations: {sorted({s.name for s in net.BY_CODE.values()})})")
    o_name, o_coord = o
    d_name, d_coord = d
    options: list[RouteOption] = []

    # -- rail (with walks at both ends) --
    if start_station_code:
        o_station = net.BY_CODE[start_station_code]
    else:
        o_station = _nearest_station(o_coord, avoid)
    d_station = _nearest_station(d_coord, avoid)
    path = rail_path(o_station.code, d_station.code, avoid)
    if path and len(path) < 2:
        path = None   # same station both ends: no rail leg to ride
    if path:
        legs: list[Leg] = []
        wsrc: set[str] = set()
        t = depart_at
        if not start_station_code and _haversine_m(o_coord, (o_station.lat, o_station.lon)) > 50:
            leg, src = _walk_leg(o_name, o_coord, o_station.name,
                                 (o_station.lat, o_station.lon), t, profile, locale)
            wsrc.add(src)
            legs.append(leg)
            t = leg.arrive
        rail = _rail_legs(path, t, locale)
        legs += rail
        t = legs[-1].arrive
        if _haversine_m(d_coord, (d_station.lat, d_station.lon)) > 50:
            leg, src = _walk_leg(d_station.name, (d_station.lat, d_station.lon),
                                 d_name, d_coord, t, profile, locale)
            wsrc.add(src)
            legs.append(leg)
        walk_m = sum(_haversine_m(g, h) for L in legs if L.mode == "walk"
                     for g, h in zip(L.geometry, L.geometry[1:]))
        options.append(RouteOption(
            kind="rail", legs=legs,
            total_min=(legs[-1].arrive - depart_at).total_seconds() / 60,
            n_transfers=max(0, len(rail) - 1), walk_m=walk_m,
            uses_stations=path, walk_sources=wsrc))

    # -- verified bus 2 (only when the journey matches its captured segment) --
    b = net.BUS2
    board, alight = b["stops"][0], b["stops"][-1]
    if (start_station_code is None
            and _haversine_m(o_coord, (board["lat"], board["lon"])) < 500
            and _haversine_m(d_coord, (alight["lat"], alight["lon"])) < 800):
        legs = []
        wsrc = set()
        t = depart_at
        leg, src = _walk_leg(o_name, o_coord, board["name"],
                             (board["lat"], board["lon"]), t, profile, locale)
        wsrc.add(src)
        legs.append(leg); t = leg.arrive
        n_stops = len(b["stops"]) - 1
        bus = _mk("bus", board["name"], alight["name"], t,
                  BOARDING_WAIT_MIN + n_stops * BUS_HOP_MIN,
                  "leg.bus.instruction", locale, svc=b["service"],
                  # fleet-level basis (SG public buses are wheelchair-
                  # accessible; per-vehicle WAB check is future work)
                  shelter="partial", step_free="verified",
                  geometry=[(s["lat"], s["lon"]) for s in b["stops"]],
                  service=b["service"], from_=board["name"], to=alight["name"])
        legs.append(bus); t = bus.arrive
        leg, src = _walk_leg(alight["name"], (alight["lat"], alight["lon"]),
                             d_name, d_coord, t, profile, locale)
        wsrc.add(src)
        legs.append(leg)
        options.append(RouteOption(
            kind="bus", legs=legs,
            total_min=(legs[-1].arrive - depart_at).total_seconds() / 60,
            n_transfers=0,
            walk_m=sum(_haversine_m(g, h) for L in legs if L.mode == "walk"
                       for g, h in zip(L.geometry, L.geometry[1:])),
            uses_stations=[], walk_sources=wsrc))

    # -- taxi (engine offers it only as last resort, §7.6) --
    start = (net.BY_CODE[start_station_code].lat,
             net.BY_CODE[start_station_code].lon) if start_station_code else o_coord
    start_name = net.BY_CODE[start_station_code].name if start_station_code else o_name
    road_m = _haversine_m(start, d_coord) * 1.4     # road detour factor
    minutes = road_m / 1000 / TAXI_SPEED_KMH * 60 + 5  # +5 hail/board
    taxi = _mk("taxi", start_name, d_name, depart_at, minutes,
               "leg.taxi.instruction", locale,
               shelter="covered", step_free="verified",  # door-to-door
               geometry=[start, d_coord], from_=start_name, to=d_name)
    options.append(RouteOption(
        kind="taxi", legs=[taxi], total_min=minutes, n_transfers=0, walk_m=0,
        driver_card=DriverCard(destination_en=d_name,
                               destination_zh=place_zh(d_name),
                               arrive_by=taxi.arrive)))

    options.sort(key=lambda opt: opt.total_min)
    return options
